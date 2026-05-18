"""
Notebook 03 — Model Comparison
Tests Ridge, Lasso, ElasticNet, Random Forest, GBR, XGBoost, LightGBM, MLP
across Forwards, Defensemen, and Goalies using 5-fold cross-validation.
Metrics reported in dollars (RMSE, MAE) and R².
"""
import os, warnings
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import make_scorer, mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore')

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(SCRIPT_DIR, 'data')
CURRENT_CAP  = 88_000_000   # 2024/25 cap ceiling — for converting pct -> dollars

# ── Feature sets (must match notebook 02) ────────────────────────────────────
SHARED = ['age_at_signing', 'gp_pct', 'toi_per_game']

FORWARD_FEATURES = SHARED + [
    'goals_per60', 'primaryA_per60', 'points_per60', 'xG_per60',
    'shots_per60', 'hdGoals_per60',
    'ev_goals_per60', 'ev_xG_per60', 'ev_xGF_pct', 'ev_corsi_pct',
    'pp_goals_per60', 'pp_xG_per60', 'pp_toi_share',
    'faceoff_pct', 'ozone_start_pct',
    'hits_per60', 'takeaways_per60', 'penDiff_per60',
]
DEFENSE_FEATURES = SHARED + [
    'primaryA_per60', 'points_per60', 'xG_per60',
    'ev_xG_per60', 'ev_xGF_pct', 'ev_corsi_pct',
    'pp_primaryA_per60', 'pp_xG_per60', 'pp_toi_share',
    'pk_toi_share',
    'hits_per60', 'blocks_per60', 'takeaways_per60', 'giveaways_per60',
    'ozone_start_pct', 'penDiff_per60',
]
GOALIE_FEATURES = SHARED + [
    'save_pct', 'hd_save_pct', 'gsaa', 'gsaa_per60', 'gaa', 'sa_per60',
]

TARGET = 'aav_pct_cap'

# ── Load data ─────────────────────────────────────────────────────────────────
skaters = pd.read_csv(os.path.join(DATA_DIR, 'features_skaters.csv'))
goalies = pd.read_csv(os.path.join(DATA_DIR, 'features_goalies.csv'))

forwards = skaters[skaters['position_group'] == 'F'].copy()
defense  = skaters[skaters['position_group'] == 'D'].copy()

# Drop rows where target is NaN (contracts with unknown signing-year cap)
forwards = forwards[forwards[TARGET].notna()].copy()
defense  = defense[defense[TARGET].notna()].copy()
goalies  = goalies[goalies[TARGET].notna()].copy()

print(f'Training sets (after dropping NaN targets):')
print(f'  Forwards:   {len(forwards):,} rows')
print(f'  Defensemen: {len(defense):,} rows')
print(f'  Goalies:    {len(goalies):,} rows')

# ── Model definitions ─────────────────────────────────────────────────────────
# Linear models wrapped in Pipeline with StandardScaler
def make_models():
    return {
        'Ridge':        Pipeline([('scl', StandardScaler()), ('m', Ridge(alpha=1.0))]),
        'Lasso':        Pipeline([('scl', StandardScaler()), ('m', Lasso(alpha=0.001, max_iter=5000))]),
        'ElasticNet':   Pipeline([('scl', StandardScaler()), ('m', ElasticNet(alpha=0.001, l1_ratio=0.5, max_iter=5000))]),
        'RandomForest': RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=4, random_state=42),
        'GBR':          GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=42),
        'XGBoost':      xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8,
                                          colsample_bytree=0.8, random_state=42, verbosity=0),
        'LightGBM':     lgb.LGBMRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8,
                                           colsample_bytree=0.8, random_state=42, verbose=-1),
        'MLP':          Pipeline([('scl', StandardScaler()),
                                  ('m', MLPRegressor(hidden_layer_sizes=(64, 32), activation='relu',
                                                     max_iter=500, random_state=42, early_stopping=True))]),
    }

# ── CV evaluation ─────────────────────────────────────────────────────────────
def neg_rmse(y_true, y_pred):
    return -np.sqrt(mean_squared_error(y_true, y_pred))

