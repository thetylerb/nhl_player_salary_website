"""
Comparables engine: Gaussian kernel-weighted estimate over ALL same-position
players with salary data.  The top-N most similar players are still returned
for the display table, but the salary estimate uses the full position pool so
a single outlier cannot skew the result.
"""

import math
import logging
from database.db import get_all_with_salary, get_all_with_salary_historical, get_cap_ceiling, get_current_cap_ceiling
from config import CURRENT_SEASON

logger = logging.getLogger(__name__)

SKATER_STAT_KEYS = [
    "goals_per_60", "primary_points_per_60", "points_per_60", "ixg_per_60",
    "toi_per_game", "zone_start_pct",
    "corsi_for_pct", "xgf_pct", "on_ice_hd_cf_pct",
    "shots_per_60", "hd_goals_per_60", "hits_per_60",
    "penalty_diff_per_60",
]
GOALIE_STAT_KEYS = [
    "save_pct", "gaa", "quality_start_pct", "hd_save_pct", "gsaa", "games_started",
]
POSITION_GROUPS = {
    "C": "F", "L": "F", "LW": "F", "R": "F", "RW": "F", "W": "F", "F": "F",
    "D": "D", "LD": "D", "RD": "D",
    "G": "G",
}


def _pos_group(position):
    return POSITION_GROUPS.get(position.upper(), "F")


def _estimate_signing_year(player):
    expiry = player.get("expiry_season")
    years = player.get("contract_years")
    if expiry and years and int(years) > 0:
        return int(expiry) - int(years)
    return int(CURRENT_SEASON)


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _compute_zscore_params(players, stat_keys):
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
    Kernel-weighted salary estimate over all same-position players.

    The bandwidth (sigma) is set to the distance to the n-th nearest neighbour
    so it adapts automatically: tight when many similar players exist, wider
    when the pool is sparse.  The top-n most similar players are returned for
    the display table without change.
    """
    season = season or CURRENT_SEASON
    position = player_stats.get("position", "C")
    pg = _pos_group(position)
    is_goalie = pg == "G"
    stat_keys = GOALIE_STAT_KEYS if is_goalie else SKATER_STAT_KEYS

    if weights is None:
        weights = {k: 1.0 for k in stat_keys}

    all_players = get_all_with_salary_historical() or get_all_with_salary(season)
    if not all_players:
        return _empty_result("No salary/stats data in database")

    if position_filter:
        pool = [p for p in all_players if _pos_group(p.get("position", "")) == pg]
    else:
        pool = all_players

    self_id = str(player_stats.get("nhl_id", ""))
    if self_id:
        pool = [p for p in pool if str(p["player_id"]) != self_id]

    if len(pool) < 3:
        pool = all_players

    params = _compute_zscore_params(pool, stat_keys)

    target_stats = player_stats.get("stats", {})
    z_target = {}
    for key in stat_keys:
        val = _safe_float(target_stats.get(key))
        mean, std = params[key]
        z_target[key] = _zscore(val, mean, std)

    effective_fa = fa_status
    if fa_status == "auto":
        effective_fa = player_stats.get("fa_type", "UFA")

    # Compute distance from target to every player in the pool
    scored = []
    for comp in pool:
        comp_stats = comp.get("stats", {})
        z_comp = {}
        for key in stat_keys:
            val = _safe_float(comp_stats.get(key))
            mean, std = params[key]
            z_comp[key] = _zscore(val, mean, std)

        dist = _weighted_distance(z_target, z_comp, weights, stat_keys)

        comp_fa = comp.get("fa_type", "UFA")
        if effective_fa != "auto" and comp_fa != effective_fa:
            dist *= 1.15

        similarity = 1.0 / (1.0 + dist)
        scored.append((dist, similarity, comp))

    scored.sort(key=lambda x: x[0])

    if not scored:
        return _empty_result("No comparable players found")

    # Bandwidth = distance to the n-th nearest neighbour (adaptive)
    n_ref = min(n, len(scored))
    sigma = max(scored[n_ref - 1][0], 0.3)

    # Gaussian kernel weights over the FULL pool
    kernel_weights = [math.exp(-0.5 * (d / sigma) ** 2) for d, _, _ in scored]
    total_kw = sum(kernel_weights)

    if total_kw < 1e-9:
        return _empty_result("No comparable players found")

    # Estimate: kernel-weighted average of cap-normalised AAVs across full pool
    current_cap = get_current_cap_ceiling()
    estimate_pct = sum(
        kw / total_kw
        * (_safe_float(p["aav"]) / max(get_cap_ceiling(_estimate_signing_year(p)), 1))
        for kw, (_, _, p) in zip(kernel_weights, scored)
    )
    estimate = estimate_pct * current_cap

    # 15th / 85th percentile of kernel-weighted distribution → low / high
    weighted_pairs = sorted(
        [
            (
                _safe_float(p["aav"]) / max(get_cap_ceiling(_estimate_signing_year(p)), 1),
                kw,
            )
            for kw, (_, _, p) in zip(kernel_weights, scored)
        ],
        key=lambda x: x[0],
    )
    cum = 0.0
    low_pct = weighted_pairs[0][0]
    high_pct = weighted_pairs[-1][0]
    for pct, kw in weighted_pairs:
        cum += kw / total_kw
        if cum <= 0.15:
            low_pct = pct
        if cum <= 0.85:
            high_pct = pct
    low = low_pct * current_cap
    high = high_pct * current_cap

    # Effective N: how many players the kernel is really drawing from
    effective_n = int(round(total_kw ** 2 / max(sum(kw ** 2 for kw in kernel_weights), 1e-9)))
    pool_size = len(scored)

    # Confidence based on effective N and similarity of the top-n
    top_n = scored[:n]
    avg_sim = sum(sim for _, sim, _ in top_n) / len(top_n)
    if effective_n > 25 and avg_sim > 0.5:
        confidence = "high"
    elif effective_n > 10 and avg_sim > 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    comparables = []
    for dist, sim, p in top_n:
        comparables.append({
            "player_id": p["player_id"],
            "name": p["player_name"],
            "team": p.get("team", ""),
            "position": p.get("position", ""),
            "aav": p["aav"],
            "fa_type": p.get("fa_type", ""),
            "similarity": round(sim, 3),
            "stats": p.get("stats", {}),
        })

    return {
        "estimate": round(estimate),
        "low": round(low),
        "high": round(high),
        "confidence": confidence,
        "n_comparables": effective_n,
        "pool_size": pool_size,
        "comparables": comparables,
    }


def _empty_result(reason=""):
    return {
        "estimate": None,
        "low": None,
        "high": None,
        "confidence": "low",
        "n_comparables": 0,
        "pool_size": 0,
        "comparables": [],
        "error": reason,
    }
