import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PORT, FRONTEND_URL, CURRENT_SEASON
from database.db import (
    init_db, upsert_stats,
    get_salary, get_stats, get_salary_count, get_stats_count,
    ensure_player_index_table,
    clear_player_index, seed_cap_ceilings, purge_seed_salaries,
)
from services.nhl_api import search_players, get_player_info, build_player_index_background, force_rebuild_player_index
from services.comparables import find_comparables
from services.regression import predict_salary, invalidate_models
from services.salary_scraper import run_daily_scrape, run_weekly_salary_scrape, run_historical_stats_scrape
from services.csv_importer import import_contracts_from_stream, import_contracts_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[
    FRONTEND_URL,
    "https://nhl-player-salary-website.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
])


# ─── Startup ─────────────────────────────────────────────────────────────────

init_db()
seed_cap_ceilings()
ensure_player_index_table()
purge_seed_salaries()

# Clear the player index and rebuild from real NHL roster IDs, then
# auto-import the bundled CSV so salary data is always fresh on deploy.
clear_player_index()

import threading

_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "nhl_contracts.csv")

def _startup_sequence():
    """Build player index first, then import CSV so name→ID matching works."""
    force_rebuild_player_index()
    if os.path.exists(_CSV_PATH):
        try:
            result = import_contracts_from_file(_CSV_PATH)
            logger.info(
                f"CSV auto-import: {result['matched']} matched, "
                f"{result['unmatched']} unmatched, {result['skipped']} skipped"
            )
            invalidate_models()
        except Exception as e:
            logger.error(f"CSV auto-import failed: {e}")
    else:
        logger.warning(f"Bundled CSV not found at {_CSV_PATH}")

threading.Thread(target=_startup_sequence, daemon=True).start()

# Start background scheduler for daily scrape
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_daily_scrape, "interval", hours=24, id="daily_stats_scrape")
    scheduler.add_job(run_weekly_salary_scrape, "interval", weeks=1, id="weekly_salary_scrape")
    scheduler.start()
    logger.info("APScheduler started — stats every 24h, salaries every 7d")
except ImportError:
    logger.warning("APScheduler not installed; scheduled scraping disabled")


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "season": CURRENT_SEASON})


@app.route("/api/players/search")
def player_search():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"players": []})
    try:
        results = search_players(q)
        logger.info(f"Search '{q}' → {len(results)} results")
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        results = []
    return jsonify({"players": results[:20]})


@app.route("/api/player/<player_id>")
def player_detail(player_id):
    """Fetch fresh player info + stats from NHL API, merge with cache."""
    info = get_player_info(player_id)
    if not info:
        return jsonify({"error": "Player not found"}), 404

    # MoneyPuck is the authoritative source for all rate and advanced stats.
    # Override every key it provides (NHL API can return 0 for TOI/rate stats
    # when featuredStats is missing or the season hasn't been processed yet).
    cached = get_stats(player_id, CURRENT_SEASON)
    if cached:
        mp_stats = cached.get("stats", {})
        if mp_stats:
            if info.get("stats") is None:
                info["stats"] = {}
            for key, val in mp_stats.items():
                if val is not None:
                    info["stats"][key] = val

    # Attach salary
    salary = get_salary(player_id)
    info["salary"] = salary
    info["nhl_id"] = player_id

    logger.debug(
        "player_detail %s stats: toi_per_game=%s points_per_60=%s goals_per_60=%s gp=%s",
        player_id,
        info["stats"].get("toi_per_game") if info.get("stats") else None,
        info["stats"].get("points_per_60") if info.get("stats") else None,
        info["stats"].get("goals_per_60") if info.get("stats") else None,
        info["stats"].get("games_played") if info.get("stats") else None,
    )

    return jsonify(info)


@app.route("/api/estimate", methods=["POST"])
def estimate():
    """
    Body:
    {
      player_id: str,
      weights: {stat_key: float, ...},
      fa_status: "auto"|"RFA"|"UFA",
      position_filter: bool,
      n_comparables: int (5-20)
    }
    """
    body = request.get_json(silent=True) or {}
    player_id = str(body.get("player_id", ""))
    weights = body.get("weights") or {}
    fa_status = body.get("fa_status", "auto")
    position_filter = bool(body.get("position_filter", True))
    n_comp = int(body.get("n_comparables", 10))
    n_comp = max(5, min(n_comp, 20))

    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    # Get player info (metadata: name, team, position, age, headshot)
    info = get_player_info(player_id)
    if not info:
        return jsonify({"error": "Player not found via NHL API"}), 404

    # MoneyPuck is the authoritative source for ALL rate and advanced stats.
    # Fetch from DB and override every key so comparables/regression always
    # operate on DB values, never on potentially-zero NHL API values.
    cached = get_stats(player_id, CURRENT_SEASON)
    if cached:
        mp_stats = cached.get("stats", {})
        if mp_stats:
            if info.get("stats") is None:
                info["stats"] = {}
            for key, val in mp_stats.items():
                if val is not None:
                    info["stats"][key] = val

    # Resolve FA type: explicit override > salary record > default UFA
    current_salary = get_salary(player_id)
    if fa_status != "auto":
        resolved_fa = fa_status
    elif current_salary and current_salary.get("fa_type"):
        resolved_fa = current_salary["fa_type"]
    else:
        resolved_fa = "UFA"

    # Build player_stats — stats come from DB (authoritative); NHL API as fallback
    player_stats = {
        "nhl_id": player_id,
        "position": info.get("position", "C"),
        "age": info.get("age", 25),
        "experience": info.get("experience", 5),
        "fa_type": resolved_fa,
        "stats": info.get("stats", {}),
    }

    # Run both models in parallel (sequential here — fast enough)
    comp_result = find_comparables(
        player_stats,
        weights=weights,
        n=n_comp,
        position_filter=position_filter,
        fa_status=fa_status,
    )

    reg_result = predict_salary(player_stats)

    # Salary verdict — use regression estimate (stats-based) as primary source,
    # fall back to comparables if regression didn't produce a result.
    verdict = None
    estimated = reg_result.get("estimate") or comp_result.get("estimate")
    if current_salary and current_salary.get("aav") and estimated:
        current_aav = current_salary["aav"]
        diff = estimated - current_aav
        pct = (diff / current_aav * 100) if current_aav else 0
        if pct > 10:
            status = "underpaid"
        elif pct < -10:
            status = "overpaid"
        else:
            status = "fair"
        verdict = {
            "status": status,
            "by": round(diff),
            "pct": round(pct, 1),
            "based_on": "regression" if reg_result.get("estimate") else "comparables",
        }

    return jsonify({
        "player": {
            "nhl_id": player_id,
            "name": info.get("name"),
            "team": info.get("team"),
            "position": info.get("position"),
            "age": info.get("age"),
            "experience": info.get("experience"),
            "headshot_url": info.get("headshot_url"),
            "stats": info.get("stats"),
            "fa_type": player_stats["fa_type"],
        },
        "current_salary": current_salary,
        "comparables_estimate": {
            **comp_result,
            "rmse_dollars": reg_result.get("rmse_dollars"),
            "position_group": reg_result.get("position_group"),
        },
        "regression_estimate": reg_result,
        "verdict": verdict,
        "comparables": comp_result.get("comparables", []),
    })


