"""
Database model tests — run against a real PostgreSQL instance (not
SQLite), using the same DATABASE_URL / engine configuration the app uses.
Requires the DB from docker-compose (or any reachable Postgres) with
migrations applied: `alembic upgrade head`.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.user import User


@pytest.fixture(scope="module")
def db_session():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def clean_tables(db_session: Session):
    """Each test starts with empty tables (order matters: children first)."""
    db_session.query(Recommendation).delete()
    db_session.query(Prediction).delete()
    db_session.query(Farm).delete()
    db_session.query(User).delete()
    db_session.commit()
    yield


def test_create_user(db_session: Session):
    user = User(email="farmer@example.com", hashed_password="not-a-real-hash", full_name="Test Farmer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.created_at is not None


def test_create_farm_linked_to_user(db_session: Session):
    user = User(email="farmer2@example.com", hashed_password="x", full_name="Farmer Two")
    db_session.add(user)
    db_session.commit()

    farm = Farm(user_id=user.id, farm_name="Green Acres", location="Punjab", area=12.5, crop_type="Rice")
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)

    assert farm.id is not None
    assert farm.user.email == "farmer2@example.com"
    assert user.farms[0].farm_name == "Green Acres"


def test_create_prediction_and_recommendation_chain(db_session: Session):
    user = User(email="farmer3@example.com", hashed_password="x", full_name="Farmer Three")
    db_session.add(user)
    db_session.commit()

    farm = Farm(user_id=user.id, farm_name="Sunny Fields", location="Iowa", area=8.0, crop_type="Maize")
    db_session.add(farm)
    db_session.commit()

    prediction = Prediction(
        farm_id=farm.id,
        fertilizer_usage=180,
        fuel_consumption=120,
        water_consumption=2500,
        electricity_consumption=500,
        predicted_carbon=1523.45,
        carbon_category="High",
    )
    db_session.add(prediction)
    db_session.commit()

    recommendation = Recommendation(
        prediction_id=prediction.id,
        category="fertilizer",
        text="Reduce fertilizer application after soil testing.",
    )
    db_session.add(recommendation)
    db_session.commit()

    db_session.refresh(farm)
    db_session.refresh(prediction)

    assert farm.predictions[0].predicted_carbon == 1523.45
    assert prediction.recommendations[0].category == "fertilizer"


def test_cascade_delete_farm_removes_predictions(db_session: Session):
    user = User(email="farmer4@example.com", hashed_password="x", full_name="Farmer Four")
    db_session.add(user)
    db_session.commit()

    farm = Farm(user_id=user.id, farm_name="Old Barn", location="Ohio", area=5.0, crop_type="Wheat")
    db_session.add(farm)
    db_session.commit()

    prediction = Prediction(
        farm_id=farm.id, fertilizer_usage=100, fuel_consumption=50,
        water_consumption=3000, electricity_consumption=200,
        predicted_carbon=900.0, carbon_category="Moderate",
    )
    db_session.add(prediction)
    db_session.commit()
    prediction_id = prediction.id

    db_session.delete(farm)
    db_session.commit()

    remaining = db_session.get(Prediction, prediction_id)
    assert remaining is None  # cascade delete confirmed on the real DB


def test_duplicate_email_raises_integrity_error(db_session: Session):
    from sqlalchemy.exc import IntegrityError

    db_session.add(User(email="dup@example.com", hashed_password="x", full_name="First"))
    db_session.commit()

    db_session.add(User(email="dup@example.com", hashed_password="y", full_name="Second"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
