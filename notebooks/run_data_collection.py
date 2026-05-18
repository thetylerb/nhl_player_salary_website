"""
Standalone version of notebook 01 — run directly to bypass Jupyter kernel cache issues.
Produces notebooks/data/raw_combined.csv
"""
import os, re, unicodedata, io, time, sys
import pandas as pd
import numpy as np
import requests

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.dirname(SCRIPT_DIR)
CSV_PATH    = os.path.join(REPO_ROOT, 'backend', 'data', 'nhl_contracts.csv')
HEADERS     = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
MP_BASE     = 'https://moneypuck.com/moneypuck/playerData/seasonSummary'
SEASONS     = [str(y) for y in range(2019, 2025)]
MIN_GP      = 40

# MoneyPuck situation column values (NOT 'pp'/'sh')
SIT_ALL  = 'all'
SIT_EV   = '5on5'
SIT_PP   = '5on4'   # power play: our team has 5, they have 4
SIT_PK   = '4on5'   # penalty kill: our team has 4, they have 5

def norm(name):
    name = unicodedata.normalize('NFD', str(name))
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9 ]', '', name.lower()).strip()

# Download cache — avoid re-hitting MoneyPuck for the same (season, ptype) CSV
_raw_csv_cache = {}

def get_raw_csv(season, ptype):
    key = (season, ptype)
    if key in _raw_csv_cache:
        return _raw_csv_cache[key]
    url = f'{MP_BASE}/{season}/regular/{ptype}.csv'
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text), low_memory=False)
        _raw_csv_cache[key] = df
        return df
    except Exception as e:
        print(f'  WARN {season}/{ptype}: {e}')
        _raw_csv_cache[key] = pd.DataFrame()
        return pd.DataFrame()

def fetch_mp(season, ptype, situation=SIT_ALL):
    df = get_raw_csv(season, ptype)
    if df.empty or 'situation' not in df.columns:
        return pd.DataFrame()
    return df[df['situation'] == situation].copy()

# ── 1. Load contracts ────────────────────────────────────────────────────────
print('Loading contracts...')
raw = pd.read_csv(CSV_PATH)
raw.columns = raw.columns.str.strip()

contracts = raw.rename(columns={
    'Player': 'player_name',
    'Pos': 'position',
    'Team                     Currently With': 'team',
    'Age                     At Signing': 'age_at_signing',
    'Start': 'start_year',
    'End': 'end_year',
    'Yrs': 'contract_years',
    'Value': 'total_value_raw',
    'AAV': 'aav_raw',
}).copy()

contracts['aav'] = (
    contracts['aav_raw']
    .str.replace(r'[\$,]', '', regex=True)
    .astype(float)
)
contracts['stat_season'] = contracts['start_year'].apply(
    lambda s: max(2019, min(int(s) - 1, 2024))
)
contracts['team'] = contracts['team'].str.strip()
contracts['player_name'] = contracts['player_name'].str.strip()

print(f'Contracts loaded: {len(contracts):,}')
print(f'Stat season distribution:')
print(contracts['stat_season'].value_counts().sort_index())

# ── 2. Build name lookup ─────────────────────────────────────────────────────
print('\nBuilding name lookup (skaters + goalies, all seasons)...')
name_to_id = {}
id_to_info  = {}

for season in SEASONS:
    for ptype in ['skaters', 'goalies']:
        df = fetch_mp(season, ptype)   # uses cache after first download
        if df.empty:
            continue
        for _, row in df.iterrows():
            pid  = str(int(row['playerId']))
            name = str(row.get('name', '')).strip()
            pos  = str(row.get('position', '')).strip()
            if name and pid:
                name_to_id[norm(name)] = pid
                id_to_info[pid] = {'name': name, 'position': pos}
    print(f'  {season}: {len(name_to_id)} unique names so far')

print(f'\nName lookup: {len(name_to_id):,} unique player names, {len(id_to_info):,} IDs')

# ── 3. Match contracts to IDs ────────────────────────────────────────────────
OVERRIDES = {
    'mats zuccarello aasen': 'mats zuccarello',
    'arseny gritsyuk':       'arseni gritsyuk',
    'anthony deangelo':      'anthony deangelo',
}

def match_player(name):
    n = norm(name)
    if n in OVERRIDES:
        n = OVERRIDES[n]
    if n in name_to_id:
        return name_to_id[n], 'exact'
    parts = n.split()
    if len(parts) >= 2:
        last, init = parts[-1], parts[0][0]
        candidates = [
            (k, v) for k, v in name_to_id.items()
            if (lambda p: p and len(p) >= 2 and p[-1] == last and p[0][0] == init)(k.split())
        ]
        if len(candidates) == 1:
            return candidates[0][1], 'last+initial'
        elif len(candidates) > 1:
            return candidates[0][1], 'last+initial (ambiguous)'
    return None, 'unmatched'

