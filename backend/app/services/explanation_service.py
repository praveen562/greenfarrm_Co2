"""
Prediction explanations (exact SHAP values) and what-if scenarios.

How the numbers are produced
----------------------------
XGBoost can return exact TreeSHAP attributions natively:
`booster.predict(DMatrix, pred_contribs=True)` gives, for every row, one
contribution per model input column plus a final bias term. The bias is the
model's average output and the contributions sum to the prediction (to
float32 precision), so nothing here is estimated, sampled or invented — it
is the trained model explaining itself. No extra dependency is needed.

The model sees 10 columns (6 one-hot crop columns + 4 scaled numeric
inputs). We report the 4 numeric inputs individually and collapse the six
one-hot columns back into a single "Crop type" factor, because that is what
the user actually chose.

`explain` is a pure function of (crop_type, 4 inputs): deterministic, no
database access. The stored-prediction endpoint therefore just re-runs it on
the inputs saved with the prediction.
"""
import pandas as pd
import xgboost as xgb

from app.ml.model_loader import get_model, get_preprocessor
from app.services.carbon_category import categorize
from app.services.prediction_service import FEATURE_COLUMNS
from app.services.sustainability_score import categorize_score, compute_sustainability_score

METHOD = "TreeSHAP via XGBoost pred_contribs (exact, from the trained model)"

CROP_COLUMN_PREFIX = "categorical__crop_type_"

# feature column -> (short label, unit)
NUMERIC_FACTORS: dict[str, tuple[str, str]] = {
    "fertilizer_usage_kg_per_ha": ("Fertilizer", "kg/ha"),
    "fuel_consumption_liters_per_ha": ("Fuel", "L/ha"),
    "water_consumption_m3_per_ha": ("Water", "m³/ha"),
    "electricity_consumption_kwh_per_ha": ("Electricity", "kWh/ha"),
}


def explain(
    crop_type: str,
    fertilizer_usage_kg_per_ha: float,
    fuel_consumption_liters_per_ha: float,
    water_consumption_m3_per_ha: float,
    electricity_consumption_kwh_per_ha: float,
) -> dict:
    """Return the model's prediction for these inputs plus its exact SHAP breakdown."""
    preprocessor = get_preprocessor()
    model = get_model()

    values = {
        "fertilizer_usage_kg_per_ha": fertilizer_usage_kg_per_ha,
        "fuel_consumption_liters_per_ha": fuel_consumption_liters_per_ha,
        "water_consumption_m3_per_ha": water_consumption_m3_per_ha,
        "electricity_consumption_kwh_per_ha": electricity_consumption_kwh_per_ha,
    }
    row = pd.DataFrame([{"crop_type": crop_type, **values}])[FEATURE_COLUMNS]
    transformed = preprocessor.transform(row)

    prediction = float(model.predict(transformed)[0])
    contribs = model.get_booster().predict(xgb.DMatrix(transformed), pred_contribs=True)[0]
    base_value = float(contribs[-1])
    per_column = contribs[:-1]

    column_names = [str(n) for n in preprocessor.get_feature_names_out()]
    if len(column_names) != len(per_column):
        # Would mean preprocessor and model are out of sync; never guess a mapping.
        raise RuntimeError(
            f"Preprocessor emits {len(column_names)} columns but the model attributes {len(per_column)}."
        )

    crop_contribution = 0.0
    numeric_contribution: dict[str, float] = {}
    for name, value in zip(column_names, per_column):
        if name.startswith(CROP_COLUMN_PREFIX):
            crop_contribution += float(value)
        else:
            numeric_contribution[name.split("__", 1)[1]] = float(value)

    factors = [
        {
            "feature": "crop_type",
            "label": "Crop type",
            "value": crop_type,
            "unit": "",
            "contribution_kg_co2e_per_ha": round(crop_contribution, 2),
        }
    ]
    for feature, (label, unit) in NUMERIC_FACTORS.items():
        factors.append({
            "feature": feature,
            "label": label,
            "value": values[feature],
            "unit": unit,
            "contribution_kg_co2e_per_ha": round(numeric_contribution[feature], 2),
        })
    factors.sort(key=lambda f: abs(f["contribution_kg_co2e_per_ha"]), reverse=True)
    for f in factors:
        f["direction"] = "increases" if f["contribution_kg_co2e_per_ha"] > 0 else "decreases"

    footprint = round(prediction, 2)
    score = compute_sustainability_score(footprint)
    return {
        "carbon_footprint_kg_co2e_per_ha": footprint,
        "carbon_category": categorize(footprint),
        "sustainability_score": score,
        "sustainability_category": categorize_score(score),
        "explanation": {
            "base_value": round(base_value, 2),
            "factors": factors,
            "method": METHOD,
            "note": (
                "Each factor shows how many kg CO2e/ha it adds to (+) or removes from (-) "
                "the model's average prediction (base value) to reach this farm's prediction."
            ),
        },
    }

