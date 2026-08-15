"""
Phase 14: dashboard/analytics endpoint tests — real aggregation queries,
scoped strictly to the requesting user.
"""
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.user import User

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


def _register_and_login(email):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1", "full_name": "Dash Tester",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


VALID_INPUTS = {
    "fertilizer_usage_kg_per_ha": 180,
    "fuel_consumption_liters_per_ha": 120,
    "water_consumption_m3_per_ha": 2500,
    "electricity_consumption_kwh_per_ha": 500,
}


def test_summary_requires_auth():
    assert client.get("/api/v1/dashboard/summary").status_code == 401


def test_summary_empty_state():
    headers = _register_and_login("dash_empty@example.com")
    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_farms"] == 0
    assert body["total_predictions"] == 0
    assert body["latest_carbon_footprint_kg_co2e_per_ha"] is None
    assert body["recent_predictions"] == []


def test_summary_with_data():
    headers = _register_and_login("dash_data@example.com")
    farm_resp = client.post("/api/v1/farms/", json={
        "farm_name": "Dash Farm", "location": "Loc", "area": 10.0, "crop_type": "Rice",
    }, headers=headers)
    farm_id = farm_resp.json()["id"]

    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_id, **VALID_INPUTS}, headers=headers)
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_id, **VALID_INPUTS}, headers=headers)

    resp = client.get("/api/v1/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_farms"] == 1
    assert body["total_predictions"] == 2
    assert body["latest_carbon_footprint_kg_co2e_per_ha"] > 0
    assert body["average_carbon_footprint_kg_co2e_per_ha"] > 0
    assert 0 <= body["average_sustainability_score"] <= 100
    assert len(body["recent_predictions"]) == 2


def test_dashboard_scoped_to_user():
    headers_a = _register_and_login("dash_a@example.com")
    farm_a = client.post("/api/v1/farms/", json={
        "farm_name": "A Farm", "location": "L", "area": 5.0, "crop_type": "Wheat",
    }, headers=headers_a).json()["id"]
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_a, **VALID_INPUTS}, headers=headers_a)

    headers_b = _register_and_login("dash_b@example.com")
    resp = client.get("/api/v1/dashboard/summary", headers=headers_b)
    assert resp.json()["total_predictions"] == 0


def test_history_endpoint():
    headers = _register_and_login("dash_hist@example.com")
    farm_id = client.post("/api/v1/farms/", json={
        "farm_name": "Hist Farm", "location": "L", "area": 5.0, "crop_type": "Maize",
    }, headers=headers).json()["id"]
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_id, **VALID_INPUTS}, headers=headers)

    resp = client.get("/api/v1/dashboard/history", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_crop_stats_endpoint():
    headers = _register_and_login("dash_crop@example.com")
    farm_id = client.post("/api/v1/farms/", json={
        "farm_name": "Crop Farm", "location": "L", "area": 5.0, "crop_type": "Sugarcane",
    }, headers=headers).json()["id"]
    client.post("/api/v1/predictions/carbon", json={"farm_id": farm_id, **VALID_INPUTS}, headers=headers)

    resp = client.get("/api/v1/dashboard/crop-stats", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["crop_type"] == "Sugarcane"
    assert body[0]["prediction_count"] == 1
