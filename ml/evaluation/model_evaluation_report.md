# Model Evaluation Report

All values below come from actually running the pipeline in this session
(`ml/preprocessing/*`, `ml/training/train_models.py`,
`ml/evaluation/evaluate_and_save.py`) — none are estimated or assumed.

## Dataset

- **Source:** synthetically generated from documented per-crop parameter
  ranges (see `ml/datasets/RAW_DATASET_SOURCES.md` for why — no reachable
  real dataset combined the required schema). Target computed from
  documented IPCC-style emission factors (`ml/preprocessing/emission_factors.py`).
- **Raw size:** 6,000 rows, 6 crop types (1,000 rows each).
- **Missing values:** 2% per numeric column injected in Phase 2 (documented,
  not a real data quality issue) → 463 rows (7.72%) dropped during cleaning
  because the target is a deterministic function of the inputs (imputing
  inputs would fabricate part of the label).
- **After cleaning + split:** 4,429 train rows / 1,108 test rows (80/20,
  stratified by `crop_type`).

## Features

| Feature | Type | Unit |
|---|---|---|
| `crop_type` | categorical (6 values) | — |
| `fertilizer_usage_kg_per_ha` | numeric | kg/ha |
| `fuel_consumption_liters_per_ha` | numeric | L/ha |
| `water_consumption_m3_per_ha` | numeric | m³/ha |
| `electricity_consumption_kwh_per_ha` | numeric | kWh/ha |

## Target

`carbon_footprint_kg_co2e_per_ha` — computed as the sum of fertilizer
(field N2O + manufacturing), fuel (diesel combustion), electricity, and
irrigation-energy emissions. See `ml/preprocessing/carbon_footprint_calculator.py`.

## Preprocessing

- Outliers (deliberately injected in Phase 2, ~1%/column): IQR-capped
  (1.5x whiskers), target recomputed from capped inputs.
- Categorical encoding: `OneHotEncoder(handle_unknown="ignore")` on `crop_type`.
- Numeric scaling: `StandardScaler` on the 4 numeric features.
- Fitted **once** on the training split, saved to `ml/models/preprocessor.joblib`,
  reused (never refit) for test evaluation and will be reused for inference.

## Models tested

Linear Regression, Random Forest (200 trees), XGBoost (300 trees, depth 5,
learning rate 0.05). Hyperparameters are reasonable defaults, not tuned.

## Results — 5-fold cross-validation (training set only, Phase 5)

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Linear Regression | 0.00 ± 0.00 | 0.00 ± 0.00 | 1.0000 ± 0.0000 |
| Random Forest | 16.03 ± 0.74 | 28.39 ± 4.74 | 0.9978 ± 0.0007 |
| XGBoost | 11.36 ± 0.57 | 18.25 ± 2.48 | 0.9991 ± 0.0003 |

## Results — held-out test set (first touch of test.csv, Phase 6)

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Linear Regression | ~0.00 | ~0.00 | 1.0000 |
| Random Forest | 15.03 | 30.98 | 0.9974 |
| XGBoost | 11.08 | 18.84 | 0.9990 |

Test-set results closely match cross-validation results for all three
models — no evidence of overfitting to the training folds.

**Note on Linear Regression's perfect score:** this is a real result, not
fabricated, but it's an artifact of how the target was constructed —
`carbon_footprint_kg_co2e_per_ha` is an exact linear combination of the 4
numeric inputs by design (Phase 3), so Linear Regression can fit it
exactly. This doesn't reflect what a real-world (noisy, nonlinear) version
of this problem would look like.

## Best model

**XGBoost**, selected over the mathematically-perfect Linear Regression for
deployment realism and because it provides genuine feature-importance
explainability (below), which the project spec requires. Saved to
`ml/models/carbon_model.joblib`.

## Feature importance (real values, extracted from the trained XGBoost model)

| Feature | Importance |
|---|---|
| Water consumption | 63.94% |
| Crop type: Rice | 22.89% |
| Fertilizer usage | 6.51% |
| Crop type: Soybean | 3.04% |
| Electricity consumption | 1.55% |
| Crop type: Wheat | 0.93% |
| Fuel consumption | 0.84% |
| Crop type: Sugarcane | 0.16% |
| Crop type: Maize | 0.07% |
| Crop type: Cotton | 0.07% |

**Why this differs from the Phase 3 emission-component breakdown**
(irrigation 40.2% / fertilizer 35.3% / fuel 12.7% / electricity 11.8% of
the *average total*): feature importance measures how much a feature helps
the model reduce prediction error *across the dataset's variance*, which
correlates with a feature's range/spread — not its average magnitude
contribution to any single farm's total. Water varies far more (3,000–20,000
m³/ha across crops) than fertilizer does, so it dominates importance even
though the two contribute comparable average shares to the target formula.
`crop_type_Rice` scoring highly reflects the model using "is this Rice?" as
a proxy for Rice's distinctly high water range, not a separate causal
effect of the crop label itself — the calculation pipeline in Phase 3 does
not use `crop_type` at all.
