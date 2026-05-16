"""
Full ID audit: trace what IDs each player has across salary, stats_cache,
and player_index tables. Identify mismatches and contaminated stats.
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATABASE_PATH, CURRENT_SEASON
from database.seed_data import get_seed_players

conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row

TARGETS = ["mcdavid", "marner", "jones"]

print("=" * 70)
print("SPOT-CHECK: SALARY / STATS_CACHE / PLAYER_INDEX per target player")
print("=" * 70)

for name_frag in TARGETS:
    print(f"\n--- {name_frag.upper()} ---")

    sal_rows = conn.execute(
        "SELECT player_id, player_name, team, position, aav, source FROM salaries "
        "WHERE LOWER(player_name) LIKE ?", (f"%{name_frag}%",)
    ).fetchall()
    for r in sal_rows:
        print(f"  SALARY  id={r['player_id']}  name={r['player_name']}  pos={r['position']}  "
              f"aav=${r['aav']:,.0f}  source={r['source']}")

    # For each salary id, check stats_cache
    for r in sal_rows:
        sc = conn.execute(
            "SELECT player_id, position, stats_json FROM stats_cache WHERE player_id=? AND season=?",
            (r['player_id'], CURRENT_SEASON)
        ).fetchone()
        if sc:
            import json
            stats = json.loads(sc['stats_json'])
            print(f"  STATS   id={sc['player_id']}  pos={sc['position']}  "
                  f"pts60={stats.get('points_per_60',0):.2f}  "
                  f"g60={stats.get('goals_per_60',0):.2f}  "
                  f"CF%={stats.get('corsi_for_pct','?')}  "
                  f"toi={stats.get('toi_per_game',0):.1f}")
        else:
            print(f"  STATS   id={r['player_id']}  >>> NO STATS FOUND <<<")

    idx_rows = conn.execute(
        "SELECT nhl_id, name, team, position FROM player_index "
        "WHERE LOWER(name) LIKE ?", (f"%{name_frag}%",)
    ).fetchall()
    for r in idx_rows:
        print(f"  INDEX   id={r['nhl_id']}  name={r['name']}  team={r['team']}  pos={r['position']}")

print()
print("=" * 70)
print("SEED DATA IDs for targets")
print("=" * 70)
seed = get_seed_players()
for p in seed:
    if any(frag in p['name'].lower() for frag in TARGETS):
        print(f"  SEED  id={p['player_id']}  name={p['name']}  pos={p['position']}")

print()
print("=" * 70)
print("DUPLICATE STATS_CACHE ANALYSIS")
print("=" * 70)
# Find IDs in stats_cache that also appear in seed data
seed_ids = {p['player_id'] for p in seed}
sc_all = conn.execute(
    "SELECT player_id, position, stats_json FROM stats_cache WHERE season=?",
    (CURRENT_SEASON,)
).fetchall()

import json
seed_in_cache = []
moneypuck_in_cache = []
for row in sc_all:
    if row['player_id'] in seed_ids:
        seed_in_cache.append(row)
    else:
        moneypuck_in_cache.append(row)

print(f"stats_cache rows from SEED IDs: {len(seed_in_cache)}")
print(f"stats_cache rows from OTHER IDs (MoneyPuck): {len(moneypuck_in_cache)}")

print()
print("=" * 70)
print("POSITION MAPPING PROBLEMS")
print("=" * 70)
# Check what distinct position values are in the salary table
pos_counts = conn.execute(
    "SELECT position, COUNT(*) as n FROM salaries GROUP BY position ORDER BY n DESC"
).fetchall()
known_F = {"C","L","LW","R","RW"}
known_D = {"D"}
known_G = {"G"}
unmapped = []
for row in pos_counts:
    pos = row['position'] or ''
    if pos not in (known_F | known_D | known_G | {''}):
        unmapped.append((pos, row['n']))

print("Unmapped position values in salary table:")
for pos, n in unmapped:
    print(f"  '{pos}' -> {n} players — would default to 'F' position group")

print()
# Check what distinct positions exist in stats_cache
pos_counts_sc = conn.execute(
    "SELECT position, COUNT(*) as n FROM stats_cache WHERE season=? GROUP BY position ORDER BY n DESC",
    (CURRENT_SEASON,)
).fetchall()
print("Positions in stats_cache:")
for row in pos_counts_sc:
    print(f"  '{row['position']}' -> {row['n']}")

conn.close()
