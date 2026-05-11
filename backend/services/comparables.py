"""
Comparables engine: find the N most similar players by stat profile,
weight their salaries by inverse distance, return an estimate.
"""

import math
import logging
from database.db import get_all_with_salary
from config import CURRENT_SEASON

logger = logging.getLogger(__name__)

SKATER_STAT_KEYS = [
    "goals_per_60", "assists_per_60", "points_per_60",
    "toi_per_game", "corsi_for_pct", "xgf_pct", "penalty_diff_per_60",
]
GOALIE_STAT_KEYS = [
    "save_pct", "gaa", "quality_start_pct", "games_started",
]
POSITION_GROUPS = {
    "C": "F", "L": "F", "LW": "F", "R": "F", "RW": "F",
    "D": "D", "G": "G",
}


def _pos_group(position):
    return POSITION_GROUPS.get(position.upper(), "F")


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _compute_zscore_params(players, stat_keys):
    """Compute mean and std for each stat across all players."""
    params = {}
    for key in stat_keys:
        vals = [_safe_float(p["stats"].get(key)) for p in players]
        n = len(vals)
        if n == 0:
            params[key] = (0.0, 1.0)
            continue
        mean = sum(vals) / n
        variance = sum((v - mean) ** 2 for v in vals) / max(n - 1, 1)
        std = math.sqrt(variance) if variance > 0 else 1.0
        params[key] = (mean, std)
    return params


def _zscore(val, mean, std):
    return (val - mean) / std if std != 0 else 0.0


def _weighted_distance(z_target, z_comp, weights, stat_keys):
    """Weighted Euclidean distance between two z-score vectors."""
    total = 0.0
    for key in stat_keys:
        w = _safe_float(weights.get(key, 1.0))
        diff = z_target.get(key, 0.0) - z_comp.get(key, 0.0)
        total += w * diff * diff
    return math.sqrt(total)


def find_comparables(player_stats, weights=None, n=10,
                     position_filter=True, fa_status="auto",
                     season=None):
    """
    Find N most comparable players for the given player_stats dict.

    player_stats must have keys: position, age, fa_type, stats (dict),
    and optionally nhl_id (to exclude self from comparables).

    Returns dict with estimate, low, high, confidence, and comparables list.
    """
    season = season or CURRENT_SEASON
    position = player_stats.get("position", "C")
    pg = _pos_group(position)
    is_goalie = pg == "G"
    stat_keys = GOALIE_STAT_KEYS if is_goalie else SKATER_STAT_KEYS

    if weights is None:
        weights = {k: 1.0 for k in stat_keys}

    # Load all players with salary + stats
    all_players = get_all_with_salary(season)
    if not all_players:
        return _empty_result("No salary/stats data in database")

    # Optionally restrict to same position group
    if position_filter:
        pool = [p for p in all_players if _pos_group(p.get("position", "")) == pg]
    else:
        pool = all_players

    # Exclude the player themselves
    self_id = str(player_stats.get("nhl_id", ""))
    if self_id:
        pool = [p for p in pool if str(p["player_id"]) != self_id]

    if len(pool) < 3:
        pool = all_players  # fall back to all positions

    # Compute z-score params from pool
    params = _compute_zscore_params(pool, stat_keys)

    # Z-score target player
    target_stats = player_stats.get("stats", {})
    z_target = {}
    for key in stat_keys:
        val = _safe_float(target_stats.get(key))
        mean, std = params[key]
        z_target[key] = _zscore(val, mean, std)

    # FA status adjustment
    effective_fa = fa_status
    if fa_status == "auto":
        effective_fa = player_stats.get("fa_type", "UFA")

    # Compute distances
    scored = []
    for comp in pool:
        comp_stats = comp.get("stats", {})
        z_comp = {}
        for key in stat_keys:
            val = _safe_float(comp_stats.get(key))
            mean, std = params[key]
            z_comp[key] = _zscore(val, mean, std)

        dist = _weighted_distance(z_target, z_comp, weights, stat_keys)

        # Minor FA status penalty if mismatch
        comp_fa = comp.get("fa_type", "UFA")
        if effective_fa != "auto" and comp_fa != effective_fa:
            dist *= 1.15

        similarity = 1.0 / (1.0 + dist)
        scored.append((dist, similarity, comp))

    scored.sort(key=lambda x: x[0])
    top_n = scored[:n]

    if not top_n:
        return _empty_result("No comparable players found")

    # Salary estimate: inverse-distance weighted average
    total_weight = sum(1.0 / (d + 1e-9) for d, _, _ in top_n)
    estimate = sum(
        (1.0 / (d + 1e-9)) / total_weight * p["aav"]
        for d, _, p in top_n
    )

    salaries = sorted([p["aav"] for _, _, p in top_n])
    low = salaries[0]
    high = salaries[-1]

    avg_sim = sum(sim for _, sim, _ in top_n) / len(top_n)
    if avg_sim > 0.7 and len(top_n) >= 8:
        confidence = "high"
    elif avg_sim > 0.5 and len(top_n) >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    comparables = []
    for dist, sim, p in top_n:
        comp_entry = {
            "player_id": p["player_id"],
            "name": p["player_name"],
            "team": p.get("team", ""),
            "position": p.get("position", ""),
            "aav": p["aav"],
            "fa_type": p.get("fa_type", ""),
            "similarity": round(sim, 3),
            "stats": p.get("stats", {}),
        }
        comparables.append(comp_entry)

    return {
        "estimate": round(estimate),
        "low": round(low),
        "high": round(high),
        "confidence": confidence,
        "n_comparables": len(top_n),
        "comparables": comparables,
    }


def _empty_result(reason=""):
    return {
        "estimate": None,
        "low": None,
        "high": None,
        "confidence": "low",
        "n_comparables": 0,
        "comparables": [],
        "error": reason,
    }
