"""
Phase 13B: rule-based recommendation engine.

Purely deterministic — no LLM, no randomness. Every recommendation is
triggered by comparing the farm's actual inputs against fixed, documented
thresholds derived from train.csv's per-feature quartiles (see the
`_Q3` constants below), so "high" means "top quartile of the training
distribution", not a guess.

Each returned item is (category, text) — category matches the
Recommendation.category column ("fertilizer" | "fuel" | "water" |
"electricity" | "general").
"""

# [DATA-DERIVED] Q3 (75th percentile) of each numeric feature in train.csv,
# post Phase 4 cleaning. "High usage" == above this threshold.
FERTILIZER_Q3 = 186.07     # kg/ha
FUEL_Q3 = 84.01            # liters/ha
WATER_Q3 = 10104.55        # m3/ha
ELECTRICITY_Q3 = 446.21    # kWh/ha


def generate_recommendations(
    fertilizer_usage_kg_per_ha: float,
    fuel_consumption_liters_per_ha: float,
    water_consumption_m3_per_ha: float,
    electricity_consumption_kwh_per_ha: float,
    carbon_category: str,
) -> list[tuple[str, str]]:
    recommendations: list[tuple[str, str]] = []

    if fertilizer_usage_kg_per_ha > FERTILIZER_Q3:
        recommendations.append((
            "fertilizer",
            "Fertilizer usage is in the top quartile for this crop. Consider soil-test-based "
            "fertilizer management to apply only what the soil actually needs, reducing both "
            "N2O emissions and cost.",
        ))

    if fuel_consumption_liters_per_ha > FUEL_Q3:
        recommendations.append((
            "fuel",
            "Fuel consumption is high. Reduce unnecessary machinery passes, combine field "
            "operations where possible, and keep engines properly maintained to cut diesel use.",
        ))

    if water_consumption_m3_per_ha > WATER_Q3:
        recommendations.append((
            "water",
            "Water consumption is high. Efficient irrigation methods (drip/sprinkler) and "
            "scheduling based on real soil-moisture needs can meaningfully cut both water and "
            "the pumping energy behind it.",
        ))

    if electricity_consumption_kwh_per_ha > ELECTRICITY_Q3:
        recommendations.append((
            "electricity",
            "On-farm electricity use is high. Efficient irrigation pumps and, where feasible, "
            "renewable electricity sources (solar pumping) can reduce this footprint component.",
        ))

    if carbon_category in ("High", "Very High"):
        recommendations.append((
            "general",
            "Overall carbon footprint is high for this farm. Focus first on the largest "
            "contributing input above rather than making small changes across every category.",
        ))

    if not recommendations:
        recommendations.append((
            "general",
            "All major inputs are within a typical range for this crop. Maintain current "
            "practices and continue monitoring year over year.",
        ))

    # Cap at 5 recommendations, per the result-page spec ("show 3-5").
    return recommendations[:5]
