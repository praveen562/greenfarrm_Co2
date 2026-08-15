from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.crop_type import CropType


class CarbonPredictionRequest(BaseModel):
    farm_id: int
    fertilizer_usage_kg_per_ha: float = Field(gt=0)
    fuel_consumption_liters_per_ha: float = Field(ge=0)
    water_consumption_m3_per_ha: float = Field(ge=0)
    electricity_consumption_kwh_per_ha: float = Field(ge=0)


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
    recommendations: list[str] = Field(default_factory=list)
    model_used: str = "XGBoost Regressor"
    created_at: datetime
