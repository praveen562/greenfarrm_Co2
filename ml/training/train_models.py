"""
Phase 5: train and cross-validate the three candidate models.

Uses the preprocessor fitted in Phase 4 (ml/models/preprocessor.joblib) —
never refits it here. All three models see the exact same transformed
features, so comparisons are apples-to-apples.

5-fold cross-validation on the TRAINING set only (test.csv is untouched
until Phase 6's final evaluation, to keep it a genuinely held-out set).
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate
from xgboost import XGBRegressor

TRAIN_PATH = "../datasets/train.csv"
PREPROCESSOR_PATH = "../models/preprocessor.joblib"
TARGET = "carbon_footprint_kg_co2e_per_ha"

# Must match ml/preprocessing/build_preprocessor.py's ALL_FEATURES exactly —
# duplicated here (rather than imported across the preprocessing/training
# folder boundary) to keep each ml/ subfolder independently runnable.
CATEGORICAL_FEATURES = ["crop_type"]
NUMERIC_FEATURES = [
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

RANDOM_STATE = 42


def rmse_scorer(estimator, X, y):
    preds = estimator.predict(X)
    return -np.sqrt(np.mean((y - preds) ** 2))  # negative so "higher is better" for cross_validate


def main():
    train_df = pd.read_csv(TRAIN_PATH)
    X_train_raw = train_df[ALL_FEATURES]
    y_train = train_df[TARGET].values

    preprocessor = joblib.load(PREPROCESSOR_PATH)
    X_train = preprocessor.transform(X_train_raw)

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            random_state=RANDOM_STATE, n_jobs=-1
        ),
    }

    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scoring = {
        "mae": "neg_mean_absolute_error",
        "rmse": rmse_scorer,
        "r2": "r2",
    }

    print(f"{'Model':<20} {'MAE (mean±std)':<22} {'RMSE (mean±std)':<22} {'R² (mean±std)':<20}")
    print("-" * 84)

    results = {}
    for name, model in models.items():
        cv_results = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        mae_mean, mae_std = -cv_results["test_mae"].mean(), cv_results["test_mae"].std()
        rmse_mean, rmse_std = -cv_results["test_rmse"].mean(), cv_results["test_rmse"].std()
        r2_mean, r2_std = cv_results["test_r2"].mean(), cv_results["test_r2"].std()

        results[name] = {"mae": mae_mean, "rmse": rmse_mean, "r2": r2_mean}
        print(f"{name:<20} {mae_mean:>8.2f} ± {mae_std:<9.2f} {rmse_mean:>8.2f} ± {rmse_std:<9.2f} "
              f"{r2_mean:>7.4f} ± {r2_std:<9.4f}")

    print("\nRaw cross-validation results saved for the report in Phase 6.")
    return results


if __name__ == "__main__":
    main()
