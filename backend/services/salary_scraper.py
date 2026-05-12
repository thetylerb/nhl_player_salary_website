"""
Data pipeline:
  Daily  — MoneyPuck CSVs → stats_cache (CF%, xGF%, etc.)
  Weekly — PuckPedia team pages → salaries table (AAV, clauses, FA type)
"""

import csv
import io
import logging
import re
import time
import unicodedata
from datetime import datetime

import requests

from config import MONEYPUCK_BASE, CURRENT_SEASON, HISTORICAL_SEASON_START
from database.db import upsert_stats, upsert_salary, get_db, search_player_index, upsert_player_index

logger = logging.getLogger(__name__)

# In-process cache of the player_index with pre-normalized names.
# Rebuilt once per scrape run so accent-stripping happens in Python, not SQL.
_index_cache: list = []
_index_cache_dirty: bool = True   # force rebuild at start of each scrape


def _rebuild_index_cache():
    global _index_cache, _index_cache_dirty
    conn = get_db()
    rows = conn.execute("SELECT nhl_id, name, team, position FROM player_index").fetchall()
    conn.close()
    _index_cache = [
        {
            "nhl_id": r["nhl_id"],
            "name": r["name"],
            "name_norm": _normalize_name(r["name"]),
            "position": r["position"] or "",
        }
        for r in rows
    ]
    _index_cache_dirty = False
    logger.info(f"Player index cache rebuilt: {len(_index_cache)} entries")


_COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT = 30

PUCKPEDIA_BASE = "https://puckpedia.com"

# Full team-name slugs used by PuckPedia URLs (/team/<slug>)
PUCKPEDIA_TEAM_SLUGS = {
    "ANA": "anaheim-ducks",
    "BOS": "boston-bruins",
    "BUF": "buffalo-sabres",
    "CAR": "carolina-hurricanes",
    "CBJ": "columbus-blue-jackets",
    "CGY": "calgary-flames",
    "CHI": "chicago-blackhawks",
    "COL": "colorado-avalanche",
    "DAL": "dallas-stars",
    "DET": "detroit-red-wings",
    "EDM": "edmonton-oilers",
    "FLA": "florida-panthers",
    "LAK": "los-angeles-kings",
    "MIN": "minnesota-wild",
    "MTL": "montreal-canadiens",
    "NJD": "new-jersey-devils",
    "NSH": "nashville-predators",
    "NYI": "new-york-islanders",
    "NYR": "new-york-rangers",
    "OTT": "ottawa-senators",
    "PHI": "philadelphia-flyers",
    "PIT": "pittsburgh-penguins",
    "SEA": "seattle-kraken",
    "SJS": "san-jose-sharks",
    "STL": "st-louis-blues",
    "TBL": "tampa-bay-lightning",
    "TOR": "toronto-maple-leafs",
    "UTA": "utah-hc",
    "VAN": "vancouver-canucks",
    "VGK": "vegas-golden-knights",
    "WSH": "washington-capitals",
    "WPG": "winnipeg-jets",
}


# ─── MoneyPuck ───────────────────────────────────────────────────────────────

