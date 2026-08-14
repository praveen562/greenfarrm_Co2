from pydantic import BaseModel, Field

from app.schemas.crop_type import CropType


class CarbonPredictionRequest(BaseModel):
    crop_type: CropType
    fertilizer_usage_kg_per_ha: float = Field(gt=0)
    fuel_consumption_liters_per_ha: float = Field(ge=0)
    water_consumption_m3_per_ha: float = Field(ge=0)
    electricity_consumption_kwh_per_ha: float = Field(ge=0)


class CarbonPredictionResponse(BaseModel):
    carbon_footprint_kg_co2e_per_ha: float
    carbon_category: str  # "Low" | "Moderate" | "High" | "Very High" — real, from Phase 8
    sustainability_score: int | None = None  # populated in Phase 13
    recommendations: list[str] = Field(default_factory=list)  # populated in Phase 13
