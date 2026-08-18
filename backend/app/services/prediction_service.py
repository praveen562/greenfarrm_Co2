"""
Prediction service.

`predict_carbon_footprint_raw` is the pure ML-inference step (Phase 8,
unchanged): crop_type + 4 numeric inputs -> footprint + category, straight
from the trained XGBoost model and fitted preprocessor. No fallback/default
value exists here — a load failure raises ModelLoadError.

`create_prediction_for_farm` (Phase 10/13) wraps that with the rest of the
pipeline: look up the farm (crop_type comes from the farm, not the
request), scale to total farm emissions via farm.area, compute the
deterministic sustainability score, generate the recommendation plan, and
persist Prediction + Recommendation rows.

Recommendation persistence note: the `recommendations` table schema was
deliberately left unchanged (id, prediction_id, category, text,
created_at) — the richer structured fields (title, priority, problem,
action, advice, simulated reduction numbers) are serialized as JSON into
the existing `text` column, and `category` keeps the short label
("Fertilizer"/"Fuel"/"Water"/"Electricity"/"General") for quick filtering.
This avoids a database migration while still supporting the full
structured recommendation contract in the API response.
"""
import json

import pandas as pd
from sqlalchemy.orm import Session

from app.ml.model_loader import get_model, get_preprocessor
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.services.carbon_category import categorize
from app.services.recommendation_engine import (
    RecommendationItem,
    build_recommendation_plan,
    rebuild_plan_from_items,
)
from app.services.sustainability_score import categorize_score, compute_sustainability_score

FEATURE_COLUMNS = [
    "crop_type",
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]


def predict_carbon_footprint_raw(
    crop_type: str,
    fertilizer_usage_kg_per_ha: float,
    fuel_consumption_liters_per_ha: float,
    water_consumption_m3_per_ha: float,
    electricity_consumption_kwh_per_ha: float,
) -> dict:
    preprocessor = get_preprocessor()
    model = get_model()

    row = pd.DataFrame([{
        "crop_type": crop_type,
        "fertilizer_usage_kg_per_ha": fertilizer_usage_kg_per_ha,
        "fuel_consumption_liters_per_ha": fuel_consumption_liters_per_ha,
        "water_consumption_m3_per_ha": water_consumption_m3_per_ha,
        "electricity_consumption_kwh_per_ha": electricity_consumption_kwh_per_ha,
    }])[FEATURE_COLUMNS]

    transformed = preprocessor.transform(row)
    prediction = float(model.predict(transformed)[0])

    return {
        "carbon_footprint_kg_co2e_per_ha": round(prediction, 2),
        "carbon_category": categorize(prediction),
    }


def create_prediction_for_farm(
    farm: Farm,
    fertilizer_usage_kg_per_ha: float,
    fuel_consumption_liters_per_ha: float,
    water_consumption_m3_per_ha: float,
    electricity_consumption_kwh_per_ha: float,
    db: Session,
) -> Prediction:
    raw = predict_carbon_footprint_raw(
        crop_type=farm.crop_type,
        fertilizer_usage_kg_per_ha=fertilizer_usage_kg_per_ha,
        fuel_consumption_liters_per_ha=fuel_consumption_liters_per_ha,
        water_consumption_m3_per_ha=water_consumption_m3_per_ha,
        electricity_consumption_kwh_per_ha=electricity_consumption_kwh_per_ha,
    )
    footprint = raw["carbon_footprint_kg_co2e_per_ha"]
    category = raw["carbon_category"]
    score = compute_sustainability_score(footprint)

    prediction = Prediction(
        farm_id=farm.id,
        fertilizer_usage=fertilizer_usage_kg_per_ha,
        fuel_consumption=fuel_consumption_liters_per_ha,
        water_consumption=water_consumption_m3_per_ha,
        electricity_consumption=electricity_consumption_kwh_per_ha,
        predicted_carbon=footprint,
        carbon_category=category,
        sustainability_score=score,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    plan = build_recommendation_plan(
        crop_type=farm.crop_type,
        fertilizer_usage_kg_per_ha=fertilizer_usage_kg_per_ha,
        fuel_consumption_liters_per_ha=fuel_consumption_liters_per_ha,
        water_consumption_m3_per_ha=water_consumption_m3_per_ha,
        electricity_consumption_kwh_per_ha=electricity_consumption_kwh_per_ha,
        baseline_carbon_footprint=footprint,
        farm_area_ha=farm.area,
    )
    for item in plan.recommendations:
        db.add(Recommendation(
            prediction_id=prediction.id,
            category=item.category,
            text=json.dumps(item.to_dict()),
        ))
    db.commit()
    db.refresh(prediction)

    return prediction


def _load_recommendation_items(prediction: Prediction) -> list[RecommendationItem]:
    items = []
    for rec in prediction.recommendations:
        try:
            data = json.loads(rec.text)
            items.append(RecommendationItem(**data))
        except (json.JSONDecodeError, TypeError):
            # Defensive: skip any row that isn't in the structured JSON format
            # (e.g. a stale row from before this schema of `text` existed).
            continue
    return items


def build_prediction_response_dict(prediction: Prediction, farm: Farm) -> dict:
    score = prediction.sustainability_score
    items = _load_recommendation_items(prediction)
    plan = rebuild_plan_from_items(
        items=items,
        baseline_carbon_footprint=prediction.predicted_carbon,
        farm_area_ha=farm.area,
    )

    return {
        "prediction_id": prediction.id,
        "farm_id": farm.id,
        "crop_type": farm.crop_type,
        "carbon_footprint_kg_co2e_per_ha": prediction.predicted_carbon,
        "total_farm_emissions_kg_co2e": round(prediction.predicted_carbon * farm.area, 2),
        "carbon_category": prediction.carbon_category,
        "sustainability_score": score,
        "sustainability_category": categorize_score(score),
        "recommendation_plan": {
            "recommendations": [item.to_dict() for item in plan.recommendations],
            "baseline_carbon_footprint": plan.baseline_carbon_footprint,
            "estimated_total_reduction_percent": plan.estimated_total_reduction_percent,
            "estimated_total_reduction_kg_co2e_per_ha": plan.estimated_total_reduction_kg_co2e_per_ha,
            "projected_carbon_footprint": plan.projected_carbon_footprint,
            "estimated_total_reduction_kg_co2e_per_farm": plan.estimated_total_reduction_kg_co2e_per_farm,
            "simulation_notice": plan.simulation_notice,
        },
        "model_used": "XGBoost Regressor",
        "created_at": prediction.created_at,
    }