def fetch_moneypuck_skaters(season=None):
    season = season or CURRENT_SEASON
    url = f"{MONEYPUCK_BASE}/{season}/regular/skaters.csv"
    logger.info(f"Fetching MoneyPuck skaters: {url}")
    try:
        resp = requests.get(url, headers=_COMMON_HEADERS, timeout=TIMEOUT)
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
        resp = requests.get(url, headers=_COMMON_HEADERS, timeout=TIMEOUT)
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

            # Extended MoneyPuck columns
            ix_goals      = float(row.get("I_F_xGoals", 0) or 0)
            hd_goals      = float(row.get("I_F_highDangerGoals", 0) or 0)
            shots_on_goal = float(row.get("I_F_shotsOnGoal", 0) or 0)
            rebounds      = float(row.get("I_F_rebounds", 0) or 0)
            rush_att      = float(row.get("I_F_rush_attempts", 0) or 0)
            hits          = float(row.get("I_F_hits", 0) or 0)
            takeaways     = float(row.get("I_F_takeaways", 0) or 0)
            giveaways     = float(row.get("I_F_giveaways", 0) or 0)

            on_ice_hd_f   = float(row.get("OnIce_F_highDangerShots", 0) or 0)
            on_ice_hd_a   = float(row.get("OnIce_A_highDangerShots", 0) or 0)

            oz = float(row.get("offenseZoneStartsWith60", 0) or 0)
            dz = float(row.get("defenseZoneStartsWith60", 0) or 0)
            nz = float(row.get("neutralZoneStartsWith60", 0) or 0)
            total_starts  = oz + dz + nz

            stats = {
                "games_played": gp,
                "goals": int(goals),
                "assists": int(assists),
                "points": int(points),
                "toi_per_game": round(toi_per_game, 2),
                "goals_per_60": round(goals / toi_h, 2),
                "assists_per_60": round(assists / toi_h, 2),
                "points_per_60": round(points / toi_h, 2),
                "primary_points_per_60": round((goals + primary_a) / toi_h, 2),
                "ixg_per_60": round(ix_goals / toi_h, 2),
                "hd_goals_per_60": round(hd_goals / toi_h, 2),
                "shots_per_60": round(shots_on_goal / toi_h, 2),
                "rebounds_per_60": round(rebounds / toi_h, 2),
                "rush_attempts_per_60": round(rush_att / toi_h, 2),
                "hits_per_60": round(hits / toi_h, 2),
                "takeaway_giveaway_ratio": round(takeaways / max(giveaways, 1), 2),
                "corsi_for_pct": round(cf / (cf + ca) * 100, 1) if (cf + ca) > 0 else 50.0,
                "xgf_pct": round(xgf / (xgf + xga) * 100, 1) if (xgf + xga) > 0 else 50.0,
                "on_ice_hd_cf_pct": round(on_ice_hd_f / (on_ice_hd_f + on_ice_hd_a) * 100, 1) if (on_ice_hd_f + on_ice_hd_a) > 0 else 50.0,
                "zone_start_pct": round(oz / total_starts * 100, 1) if total_starts > 0 else 50.0,
                "penalty_diff_per_60": round((drawn - taken) / toi_h, 2),
                "plus_minus": 0,
            }
            position = row.get("position", "")
            upsert_stats(player_id, season, position, stats)

            # Also keep player_index current — covers traded/LTIR players
            # that aren't on any current NHL roster.
            # preserve_name=True so NHL roster API names (correct unicode) are
            # never overwritten by MoneyPuck CSV names (which drop some diacritics).
            mp_name = row.get("name", "").strip()
            mp_team = row.get("team", "").strip()
            if mp_name:
                upsert_player_index(player_id, mp_name, mp_team, position, preserve_name=True)

            count += 1
        except Exception as e:
            logger.debug(f"Skater row parse error: {e}")
    logger.info(f"MoneyPuck: stored {count} skater stat rows for season {season}")
    global _index_cache_dirty
    _index_cache_dirty = True   # index changed; force rebuild before next scrape
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

            hd_shots = float(row.get("highDangerShotsAgainst", 0) or 0)
            hd_saves = float(row.get("highDangerSaves", 0) or 0)
            qs_pct = round(hd_saves / hd_shots, 3) if hd_shots > 0 else sv_pct

            xga_total = float(row.get("xGoalsAgainst", row.get("xGoals_Against", 0)) or 0)
            gsaa = round(xga_total - ga, 2)  # positive = saved more than expected

            stats = {
                "games_played": gp,
                "games_started": gs,
                "gaa": gaa,
                "save_pct": sv_pct,
                "quality_start_pct": qs_pct,
                "gsaa": gsaa,
                "hd_save_pct": round(hd_saves / hd_shots, 4) if hd_shots > 0 else sv_pct,
                "toi_per_game": round((toi_sec / 60) / gp, 2) if gp > 0 else 0.0,
            }
            upsert_stats(player_id, season, "G", stats)

            mp_name = row.get("name", "").strip()
            mp_team = row.get("team", "").strip()
            if mp_name:
                upsert_player_index(player_id, mp_name, mp_team, "G", preserve_name=True)

            count += 1
        except Exception as e:
            logger.debug(f"Goalie row parse error: {e}")
    logger.info(f"MoneyPuck: stored {count} goalie stat rows for season {season}")
    global _index_cache_dirty
    _index_cache_dirty = True
    return count


