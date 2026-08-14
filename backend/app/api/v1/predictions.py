"""
Predictions router.

Phase 8: real ML inference via the trained XGBoost model + fitted
preprocessor (both loaded once and cached, see app/ml/model_loader.py).
sustainability_score and recommendations are intentionally left unset —
they're rule-based systems that land in Phase 13, not part of this ML
integration.
"""
import logging

from fastapi import APIRouter, HTTPException, status

from app.ml.model_loader import ModelLoadError
from app.schemas.prediction import CarbonPredictionRequest, CarbonPredictionResponse
from app.services.prediction_service import predict_carbon_footprint

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/carbon", response_model=CarbonPredictionResponse)
def predict_carbon(payload: CarbonPredictionRequest):
    try:
        result = predict_carbon_footprint(payload)
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

    return CarbonPredictionResponse(**result)
