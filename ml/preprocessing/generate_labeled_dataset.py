"""
Generate the labeled dataset: raw farm inputs + carbon_footprint_kg_co2e_per_ha
(plus per-component breakdown columns for transparency).

Reads:  ml/datasets/raw_farm_data.csv
Writes: ml/datasets/labeled_farm_data.csv
"""
import pandas as pd

from carbon_footprint_calculator import compute_carbon_footprint

RAW_PATH = "../datasets/raw_farm_data.csv"
LABELED_PATH = "../datasets/labeled_farm_data.csv"


def main():
    df = pd.read_csv(RAW_PATH)
    labeled = compute_carbon_footprint(df)
    labeled.to_csv(LABELED_PATH, index=False)

    print(f"Wrote {len(labeled)} rows -> {LABELED_PATH}")
    print("\nRows with a computed target (non-null):", labeled["carbon_footprint_kg_co2e_per_ha"].notna().sum())
    print("Rows with missing target (missing inputs, propagated as NaN):",
          labeled["carbon_footprint_kg_co2e_per_ha"].isna().sum())

    print("\n=== Target descriptive statistics (kg CO2e/ha) ===")
    print(labeled["carbon_footprint_kg_co2e_per_ha"].describe().round(2))

    print("\n=== Target by crop type (mean) ===")
    print(labeled.groupby("crop_type")["carbon_footprint_kg_co2e_per_ha"].mean().round(2).sort_values(ascending=False))

    print("\n=== Average emissions contribution by component (kg CO2e/ha) ===")
    components = [
        "fertilizer_emissions_kg_co2e",
        "fuel_emissions_kg_co2e",
        "electricity_emissions_kg_co2e",
        "irrigation_energy_emissions_kg_co2e",
    ]
    means = labeled[components].mean().round(2)
    total_mean = means.sum()
    for comp in components:
        pct = (means[comp] / total_mean * 100).round(1)
        print(f"{comp}: {means[comp]} ({pct}%)")


if __name__ == "__main__":
    main()
