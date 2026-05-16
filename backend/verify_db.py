import sqlite3
from config import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row

total = conn.execute("SELECT COUNT(*) FROM salaries").fetchone()[0]
with_clauses = conn.execute("SELECT COUNT(*) FROM salaries WHERE clauses IS NOT NULL").fetchone()[0]
print(f"Total salary records: {total}")
print(f"Players with clauses: {with_clauses}")
print()

rows = conn.execute("SELECT player_name, team, aav, fa_type, expiry_season, clauses FROM salaries WHERE clauses IS NOT NULL LIMIT 10").fetchall()
for r in rows:
    print(f"{r['player_name']} ({r['team']}) AAV=${r['aav']:,.0f} {r['fa_type']} exp={r['expiry_season']} | {r['clauses']}")

print()
jan = conn.execute("SELECT player_name, team, aav, clauses FROM salaries WHERE LOWER(player_name) LIKE '%jankowski%'").fetchone()
print("Jankowski:", dict(jan) if jan else "not found")

mcd = conn.execute("SELECT player_name, team, aav, clauses, fa_type FROM salaries WHERE LOWER(player_name) LIKE '%mcdavid%'").fetchone()
print("McDavid:", dict(mcd) if mcd else "not found")
conn.close()
