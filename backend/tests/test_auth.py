"""
Phase 10: authentication tests — real bcrypt hashing, real JWTs, real
protected-route enforcement, against a live Postgres DB.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.security import verify_password
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


def test_register_creates_user_with_hashed_password():
    response = client.post("/api/v1/auth/register", json={
        "email": "newfarmer@example.com", "password": "strongpassword1", "full_name": "New Farmer",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newfarmer@example.com"
    assert "password" not in body
    assert "hashed_password" not in body

    db = SessionLocal()
    user = db.query(User).filter(User.email == "newfarmer@example.com").first()
    assert user.hashed_password != "strongpassword1"  # never plaintext
    assert verify_password("strongpassword1", user.hashed_password)
    db.close()


def test_register_duplicate_email_returns_400():
    payload = {"email": "dupe@example.com", "password": "password123", "full_name": "Dupe"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


def test_register_short_password_returns_422():
    response = client.post("/api/v1/auth/register", json={
        "email": "shortpw@example.com", "password": "short", "full_name": "Short PW",
    })
    assert response.status_code == 422


def test_login_success_returns_jwt():
    client.post("/api/v1/auth/register", json={
        "email": "loginok@example.com", "password": "correctpassword", "full_name": "Login OK",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "loginok@example.com", "password": "correctpassword",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password_returns_401():
    client.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com", "password": "correctpassword", "full_name": "Wrong PW",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com", "password": "incorrectpassword",
    })
    assert response.status_code == 401


def test_login_unknown_email_returns_401():
    response = client.post("/api/v1/auth/login", json={
        "email": "doesnotexist@example.com", "password": "whatever123",
    })
    assert response.status_code == 401


def test_me_without_token_returns_401():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_returns_401():
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_with_valid_token_returns_current_user():
    client.post("/api/v1/auth/register", json={
        "email": "meuser@example.com", "password": "password123", "full_name": "Me User",
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "meuser@example.com", "password": "password123",
    })
    token = login_resp.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "meuser@example.com"
