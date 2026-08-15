"""
Model info router.

Serves the real evaluation results produced by
ml/evaluation/evaluate_and_save.py (Phase 6) — reads
ml/evaluation/test_set_results.json directly rather than hardcoding any
metric or importance value in application code. If that file is missing
(model not yet trained/evaluated), this returns 503 rather than fabricated
numbers.
"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.schemas.model_info import ModelInfo

router = APIRouter()

RESULTS_FILENAME = "ml/evaluation/test_set_results.json"


def _resolve_results_path() -> Path:
    cwd_relative = Path(RESULTS_FILENAME)
    if cwd_relative.exists():
        return cwd_relative
    repo_root = Path(__file__).resolve().parents[4]
    repo_root_relative = repo_root / RESULTS_FILENAME
    if repo_root_relative.exists():
        return repo_root_relative
    raise FileNotFoundError(RESULTS_FILENAME)


@router.get("/info", response_model=ModelInfo)
def get_model_info():
    try:
        path = _resolve_results_path()
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model evaluation results are not available. Has evaluate_and_save.py been run?",
        ) from exc

    xgb = data["test_results"]["XGBoost"]
    return ModelInfo(
        metrics={"mae": xgb["mae"], "rmse": xgb["rmse"], "r2": xgb["r2"]},
        feature_importance=[
            {"feature": item["feature"], "importance_pct": item["importance_pct"]}
            for item in data["feature_importance"]
        ],
        n_train=data["n_train"],
        n_test=data["n_test"],
    )
