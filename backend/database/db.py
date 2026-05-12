import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, CURRENT_SEASON

# Historical NHL salary cap ceilings by season start year (e.g. 2024 = 2024-25 season)
_CAP_CEILINGS = {
    2005: 39_000_000,
    2006: 44_000_000,
    2007: 50_300_000,
    2008: 56_700_000,
    2009: 56_800_000,
    2010: 59_400_000,
    2011: 64_300_000,
    2012: 70_200_000,
    2013: 64_300_000,
    2014: 69_000_000,
    2015: 71_400_000,
    2016: 73_000_000,
    2017: 75_000_000,
    2018: 79_500_000,
    2019: 81_500_000,
    2020: 81_500_000,
    2021: 81_500_000,
    2022: 82_500_000,
    2023: 83_500_000,
    2024: 88_000_000,
    2025: 95_500_000,
    2026: 104_800_000,
    2027: 113_500_000,
}


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS cap_ceilings (
            season_year INTEGER PRIMARY KEY,
            cap_ceiling  REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS salaries (
            player_id   TEXT PRIMARY KEY,
            player_name TEXT NOT NULL,
            team        TEXT,
            position    TEXT,
            aav         REAL,
            total_value REAL,
            contract_years INTEGER,
            expiry_season  INTEGER,
            fa_type     TEXT,
            clauses     TEXT,
            source      TEXT DEFAULT 'seed',
            scraped_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stats_cache (
            player_id TEXT NOT NULL,
            season    TEXT NOT NULL,
            position  TEXT,
            stats_json TEXT,
            cached_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, season)
        );

        CREATE TABLE IF NOT EXISTS scrape_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status     TEXT,
            players_updated INTEGER DEFAULT 0,
            error      TEXT
        );
    ''')
    conn.commit()
    # Migrate existing databases that predate the clauses column
    try:
        c.execute("ALTER TABLE salaries ADD COLUMN clauses TEXT")
        conn.commit()
    except Exception:
        pass
    conn.close()


def seed_cap_ceilings():
    """Populate cap_ceilings table from the built-in historical data (idempotent)."""
    conn = get_db()
    conn.executemany(
        "INSERT OR IGNORE INTO cap_ceilings (season_year, cap_ceiling) VALUES (?,?)",
        list(_CAP_CEILINGS.items()),
    )
    conn.commit()
    conn.close()


def get_cap_ceiling(season_year):
    """Return cap ceiling for a given season start year. Falls back to table min/max."""
    conn = get_db()
    row = conn.execute(
        "SELECT cap_ceiling FROM cap_ceilings WHERE season_year=?", (int(season_year),)
    ).fetchone()
    conn.close()
    if row:
        return float(row[0])
    # Clamp to nearest known year
    year = int(season_year)
    if year < min(_CAP_CEILINGS):
        return float(_CAP_CEILINGS[min(_CAP_CEILINGS)])
    return float(_CAP_CEILINGS[max(_CAP_CEILINGS)])


def get_current_cap_ceiling():
    """Return the cap ceiling for the current season."""
    return get_cap_ceiling(int(CURRENT_SEASON))


def upsert_salary(player_id, name, team, position, aav, total_value,
                  contract_years, expiry_season, fa_type, source='seed', clauses=None):
    conn = get_db()
    conn.execute('''
        INSERT INTO salaries
            (player_id, player_name, team, position, aav, total_value,
             contract_years, expiry_season, fa_type, clauses, source, scraped_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(player_id) DO UPDATE SET
            player_name=excluded.player_name,
            team=excluded.team,
            position=excluded.position,
            aav=excluded.aav,
            total_value=excluded.total_value,
            contract_years=excluded.contract_years,
            expiry_season=excluded.expiry_season,
            fa_type=excluded.fa_type,
            clauses=excluded.clauses,
            source=excluded.source,
            scraped_at=CURRENT_TIMESTAMP
    ''', (player_id, name, team, position, aav, total_value,
          contract_years, expiry_season, fa_type, clauses, source))
    conn.commit()
    conn.close()


def upsert_stats(player_id, season, position, stats_dict):
    conn = get_db()
    conn.execute('''
        INSERT INTO stats_cache (player_id, season, position, stats_json, cached_at)
        VALUES (?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(player_id, season) DO UPDATE SET
            position=excluded.position,
            stats_json=excluded.stats_json,
            cached_at=CURRENT_TIMESTAMP
    ''', (player_id, season, position, json.dumps(stats_dict)))
    conn.commit()
    conn.close()


def get_salary(player_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM salaries WHERE player_id=?', (player_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats(player_id, season):
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM stats_cache WHERE player_id=? AND season=?',
        (player_id, season)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['stats'] = json.loads(d['stats_json'])
        return d
    return None


def get_all_with_salary(season):
    """Return all players that have both a salary and cached stats for one season."""
    conn = get_db()
    rows = conn.execute('''
        SELECT s.player_id, s.player_name, s.team,
               COALESCE(NULLIF(sc.position, ''), NULLIF(s.position, ''), '') AS position,
               s.aav, s.fa_type, s.expiry_season, s.contract_years, sc.stats_json,
               sc.season
        FROM salaries s
        JOIN stats_cache sc ON sc.player_id = s.player_id AND sc.season = ?
        WHERE s.aav IS NOT NULL AND s.aav > 0
    ''', (season,)).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['stats'] = json.loads(d['stats_json'])
        result.append(d)
    return result


def get_all_with_salary_historical():
    """Return all (player, season) combos that have a salary and stats — every season."""
    conn = get_db()
    rows = conn.execute('''
        SELECT s.player_id, s.player_name, s.team,
               COALESCE(NULLIF(sc.position, ''), NULLIF(s.position, ''), '') AS position,
               s.aav, s.fa_type, s.expiry_season, s.contract_years, sc.stats_json,
               sc.season
        FROM salaries s
        JOIN stats_cache sc ON sc.player_id = s.player_id
        WHERE s.aav IS NOT NULL AND s.aav > 0
    ''').fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['stats'] = json.loads(d['stats_json'])
        result.append(d)
    return result


def get_salary_count():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM salaries').fetchone()[0]
    conn.close()
    return count


def get_stats_count(season):
    conn = get_db()
    count = conn.execute(
        'SELECT COUNT(*) FROM stats_cache WHERE season=?', (season,)
    ).fetchone()[0]
    conn.close()
    return count


# ─── Player search index ──────────────────────────────────────────────────────

def ensure_player_index_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS player_index (
            nhl_id   TEXT PRIMARY KEY,
            name     TEXT NOT NULL,
            team     TEXT,
            position TEXT
        )
    ''')
    conn.commit()
    conn.close()


def upsert_player_index(nhl_id, name, team, position, preserve_name=False):
    """
    Upsert a player into the index.
    preserve_name=True: only update team/position on conflict, not the name.
    Use this when the name source is less reliable than what's already stored
    (e.g. MoneyPuck CSVs drop some diacritic characters).
    """
    conn = get_db()
    if preserve_name:
        conn.execute('''
            INSERT INTO player_index (nhl_id, name, team, position)
            VALUES (?,?,?,?)
            ON CONFLICT(nhl_id) DO UPDATE SET
                team=excluded.team, position=excluded.position
        ''', (str(nhl_id), name, team, position))
    else:
        conn.execute('''
            INSERT INTO player_index (nhl_id, name, team, position)
            VALUES (?,?,?,?)
            ON CONFLICT(nhl_id) DO UPDATE SET
                name=excluded.name, team=excluded.team, position=excluded.position
        ''', (str(nhl_id), name, team, position))
    conn.commit()
    conn.close()


def search_player_index(query, limit=20):
    conn = get_db()
    q = f'%{query.lower()}%'
    rows = conn.execute(
        "SELECT nhl_id, name, team, position FROM player_index WHERE LOWER(name) LIKE ? LIMIT ?",
        (q, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_player_index_count():
    conn = get_db()
    n = conn.execute('SELECT COUNT(*) FROM player_index').fetchone()[0]
    conn.close()
    return n


def clear_player_index():
    conn = get_db()
    conn.execute('DELETE FROM player_index')
    conn.commit()
    conn.close()


def delete_stats_for_ids(player_ids):
    """Remove stats_cache rows for a specific set of player IDs."""
    if not player_ids:
        return
    conn = get_db()
    placeholders = ",".join("?" * len(player_ids))
    conn.execute(f'DELETE FROM stats_cache WHERE player_id IN ({placeholders})', list(player_ids))
    conn.commit()
    conn.close()
