"""
Train final per-group-winner models on the full dataset and save to backend/models/.

Winners:
  Forwards   → GBR  (R²=0.813, RMSE=$1.26M)
  Defensemen → Ridge (R²=0.753, RMSE=$1.35M)
  Goalies    → Ridge (R²=0.363, RMSE=$2.00M)

Saves for each model:
  {group}_model.joblib     — trained sklearn Pipeline
  {group}_medians.json     — training-set feature medians (fallback for missing DB stats)
  {group}_features.json    — ordered feature list

Output: backend/models/
"""
import os, json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
import joblib

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(SCRIPT_DIR)
DATA_DIR    = os.path.join(SCRIPT_DIR, 'data')
MODELS_DIR  = os.path.join(REPO_ROOT, 'backend', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

TARGET = 'aav_pct_cap'

# ── Feature sets (must match run_feature_engineering.py) ─────────────────────
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

# ── Load data ─────────────────────────────────────────────────────────────────
skaters = pd.read_csv(os.path.join(DATA_DIR, 'features_skaters.csv'))
goalies = pd.read_csv(os.path.join(DATA_DIR, 'features_goalies.csv'))

forwards = skaters[skaters['position_group'] == 'F'].copy()
defense  = skaters[skaters['position_group'] == 'D'].copy()

for df in [forwards, defense, goalies]:
    df.dropna(subset=[TARGET], inplace=True)

print(f'Training samples: F={len(forwards)}, D={len(defense)}, G={len(goalies)}')

# ── Train and save ────────────────────────────────────────────────────────────
configs = [
    ('F', forwards, FORWARD_FEATURES,
     Pipeline([('scl', StandardScaler()),
               ('m', GradientBoostingRegressor(
                   n_estimators=200, max_depth=4, learning_rate=0.05,
                   subsample=0.8, random_state=42))])),
    ('D', defense, DEFENSE_FEATURES,
     Pipeline([('scl', StandardScaler()), ('m', Ridge(alpha=1.0))])),
    ('G', goalies, GOALIE_FEATURES,
     Pipeline([('scl', StandardScaler()), ('m', Ridge(alpha=1.0))])),
]

for group, df, features, model in configs:
    feat_cols = [f for f in features if f in df.columns]
    X = df[feat_cols].values
    y = df[TARGET].values

    model.fit(X, y)

    # Compute training-set medians for every feature (fallback at inference time)
    medians = {f: float(df[f].median()) for f in feat_cols}

    # Save model
    model_path   = os.path.join(MODELS_DIR, f'{group}_model.joblib')
    medians_path = os.path.join(MODELS_DIR, f'{group}_medians.json')
    feats_path   = os.path.join(MODELS_DIR, f'{group}_features.json')

    joblib.dump(model, model_path)
    with open(medians_path, 'w') as f:
        json.dump(medians, f, indent=2)
    with open(feats_path, 'w') as f:
        json.dump(feat_cols, f, indent=2)

    algo = 'GBR' if group == 'F' else 'Ridge'
    print(f'[{group}] {algo} trained on {len(X)} samples, {len(feat_cols)} features -> saved')

print(f'\nAll models saved to {MODELS_DIR}')
print('Files:')
for f in sorted(os.listdir(MODELS_DIR)):
    path = os.path.join(MODELS_DIR, f)
    size = os.path.getsize(path)
    print(f'  {f}  ({size:,} bytes)')
