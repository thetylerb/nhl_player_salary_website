"""
Standalone version of notebook 02 — run directly to bypass Jupyter kernel issues.
Input:  notebooks/data/raw_combined.csv
Output: notebooks/data/features_skaters.csv, notebooks/data/features_goalies.csv
"""
import os
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, 'data')

df = pd.read_csv(os.path.join(DATA_DIR, 'raw_combined.csv'))
print(f'Loaded: {len(df):,} rows x {len(df.columns)} cols')
print(f'Positions: {df["position"].value_counts().to_dict()}')

# ── 1. Cap-normalize target ──────────────────────────────────────────────────
CAP = {
    2019: 81_500_000,
    2020: 81_500_000,
    2021: 81_500_000,
    2022: 82_500_000,
    2023: 83_500_000,
    2024: 88_000_000,
    2025: 88_000_000,
}

df['cap_at_signing'] = df['start_year'].map(CAP)
df['aav_pct_cap']    = df['aav'] / df['cap_at_signing']

print('\nAAV as % of cap:')
print(df['aav_pct_cap'].describe().round(4))

# ── 2. Per-60 rates ──────────────────────────────────────────────────────────
def per60(count_col, ice_col, df):
    minutes = df[ice_col] / 60.0
    return np.where(minutes > 0, df[count_col] / minutes, 0.0)

df['goals_per60']       = per60('I_F_goals',           'icetime', df)
df['primaryA_per60']    = per60('I_F_primaryAssists',  'icetime', df)
df['points_per60']      = (
    per60('I_F_goals', 'icetime', df) +
    per60('I_F_primaryAssists', 'icetime', df) +
    per60('I_F_secondaryAssists', 'icetime', df)
)
df['xG_per60']          = per60('I_F_xGoals',          'icetime', df)
df['shots_per60']       = per60('I_F_shotsOnGoal',     'icetime', df)
df['hdGoals_per60']     = per60('I_F_highDangerGoals', 'icetime', df)
df['hits_per60']        = per60('I_F_hits',            'icetime', df)
df['takeaways_per60']   = per60('I_F_takeaways',       'icetime', df)
df['giveaways_per60']   = per60('I_F_giveaways',       'icetime', df)
df['blocks_per60']      = per60('shotsBlockedByPlayer','icetime', df)
df['penDiff_per60']     = (
    per60('penaltiesDrawn', 'icetime', df) -
    per60('penalties',      'icetime', df)
)

df['ev_goals_per60']    = per60('ev_I_F_goals',          'ev_icetime', df)
df['ev_primaryA_per60'] = per60('ev_I_F_primaryAssists', 'ev_icetime', df)
df['ev_xG_per60']       = per60('ev_I_F_xGoals',         'ev_icetime', df)

df['pp_goals_per60']    = per60('pp_I_F_goals',          'pp_icetime', df)
df['pp_primaryA_per60'] = per60('pp_I_F_primaryAssists', 'pp_icetime', df)
df['pp_xG_per60']       = per60('pp_I_F_xGoals',         'pp_icetime', df)

df['pk_goals_per60']    = per60('sh_I_F_goals',  'sh_icetime', df)
df['pk_xG_per60']       = per60('sh_I_F_xGoals', 'sh_icetime', df)

print('\nPer-60 rates created.')

# ── 3. On-ice % metrics ──────────────────────────────────────────────────────
def safe_pct(num, den):
    total = num + den
    return np.where(total > 0, num / total, 0.5)

df['xGF_pct']       = safe_pct(df['OnIce_F_xGoals'],       df['OnIce_A_xGoals'])
df['corsi_pct']     = safe_pct(df['OnIce_F_shotAttempts'],  df['OnIce_A_shotAttempts'])
df['ev_xGF_pct']    = safe_pct(df['ev_OnIce_F_xGoals'],     df['ev_OnIce_A_xGoals'])
df['ev_corsi_pct']  = safe_pct(df['ev_OnIce_F_shotAttempts'], df['ev_OnIce_A_shotAttempts'])

total_starts = (df['I_F_oZoneShiftStarts'] + df['I_F_dZoneShiftStarts'] +
                df['I_F_neutralZoneShiftStarts'])
df['ozone_start_pct'] = np.where(total_starts > 0,
                                  df['I_F_oZoneShiftStarts'] / total_starts, 0.5)

total_fo = df['faceoffsWon'] + df['faceoffsLost']
df['faceoff_pct'] = np.where(total_fo > 0, df['faceoffsWon'] / total_fo, np.nan)

df['pp_toi_share'] = np.where(df['icetime'] > 0, df['pp_icetime'] / df['icetime'], 0.0)
df['pk_toi_share'] = np.where(df['icetime'] > 0, df['sh_icetime'] / df['icetime'], 0.0)
df['ev_toi_share'] = np.where(df['icetime'] > 0, df['ev_icetime'] / df['icetime'], 0.0)

print('On-ice % metrics created.')

# ── 4. Durability & usage ────────────────────────────────────────────────────
df['gp_pct']         = df['games_played'] / 82.0
df['toi_per_game']   = (df['icetime'] / 60.0) / df['games_played']
df['age_at_signing'] = pd.to_numeric(df['age_at_signing'], errors='coerce')

