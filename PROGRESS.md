# Progress Log

## Phase 1 — Architecture & environment setup ✅ (this delivery)

**Files created:**
- `backend/app/main.py` — FastAPI app, CORS, `/health` endpoint
- `backend/app/core/config.py` — pydantic-settings config loaded from env vars
- `backend/requirements.txt`
- `backend/Dockerfile`
- `ml/requirements.txt` (kept separate from backend runtime deps)
- `docker-compose.yml` — `db` (Postgres) + `backend` services; `frontend` service stubbed/commented, enabled in Phase 11
- `.env.example`, `.gitignore`
- Full directory skeleton for `backend/app/{core,api/v1,models,schemas,services,ml,db,utils}`, `frontend/src/{components,pages,services,hooks,types,utils}`, `ml/{datasets,notebooks,preprocessing,training,evaluation,models}`
- `README.md`, this file

**What was implemented:**
- Monorepo structure matching the spec exactly.
- Minimal FastAPI app that boots and serves a real `/health` check (verified — see "Test results" below).
- Config layer reads all settings from environment variables, no hardcoded secrets.
- Docker Compose brings up Postgres + backend; healthcheck gates backend startup on DB readiness.

**Test results (actually run, not claimed):**
- `pip install -r backend/requirements.txt` — succeeded in a clean venv.
- `uvicorn app.main:app` started successfully; `GET /health` returned `{"status":"ok","service":"GreenFarm Carbon AI"}` with HTTP 200.
- Did **not** yet test `docker compose up` (no Docker daemon in this sandboxed session) — you should run this locally before Phase 2 and report back if it fails.

