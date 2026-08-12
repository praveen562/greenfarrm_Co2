"""
GreenFarm Carbon AI — FastAPI entrypoint.

Phase 1 scope: application bootstraps, CORS is configured, and a health
check endpoint proves the service and config wiring work end to end.
Routers (auth, farms, predictions, dashboard) are added in later phases.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Liveness/readiness probe. Does not touch the database or ML model."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


# NOTE: routers are registered here in later phases, e.g.:
# from app.api.v1 import auth, farms, predictions, dashboard
# app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
