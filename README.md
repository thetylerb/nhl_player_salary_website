# NHL Salary Estimator

AI-powered NHL player contract valuation using a comparables engine and gradient-boosting regression model.

## Architecture

```
nhl_player_salary_website/
├── backend/          Flask API + ML models
└── frontend/         React SPA
```

**Data pipeline:**
- **NHL API** (`api-web.nhle.com`) — player stats, search (free, no auth)
- **MoneyPuck** — advanced stats CSV (CF%, xGF%, etc.) — fetched daily
- **PuckPedia** — salary scraper (best-effort; falls back to seed data)
- **SQLite** — local cache for salaries + stats

**Estimation methods:**
1. **Comparables engine** — z-score normalized stats, weighted Euclidean distance, inverse-distance weighted salary average
2. **Regression model** — `GradientBoostingRegressor` (sklearn) trained on the salary × stats dataset, one model per position group (F / D / G)

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit env
cp .env.example .env

python app.py
# → http://localhost:5000/api/health
```

The server seeds ~100 players on first start and kicks off a daily MoneyPuck scrape at midnight.

### Frontend

```bash
cd frontend
npm install

# Copy and edit env
cp .env.example .env
# Set REACT_APP_API_URL=http://localhost:5000

npm start
# → http://localhost:3000
```

---

## Deployment on Railway

### Backend service

1. Create a new Railway project → **New Service** → **GitHub repo** → select the `/backend` root directory (set Root Directory in settings).
2. Railway auto-detects Python via Nixpacks and uses `railway.toml`.
3. Set environment variables:

| Variable | Value |
|---|---|
| `DATABASE_PATH` | `/tmp/salary_cache.db` (or mount a volume for persistence) |
| `FRONTEND_URL` | Your frontend Railway URL, e.g. `https://nhl-salary-frontend.up.railway.app` |
| `PORT` | Auto-set by Railway |

4. Deploy → health check hits `/api/health`.

> **Persistence note:** `/tmp` is ephemeral on Railway free tier. The seed data re-loads on each restart (takes ~1 s). For a persistent DB, attach a Railway Volume and set `DATABASE_PATH=/data/salary_cache.db`.

### Frontend service

1. **New Service** → same repo → set Root Directory to `/frontend`.
2. Railway uses `railway.toml` to run `npm run build` then `npx serve -s build`.
3. Set environment variable:

| Variable | Value |
|---|---|
| `REACT_APP_API_URL` | Your backend Railway URL, e.g. `https://nhl-salary-backend.up.railway.app` |

> `REACT_APP_API_URL` must be set **before the build step** (it's baked in at build time by CRA). Set it in Railway's Variables tab before the first deploy.

### Custom domain

Point your DNS CNAME to the Railway-provided domain for either service. No code changes required — the env-var approach handles all URL routing.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/players/search?q=name` | Search players |
| `GET` | `/api/player/:id` | Player info + stats |
| `POST` | `/api/estimate` | Salary estimate |
| `POST` | `/api/admin/scrape` | Trigger manual scrape |
| `GET` | `/api/admin/db-stats` | DB row counts |

### POST `/api/estimate` body

```json
{
  "player_id": "8478483",
  "weights": {
    "goals_per_60": 1.0,
    "assists_per_60": 0.8,
    "points_per_60": 1.0,
    "toi_per_game": 0.7,
    "corsi_for_pct": 0.5,
    "xgf_pct": 0.6,
    "penalty_diff_per_60": 0.3
  },
  "fa_status": "auto",
  "position_filter": true,
  "n_comparables": 10
}
```

---

## Salary Data Notes

- On first launch, 100 seeded contracts (2023-24 season) power the models
- The daily scraper runs at midnight and tries:
  1. MoneyPuck CSVs for advanced stats
  2. PuckPedia for salary data
- If scraping is blocked (403 / bot detection), the seed dataset remains active
- Trigger a manual scrape: `POST /api/admin/scrape`
