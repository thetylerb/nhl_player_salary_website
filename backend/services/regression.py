"""
Regression model: train on salary + stats dataset, predict salary for a player.
F: GradientBoostingRegressor (enough data to benefit from non-linearity).
D/G: Ridge Regression (small datasets — Ridge generalizes; GBR just memorizes).
Models are retrained each call if stale (or on first call).
"""

import logging
import math
from datetime import datetime, timedelta

from database.db import get_all_with_salary, get_all_with_salary_historical, get_cap_ceiling, get_current_cap_ceiling
from config import CURRENT_SEASON

logger = logging.getLogger(__name__)

# In-memory model cache: { position_group: { "model": ..., "trained_at": datetime } }
_model_cache = {}
MODEL_TTL_HOURS = 6

# RMSE cache: { position_group: rmse_dollars } — populated on first predict per group
_rmse_cache = {}

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
    "C": "F", "L": "F", "LW": "F", "R": "F", "RW": "F", "W": "F", "F": "F",
    "D": "D", "LD": "D", "RD": "D",
    "G": "G",
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


def _estimate_signing_year(player):
    """Return the season start year when the contract was signed."""
    expiry = player.get("expiry_season")
    years = player.get("contract_years")
    if expiry and years and int(years) > 0:
        return int(expiry) - int(years)
    return int(CURRENT_SEASON)


def _build_training_data(pg, season):
    # Use all historical seasons for more training data. Each (player, season)
    # row is a separate sample: stats from that season paired with the player's
    # AAV normalised by the cap ceiling for that same season.
    all_rows = get_all_with_salary_historical()

    # Fall back to current-season-only if historical pull is empty
    if not all_rows:
        all_rows = get_all_with_salary(season)

    pool = [p for p in all_rows if _pos_group(p.get("position", "")) == pg]

    X, y = [], []
    seen = set()
    for p in pool:
        aav = _safe_float(p.get("aav"))
        if aav <= 0:
            continue
        stat_season = int(p.get("season", season))
        cap = get_cap_ceiling(stat_season)
        if cap <= 0:
            continue
        cap_pct = aav / cap
        feats = _extract_features(p, pg)
        if any(math.isnan(f) or math.isinf(f) for f in feats):
            continue
        # Deduplicate identical (player, season) rows
        key = (p.get("player_id"), stat_season)
        if key in seen:
            continue
        seen.add(key)
        X.append(feats)
        y.append(cap_pct)
    return X, y


def _use_gbr(pg, n_samples):
    """GBR only for forwards with enough data; Ridge for D/G always."""
    return pg == "F" and n_samples >= 30


def _train_model(pg, season):
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        import numpy as np

        X, y = _build_training_data(pg, season)
        min_samples = 5 if pg == "F" else 3
        if len(X) < min_samples:
            logger.warning(f"Not enough training data for {pg} model ({len(X)} samples)")
            return None

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)

        if _use_gbr(pg, len(X)):
            estimator = ("gbr", GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.08,
                max_depth=4,
                subsample=0.85,
                random_state=42,
            ))
        else:
            estimator = ("ridge", Ridge(alpha=1.0))

        model = Pipeline([("scaler", StandardScaler()), estimator])
        model.fit(X_arr, y_arr)
        algo = "GBR" if _use_gbr(pg, len(X)) else "Ridge"
        logger.info(f"Trained {pg} model ({algo}) on {len(X)} samples")
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

        current_cap = get_current_cap_ceiling()
        feats = _extract_features(player_stats, pg)
        X = np.array([feats], dtype=float)
        pred_pct = float(model.predict(X)[0])
        pred = pred_pct * current_cap

        n = len(_build_training_data(pg, season)[0])

        is_gbr = "gbr" in model.named_steps
        if is_gbr:
            # Bootstrap confidence interval via staged predictions
            n_est = len(model.named_steps["gbr"].estimators_)
            partial_preds = []
            step = max(1, n_est // 20)
            for i in range(step, n_est + 1, step):
                partial_pct = _partial_predict(model, X, i)
                if partial_pct is not None:
                    partial_preds.append(partial_pct * current_cap)

            if len(partial_preds) >= 3:
                arr = sorted(partial_preds)
                lo_idx = max(0, int(len(arr) * 0.1))
                hi_idx = min(len(arr) - 1, int(len(arr) * 0.9))
                low = arr[lo_idx]
                high = arr[hi_idx]
            else:
                low, high = pred * 0.85, pred * 1.15
        else:
            # Ridge: sample-count-based spread (wider when fewer samples)
            spread = 0.20 if n < 10 else (0.15 if n < 25 else 0.10)
            low, high = pred * (1 - spread), pred * (1 + spread)

        if n >= 20:
            confidence = "high"
        elif n >= 8:
            confidence = "medium"
        else:
            confidence = "low"

        rmse = _get_rmse(pg, season)
        return {
            "estimate": round(max(pred, 750000)),
            "low": round(max(low, 750000)),
            "high": round(max(high, 750000)),
            "confidence": confidence,
            "rmse_dollars": rmse,
            "algo": "GBR" if is_gbr else "Ridge",
            "position_group": pg,
            "n_samples": n,
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


def cross_validate_model(pg, season=None):
    """
    Run 5-fold cross-validation on the position group model.
    Returns dict with r2, rmse_dollars, n_samples — or None if insufficient data.
    """
    season = season or CURRENT_SEASON
    try:
        from sklearn.model_selection import KFold, cross_val_score
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        import numpy as np

        X, y = _build_training_data(pg, season)
        n = len(X)
        min_samples = 5 if pg == "F" else 3
        if n < min_samples:
            return {"r2": None, "rmse_dollars": None, "n_samples": n, "error": "too few samples"}

        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)

        if _use_gbr(pg, n):
            estimator = ("gbr", GradientBoostingRegressor(
                n_estimators=150, learning_rate=0.08,
                max_depth=4, subsample=0.85, random_state=42,
            ))
        else:
            estimator = ("ridge", Ridge(alpha=1.0))

        pipeline = Pipeline([("scaler", StandardScaler()), estimator])
        current_cap = get_current_cap_ceiling()

        n_splits = min(5, n)
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)

        r2_scores = cross_val_score(pipeline, X_arr, y_arr, cv=kf, scoring="r2")
        neg_rmse = cross_val_score(pipeline, X_arr, y_arr, cv=kf,
                                   scoring="neg_root_mean_squared_error")

        rmse_pct = float(-neg_rmse.mean())
        rmse_dollars = round(rmse_pct * current_cap)

        return {
            "n_samples": n,
            "n_folds": n_splits,
            "algo": "GBR" if _use_gbr(pg, n) else "Ridge",
            "r2_mean": round(float(r2_scores.mean()), 3),
            "r2_std": round(float(r2_scores.std()), 3),
            "rmse_dollars": rmse_dollars,
        }
    except ImportError:
        return {"error": "scikit-learn not available"}
    except Exception as e:
        logger.error(f"CV error for {pg}: {e}")
        return {"error": str(e)}


def invalidate_models():
    """Force model retraining on next prediction call."""
    _model_cache.clear()
    _rmse_cache.clear()


def _get_rmse(pg, season):
    """Return RMSE in dollars for a position group, running CV once and caching."""
    if pg not in _rmse_cache:
        result = cross_validate_model(pg, season)
        _rmse_cache[pg] = result.get("rmse_dollars")
    return _rmse_cache.get(pg)
