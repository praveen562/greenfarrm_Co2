from pydantic import BaseModel, ConfigDict


class ModelMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float


class FeatureImportanceItem(BaseModel):
    feature: str
    importance_pct: float


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = "XGBoost Regressor"
    metrics: ModelMetrics
    feature_importance: list[FeatureImportanceItem]
    n_train: int
    n_test: int