scorers = {
    'rmse': make_scorer(neg_rmse),
    'mae':  make_scorer(lambda y, p: -mean_absolute_error(y, p)),
    'r2':   make_scorer(r2_score),
}

def evaluate_group(df, features, label, n_splits=5):
    feat_cols = [f for f in features if f in df.columns]
    X = df[feat_cols].values
    y = df[TARGET].values

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)

    print(f'\n{"="*60}')
    print(f'  {label}  ({len(df)} rows, {len(feat_cols)} features, {n_splits}-fold CV)')
    print(f'{"="*60}')
    print(f'{"Model":<14} {"RMSE ($M)":>10} {"MAE ($M)":>10} {"R²":>8}')
    print('-' * 46)

    results = {}
    for name, model in make_models().items():
        cv = cross_validate(model, X, y, cv=kf, scoring=scorers, return_train_score=False)
        rmse_m = -cv['test_rmse'].mean() * CURRENT_CAP / 1e6
        mae_m  = -cv['test_mae'].mean()  * CURRENT_CAP / 1e6
        r2     =  cv['test_r2'].mean()
        results[name] = {'rmse': rmse_m, 'mae': mae_m, 'r2': r2}
        print(f'{name:<14} {rmse_m:>9.2f}M {mae_m:>9.2f}M {r2:>8.3f}')

    best = min(results, key=lambda k: results[k]['rmse'])
    print(f'\n  Best model (lowest RMSE): {best}')
    print(f'  RMSE={results[best]["rmse"]:.2f}M  MAE={results[best]["mae"]:.2f}M  R²={results[best]["r2"]:.3f}')
    return results, best

# ── Run evaluations ───────────────────────────────────────────────────────────
f_results, f_best = evaluate_group(forwards, FORWARD_FEATURES, 'FORWARDS')
d_results, d_best = evaluate_group(defense,  DEFENSE_FEATURES, 'DEFENSEMEN')
g_results, g_best = evaluate_group(goalies,  GOALIE_FEATURES,  'GOALIES')

# ── Summary table ─────────────────────────────────────────────────────────────
print(f'\n{"="*60}')
print('  SUMMARY — Best model per group')
print(f'{"="*60}')
for label, results, best in [('Forwards',   f_results, f_best),
                               ('Defensemen', d_results, d_best),
                               ('Goalies',    g_results, g_best)]:
    r = results[best]
    print(f'  {label:<12} -> {best:<14}  RMSE={r["rmse"]:.2f}M  MAE={r["mae"]:.2f}M  R²={r["r2"]:.3f}')

# ── Full comparison table ranked by RMSE ─────────────────────────────────────
print(f'\n{"="*60}')
print('  FORWARDS — all models ranked by RMSE')
print(f'{"="*60}')
f_df = pd.DataFrame(f_results).T.sort_values('rmse')
f_df['rmse'] = f_df['rmse'].map('{:.2f}M'.format)
f_df['mae']  = f_df['mae'].map('{:.2f}M'.format)
f_df['r2']   = f_df['r2'].map('{:.3f}'.format)
print(f_df.to_string())

print(f'\n{"="*60}')
print('  DEFENSEMEN — all models ranked by RMSE')
print(f'{"="*60}')
d_df = pd.DataFrame(d_results).T.sort_values('rmse')
d_df['rmse'] = d_df['rmse'].map('{:.2f}M'.format)
d_df['mae']  = d_df['mae'].map('{:.2f}M'.format)
d_df['r2']   = d_df['r2'].map('{:.3f}'.format)
print(d_df.to_string())

print(f'\n{"="*60}')
print('  GOALIES — all models ranked by RMSE')
print(f'{"="*60}')
g_df = pd.DataFrame(g_results).T.sort_values('rmse')
g_df['rmse'] = g_df['rmse'].map('{:.2f}M'.format)
g_df['mae']  = g_df['mae'].map('{:.2f}M'.format)
g_df['r2']   = g_df['r2'].map('{:.3f}'.format)
print(g_df.to_string())

print('\nDone.')
