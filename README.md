# GreenFarm Carbon AI

An AI-powered decision-support tool that estimates a farm's carbon footprint
from five agricultural activity inputs, using a trained XGBoost regression
model, and turns that estimate into a sustainability score and concrete,
rule-based recommendations.

> **This system provides an estimated farm-level carbon footprint using
> agricultural activity inputs and a trained XGBoost regression model. It is
> a prototype decision-support system and not a complete Life Cycle
> Assessment.**

## 1. Problem statement

Farmers and agricultural planners rarely have an easy way to see how their
day-to-day input choices — fertilizer, fuel, irrigation water, electricity —
translate into greenhouse gas emissions. Full Life Cycle Assessments exist
but are slow, expensive, and inaccessible to an individual farm. GreenFarm
Carbon AI closes part of that gap: a farmer enters what they actually used
this season and gets back an estimated footprint, a 0–100 sustainability
score, and specific next steps, in seconds.

## 2. Objectives

- Predict per-hectare carbon footprint from five real inputs using a
  trained regression model, not a rule-of-thumb formula.
- Make every number explainable: feature importance, evaluation metrics,
  and scoring thresholds are all real and inspectable, never fabricated.
- Give the user actionable output (sustainability score + recommendations),
  not just a raw number.
- Keep every user's data private from every other user.

## 3. Features

- Email/password registration and login (JWT-based sessions)
- Farm management (create, list, update, delete)
- Carbon footprint prediction via the trained XGBoost model
- Deterministic 0–100 sustainability score with category labels
- Deterministic, rule-based recommendations (no LLM involved)
- Prediction history per farm and per user
- Dashboard with real aggregate statistics and charts
- Model information page showing the actual trained model's metrics and
  feature importance
- Strict per-user data isolation on every endpoint

## 4. Architecture

```
greenfarrm_Co2/
├── backend/          FastAPI application
│   ├── app/
│   │   ├── api/v1/       auth, farms, predictions, dashboard, model_info routers
│   │   ├── core/         config, security (JWT/bcrypt)
│   │   ├── db/           SQLAlchemy session/base
│   │   ├── ml/           model/preprocessor loader (reads ml/models/*.joblib)
│   │   ├── models/       SQLAlchemy models: User, Farm, Prediction, Recommendation
│   │   ├── schemas/      Pydantic request/response contracts
│   │   └── services/     prediction pipeline, sustainability score, recommendation engine
│   ├── alembic/          database migrations
│   └── tests/            41 automated tests (pytest)
├── frontend/          React + TypeScript + Vite + Tailwind + Recharts
│   └── src/
│       ├── pages/        Login, Register, Dashboard, Farms, Predict, History, ModelInfo
│       ├── components/   AppShell, GrowthRing (sustainability gauge), shared UI primitives
│       ├── context/       AuthContext (JWT session state)
│       └── services/      typed API client (axios)
├── ml/
│   ├── datasets/          synthetic dataset (raw + labeled + train/test split)
│   ├── preprocessing/     dataset generation, emission-factor formulas, cleaning, preprocessor
│   ├── training/           model training/cross-validation
│   ├── evaluation/         held-out evaluation + saved metrics/feature importance
│   └── models/             trained artifacts (.joblib — gitignored, regenerate via scripts below)
└── docker-compose.yml (db + backend service definitions; not built/run in this pass — see Limitations)
```

Request flow: **React frontend → FastAPI (JWT-protected) → SQLAlchemy/PostgreSQL
for persistence, and the saved XGBoost model + preprocessor for inference.**

## 5. Dataset

A 6,000-row synthetic dataset across 6 crops (Rice, Wheat, Maize, Soybean,
Sugarcane, Cotton), generated from documented per-crop parameter ranges
(triangular distributions) in `ml/preprocessing/crop_parameter_ranges.py`.

**Honesty note (carried through from Phase 2):** no publicly reachable
dataset combining crop type, fertilizer, fuel, water, and electricity use at
farm level with a validated carbon-footprint target was found (search log in
`ml/datasets/RAW_DATASET_SOURCES.md`). The parameter ranges are therefore
illustrative, order-of-magnitude figures rather than sourced statistics, and
are explicitly marked `UNVERIFIED` in code — they should be replaced with
cited regional data (FAO AQUASTAT, national ag-extension statistics) before
any real-world or academic-citation use.

## 6. The five ML features

| Feature | Unit | Role |
|---|---|---|
| Crop type | categorical (6 crops) | one-hot encoded |
| Fertilizer usage | kg/ha | numeric, standardized |
| Fuel consumption | liters/ha | numeric, standardized |
| Water consumption | m³/ha | numeric, standardized |
| Electricity consumption | kWh/ha | numeric, standardized |

Farm area (hectares) is collected separately and used only to scale the
per-hectare prediction to total farm emissions — it is not a model feature.

## 7. Carbon footprint calculation (training-label generation)

