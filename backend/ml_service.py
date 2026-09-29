import joblib
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FOLDER = PROJECT_ROOT / "ml" / "models"
DATA_FOLDER = PROJECT_ROOT / "data" / "processed"


# ============================================================
# MODEL LOADER
# ============================================================

def load_model(model_name):
    model_path = MODEL_FOLDER / model_name

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )

    return joblib.load(model_path)


# ============================================================
# ADMISSION DEMAND FORECAST
# ============================================================

def admission_forecast():

    model = load_model(
        "admission_demand_forecasting_model.pkl"
    )

    file_path = DATA_FOLDER / "admissions" / "admissions_clean.csv"

    df = pd.read_csv(file_path)

    # Convert date
    df["admission_date"] = pd.to_datetime(
        df["admission_date"]
    )

    # Monthly admissions
    monthly = (
        df.set_index("admission_date")
        .resample("MS")
        .size()
        .reset_index(name="admissions")
    )

    monthly["time_index"] = range(len(monthly))

    monthly["year"] = monthly["admission_date"].dt.year
    monthly["month"] = monthly["admission_date"].dt.month

    # Lag features
    monthly["lag_1"] = monthly["admissions"].shift(1)
    monthly["lag_2"] = monthly["admissions"].shift(2)
    monthly["lag_3"] = monthly["admissions"].shift(3)

    monthly = monthly.dropna().reset_index(drop=True)

    # --------------------------------------------------------
    # Next month
    # --------------------------------------------------------

    next_date = (
        monthly["admission_date"].max()
        + pd.DateOffset(months=1)
    )

    next_row = pd.DataFrame({
        "time_index": [
            monthly["time_index"].max() + 1
        ],
        "year": [
            next_date.year
        ],
        "month": [
            next_date.month
        ],
        "lag_1": [
            monthly["admissions"].iloc[-1]
        ],
        "lag_2": [
            monthly["admissions"].iloc[-2]
        ],
        "lag_3": [
            monthly["admissions"].iloc[-3]
        ]
    })

    # --------------------------------------------------------
    # IMPORTANT:
    # Match the exact feature names AND exact order
    # used while training the model.
    # --------------------------------------------------------

    if hasattr(model, "feature_names_in_"):

        expected_features = list(
            model.feature_names_in_
        )

        next_row = next_row.reindex(
            columns=expected_features
        )

    prediction = model.predict(next_row)

    predicted_admissions = round(
        float(prediction[0]),
        2
    )

    return {
        "forecast_month": next_date.strftime("%Y-%m"),
        "predicted_admissions": predicted_admissions
    }


# ============================================================
# BED DEMAND FORECAST
# ============================================================

def bed_forecast():

    model = load_model(
        "bed_demand_forecasting_model.pkl"
    )

    file_path = DATA_FOLDER / "beds" / "beds_clean.csv"

    df = pd.read_csv(file_path)

    # Convert date
    df["record_date"] = pd.to_datetime(
        df["record_date"]
    )

    # Daily total occupied beds
    daily = (
        df.groupby("record_date")["occupied_beds"]
        .sum()
        .reset_index()
    )

    daily = daily.sort_values(
        "record_date"
    ).reset_index(drop=True)

    daily["time_index"] = range(len(daily))

    daily["dayofweek"] = (
        daily["record_date"].dt.dayofweek
    )

    daily["month"] = (
        daily["record_date"].dt.month
    )

    daily["dayofyear"] = (
        daily["record_date"].dt.dayofyear
    )

    # Lag features
    daily["lag_1"] = daily["occupied_beds"].shift(1)
    daily["lag_7"] = daily["occupied_beds"].shift(7)
    daily["lag_30"] = daily["occupied_beds"].shift(30)

    daily = daily.dropna().reset_index(drop=True)

    # --------------------------------------------------------
    # Recursive 7-day forecasting
    # --------------------------------------------------------

    history = daily[
        ["record_date", "occupied_beds"]
    ].copy()

    predictions = []

    for i in range(7):

        next_date = (
            history["record_date"].max()
            + pd.Timedelta(days=1)
        )

        time_index = (
            daily["time_index"].max()
            + i
            + 1
        )

        dayofweek = next_date.dayofweek
        month = next_date.month
        dayofyear = next_date.dayofyear

        lag_1 = history["occupied_beds"].iloc[-1]

        lag_7 = (
            history["occupied_beds"].iloc[-7]
            if len(history) >= 7
            else history["occupied_beds"].iloc[0]
        )

        lag_30 = (
            history["occupied_beds"].iloc[-30]
            if len(history) >= 30
            else history["occupied_beds"].iloc[0]
        )

        next_row = pd.DataFrame({
            "time_index": [time_index],
            "dayofweek": [dayofweek],
            "month": [month],
            "dayofyear": [dayofyear],
            "lag_1": [lag_1],
            "lag_7": [lag_7],
            "lag_30": [lag_30]
        })

        # Match training feature order
        if hasattr(model, "feature_names_in_"):

            expected_features = list(
                model.feature_names_in_
            )

            next_row = next_row.reindex(
                columns=expected_features
            )

        prediction = model.predict(next_row)

        predicted_beds = max(
            0,
            round(float(prediction[0]), 2)
        )

        predictions.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "predicted_occupied_beds": predicted_beds
        })

        # Add prediction to history
        history = pd.concat(
            [
                history,
                pd.DataFrame({
                    "record_date": [next_date],
                    "occupied_beds": [predicted_beds]
                })
            ],
            ignore_index=True
        )

    average_beds = round(
        sum(
            item["predicted_occupied_beds"]
            for item in predictions
        ) / len(predictions),
        2
    )

    return {
        "forecast_days": 7,
        "average_predicted_occupied_beds": average_beds,
        "predictions": predictions
    }


