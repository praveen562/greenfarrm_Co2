"""
Tests for the /api/v1/predictions/carbon request contract.

Phase 10 restructured this endpoint to be auth-protected and farm-scoped
(farm_id + crop_type comes from the farm, not the request body). These
tests exercise the full real stack: register -> login -> create farm ->
predict, against a live trained model and a real Postgres DB.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.user import User
from app.db.session import SessionLocal

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_tables():
    db = SessionLocal()
    db.query(Recommendation).delete()
    db.query(Prediction).delete()
    db.query(Farm).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    yield


def _register_and_login(email="predtest@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1", "full_name": "Pred Tester",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_farm(headers, crop_type="Rice", area=10.0):
    resp = client.post("/api/v1/farms/", json={
        "farm_name": "Test Farm", "location": "Punjab", "area": area, "crop_type": crop_type,
    }, headers=headers)
    return resp.json()["id"]


VALID_INPUTS = {
    "fertilizer_usage_kg_per_ha": 180,
    "fuel_consumption_liters_per_ha": 120,
    "water_consumption_m3_per_ha": 2500,
    "electricity_consumption_kwh_per_ha": 500,
}


def test_predict_requires_auth():
    response = client.post("/api/v1/predictions/carbon", json={"farm_id": 1, **VALID_INPUTS})
    assert response.status_code == 401


def test_negative_fertilizer_returns_422():
    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **VALID_INPUTS, "fertilizer_usage_kg_per_ha": -10}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 422


def test_zero_fertilizer_returns_422():
    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **VALID_INPUTS, "fertilizer_usage_kg_per_ha": 0}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 422


def test_negative_water_returns_422():
    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **VALID_INPUTS, "water_consumption_m3_per_ha": -100}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 422


def test_missing_field_returns_422():
    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **{k: v for k, v in VALID_INPUTS.items() if k != "water_consumption_m3_per_ha"}}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 422


def test_unknown_farm_returns_404():
    headers = _register_and_login()
    payload = {"farm_id": 999999, **VALID_INPUTS}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 404


def test_cannot_predict_on_another_users_farm():
    headers_a = _register_and_login("owner_a@example.com")
    farm_id = _create_farm(headers_a)

    headers_b = _register_and_login("owner_b@example.com")
    payload = {"farm_id": farm_id, **VALID_INPUTS}
    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers_b)
    assert response.status_code == 404


def test_valid_payload_returns_successful_prediction_and_persists():
    """
    Real, end-to-end: the trained model runs, a Prediction row is
    persisted, sustainability score + recommendations are computed —
    nothing faked.
    """
    headers = _register_and_login()
    farm_id = _create_farm(headers, area=10.0)
    payload = {"farm_id": farm_id, **VALID_INPUTS}

    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()

    assert body["carbon_footprint_kg_co2e_per_ha"] > 0
    assert body["carbon_category"] in {"Low", "Moderate", "High", "Very High"}
    assert body["total_farm_emissions_kg_co2e"] == round(body["carbon_footprint_kg_co2e_per_ha"] * 10.0, 2)
    assert 0 <= body["sustainability_score"] <= 100
    assert body["sustainability_category"] in {"Excellent", "Good", "Moderate", "Needs Improvement"}
    assert 1 <= len(body["recommendations"]) <= 5
    assert body["model_used"] == "XGBoost Regressor"

    db = SessionLocal()
    persisted = db.get(Prediction, body["prediction_id"])
    assert persisted is not None
    assert persisted.farm_id == farm_id
    assert len(persisted.recommendations) == len(body["recommendations"])
    db.close()


def test_prediction_matches_direct_model_call():
    """Cross-check the API's prediction against calling the saved model directly."""
    import pandas as pd

    from app.ml.model_loader import get_model, get_preprocessor

    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **VALID_INPUTS}

    preprocessor = get_preprocessor()
    model = get_model()
    row = pd.DataFrame([{
        "crop_type": "Rice",
        **VALID_INPUTS,
    }])
    expected = float(model.predict(preprocessor.transform(row))[0])

    response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    actual = response.json()["carbon_footprint_kg_co2e_per_ha"]
    assert actual == round(expected, 2)


def test_model_load_error_returns_503_not_stack_trace():
    """Simulate a model-loading failure and confirm no internals leak to the client."""
    from unittest.mock import patch

    from app.ml.model_loader import ModelLoadError

    headers = _register_and_login()
    farm_id = _create_farm(headers)
    payload = {"farm_id": farm_id, **VALID_INPUTS}

    with patch(
        "app.api.v1.predictions.create_prediction_for_farm",
        side_effect=ModelLoadError("simulated failure for testing"),
    ):
        response = client.post("/api/v1/predictions/carbon", json=payload, headers=headers)
    assert response.status_code == 503
    assert "simulated failure" not in response.text  # internals not leaked


def test_prediction_history_scoped_to_user():
    headers_a = _register_and_login("hist_a@example.com")
    farm_a = _create_farm(headers_a)
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_a, **VALID_INPUTS}, headers=headers_a)

    headers_b = _register_and_login("hist_b@example.com")
    farm_b = _create_farm(headers_b)
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_b, **VALID_INPUTS}, headers=headers_b)

    resp_a = client.get("/api/v1/predictions/history", headers=headers_a)
    assert resp_a.status_code == 200
    assert len(resp_a.json()) == 1
    assert resp_a.json()[0]["farm_id"] == farm_a


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
