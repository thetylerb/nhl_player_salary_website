# ─── Stage 1: build the React frontend ────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Empty base URL bakes relative /api/... paths into the build, so the app
# never has to know or care what host it's running on (see api.js).
ENV REACT_APP_API_URL=""
RUN npm run build


# ─── Stage 2: Flask API + built frontend, served by gunicorn ─────────────
# Pinned to 3.11, not 3.13: the scikit-learn/pandas/numpy versions pinned in
# requirements.txt have no prebuilt wheels for 3.13, so pip falls back to
# compiling from source and fails on a Cython/GCC incompatibility.
FROM python:3.11-slim AS backend

# Paths in the app (models, data, sqlite db) are resolved relative to each
# module's own file location, not the process cwd, but gunicorn still needs
# to be run from here to import the app:app module.
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /app/frontend/build ./frontend_build

ENV PORT=5000
EXPOSE 5000

# 2 workers each load their own copy of the models into memory; at ~480KB of
# joblib artifacts total this is negligible, so 2 workers is safe even on a
# small instance. Shell form so ${PORT} expands at container start.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120
