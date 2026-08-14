"""
Prediction service: turns a validated CarbonPredictionRequest into a real
model prediction. No fallback/default prediction value exists anywhere in
this module — if the model or preprocessor can't be loaded, this raises
ModelLoadError and the router turns that into a proper error response
rather than ever returning a made-up number.
"""
import pandas as pd

from app.ml.model_loader import get_model, get_preprocessor
from app.schemas.prediction import CarbonPredictionRequest
from app.services.carbon_category import categorize

# Must match ml/preprocessing/build_preprocessor.py's ALL_FEATURES exactly —
# the preprocessor was fit expecting this exact column set (order doesn't
# matter to a DataFrame-based ColumnTransformer, but the names must match).
FEATURE_COLUMNS = [
    "crop_type",
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]


def predict_carbon_footprint(request: CarbonPredictionRequest) -> dict:
    preprocessor = get_preprocessor()
    model = get_model()

    row = pd.DataFrame([{
        "crop_type": request.crop_type.value,
        "fertilizer_usage_kg_per_ha": request.fertilizer_usage_kg_per_ha,
        "fuel_consumption_liters_per_ha": request.fuel_consumption_liters_per_ha,
        "water_consumption_m3_per_ha": request.water_consumption_m3_per_ha,
        "electricity_consumption_kwh_per_ha": request.electricity_consumption_kwh_per_ha,
    }])[FEATURE_COLUMNS]

    transformed = preprocessor.transform(row)
    prediction = float(model.predict(transformed)[0])

    return {
        "carbon_footprint_kg_co2e_per_ha": round(prediction, 2),
        "carbon_category": categorize(prediction),
        # sustainability_score and recommendations land in Phase 13 —
        # deliberately left unset here rather than faked.
        "sustainability_score": None,
        "recommendations": [],
    }
