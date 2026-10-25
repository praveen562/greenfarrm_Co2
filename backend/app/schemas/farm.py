from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.crop_type import CropType


# Larger than any single real farm; rejects inf/NaN and absurd values (was a 500).
MAX_FARM_AREA_HA = 1_000_000


class FarmCreate(BaseModel):
    farm_name: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    area: float = Field(gt=0, le=MAX_FARM_AREA_HA, allow_inf_nan=False, description="Farm area in hectares")
    crop_type: CropType


class FarmUpdate(BaseModel):
    farm_name: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, min_length=1, max_length=200)
    area: float | None = Field(default=None, gt=0, le=MAX_FARM_AREA_HA, allow_inf_nan=False)
    crop_type: CropType | None = None


class FarmOut(BaseModel):
    id: int
    user_id: int
    farm_name: str
    location: str
    area: float
    crop_type: CropType
    created_at: datetime

    model_config = {"from_attributes": True}
