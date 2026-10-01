import joblib
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FOLDER = PROJECT_ROOT / "ml" / "models"
DATA_FOLDER = PROJECT_ROOT / "data" / "processed"

MODEL_UNAVAILABLE_REASONS = {
    "length_of_stay": (
        "No trained length-of-stay artifact is installed. The only admissions file has 20 test rows and lacks features used by the notebook model (age, gender, and bed type), so it is insufficient for legitimate training and validation."
    ),
    "bed_forecast": (
        "No trained bed-demand artifact or processed bed history is installed."
    ),
    "appointment_no_show": (
        "No trained appointment no-show artifact or labeled appointment training cohort is installed."
    ),
    "equipment_failure": (
        "No trained equipment-failure artifact or labeled equipment source data is installed."
    ),
}


def _unavailable(message):
    return {"status": "unavailable", "message": message}


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

    result = {
        "length_of_stay": _unavailable(MODEL_UNAVAILABLE_REASONS["length_of_stay"]),
        "appointment_no_show": _unavailable(MODEL_UNAVAILABLE_REASONS["appointment_no_show"]),
    }

    # --------------------------------------------------------
    # Admission Forecast
    # --------------------------------------------------------

    try:

        result["admission_forecast"] = (
            admission_forecast()
        )

    except Exception:
        result["admission_forecast"] = _unavailable(
            "No compatible trained admission-demand model and processed admission history are installed."
        )

    # --------------------------------------------------------
    # Bed Forecast
    # --------------------------------------------------------

    try:

        result["bed_forecast"] = (
            bed_forecast()
        )

    except Exception:
        result["bed_forecast"] = _unavailable(MODEL_UNAVAILABLE_REASONS["bed_forecast"])

    # --------------------------------------------------------
    # Equipment Failure
    # --------------------------------------------------------

    try:

        result["equipment_failure"] = (
            equipment_failure_risk()
        )

    except Exception:
        result["equipment_failure"] = _unavailable(MODEL_UNAVAILABLE_REASONS["equipment_failure"])

    return result

