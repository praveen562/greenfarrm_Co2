"""
Transparent carbon footprint calculation pipeline.

carbon_footprint_kg_co2e_per_ha =
    fertilizer_emissions      (N2O field emissions + upstream manufacturing)
  + fuel_emissions            (diesel combustion)
  + electricity_emissions     (on-farm metered electricity x grid factor)
  + irrigation_energy_emissions   (water volume x pumping intensity x grid factor)

Every component is returned individually (not just the total) so the
calculation is auditable and so Phase-6+ explainability work can show
"where the emissions came from" per farm, not just a black-box number.

All constants live in emission_factors.py — nothing here is a magic number.
"""
import pandas as pd

import emission_factors as ef


def fertilizer_emissions_kg_co2e(fertilizer_usage_kg_per_ha: pd.Series) -> pd.Series:
    """N2O from field application (IPCC Tier 1) + upstream manufacturing."""
    n_applied = fertilizer_usage_kg_per_ha * ef.FERTILIZER_N_CONTENT_FRACTION

    n2o_n = n_applied * ef.N2O_EF1_KG_N2ON_PER_KG_N
    n2o = n2o_n * ef.N2O_N_TO_N2O_MASS_RATIO
    field_emissions = n2o * ef.GWP_N2O_100YR

    manufacturing_emissions = n_applied * ef.FERTILIZER_MANUFACTURING_KG_CO2E_PER_KG_N

    return field_emissions + manufacturing_emissions


def fuel_emissions_kg_co2e(fuel_consumption_liters_per_ha: pd.Series) -> pd.Series:
    """Diesel combustion emissions."""
    return fuel_consumption_liters_per_ha * ef.DIESEL_EMISSION_FACTOR_KG_CO2E_PER_LITER


def electricity_emissions_kg_co2e(electricity_consumption_kwh_per_ha: pd.Series) -> pd.Series:
    """On-farm metered electricity (equipment, drying, non-irrigation pumps)."""
    return electricity_consumption_kwh_per_ha * ef.GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2E_PER_KWH


def irrigation_energy_emissions_kg_co2e(water_consumption_m3_per_ha: pd.Series) -> pd.Series:
    """
    Energy embodied in delivering irrigation water — NOT a direct per-m3
    emission factor (water itself doesn't emit CO2; pumping it does).
    Returns all zeros if INCLUDE_IRRIGATION_ENERGY_EMISSIONS is False.
    """
    if not ef.INCLUDE_IRRIGATION_ENERGY_EMISSIONS:
        return water_consumption_m3_per_ha * 0.0
    pumping_energy_kwh = water_consumption_m3_per_ha * ef.IRRIGATION_ENERGY_INTENSITY_KWH_PER_M3
    return pumping_energy_kwh * ef.GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2E_PER_KWH


def compute_carbon_footprint(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds per-component emission columns and the final target column to df.
    Rows with missing inputs propagate NaN in the corresponding component
    and total — Phase 4 decides how to handle those (impute or drop), this
    function does not silently fill gaps.
    """
    df = df.copy()

    df["fertilizer_emissions_kg_co2e"] = fertilizer_emissions_kg_co2e(
        df["fertilizer_usage_kg_per_ha"]
    )
    df["fuel_emissions_kg_co2e"] = fuel_emissions_kg_co2e(
        df["fuel_consumption_liters_per_ha"]
    )
    df["electricity_emissions_kg_co2e"] = electricity_emissions_kg_co2e(
        df["electricity_consumption_kwh_per_ha"]
    )
    df["irrigation_energy_emissions_kg_co2e"] = irrigation_energy_emissions_kg_co2e(
        df["water_consumption_m3_per_ha"]
    )

    df["carbon_footprint_kg_co2e_per_ha"] = (
        df["fertilizer_emissions_kg_co2e"]
        + df["fuel_emissions_kg_co2e"]
        + df["electricity_emissions_kg_co2e"]
        + df["irrigation_energy_emissions_kg_co2e"]
    )

    return df
