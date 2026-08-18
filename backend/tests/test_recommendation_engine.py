"""
Recommendation engine tests — the redesigned, tiered, simulated-reduction
engine. Covers every scenario called out in the spec: low-input farm,
each single-high-input farm, a multi-high-input farm, and each supported
crop. All assertions are against the pure `build_recommendation_plan`
function — deterministic, no DB/network needed.
"""
from app.services.recommendation_engine import (
    CROP_CATEGORY_EMPHASIS,
    PROTOTYPE_MAX_COMBINED_REDUCTION_PERCENT,
    build_recommendation_plan,
)

BASELINE_FOOTPRINT = 1368.81
FARM_AREA = 10.0

# Values chosen from real train.csv medians so a "low-input" farm sits
# at or below every feature's median -> no recommendations triggered.
LOW_INPUTS = dict(
    fertilizer_usage_kg_per_ha=120.0,   # < median 150.57
    fuel_consumption_liters_per_ha=50.0,  # < median 67.36
    water_consumption_m3_per_ha=5000.0,   # < median 6504.13
    electricity_consumption_kwh_per_ha=250.0,  # < median 324.17
)


def _plan(crop_type="Wheat", **overrides):
    inputs = {**LOW_INPUTS, **overrides}
    return build_recommendation_plan(
        crop_type=crop_type,
        baseline_carbon_footprint=BASELINE_FOOTPRINT,
        farm_area_ha=FARM_AREA,
        **inputs,
    )


def test_low_input_farm_gets_no_recommendations():
    plan = _plan()
    assert plan.recommendations == []
    assert plan.estimated_total_reduction_percent == 0
    assert plan.estimated_total_reduction_kg_co2e_per_ha == 0
    assert plan.projected_carbon_footprint == round(BASELINE_FOOTPRINT, 2)
    assert plan.estimated_total_reduction_kg_co2e_per_farm == 0
    assert "simulated" in plan.simulation_notice.lower()


def test_high_fertilizer_farm():
    plan = _plan(fertilizer_usage_kg_per_ha=1000.0)  # far above Q90 (214.87) -> Very High
    categories = [r.category for r in plan.recommendations]
    assert "Fertilizer" in categories
    fert = next(r for r in plan.recommendations if r.category == "Fertilizer")
    assert fert.priority == "High"
    assert 12 <= fert.estimated_reduction_percent <= 18
    assert fert.estimated_reduction_kg_co2e_per_ha == round(BASELINE_FOOTPRINT * fert.estimated_reduction_percent / 100, 2)
    assert fert.projected_footprint_kg_co2e_per_ha == round(BASELINE_FOOTPRINT - fert.estimated_reduction_kg_co2e_per_ha, 2)
    # Only fertilizer is elevated -> it should be the sole/first recommendation.
    assert categories[0] == "Fertilizer"


def test_high_water_farm():
    plan = _plan(water_consumption_m3_per_ha=18000.0)  # above Q90 17316.8 -> Very High
    categories = [r.category for r in plan.recommendations]
    assert categories[0] == "Water"
    water = plan.recommendations[0]
    assert 8 <= water.estimated_reduction_percent <= 12


def test_high_fuel_farm():
    plan = _plan(fuel_consumption_liters_per_ha=120.0)  # above Q90 102.02 -> Very High
    categories = [r.category for r in plan.recommendations]
    assert "Fuel" in categories
    fuel = next(r for r in plan.recommendations if r.category == "Fuel")
    assert 6 <= fuel.estimated_reduction_percent <= 10


def test_high_electricity_farm():
    plan = _plan(electricity_consumption_kwh_per_ha=700.0)  # above Q90 565.28 -> Very High
    categories = [r.category for r in plan.recommendations]
    assert "Electricity" in categories
    elec = next(r for r in plan.recommendations if r.category == "Electricity")
    assert 6 <= elec.estimated_reduction_percent <= 10


def test_multiple_high_inputs_returns_ranked_conservative_combination():
    plan = _plan(
        fertilizer_usage_kg_per_ha=1000.0,   # Very High
        fuel_consumption_liters_per_ha=120.0,  # Very High
        water_consumption_m3_per_ha=18000.0,  # Very High
        electricity_consumption_kwh_per_ha=700.0,  # Very High
    )
    assert 2 <= len(plan.recommendations) <= 4
    # Never just sum the individual percentages.
    naive_sum = sum(r.estimated_reduction_percent for r in plan.recommendations)
    assert plan.estimated_total_reduction_percent < naive_sum
    assert plan.estimated_total_reduction_percent <= PROTOTYPE_MAX_COMBINED_REDUCTION_PERCENT
    assert plan.projected_carbon_footprint == round(
        BASELINE_FOOTPRINT - plan.estimated_total_reduction_kg_co2e_per_ha, 2
    )
    assert plan.estimated_total_reduction_kg_co2e_per_farm == round(
        plan.estimated_total_reduction_kg_co2e_per_ha * FARM_AREA, 2
    )


def test_moderate_input_does_not_recommend_when_already_reasonable():
    """A value right at the median (not above it) should not trigger anything."""
    plan = _plan(fertilizer_usage_kg_per_ha=150.57)  # == median, not > median
    assert all(r.category != "Fertilizer" for r in plan.recommendations)


def test_no_duplicate_categories_in_a_single_plan():
    plan = _plan(
        fertilizer_usage_kg_per_ha=1000.0,
        fuel_consumption_liters_per_ha=120.0,
        water_consumption_m3_per_ha=18000.0,
        electricity_consumption_kwh_per_ha=700.0,
    )
    categories = [r.category for r in plan.recommendations]
    assert len(categories) == len(set(categories))


def test_rice_prioritizes_water_and_mentions_awd():
    plan = _plan(
        crop_type="Rice",
        water_consumption_m3_per_ha=12000.0,  # High tier
        fertilizer_usage_kg_per_ha=190.0,     # High tier
    )
    assert plan.recommendations[0].category == "Water"
    water_item = plan.recommendations[0]
    assert "alternate wetting and drying" in water_item.advice.lower()


def test_every_supported_crop_produces_a_valid_plan():
    for crop in CROP_CATEGORY_EMPHASIS:
        plan = _plan(
            crop_type=crop,
            fertilizer_usage_kg_per_ha=1000.0,
            water_consumption_m3_per_ha=18000.0,
        )
        assert len(plan.recommendations) >= 1
        for item in plan.recommendations:
            assert item.title
            assert item.problem
            assert item.action
            assert item.advice
            assert item.priority in {"High", "Medium", "Low"}
            assert item.estimated_reduction_percent > 0


def test_simulation_notice_present_and_not_overclaiming():
    plan = _plan(fertilizer_usage_kg_per_ha=1000.0)
    notice = plan.simulation_notice.lower()
    assert "simulated" in notice or "not field-validated" in notice
    assert "ipcc" not in notice  # never falsely attribute to IPCC/field research