contracts['mp_id']        = None
contracts['match_method'] = None

for idx, row in contracts.iterrows():
    pid, method = match_player(row['player_name'])
    contracts.at[idx, 'mp_id']        = pid
    contracts.at[idx, 'match_method'] = method

print('\nMatch results:')
print(contracts['match_method'].value_counts())
matched   = contracts[contracts['mp_id'].notna()]
unmatched = contracts[contracts['mp_id'].isna()]
print(f'\nMatched: {len(matched):,} / {len(contracts):,} ({len(matched)/len(contracts)*100:.1f}%)')
print(f'Unmatched: {len(unmatched):,}')

# ── 4. Fetch all situation stats (cached — no duplicate downloads) ────────────
ALL_COLS = [
    'playerId','season','name','team','position','games_played','icetime','gameScore',
    'onIce_xGoalsPercentage','offIce_xGoalsPercentage',
    'onIce_corsiPercentage','offIce_corsiPercentage',
    'I_F_goals','I_F_primaryAssists','I_F_secondaryAssists',
    'I_F_xGoals','I_F_highDangerGoals','I_F_highDangerShots',
    'I_F_shotsOnGoal','I_F_rebounds',
    'I_F_hits','I_F_takeaways','I_F_giveaways','I_F_dZoneGiveaways',
    'penaltiesDrawn','penalties','shotsBlockedByPlayer',
    'faceoffsWon','faceoffsLost',
    'OnIce_F_xGoals','OnIce_A_xGoals',
    'OnIce_F_shotAttempts','OnIce_A_shotAttempts',
    'OnIce_F_highDangerShots','OnIce_A_highDangerShots',
    'I_F_oZoneShiftStarts','I_F_dZoneShiftStarts','I_F_neutralZoneShiftStarts',
]
GOALIE_ALL_COLS = [
    'playerId','season','name','team','position','games_played','icetime','gameScore',
    'shotsOnGoalAgainst','goalsAgainst',
    'xGoalsAgainst','highDangerShotsAgainst','highDangerGoalsAgainst',
    'highDangerSaves','lowDangerShotsAgainst','mediumDangerShotsAgainst',
    'games_started',
]
SPLIT_COLS = [
    'playerId','season','situation','icetime',
    'I_F_goals','I_F_primaryAssists','I_F_secondaryAssists','I_F_xGoals',
    'OnIce_F_xGoals','OnIce_A_xGoals',
    'OnIce_F_shotAttempts','OnIce_A_shotAttempts',
]

def safe_cols(df, wanted):
    return [c for c in wanted if c in df.columns]

print('\nBuilding per-situation stat frames (using cached downloads)...')
mp_frames = {}

for season in SEASONS:
    for ptype in ['skaters', 'goalies']:
        for sit in [SIT_ALL, SIT_EV, SIT_PP, SIT_PK]:
            df = fetch_mp(season, ptype, sit)
            if not df.empty:
                if ptype == 'goalies' and sit == SIT_ALL:
                    df = df[safe_cols(df, GOALIE_ALL_COLS)]
                elif sit == SIT_ALL:
                    df = df[safe_cols(df, ALL_COLS)]
                else:
                    df = df[safe_cols(df, SPLIT_COLS)]
                df = df.copy()
                df['season'] = season
                df['playerId'] = df['playerId'].astype(int).astype(str)
                mp_frames[(season, ptype, sit)] = df

for season in SEASONS:
    counts = {sit: len(mp_frames.get((season, 'skaters', sit), pd.DataFrame()))
              for sit in [SIT_ALL, SIT_EV, SIT_PP, SIT_PK]}
    print(f'  {season} skaters: all={counts[SIT_ALL]}, 5on5={counts[SIT_EV]}, pp={counts[SIT_PP]}, pk={counts[SIT_PK]}')

# ── 5. Build per-player-season rows ─────────────────────────────────────────
def prefix_df(df, prefix):
    keep = {'playerId', 'season', 'situation'}
    rename = {c: f'{prefix}_{c}' for c in df.columns if c not in keep}
    return df.drop(columns=['situation'], errors='ignore').rename(columns=rename)

skater_seasons = []
for season in SEASONS:
    base = mp_frames.get((season, 'skaters', SIT_ALL), pd.DataFrame())
    if base.empty:
        continue
    merged = base.copy()
    for sit, pfx in [(SIT_EV, 'ev'), (SIT_PP, 'pp'), (SIT_PK, 'sh')]:
        split = mp_frames.get((season, 'skaters', sit), pd.DataFrame())
        if not split.empty:
            split_p = prefix_df(split, pfx)
            merged = merged.merge(split_p, on=['playerId', 'season'], how='left')
    skater_seasons.append(merged)

