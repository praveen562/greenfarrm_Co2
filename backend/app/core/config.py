"""
Application configuration.

All values are read from environment variables (see .env.example at the repo
root). Nothing here should be hardcoded to a real secret or credential.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    PROJECT_NAME: str = "GreenFarm Carbon AI"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str

    # --- Auth ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # --- ML artifact paths (relative to repo root) ---
    MODEL_PATH: str = "ml/models/carbon_model.joblib"
    PREPROCESSOR_PATH: str = "ml/models/preprocessor.joblib"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so we parse the environment only once."""
    return Settings()