**Assumptions made:**
- Postgres 16-alpine as the DB image (spec didn't pin a version).
- `SECRET_KEY`/`POSTGRES_PASSWORD` placeholders in `.env.example` — you must replace before running for real.
- Frontend Dockerfile/service intentionally deferred to Phase 11 rather than stubbed with a fake Vite app, per the "don't generate everything in one step" rule.

**What remains for Phase 2:**
- Source or construct the raw agriculture dataset(s).
- Document dataset origin, license, and known gaps against the required schema (`crop_type`, `fertilizer_usage_kg_per_ha`, `fuel_consumption_liters_per_ha`, `water_consumption_m3_per_ha`, `electricity_consumption_kwh_per_ha`, `carbon_footprint_kg_co2e_per_ha`).
- Initial exploration notebook/script: shape, dtypes, missingness, distributions.

---
## Phase 2 — Dataset preparation & exploration ✅

**Files created:**
- `ml/preprocessing/crop_parameter_ranges.py` — per-crop input ranges, each flagged `UNVERIFIED` pending citation
- `ml/preprocessing/generate_raw_dataset.py` — generates raw farm data from those ranges
- `ml/datasets/raw_farm_data.csv` — 6,000 rows, 6 crop types
- `ml/notebooks/01_data_exploration.py` — real EDA script
- `ml/datasets/RAW_DATASET_SOURCES.md` — full search log and methodology

**What was implemented:**
- Searched GitHub (only reachable external data source) for a real dataset matching the required schema — none exists (see `RAW_DATASET_SOURCES.md` for the full log and why each candidate was rejected).
- Built a documented raw-data generator instead of fabricating a target metric: per-crop ranges for fertilizer/fuel/water/electricity, sampled via triangular distribution, with a shared "mechanization" factor correlating fuel and electricity use per farm.
- Deliberately injected 2% missing values and ~1%/column outliers so Phase 4 has real cleaning work to do — documented, not accidental.
- **No carbon-footprint target yet** — computed properly in Phase 3 from real emission factors, kept as a separate auditable step.

**Test results (actually run):**
- `generate_raw_dataset.py` ran successfully → 6,000 rows written to `ml/datasets/raw_farm_data.csv`.
- `01_data_exploration.py` ran successfully. Real findings: shape (6000, 6); 2.0% missing per numeric column as designed; 0 duplicate `farm_id`s; per-crop means directionally sane (e.g. Sugarcane highest water at ~17,945 m³/ha, Soybean lowest fertilizer at ~46 kg/ha); IQR scan found 58–131 outliers per column.

**Assumptions made (flagged prominently, user confirmed this approach):**
- Per-crop input ranges are illustrative, sourced from general agronomic knowledge, **not yet cited to a live authoritative source** — this sandbox has no general web access to verify. Must be replaced with real citations before academic submission.
- 6 crop types chosen (Rice, Wheat, Maize, Soybean, Sugarcane, Cotton) as commonly-studied, agronomically distinct crops.
- 1,000 samples/crop (6,000 total) — reasonable size for the model comparison in Phase 5, adjustable later.

**What remains for Phase 3:**
- Build `emission_factors.py` with real, cited IPCC-style emission factors.
- Build the transparent calculation pipeline (fertilizer + fuel + electricity + irrigation-related emissions → total).
- Compute `carbon_footprint_kg_co2e_per_ha` for every row and save the labeled dataset.

---
## Phase 3 — Carbon-footprint calculation & target generation ✅

**Files created:**
- `ml/preprocessing/emission_factors.py` — every constant labeled `[STANDARD]` / `[LITERATURE]` / `[ASSUMPTION]` with source and confidence
- `ml/preprocessing/carbon_footprint_calculator.py` — component-by-component calculation pipeline (fertilizer, fuel, electricity, irrigation energy)
- `ml/preprocessing/generate_labeled_dataset.py` — applies the pipeline, writes labeled dataset
- `ml/datasets/labeled_farm_data.csv` — raw inputs + 4 emission-component columns + final target

**What was implemented:**
- Fertilizer emissions: IPCC 2019 Refinement Tier 1 default (EF1 = 1% of applied N emitted as N2O-N, `[STANDARD]`) for direct field N2O, converted to CO2e via AR5 GWP100 = 265, plus upstream manufacturing emissions (`[LITERATURE]`, 3.7 kg CO2e/kg N). Blended-product N content assumed at 46% (`[ASSUMPTION]`, configurable).
- Fuel emissions: standard diesel combustion factor, 2.68 kg CO2e/liter (`[STANDARD]`).
- Electricity emissions: on-farm metered use x grid carbon intensity, defaulted to a global-average 0.5 kg CO2e/kWh (`[ASSUMPTION]` — flagged as the single most important constant to swap for regional accuracy).
- Irrigation emissions: modeled as embodied pumping energy (water volume x energy intensity x grid factor), **not** a direct per-m3 factor, per the spec's explicit instruction not to treat every m3 as equally emissive. Toggleable via `INCLUDE_IRRIGATION_ENERGY_EMISSIONS` with documented double-counting rationale against the electricity feature.
- Rows with missing raw inputs propagate `NaN` in the target rather than being silently imputed — Phase 4 owns that decision.

**Test results (actually run):**
- `generate_labeled_dataset.py` ran successfully → `labeled_farm_data.csv`, 6,000 rows.
- 5,537 rows got a computed target; 463 have `NaN` target (exactly matching the 2%/column missingness injected across 4 columns in Phase 2 — expected, not a bug).
- Target stats: mean 1,528.81 kg CO2e/ha, std 656.89, range [557.00, 6,523.07].
- Target by crop (highest → lowest): Sugarcane 2,680.66 → Rice 1,776.86 → Cotton 1,492.93 → Maize 1,426.63 → Wheat 1,034.00 → Soybean 741.01 — directionally consistent with each crop's fertilizer/water intensity, a useful sanity check that the pipeline isn't producing nonsense.
- Component contribution to the average total: irrigation energy 40.2%, fertilizer 35.3%, fuel 12.7%, electricity 11.8%.

**Assumptions made (all documented in `emission_factors.py`, several flagged for citation before final submission):**
- Fertilizer N content fraction (46%), manufacturing emission factor (3.7 kg CO2e/kg N), grid electricity intensity (0.5 kg CO2e/kWh, global average), irrigation pumping energy intensity (0.15 kWh/m3) are all `[LITERATURE]` or `[ASSUMPTION]` tier — swap for region-specific cited values before academic submission.
- IPCC Tier 1 N2O factor, N2O/N2 mass ratio, AR5 GWP100, and diesel combustion factor are `[STANDARD]` — high confidence, standard across ag-LCA tools.

**What remains for Phase 4:**
- Decide and implement missing-value handling for the 463 rows with `NaN` inputs/target (impute vs. drop).
- Outlier handling for the deliberately-injected outliers from Phase 2.
- Categorical encoding for `crop_type`.
- Train/test split.

---
## Phase 4 — ML preprocessing & feature engineering ✅

**Files created:**
- `ml/preprocessing/clean_and_split.py` — drops rows with missing inputs, IQR-caps outliers, recomputes target from cleaned inputs, stratified train/test split
- `ml/preprocessing/build_preprocessor.py` — fits and saves the `ColumnTransformer` (OneHotEncoder + StandardScaler), fit on train only
- `ml/datasets/train.csv` (4,429 rows) / `test.csv` (1,108 rows)
- `ml/models/preprocessor.joblib` — fitted encoder+scaler, verified to reload and transform correctly outside the fitting script

**What was implemented:**
- Missing values: rows with any missing input **dropped**, not imputed — the target is a deterministic function of the 4 inputs, so imputing an input would fabricate part of the label. Production inference (Phase 8) will reject incomplete requests with 422 for the same reason, rather than silently filling gaps.
- Outliers: IQR-based winsorization (capped to 1.5x-IQR bounds) rather than dropped, preserving sample size while neutralizing the extreme values deliberately injected in Phase 2.
- Target recomputed from the capped inputs using the Phase 3 calculator, so features and label stay consistent — the pre-cap target values were discarded.
- Train/test split: 80/20, stratified by `crop_type`, `random_state=42`.
- Preprocessing pipeline (`OneHotEncoder(handle_unknown="ignore")` for `crop_type`, `StandardScaler` for the 4 numeric features) fit **only on the training split**.
- Preprocessor saved via joblib — this exact fitted object will be loaded (never refit) at both training and inference time.
- No engineered/derived features beyond the 5 raw inputs — kept the feature set exactly aligned with what the prediction API can supply at inference time.

**Test results (actually run):**
- Missing-value handling: dropped 463 of 6,000 rows (7.72%) — matches the Phase 2/3 injected missingness exactly.
- Outlier capping: 65–111 values capped per column; post-cap target max fell from 6,523 → 3,020 kg CO2e/ha.
- Split: 4,429 train / 1,108 test rows; crop-type proportions match to within 0.3% between splits (stratification confirmed).
- Train vs. test target means nearly identical (1,507.55 vs. 1,509.46) — no leakage-driven skew.
- Preprocessor: input shape (4429, 5) → output shape (4429, 10) (6 one-hot crop columns + 4 scaled numeric).
- **Verified** the saved preprocessor round-trips correctly on `test.csv` (1108, 10 output, no NaNs) and on a single inference-shaped row matching the future `POST /api/v1/predictions/carbon` schema.

**Assumptions made:**
- Outliers treated as likely data-entry noise (capped) rather than genuine rare farms (dropped) — reasonable given they were deliberately injected in Phase 2, worth reconsidering with a real dataset.
- No engineered interaction/derived features — prioritized inference-time simplicity over marginal accuracy gains.

**What remains for Phase 5:**
- Train Linear Regression, Random Forest, and XGBoost using `train.csv` + the saved preprocessor.
- Cross-validation, comparison table, model selection based on actual held-out performance.

---
---
## Phase 5 — Train Linear Regression, Random Forest, and XGBoost ✅

**Files created:**
- `ml/training/train_models.py` — 5-fold cross-validation comparison of all three models, using the Phase 4 preprocessor (never refit here)

**What was implemented:**
- Loaded `train.csv`, transformed via the saved `preprocessor.joblib` (fit-once-in-Phase-4, loaded not refit).
- 5-fold CV (`KFold`, `shuffle=True`, `random_state=42`) on the training set only — `test.csv` stays untouched until Phase 6's final held-out evaluation.
- Compared MAE, RMSE, R² across Linear Regression, Random Forest (200 trees), XGBoost (300 trees, depth 5, lr 0.05).

**Test results (actually run, real cross-validation output):**

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Linear Regression | 0.00 ± 0.00 | 0.00 ± 0.00 | 1.0000 ± 0.0000 |
| Random Forest | 16.03 ± 0.74 | 28.39 ± 4.74 | 0.9978 ± 0.0007 |
| XGBoost | 11.36 ± 0.57 | 18.25 ± 2.48 | 0.9991 ± 0.0003 |

**Important, flagged honestly (not hidden in the numbers table):** Linear Regression's perfect score is an artifact, not a genuine win — `carbon_footprint_kg_co2e_per_ha` is an exact linear combination of the 4 numeric inputs by construction (Phase 3's calculator sums fixed-factor multiples of each input), so Linear Regression can fit it exactly. Random Forest and XGBoost can only approximate a continuous linear function via splits, so their near-perfect-but-not-perfect scores are expected, not a weakness. This synthetic-label artifact means the comparison doesn't reflect what a real-world (noisy, nonlinear) carbon-prediction problem would look like — noted here and in the eventual project report so it isn't presented as more meaningful than it is.