The *label* the model is trained on (`carbon_footprint_kg_co2e_per_ha`) is
computed from IPCC-style emission factors across four components
(`ml/preprocessing/emission_factors.py`), not guessed:

- **Fertilizer:** N₂O from field application (IPCC 2019 Refinement Tier 1,
  EF1 = 1% of applied N; AR5 GWP of 265) + upstream manufacturing emissions.
- **Fuel:** diesel combustion at ~2.68 kg CO₂e/liter (DEFRA/EPA-aligned).
- **Electricity:** on-farm metered use × grid carbon intensity.
- **Irrigation:** water volume × pumping energy intensity (kWh/m³) × grid
  carbon intensity — water itself has no emissions; the *energy to move it*
  does.

Every constant is labeled `[STANDARD]`, `[LITERATURE]`, or `[ASSUMPTION]` in
the source file so it's clear which numbers are well-established physical
factors vs. configurable, region-dependent assumptions.

At **inference time**, the trained XGBoost model predicts this same
footprint directly from the five inputs — it does not re-run the emission
formula. This is the whole point of training a model: to approximate that
formula (and any real-world nonlinearity/noise in the label) fast, from
inputs alone.

## 8. XGBoost methodology

- Preprocessing: `ColumnTransformer` (OneHotEncoder for crop type +
  StandardScaler for the four numeric features), fit on the training split
  only.
- Missing rows were **dropped**, not imputed — because the label is
  deterministic from the inputs, imputing an input would fabricate a label.
- Outliers were winsorized, with the target recomputed after.
- 5-fold cross-validation compared Linear Regression, Random Forest, and
  XGBoost. Linear Regression's R²=1.0 was flagged and disclosed as an
  artifact of the linear emission formula, not a genuine "best model."
- **XGBoost was selected** for its strong accuracy plus native feature
  importance (explainability was a project requirement).

## 9. Model evaluation (real, from the saved model — `GET /api/v1/model/info`)

| Metric | Value |
|---|---|
| MAE | 10.68 kg CO₂e/ha |
| RMSE | 17.92 kg CO₂e/ha |
| R² | 0.9991 |

Trained on 4,429 rows, evaluated on a held-out test set of 1,108 rows.

**Feature importance** (top 3 of 10 post-encoding features): water
consumption (64.2%), crop_type=Rice (20.5%), fertilizer usage (6.6%). The
frontend's Model page renders this list directly from
`ml/evaluation/test_set_results.json` — nothing is hardcoded in application
code, and the backend returns 503 rather than fake numbers if that file is
missing.

## 10. Sustainability scoring

Deterministic linear mapping, anchored to the real min/max of the training
label (not arbitrary numbers):

```
score = 100 - ((footprint - 557.00) / (3020.03 - 557.00)) * 100
```
clamped to [0, 100], rounded to the nearest integer. Categories:

| Score | Category |
|---|---|
| 90–100 | Excellent |
| 75–89 | Good |
| 50–74 | Moderate |
| 0–49 | Needs Improvement |

Implementation: `backend/app/services/sustainability_score.py`.

## 11. Recommendation system

Rule-based and fully deterministic — **no LLM**. Each of the four numeric
inputs is compared against its real Q3 (75th percentile) in the training
data: fertilizer 186.07 kg/ha, fuel 84.01 L/ha, water 10,104.55 m³/ha,
electricity 446.21 kWh/ha. Exceeding a threshold triggers a specific,
actionable recommendation for that input; a High/Very High overall category
adds a "focus on the largest contributor" note. Falls back to a
"maintain current practices" message when nothing is elevated. Capped at 5
items, persisted to the `recommendations` table linked to the prediction.
Implementation: `backend/app/services/recommendation_engine.py`.

## 12. API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | – | Create account (bcrypt-hashed password) |
| POST | `/api/v1/auth/login` | – | Returns JWT access token |
| GET | `/api/v1/auth/me` | ✓ | Current user |
| POST | `/api/v1/farms/` | ✓ | Create farm |
| GET | `/api/v1/farms/` | ✓ | List own farms |
| GET/PATCH/DELETE | `/api/v1/farms/{id}` | ✓ | Manage own farm (404 if not owned) |
| POST | `/api/v1/predictions/carbon` | ✓ | Run XGBoost prediction on an owned farm; persists prediction + recommendations |
| GET | `/api/v1/predictions/history` | ✓ | Own prediction history (optional `?farm_id=`) |
| GET | `/api/v1/dashboard/summary` | ✓ | Totals, averages, recent predictions |
| GET | `/api/v1/dashboard/history` | ✓ | Full history for charting |
| GET | `/api/v1/dashboard/crop-stats` | ✓ | Per-crop prediction counts/averages |
| GET | `/api/v1/model/info` | – | Real model metrics + feature importance |