# ============================================================
# EQUIPMENT FAILURE RISK
# ============================================================

def equipment_failure_risk():

    model_path = (
        MODEL_FOLDER /
        "equipment_failure_model.pkl"
    )

    # Model currently missing
    if not model_path.exists():

        return {
            "status": "model_not_found",
            "message": (
                "Equipment failure model is not available."
            )
        }

    model = joblib.load(model_path)

    file_path = (
        DATA_FOLDER /
        "equipment" /
        "equipment_clean.csv"
    )

    df = pd.read_csv(file_path)

    # --------------------------------------------------------
    # Feature preparation
    # --------------------------------------------------------

    df["installation_date"] = pd.to_datetime(
        df["installation_date"]
    )

    df["next_maintenance_date"] = pd.to_datetime(
        df["next_maintenance_date"]
    )

    reference_date = pd.Timestamp.today()

    df["equipment_age_days"] = (
        reference_date -
        df["installation_date"]
    ).dt.days

    df["days_until_next_maintenance"] = (
        df["next_maintenance_date"] -
        reference_date
    ).dt.days

    # Fill missing values
    df["days_until_next_maintenance"] = (
        df["days_until_next_maintenance"]
        .fillna(0)
    )

    df["equipment_age_days"] = (
        df["equipment_age_days"]
        .fillna(
            df["equipment_age_days"].median()
        )
    )

    df["usage_hours"] = (
        df["usage_hours"]
        .fillna(df["usage_hours"].median())
    )

    df["maintenance_count"] = (
        df["maintenance_count"]
        .fillna(
            df["maintenance_count"].median()
        )
    )

    features = df[
        [
            "department_id",
            "equipment_type",
            "equipment_age_days",
            "days_until_next_maintenance",
            "usage_hours",
            "maintenance_count"
        ]
    ].copy()

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    try:

        if hasattr(model, "feature_names_in_"):

            expected_features = list(
                model.feature_names_in_
            )

            features = features.reindex(
                columns=expected_features
            )

        prediction = model.predict(
            features.head(1)
        )

        risk = (
            "High Risk"
            if int(prediction[0]) == 1
            else "Low Risk"
        )

        return {
            "status": "success",
            "risk": risk
        }

    except Exception as e:

        return {
            "status": "prediction_error",
            "message": str(e)
        }


# ============================================================
# MAIN ML SERVICE
# ============================================================

def get_ml_predictions():

    result = {}

    # --------------------------------------------------------
    # Admission Forecast
    # --------------------------------------------------------

    try:

        result["admission_forecast"] = (
            admission_forecast()
        )

    except Exception as e:

        result["admission_forecast"] = {
            "error": str(e)
        }

    # --------------------------------------------------------
    # Bed Forecast
    # --------------------------------------------------------

    try:

        result["bed_forecast"] = (
            bed_forecast()
        )

    except Exception as e:

        result["bed_forecast"] = {
            "error": str(e)
        }

    # --------------------------------------------------------
    # Equipment Failure
    # --------------------------------------------------------

    try:

        result["equipment_failure"] = (
            equipment_failure_risk()
        )

    except Exception as e:

        result["equipment_failure"] = {
            "error": str(e)
        }

    return result