**Model selection (user-confirmed):** **XGBoost**, not the mathematically-perfect Linear Regression — chosen for deployment realism and because it supports the real feature-importance explainability the spec requires in Phase 8, rather than for topping this particular (somewhat artificial) leaderboard.

**Assumptions made:**
- Model hyperparameters (RF: 200 trees; XGBoost: 300 trees, depth 5, learning rate 0.05) are reasonable defaults, not tuned — hyperparameter tuning wasn't in scope for this phase and can be added in Phase 6 if you want it.

**What remains for Phase 6:**
- Final evaluation of XGBoost on the held-out `test.csv` (first real look at the test set).
- Feature importance extraction (real values from the trained model, per the spec's explainability requirement).
- Save the final model via joblib to `ml/models/carbon_model.joblib`.
- Assemble the model evaluation report (dataset size, features, metrics, feature importance) with actual values only.

---
---
## Phase 6 — Evaluate models & save the best model ✅

**Files created:**
- `ml/evaluation/evaluate_and_save.py` — trains all 3 models on full `train.csv`, evaluates on `test.csv` (first touch of the held-out set), extracts feature importance, saves the final model
- `ml/models/carbon_model.joblib` — final XGBoost model
- `ml/evaluation/test_set_results.json` — raw results
- `ml/evaluation/model_evaluation_report.md` — full report: dataset, features, target, preprocessing, models, metrics, feature importance

**What was implemented:**
- All 3 models trained on the full training set and evaluated on `test.csv` for the first time — confirms the Phase 5 CV numbers weren't a fluke of the fold split.
- Real feature importance extracted from the trained XGBoost model (`model.feature_importances_`), not invented.
- Model saved via joblib to the exact path (`ml/models/carbon_model.joblib`) the spec requires.

**Test results (actually run — held-out test set, first touch):**

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Linear Regression | ~0.00 | ~0.00 | 1.0000 |
| Random Forest | 15.03 | 30.98 | 0.9974 |
| XGBoost | 11.08 | 18.84 | 0.9990 |

Closely matches Phase 5's cross-validation numbers (XGBoost: CV R²=0.9991 vs. test R²=0.9990) — no overfitting surprise.

**Feature importance (real, from the trained model):** water consumption 63.94%, crop_type_Rice 22.89%, fertilizer 6.51%, remaining crop-type/fuel/electricity columns under 4% each.

**Important finding, flagged honestly:** this importance ranking does **not** match the Phase 3 emission-component breakdown (irrigation 40.2% / fertilizer 35.3% of the average total). That's expected, not a contradiction — feature importance reflects how much a feature helps explain variance across the dataset (correlated with a feature's range/spread), while the Phase 3 breakdown reflects average magnitude contribution to any single farm's total. Water's huge range (3,000–20,000 m³/ha) makes it dominate importance even though fertilizer contributes a comparable average share. Full explanation in `model_evaluation_report.md`.

