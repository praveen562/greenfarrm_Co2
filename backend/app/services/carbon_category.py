"""
Carbon footprint categorization.

Thresholds are the actual quartiles of carbon_footprint_kg_co2e_per_ha in
ml/datasets/train.csv (computed once, after Phase 4 cleaning — see
PROGRESS.md Phase 8), not arbitrary round numbers. This ties "High"/"Low"
to how this training distribution actually looks, rather than an
unexplained guess. If the model is retrained on different data, these
should be recomputed.
"""

# [DATA-DERIVED] Quartiles of carbon_footprint_kg_co2e_per_ha in train.csv
# (4,429 rows, post-cleaning). Recompute if the training data changes.
Q1 = 1015.56
MEDIAN = 1431.53
Q3 = 1748.27


def categorize(carbon_footprint_kg_co2e_per_ha: float) -> str:
    if carbon_footprint_kg_co2e_per_ha < Q1:
        return "Low"
    if carbon_footprint_kg_co2e_per_ha < MEDIAN:
        return "Moderate"
    if carbon_footprint_kg_co2e_per_ha < Q3:
        return "High"
    return "Very High"
