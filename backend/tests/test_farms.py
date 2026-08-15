"""
Phase 10: farms router tests — real persistence, auth-protected,
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


def _register_and_login(email="farmowner@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1", "full_name": "Farm Owner",
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_farm_requires_auth():
    response = client.post("/api/v1/farms/", json={
        "farm_name": "X", "location": "Y", "area": 5.0, "crop_type": "Rice",
    })
    assert response.status_code == 401


def test_create_and_list_farm():
    headers = _register_and_login()
    create_resp = client.post("/api/v1/farms/", json={
        "farm_name": "Green Acres", "location": "Punjab", "area": 12.5, "crop_type": "Rice",
    }, headers=headers)
    assert create_resp.status_code == 201
    farm_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/farms/", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == farm_id


def test_invalid_crop_type_returns_422():
    headers = _register_and_login()
    response = client.post("/api/v1/farms/", json={
        "farm_name": "X", "location": "Y", "area": 5.0, "crop_type": "Dragonfruit",
    }, headers=headers)
    assert response.status_code == 422


def test_negative_area_returns_422():
    headers = _register_and_login()
    response = client.post("/api/v1/farms/", json={
        "farm_name": "X", "location": "Y", "area": -5.0, "crop_type": "Rice",
    }, headers=headers)
    assert response.status_code == 422


def test_users_cannot_see_each_others_farms():
    headers_a = _register_and_login("farm_a@example.com")
    client.post("/api/v1/farms/", json={
        "farm_name": "Farm A", "location": "Loc A", "area": 5.0, "crop_type": "Wheat",
    }, headers=headers_a)

    headers_b = _register_and_login("farm_b@example.com")
    list_resp = client.get("/api/v1/farms/", headers=headers_b)
    assert list_resp.status_code == 200
    assert list_resp.json() == []


def test_users_cannot_get_or_update_or_delete_others_farm():
    headers_a = _register_and_login("owner_x@example.com")
    create_resp = client.post("/api/v1/farms/", json={
        "farm_name": "Farm X", "location": "Loc X", "area": 5.0, "crop_type": "Maize",
    }, headers=headers_a)
    farm_id = create_resp.json()["id"]

    headers_b = _register_and_login("owner_y@example.com")
    assert client.get(f"/api/v1/farms/{farm_id}", headers=headers_b).status_code == 404
    assert client.patch(f"/api/v1/farms/{farm_id}", json={"farm_name": "Hacked"}, headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/farms/{farm_id}", headers=headers_b).status_code == 404


def test_update_own_farm():
    headers = _register_and_login("updater@example.com")
    create_resp = client.post("/api/v1/farms/", json={
        "farm_name": "Old Name", "location": "Loc", "area": 5.0, "crop_type": "Cotton",
    }, headers=headers)
    farm_id = create_resp.json()["id"]

    update_resp = client.patch(f"/api/v1/farms/{farm_id}", json={"farm_name": "New Name"}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["farm_name"] == "New Name"


def test_delete_own_farm():
    headers = _register_and_login("deleter@example.com")
    create_resp = client.post("/api/v1/farms/", json={
        "farm_name": "To Delete", "location": "Loc", "area": 5.0, "crop_type": "Soybean",
    }, headers=headers)
    farm_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/farms/{farm_id}", headers=headers)
    assert delete_resp.status_code == 204
    assert client.get(f"/api/v1/farms/{farm_id}", headers=headers).status_code == 404
