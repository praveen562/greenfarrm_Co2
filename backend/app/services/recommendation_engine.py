"""
Carbon-reduction recommendation engine — practical, prototype version.

Still fully deterministic and rule-based — **no LLM, no randomness**. Given
the same inputs it always returns the same plan.

WHAT CHANGED FROM THE FIRST VERSION
------------------------------------
The original engine only said "usage is high, do X" with no numbers. This
version identifies the main *contributing* inputs, ranks them by severity
and crop relevance, and attaches a **simulated** estimated CO2e reduction
to each recommended action, then combines those into a farm-level
reduction plan.

⚠️  IMPORTANT — THESE PERCENTAGES ARE PROTOTYPE SIMULATIONS, NOT SCIENCE
--------------------------------------------------------------------------
The reduction ranges below (e.g. "high fertilizer -> 8-14%") are
illustrative, order-of-magnitude prototype assumptions for a college
demonstration. They are NOT sourced from IPCC guidance, peer-reviewed
field trials, or any measured intervention study. Every recommendation and
every API response carries an explicit `simulation_notice` saying this.
Do not present these numbers as validated agronomic research.

TIER THRESHOLDS
----------------
Each of the four numeric inputs is bucketed into a tier by comparing it to
the [DATA-DERIVED] median / Q3 (75th percentile) / Q90 (90th percentile)
of that feature in ml/datasets/train.csv (post Phase 4 cleaning) — real
numbers pulled from the actual training data, not guessed:

    feature       median     Q3         Q90
    fertilizer    150.57     186.07     214.87   kg/ha
    fuel          67.36      84.01      102.02   L/ha
    water         6504.13    10104.55   17316.80 m3/ha
    electricity   324.17     446.21     565.28   kWh/ha

    value <= median                  -> Normal   (no recommendation)
    median  < value <= Q3            -> Moderate
    Q3      < value <= Q90           -> High
    value   > Q90                    -> Very High

Within a tier, the exact simulated reduction percentage is a deterministic
linear interpolation between that tier's [low, high] percent range, based
on where the value sits within the tier's numeric span — so a value near
the top of "Very High" gets a bigger simulated reduction than one just
over the Q90 line, without ever being random.

COMBINING MULTIPLE RECOMMENDATIONS
------------------------------------
Reduction percentages are NOT summed (three 15%/8%/5% actions do not imply
a 28% total — real-world interventions overlap and have diminishing
returns). Instead this engine uses a standard diminishing-returns
combination:

    combined = 1 - (1 - p1) * (1 - p2) * ... * (1 - pn)

then caps the result at PROTOTYPE_MAX_COMBINED_REDUCTION_PERCENT (35%),
which is itself a stated prototype ceiling, not a measured limit.
"""
from dataclasses import dataclass, field

# [DATA-DERIVED] median / Q3 / Q90 of each numeric feature in train.csv
# (4,429 rows, post Phase 4 cleaning). Recompute if the training data changes.
FEATURE_TIERS = {
    "Fertilizer": {"median": 150.57, "q3": 186.07, "q90": 214.87, "unit": "kg/ha"},
    "Fuel": {"median": 67.36, "q3": 84.01, "q90": 102.02, "unit": "liters/ha"},
    "Water": {"median": 6504.13, "q3": 10104.55, "q90": 17316.80, "unit": "m3/ha"},
    "Electricity": {"median": 324.17, "q3": 446.21, "q90": 565.28, "unit": "kWh/ha"},
}

# [PROTOTYPE ASSUMPTION] simulated reduction ranges per tier, per the project spec.
# NOT derived from IPCC or field research — explicitly illustrative.
REDUCTION_RANGES_PERCENT = {
    "Fertilizer": {"Moderate": (4, 8), "High": (8, 14), "Very High": (12, 18)},
    "Fuel": {"Moderate": (2, 4), "High": (4, 7), "Very High": (6, 10)},
    "Water": {"Moderate": (3, 5), "High": (5, 9), "Very High": (8, 12)},
    "Electricity": {"Moderate": (2, 4), "High": (4, 7), "Very High": (6, 10)},
}

TIER_PRIORITY = {"Moderate": "Low", "High": "Medium", "Very High": "High"}

# Crop-specific emphasis: categories in this list are ranked ahead of
# equal-tier recommendations for that crop, per the project's agronomic
# guidance (e.g. water/irrigation management matters more for rice than
# for wheat).
CROP_CATEGORY_EMPHASIS = {
    "Rice": ["Water", "Fertilizer", "Electricity", "Fuel"],
    "Wheat": ["Fertilizer", "Water", "Fuel", "Electricity"],
    "Maize": ["Fertilizer", "Water", "Fuel", "Electricity"],
    "Cotton": ["Fertilizer", "Water", "Fuel", "Electricity"],
    "Soybean": ["Fertilizer", "Water", "Fuel", "Electricity"],
    "Sugarcane": ["Fertilizer", "Water", "Electricity", "Fuel"],
}

