from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.crop_type import CropType


# Sanity ceilings for user-supplied inputs. They sit roughly 7-10x above the
# largest value in ml/datasets/train.csv (fertilizer 280, fuel 125, water
# 18,886, electricity 750) so legitimate heavy-use farms pass, while absurd
# values (and inf/NaN, which previously crashed the model with a 500) are
# rejected with a 422.
MAX_FERTILIZER_KG_PER_HA = 2_000
MAX_FUEL_LITERS_PER_HA = 1_000
MAX_WATER_M3_PER_HA = 100_000
MAX_ELECTRICITY_KWH_PER_HA = 7_500


class CarbonPredictionRequest(BaseModel):
    farm_id: int
    fertilizer_usage_kg_per_ha: float = Field(gt=0, le=MAX_FERTILIZER_KG_PER_HA, allow_inf_nan=False)
    fuel_consumption_liters_per_ha: float = Field(ge=0, le=MAX_FUEL_LITERS_PER_HA, allow_inf_nan=False)
    water_consumption_m3_per_ha: float = Field(ge=0, le=MAX_WATER_M3_PER_HA, allow_inf_nan=False)
    electricity_consumption_kwh_per_ha: float = Field(ge=0, le=MAX_ELECTRICITY_KWH_PER_HA, allow_inf_nan=False)


class RecommendationItem(BaseModel):
    title: str
    category: str  # "Fertilizer" | "Fuel" | "Water" | "Electricity" | "General"
    priority: str  # "High" | "Medium" | "Low"
    problem: str
    action: str
    advice: str
    estimated_reduction_percent: float
    estimated_reduction_kg_co2e_per_ha: float
    projected_footprint_kg_co2e_per_ha: float


class RecommendationPlan(BaseModel):
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    baseline_carbon_footprint: float
    estimated_total_reduction_percent: float
    estimated_total_reduction_kg_co2e_per_ha: float
    projected_carbon_footprint: float
    estimated_total_reduction_kg_co2e_per_farm: float
    simulation_notice: str = (
        "Reduction values are simulated estimates for this prototype and are not "
        "field-validated emission reductions."
    )


class CarbonPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction_id: int
    farm_id: int
    crop_type: CropType
    carbon_footprint_kg_co2e_per_ha: float
    total_farm_emissions_kg_co2e: float
    carbon_category: str  # "Low" | "Moderate" | "High" | "Very High"
    sustainability_score: int
    sustainability_category: str  # "Excellent" | "Good" | "Moderate" | "Needs Improvement"
    recommendation_plan: RecommendationPlan
    model_used: str = "XGBoost Regressor"
    created_at: datetime


class ExplanationFactor(BaseModel):
    feature: str  # "crop_type" | "fertilizer_usage_kg_per_ha" | ...
    label: str  # "Crop type" | "Fertilizer" | "Fuel" | "Water" | "Electricity"
    value: float | str  # the input value (crop name for crop_type)
    unit: str
    contribution_kg_co2e_per_ha: float  # signed SHAP value
    direction: str  # "increases" | "decreases"


class PredictionExplanation(BaseModel):
    base_value: float  # model's average prediction; base + sum(contributions) == prediction
    factors: list[ExplanationFactor]  # sorted by absolute contribution, largest first
    method: str
    note: str


class ExplainedPrediction(BaseModel):
    """A prediction value together with its exact SHAP breakdown."""
    carbon_footprint_kg_co2e_per_ha: float
    carbon_category: str
    sustainability_score: int
    sustainability_category: str
    explanation: PredictionExplanation


class WhatIfRequest(CarbonPredictionRequest):
    """Same inputs and the same validation limits as a real prediction."""


class WhatIfResponse(ExplainedPrediction):
    """A scenario result. Nothing is stored; the farm only supplies crop and area."""
    farm_id: int
    crop_type: CropType
    total_farm_emissions_kg_co2e: float
    persisted: bool = False


class StoredPredictionExplanation(ExplainedPrediction):
    prediction_id: int
    farm_id: int
    crop_type: CropType
