from datetime import datetime

from pydantic import BaseModel


class RecentPrediction(BaseModel):
    prediction_id: int
    farm_id: int
    farm_name: str
    crop_type: str
    carbon_footprint_kg_co2e_per_ha: float
    carbon_category: str
    sustainability_score: int | None
    created_at: datetime


class DashboardSummary(BaseModel):
    total_farms: int
    total_predictions: int
    latest_carbon_footprint_kg_co2e_per_ha: float | None
    average_carbon_footprint_kg_co2e_per_ha: float | None
    average_sustainability_score: float | None
    recent_predictions: list[RecentPrediction]


class HistoryPoint(BaseModel):
    prediction_id: int
    farm_id: int
    farm_name: str
    carbon_footprint_kg_co2e_per_ha: float
    sustainability_score: int | None
    created_at: datetime


class CropStat(BaseModel):
    crop_type: str
    prediction_count: int
    average_carbon_footprint_kg_co2e_per_ha: float
