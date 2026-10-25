"""Auth schemas. Endpoints are wired up for real in Phase 10 (JWT auth);
for now these define and validate the request/response contract."""
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72, description="8-72 characters (bcrypt ignores anything past 72 bytes)")
    full_name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    # Capped so an oversized body can't reach the hasher (passlib raised -> 500).
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
