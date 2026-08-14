# GreenFarm Carbon AI

AI-powered carbon footprint prediction and sustainable farming advisory system.

## Status

Phase 1 complete: project architecture, backend bootstrap, Docker Compose
skeleton (Postgres + FastAPI). No ML model, database schema, auth, or
frontend UI yet — those land in later phases (see `PROGRESS.md`).

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS + Recharts (Phase 11+)
- **Backend:** FastAPI + Pydantic + SQLAlchemy
- **Database:** PostgreSQL
- **ML:** Pandas, NumPy, Scikit-learn, XGBoost, Joblib
- **Auth:** JWT
- **Deployment:** Docker + Docker Compose

## Repository layout

```
greenfarm-carbon-ai/
├── backend/        FastAPI application (API only, no ML training code)
├── frontend/        React/Vite app (scaffolded in Phase 11)
├── ml/              Dataset prep, training, evaluation — separate from backend runtime
├── docker-compose.yml
└── .env.example
```

## Local setup (current state — backend only)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # then fill in real values
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/health` — should return `{"status": "ok", ...}`.

## Docker (db + backend)

```bash
cp .env.example .env   # fill in real values first
docker compose up --build
```

## Development approach

This project is built in phases (see `PROGRESS.md` for the full plan and a
running log of what's implemented, tested, and pending). ML predictions,
dashboard statistics, and evaluation metrics are always generated from real
data and real trained models — never hardcoded.