# ── 5. Goalie metrics ────────────────────────────────────────────────────────
df['save_pct'] = np.where(
    df['ongoal'].notna() & (df['ongoal'] > 0),
    (df['ongoal'] - df['goals']) / df['ongoal'], np.nan
)
df['hd_save_pct'] = np.where(
    df['highDangerShots'].notna() & (df['highDangerShots'] > 0),
    (df['highDangerShots'] - df['highDangerGoals']) / df['highDangerShots'], np.nan
)
df['gsaa']      = np.where(df['xGoals'].notna(), df['xGoals'] - df['goals'], np.nan)
df['gsaa_per60'] = np.where(
    df['icetime'].notna() & (df['icetime'] > 0) & df['gsaa'].notna(),
    df['gsaa'] / (df['icetime'] / 60.0), np.nan
)
df['gaa'] = np.where(
    df['icetime'].notna() & (df['icetime'] > 0) & df['goals'].notna(),
    df['goals'] / (df['icetime'] / 60.0), np.nan
)
df['sa_per60'] = np.where(
    df['icetime'].notna() & (df['icetime'] > 0) & df['ongoal'].notna(),
    df['ongoal'] / (df['icetime'] / 60.0), np.nan
)

print('Goalie metrics created.')

# ── 6. Feature sets ──────────────────────────────────────────────────────────
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

# ── 7. Build position DataFrames ─────────────────────────────────────────────
FORWARD_POS = {'C', 'L', 'LW', 'R', 'RW', 'W', 'F'}
DEFENSE_POS = {'D', 'LD', 'RD'}

pos_upper  = df['position'].str.upper()
is_forward = pos_upper.isin(FORWARD_POS)
is_defense = pos_upper.isin(DEFENSE_POS)
is_goalie  = pos_upper == 'G'

META = ['player_name', 'position', 'stat_season', 'start_year', 'aav', 'cap_at_signing']

def build_df(mask, features, pos_group, label):
    sub = df[mask].copy()
    if 'faceoff_pct' in features:
        sub['faceoff_pct'] = sub['faceoff_pct'].fillna(0.5)
    cols = META + [TARGET] + [f for f in features if f in sub.columns]
    sub = sub[cols].copy()
    sub['position_group'] = pos_group
    null_count = sub[[f for f in features if f in sub.columns]].isnull().sum().sum()
    print(f'{label}: {len(sub):,} rows, {len(features)} features, {null_count} nulls')
    return sub

forwards = build_df(is_forward, FORWARD_FEATURES, 'F', 'Forwards')
defense  = build_df(is_defense, DEFENSE_FEATURES, 'D', 'Defensemen')
goalies  = build_df(is_goalie,  GOALIE_FEATURES,  'G', 'Goalies')

# ── 8. Fill nulls ─────────────────────────────────────────────────────────────
def fill_nulls(sub_df, features):
    sub = sub_df.copy()
    for col in [f for f in features if f in sub.columns]:
        if sub[col].isnull().any():
            sub[col] = sub[col].fillna(sub[col].median())
    return sub

forwards = fill_nulls(forwards, FORWARD_FEATURES)
defense  = fill_nulls(defense,  DEFENSE_FEATURES)
goalies  = fill_nulls(goalies,  GOALIE_FEATURES)

print('\nAfter null fill — remaining nulls:')
for name, sub, feats in [('Forwards', forwards, FORWARD_FEATURES),
                          ('Defense',  defense,  DEFENSE_FEATURES),
                          ('Goalies',  goalies,  GOALIE_FEATURES)]:
    n = sub[[f for f in feats if f in sub.columns]].isnull().sum().sum()
    print(f'  {name}: {n}')

# ── 9. Correlations ──────────────────────────────────────────────────────────
print('\n--- Forwards: top correlations with aav_pct_cap ---')
feat_cols = [f for f in FORWARD_FEATURES if f in forwards.columns]
corr = forwards[feat_cols + [TARGET]].corr()[TARGET].drop(TARGET).abs().sort_values(ascending=False)
print(corr.head(10).round(3).to_string())

print('\n--- Defensemen: top correlations with aav_pct_cap ---')
feat_cols = [f for f in DEFENSE_FEATURES if f in defense.columns]
corr = defense[feat_cols + [TARGET]].corr()[TARGET].drop(TARGET).abs().sort_values(ascending=False)
print(corr.head(10).round(3).to_string())

# ── 10. Spot check ────────────────────────────────────────────────────────────
print('\n--- Top 8 Forwards by AAV ---')
print(forwards.nlargest(8, 'aav')[
    ['player_name','start_year','aav','aav_pct_cap','goals_per60','points_per60','ev_xGF_pct','pp_toi_share','gp_pct']
].to_string(index=False))

print('\n--- Top 8 Defensemen by AAV ---')
print(defense.nlargest(8, 'aav')[
    ['player_name','start_year','aav','aav_pct_cap','primaryA_per60','ev_xGF_pct','pp_toi_share','gp_pct']
].to_string(index=False))

print('\n--- Goalies by AAV ---')
print(goalies.nlargest(10, 'aav')[
    ['player_name','start_year','aav','aav_pct_cap','save_pct','hd_save_pct','gsaa','gp_pct']
].to_string(index=False))

# ── 11. Export ────────────────────────────────────────────────────────────────
skaters = pd.concat([forwards, defense], ignore_index=True)

skaters_path = os.path.join(DATA_DIR, 'features_skaters.csv')
goalies_path = os.path.join(DATA_DIR, 'features_goalies.csv')

skaters.to_csv(skaters_path, index=False)
goalies.to_csv(goalies_path, index=False)

print(f'\nSaved: {len(skaters):,} skaters x {len(skaters.columns)} cols -> {skaters_path}')
print(f'Saved: {len(goalies):,} goalies  x {len(goalies.columns)} cols -> {goalies_path}')
print('\nDone.')
