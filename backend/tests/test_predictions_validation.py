"""
Tests for the /api/v1/predictions/carbon request contract.

These test real, live behavior in Phase 7: Pydantic validation. The
endpoint itself returns 501 until Phase 8 wires in the trained model —
that specific "valid request -> successful prediction" test is added in
Phase 8, since it would be meaningless (and dishonest) to assert against a
stub response now.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "crop_type": "Rice",
    "fertilizer_usage_kg_per_ha": 180,
    "fuel_consumption_liters_per_ha": 120,
    "water_consumption_m3_per_ha": 2500,
    "electricity_consumption_kwh_per_ha": 500,
}


def test_negative_fertilizer_returns_422():
    payload = {**VALID_PAYLOAD, "fertilizer_usage_kg_per_ha": -10}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_negative_fuel_returns_422():
    payload = {**VALID_PAYLOAD, "fuel_consumption_liters_per_ha": -5}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_negative_water_returns_422():
    payload = {**VALID_PAYLOAD, "water_consumption_m3_per_ha": -100}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_negative_electricity_returns_422():
    payload = {**VALID_PAYLOAD, "electricity_consumption_kwh_per_ha": -50}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_zero_fertilizer_returns_422():
    """fertilizer_usage must be > 0, not just >= 0."""
    payload = {**VALID_PAYLOAD, "fertilizer_usage_kg_per_ha": 0}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_invalid_crop_type_returns_422():
    payload = {**VALID_PAYLOAD, "crop_type": "Unicorn Grain"}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_missing_field_returns_422():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "water_consumption_m3_per_ha"}
    response = client.post("/api/v1/predictions/carbon", json=payload)
    assert response.status_code == 422


def test_valid_payload_returns_successful_prediction():
    """
    Real, end-to-end: the trained model actually runs and returns a
    plausible carbon footprint. Cross-checked below against a direct
    preprocessor+model call so this isn't just checking "status == 200".
    """
    response = client.post("/api/v1/predictions/carbon", json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["carbon_footprint_kg_co2e_per_ha"] > 0
    assert body["carbon_category"] in {"Low", "Moderate", "High", "Very High"}
    # Phase 13 fields deliberately unset in Phase 8, not faked
    assert body["sustainability_score"] is None
    assert body["recommendations"] == []


def test_prediction_matches_direct_model_call():
    """Cross-check the API's prediction against calling the saved model directly."""
    import pandas as pd

    from app.ml.model_loader import get_model, get_preprocessor

    preprocessor = get_preprocessor()
    model = get_model()
    row = pd.DataFrame([{
        "crop_type": VALID_PAYLOAD["crop_type"],
        "fertilizer_usage_kg_per_ha": VALID_PAYLOAD["fertilizer_usage_kg_per_ha"],
        "fuel_consumption_liters_per_ha": VALID_PAYLOAD["fuel_consumption_liters_per_ha"],
        "water_consumption_m3_per_ha": VALID_PAYLOAD["water_consumption_m3_per_ha"],
        "electricity_consumption_kwh_per_ha": VALID_PAYLOAD["electricity_consumption_kwh_per_ha"],
    }])
    expected = float(model.predict(preprocessor.transform(row))[0])

    response = client.post("/api/v1/predictions/carbon", json=VALID_PAYLOAD)
    actual = response.json()["carbon_footprint_kg_co2e_per_ha"]
    assert actual == round(expected, 2)


def test_model_load_error_returns_503_not_stack_trace():
    """Simulate a model-loading failure and confirm no internals leak to the client."""
    from unittest.mock import patch

    from app.ml.model_loader import ModelLoadError

    with patch(
        "app.api.v1.predictions.predict_carbon_footprint",
        side_effect=ModelLoadError("simulated failure for testing"),
    ):
        response = client.post("/api/v1/predictions/carbon", json=VALID_PAYLOAD)
    assert response.status_code == 503
    assert "simulated failure" not in response.text  # internals not leaked


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
