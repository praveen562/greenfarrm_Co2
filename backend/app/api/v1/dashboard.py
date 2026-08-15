"""
Dashboard router.

Phase 14: real aggregation queries against Farm/Prediction, always scoped
to `current_user.id` via a join through Farm — a user can never see
another user's stats. No hardcoded numbers anywhere here.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.dashboard import CropStat, DashboardSummary, HistoryPoint, RecentPrediction

router = APIRouter()


def _user_predictions_query(db: Session, current_user: User):
    return (
        db.query(Prediction)
        .join(Farm, Prediction.farm_id == Farm.id)
        .filter(Farm.user_id == current_user.id)
    )


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_farms = db.query(Farm).filter(Farm.user_id == current_user.id).count()

    base = _user_predictions_query(db, current_user)
    total_predictions = base.count()

    aggregates = (
        db.query(
            func.avg(Prediction.predicted_carbon),
            func.avg(Prediction.sustainability_score),
        )
        .select_from(Prediction)
        .join(Farm, Prediction.farm_id == Farm.id)
        .filter(Farm.user_id == current_user.id)
        .first()
    )
    avg_footprint, avg_score = aggregates if aggregates else (None, None)

    latest = base.order_by(Prediction.created_at.desc()).first()

    recent = base.order_by(Prediction.created_at.desc()).limit(5).all()

    return DashboardSummary(
        total_farms=total_farms,
        total_predictions=total_predictions,
        latest_carbon_footprint_kg_co2e_per_ha=latest.predicted_carbon if latest else None,
        average_carbon_footprint_kg_co2e_per_ha=round(avg_footprint, 2) if avg_footprint is not None else None,
        average_sustainability_score=round(avg_score, 1) if avg_score is not None else None,
        recent_predictions=[
            RecentPrediction(
                prediction_id=p.id,
                farm_id=p.farm_id,
                farm_name=p.farm.farm_name,
                crop_type=p.farm.crop_type,
                carbon_footprint_kg_co2e_per_ha=p.predicted_carbon,
                carbon_category=p.carbon_category,
                sustainability_score=p.sustainability_score,
                created_at=p.created_at,
            )
            for p in recent
        ],
    )


@router.get("/history", response_model=list[HistoryPoint])
def dashboard_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    predictions = _user_predictions_query(db, current_user).order_by(Prediction.created_at.asc()).all()
    return [
        HistoryPoint(
            prediction_id=p.id,
            farm_id=p.farm_id,
            farm_name=p.farm.farm_name,
            carbon_footprint_kg_co2e_per_ha=p.predicted_carbon,
            sustainability_score=p.sustainability_score,
            created_at=p.created_at,
        )
        for p in predictions
    ]


@router.get("/crop-stats", response_model=list[CropStat])
def dashboard_crop_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            Farm.crop_type,
            func.count(Prediction.id),
            func.avg(Prediction.predicted_carbon),
        )
        .join(Prediction, Prediction.farm_id == Farm.id)
        .filter(Farm.user_id == current_user.id)
        .group_by(Farm.crop_type)
        .all()
    )
    return [
        CropStat(
            crop_type=crop_type,
            prediction_count=count,
            average_carbon_footprint_kg_co2e_per_ha=round(avg_footprint, 2),
        )
        for crop_type, count, avg_footprint in rows
    ]