PROTOTYPE_MAX_COMBINED_REDUCTION_PERCENT = 35
MAX_RECOMMENDATIONS = 4

SIMULATION_NOTICE = (
    "Reduction values are simulated estimates for this prototype and are not "
    "field-validated emission reductions."
)

_TITLES = {
    "Fertilizer": "Reduce excessive fertilizer application",
    "Fuel": "Improve fuel efficiency in field operations",
    "Water": "Improve irrigation water management",
    "Electricity": "Improve irrigation pump / electricity efficiency",
}

_ACTIONS = {
    "Fertilizer": (
        "Apply fertilizer based on soil-test results and split the nitrogen dose into "
        "multiple smaller applications timed to crop growth stages, instead of one large "
        "application."
    ),
    "Fuel": (
        "Combine field operations to reduce the number of separate tractor passes, plan "
        "routes to avoid re-covering ground, and cut unnecessary engine idling."
    ),
    "Water": (
        "Move from fixed-calendar irrigation to scheduling based on real soil-moisture "
        "readings."
    ),
    "Electricity": (
        "Service and calibrate irrigation pumps for peak efficiency and cut unnecessary "
        "pumping cycles."
    ),
}

_ADVICE = {
    "Fertilizer": (
        "Avoid blanket fertilizer application. Test soil nutrient levels before the season "
        "and match the dose to actual crop demand — this improves nitrogen-use efficiency "
        "and directly lowers N2O emissions from over-application."
    ),
    "Fuel": (
        "Keep machinery serviced and well-maintained, and sequence field operations "
        "efficiently. Less diesel burned per hectare means less CO2 from combustion."
    ),
    "Water": (
        "Use soil-moisture monitoring or tensiometers rather than guesswork, and consider "
        "drip irrigation where the crop and terrain allow it. Less over-irrigation means "
        "less pumping energy spent moving water that the crop doesn't need."
    ),
    "Electricity": (
        "Use efficient pump motors and, where feasible, consider solar-powered irrigation "
        "as a longer-term option to reduce dependence on grid electricity."
    ),
}

_RICE_WATER_ADVICE_SUFFIX = (
    " For rice specifically, consider alternate wetting and drying (AWD) — it can meaningfully "
    "cut both water use and the pumping energy behind it while maintaining yield."
)


@dataclass
class RecommendationItem:
    title: str
    category: str
    priority: str
    problem: str
    action: str
    advice: str
    estimated_reduction_percent: float
    estimated_reduction_kg_co2e_per_ha: float
    projected_footprint_kg_co2e_per_ha: float

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "problem": self.problem,
            "action": self.action,
            "advice": self.advice,
            "estimated_reduction_percent": self.estimated_reduction_percent,
            "estimated_reduction_kg_co2e_per_ha": self.estimated_reduction_kg_co2e_per_ha,
            "projected_footprint_kg_co2e_per_ha": self.projected_footprint_kg_co2e_per_ha,
        }


@dataclass
class RecommendationPlan:
    recommendations: list[RecommendationItem] = field(default_factory=list)
    baseline_carbon_footprint: float = 0.0
    estimated_total_reduction_percent: float = 0.0
    estimated_total_reduction_kg_co2e_per_ha: float = 0.0
    projected_carbon_footprint: float = 0.0
    estimated_total_reduction_kg_co2e_per_farm: float = 0.0
    simulation_notice: str = SIMULATION_NOTICE


def _tier_for(category: str, value: float) -> str | None:
    bounds = FEATURE_TIERS[category]
    if value <= bounds["median"]:
        return None
    if value <= bounds["q3"]:
        return "Moderate"
    if value <= bounds["q90"]:
        return "High"
    return "Very High"


def _interpolated_percent(category: str, tier: str, value: float) -> float:
    """Deterministic linear interpolation of the reduction % within a tier's range."""
    bounds = FEATURE_TIERS[category]
    low_pct, high_pct = REDUCTION_RANGES_PERCENT[category][tier]

    if tier == "Moderate":
        span_start, span_end = bounds["median"], bounds["q3"]
    elif tier == "High":
        span_start, span_end = bounds["q3"], bounds["q90"]
    else:  # Very High — open-ended tier; extend one Q3-to-Q90 span past Q90
        span_start = bounds["q90"]
        span_end = bounds["q90"] + (bounds["q90"] - bounds["q3"])

    if span_end <= span_start:
        frac = 1.0
    else:
        frac = (value - span_start) / (span_end - span_start)
    frac = max(0.0, min(1.0, frac))

    return round(low_pct + (high_pct - low_pct) * frac, 1)


