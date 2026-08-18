from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.crop_type import CropType


class CarbonPredictionRequest(BaseModel):
    farm_id: int
    fertilizer_usage_kg_per_ha: float = Field(gt=0)
    fuel_consumption_liters_per_ha: float = Field(ge=0)
    water_consumption_m3_per_ha: float = Field(ge=0)
    electricity_consumption_kwh_per_ha: float = Field(ge=0)


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
