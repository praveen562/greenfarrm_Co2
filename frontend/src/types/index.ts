export type CropType = "Rice" | "Wheat" | "Maize" | "Soybean" | "Sugarcane" | "Cotton";

export const CROP_TYPES: CropType[] = ["Rice", "Wheat", "Maize", "Soybean", "Sugarcane", "Cotton"];

export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface Farm {
  id: number;
  user_id: number;
  farm_name: string;
  location: string;
  area: number;
  crop_type: CropType;
  created_at: string;
}

export interface CarbonPredictionRequest {
  farm_id: number;
  fertilizer_usage_kg_per_ha: number;
  fuel_consumption_liters_per_ha: number;
  water_consumption_m3_per_ha: number;
  electricity_consumption_kwh_per_ha: number;
}

export interface RecommendationItem {
  title: string;
  category: "Fertilizer" | "Fuel" | "Water" | "Electricity" | "General";
  priority: "High" | "Medium" | "Low";
  problem: string;
  action: string;
  advice: string;
  estimated_reduction_percent: number;
  estimated_reduction_kg_co2e_per_ha: number;
  projected_footprint_kg_co2e_per_ha: number;
}

export interface RecommendationPlan {
  recommendations: RecommendationItem[];
  baseline_carbon_footprint: number;
  estimated_total_reduction_percent: number;
  estimated_total_reduction_kg_co2e_per_ha: number;
  projected_carbon_footprint: number;
  estimated_total_reduction_kg_co2e_per_farm: number;
  simulation_notice: string;
}

export interface CarbonPredictionResponse {
  prediction_id: number;
  farm_id: number;
  crop_type: CropType;
  carbon_footprint_kg_co2e_per_ha: number;
  total_farm_emissions_kg_co2e: number;
  carbon_category: "Low" | "Moderate" | "High" | "Very High";
  sustainability_score: number;
  sustainability_category: "Excellent" | "Good" | "Moderate" | "Needs Improvement";
  recommendation_plan: RecommendationPlan;
  model_used: string;
  created_at: string;
}

export interface RecentPrediction {
  prediction_id: number;
  farm_id: number;
  farm_name: string;
  crop_type: string;
  carbon_footprint_kg_co2e_per_ha: number;
  carbon_category: string;
  sustainability_score: number | null;
  created_at: string;
}

export interface DashboardSummary {
  total_farms: number;
  total_predictions: number;
  latest_carbon_footprint_kg_co2e_per_ha: number | null;
  average_carbon_footprint_kg_co2e_per_ha: number | null;
  average_sustainability_score: number | null;
  recent_predictions: RecentPrediction[];
}

export interface HistoryPoint {
  prediction_id: number;
  farm_id: number;
  farm_name: string;
  carbon_footprint_kg_co2e_per_ha: number;
  sustainability_score: number | null;
  created_at: string;
}

export interface CropStat {
  crop_type: string;
  prediction_count: number;
  average_carbon_footprint_kg_co2e_per_ha: number;
}

export interface ApiError {
  detail: string | { msg: string; loc: (string | number)[] }[];
}
