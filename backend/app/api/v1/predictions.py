"""
Predictions router.

Phase 8: real ML inference. Phase 10: protected behind auth, scoped to
the requesting user's own farms. Phase 13: sustainability score +
rule-based recommendations computed and persisted alongside every
prediction, never faked.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.ml.model_loader import ModelLoadError
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import (
    CarbonPredictionRequest,
    CarbonPredictionResponse,
    StoredPredictionExplanation,
    WhatIfRequest,
    WhatIfResponse,
)
from app.services.explanation_service import explain
from app.services.prediction_service import build_prediction_response_dict, create_prediction_for_farm

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/carbon", response_model=CarbonPredictionResponse, status_code=status.HTTP_201_CREATED)
def predict_carbon(
    payload: CarbonPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = db.get(Farm, payload.farm_id)
    if farm is None or farm.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")

    try:
        prediction = create_prediction_for_farm(
            farm=farm,
            fertilizer_usage_kg_per_ha=payload.fertilizer_usage_kg_per_ha,
            fuel_consumption_liters_per_ha=payload.fuel_consumption_liters_per_ha,
            water_consumption_m3_per_ha=payload.water_consumption_m3_per_ha,
            electricity_consumption_kwh_per_ha=payload.electricity_consumption_kwh_per_ha,
            db=db,
        )
    except ModelLoadError as exc:
        logger.error("Model loading failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The prediction model is currently unavailable. Please try again shortly.",
        ) from exc
    except Exception as exc:  # noqa: BLE001 — never leak internals to the client
        logger.exception("Unexpected error during prediction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the prediction.",
        ) from exc

    return build_prediction_response_dict(prediction, farm)


@router.get("/history", response_model=list[CarbonPredictionResponse])
def prediction_history(
    farm_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Prediction)
        .join(Farm, Prediction.farm_id == Farm.id)
        .filter(Farm.user_id == current_user.id)
    )
    if farm_id is not None:
        query = query.filter(Prediction.farm_id == farm_id)

    predictions = query.order_by(Prediction.created_at.desc()).all()
    return [build_prediction_response_dict(p, p.farm) for p in predictions]


def _explain_or_http_error(**kwargs) -> dict:
    try:
        return explain(**kwargs)
    except ModelLoadError as exc:
        logger.error("Model loading failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The prediction model is currently unavailable. Please try again shortly.",
        ) from exc
    except Exception as exc:  # noqa: BLE001 — never leak internals to the client
        logger.exception("Unexpected error while explaining a prediction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the explanation.",
        ) from exc


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(
    payload: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run the real model on hypothetical inputs. Stateless: writes nothing."""
    farm = db.get(Farm, payload.farm_id)
    if farm is None or farm.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")

    result = _explain_or_http_error(
        crop_type=farm.crop_type,
        fertilizer_usage_kg_per_ha=payload.fertilizer_usage_kg_per_ha,
        fuel_consumption_liters_per_ha=payload.fuel_consumption_liters_per_ha,
        water_consumption_m3_per_ha=payload.water_consumption_m3_per_ha,
        electricity_consumption_kwh_per_ha=payload.electricity_consumption_kwh_per_ha,
    )
    return {
        **result,
        "farm_id": farm.id,
        "crop_type": farm.crop_type,
        "total_farm_emissions_kg_co2e": round(result["carbon_footprint_kg_co2e_per_ha"] * farm.area, 2),
        "persisted": False,
    }


@router.get("/{prediction_id}/explanation", response_model=StoredPredictionExplanation)
def prediction_explanation(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exact SHAP breakdown for a stored prediction, recomputed from its saved inputs."""
    prediction = db.get(Prediction, prediction_id)
    farm = db.get(Farm, prediction.farm_id) if prediction is not None else None
    if prediction is None or farm is None or farm.user_id != current_user.id:
        # Same 404 for "missing" and "someone else's" — never leak existence.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found.")

    result = _explain_or_http_error(
        crop_type=farm.crop_type,
        fertilizer_usage_kg_per_ha=prediction.fertilizer_usage,
        fuel_consumption_liters_per_ha=prediction.fuel_consumption,
        water_consumption_m3_per_ha=prediction.water_consumption,
        electricity_consumption_kwh_per_ha=prediction.electricity_consumption,
    )
    return {**result, "prediction_id": prediction.id, "farm_id": farm.id, "crop_type": farm.crop_type}
