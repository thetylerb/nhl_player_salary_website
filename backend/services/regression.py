"""
Regression model: train on salary + stats dataset, predict salary for a player.
Uses GradientBoostingRegressor. Trained per position group (F, D, G).
Models are retrained each call if stale (or on first call).
"""

import logging
import math
from datetime import datetime, timedelta

from database.db import get_all_with_salary
from config import CURRENT_SEASON

logger = logging.getLogger(__name__)

# In-memory model cache: { position_group: { "model": ..., "trained_at": datetime } }
_model_cache = {}
MODEL_TTL_HOURS = 6

SKATER_FEATURES = [
    "goals_per_60", "assists_per_60", "points_per_60",
    "toi_per_game", "corsi_for_pct", "xgf_pct",
    "penalty_diff_per_60",
]
GOALIE_FEATURES = [
    "save_pct", "gaa", "quality_start_pct", "games_started",
]
COMMON_FEATURES = ["age", "experience", "is_ufa"]

POSITION_GROUPS = {
    "C": "F", "L": "F", "LW": "F", "R": "F", "RW": "F",
    "D": "D", "G": "G",
}


def _pos_group(position):
    return POSITION_GROUPS.get(str(position).upper(), "F")


def _safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _feature_keys(pg):
    if pg == "G":
        return GOALIE_FEATURES + COMMON_FEATURES
    return SKATER_FEATURES + COMMON_FEATURES


def _extract_features(player, pg):
    stats = player.get("stats", {}) if isinstance(player, dict) else {}
    age = _safe_float(player.get("age", 28))
    experience = _safe_float(player.get("experience", 5))
    fa_type = player.get("fa_type", "UFA") or "UFA"
    is_ufa = 1.0 if str(fa_type).upper() == "UFA" else 0.0

    row = []
    feat_keys = SKATER_FEATURES if pg != "G" else GOALIE_FEATURES
    for key in feat_keys:
        row.append(_safe_float(stats.get(key)))
    row.extend([age, experience, is_ufa])
    return row


def _build_training_data(pg, season):
    all_players = get_all_with_salary(season)
    pool = [p for p in all_players if _pos_group(p.get("position", "")) == pg]

    X, y = [], []
    for p in pool:
        aav = _safe_float(p.get("aav"))
        if aav <= 0:
            continue
        feats = _extract_features(p, pg)
        if any(math.isnan(f) or math.isinf(f) for f in feats):
            continue
        X.append(feats)
        y.append(aav)
    return X, y


def _train_model(pg, season):
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        import numpy as np

        X, y = _build_training_data(pg, season)
        if len(X) < 5:
            logger.warning(f"Not enough training data for {pg} model ({len(X)} samples)")
            return None

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.08,
                max_depth=4,
                subsample=0.85,
                random_state=42,
            )),
        ])
        model.fit(X_arr, y_arr)
        logger.info(f"Trained {pg} model on {len(X)} samples")
        return model
    except ImportError:
        logger.warning("scikit-learn not available, regression model disabled")
        return None
    except Exception as e:
        logger.error(f"Training error for {pg}: {e}")
        return None


def _get_model(pg, season):
    entry = _model_cache.get(pg)
    if entry:
        age = datetime.utcnow() - entry["trained_at"]
        if age < timedelta(hours=MODEL_TTL_HOURS) and entry["model"] is not None:
            return entry["model"]

    model = _train_model(pg, season)
    _model_cache[pg] = {"model": model, "trained_at": datetime.utcnow()}
    return model


def predict_salary(player_stats, season=None):
    """
    Predict salary for a player given their stat dict.

    player_stats must have: position, age, experience, fa_type, stats (dict)

    Returns dict with estimate, low, high, confidence.
    """
    season = season or CURRENT_SEASON
    position = player_stats.get("position", "C")
    pg = _pos_group(position)

    model = _get_model(pg, season)
    if model is None:
        return {
            "estimate": None, "low": None, "high": None,
            "confidence": "low",
            "error": "Model not available (insufficient data or sklearn missing)",
        }

    try:
        import numpy as np

        feats = _extract_features(player_stats, pg)
        X = np.array([feats], dtype=float)
        pred = float(model.predict(X)[0])

        # Bootstrap confidence interval using staged predictions
        estimators = model.named_steps["gbr"].estimators_
        n_est = len(estimators)
        partial_preds = []
        # Sample ~20 partial predictions to estimate variance
        step = max(1, n_est // 20)
        for i in range(step, n_est + 1, step):
            partial_model = _partial_predict(model, X, i)
            if partial_model is not None:
                partial_preds.append(partial_model)

        if len(partial_preds) >= 3:
            arr = sorted(partial_preds)
            lo_idx = max(0, int(len(arr) * 0.1))
            hi_idx = min(len(arr) - 1, int(len(arr) * 0.9))
            low = arr[lo_idx]
            high = arr[hi_idx]
        else:
            low = pred * 0.85
            high = pred * 1.15

        # Confidence from R² of training set (approximated)
        confidence = "medium"
        training_samples, _ = _build_training_data(pg, season)
        if len(training_samples) >= 20:
            confidence = "high"
        elif len(training_samples) < 8:
            confidence = "low"

        return {
            "estimate": round(max(pred, 750000)),
            "low": round(max(low, 750000)),
            "high": round(max(high, 750000)),
            "confidence": confidence,
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {
            "estimate": None, "low": None, "high": None,
            "confidence": "low", "error": str(e),
        }


def _partial_predict(pipeline, X, n_estimators):
    """Predict using only the first n_estimators trees."""
    try:
        import numpy as np
        from sklearn.ensemble._gb import BaseGradientBoosting

        scaler = pipeline.named_steps["scaler"]
        gbr = pipeline.named_steps["gbr"]
        X_scaled = scaler.transform(X)

        init_pred = gbr._raw_predict_init(X_scaled)
        pred = init_pred.copy()
        lr = gbr.learning_rate

        for i, stage in enumerate(gbr.estimators_):
            if i >= n_estimators:
                break
            for k, tree in enumerate(stage):
                pred[:, k] += lr * tree.predict(X_scaled)

        return float(pred[0, 0])
    except Exception:
        return None


def invalidate_models():
    """Force model retraining on next prediction call."""
    _model_cache.clear()
