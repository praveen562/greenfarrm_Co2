"""
GreenFarm Carbon AI — FastAPI entrypoint.

Phase 1 scope: application bootstraps, CORS is configured, and a health
check endpoint proves the service and config wiring work end to end.
Routers (auth, farms, predictions, dashboard) are added in later phases.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, dashboard, farms, model_info, predictions
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
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 body with loc/msg/type only.

    FastAPI's default handler echoes each rejected value back under `input`.
    For `Infinity`/`NaN` that value can't be serialised as JSON, so the
    *rejection itself* crashed with a 500. It also reflected request data
    (e.g. oversized passwords) back to the client. Same shape as the default
    minus `input`/`ctx`, so existing clients keep working.
    """
    errors = [
        {"loc": list(err.get("loc", ())), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errors})


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Liveness/readiness probe. Does not touch the database or ML model."""
    return {"status": "ok", "service": settings.PROJECT_NAME}


app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(farms.router, prefix=f"{settings.API_V1_PREFIX}/farms", tags=["farms"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_PREFIX}/predictions", tags=["predictions"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(model_info.router, prefix=f"{settings.API_V1_PREFIX}/model", tags=["model"])
