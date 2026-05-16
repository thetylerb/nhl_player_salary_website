"""Diagnostic: inspect training data quality and model predictions for key players."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CURRENT_SEASON
from database.db import get_all_with_salary, get_salary, get_stats
from services.regression import _build_training_data, _pos_group, predict_salary
from services.comparables import find_comparables

# ── Training data summary ─────────────────────────────────────────────────────
print("=" * 60)
print("TRAINING DATA SUMMARY")
print("=" * 60)
all_data = get_all_with_salary(CURRENT_SEASON)
print(f"Total players with both salary + stats: {len(all_data)}")

for pg in ["F", "D", "G"]:
    X, y = _build_training_data(pg, CURRENT_SEASON)
    if y:
        print(f"  {pg}: {len(y)} samples  |  AAV range: ${min(y):,.0f} – ${max(y):,.0f}  |  mean: ${sum(y)/len(y):,.0f}")
    else:
        print(f"  {pg}: 0 samples")

# ── Salary distribution check ─────────────────────────────────────────────────
print()
print("TOP 10 SALARIES IN TRAINING SET (F)")
X, y = _build_training_data("F", CURRENT_SEASON)
forwards = [p for p in all_data if _pos_group(p.get("position","")) == "F"]
forwards_sorted = sorted(forwards, key=lambda p: p["aav"], reverse=True)
for p in forwards_sorted[:10]:
    stats = p.get("stats", {})
    pts60 = stats.get("points_per_60", 0) or 0
    print(f"  {p['player_name']:<22} ${p['aav']:>12,.0f}  pts/60={pts60:.2f}  pos={p['position']}")

# ── McDavid specifically ───────────────────────────────────────────────────────
print()
print("=" * 60)
print("McDaVID DIAGNOSIS")
print("=" * 60)

# Find McDavid in salary table
from database.db import get_db
conn = get_db()
conn.row_factory = __import__('sqlite3').Row
mcd_row = conn.execute(
    "SELECT * FROM salaries WHERE LOWER(player_name) LIKE '%mcdavid%'"
).fetchone()
conn.close()

if mcd_row:
    mcd = dict(mcd_row)
    print(f"Salary record: {mcd['player_name']} | ID={mcd['player_id']} | AAV=${mcd['aav']:,.0f} | source={mcd['source']}")

    # Check if stats exist for this ID
    stats_row = get_stats(mcd['player_id'], CURRENT_SEASON)
    print(f"Stats in cache (id={mcd['player_id']}): {'YES' if stats_row else 'NO'}")
    if stats_row:
        s = stats_row['stats']
        print(f"  pts/60={s.get('points_per_60',0):.2f}  goals/60={s.get('goals_per_60',0):.2f}  CF%={s.get('corsi_for_pct',0)}")

    # Build player_stats as the estimate endpoint would
    player_stats = {
        "nhl_id": mcd['player_id'],
        "position": mcd.get('position') or 'C',
        "age": 27,
        "experience": 9,
        "fa_type": mcd.get('fa_type', 'UFA'),
        "stats": stats_row['stats'] if stats_row else {},
    }

    print()
    print("Regression prediction:")
    reg = predict_salary(player_stats)
    print(f"  estimate=${reg.get('estimate'):,.0f}  low=${reg.get('low'):,.0f}  high=${reg.get('high'):,.0f}  conf={reg.get('confidence')}")

    print()
    print("Comparables (top 5):")
    comp = find_comparables(player_stats, n=10)
    print(f"  Comparables estimate: ${comp.get('estimate'):,.0f}")
    for c in comp.get('comparables', [])[:5]:
        print(f"  {c['name']:<22} AAV=${c['aav']:>10,.0f}  sim={c['similarity']:.3f}  pts/60={c['stats'].get('points_per_60',0):.2f}")
else:
    print("McDavid NOT FOUND in salary table")

# ── Cap % analysis ─────────────────────────────────────────────────────────────
NHL_CAP_2024 = 88_000_000
print()
print("=" * 60)
print(f"CAP % ANALYSIS (2024-25 cap ceiling = ${NHL_CAP_2024:,})")
print("=" * 60)
if mcd_row:
    print(f"McDavid cap%: {mcd['aav']/NHL_CAP_2024*100:.1f}%")
forwards_sorted_short = forwards_sorted[:15]
for p in forwards_sorted_short:
    pct = p['aav'] / NHL_CAP_2024 * 100
    print(f"  {p['player_name']:<22} ${p['aav']:>12,.0f}  ({pct:.1f}% of cap)")
