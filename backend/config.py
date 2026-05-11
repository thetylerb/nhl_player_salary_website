import os

_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salary_cache.db')
DATABASE_PATH = os.environ.get('DATABASE_PATH', _default_db)
PORT = int(os.environ.get('PORT', 5000))
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
NHL_API_BASE = 'https://api-web.nhle.com/v1'
SUGGEST_API_BASE = 'https://suggest.svc.nhl.com/svc/suggest/v1'
MONEYPUCK_BASE = 'https://moneypuck.com/moneypuck/playerData/seasonSummary'
CURRENT_SEASON = os.environ.get('CURRENT_SEASON', '2024')
