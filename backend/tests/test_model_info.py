"""
Model info endpoint: serves the real evaluate_and_save.py output, never
fabricated numbers.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_model_info_returns_real_metrics():
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    body = response.json()

    with open(Path(__file__).resolve().parents[2] / "ml/evaluation/test_set_results.json") as f:
        expected = json.load(f)

    assert body["metrics"]["mae"] == expected["test_results"]["XGBoost"]["mae"]
    assert body["metrics"]["r2"] == expected["test_results"]["XGBoost"]["r2"]
    assert len(body["feature_importance"]) == len(expected["feature_importance"])
    assert body["model_name"] == "XGBoost Regressor"
    assert body["n_train"] == expected["n_train"]
