"""
Import all ORM models here so Base.metadata sees every table. Alembic's
env.py imports this module (not each model file individually) for
autogenerate to work correctly.
"""
from app.db.base_class import Base  # noqa: F401
from app.models.farm import Farm  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.user import User  # noqa: F401
