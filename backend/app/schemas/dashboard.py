from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_farms: int
    average_carbon_footprint_kg_co2e_per_ha: float
    average_sustainability_score: float
    highest_emission_source: str
    average_water_usage_m3_per_ha: float
    average_fuel_usage_liters_per_ha: float
