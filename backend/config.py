import os
import datetime as _dt

_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salary_cache.db')
DATABASE_PATH = os.environ.get('DATABASE_PATH', _default_db)
PORT = int(os.environ.get('PORT', 5000))
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
NHL_API_BASE = 'https://api-web.nhle.com/v1'
SUGGEST_API_BASE = 'https://suggest.svc.nhl.com/svc/suggest/v1'
MONEYPUCK_BASE = 'https://moneypuck.com/moneypuck/playerData/seasonSummary'

def _detect_season():
    """NHL season starts in October — before October the current season started last year."""
    now = _dt.date.today()
    return str(now.year - 1) if now.month < 10 else str(now.year)

CURRENT_SEASON = os.environ.get('CURRENT_SEASON', _detect_season())
HISTORICAL_SEASON_START = int(os.environ.get('HISTORICAL_SEASON_START', '2019'))
