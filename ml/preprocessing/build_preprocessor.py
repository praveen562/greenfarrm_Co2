"""
Phase 4, step 2: build and fit the preprocessing pipeline.

Fit ONLY on train.csv (never on test or on inference-time data) to avoid
leakage. The fitted ColumnTransformer is saved via joblib and MUST be the
exact object loaded again at inference time (Phase 8) — never re-fit a new
encoder/scaler on request data, or train/inference preprocessing would
silently diverge.

Encoding choice: OneHotEncoder for crop_type (handle_unknown="ignore" so an
unseen crop at inference time doesn't crash the API — it just contributes
an all-zero encoding rather than raising). StandardScaler for the 4 numeric
inputs — required for Linear Regression to behave sensibly, harmless for
Random Forest / XGBoost (tree splits are scale-invariant).
"""
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TRAIN_PATH = "../datasets/train.csv"
PREPROCESSOR_PATH = "../models/preprocessor.joblib"

NUMERIC_FEATURES = [
    "fertilizer_usage_kg_per_ha",
    "fuel_consumption_liters_per_ha",
    "water_consumption_m3_per_ha",
    "electricity_consumption_kwh_per_ha",
]
CATEGORICAL_FEATURES = ["crop_type"]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES  # model input order


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ]
    )


def main():
    train_df = pd.read_csv(TRAIN_PATH)
    X_train = train_df[ALL_FEATURES]

    preprocessor = build_preprocessor()
    preprocessor.fit(X_train)

    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Fitted preprocessor saved -> {PREPROCESSOR_PATH}")

    transformed = preprocessor.transform(X_train)
    feature_names = preprocessor.get_feature_names_out()
    print(f"\nInput shape:  {X_train.shape}")
    print(f"Output shape: {transformed.shape}")
    print(f"Output feature names ({len(feature_names)}): {list(feature_names)}")


if __name__ == "__main__":
    main()