def _build_candidate(
    category: str,
    value: float,
    crop_type: str,
    baseline_footprint: float,
) -> RecommendationItem | None:
    tier = _tier_for(category, value)
    if tier is None:
        return None  # input is already at/below a normal level — no recommendation

    percent = _interpolated_percent(category, tier, value)
    reduction_kg = round(baseline_footprint * percent / 100, 2)
    projected = round(baseline_footprint - reduction_kg, 2)

    unit = FEATURE_TIERS[category]["unit"]
    problem = (
        f"{category} usage is {tier.lower()} at {value:g} {unit} for this {crop_type} farm."
    )

    advice = _ADVICE[category]
    if category == "Water" and crop_type == "Rice":
        advice = advice + _RICE_WATER_ADVICE_SUFFIX

    return RecommendationItem(
        title=_TITLES[category],
        category=category,
        priority=TIER_PRIORITY[tier],
        problem=problem,
        action=_ACTIONS[category],
        advice=advice,
        estimated_reduction_percent=percent,
        estimated_reduction_kg_co2e_per_ha=reduction_kg,
        projected_footprint_kg_co2e_per_ha=projected,
    )


_TIER_RANK = {"Very High": 3, "High": 2, "Moderate": 1}


def _sort_key(item: RecommendationItem, crop_type: str):
    tier_rank = {"High": 3, "Medium": 2, "Low": 1}[item.priority]
    emphasis_list = CROP_CATEGORY_EMPHASIS.get(crop_type, [])
    emphasis_rank = (
        len(emphasis_list) - emphasis_list.index(item.category)
        if item.category in emphasis_list
        else 0
    )
    # Higher tier first, then crop emphasis, then bigger simulated reduction first.
    return (-tier_rank, -emphasis_rank, -item.estimated_reduction_percent)


def _combine_reductions(items: list[RecommendationItem], baseline: float) -> tuple[float, float, float]:
    """Diminishing-returns combination, capped at the prototype ceiling."""
    if not items:
        return 0.0, 0.0, round(baseline, 2)

    remaining_fraction = 1.0
    for item in items:
        remaining_fraction *= 1 - (item.estimated_reduction_percent / 100)
    combined_percent = (1 - remaining_fraction) * 100
    combined_percent = min(combined_percent, PROTOTYPE_MAX_COMBINED_REDUCTION_PERCENT)
    combined_percent = round(combined_percent)

    combined_kg = round(baseline * combined_percent / 100, 2)
    projected = round(baseline - combined_kg, 2)
    return combined_percent, combined_kg, projected


def build_recommendation_plan(
    crop_type: str,
    fertilizer_usage_kg_per_ha: float,
    fuel_consumption_liters_per_ha: float,
    water_consumption_m3_per_ha: float,
    electricity_consumption_kwh_per_ha: float,
    baseline_carbon_footprint: float,
    farm_area_ha: float,
) -> RecommendationPlan:
    values = {
        "Fertilizer": fertilizer_usage_kg_per_ha,
        "Fuel": fuel_consumption_liters_per_ha,
        "Water": water_consumption_m3_per_ha,
        "Electricity": electricity_consumption_kwh_per_ha,
    }

    candidates = [
        item
        for category, value in values.items()
        if (item := _build_candidate(category, value, crop_type, baseline_carbon_footprint)) is not None
    ]
    candidates.sort(key=lambda item: _sort_key(item, crop_type))
    selected = candidates[:MAX_RECOMMENDATIONS]

    total_percent, total_kg, projected = _combine_reductions(selected, baseline_carbon_footprint)

    return RecommendationPlan(
        recommendations=selected,
        baseline_carbon_footprint=round(baseline_carbon_footprint, 2),
        estimated_total_reduction_percent=total_percent,
        estimated_total_reduction_kg_co2e_per_ha=total_kg,
        projected_carbon_footprint=projected,
        estimated_total_reduction_kg_co2e_per_farm=round(total_kg * farm_area_ha, 2),
        simulation_notice=SIMULATION_NOTICE,
    )


def rebuild_plan_from_items(
    items: list[RecommendationItem],
    baseline_carbon_footprint: float,
    farm_area_ha: float,
) -> RecommendationPlan:
    """
    Reconstruct a RecommendationPlan's aggregate fields from already-persisted
    RecommendationItems (read path — e.g. GET /predictions/history). Uses the
    same combination function as generation time, so re-reading a persisted
    prediction always yields numbers consistent with what was originally
    computed and stored.
    """
    total_percent, total_kg, projected = _combine_reductions(items, baseline_carbon_footprint)
    return RecommendationPlan(
        recommendations=items,
        baseline_carbon_footprint=round(baseline_carbon_footprint, 2),
        estimated_total_reduction_percent=total_percent,
        estimated_total_reduction_kg_co2e_per_ha=total_kg,
        projected_carbon_footprint=projected,
        estimated_total_reduction_kg_co2e_per_farm=round(total_kg * farm_area_ha, 2),
        simulation_notice=SIMULATION_NOTICE,
    )
