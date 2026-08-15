"""
Farms router.

Phase 9 added real persistence models; Phase 10 wires the routes to that
persistence AND protects every route behind authentication, scoping every
query to `current_user.id` so no user can ever see or modify another
user's farms.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.user import User
from app.schemas.farm import FarmCreate, FarmOut, FarmUpdate

router = APIRouter()


def _get_owned_farm_or_404(farm_id: int, current_user: User, db: Session) -> Farm:
    farm = db.get(Farm, farm_id)
    if farm is None or farm.user_id != current_user.id:
        # Same 404 whether the farm doesn't exist or belongs to someone else —
        # never leak the existence of another user's data.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found.")
    return farm


@router.post("/", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = Farm(user_id=current_user.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/", response_model=list[FarmOut])
def list_farms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Farm)
        .filter(Farm.user_id == current_user.id)
        .order_by(Farm.created_at.desc())
        .all()
    )


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_farm_or_404(farm_id, current_user, db)


@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = _get_owned_farm_or_404(farm_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = _get_owned_farm_or_404(farm_id, current_user, db)
    db.delete(farm)
    db.commit()
