"""
Contract aging service.

Projects how a player's production and cap hit evolve over the life of their
contract. Age curves are pre-computed by run_train_final_models.py and stored
in backend/models/age_curves.json — no pandas required at runtime.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

POSITION_GROUPS = {
    'C': 'F', 'L': 'F', 'LW': 'F', 'R': 'F', 'RW': 'F', 'W': 'F', 'F': 'F',
    'D': 'D', 'LD': 'D', 'RD': 'D',
    'G': 'G',
}

METRIC_FIELDS = {'F': 'points_per_60', 'D': 'points_per_60', 'G': 'save_pct'}
METRIC_LABELS = {'F': 'Points / 60', 'D': 'Points / 60', 'G': 'Save %'}

# Known + CBA-projected cap ceilings ($ per season start year)
_CAP = {
    2019: 81_500_000, 2020: 81_500_000, 2021: 81_500_000,
    2022: 82_500_000, 2023: 83_500_000, 2024: 88_000_000,
    2025: 95_500_000, 2026: 104_800_000, 2027: 113_500_000,
}
_v = _CAP[2027]
for _yr in range(2028, 2055):
    _v = round(_v * 1.035)
    _CAP[_yr] = _v

_age_curves_cache = None


def _load_age_curves():
    global _age_curves_cache
    if _age_curves_cache is not None:
        return _age_curves_cache
    path = os.path.join(MODELS_DIR, 'age_curves.json')
    try:
        with open(path) as f:
            _age_curves_cache = json.load(f)
        logger.info('Loaded age curves from %s', path)
    except Exception as e:
        logger.warning('Could not load age curves (%s) — chart will show no avg curve', e)
        _age_curves_cache = {'F': {}, 'D': {}, 'G': {}}
    return _age_curves_cache


def _interp(curve_dict, age):
    """Return linearly interpolated metric value at given age from {age_str: value}."""
    if not curve_dict:
        return None
    ages = sorted(int(k) for k in curve_dict)
    age = float(age)
    if age <= ages[0]:
        return float(curve_dict[str(ages[0])])
    if age >= ages[-1]:
        return float(curve_dict[str(ages[-1])])
    for i in range(len(ages) - 1):
        a0, a1 = ages[i], ages[i + 1]
        if a0 <= age <= a1:
            t = (age - a0) / (a1 - a0)
            return float(curve_dict[str(a0)]) + t * (
                float(curve_dict[str(a1)]) - float(curve_dict[str(a0)])
            )
    return None


def _get_cap(year):
    year = int(year)
    return float(_CAP.get(year, _CAP.get(max(k for k in _CAP if k <= year), _CAP[2027])))


def get_contract_aging(player_id, player_info, salary):
    """
    Build the contract aging payload for a player.

    Returns a dict with:
      career_stats  — list of {age, metric, season} from stats_cache
      avg_curve     — list of {age, metric} for the position group
      projection    — list of {age, metric, contract_year} for each contract year
      contract      — {aav, years, first_season, expiry_season, yearly[]}
      metric_label  — human-readable y-axis label
      position_group
      confidence    — 'high' / 'medium' / 'low'
    """
    from database.db import get_db
    from config import CURRENT_SEASON

    curves = _load_age_curves()

    position = str((player_info.get('position') or 'C')).upper()
    pg = POSITION_GROUPS.get(position, 'F')
    pg_curve = curves.get(pg, {})

    age_now = float(player_info.get('age') or 28)
    metric_field = METRIC_FIELDS[pg]
    metric_label = METRIC_LABELS[pg]
    cur_season_int = int(str(CURRENT_SEASON)[:4])

    # ── Career stats from DB ─────────────────────────────────────────────────
    conn = get_db()
    rows = conn.execute(
        'SELECT season, stats_json FROM stats_cache WHERE player_id=? ORDER BY season',
        (player_id,)
    ).fetchall()
    conn.close()

    career_stats = []
    seen = set()
    for row in rows:
        try:
            season_int = int(str(row['season'])[:4])
            if season_int in seen:
                continue
            seen.add(season_int)
            s = json.loads(row['stats_json'])
            raw = s.get(metric_field)
            if raw is None:
                continue
            val = float(raw)
            if val <= 0:
                continue
            years_ago = cur_season_int - season_int
            age_at = round(age_now - years_ago, 1)
            if 16 <= age_at <= 45:
                career_stats.append({
                    'age': age_at,
                    'metric': round(val, 4),
                    'season': str(row['season']),
                })
        except Exception:
            pass

    career_stats.sort(key=lambda x: x['age'])

    # Ensure current season is in career_stats
    stats = player_info.get('stats') or {}
    cur_raw = stats.get(metric_field)
    if cur_raw is not None:
        cur_val = float(cur_raw)
        if cur_val > 0 and not any(s['season'] == str(CURRENT_SEASON) for s in career_stats):
            career_stats.append({
                'age': round(age_now, 1),
                'metric': round(cur_val, 4),
                'season': str(CURRENT_SEASON),
            })
            career_stats.sort(key=lambda x: x['age'])

    last_metric = career_stats[-1]['metric'] if career_stats else None

    # ── Average curve (full age range for chart) ─────────────────────────────
    avg_curve = [
        {'age': int(a), 'metric': round(float(v), 4)}
        for a, v in sorted(pg_curve.items(), key=lambda x: int(x[0]))
        if 18 <= int(a) <= 42
    ]

    # ── Contract ─────────────────────────────────────────────────────────────
    if not salary or not salary.get('aav'):
        return {
            'career_stats': career_stats,
            'avg_curve': avg_curve,
            'contract': None,
            'projection': [],
            'metric_label': metric_label,
            'position_group': pg,
            'confidence': 'low' if len(career_stats) <= 1 else 'medium',
        }

    aav = float(salary['aav'])
    contract_years = int(salary.get('contract_years') or 1)
    expiry_season = int(salary.get('expiry_season') or cur_season_int)
    first_season = expiry_season - contract_years + 1

    yearly = []
    for i, yr in enumerate(range(first_season, expiry_season + 1)):
        age_at_yr = round(age_now + (yr - cur_season_int), 1)
        cap = _get_cap(yr)
        cap_pct = round(aav / cap * 100, 2) if cap > 0 else 0
        yearly.append({
            'contract_year': i + 1,
            'season_year': yr,
            'age': age_at_yr,
            'cap': round(cap),
            'cap_pct': cap_pct,
        })

    # ── Production projection ─────────────────────────────────────────────────
    # Offset-ratio: how far above/below the average curve the player currently is.
    # Apply that same ratio to each future age's average to project their output.
    avg_at_now = _interp(pg_curve, age_now)
    if last_metric is not None and avg_at_now and avg_at_now > 0:
        offset_ratio = max(0.1, min(4.0, last_metric / avg_at_now))
    else:
        offset_ratio = 1.0

    projection = []
    for entry in yearly:
        avg_at = _interp(pg_curve, entry['age'])
        if avg_at is not None:
            proj = round(avg_at * offset_ratio, 4)
        elif last_metric is not None:
            proj = round(last_metric * (0.975 ** entry['contract_year']), 4)
        else:
            continue
        projection.append({
            'age': entry['age'],
            'metric': proj,
            'contract_year': entry['contract_year'],
        })

    confidence = 'high' if len(career_stats) >= 4 else (
        'medium' if len(career_stats) >= 2 else 'low'
    )

    return {
        'career_stats': career_stats,
        'avg_curve': avg_curve,
        'contract': {
            'aav': aav,
            'years': contract_years,
            'first_season': first_season,
            'expiry_season': expiry_season,
            'yearly': yearly,
        },
        'projection': projection,
        'metric_label': metric_label,
        'position_group': pg,
        'confidence': confidence,
    }
