"""
Generate the raw farm-level input dataset.

Samples fertilizer/fuel/water/electricity usage per crop from the ranges in
crop_parameter_ranges.py using a triangular distribution (peaked at the
range midpoint, so most farms cluster near "typical" practice with fewer at
the extremes — more realistic than pure uniform sampling).

To make later pipeline phases (missing-value handling, outlier analysis)
meaningful rather than trivial, this script deliberately injects:
- ~2% missing values (MCAR) across the numeric columns
- ~1% high-outlier rows per numeric column (simulating data-entry errors /
  genuinely atypical farms)
Both are documented here, not hidden — Phase 4 will handle them explicitly.

Output: ml/datasets/raw_farm_data.csv
No carbon_footprint column yet — that's computed in Phase 3 from documented
emission factors, deliberately kept as a separate, auditable step.
"""
import numpy as np
import pandas as pd

from crop_parameter_ranges import CROP_PARAMETER_RANGES

RNG_SEED = 42
SAMPLES_PER_CROP = 1000
MISSING_FRACTION = 0.02
OUTLIER_FRACTION = 0.01

NUMERIC_COLUMNS = [
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]


def sample_triangular(rng: np.random.Generator, low: float, high: float, size: int) -> np.ndarray:
    mode = (low + high) / 2
    return rng.triangular(left=low, mode=mode, right=high, size=size)


def generate_raw_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(RNG_SEED)
    rows = []

    for crop, params in CROP_PARAMETER_RANGES.items():
        n = SAMPLES_PER_CROP
        fert_low, fert_high = params["fertilizer_usage_kg_per_ha"]
        fuel_low, fuel_high = params["fuel_consumption_liters_per_ha"]
        water_low, water_high = params["water_consumption_m3_per_ha"]
        elec_low, elec_high = params["electricity_consumption_kwh_per_ha"]

        fertilizer = sample_triangular(rng, fert_low, fert_high, n)
        water = sample_triangular(rng, water_low, water_high, n)

        # Fuel and electricity are mildly correlated with each other (more
        # mechanized farms tend to use more of both) — modeled by drawing a
        # shared "mechanization" factor per farm and nudging both by it.
        mechanization = rng.normal(loc=0.0, scale=0.15, size=n)
        fuel = sample_triangular(rng, fuel_low, fuel_high, n) * (1 + mechanization)
        electricity = sample_triangular(rng, elec_low, elec_high, n) * (1 + mechanization)

        fuel = np.clip(fuel, fuel_low * 0.7, fuel_high * 1.3)
        electricity = np.clip(electricity, elec_low * 0.7, elec_high * 1.3)

        crop_df = pd.DataFrame(
            {
                "crop_type": crop,
                "fertilizer_usage_kg_per_ha": fertilizer,
                "fuel_consumption_liters_per_ha": fuel,
                "water_consumption_m3_per_ha": water,
                "electricity_consumption_kwh_per_ha": electricity,
            }
        )
        rows.append(crop_df)

    df = pd.concat(rows, ignore_index=True)
    df = df.sample(frac=1, random_state=RNG_SEED).reset_index(drop=True)
    df.insert(0, "farm_id", [f"FARM-{i:05d}" for i in range(1, len(df) + 1)])

    # Round to sensible precision
    for col in NUMERIC_COLUMNS:
        df[col] = df[col].round(2)

    df = inject_outliers(df, rng)
    df = inject_missing_values(df, rng)
    return df


def inject_outliers(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    df = df.copy()
    n_outliers = int(len(df) * OUTLIER_FRACTION)
    for col in NUMERIC_COLUMNS:
        idx = rng.choice(df.index, size=n_outliers, replace=False)
        multiplier = rng.uniform(2.5, 4.0, size=n_outliers)
        df.loc[idx, col] = df.loc[idx, col] * multiplier
    return df


def inject_missing_values(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    df = df.copy()
    n_missing = int(len(df) * MISSING_FRACTION)
    for col in NUMERIC_COLUMNS:
        idx = rng.choice(df.index, size=n_missing, replace=False)
        df.loc[idx, col] = np.nan
    return df


if __name__ == "__main__":
    dataset = generate_raw_dataset()
    output_path = "../datasets/raw_farm_data.csv"
    dataset.to_csv(output_path, index=False)
    print(f"Generated {len(dataset)} rows -> {output_path}")
    print(dataset.head())
