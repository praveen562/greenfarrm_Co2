"""
Loads the trained model + preprocessor once and caches them in memory.

Path resolution: MODEL_PATH/PREPROCESSOR_PATH in config are repo-root
relative (this matches the Docker container, where the docker-compose
volume mount puts ml/models directly under the backend's WORKDIR). For
local (non-Docker) dev, the backend runs with cwd=backend/, so the
repo-root-relative path won't resolve from cwd alone — this mirrors the
same class of bug caught with .env in Phase 1, so we resolve defensively:
try cwd-relative first, then fall back to resolving relative to the actual
repo root computed from this file's location.
"""
import logging
from pathlib import Path
from typing import Any

import joblib

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ModelLoadError(RuntimeError):
    """Raised when the trained model or preprocessor can't be loaded."""


def _resolve_artifact_path(configured_path: str) -> Path:
    cwd_relative = Path(configured_path)
    if cwd_relative.exists():
        return cwd_relative

    # backend/app/ml/model_loader.py -> parents[3] == repo root
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_relative = repo_root / configured_path
    if repo_root_relative.exists():
        return repo_root_relative

    raise ModelLoadError(
        f"Could not find ML artifact '{configured_path}'. Tried "
        f"{cwd_relative.resolve()} and {repo_root_relative}. "
        f"Has the model been trained (see ml/evaluation/evaluate_and_save.py)?"
    )


_model: Any = None
_preprocessor: Any = None


def get_model():
    global _model
    if _model is None:
        settings = get_settings()
        path = _resolve_artifact_path(settings.MODEL_PATH)
        try:
            _model = joblib.load(path)
            logger.info("Loaded ML model from %s", path)
        except Exception as exc:  # noqa: BLE001 — deliberately broad, re-raised as ModelLoadError
            raise ModelLoadError(f"Failed to load ML model from {path}: {exc}") from exc
    return _model


def get_preprocessor():
    global _preprocessor
    if _preprocessor is None:
        settings = get_settings()
        path = _resolve_artifact_path(settings.PREPROCESSOR_PATH)
        try:
            _preprocessor = joblib.load(path)
            logger.info("Loaded preprocessor from %s", path)
        except Exception as exc:  # noqa: BLE001
            raise ModelLoadError(f"Failed to load preprocessor from {path}: {exc}") from exc
    return _preprocessor


def reset_cache() -> None:
    """Test-only helper to force a reload on the next get_model()/get_preprocessor() call."""
    global _model, _preprocessor
    _model = None
    _preprocessor = None
