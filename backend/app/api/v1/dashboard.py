"""
Dashboard router.

Phase 7 scope: schema defined. Real aggregation queries against the
Prediction/Farm tables land in Phase 9 (database) + Phase 14 (historical
analytics) — returning 501 rather than hardcoded dashboard stats.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.dashboard import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def dashboard_summary():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Dashboard aggregation lands in Phase 9 (database) + Phase 14 (historical analytics).",
    )
