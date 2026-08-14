"""
Phase 6: final evaluation on the held-out test set + save the best model.

- Trains all three models on the FULL training set (train.csv) — this is
  the first time test.csv is touched by any model.
- Evaluates all three on test.csv for a complete comparison table (not just
  the Phase 5 cross-validation numbers).
- Extracts real feature importance from the selected XGBoost model.
- Saves the final XGBoost model via joblib.
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

TRAIN_PATH = "../datasets/train.csv"
TEST_PATH = "../datasets/test.csv"
PREPROCESSOR_PATH = "../models/preprocessor.joblib"
MODEL_PATH = "../models/carbon_model.joblib"
TARGET = "carbon_footprint_kg_co2e_per_ha"

CATEGORICAL_FEATURES = ["crop_type"]
NUMERIC_FEATURES = [
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
RANDOM_STATE = 42


def evaluate(model, X_test, y_test) -> dict:
    preds = model.predict(X_test)
    return {
        "mae": mean_absolute_error(y_test, preds),
        "rmse": np.sqrt(mean_squared_error(y_test, preds)),
        "r2": r2_score(y_test, preds),
    }


def main():
    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    preprocessor = joblib.load(PREPROCESSOR_PATH)
    X_train = preprocessor.transform(train_df[ALL_FEATURES])
    X_test = preprocessor.transform(test_df[ALL_FEATURES])
    y_train = train_df[TARGET].values
    y_test = test_df[TARGET].values

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            random_state=RANDOM_STATE, n_jobs=-1
        ),
    }

    print(f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'R²':<10}")
    print("-" * 54)

    test_results = {}
    fitted_models = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        fitted_models[name] = model
        metrics = evaluate(model, X_test, y_test)
        test_results[name] = metrics
        print(f"{name:<20} {metrics['mae']:<12.2f} {metrics['rmse']:<12.2f} {metrics['r2']:<10.4f}")

    # --- Save the selected model (XGBoost) ---
    best_model = fitted_models["XGBoost"]
    joblib.dump(best_model, MODEL_PATH)
    print(f"\nSaved final model -> {MODEL_PATH}")

    # --- Feature importance (real values from the trained model) ---
    feature_names = preprocessor.get_feature_names_out()
    importances = best_model.feature_importances_
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    importance_df["importance_pct"] = (importance_df["importance"] / importance_df["importance"].sum() * 100).round(2)

    print("\n=== XGBoost feature importance (real, from trained model) ===")
    print(importance_df.to_string(index=False))

    # Save results for the Phase 6 report / progress log
    with open("../evaluation/test_set_results.json", "w") as f:
        json.dump({
            "test_results": {k: {mk: float(mv) for mk, mv in v.items()} for k, v in test_results.items()},
            "feature_importance": importance_df.to_dict(orient="records"),
            "n_train": len(train_df),
            "n_test": len(test_df),
        }, f, indent=2)
    print("\nSaved raw results -> ../evaluation/test_set_results.json")


if __name__ == "__main__":
    main()
