import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "equipment"
    / "equipment_clean.csv"
)

MODEL_FOLDER = (
    PROJECT_ROOT
    / "ml"
    / "models"
)

MODEL_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

MODEL_PATH = (
    MODEL_FOLDER
    / "equipment_failure_model.pkl"
)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_PATH)

print("Dataset loaded")
print("Rows:", len(df))


# ============================================================
# TARGET
# ============================================================

# Failure risk:
# 1 = equipment has recorded failure
# 0 = no recorded failure

df["failure_risk"] = (
    df["failure_count"] > 0
).astype(int)


# ============================================================
# FEATURE ENGINEERING
# ============================================================

df["installation_date"] = pd.to_datetime(
    df["installation_date"]
)

df["last_maintenance_date"] = pd.to_datetime(
    df["last_maintenance_date"]
)

df["next_maintenance_date"] = pd.to_datetime(
    df["next_maintenance_date"]
)

# Use the latest date in the dataset as reference
reference_date = df[
    "installation_date"
].max()

df["equipment_age_days"] = (
    reference_date
    - df["installation_date"]
).dt.days

df["days_until_next_maintenance"] = (
    df["next_maintenance_date"]
    - reference_date
).dt.days


# ============================================================
# SELECT FEATURES
# ============================================================

features = [
    "department_id",
    "equipment_type",
    "equipment_age_days",
    "days_until_next_maintenance",
    "usage_hours",
    "maintenance_count"
]

X = df[features].copy()

y = df["failure_risk"]


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

X["days_until_next_maintenance"] = (
    X["days_until_next_maintenance"]
    .fillna(0)
)

X["equipment_age_days"] = (
    X["equipment_age_days"]
    .fillna(
        X["equipment_age_days"].median()
    )
)

X["usage_hours"] = (
    X["usage_hours"]
    .fillna(
        X["usage_hours"].median()
    )
)

X["maintenance_count"] = (
    X["maintenance_count"]
    .fillna(
        X["maintenance_count"].median()
    )
)

X["department_id"] = (
    X["department_id"]
    .fillna("Unknown")
)

X["equipment_type"] = (
    X["equipment_type"]
    .fillna("Unknown")
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ============================================================
# CATEGORICAL + NUMERICAL FEATURES
# ============================================================

categorical_features = [
    "department_id",
    "equipment_type"
]

numerical_features = [
    "equipment_age_days",
    "days_until_next_maintenance",
    "usage_hours",
    "maintenance_count"
]


# ============================================================
# PREPROCESSING
# ============================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        ),
        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)


# ============================================================
# RANDOM FOREST
# ============================================================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced",
    max_depth=None
)


# ============================================================
# PIPELINE
# ============================================================

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining model...")

pipeline.fit(
    X_train,
    y_train
)


# ============================================================
# EVALUATION
# ============================================================

y_pred = pipeline.predict(
    X_test
)

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)


print("\n==============================")
print("EQUIPMENT FAILURE MODEL")
print("==============================")

print(
    f"Accuracy  : {accuracy:.4f}"
)

print(
    f"Precision : {precision:.4f}"
)

print(
    f"Recall    : {recall:.4f}"
)

print(
    f"F1 Score  : {f1:.4f}"
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    pipeline,
    MODEL_PATH
)

print("\nModel saved successfully:")
print(MODEL_PATH)