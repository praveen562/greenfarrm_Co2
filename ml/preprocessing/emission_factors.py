"""
Emission factors used to compute carbon_footprint_kg_co2e_per_ha.

Every constant below is labeled with a confidence tier so it's clear which
numbers are standard/well-established vs. which are configurable
assumptions you should adjust for your region before final submission:

  [STANDARD]   Physical constants or IPCC Tier 1 defaults that are widely
               used across agricultural LCA tools. High confidence.
  [LITERATURE] Commonly cited in agricultural LCA literature, but this
               session has no live web access to pin an exact paper/report
               citation — verify before citing in a thesis.
  [ASSUMPTION] A simplifying modeling choice made explicit and configurable
               here specifically so it can be swapped without touching the
               calculation code.

Replacing any single constant here automatically changes every downstream
prediction, since the model is retrained on data generated from this file.
"""

# ---------------------------------------------------------------------------
# FERTILIZER — N2O emissions from field application + upstream manufacturing
# ---------------------------------------------------------------------------

# [ASSUMPTION] The raw dataset's fertilizer_usage_kg_per_ha is a blended
# N+P2O5+K2O product weight, not pure nitrogen. IPCC's N2O factor applies to
# applied nitrogen specifically, so we estimate the nitrogen fraction of a
# typical blended fertilizer product. 0.46 approximates urea-equivalent N
# content, a common reference point in ag-fertilizer literature.
FERTILIZER_N_CONTENT_FRACTION = 0.46

# [STANDARD] IPCC 2019 Refinement to the 2006 IPCC Guidelines for National
# GHG Inventories, Vol. 4, Ch. 11 — Tier 1 default emission factor EF1 for
# direct N2O emissions from synthetic nitrogen fertilizer applied to
# mineral soils: 1% of applied N is emitted as N2O-N.
N2O_EF1_KG_N2ON_PER_KG_N = 0.01

# [STANDARD] Molecular weight ratio to convert N2O-N (nitrogen mass basis)
# to N2O (full molecule mass). Physical constant: N2O = 44 g/mol, N2 = 28 g/mol.
N2O_N_TO_N2O_MASS_RATIO = 44 / 28

# [STANDARD] IPCC AR5 (2014) 100-year Global Warming Potential for N2O.
# (Note: AR6 revised this to 273; this project uses AR5's 265, the value
# most commonly paired with the IPCC 2019 Refinement Tier 1 factors above.)
GWP_N2O_100YR = 265

# [LITERATURE] Upstream (manufacturing) emissions per kg of nitrogen
# fertilizer produced — covers the Haber-Bosch process and associated
# energy use. Typical LCA studies (e.g. Brentrup-style N fertilizer LCAs)
# report values in the 3-5 kg CO2e/kg N range; 3.7 used as a mid-range
# placeholder. VERIFY against a specific cited study before final submission.
FERTILIZER_MANUFACTURING_KG_CO2E_PER_KG_N = 3.7


# ---------------------------------------------------------------------------
# FUEL — diesel combustion (tractors, harvesters, transport)
# ---------------------------------------------------------------------------

# [STANDARD] Widely cited diesel combustion emission factor (e.g. UK DEFRA /
# US EPA style factors converge in this range): ~2.68 kg CO2e per liter of
# diesel burned, covering CO2 plus small CH4/N2O contributions.
DIESEL_EMISSION_FACTOR_KG_CO2E_PER_LITER = 2.68


# ---------------------------------------------------------------------------
# ELECTRICITY — on-farm metered electricity (pumps, dryers, equipment)
# ---------------------------------------------------------------------------

# [ASSUMPTION] Global average grid carbon intensity. Grid intensity varies
# enormously by country (coal-heavy grids can exceed 0.8-0.9 kg CO2e/kWh;
# hydro/nuclear-heavy grids can be under 0.1). REPLACE with your region's
# actual grid emission factor (IEA, national utility, or EPA eGRID-style
# data) — this single number matters more than almost any other constant
# here for real-world accuracy.
GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2E_PER_KWH = 0.5


# ---------------------------------------------------------------------------
# WATER / IRRIGATION — energy embodied in delivering irrigation water
# ---------------------------------------------------------------------------
# Per the project spec: water itself has no direct emissions. What has
# emissions is the ENERGY used to pump/deliver it. We model irrigation
# emissions as (water volume) x (pumping energy intensity) x (grid factor),
# NOT as a direct per-m3 emission factor.

# [ASSUMPTION] Whether to include this term at all. Set False if your
# on-farm "electricity_consumption_kwh_per_ha" feature already fully
# captures irrigation pump electricity for your data source — including
# both would double-count. Default True here because this project's raw
# dataset treats electricity_consumption as general on-farm equipment/
# drying/processing use, separate from irrigation-specific pumping energy.
INCLUDE_IRRIGATION_ENERGY_EMISSIONS = True

# [LITERATURE] Blended average pumping energy intensity across irrigation
# methods (gravity-fed surface irrigation is near 0 kWh/m3; deep groundwater
# pumping can exceed 0.3-0.5 kWh/m3 depending on lift height). 0.15 kWh/m3
# is a commonly cited mid-range figure in irrigation-energy literature.
# VERIFY / replace with a water-source-specific figure for your region.
IRRIGATION_ENERGY_INTENSITY_KWH_PER_M3 = 0.15
