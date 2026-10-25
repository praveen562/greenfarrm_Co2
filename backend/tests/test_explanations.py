"""
What-if simulator + SHAP explanations.

The key property under test: the explanation is *exact*, not decorative —
base_value + sum(factor contributions) reproduces the model's prediction —
and the what-if endpoint returns precisely what a real prediction would,
without storing anything.
"""
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.crop_type import CropType

client = TestClient(app, raise_server_exceptions=False)

INPUTS = {
    "fertilizer_usage_kg_per_ha": 180.0,
    "fuel_consumption_liters_per_ha": 80.0,
    "water_consumption_m3_per_ha": 12000.0,
    "electricity_consumption_kwh_per_ha": 450.0,
}
CROPS = [c.value for c in CropType]


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


def _login(email="explain@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1", "full_name": "Explain Tester",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _farm(headers, crop="Rice", area=10):
    resp = client.post("/api/v1/farms/", headers=headers, json={
        "farm_name": f"{crop} farm", "location": "Chennai", "area": area, "crop_type": crop,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _what_if(headers, farm_id, **overrides):
    return client.post("/api/v1/predictions/what-if", headers=headers,
                       json={"farm_id": farm_id, **INPUTS, **overrides})


def _prediction_count():
    db = SessionLocal()
    try:
        return db.query(Prediction).count()
    finally:
        db.close()


# --- exactness of the explanation ------------------------------------------

@pytest.mark.parametrize("crop", CROPS)
def test_base_plus_contributions_reproduces_the_prediction(crop):
    headers = _login()
    resp = _what_if(headers, _farm(headers, crop))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    exp = body["explanation"]
    reconstructed = exp["base_value"] + sum(f["contribution_kg_co2e_per_ha"] for f in exp["factors"])
    # contributions are rounded to 2 dp each (5 factors) -> allow a few cents
    assert reconstructed == pytest.approx(body["carbon_footprint_kg_co2e_per_ha"], abs=0.1)


def test_explanation_shape_and_ordering():
    headers = _login()
    body = _what_if(headers, _farm(headers, "Wheat")).json()
    factors = body["explanation"]["factors"]
    assert {f["feature"] for f in factors} == {
        "crop_type",
        "fertilizer_usage_kg_per_ha",
        "fuel_consumption_liters_per_ha",
        "water_consumption_m3_per_ha",
        "electricity_consumption_kwh_per_ha",
    }
    magnitudes = [abs(f["contribution_kg_co2e_per_ha"]) for f in factors]
    assert magnitudes == sorted(magnitudes, reverse=True)
    for f in factors:
        assert f["direction"] == ("increases" if f["contribution_kg_co2e_per_ha"] > 0 else "decreases")
    crop_factor = next(f for f in factors if f["feature"] == "crop_type")
    assert crop_factor["value"] == "Wheat"


def test_more_water_raises_footprint_and_water_contribution():
    headers = _login()
    farm_id = _farm(headers)
    low = _what_if(headers, farm_id, water_consumption_m3_per_ha=5000.0).json()
    high = _what_if(headers, farm_id, water_consumption_m3_per_ha=17000.0).json()
    assert high["carbon_footprint_kg_co2e_per_ha"] > low["carbon_footprint_kg_co2e_per_ha"]

    def water(body):
        return next(f for f in body["explanation"]["factors"] if f["feature"] == "water_consumption_m3_per_ha")

    assert water(high)["contribution_kg_co2e_per_ha"] > water(low)["contribution_kg_co2e_per_ha"]


# --- what-if matches a real prediction, and stores nothing ------------------

def test_what_if_matches_real_prediction_exactly():
    headers = _login()
    farm_id = _farm(headers, "Maize", area=7.5)
    real = client.post("/api/v1/predictions/carbon", headers=headers, json={"farm_id": farm_id, **INPUTS})
    assert real.status_code == 201
    real = real.json()
    sim = _what_if(headers, farm_id).json()

    assert sim["carbon_footprint_kg_co2e_per_ha"] == real["carbon_footprint_kg_co2e_per_ha"]
    assert sim["carbon_category"] == real["carbon_category"]
    assert sim["sustainability_score"] == real["sustainability_score"]
    assert sim["sustainability_category"] == real["sustainability_category"]
    assert sim["total_farm_emissions_kg_co2e"] == real["total_farm_emissions_kg_co2e"]


def test_what_if_does_not_persist_anything():
    headers = _login()
    farm_id = _farm(headers)
    before = _prediction_count()
    for _ in range(3):
        resp = _what_if(headers, farm_id)
        assert resp.status_code == 200
        assert resp.json()["persisted"] is False
    assert _prediction_count() == before
    assert client.get("/api/v1/predictions/history", headers=headers).json() == []


# --- what-if access control and validation ----------------------------------

def test_what_if_requires_auth():
    assert client.post("/api/v1/predictions/what-if", json={"farm_id": 1, **INPUTS}).status_code == 401


def test_what_if_on_another_users_farm_is_404():
    owner = _login("owner@example.com")
    farm_id = _farm(owner)
    intruder = _login("intruder@example.com")
    assert _what_if(intruder, farm_id).status_code == 404


def test_what_if_unknown_farm_is_404():
    assert _what_if(_login(), 999999).status_code == 404


@pytest.mark.parametrize("field,bad", [
    ("fertilizer_usage_kg_per_ha", 0),
    ("fuel_consumption_liters_per_ha", -1),
    ("water_consumption_m3_per_ha", 1e300),
    ("electricity_consumption_kwh_per_ha", 99999),
])
def test_what_if_applies_the_same_validation_as_real_predictions(field, bad):
    headers = _login()
    assert _what_if(headers, _farm(headers), **{field: bad}).status_code == 422


def test_what_if_rejects_infinity_with_422_not_500():
    headers = _login()
    farm_id = _farm(headers)
    resp = client.post(
        "/api/v1/predictions/what-if",
        headers={**headers, "Content-Type": "application/json"},
        content='{"farm_id": %d, "fertilizer_usage_kg_per_ha": Infinity, '
                '"fuel_consumption_liters_per_ha": 1, "water_consumption_m3_per_ha": 1, '
                '"electricity_consumption_kwh_per_ha": 1}' % farm_id,
    )
    assert resp.status_code == 422


# --- stored prediction explanation ------------------------------------------

def test_stored_prediction_explanation_matches_what_if_on_same_inputs():
    headers = _login()
    farm_id = _farm(headers, "Sugarcane")
    real = client.post("/api/v1/predictions/carbon", headers=headers, json={"farm_id": farm_id, **INPUTS}).json()
    stored = client.get(f"/api/v1/predictions/{real['prediction_id']}/explanation", headers=headers)
    assert stored.status_code == 200, stored.text
    stored = stored.json()
    sim = _what_if(headers, farm_id).json()

    assert stored["prediction_id"] == real["prediction_id"]
    assert stored["carbon_footprint_kg_co2e_per_ha"] == real["carbon_footprint_kg_co2e_per_ha"]
    assert stored["explanation"] == sim["explanation"]


def test_stored_explanation_requires_auth():
    assert client.get("/api/v1/predictions/1/explanation").status_code == 401


def test_stored_explanation_of_another_users_prediction_is_404():
    owner = _login("owner2@example.com")
    farm_id = _farm(owner)
    pred_id = client.post("/api/v1/predictions/carbon", headers=owner, json={"farm_id": farm_id, **INPUTS}).json()["prediction_id"]
    intruder = _login("intruder2@example.com")
    assert client.get(f"/api/v1/predictions/{pred_id}/explanation", headers=intruder).status_code == 404


def test_stored_explanation_unknown_id_is_404():
    assert client.get("/api/v1/predictions/999999/explanation", headers=_login()).status_code == 404
