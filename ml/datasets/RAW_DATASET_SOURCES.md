# Raw Dataset — Sourcing Log & Methodology

## What was searched

This environment can only reach `api.github.com` / `raw.githubusercontent.com`
for external data (no Kaggle, UCI ML Repository, FAO AQUASTAT, or national
ag-statistics portals). Searched via GitHub's repository search API for:
`agriculture carbon footprint dataset`, `crop_type fertilizer_usage
carbon_footprint`, `farm carbon emission dataset csv`, `agricultural
emissions machine learning dataset`, `sustainable farming carbon prediction
dataset`.

## Candidates found and why each was rejected

| Repository | Contents | Why rejected |
|---|---|---|
| `Aathika27/Shell-internship` | `Food_Production.csv` — the Poore & Nemecek food-LCA dataset (43 food products, land/water/GHG per kg of food) | Product-level, not farm-operational-input level. No fertilizer/fuel/electricity columns, no per-farm granularity. |
| `thisisharshsah/Green-House-Emission` | 10,000-row synthetic dataset with crop type, fertilizer, soil/weather features, CO2/N2O emissions | Own README states values are "generated with random values ... for demonstration purposes." No fuel or electricity columns. Using its emissions column would mean training on fabricated targets — explicitly disallowed. |
| `madhulraokadam/ml-projects-green-scale-datasets`, `avin1403/Hybrid-Model-for-Crop-Yield-Prediction-and-GHG-Emission-Trade-off` | Yield/GHG tradeoff studies | Different schema (yield-focused), not farm input → carbon-footprint. |

**Conclusion:** no dataset reachable from this environment combines
`crop_type + fertilizer_usage + fuel_consumption + water_consumption +
electricity_consumption` at farm level with a defensible carbon-footprint
target. This was confirmed by search, not assumed.

## Approach taken

1. **Raw input features** (`ml/preprocessing/generate_raw_dataset.py`) are
   sampled from per-crop parameter ranges
   (`ml/preprocessing/crop_parameter_ranges.py`) drawn from general
   agronomic/water-footprint knowledge. **These ranges are flagged
   `UNVERIFIED` in the source file** — this sandbox has no live web access to
   pin exact citations. Before using this in a thesis/report, replace them
   with cited figures (FAO AQUASTAT for water, national fertilizer-use
   statistics, published LCA studies for fuel/electricity).
2. **Carbon-footprint target** (Phase 3, not yet done) will be computed from
   documented, real IPCC-style emission factors — not sampled or guessed.
   This keeps the ML target itself grounded in citable sources even though
   the input feature *distributions* are illustrative.
3. Missing values (2% per numeric column, MCAR) and outliers (1% per column,
   2.5–4x multiplier) were **deliberately injected** so Phase 4's
   missing-value handling and outlier analysis have real work to do, rather
   than being no-ops on a suspiciously clean dataset. This is documented
   here so it's never mistaken for a data quality problem in the generation
   logic.

## Generated dataset summary (from actually running the pipeline)

- 6,000 rows, 6 columns, 6 crop types (Rice, Wheat, Maize, Soybean,
  Sugarcane, Cotton), 1,000 rows each.
- 2.0% missing values per numeric column (120 of 6,000), as designed.
- 0 duplicate `farm_id`s, 0 fully duplicate rows.
- IQR-based outlier scan found 58–131 outliers per column (expected, given
  the deliberate injection plus natural triangular-distribution tails).
- Per-crop means are directionally consistent with the source ranges (e.g.
  Sugarcane highest water use at ~17,945 m³/ha, Soybean lowest fertilizer
  at ~46 kg/ha) — see `ml/notebooks/01_data_exploration.py` output for full
  detail.

Full EDA script: `ml/notebooks/01_data_exploration.py`.