@app.route("/api/admin/scrape", methods=["POST"])
def trigger_scrape():
    """Manually trigger both the stats and salary scrapes."""
    stats = run_daily_scrape()
    salaries = run_weekly_salary_scrape()
    return jsonify({"status": "ok", "stats_rows": stats, "salary_rows": salaries})


@app.route("/api/admin/db-stats")
def db_stats():
    return jsonify({
        "salary_count": get_salary_count(),
        "stats_count": get_stats_count(CURRENT_SEASON),
        "season": CURRENT_SEASON,
    })


@app.route("/api/admin/scrape-historical", methods=["POST"])
def trigger_historical_scrape():
    """Scrape MoneyPuck stats for all past seasons (2019 → current-1)."""
    rows = run_historical_stats_scrape()
    invalidate_models()
    return jsonify({"status": "ok", "rows": rows})


@app.route("/api/admin/missing-data")
def missing_data():
    """Players with stats but no salary, and salary but no stats."""
    from database.db import get_db
    conn = get_db()

    # Players with stats this season but no salary record at all
    stats_no_salary = conn.execute('''
        SELECT sc.player_id, pi.name, pi.team, pi.position
        FROM stats_cache sc
        LEFT JOIN salaries s ON s.player_id = sc.player_id
        LEFT JOIN player_index pi ON pi.nhl_id = sc.player_id
        WHERE s.player_id IS NULL AND sc.season = ?
        ORDER BY pi.name
    ''', (CURRENT_SEASON,)).fetchall()

    # Players with a salary record but no stats in ANY season
    # (catches csv_ synthetic IDs and players never scraped by MoneyPuck)
    salary_no_stats = conn.execute('''
        SELECT s.player_id, s.player_name AS name, s.team, s.position, s.aav, s.source
        FROM salaries s
        LEFT JOIN stats_cache sc ON sc.player_id = s.player_id
        WHERE sc.player_id IS NULL AND s.aav IS NOT NULL AND s.aav > 0
        ORDER BY s.aav DESC
    ''').fetchall()

    # Summary counts for quick health check
    salary_count = conn.execute('SELECT COUNT(*) FROM salaries').fetchone()[0]
    stats_count = conn.execute(
        'SELECT COUNT(*) FROM stats_cache WHERE season=?', (CURRENT_SEASON,)
    ).fetchone()[0]
    csv_count = conn.execute(
        "SELECT COUNT(*) FROM salaries WHERE source='csv'"
    ).fetchone()[0]

    conn.close()
    return jsonify({
        "season": CURRENT_SEASON,
        "salary_count": salary_count,
        "stats_count": stats_count,
        "csv_salary_count": csv_count,
        "stats_no_salary": [dict(r) for r in stats_no_salary],
        "salary_no_stats": [dict(r) for r in salary_no_stats],
    })



@app.route("/api/admin/import-csv", methods=["POST"])
def import_csv():
    """
    Accept a multipart CSV upload OR re-import the bundled data/nhl_contracts.csv.
    POST with no file body → re-import bundled CSV.
    POST with file field 'file' → import that CSV.
    """
    import os
    from services.csv_importer import import_contracts_from_stream, import_contracts_from_file

    if 'file' in request.files:
        f = request.files['file']
        result = import_contracts_from_stream(f.stream)
    else:
        bundled = os.path.join(os.path.dirname(__file__), "data", "nhl_contracts.csv")
        if not os.path.exists(bundled):
            return jsonify({"error": "No bundled CSV found and no file uploaded"}), 400
        result = import_contracts_from_file(bundled)

    invalidate_models()
    return jsonify({"status": "ok", **result})


@app.route("/api/debug/search")
def debug_search():
    from database.db import search_player_index, get_player_index_count
    from services.nhl_api import search_players
    q = request.args.get("q", "mcdavid")
    index_count = get_player_index_count()
    raw = search_player_index(q, 5)
    via_func = search_players(q)
    return jsonify({"index_count": index_count, "raw_index": raw, "search_players": via_func})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
