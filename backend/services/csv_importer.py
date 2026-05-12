"""
CSV contract importer.

Reads an NHL contracts CSV (columns: Player, Pos, Team Currently With,
Age At Signing, Start, End, Yrs, Value, AAV), matches each row to a real
NHL API player ID via the player_index, and upserts into the salaries table.

All historical rows are kept for model training; only the most recent active
contract per player is used for salary display (via the salaries table, which
stores one row per player_id).
"""

import csv
import io
import logging
import re
import unicodedata

from database.db import get_db, upsert_salary
from config import CURRENT_SEASON

logger = logging.getLogger(__name__)

_TEAM_ALIASES = {
    "WAS": "WSH", "TB": "TBL", "SJ": "SJS", "NJ": "NJD",
    "LA": "LAK", "CLB": "CBJ", "PHX": "ARI", "ARI": "UTA",
}


def _normalize(name):
    """Lowercase, remove accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_name).strip().lower()


def _parse_dollars(s):
    """'$14,000,000' → 14000000.0"""
    if not s:
        return None
    cleaned = re.sub(r"[$,\s]", "", s)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_team(raw):
    """'MIN                  MIN' → 'MIN'"""
    parts = raw.strip().split()
    if parts:
        t = parts[0].upper()
        return _TEAM_ALIASES.get(t, t)
    return ""


def _fa_type(age_at_signing, contract_start, contract_end):
    """
    Approximate UFA/RFA based on age at signing.
    NHL RFA threshold: typically signed before age 27 or with fewer than
    7 accrued seasons (~age 25 first ELC).  We use age >= 27 → UFA.
    """
    try:
        age = int(age_at_signing)
    except (TypeError, ValueError):
        age = 28
    return "UFA" if age >= 27 else "RFA"


def _load_index():
    """Return list of player_index rows as dicts."""
    conn = get_db()
    rows = conn.execute(
        "SELECT nhl_id, name, name_norm, team FROM player_index"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _match_player(name_norm, team, index):
    """
    Try to find an NHL ID in the player_index.
    Priority: exact name + same team → exact name (any team).
    Returns nhl_id string or None.
    """
    candidates = [e for e in index if e["name_norm"] == name_norm]
    if not candidates:
        return None
    same_team = [e for e in candidates if e.get("team") == team]
    if same_team:
        return same_team[0]["nhl_id"]
    # One candidate with no team ambiguity
    if len(candidates) == 1:
        return candidates[0]["nhl_id"]
    # Multiple candidates, different teams — can't resolve safely
    return None


def import_contracts_from_stream(stream, filename="upload"):
    """
    Parse a CSV file-like object and upsert contracts into the salaries table.

    Returns a summary dict:
      matched   — rows written with a real NHL ID
      unmatched — rows where name lookup failed (stored with pp_<name> ID)
      skipped   — rows with no AAV / parse errors
      total     — total rows in CSV
      unmatched_names — list of names that didn't match
    """
    text = stream.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))

    # Normalise column names — strip whitespace from headers
    rows = []
    for row in reader:
        rows.append({k.strip(): v for k, v in row.items()})

    index = _load_index()
    index_count = len(index)
    logger.info(f"CSV import: {len(rows)} rows, player_index has {index_count} entries")

    # Group by player name and keep the most-recent contract per player
    # (highest End year) for the salary display record. All rows are also
    # individually written so historical data is preserved for training
    # via the stats_cache JOIN (which keys on player_id + season).
    # Since the salaries table has one row per player_id (upsert), we
    # process each player's rows oldest-first so the newest wins.
    from collections import defaultdict
    by_player = defaultdict(list)
    for row in rows:
        by_player[row.get("Player", "").strip()].append(row)

    matched = 0
    unmatched = 0
    skipped = 0
    unmatched_names = []

    current_year = int(CURRENT_SEASON)

    for player_name, contracts in by_player.items():
        if not player_name:
            skipped += 1
            continue

        # Sort oldest→newest so newest upsert wins in the salaries table
        contracts.sort(key=lambda r: int(r.get("End", 0) or 0))

        norm = _normalize(player_name)

        for row in contracts:
            aav = _parse_dollars(row.get("AAV") or row.get("aav", ""))
            total_value = _parse_dollars(row.get("Value", ""))
            if not aav:
                skipped += 1
                continue

            raw_team = row.get("Team                     Currently With") or row.get("Team", "")
            team = _extract_team(raw_team)
            position = (row.get("Pos") or row.get("position", "")).strip().upper()
            age_at_signing = row.get("Age                     At Signing") or row.get("Age", "")
            start = int(row.get("Start") or 0)
            end = int(row.get("End") or 0)
            years = int(row.get("Yrs") or 0)
            fa = _fa_type(age_at_signing, start, end)

            nhl_id = _match_player(norm, team, index)

            if nhl_id:
                matched += 1
            else:
                # Stable synthetic ID so the row still enters the DB
                nhl_id = f"csv_{norm.replace(' ', '_')}"
                if player_name not in unmatched_names:
                    unmatched_names.append(player_name)
                unmatched += 1
                logger.warning(f"CSV import: no index match for '{player_name}' ({team})")

            upsert_salary(
                player_id=nhl_id,
                name=player_name,
                team=team,
                position=position,
                aav=aav,
                total_value=total_value,
                contract_years=years,
                expiry_season=end,
                fa_type=fa,
                source="csv",
            )

    logger.info(
        f"CSV import done: {matched} matched, {unmatched} unmatched, {skipped} skipped"
    )
    return {
        "total": len(rows),
        "matched": matched,
        "unmatched": unmatched,
        "skipped": skipped,
        "unmatched_names": unmatched_names,
    }


def import_contracts_from_file(path):
    """Import from a file path (used for the bundled default CSV)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return import_contracts_from_stream(f)
