import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
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
    conn.close()


def upsert_salary(player_id, name, team, position, aav, total_value,
                  contract_years, expiry_season, fa_type, source='seed'):
    conn = get_db()
    conn.execute('''
        INSERT INTO salaries
            (player_id, player_name, team, position, aav, total_value,
             contract_years, expiry_season, fa_type, source, scraped_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(player_id) DO UPDATE SET
            player_name=excluded.player_name,
            team=excluded.team,
            position=excluded.position,
            aav=excluded.aav,
            total_value=excluded.total_value,
            contract_years=excluded.contract_years,
            expiry_season=excluded.expiry_season,
            fa_type=excluded.fa_type,
            source=excluded.source,
            scraped_at=CURRENT_TIMESTAMP
    ''', (player_id, name, team, position, aav, total_value,
          contract_years, expiry_season, fa_type, source))
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
    """Return all players that have both a salary and cached stats."""
    conn = get_db()
    rows = conn.execute('''
        SELECT s.player_id, s.player_name, s.team, s.position, s.aav,
               s.fa_type, sc.stats_json
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


def upsert_player_index(nhl_id, name, team, position):
    conn = get_db()
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
