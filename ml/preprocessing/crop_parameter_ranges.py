"""
Per-crop parameter ranges for raw farm input data generation.

*** IMPORTANT — READ BEFORE USING THESE VALUES IN A THESIS/REPORT ***

No publicly reachable dataset (checked: GitHub search via api.github.com,
the only external data source this environment can reach — no Kaggle, UCI,
FAO AQUASTAT, or national ag-statistics portals) combines crop type,
fertilizer, fuel, water, and electricity use at farm level with a validated
carbon-footprint target. See ml/datasets/RAW_DATASET_SOURCES.md for the
search log.

The ranges below are illustrative, order-of-magnitude figures assembled
from general agronomic and water-footprint knowledge (the kind of numbers
that show up repeatedly across FAO reports, national ag-extension guides,
and water-footprint literature such as Mekonnen & Hoekstra). They are
UNVERIFIED against a live, citable source in this session because this
sandbox has no general web access.

Before this goes into a final report, replace `source` below with a real
citation for each crop (FAO AQUASTAT for water, national fertilizer-use
statistics, or published LCA studies for fuel/electricity), and adjust the
ranges accordingly. Everything downstream (dataset generation, training,
evaluation) reads from this file, so updating it here propagates everywhere.

Units:
- fertilizer_usage_kg_per_ha: kg/ha (N+P2O5+K2O combined, typical season application)
- fuel_consumption_liters_per_ha: liters of diesel/ha/season (tillage, transport, machinery)
- water_consumption_m3_per_ha: m3/ha/season (irrigation, excludes rainfall)
- electricity_consumption_kwh_per_ha: kWh/ha/season (irrigation pumps, on-farm equipment)
"""

CROP_PARAMETER_RANGES: dict = {
    "Rice": {
        "fertilizer_usage_kg_per_ha": (120, 180),
        "fuel_consumption_liters_per_ha": (60, 100),
        "water_consumption_m3_per_ha": (8000, 12000),  # flood irrigation — high by design
        "electricity_consumption_kwh_per_ha": (300, 600),
        "source": "UNVERIFIED — placeholder, replace with FAO AQUASTAT / national ag-extension citation",
    },
    "Wheat": {
        "fertilizer_usage_kg_per_ha": (100, 150),
        "fuel_consumption_liters_per_ha": (40, 70),
        "water_consumption_m3_per_ha": (3000, 5000),
        "electricity_consumption_kwh_per_ha": (150, 300),
        "source": "UNVERIFIED — placeholder, replace with cited source",
    },
    "Maize": {
        "fertilizer_usage_kg_per_ha": (150, 220),
        "fuel_consumption_liters_per_ha": (50, 90),
        "water_consumption_m3_per_ha": (4000, 6000),
        "electricity_consumption_kwh_per_ha": (200, 400),
        "source": "UNVERIFIED — placeholder, replace with cited source",
    },
    "Soybean": {
        "fertilizer_usage_kg_per_ha": (30, 60),  # nitrogen-fixing crop, lower N demand
        "fuel_consumption_liters_per_ha": (40, 70),
        "water_consumption_m3_per_ha": (3000, 5000),
        "electricity_consumption_kwh_per_ha": (150, 300),
        "source": "UNVERIFIED — placeholder, replace with cited source",
    },
    "Sugarcane": {
        "fertilizer_usage_kg_per_ha": (180, 250),
        "fuel_consumption_liters_per_ha": (80, 120),
        "water_consumption_m3_per_ha": (15000, 20000),  # very water-intensive
        "electricity_consumption_kwh_per_ha": (400, 700),
        "source": "UNVERIFIED — placeholder, replace with cited source",
    },
    "Cotton": {
        "fertilizer_usage_kg_per_ha": (120, 180),
        "fuel_consumption_liters_per_ha": (50, 80),
        "water_consumption_m3_per_ha": (6000, 9000),
        "electricity_consumption_kwh_per_ha": (250, 450),
        "source": "UNVERIFIED — placeholder, replace with cited source",
    },
}

CROP_TYPES = list(CROP_PARAMETER_RANGES.keys())
