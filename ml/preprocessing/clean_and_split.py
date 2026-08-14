"""
Phase 4, step 1: clean the labeled dataset and split into train/test.

Missing values
--------------
The target is a DETERMINISTIC function of the 4 numeric inputs (see
carbon_footprint_calculator.py). Imputing a missing input would mean
fabricating part of the label from a guess, not from the farm's actual
practices — so rows with ANY missing input are dropped, not imputed.
This mirrors production behavior: the FastAPI prediction endpoint (Phase 8)
will reject incomplete requests with 422, not silently fill gaps either.

Outliers
--------
The raw dataset deliberately contains injected outliers (Phase 2, ~1% per
numeric column, 2.5-4x multiplier) to simulate data-entry errors or
genuinely atypical farms. These are treated as likely erroneous rather than
dropped outright (dropping would lose real farms too, since some legitimately
sit at the edge of the distribution) — instead they're WINSORIZED (capped)
to the 1.5x-IQR bounds per column. The carbon-footprint target is then
RECOMPUTED from the capped inputs so target and features stay consistent.

Split
-----
80/20 train/test, stratified by crop_type so both sets have proportional
representation of all 6 crops, fixed random_state for reproducibility.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

from carbon_footprint_calculator import compute_carbon_footprint

LABELED_PATH = "../datasets/labeled_farm_data.csv"
TRAIN_PATH = "../datasets/train.csv"
TEST_PATH = "../datasets/test.csv"

NUMERIC_COLUMNS = [
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]

RAW_INPUT_COLUMNS = ["farm_id", "crop_type"] + NUMERIC_COLUMNS


def drop_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=NUMERIC_COLUMNS).copy()
    after = len(df)
    print(f"Missing-value handling: dropped {before - after} of {before} rows "
          f"({(before - after) / before * 100:.2f}%) with at least one missing input.")
    return df


def winsorize_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    print("\nOutlier handling (IQR capping, 1.5x whiskers):")
    for col in NUMERIC_COLUMNS:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_capped = ((df[col] < lower) | (df[col] > upper)).sum()
        df[col] = df[col].clip(lower=max(lower, 0), upper=upper)
        print(f"  {col}: capped {n_capped} values to [{max(lower, 0):.1f}, {upper:.1f}]")
    return df


def main():
    df = pd.read_csv(LABELED_PATH)[RAW_INPUT_COLUMNS]
    print(f"Loaded {len(df)} rows.\n")

    df = drop_missing_rows(df)
    df = winsorize_outliers(df)

    # Recompute the target from the (now capped) inputs so features and
    # target stay consistent — the pre-cap target is discarded.
    df = compute_carbon_footprint(df)
    assert df["carbon_footprint_kg_co2e_per_ha"].isna().sum() == 0, \
        "Target should be fully computable after dropping missing rows."

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["crop_type"]
    )

    train_df.to_csv(TRAIN_PATH, index=False)
    test_df.to_csv(TEST_PATH, index=False)

    print(f"\nFinal clean dataset: {len(df)} rows")
    print(f"Train: {len(train_df)} rows -> {TRAIN_PATH}")
    print(f"Test:  {len(test_df)} rows -> {TEST_PATH}")

    print("\nCrop distribution — train:")
    print(train_df["crop_type"].value_counts(normalize=True).round(3))
    print("\nCrop distribution — test:")
    print(test_df["crop_type"].value_counts(normalize=True).round(3))

    print("\nTarget stats — train:")
    print(train_df["carbon_footprint_kg_co2e_per_ha"].describe().round(2))
    print("\nTarget stats — test:")
    print(test_df["carbon_footprint_kg_co2e_per_ha"].describe().round(2))


if __name__ == "__main__":
    main()
