"""
Daily data pipeline:
  1. Download MoneyPuck season CSVs → fill stats_cache
  2. Attempt PuckPedia salary scrape → fill salaries table
  3. If scraping blocked → seed data already loaded at startup
"""

import csv
import io
import logging
import time
from datetime import datetime

import requests

from config import MONEYPUCK_BASE, CURRENT_SEASON
from database.db import upsert_stats, upsert_salary, get_db

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 30


# ─── MoneyPuck ──────────────────────────────────────────────────────────────

def fetch_moneypuck_skaters(season=None):
    season = season or CURRENT_SEASON
    url = f"{MONEYPUCK_BASE}/{season}/regular/skaters.csv"
    logger.info(f"Fetching MoneyPuck skaters: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return _parse_skater_csv(resp.text, season)
    except Exception as e:
        logger.warning(f"MoneyPuck skaters fetch failed: {e}")
        return 0


def fetch_moneypuck_goalies(season=None):
    season = season or CURRENT_SEASON
    url = f"{MONEYPUCK_BASE}/{season}/regular/goalies.csv"
    logger.info(f"Fetching MoneyPuck goalies: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return _parse_goalie_csv(resp.text, season)
    except Exception as e:
        logger.warning(f"MoneyPuck goalies fetch failed: {e}")
        return 0


def _parse_skater_csv(text, season):
    count = 0
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            if row.get("situation", "").lower() != "all":
                continue

            player_id = str(row.get("playerId", "")).strip()
            if not player_id:
                continue

            toi_sec = float(row.get("icetime", 0) or 0)
            toi_min = toi_sec / 60
            gp = int(row.get("games_played", 1) or 1)
            toi_per_game = (toi_min / gp) if gp else 0

            goals = float(row.get("I_F_goals", 0) or 0)
            primary_a = float(row.get("I_F_primaryAssists", 0) or 0)
            secondary_a = float(row.get("I_F_secondaryAssists", 0) or 0)
            assists = primary_a + secondary_a
            points = goals + assists

            drawn = float(row.get("I_F_penaltiesDrawn", row.get("I_F_PenaltiesDrawn", 0)) or 0)
            taken = float(row.get("I_F_PenaltiesTaken", row.get("penalties", 0)) or 0)

            cf = float(row.get("OnIce_F_corsiAttempts", row.get("I_F_shotsAttempted", 1)) or 1)
            ca = float(row.get("OnIce_A_corsiAttempts", 1) or 1)
            xgf = float(row.get("OnIce_F_xGoals", 1) or 1)
            xga = float(row.get("OnIce_A_xGoals", 1) or 1)

            toi_h = toi_sec / 3600 if toi_sec > 0 else 1

            stats = {
                "games_played": gp,
                "goals": int(goals),
                "assists": int(assists),
                "points": int(points),
                "toi_per_game": round(toi_per_game, 2),
                "goals_per_60": round(goals / toi_h, 2),
                "assists_per_60": round(assists / toi_h, 2),
                "points_per_60": round(points / toi_h, 2),
                "corsi_for_pct": round(cf / (cf + ca) * 100, 1) if (cf + ca) > 0 else 50.0,
                "xgf_pct": round(xgf / (xgf + xga) * 100, 1) if (xgf + xga) > 0 else 50.0,
                "penalty_diff_per_60": round((drawn - taken) / toi_h, 2),
                "plus_minus": 0,  # not in MoneyPuck all-sit CSV
            }

            position = row.get("position", "")
            upsert_stats(player_id, season, position, stats)
            count += 1
        except Exception as e:
            logger.debug(f"Skater row parse error: {e}")
    logger.info(f"MoneyPuck: stored {count} skater stat rows for season {season}")
    return count


def _parse_goalie_csv(text, season):
    count = 0
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            if row.get("situation", "").lower() != "all":
                continue

            player_id = str(row.get("playerId", "")).strip()
            if not player_id:
                continue

            toi_sec = float(row.get("icetime", 0) or 0)
            gp = int(row.get("games_played", 1) or 1)
            gs = int(row.get("games_started", gp) or gp)
            ga = float(row.get("goals_against", row.get("I_F_goalsAgainst", 0)) or 0)
            shots = float(row.get("shotsOnGoalAgainst", row.get("shots_against", 1)) or 1)
            saves = shots - ga
            toi_h = toi_sec / 3600 if toi_sec > 0 else 1
            gaa = round(ga / toi_h, 3) if toi_h > 0 else 0.0
            sv_pct = round(saves / shots, 4) if shots > 0 else 0.0

            # Quality start: approximated from high-danger data if available
            hd_shots = float(row.get("highDangerShotsAgainst", 0) or 0)
            hd_saves = float(row.get("highDangerSaves", 0) or 0)
            qs_pct = round(hd_saves / hd_shots, 3) if hd_shots > 0 else sv_pct

            stats = {
                "games_played": gp,
                "games_started": gs,
                "gaa": gaa,
                "save_pct": sv_pct,
                "quality_start_pct": qs_pct,
            }

            upsert_stats(player_id, season, "G", stats)
            count += 1
        except Exception as e:
            logger.debug(f"Goalie row parse error: {e}")
    logger.info(f"MoneyPuck: stored {count} goalie stat rows for season {season}")
    return count


# ─── PuckPedia scraper (best-effort) ────────────────────────────────────────

def scrape_puckpedia_salaries():
    """
    Attempt to scrape top contract data from PuckPedia.
    Returns number of players updated. On failure returns 0.
    """
    try:
        resp = requests.get(
            "https://puckpedia.com/salary/topcaps",
            headers=HEADERS, timeout=TIMEOUT
        )
        if resp.status_code != 200:
            logger.warning(f"PuckPedia returned {resp.status_code}, skipping scrape")
            return 0

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        count = 0

        # Look for contract rows (structure may change)
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            try:
                name = cells[1].get_text(strip=True)
                team = cells[2].get_text(strip=True)
                aav_text = cells[3].get_text(strip=True).replace("$", "").replace(",", "").strip()
                aav = float(aav_text)

                # Use name as placeholder ID since we don't have nhl_id from scrape
                player_id = _name_to_id(name)
                upsert_salary(
                    player_id, name, team, "", aav, None,
                    None, None, "UFA", source="puckpedia"
                )
                count += 1
            except Exception:
                continue

        logger.info(f"PuckPedia scrape: updated {count} salary records")
        return count
    except Exception as e:
        logger.warning(f"PuckPedia scrape failed: {e}")
        return 0


def _name_to_id(name):
    """Generate a stable synthetic ID from player name for scraped data."""
    return "scraped_" + name.lower().replace(" ", "_").replace("'", "")


# ─── Orchestrator ────────────────────────────────────────────────────────────

def run_daily_scrape():
    """Run full daily data pipeline. Called by APScheduler."""
    logger.info("Starting daily scrape...")
    start = time.time()
    stats_count = 0
    error = None

    try:
        stats_count += fetch_moneypuck_skaters()
        stats_count += fetch_moneypuck_goalies()
        scrape_puckpedia_salaries()
    except Exception as e:
        error = str(e)
        logger.error(f"Daily scrape error: {e}")

    elapsed = round(time.time() - start, 1)
    status = "error" if error else "success"

    conn = get_db()
    conn.execute(
        "INSERT INTO scrape_log (ran_at, status, players_updated, error) VALUES (CURRENT_TIMESTAMP,?,?,?)",
        (status, stats_count, error)
    )
    conn.commit()
    conn.close()
    logger.info(f"Daily scrape done in {elapsed}s — {stats_count} stat rows updated")
    return stats_count
