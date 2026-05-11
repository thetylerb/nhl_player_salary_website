import requests
import json
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

NHL_BASE = "https://api-web.nhle.com/v1"
HEADERS = {"User-Agent": "NHLSalaryEstimator/1.0"}
TIMEOUT = 12

# All 32 NHL team abbreviations (2024-25)
ALL_TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WSH", "WPG",
]

_index_built = False
_index_lock = threading.Lock()


def search_players(query):
    """Search for players by name using local DB index (fast) then NHL API."""
    from database.db import search_player_index
    results = search_player_index(query, limit=20)
    if results:
        return [
            {
                "nhl_id": r["nhl_id"],
                "name": r["name"],
                "team": r.get("team", ""),
                "position": r.get("position", ""),
            }
            for r in results
        ]
    return []


def build_player_index_background():
    """Fetch all 32 team rosters and populate the local player_index table."""
    global _index_built
    with _index_lock:
        if _index_built:
            return
        _index_built = True

    from database.db import ensure_player_index_table, upsert_player_index, get_player_index_count

    ensure_player_index_table()
    if get_player_index_count() >= 500:
        logger.info("Player index already populated, skipping roster fetch")
        return

    logger.info("Building player search index from NHL rosters...")
    count = 0
    for team in ALL_TEAMS:
        try:
            url = f"{NHL_BASE}/roster/{team}/current"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for group in ("forwards", "defensemen", "goalies"):
                for p in data.get(group, []):
                    nhl_id = str(p.get("id", ""))
                    first = p.get("firstName", {}).get("default", "")
                    last = p.get("lastName", {}).get("default", "")
                    pos = p.get("positionCode", "")
                    if nhl_id and (first or last):
                        upsert_player_index(nhl_id, f"{first} {last}".strip(), team, pos)
                        count += 1
        except Exception as e:
            logger.warning(f"Roster fetch failed for {team}: {e}")

    logger.info(f"Player index built: {count} players from NHL rosters")


def get_player_landing(nhl_id):
    """Fetch full player landing page from NHL API."""
    try:
        url = f"{NHL_BASE}/player/{nhl_id}/landing"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to get player landing {nhl_id}: {e}")
        return None


def parse_skater_stats(landing):
    """Extract normalized skater stats from landing page."""
    try:
        info = {
            "nhl_id": str(landing.get("playerId", "")),
            "name": (
                landing.get("firstName", {}).get("default", "") + " " +
                landing.get("lastName", {}).get("default", "")
            ).strip(),
            "team": landing.get("currentTeamAbbrev", ""),
            "position": landing.get("positionCode", ""),
            "headshot_url": landing.get("headshot", ""),
            "birth_date": landing.get("birthDate", ""),
            "age": _calc_age(landing.get("birthDate", "")),
        }

        # Pull career info for experience
        career = landing.get("careerTotals", {}).get("regularSeason", {})
        seasons_played = landing.get("seasonTotals", [])
        nhl_seasons = [
            s for s in seasons_played
            if s.get("leagueAbbrev") == "NHL" and s.get("gameTypeId") == 2
        ]
        info["experience"] = len(nhl_seasons)

        # Current season stats
        featured = landing.get("featuredStats", {}).get("regularSeason", {})
        sub = featured.get("subSeason", featured.get("career", {}))

        gp = sub.get("gamesPlayed", 0) or 1
        goals = sub.get("goals", 0)
        assists = sub.get("assists", 0)
        points = sub.get("points", 0)
        plus_minus = sub.get("plusMinus", 0)
        toi_str = sub.get("timeOnIcePerGame", "00:00")
        toi = _toi_to_minutes(toi_str)
        pim = sub.get("pim", 0)

        toi_total_min = toi * gp
        goals_per_60 = (goals / toi_total_min * 60) if toi_total_min > 0 else 0
        assists_per_60 = (assists / toi_total_min * 60) if toi_total_min > 0 else 0
        points_per_60 = (points / toi_total_min * 60) if toi_total_min > 0 else 0

        info["stats"] = {
            "games_played": gp,
            "goals": goals,
            "assists": assists,
            "points": points,
            "plus_minus": plus_minus,
            "toi_per_game": round(toi, 2),
            "goals_per_60": round(goals_per_60, 2),
            "assists_per_60": round(assists_per_60, 2),
            "points_per_60": round(points_per_60, 2),
            # Advanced stats default to None; will be filled from MoneyPuck
            "corsi_for_pct": None,
            "xgf_pct": None,
            "penalty_diff_per_60": 0.0,
        }
        return info
    except Exception as e:
        logger.error(f"Failed to parse skater stats: {e}")
        return None


def parse_goalie_stats(landing):
    """Extract normalized goalie stats from landing page."""
    try:
        info = {
            "nhl_id": str(landing.get("playerId", "")),
            "name": (
                landing.get("firstName", {}).get("default", "") + " " +
                landing.get("lastName", {}).get("default", "")
            ).strip(),
            "team": landing.get("currentTeamAbbrev", ""),
            "position": "G",
            "headshot_url": landing.get("headshot", ""),
            "birth_date": landing.get("birthDate", ""),
            "age": _calc_age(landing.get("birthDate", "")),
        }

        seasons_played = landing.get("seasonTotals", [])
        nhl_seasons = [
            s for s in seasons_played
            if s.get("leagueAbbrev") == "NHL" and s.get("gameTypeId") == 2
        ]
        info["experience"] = len(nhl_seasons)

        featured = landing.get("featuredStats", {}).get("regularSeason", {})
        sub = featured.get("subSeason", featured.get("career", {}))

        gp = sub.get("gamesPlayed", 0) or 1
        gs = sub.get("gamesStarted", gp)
        gaa = sub.get("goalsAgainstAverage", 0.0)
        sv_pct = sub.get("savePctg", 0.0)

        info["stats"] = {
            "games_played": gp,
            "games_started": gs,
            "gaa": round(gaa, 3),
            "save_pct": round(sv_pct, 4),
            "quality_start_pct": None,  # filled from MoneyPuck
        }
        return info
    except Exception as e:
        logger.error(f"Failed to parse goalie stats: {e}")
        return None


def get_player_info(nhl_id):
    """High-level: fetch and parse player data from NHL API."""
    landing = get_player_landing(nhl_id)
    if not landing:
        return None

    position = landing.get("positionCode", "")
    if position == "G":
        return parse_goalie_stats(landing)
    else:
        return parse_skater_stats(landing)


def _calc_age(birth_date_str):
    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - bd.year - (
            (today.month, today.day) < (bd.month, bd.day)
        )
    except Exception:
        return 0


def _toi_to_minutes(toi_str):
    """Convert 'MM:SS' string to float minutes."""
    try:
        parts = str(toi_str).split(":")
        return int(parts[0]) + int(parts[1]) / 60
    except Exception:
        try:
            return float(toi_str) / 60  # already seconds?
        except Exception:
            return 0.0