# ─── PuckPedia team scraper ──────────────────────────────────────────────────

def _get_scraper():
    """Return a cloudscraper session (bypasses Cloudflare JS challenge)."""
    try:
        import cloudscraper
        return cloudscraper.create_scraper()
    except ImportError:
        logger.warning("cloudscraper not installed; falling back to requests (may be blocked by Cloudflare)")
        return requests.Session()


def scrape_all_puckpedia_teams():
    """Scrape all 32 NHL team cap pages from PuckPedia. Returns total contracts saved."""
    global _index_cache_dirty
    _index_cache_dirty = True   # always rebuild from current DB state before matching
    scraper = _get_scraper()
    total = 0
    failed = []
    for nhl_abbrev, slug in PUCKPEDIA_TEAM_SLUGS.items():
        count = _scrape_team_page(scraper, nhl_abbrev, slug)
        if count == 0:
            failed.append(nhl_abbrev)
        total += count
        time.sleep(1.5)

    if failed:
        logger.warning(f"PuckPedia: 0 contracts parsed for {', '.join(failed)}")
    logger.info(f"PuckPedia scrape complete: {total} contracts across {len(PUCKPEDIA_TEAM_SLUGS)} teams")
    return total


def _scrape_team_page(scraper, team_abbrev, slug):
    """Fetch and parse one PuckPedia team cap page."""
    url = f"{PUCKPEDIA_BASE}/team/{slug}"
    try:
        resp = scraper.get(url, headers=_COMMON_HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            logger.warning(f"PuckPedia {team_abbrev}: HTTP {resp.status_code} for {url}")
            return 0

        contracts = _parse_team_contracts(resp.text, team_abbrev)
        if not contracts:
            logger.warning(f"PuckPedia {team_abbrev}: 0 contracts parsed")
            return 0

        count = 0
        for c in contracts:
            player_id = _match_player_id(c["name"], team=team_abbrev) or (
                "pp_" + _normalize_name(c["name"]).replace(" ", "_")
            )
            # Prefer player_index position (from NHL API, always correct) over
            # PuckPedia scraped position, which stores shot hand (L/R) for goalies.
            scraped_pos = c.get("position", "")
            if not player_id.startswith("pp_"):
                idx_entry = next((e for e in _index_cache if e["nhl_id"] == player_id), None)
                position = (idx_entry["position"] if idx_entry and idx_entry["position"] else scraped_pos)
            else:
                position = scraped_pos
            upsert_salary(
                player_id=player_id,
                name=c["name"],
                team=team_abbrev,
                position=position,
                aav=c["aav"],
                total_value=(c["aav"] * c["years"]) if c.get("years") else None,
                contract_years=c.get("years"),
                expiry_season=c.get("expiry"),
                fa_type=c.get("fa_type", "UFA"),
                source="puckpedia",
                clauses=c.get("clauses"),
            )
            count += 1

        logger.info(f"PuckPedia {team_abbrev}: {count} contracts saved")
        return count

    except Exception as e:
        logger.warning(f"PuckPedia {team_abbrev} failed: {e}")
        return 0


def _parse_team_contracts(html, team_abbrev):
    """
    Parse all player contracts from a PuckPedia team page.

    PuckPedia structure (Drupal/Tailwind):
    - Multiple <table> elements per page; the ones we want have "Player" as
      the first <th> and season-year strings ("2025-26") as subsequent headers.
    - Each player <td> contains an <a class="pp_link"> for the name.
    - Salary cells have data-aav="$X,XXX,XXX" and data-ch="$0" on the expiry column.
    - Clause icons carry data-title="<i ...> No Movement Clause" etc.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    contracts = []
    seen_names = set()

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers or headers[0] != "Player":
            continue

        # Season column labels ("2025-26", "2026-27", …)
        season_cols = [h for h in headers[1:] if re.match(r'\d{4}-\d{2}', h)]

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if not cells:
                continue

            # ── Name ──────────────────────────────────────────────────────────
            name_tag = cells[0].find("a", class_="pp_link")
            if not name_tag:
                continue
            name_raw = name_tag.get_text(strip=True)   # "Last, First"
            if "," in name_raw:
                last, first = name_raw.split(",", 1)
                name = f"{first.strip()} {last.strip()}"
            else:
                name = name_raw.strip()

            if not name or name in seen_names:
                continue
            seen_names.add(name)

            # ── Position ──────────────────────────────────────────────────────
            # PuckPedia wraps pos in: pos<span class="uppercase font-bold">C</span>
            pos_label = cells[0].find("span", string=re.compile(r"^[CLRDWG]+$", re.I))
            position = ""
            # Walk spans after "pos" text
            for span in cells[0].find_all("span", class_="uppercase"):
                txt = span.get_text(strip=True)
                if re.match(r'^[A-Z,/]+$', txt) and len(txt) <= 6:
                    # Take first position listed (e.g. "C" from "C,LW")
                    position = txt.split(",")[0].strip()
                    break

            # ── AAV (first non-empty salary cell) ────────────────────────────
            aav = None
            salary_cells = cells[1:]
            for sc in salary_cells:
                aav_str = sc.get("data-aav", "")
                v = _parse_dollar(aav_str)
                if v and v > 0:
                    aav = v
                    break

            if not aav:
                continue

            # ── Clauses (from data-title on icons in any salary cell) ─────────
            clause_texts = set()
            for sc in salary_cells:
                for elem in sc.find_all(attrs={"data-title": True}):
                    raw_title = elem.get("data-title", "")
                    # Strip embedded HTML tags (e.g. <i class='...'></i>)
                    clean = re.sub(r'<[^>]+>', '', raw_title).strip()
                    if clean and any(kw in clean.lower() for kw in
                                     ("clause", "no movement", "no trade", "no-trade",
                                      "no-movement", "modified")):
                        clause_texts.add(clean)

            clauses = "; ".join(sorted(clause_texts)) if clause_texts else None

            # ── Expiry season + FA type ───────────────────────────────────────
            # The expiry cell has data-extract_ch='0' and text like "$0UFA" or "$0RFA"
            expiry = None
            fa_type = "UFA"
            for idx, sc in enumerate(salary_cells):
                is_zero = (
                    sc.get("data-extract_ch") == "0"
                    or sc.get("data-ch") == "$0"
                    or sc.get_text(strip=True).startswith("$0")
                )
                if is_zero:
                    if idx < len(season_cols):
                        expiry = _parse_expiry(season_cols[idx])
                    cell_text = sc.get_text(strip=True).upper()
                    if "RFA" in cell_text:
                        fa_type = "RFA"
                    elif "UFA" in cell_text:
                        fa_type = "UFA"
                    break

            # ── Remaining contract years ──────────────────────────────────────
            years = sum(
                1 for sc in salary_cells
                if (_parse_dollar(sc.get("data-aav", "")) or 0) > 0
            )

            contracts.append({
                "name": name,
                "aav": aav,
                "position": position,
                "fa_type": fa_type,
                "expiry": expiry,
                "years": years or None,
                "clauses": clauses,
            })

    return contracts


# ─── Name → NHL ID resolution ────────────────────────────────────────────────

def _normalize_name(name):
    """Strip accents, hyphens, apostrophes, lowercase — for comparison only."""
    name = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _match_player_id(name, team=None):
    """
    Look up real NHL ID by normalized name.

    Uses the in-process cache so normalization is done in Python (not SQL),
    which correctly handles accents, hyphens, and apostrophes that SQLite
    LIKE comparisons miss.  Matching order:
      1. Exact full-name match — prefer same team if provided (handles
         two players with identical names on different teams)
      2. Last name + first initial (handles Jr./suffix differences)
    """
    global _index_cache, _index_cache_dirty
    if _index_cache_dirty or not _index_cache:
        _rebuild_index_cache()

    norm = _normalize_name(name)
    if not norm:
        return None
    parts = norm.split()
    last = parts[-1] if parts else norm

    # Pass 1: exact normalized match
    candidates = [e for e in _index_cache if e["name_norm"] == norm]
    if candidates:
        if team:
            same_team = [e for e in candidates if e.get("team") == team]
            if same_team:
                return same_team[0]["nhl_id"]
            # No same-team match → return None so the caller assigns a pp_ ID.
            # Cross-team fallback is intentionally removed: it caused name
            # collisions (e.g. two players named Sebastian Aho on different teams)
            # to corrupt the matched player's salary record.
            # Traded players are handled correctly because the player_index is
            # rebuilt from live NHL rosters on every app startup.
            return None
        return candidates[0]["nhl_id"]

    # Pass 2: same last name + same first initial
    if len(parts) >= 2:
        first_initial = parts[0][0]
        candidates = [
            e for e in _index_cache
            if (lambda ep: ep and ep[-1] == last and ep[0][0] == first_initial)(
                e["name_norm"].split()
            )
        ]
        if candidates:
            if team:
                same_team = [e for e in candidates if e.get("team") == team]
                if same_team:
                    return same_team[0]["nhl_id"]
                return None
            return candidates[0]["nhl_id"]

    return None


# ─── Parse helpers ────────────────────────────────────────────────────────────

def _parse_dollar(text):
    if not text:
        return None
    text = str(text).strip().replace("$", "").replace(",", "")
    try:
        if text.upper().endswith("M"):
            return float(text[:-1]) * 1_000_000
        elif text.upper().endswith("K"):
            return float(text[:-1]) * 1_000
        v = float(text)
        return v  # may be 0, which is intentional for expiry detection
    except (ValueError, AttributeError):
        return None


def _parse_expiry(text):
    """'2026-27' → 2027,  '2027' → 2027."""
    if not text:
        return None
    m = re.search(r'(\d{4})-(\d{2})', text)
    if m:
        return int(m.group(1)) + 1
    m = re.search(r'\b(20\d{2})\b', text)
    return int(m.group(1)) if m else None


# ─── Orchestrators ────────────────────────────────────────────────────────────

def run_historical_stats_scrape(start_season=None):
    """Scrape MoneyPuck stats for all past seasons from start_season to current-1."""
    start = start_season or HISTORICAL_SEASON_START
    end = int(CURRENT_SEASON)  # stop before current (already handled by daily scrape)
    logger.info(f"Historical stats scrape: seasons {start} to {end - 1}")
    total = 0
    for yr in range(start, end):
        logger.info(f"Fetching season {yr}...")
        total += fetch_moneypuck_skaters(str(yr))
        total += fetch_moneypuck_goalies(str(yr))
    logger.info(f"Historical stats scrape complete: {total} rows")
    return total


def run_daily_scrape():
    """MoneyPuck stats only — runs every 24h via APScheduler."""
    logger.info("Daily stats scrape starting...")
    start = time.time()
    stats_count = 0
    error = None
    try:
        stats_count += fetch_moneypuck_skaters()
        stats_count += fetch_moneypuck_goalies()
    except Exception as e:
        error = str(e)
        logger.error(f"Daily scrape error: {e}")

    elapsed = round(time.time() - start, 1)
    _log_scrape("stats", "error" if error else "success", stats_count, error)
    logger.info(f"Daily stats scrape done in {elapsed}s — {stats_count} rows updated")
    return stats_count


def run_weekly_salary_scrape():
    """PuckPedia team scrape — runs once a week via APScheduler."""
    from services.regression import invalidate_models
    logger.info("Weekly salary scrape starting...")
    start = time.time()
    count = 0
    error = None
    try:
        count = scrape_all_puckpedia_teams()
        invalidate_models()
    except Exception as e:
        error = str(e)
        logger.error(f"Weekly salary scrape error: {e}")

    elapsed = round(time.time() - start, 1)
    _log_scrape("salary", "error" if error else "success", count, error)
    logger.info(f"Weekly salary scrape done in {elapsed}s — {count} contracts updated")
    return count


def _log_scrape(scrape_type, status, count, error):
    conn = get_db()
    conn.execute(
        "INSERT INTO scrape_log (ran_at, status, players_updated, error) VALUES (CURRENT_TIMESTAMP,?,?,?)",
        (f"{scrape_type}:{status}", count, error)
    )
    conn.commit()
    conn.close()
