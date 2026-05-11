import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PORT, FRONTEND_URL, CURRENT_SEASON
from database.db import (
    init_db, upsert_salary, upsert_stats,
    get_salary, get_stats, get_salary_count, get_stats_count,
    ensure_player_index_table, upsert_player_index,
)
from database.seed_data import get_seed_players
from services.nhl_api import search_players, get_player_info, build_player_index_background
from services.comparables import find_comparables
from services.regression import predict_salary, invalidate_models
from services.salary_scraper import run_daily_scrape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"])


# ─── Startup ─────────────────────────────────────────────────────────────────

def seed_database():
    """Load seed data if database is empty."""
    if get_salary_count() == 0:
        logger.info("Seeding database with static player data...")
        players = get_seed_players()
        for p in players:
            upsert_salary(
                player_id=p["player_id"],
                name=p["name"],
                team=p["team"],
                position=p["position"],
                aav=p["aav"],
                total_value=p["aav"] * p.get("contract_years", 1),
                contract_years=p.get("contract_years"),
                expiry_season=p.get("expiry_season"),
                fa_type=p.get("fa_type", "UFA"),
                source="seed",
            )
            upsert_stats(
                player_id=p["player_id"],
                season=CURRENT_SEASON,
                position=p["position"],
                stats_dict=p["stats"],
            )
        logger.info(f"Seeded {len(players)} players")
    else:
        # Ensure stats_cache is populated too (may have salary but not stats after restart)
        if get_stats_count(CURRENT_SEASON) == 0:
            players = get_seed_players()
            for p in players:
                upsert_stats(p["player_id"], CURRENT_SEASON, p["position"], p["stats"])


init_db()
ensure_player_index_table()
seed_database()

# Seed the player search index from seed data immediately (fast)
for _p in get_seed_players():
    upsert_player_index(_p["player_id"], _p["name"], _p["team"], _p["position"])

# Then build the full index from NHL rosters in a background thread
import threading
threading.Thread(target=build_player_index_background, daemon=True).start()

# Start background scheduler for daily scrape
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_daily_scrape, "interval", hours=24, id="daily_scrape")
    scheduler.start()
    logger.info("APScheduler started — daily scrape every 24h")
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

    # Merge with MoneyPuck advanced stats if available
    cached = get_stats(player_id, CURRENT_SEASON)
    if cached and info.get("stats"):
        mp_stats = cached.get("stats", {})
        for key in ["corsi_for_pct", "xgf_pct", "penalty_diff_per_60", "quality_start_pct"]:
            if mp_stats.get(key) is not None:
                info["stats"][key] = mp_stats[key]

    # Attach salary
    salary = get_salary(player_id)
    info["salary"] = salary
    info["nhl_id"] = player_id

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

    # Get player info
    info = get_player_info(player_id)
    if not info:
        return jsonify({"error": "Player not found via NHL API"}), 404

    # Merge advanced stats from cache
    cached = get_stats(player_id, CURRENT_SEASON)
    if cached and info.get("stats"):
        mp_stats = cached.get("stats", {})
        for key in ["corsi_for_pct", "xgf_pct", "penalty_diff_per_60", "quality_start_pct"]:
            if mp_stats.get(key) is not None:
                info["stats"][key] = mp_stats[key]

    # Fallback for missing advanced stats: use seed data if available
    seed_entry = next(
        (p for p in get_seed_players() if p["player_id"] == player_id), None
    )
    if seed_entry and info.get("stats"):
        for key in ["corsi_for_pct", "xgf_pct", "penalty_diff_per_60", "quality_start_pct"]:
            if info["stats"].get(key) is None and seed_entry["stats"].get(key) is not None:
                info["stats"][key] = seed_entry["stats"][key]
        # Use seed stats for rate stats too if NHL API returned zeros
        if info["stats"].get("goals_per_60", 0) == 0 and seed_entry["stats"].get("goals_per_60"):
            for k in ["goals_per_60", "assists_per_60", "points_per_60", "toi_per_game"]:
                info["stats"][k] = seed_entry["stats"].get(k, info["stats"].get(k, 0))
        if info.get("age", 0) == 0:
            info["age"] = seed_entry.get("age", 0)
        if info.get("experience", 0) == 0:
            info["experience"] = seed_entry.get("experience", 0)

    # Build player_stats for model input
    player_stats = {
        "nhl_id": player_id,
        "position": info.get("position", "C"),
        "age": info.get("age", 25),
        "experience": info.get("experience", 5),
        "fa_type": fa_status if fa_status != "auto" else (
            seed_entry.get("fa_type", "UFA") if seed_entry else "UFA"
        ),
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

    # Salary verdict
    current_salary = get_salary(player_id)
    verdict = None
    if current_salary and current_salary.get("aav") and comp_result.get("estimate"):
        current_aav = current_salary["aav"]
        estimated = comp_result["estimate"]
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
        "comparables_estimate": comp_result,
        "regression_estimate": reg_result,
        "verdict": verdict,
        "comparables": comp_result.get("comparables", []),
    })


@app.route("/api/admin/scrape", methods=["POST"])
def trigger_scrape():
    """Manually trigger the daily data scrape."""
    count = run_daily_scrape()
    invalidate_models()
    return jsonify({"status": "ok", "rows_updated": count})


@app.route("/api/admin/db-stats")
def db_stats():
    return jsonify({
        "salary_count": get_salary_count(),
        "stats_count": get_stats_count(CURRENT_SEASON),
        "season": CURRENT_SEASON,
    })



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