goalie_seasons = []
for season in SEASONS:
    g = mp_frames.get((season, 'goalies', SIT_ALL), pd.DataFrame())
    if not g.empty:
        goalie_seasons.append(g)

skaters_all_seasons = pd.concat(skater_seasons, ignore_index=True) if skater_seasons else pd.DataFrame()
goalies_all_seasons  = pd.concat(goalie_seasons, ignore_index=True) if goalie_seasons  else pd.DataFrame()

print(f'\nSkater rows (all seasons): {len(skaters_all_seasons):,}')
print(f'Goalie rows (all seasons): {len(goalies_all_seasons):,}')
pp_cols = [c for c in skaters_all_seasons.columns if c.startswith('pp_')]
sh_cols = [c for c in skaters_all_seasons.columns if c.startswith('sh_')]
ev_cols = [c for c in skaters_all_seasons.columns if c.startswith('ev_')]
print(f'ev_ columns: {len(ev_cols)}, pp_ columns: {len(pp_cols)}, sh_ columns: {len(sh_cols)}')

# ── 6. Join contracts to stats ───────────────────────────────────────────────
matched_contracts = contracts[contracts['mp_id'].notna()].copy()
matched_contracts['stat_season'] = matched_contracts['stat_season'].astype(str)
matched_contracts['is_goalie'] = matched_contracts['position'].str.upper() == 'G'

skater_contracts = matched_contracts[~matched_contracts['is_goalie']].copy()
goalie_contracts = matched_contracts[ matched_contracts['is_goalie']].copy()

skaters_all_seasons['playerId'] = skaters_all_seasons['playerId'].astype(str)
skaters_all_seasons['season']   = skaters_all_seasons['season'].astype(str)
goalies_all_seasons['playerId'] = goalies_all_seasons['playerId'].astype(str)
goalies_all_seasons['season']   = goalies_all_seasons['season'].astype(str)

joined_skaters = skater_contracts.merge(
    skaters_all_seasons,
    left_on  = ['mp_id', 'stat_season'],
    right_on = ['playerId', 'season'],
    how='left',
    suffixes=('', '_mp')
)
joined_goalies = goalie_contracts.merge(
    goalies_all_seasons,
    left_on  = ['mp_id', 'stat_season'],
    right_on = ['playerId', 'season'],
    how='left',
    suffixes=('', '_mp')
)

combined = pd.concat([joined_skaters, joined_goalies], ignore_index=True)
print(f'\nAfter join: {len(combined):,} rows')
print(f'  Has stats: {combined["games_played"].notna().sum():,}')
print(f'  No stats:  {combined["games_played"].isna().sum():,}')

# ── 7. GP filter ─────────────────────────────────────────────────────────────
has_stats = combined[combined['games_played'].notna()].copy()
before_gp = len(has_stats)
has_stats = has_stats[has_stats['games_played'] >= MIN_GP].copy()
after_gp  = len(has_stats)

print(f'\nGP >= {MIN_GP} filter: {before_gp:,} -> {after_gp:,} (dropped {before_gp - after_gp:,})')
print(f'FINAL TRAINING ROWS: {after_gp:,}')

# Use 'position' from contracts (not the MoneyPuck copy)
pos_col = 'position' if 'position' in has_stats.columns else 'position_mp'
print('\nBy position:')
print(has_stats[pos_col].value_counts())

# ── 8. Export ────────────────────────────────────────────────────────────────
out_dir  = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'raw_combined.csv')

has_stats.to_csv(out_path, index=False)

print(f'\nSaved {len(has_stats):,} rows x {len(has_stats.columns)} columns -> {out_path}')
print()
print('Spot check (known players):')
check = ['Connor McDavid','Nathan MacKinnon','Auston Matthews','Cale Makar','Igor Shesterkin']
spot_cols = ['player_name','stat_season','position','games_played','I_F_goals','aav']
existing = [c for c in spot_cols if c in has_stats.columns]
spot = has_stats[has_stats['player_name'].isin(check)][existing].sort_values(['player_name','stat_season'])
print(spot.to_string())
print()
print('Null audit (pp_/sh_ columns):')
for pfx in ['pp_', 'sh_', 'ev_']:
    cols = [c for c in has_stats.columns if c.startswith(pfx)]
    if cols:
        null_rate = has_stats[cols].isnull().mean().mean() * 100
        print(f'  {pfx}: {len(cols)} cols, avg null rate {null_rate:.1f}%')
    else:
        print(f'  {pfx}: NO COLUMNS FOUND')
print('\nDone.')
