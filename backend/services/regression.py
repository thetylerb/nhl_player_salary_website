"""
Regression model: loads pre-trained per-position-group models from backend/models/.

Winners from 5-fold CV on 720 historical contracts (2019-2024):
  Forwards   → GBR   R²=0.813  RMSE=$1.26M
  Defensemen → Ridge R²=0.753  RMSE=$1.35M
  Goalies    → Ridge R²=0.363  RMSE=$2.00M

Feature extraction maps available DB stats to model features.
Missing features (PP splits, EV splits) are filled with training-set medians.
"""

import json
import logging
import os
import math

import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

# Reported RMSE from 5-fold CV (in dollars, at $88M cap)
_CV_RMSE = {'F': 1_260_000, 'D': 1_350_000, 'G': 2_000_000}

# Model cache: loaded once on first use
_loaded = {}

POSITION_GROUPS = {
    'C': 'F', 'L': 'F', 'LW': 'F', 'R': 'F', 'RW': 'F', 'W': 'F', 'F': 'F',
    'D': 'D', 'LD': 'D', 'RD': 'D',
    'G': 'G',
}

# Maps notebook feature names → DB stat field names (where they differ)
_STAT_ALIASES = {
    'goals_per60'     : 'goals_per_60',
    'primaryA_per60'  : 'primary_points_per_60',
    'points_per60'    : 'points_per_60',
    'xG_per60'        : 'ixg_per_60',
    'shots_per60'     : 'shots_per_60',
    'hdGoals_per60'   : 'hd_goals_per_60',
    'hits_per60'      : 'hits_per_60',
    'penDiff_per60'   : 'penalty_diff_per_60',
    'ozone_start_pct' : 'zone_start_pct',
    'ev_xGF_pct'      : 'xgf_pct',
    'ev_corsi_pct'    : 'corsi_for_pct',
    'gsaa'            : 'gsaa',
    'gaa'             : 'gaa',
    'save_pct'        : 'save_pct',
    'hd_save_pct'     : 'hd_save_pct',
}


def _pos_group(position):
    return POSITION_GROUPS.get(str(position).upper(), 'F')


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _load_group(pg):
    """Load model, feature list, and medians for a position group. Cached."""
    if pg in _loaded:
        return _loaded[pg]
    try:
        import joblib
        model = joblib.load(os.path.join(MODELS_DIR, f'{pg}_model.joblib'))
        with open(os.path.join(MODELS_DIR, f'{pg}_features.json')) as f:
            features = json.load(f)
        with open(os.path.join(MODELS_DIR, f'{pg}_medians.json')) as f:
            medians = json.load(f)
        _loaded[pg] = (model, features, medians)
        logger.info(f'Loaded pre-trained {pg} model ({len(features)} features)')
        return _loaded[pg]
    except Exception as e:
        logger.warning(f'Could not load {pg} model: {e}')
        return None


def _extract_features(player_stats, features, medians):
    """
    Build a feature vector mapping player_stats to model feature names.
    Falls back to training-set median for any feature not directly available.
    """
    stats = player_stats.get('stats', {}) or {}
    age   = _safe_float(player_stats.get('age', 28))
    gp    = _safe_float(stats.get('games_played', 0))
    toi   = _safe_float(stats.get('toi_per_game'))

    direct = {
        'age_at_signing': age,
        'gp_pct'        : min(gp / 82.0, 1.0) if gp > 0 else medians.get('gp_pct', 0.7),
        'toi_per_game'  : toi if toi > 0 else medians.get('toi_per_game', 16.0),
    }

    # Map aliased stat fields
    for feat, db_field in _STAT_ALIASES.items():
        val = stats.get(db_field)
        if val is not None:
            direct[feat] = _safe_float(val)

    # Direct name matches (future-proofing if DB gains more fields)
    for feat in features:
        if feat not in direct and feat in stats:
            direct[feat] = _safe_float(stats[feat])

    return [direct.get(feat, medians.get(feat, 0.0)) for feat in features]


def predict_salary(player_stats, season=None):
    """
    Predict salary for a player given their stat dict.
    player_stats must include: position, age, stats (dict of MoneyPuck fields).
    Returns dict with estimate, low, high, confidence, rmse_dollars, algo.
    """
    from database.db import get_current_cap_ceiling

    position = player_stats.get('position', 'C')
    pg = _pos_group(position)

    loaded = _load_group(pg)
    if loaded is None:
        return _fallback_error(pg, 'Pre-trained model not available')

    model, features, medians = loaded

    try:
        row = _extract_features(player_stats, features, medians)
        X   = np.array([row], dtype=float)

        if any(math.isnan(v) or math.isinf(v) for v in row):
            return _fallback_error(pg, 'Invalid feature values')

        current_cap = get_current_cap_ceiling()
        pred_pct    = float(model.predict(X)[0])
        estimate    = pred_pct * current_cap

        rmse = _CV_RMSE.get(pg, 1_500_000)
        low  = max(estimate - rmse, 750_000)
        high = estimate + rmse

        # Confidence: how many features came from live DB stats vs medians
        stats = player_stats.get('stats', {}) or {}
        n_direct = sum(
            1 for feat in features
            if feat in ('age_at_signing', 'gp_pct', 'toi_per_game')
            or _STAT_ALIASES.get(feat) in stats
            or feat in stats
        )
        coverage = n_direct / max(len(features), 1)
        confidence = 'high' if coverage >= 0.7 else ('medium' if coverage >= 0.4 else 'low')

        algo = 'GBR' if pg == 'F' else 'Ridge'

        return {
            'estimate'      : round(max(estimate, 750_000)),
            'low'           : round(low),
            'high'          : round(high),
            'confidence'    : confidence,
            'rmse_dollars'  : rmse,
            'algo'          : algo,
            'position_group': pg,
            'n_samples'     : {'F': 381, 'D': 197, 'G': 63}[pg],
        }

    except Exception as e:
        logger.error(f'Prediction error for {pg}: {e}')
        return _fallback_error(pg, str(e))


def _fallback_error(pg, msg):
    return {
        'estimate'  : None,
        'low'       : None,
        'high'      : None,
        'confidence': 'low',
        'error'     : msg,
        'algo'      : 'GBR' if pg == 'F' else 'Ridge',
    }


def invalidate_models():
    """Force model reload on next prediction call."""
    _loaded.clear()


def cross_validate_model(pg, season=None):
    """Return pre-computed CV metrics (used by the /estimate API endpoint)."""
    pg = _pos_group(pg) if len(pg) > 1 else pg
    return {
        'n_samples'   : {'F': 381, 'D': 197, 'G': 63}.get(pg),
        'n_folds'     : 5,
        'algo'        : 'GBR' if pg == 'F' else 'Ridge',
        'r2_mean'     : {'F': 0.813, 'D': 0.753, 'G': 0.363}.get(pg),
        'rmse_dollars': _CV_RMSE.get(pg),
    }