**Assumptions made:** none beyond those already documented in Phases 1–5 (hyperparameters still untuned defaults).

**What remains for Phase 7:**
- Build out the FastAPI backend routers (`auth`, `farms`, `predictions`, `dashboard`) — currently only `/health` exists.
- Pydantic request/response schemas matching the prediction API contract.

---
---
## Phase 7 — FastAPI backend build-out ✅

**Files created:**
- `backend/app/schemas/{auth,crop_type,farm,prediction,dashboard}.py` — full request/response contracts
- `backend/app/api/v1/{auth,farms,predictions,dashboard}.py` — routers wired into `main.py`
- `backend/tests/test_predictions_validation.py` — 9 real tests

**Files modified:**
- `backend/app/main.py` — routers registered
- `backend/requirements.txt` — added `pydantic[email]` (see bug below)

**What was implemented:**
- Full API surface for all 4 domains (`auth`, `farms`, `predictions`, `dashboard`) with real Pydantic validation live now.
- `crop_type` restricted to an `Enum` matching exactly the 6 crops the trained model's `OneHotEncoder` was fit on (Rice/Wheat/Maize/Soybean/Sugarcane/Cotton) — an unsupported crop is a clean 422, not a silently degraded prediction.
- Prediction request validation matches the spec exactly: `fertilizer_usage_kg_per_ha > 0`, `fuel/water/electricity >= 0`.
- Endpoints that depend on not-yet-built pieces (DB in Phase 9, JWT in Phase 10, ML model in Phase 8) return **501 with a clear message pointing to the phase that implements them** — deliberately not stubbed with fake data, per the "never hardcode predictions/dashboard stats" rules.

