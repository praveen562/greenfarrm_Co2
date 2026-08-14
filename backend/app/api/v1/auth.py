"""
Auth router.

Phase 7 scope: routes exist, request/response schemas are enforced by
Pydantic (so validation errors are real and testable now). Password
hashing + real JWT issuance land in Phase 10 — until then these return
501 rather than a fake token, per the "never fake ML/business responses"
rule.
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import Token, UserCreate, UserLogin, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def register(payload: UserCreate):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration lands in Phase 10 (authentication) once the User DB model exists.",
    )


@router.post("/login", response_model=Token, status_code=status.HTTP_501_NOT_IMPLEMENTED)
def login(payload: UserLogin):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login lands in Phase 10 (authentication) once the User DB model exists.",
    )
