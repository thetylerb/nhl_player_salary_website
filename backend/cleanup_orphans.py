"""
One-time cleanup:
- Delete orphaned salary records where the player_id no longer exists in player_index
  AND the source is 'puckpedia' (stale from old scrapes with wrong IDs).
- Delete stats_cache rows for seed IDs that are NOT in the current player_index
  (those IDs are no longer authoritative).
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATABASE_PATH, CURRENT_SEASON
from database.seed_data import get_seed_players

conn = sqlite3.connect(DATABASE_PATH)

# Seed IDs that are NOT real NHL player IDs in the current index
seed_ids = [p['player_id'] for p in get_seed_players()]
valid_index_ids = {
    r[0] for r in conn.execute("SELECT nhl_id FROM player_index").fetchall()
}

stale_seed_ids = [sid for sid in seed_ids if sid not in valid_index_ids]
print(f"Seed IDs not in current player_index (stale): {len(stale_seed_ids)}")

# Delete stale seed stats
if stale_seed_ids:
    placeholders = ",".join("?" * len(stale_seed_ids))
    deleted_stats = conn.execute(
        f"DELETE FROM stats_cache WHERE player_id IN ({placeholders})",
        stale_seed_ids
    ).rowcount
    print(f"Deleted {deleted_stats} stale seed stats rows")

# Delete orphaned puckpedia salary records (ID not in player_index, not a seed salary)
orphan_salaries = conn.execute("""
    SELECT player_id, player_name, source FROM salaries
    WHERE source = 'puckpedia'
    AND player_id NOT IN (SELECT nhl_id FROM player_index)
    AND player_id NOT LIKE 'pp_%'
""").fetchall()
print(f"Orphaned puckpedia salary records (ID not in index): {len(orphan_salaries)}")
for r in orphan_salaries[:10]:
    print(f"  {r[1]} id={r[0]}")

if orphan_salaries:
    ids = [r[0] for r in orphan_salaries]
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM salaries WHERE player_id IN ({placeholders})", ids)
    print(f"Deleted {len(orphan_salaries)} orphaned salary rows")

conn.commit()
conn.close()
print("\nCleanup complete.")