All `✓` routes require `Authorization: Bearer <token>` and are scoped to
`current_user.id` — cross-user access returns `404` (not `403`), so a
request never confirms that another user's resource even exists.

## 13. Database design

PostgreSQL, managed with Alembic migrations (`backend/alembic/`).

```
users            id, email (unique), hashed_password, full_name, created_at
farms            id, user_id → users, farm_name, location, area, crop_type, created_at
predictions      id, farm_id → farms, fertilizer/fuel/water/electricity inputs,
                 predicted_carbon, carbon_category, sustainability_score, created_at
recommendations  id, prediction_id → predictions, category, text
```

Ownership chain: `Recommendation → Prediction → Farm → User`. Every
dashboard/history query joins through this chain filtered on
`Farm.user_id == current_user.id`.

## 14. Frontend

React + TypeScript + Vite + Tailwind CSS, with Recharts for charts and
react-router-dom for routing.

- **Pages:** `/login`, `/register`, `/dashboard`, `/farms`, `/predict`,
  `/history`, `/model`
- **Auth:** JWT stored in `sessionStorage` (clears on tab close — a
  deliberate, documented tradeoff for this academic MVP; see Limitations)
- **API layer:** `src/services/api.ts` — a single typed axios client with
  automatic JWT injection and consistent error extraction
- **States handled:** loading, error (network + validation), unauthorized
  (redirect to `/login`), empty (no farms / no predictions yet)
- **Design:** green/white/light-grey palette (`canopy`/`soil`/`clay`/`rust`
  Tailwind tokens), Space Grotesk for headings, Inter for body text,
  JetBrains Mono for numeric data. Signature element: a "growth ring" radial
  gauge for the sustainability score.

## 15. Installation

**Prerequisites:** Python 3.12, Node 20+, PostgreSQL 16 running locally.

```bash
git clone <repo-url>
cd greenfarrm_Co2

# --- Backend ---
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in real values — see below

# --- ML artifacts (only needed once, or after changing ml/ code) ---
cd ../ml/preprocessing && python build_preprocessor.py
cd ../evaluation && python evaluate_and_save.py

# --- Database ---
createuser greenfarm --pwprompt
createdb greenfarm_carbon_ai -O greenfarm
cd ../../backend && alembic upgrade head

# --- Frontend ---
cd ../frontend
npm install
```

Required `.env` values (backend, copied to `backend/.env`):
```
DATABASE_URL=postgresql://greenfarm:<password>@localhost:5432/greenfarm_carbon_ai
SECRET_KEY=<a long random string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MODEL_PATH=ml/models/carbon_model.joblib
PREPROCESSOR_PATH=ml/models/preprocessor.joblib
```

Frontend `.env`:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 16. Running instructions

```bash
# Terminal 1 — backend (from backend/, with .venv active)
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Visit `http://localhost:5173`. Backend health check:
`http://localhost:8000/health`.

## 17. SDG alignment

- **SDG 13 (Climate Action):** direct farm-level visibility into GHG
  emissions, the first step toward reduction.
- **SDG 2 (Zero Hunger):** supports agricultural decision-making without
  requiring a tradeoff against yield — recommendations target efficiency
  (e.g. soil-test-based fertilizer use), not blanket reduction.
- **SDG 12 (Responsible Consumption and Production):** encourages
  input-efficient farming practices (irrigation scheduling, reduced
  machinery passes).

## 18. Limitations

- **Synthetic training data.** Parameter ranges are order-of-magnitude
  estimates, not sourced regional statistics — see Section 5. Predictions
  reflect the *shape* of realistic farm data, not validated real-world
  measurements for any specific region.
- **Not a full LCA.** The emission-factor formula covers four major
  components; a complete Life Cycle Assessment would include soil carbon
  dynamics, embodied emissions in machinery/infrastructure, transport
  beyond the farm gate, and more.
- **Fixed emission-factor assumptions.** Grid carbon intensity (0.5 kg
  CO₂e/kWh) and irrigation energy intensity (0.15 kWh/m³) are global
  averages, not region-specific.
- **JWT in `sessionStorage`.** No refresh-token rotation or remember-me;
  acceptable for an academic MVP, not production-grade session management.
- **No rate limiting or email verification** on registration.
- **Docker not built/run in this pass.** `docker-compose.yml` and each
  service's `Dockerfile` are present in the repo (reviewed for consistency
  with the real dependency set), but were not executed here — no Docker
  daemon was available in the environment this work was done in, and
  building/running them was explicitly out of scope for this iteration.
  Local (non-container) development is fully working and tested.

## 19. Future scope

- Replace synthetic data with sourced regional agricultural statistics.
- Region-selectable grid carbon intensity and irrigation energy factors.
- Refresh tokens / longer-lived sessions with proper rotation.
- Farm-level historical trend analysis (year-over-year, not just per-prediction).
- Export prediction reports (PDF) for offline sharing with agronomists.
- Multi-language support for non-English-speaking farmers.
