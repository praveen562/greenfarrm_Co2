"""
Farms router.

Phase 7 scope: routes + schemas defined and validated. Real persistence
(PostgreSQL via SQLAlchemy) lands in Phase 9. Returning 501 here rather
than an in-memory fake store, so nothing about "farm data" is ever
presented as real before it actually is.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.farm import FarmCreate, FarmOut, FarmUpdate

router = APIRouter()


@router.post("/", response_model=FarmOut, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def create_farm(payload: FarmCreate):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Farm persistence lands in Phase 9 (PostgreSQL database).",
    )


@router.get("/", response_model=list[FarmOut], status_code=status.HTTP_501_NOT_IMPLEMENTED)
def list_farms():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Farm persistence lands in Phase 9 (PostgreSQL database).",
    )


@router.get("/{farm_id}", response_model=FarmOut, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def get_farm(farm_id: int):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Farm persistence lands in Phase 9 (PostgreSQL database).",
    )


@router.patch("/{farm_id}", response_model=FarmOut, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def update_farm(farm_id: int, payload: FarmUpdate):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Farm persistence lands in Phase 9 (PostgreSQL database).",
    )