**Test results (actually run):**
- 9/9 tests passed: negative fertilizer/fuel/water/electricity → 422, zero fertilizer → 422 (must be `>0` not `>=0`), invalid crop type → 422, missing field → 422, valid payload clears validation and correctly reaches the 501 stub, `/health` → 200.
- Booted the full app and hit it live: OpenAPI schema lists all 7 routes correctly; a live invalid request returns a proper 422 with a clear Pydantic error message.
- **Caught and fixed a real bug**: `EmailStr` requires the `email-validator` package, which wasn't in `requirements.txt` — tests failed to even collect until this was added. Fixed in the requirements file, not just the local venv.

**Assumptions made:**
- `crop_type` uses a fixed enum rather than a free string, tied to the model's training data — means adding a new crop later requires retraining the model AND updating this enum together (documented here so that dependency isn't a surprise).

**What remains for Phase 8:**
- Load `carbon_model.joblib` + `preprocessor.joblib` in a service module.
- Replace the `/predictions/carbon` 501 stub with real inference.
- Add the "valid request → successful prediction" test that was deliberately deferred from Phase 7.

---
---
## Phase 8 — Integrate trained model with FastAPI ✅

**Files created:**
- `backend/app/ml/model_loader.py` — cached model/preprocessor loading with dual-path resolution (cwd-relative for Docker, repo-root fallback for local dev) and a distinct `ModelLoadError`
- `backend/app/services/carbon_category.py` — categorization using real quartiles from `train.csv` (Q1=1015.56, median=1431.53, Q3=1748.27), not arbitrary numbers
- `backend/app/services/prediction_service.py` — real inference: builds the feature row, transforms via the saved preprocessor, predicts via the saved model

**Files modified:**
- `backend/app/api/v1/predictions.py` — real inference replaces the 501 stub; model/inference errors return 503/500 without leaking internals
- `backend/app/schemas/prediction.py` — `sustainability_score`/`recommendations` made optional/default-empty (they're rule-based systems landing in Phase 13, not part of ML integration)
- `backend/tests/test_predictions_validation.py` — added real prediction tests, removed the now-obsolete 501 test

**What was implemented:**
- `/api/v1/predictions/carbon` now calls the actual trained XGBoost model — no hardcoded numbers anywhere in the path.
- Model-loading errors surface as 503 with a generic message; other unexpected errors as 500 — stack traces never reach the client (spec's error-handling requirement).

**Real bug caught and fixed:** the saved `preprocessor.joblib`/`carbon_model.joblib` were pickled with scikit-learn 1.9.0 (from unpinned installs in earlier phases' throwaway venvs) while `backend/requirements.txt` pins 1.5.2 — sklearn's `InconsistentVersionWarning` surfaced this during testing. **Regenerated both artifacts using the exact pinned `ml/requirements.txt` versions** to eliminate the mismatch, and reran evaluation to confirm results didn't meaningfully drift (XGBoost test R²: 0.9990 → 0.9991, MAE 11.08 → 10.68 — consistent, not a fluke of the version change).

**Test results (actually run):**
- 11/11 tests passed, including a cross-check that the API's prediction exactly matches calling `model.predict(preprocessor.transform(...))` directly, and a mocked-failure test confirming a 503 with no internal details leaked.
- Live server test: Sugarcane (high fertilizer/water) → 2,500.44 kg CO2e/ha, "Very High"; Soybean (low inputs) → 712.59, "Low" — directionally correct, consistent with every prior phase's findings.
- Warning-free test run after the version fix (previously showed 3 `InconsistentVersionWarning`s).

**Assumptions made:**
- Category thresholds are fixed quartiles from this training run — will need recomputation if the model is retrained on different/expanded data (noted in the module itself).

**What remains for Phase 9:**
- SQLAlchemy models for User/Farm/Prediction/Recommendation.
- Alembic migrations.
- Wire the farms/predictions routers to real persistence (replacing their 501 stubs).

---
## Phase 9 — PostgreSQL database ⏳ not started
## Phase 10 — Authentication ⏳ not started
## Phase 11 — React frontend scaffold ⏳ not started
## Phase 12 — Prediction dashboard UI ⏳ not started
## Phase 13 — Sustainability scoring & recommendations ⏳ not started
## Phase 14 — Historical analytics ⏳ not started
## Phase 15 — Testing, security, Docker, final cleanup ⏳ not started
