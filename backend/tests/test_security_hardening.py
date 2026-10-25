"""
Phase 15: security-hardening regression tests.

Each test pins a behaviour that was a real defect found by probing the live
API (inf/NaN and oversized input returned 500, absurd values were stored,
weak SECRET_KEY was accepted, tokens without `exp` were honoured).
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.main import app
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.user import User

client = TestClient(app, raise_server_exceptions=False)

VALID_INPUTS = {
    "fertilizer_usage_kg_per_ha": 120.0,
    "fuel_consumption_liters_per_ha": 60.0,
    "water_consumption_m3_per_ha": 9000.0,
    "electricity_consumption_kwh_per_ha": 300.0,
}


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


def _login(email="hardening@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1", "full_name": "Hardening Tester",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _make_farm(headers) -> int:
    resp = client.post("/api/v1/farms/", headers=headers, json={
        "farm_name": "F", "location": "L", "area": 5, "crop_type": "Rice",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def _predict_raw(headers, farm_id, **overrides):
    """Send raw JSON text so non-standard literals (NaN/Infinity) reach the server."""
    import json

    body = {"farm_id": farm_id, **VALID_INPUTS, **overrides}
    text = json.dumps(body, allow_nan=True)
    return client.post(
        "/api/v1/predictions/carbon",
        headers={**headers, "Content-Type": "application/json"},
        content=text,
    )


# --- prediction input validation ------------------------------------------

@pytest.mark.parametrize("field", list(VALID_INPUTS))
@pytest.mark.parametrize("bad", [float("inf"), float("nan")])
def test_prediction_rejects_inf_and_nan_with_422(field, bad):
    headers = _login()
    farm_id = _make_farm(headers)
    resp = _predict_raw(headers, farm_id, **{field: bad})
    assert resp.status_code == 422, resp.text


@pytest.mark.parametrize("field", list(VALID_INPUTS))
def test_prediction_rejects_absurdly_large_values(field):
    headers = _login()
    farm_id = _make_farm(headers)
    resp = _predict_raw(headers, farm_id, **{field: 1e300})
    assert resp.status_code == 422, resp.text


def test_prediction_still_accepts_realistic_values():
    headers = _login()
    farm_id = _make_farm(headers)
    assert _predict_raw(headers, farm_id).status_code == 201


def test_prediction_accepts_heavy_use_above_training_range():
    """Ceilings must not reject plausible farms just above the training maxima."""
    headers = _login()
    farm_id = _make_farm(headers)
    resp = _predict_raw(
        headers, farm_id,
        fertilizer_usage_kg_per_ha=400.0,
        fuel_consumption_liters_per_ha=200.0,
        water_consumption_m3_per_ha=25000.0,
        electricity_consumption_kwh_per_ha=1200.0,
    )
    assert resp.status_code == 201, resp.text


# --- farm area validation --------------------------------------------------

@pytest.mark.parametrize("area", ["Infinity", "NaN", "1e300"])
def test_farm_area_rejects_inf_nan_and_absurd_values(area):
    headers = _login()
    resp = client.post(
        "/api/v1/farms/",
        headers={**headers, "Content-Type": "application/json"},
        content='{"farm_name":"F","location":"L","area":%s,"crop_type":"Rice"}' % area,
    )
    assert resp.status_code == 422, resp.text


def test_farm_update_area_rejects_inf():
    headers = _login()
    farm_id = _make_farm(headers)
    resp = client.patch(
        f"/api/v1/farms/{farm_id}",
        headers={**headers, "Content-Type": "application/json"},
        content='{"area": Infinity}',
    )
    assert resp.status_code == 422, resp.text


# --- password handling -----------------------------------------------------

def test_register_rejects_password_over_72_chars():
    resp = client.post("/api/v1/auth/register", json={
        "email": "long@example.com", "password": "x" * 73, "full_name": "Long",
    })
    assert resp.status_code == 422


def test_register_accepts_72_char_password():
    resp = client.post("/api/v1/auth/register", json={
        "email": "edge@example.com", "password": "x" * 72, "full_name": "Edge",
    })
    assert resp.status_code == 201


def test_login_with_oversized_password_is_not_a_500():
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "x" * 100_000,
    })
    assert resp.status_code == 422


def test_login_unknown_email_and_wrong_password_are_indistinguishable():
    _login("real@example.com")
    unknown = client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever123"})
    wrong = client.post("/api/v1/auth/login", json={"email": "real@example.com", "password": "whatever123"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


# --- JWT -------------------------------------------------------------------

def _forge(claims: dict, key: str | None = None) -> dict:
    s = get_settings()
    token = jwt.encode(claims, key or s.SECRET_KEY, algorithm=s.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def test_token_without_exp_is_rejected():
    headers = _login()
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    resp = client.get("/api/v1/auth/me", headers=_forge({"sub": str(user_id)}))
    assert resp.status_code == 401


def test_expired_token_is_rejected():
    headers = _login()
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    resp = client.get("/api/v1/auth/me", headers=_forge({"sub": str(user_id), "exp": past}))
    assert resp.status_code == 401


def test_token_signed_with_wrong_key_is_rejected():
    headers = _login()
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    resp = client.get(
        "/api/v1/auth/me",
        headers=_forge({"sub": str(user_id), "exp": future}, key="a-completely-different-signing-key-123456"),
    )
    assert resp.status_code == 401


def test_valid_token_still_works():
    headers = _login()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


# --- SECRET_KEY strength ---------------------------------------------------

@pytest.mark.parametrize("weak", ["short", "replace_with_a_long_random_string", "x" * 31])
def test_weak_secret_key_is_rejected(weak):
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="postgresql://u:p@localhost/db", SECRET_KEY=weak)


def test_strong_secret_key_is_accepted():
    Settings(DATABASE_URL="postgresql://u:p@localhost/db", SECRET_KEY="k" * 48)


# --- CORS ------------------------------------------------------------------

def test_cors_preflight_allows_configured_origin_and_authorization_header():
    resp = client.options(
        "/api/v1/farms/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_rejects_unlisted_origin():
    resp = client.options(
        "/api/v1/farms/",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in resp.headers