def get_ml_predictions_for_dataset(file_path, available_modules):
    # Run configured estimators against the current uploaded dataset only.
    from backend.analytics import resolve_column
    from backend.data_understanding import load_dataset

    modules = set(available_modules or [])
    frame = load_dataset(file_path)
    result = {
        "length_of_stay": _unavailable(MODEL_UNAVAILABLE_REASONS["length_of_stay"]),
        "admission_forecast": _unavailable(
            "The current upload does not contain an admissions module or no compatible trained model is installed."
        ),
        "bed_forecast": _unavailable(
            "The current upload does not contain bed-capacity data or no compatible trained model is installed."
        ),
        "appointment_no_show": _unavailable(
            "The current upload does not contain labeled appointment data or no compatible trained model is installed."
        ),
        "equipment_failure": _unavailable(
            "The current upload does not contain equipment data or no compatible trained model is installed."
        ),
    }

    unavailable = _unavailable

    if "Admission Analytics" in modules:
        result["length_of_stay"] = _unavailable(MODEL_UNAVAILABLE_REASONS["length_of_stay"])
        model_path = MODEL_FOLDER / "admission_demand_forecasting_model.pkl"
        date_column = next((name for name in ("admission_date", "admit_date", "admitted_at", "date_of_admission") if name in frame.columns), None)
        try:
            if not model_path.exists():
                raise FileNotFoundError
            if not date_column:
                result["admission_forecast"] = unavailable("This upload has no admission date column.")
            else:
                model = joblib.load(model_path)
                dates = pd.to_datetime(frame[date_column], errors="coerce")
                monthly = pd.DataFrame({"date": dates}).dropna().set_index("date").resample("MS").size().rename("admissions").reset_index()
                if len(monthly) < 3:
                    result["admission_forecast"] = unavailable("At least three monthly observations are needed by the configured model.")
                else:
                    monthly["time_index"] = range(len(monthly))
                    monthly["year"] = monthly["date"].dt.year
                    monthly["month"] = monthly["date"].dt.month
                    monthly["lag_1"] = monthly["admissions"].shift(1)
                    monthly["lag_2"] = monthly["admissions"].shift(2)
                    monthly["lag_3"] = monthly["admissions"].shift(3)
                    next_date = monthly["date"].max() + pd.DateOffset(months=1)
                    row = pd.DataFrame({"time_index": [int(monthly["time_index"].max() + 1)], "year": [next_date.year], "month": [next_date.month], "lag_1": [float(monthly["admissions"].iloc[-1])], "lag_2": [float(monthly["admissions"].iloc[-2])], "lag_3": [float(monthly["admissions"].iloc[-3])]})
                    features = list(getattr(model, "feature_names_in_", row.columns))
                    if not set(features).issubset(row.columns):
                        result["admission_forecast"] = unavailable("The configured model features do not match the available admission history.")
                    else:
                        prediction = round(float(model.predict(row.reindex(columns=features))[0]), 2)
                        history = [{"date": item["date"].strftime("%Y-%m"), "admissions": int(item["admissions"])} for item in monthly.tail(12).to_dict(orient="records")]
                        result["admission_forecast"] = {"status": "success", "forecast_month": next_date.strftime("%Y-%m"), "predicted_admissions": prediction, "history": history, "predictions": [{"date": next_date.strftime("%Y-%m-01"), "predicted_admissions": prediction}]}
        except FileNotFoundError:
            result["admission_forecast"] = unavailable("No compatible trained admission model is installed.")
        except Exception:
            result["admission_forecast"] = unavailable("The configured admission model could not use this upload.")

    if "Bed & Capacity Analytics" in modules:
        result["bed_forecast"] = _unavailable(MODEL_UNAVAILABLE_REASONS["bed_forecast"])
        model_path = MODEL_FOLDER / "bed_demand_forecasting_model.pkl"
        date_column = next((name for name in ("record_date", "bed_date", "date", "observation_date") if name in frame.columns), None)
        occupied_column = resolve_column(frame.columns, "occupied_beds")
        try:
            if not model_path.exists():
                raise FileNotFoundError
            if not date_column or not occupied_column:
                result["bed_forecast"] = unavailable("This upload needs a date field and occupied-bed metric.")
            else:
                model = joblib.load(model_path)
                dates = pd.to_datetime(frame[date_column], errors="coerce")
                occupied = pd.to_numeric(frame[occupied_column], errors="coerce")
                daily_source = pd.DataFrame({"date": dates, "occupied": occupied}).dropna()
                daily = daily_source.groupby("date", as_index=False)["occupied"].sum().sort_values("date").reset_index(drop=True)
                if len(daily) < 31:
                    result["bed_forecast"] = unavailable("At least 31 dated occupied-bed observations are needed by the configured model.")
                else:
                    history_values = daily["occupied"].astype(float).tolist()
                    predictions = []
                    history_dates = daily["date"].tolist()
                    for offset in range(7):
                        next_date = history_dates[-1] + pd.Timedelta(days=1)
                        next_row = pd.DataFrame({"time_index": [len(history_values)], "dayofweek": [next_date.dayofweek], "month": [next_date.month], "dayofyear": [next_date.dayofyear], "lag_1": [history_values[-1]], "lag_7": [history_values[-7]], "lag_30": [history_values[-30]]})
                        features = list(getattr(model, "feature_names_in_", next_row.columns))
                        if not set(features).issubset(next_row.columns):
                            raise ValueError("Configured bed model features do not match.")
                        predicted = max(0, round(float(model.predict(next_row.reindex(columns=features))[0]), 2))
                        predictions.append({"date": next_date.strftime("%Y-%m-%d"), "predicted_occupied_beds": predicted})
                        history_dates.append(next_date)
                        history_values.append(predicted)
                    historical = [{"date": date.strftime("%Y-%m-%d"), "occupied_beds": round(value, 2)} for date, value in zip(daily["date"].tail(30), daily["occupied"].tail(30))]
                    result["bed_forecast"] = {"status": "success", "forecast_days": len(predictions), "average_predicted_occupied_beds": round(sum(row["predicted_occupied_beds"] for row in predictions) / len(predictions), 2), "history": historical, "predictions": predictions}
        except FileNotFoundError:
            result["bed_forecast"] = unavailable("No compatible trained bed-demand model is installed.")
        except Exception:
            result["bed_forecast"] = unavailable("The configured bed-demand model could not use this upload.")

    if "Equipment Analytics" in modules:
        result["equipment_failure"] = _unavailable(MODEL_UNAVAILABLE_REASONS["equipment_failure"])
        model_path = MODEL_FOLDER / "equipment_failure_model.pkl"
        try:
            if not model_path.exists():
                raise FileNotFoundError
            model = joblib.load(model_path)
            required_roles = {
                "department_id": next((c for c in frame.columns if c in {"department_id", "department", "dept_id"}), None),
                "equipment_type": resolve_column(frame.columns, "equipment_type"),
                "usage_hours": resolve_column(frame.columns, "usage_hours"),
                "maintenance_count": resolve_column(frame.columns, "maintenance_count"),
            }
            installation = next((c for c in frame.columns if c in {"installation_date", "installed_date"}), None)
            next_maintenance = next((c for c in frame.columns if c in {"next_maintenance_date", "maintenance_due_date"}), None)
            if not all(required_roles.values()) or not installation or not next_maintenance:
                result["equipment_failure"] = unavailable("This upload does not contain all features required by the configured equipment model.")
            else:
                reference_date = pd.Timestamp.today().normalize()
                features = pd.DataFrame(index=frame.index)
                features["department_id"] = frame[required_roles["department_id"]]
                features["equipment_type"] = frame[required_roles["equipment_type"]]
                features["equipment_age_days"] = (reference_date - pd.to_datetime(frame[installation], errors="coerce")).dt.days
                features["days_until_next_maintenance"] = (pd.to_datetime(frame[next_maintenance], errors="coerce") - reference_date).dt.days
                features["usage_hours"] = pd.to_numeric(frame[required_roles["usage_hours"]], errors="coerce")
                features["maintenance_count"] = pd.to_numeric(frame[required_roles["maintenance_count"]], errors="coerce")
                expected = list(getattr(model, "feature_names_in_", features.columns))
                if not set(expected).issubset(features.columns):
                    result["equipment_failure"] = unavailable("The configured equipment model features do not match this upload.")
                else:
                    usable = features[expected].dropna()
                    if usable.empty:
                        result["equipment_failure"] = unavailable("No complete equipment records are available for prediction.")
                    else:
                        predictions = model.predict(usable.head(100))
                        flagged = int(sum(int(value) == 1 for value in predictions))
                        result["equipment_failure"] = {"status": "success", "risk": f"{flagged} of {len(predictions)} equipment records flagged high risk", "predicted_high_risk": flagged, "records_scored": len(predictions)}
        except FileNotFoundError:
            result["equipment_failure"] = unavailable("No compatible trained equipment model is installed.")
        except Exception:
            result["equipment_failure"] = unavailable("The configured equipment model could not use this upload.")

    if "Appointment Analytics" in modules:
        result["appointment_no_show"] = _unavailable(
            MODEL_UNAVAILABLE_REASONS["appointment_no_show"]
        )

    return result
