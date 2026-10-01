from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
import logging
import os
import secrets
import shutil
import tempfile

from backend.data_understanding import understand_dataset
from backend.analytics import calculate_analytics
from backend.ml_service import get_ml_predictions, get_ml_predictions_for_dataset
from backend.dashboard_config import build_dashboard_config
from backend.documents.api import (
    router as documents_router,
    DocumentQuestion,
    ask_document_question,
)
from backend.auth import router as auth_router
from backend.copilot_router import classify_question
from backend.sql_analytics import run_sql_question, get_database_analytics
from backend.nexa_priority_service import get_equipment_priority

from starlette.concurrency import run_in_threadpool


logger = logging.getLogger(__name__)

app = FastAPI(
    title="MedaNexa - Hospital Intelligence Platform",
    version="1.0",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_FOLDER = PROJECT_ROOT / "app"
TEMP_FOLDER = PROJECT_ROOT / "temp"

TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

MAX_DATASET_BYTES = 25 * 1024 * 1024

WORKSPACE_ANALYSES = {}


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)


# ============================================================
# AUTHENTICATION / PROTECTED ROUTES
# ============================================================

PUBLIC_PATHS = {
    "/",
    "/home.html",
    "/login.html",
    "/register.html",
    "/style.css",
    "/auth.js",
    "/favicon.ico",
}

PROTECTED_API_PREFIXES = (
    "/documents",
    "/analyze-dataset",
    "/ml-predictions",
    "/workspace",
    "/copilot",
    "/nexa-priority",
)

WORKSPACE_PAGES = {
    "/index.html",
    "/analytics.html",
    "/predict.html",
    "/documents.html",
    "/copilot.html",
    "/command.html",
}


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    path = request.url.path

    # Public pages and authentication routes
    if path in PUBLIC_PATHS or path.startswith("/auth/"):
        return await call_next(request)

    # Static files
    if path.endswith(
        (
            ".css",
            ".js",
            ".ico",
            ".png",
            ".svg",
            ".woff",
            ".woff2",
        )
    ):
        return await call_next(request)

    authenticated = bool(request.session.get("user_id"))

    # Workspace pages require login
    if path in WORKSPACE_PAGES and not authenticated:
        return RedirectResponse(
            url="/home.html",
            status_code=302,
        )

    # Other HTML pages require login
    if (
        path.endswith(".html")
        and path not in {
            "/home.html",
            "/login.html",
            "/register.html",
        }
        and not authenticated
    ):
        return RedirectResponse(
            url="/home.html",
            status_code=302,
        )

    # Protected APIs require login
    if path.startswith(PROTECTED_API_PREFIXES) and not authenticated:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "detail": "Authentication required.",
            },
        )

    response = await call_next(request)

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "same-origin",
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "SAMEORIGIN",
    )

    return response


# ============================================================
# SESSION CONFIGURATION
# ============================================================

# A random development key keeps local sessions functional
# without a hardcoded secret.
#
# Set SESSION_SECRET_KEY to a stable private value before deployment.

SESSION_SECRET_KEY = (
    os.getenv("SESSION_SECRET_KEY")
    or secrets.token_urlsafe(48)
)

SESSION_HTTPS_ONLY = (
    os.getenv("SESSION_HTTPS_ONLY", "false").lower()
    in {"1", "true", "yes"}
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=SESSION_HTTPS_ONLY,
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home(request: Request):
    page = (
        "index.html"
        if request.session.get("user_id")
        else "home.html"
    )

    return FileResponse(APP_FOLDER / page)


# ============================================================
# WORKSPACE
# ============================================================

@app.get("/index.html")
async def workspace(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(
            url="/home.html",
            status_code=302,
        )

    return FileResponse(APP_FOLDER / "index.html")


# ============================================================
# DATASET ANALYSIS
# ============================================================

@app.post("/analyze-dataset")
async def analyze_dataset(
    request: Request,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    temp_file = None

    try:
        # Check file size
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_DATASET_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Dataset exceeds the 25 MB upload limit.",
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
            dir=TEMP_FOLDER,
        ) as temp:

            temp_file = Path(temp.name)

            shutil.copyfileobj(
                file.file,
                temp,
            )

        # Understand dataset
        understanding = understand_dataset(
            str(temp_file)
        )

        # Calculate analytics
        analytics = calculate_analytics(
            str(temp_file)
        )

        file_name = Path(file.filename).name

        understanding["file_name"] = file_name

        # ML predictions
        predictions = get_ml_predictions_for_dataset(
            str(temp_file),
            understanding.get(
                "available_modules",
                [],
            ),
        )

        # Dynamic dashboard
        dashboard = build_dashboard_config(
            str(temp_file),
            understanding,
            analytics,
            predictions,
        )

        result = {
            "status": "success",
            "file_name": file_name,
            "understanding": understanding,
            "analytics": analytics,
            "predictions": predictions,
            "dashboard": dashboard,
        }

        # Store analysis for logged-in user
        user_id = request.session.get("user_id")

        if user_id is not None:
            WORKSPACE_ANALYSES[str(user_id)] = result

        return result

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Dataset analysis failed"
        )

        raise HTTPException(
            status_code=422,
            detail=(
                "Dataset analysis failed. "
                "Check that the file is a valid, "
                "readable CSV or XLSX dataset."
            ),
        )

    finally:
        if temp_file and temp_file.exists():
            temp_file.unlink(
                missing_ok=True
            )

        await file.close()


# ============================================================
# ML PREDICTIONS
# ============================================================

@app.get("/ml-predictions")
async def ml_predictions(request: Request):

    try:
        user_id = str(
            request.session.get("user_id")
        )

        analysis = WORKSPACE_ANALYSES.get(
            user_id
        )

        predictions = (
            analysis.get("predictions")
            if analysis
            else get_ml_predictions()
        )

        safe_predictions = {}

        for name, value in predictions.items():

            if (
                isinstance(value, dict)
                and (
                    value.get("error")
                    or value.get("status")
                    in {
                        "model_not_found",
                        "prediction_error",
                    }
                )
            ):

                message = (
                    value.get("message")
                    if value.get("status")
                    != "prediction_error"
                    else None
                )

                safe_predictions[name] = {
                    "status": "unavailable",
                    "message": (
                        message
                        or
                        "No compatible trained model "
                        "and source data are installed."
                    ),
                }

            else:
                safe_predictions[name] = value

        return {
            "status": "success",
            "predictions": safe_predictions,
            "source": (
                analysis.get("file_name")
                if analysis
                else None
            ),
        }

    except Exception:
        logger.exception(
            "ML prediction service failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Prediction service is "
                "temporarily unavailable."
            ),
        )


# ============================================================
# NEXA PRIORITY
# ============================================================

@app.get("/nexa-priority")
async def nexa_priority(
    request: Request,
    top_n: int = 20,
):

    if top_n < 1 or top_n > 100:
        raise HTTPException(
            status_code=400,
            detail="top_n must be between 1 and 100.",
        )

    try:

        result = await run_in_threadpool(
            get_equipment_priority,
            top_n,
        )

        return result

    except Exception:
        logger.exception(
            "NexaPriority service failed"
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "NexaPriority service is "
                "temporarily unavailable."
            ),
        )


# ============================================================
# WORKSPACE CONTEXT
# ============================================================

@app.get("/workspace/context")
async def workspace_context(
    request: Request,
):

    user_id = str(
        request.session.get("user_id")
    )

    analysis = WORKSPACE_ANALYSES.get(
        user_id
    )

    if analysis:

        predictions = (
            analysis.get("predictions")
            or {}
        )

        dashboard = (
            analysis.get("dashboard")
            or {}
        )

    else:

        try:

            predictions = (
                await ml_predictions(request)
            ).get(
                "predictions",
                {},
            )

        except HTTPException:

            predictions = {}

        dashboard = None

    return {
        "status": "success",
        "analysis": analysis,
        "dashboard": dashboard,
        "predictions": predictions,
        "database_analytics": (
            await run_in_threadpool(
                get_database_analytics
            )
        ),
    }


# ============================================================
# COPILOT QUESTION MODEL
# ============================================================

class CopilotQuestion(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1000,
    )


# ============================================================
# COPILOT
# ============================================================

@app.post("/copilot/ask")
async def copilot_ask(
    request: Request,
    payload: CopilotQuestion,
):

    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Enter a question.",
        )

    route = await run_in_threadpool(
        classify_question,
        question,
    )

    # --------------------------------------------------------
    # SQL
    # --------------------------------------------------------

    if route.intent == "sql":

        response = await run_in_threadpool(
            run_sql_question,
            route.model or "",
            route.department,
        )

        response["route"] = "sql"
        response["intent_confidence"] = (
            route.confidence
        )

        return response

    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    if route.intent == "ml":

        predictions = (
            await ml_predictions(request)
        ).get(
            "predictions",
            {},
        )

        prediction = predictions.get(
            route.model or ""
        )

        (
            answer,
            sources,
            available,
        ) = _prediction_copilot_answer(
            route.model or "",
            prediction,
        )

        return {
            "status": (
                "success"
                if available
                else "unavailable"
            ),
            "route": "ml",
            "intent_confidence": (
                route.confidence
            ),
            "answer": answer,
            "sources": sources,
        }

    # --------------------------------------------------------
    # RAG / DOCUMENT
    # --------------------------------------------------------

    if route.intent == "rag":

        try:

            answer = await run_in_threadpool(
                ask_document_question,
                DocumentQuestion(
                    question=question
                ),
                request,
            )

            answer["route"] = "rag"

            answer["intent_confidence"] = (
                route.confidence
            )

            return answer

        except HTTPException as error:

            if error.status_code == 404:

                return {
                    "status": "no_source",
                    "route": "rag",
                    "intent_confidence": (
                        route.confidence
                    ),
                    "answer": (
                        "No matching uploaded "
                        "hospital document was found. "
                        "Upload or select a PDF/DOCX "
                        "report in NexaDocs and ask again."
                    ),
                    "sources": [],
                }

            raise

    # --------------------------------------------------------
    # CLARIFICATION
    # --------------------------------------------------------

    if route.intent == "clarify":

        return {
            "status": "clarification_needed",
            "route": "clarify",
            "intent_confidence": (
                route.confidence
            ),
            "answer": (
                "I couldn’t confidently identify "
                "a source for that question. "
                "Ask about a hospital metric, "
                "a real model prediction, or an "
                "uploaded report; you can name "
                "the dataset when asking about "
                "uploaded analytics."
            ),
            "sources": [],
        }

    # --------------------------------------------------------
    # DATASET ANALYTICS
    # --------------------------------------------------------

    analysis = WORKSPACE_ANALYSES.get(
        str(request.session.get("user_id"))
    )

    if not analysis:

        raise HTTPException(
            status_code=409,
            detail=(
                "Analyze a hospital dataset in "
                "Pulse first to ask questions "
                "about uploaded analytics."
            ),
        )

    analytics = (
        analysis.get("analytics")
        or {}
    )

    kpis = (
        analytics.get("kpis")
        or []
    )

    tables = (
        analytics.get("tables")
        or []
    )

    tokens = {
        word.lower().strip(
            ".,?!:;()"
        )
        for word in question.split()
        if len(word) > 2
    }

    matches = []

    # --------------------------------------------------------
    # KPI MATCHING
    # --------------------------------------------------------

    for kpi in kpis:

        if not isinstance(kpi, dict):
            continue

        label = str(
            kpi.get("label")
            or kpi.get("name")
            or kpi.get("title")
            or "Metric"
        )

        value = kpi.get(
            "value",
            kpi.get(
                "metric",
                "—",
            ),
        )

        label_tokens = {
            word.lower().strip(
                ".,?!:;()"
            )
            for word in label
            .replace("_", " ")
            .split()
        }

        if tokens & label_tokens:

            matches.append(
                f"{label}: {value}"
            )

    # --------------------------------------------------------
    # TABLE ANALYTICS
    # --------------------------------------------------------

    for table in tables:

        if not isinstance(table, dict):
            continue

        title = str(
            table.get("title")
            or table.get("name")
            or "Analysis"
        )

        columns = (
            table.get("columns")
            or table.get("headers")
            or []
        )

        rows = (
            table.get("rows")
            or table.get("data")
            or []
        )

        # Highest admissions
        if (
            {"highest", "most", "largest", "maximum"}
            & tokens
            and
            {"admission", "admissions"}
            & tokens
        ):

            normalized_columns = {
                str(column)
                .strip()
                .lower()
                .replace("_", " "): column
                for column in columns
            }

            department_column = next(
                (
                    normalized_columns[name]
                    for name in (
                        "department id",
                        "department name",
                        "department",
                    )
                    if name in normalized_columns
                ),
                None,
            )

            admissions_column = next(
                (
                    normalized_columns[name]
                    for name in (
                        "admissions",
                        "total admissions",
                        "admission count",
                    )
                    if name in normalized_columns
                ),
                None,
            )

            candidates = []

            if (
                department_column
                and admissions_column
            ):

                for row in rows:

                    if isinstance(row, dict):

                        department = row.get(
                            department_column
                        )

                        value = row.get(
                            admissions_column
                        )

                    elif isinstance(row, list):

                        department_index = (
                            columns.index(
                                department_column
                            )
                            if department_column
                            in columns
                            else -1
                        )

                        admissions_index = (
                            columns.index(
                                admissions_column
                            )
                            if admissions_column
                            in columns
                            else -1
                        )

                        department = (
                            row[department_index]
                            if (
                                department_index >= 0
                                and department_index
                                < len(row)
                            )
                            else None
                        )

                        value = (
                            row[admissions_index]
                            if (
                                admissions_index >= 0
                                and admissions_index
                                < len(row)
                            )
                            else None
                        )

                    else:
                        continue

                    try:

                        candidates.append(
                            (
                                float(
                                    str(value)
                                    .replace(",", "")
                                ),
                                department,
                            )
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):
                        continue

            if candidates:

                highest_value, highest_department = max(
                    candidates,
                    key=lambda item: item[0],
                )

                formatted_value = (
                    int(highest_value)
                    if highest_value.is_integer()
                    else highest_value
                )

                direct_answer = (
                    "Department with the highest "
                    "admissions in the analyzed "
                    f"dataset: {highest_department} "
                    f"({formatted_value})."
                )

                if direct_answer not in matches:
                    matches.append(
                        direct_answer
                    )

        # General table matching
        searchable = (
            title
            + " "
            + " ".join(
                map(str, columns)
            )
        ).lower().replace(
            "_",
            " ",
        )

        searchable_tokens = {
            word.strip(
                ".,?!:;()"
            )
            for word in searchable.split()
        }

        if tokens & searchable_tokens:

            matches.append(
                f"{title}: "
                f"{len(rows)} result row(s) "
                "are available in NexaSight."
            )

            for row in rows[:3]:

                if isinstance(row, list):

                    matches.append(
                        " · "
                        + ", ".join(
                            f"{columns[i] if i < len(columns) else 'Value'}: {v}"
                            for i, v in enumerate(row)
                        )
                    )

                elif isinstance(row, dict):

                    matches.append(
                        " · "
                        + ", ".join(
                            f"{key}: {value}"
                            for key, value in row.items()
                        )
                    )

                else:

                    matches.append(
                        " · "
                        + str(row)
                    )

    # --------------------------------------------------------
    # PREDICTION INFORMATION
    # --------------------------------------------------------

    predictions = (
        await ml_predictions(request)
    ).get(
        "predictions",
        {},
    )

    if any(
        token in question.lower()
        for token in (
            "admission",
            "admissions",
            "capacity",
            "bed",
            "beds",
            "equipment",
            "failure",
            "forecast",
            "risk",
        )
    ):

        admission = predictions.get(
            "admission_forecast",
            {},
        )

        if (
            isinstance(admission, dict)
            and admission.get(
                "predicted_admissions"
            ) is not None
        ):

            matches.append(
                "Admission demand forecast "
                f"for {admission.get('forecast_month', 'the next period')}: "
                f"{admission['predicted_admissions']}."
            )

        beds = predictions.get(
            "bed_forecast",
            {},
        )

        if (
            isinstance(beds, dict)
            and beds.get(
                "average_predicted_occupied_beds"
            ) is not None
        ):

            matches.append(
                "Bed demand forecast: "
                f"{beds['average_predicted_occupied_beds']} "
                "average occupied beds over "
                f"{beds.get('forecast_days', 'the forecast')} days."
            )

        equipment = predictions.get(
            "equipment_failure",
            {},
        )

        if (
            isinstance(equipment, dict)
            and equipment.get("status")
            == "success"
            and equipment.get("risk")
        ):

            matches.append(
                "Equipment failure model signal: "
                f"{equipment['risk']}."
            )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not matches:

        matches = [
            (
                f"{kpi.get('label') or kpi.get('name') or 'Metric'}: "
                f"{kpi.get('value', kpi.get('metric', '—'))}"
            )
            for kpi in kpis[:6]
            if isinstance(kpi, dict)
        ]

    if not matches:

        return {
            "status": "success",
            "answer": (
                "The analyzed dataset does not "
                "contain a matching operational "
                "metric for that question."
            ),
            "sources": [],
        }

    answer = (
        "Based on the analyzed dataset:\n"
        + "\n".join(matches[:10])
    )

    return {
        "status": "success",
        "route": "dataset",
        "intent_confidence": (
            route.confidence
        ),
        "answer": answer,
        "sources": [
            {
                "file_name": analysis.get(
                    "file_name"
                ),
                "type": "dataset analytics",
            }
        ],
    }


# ============================================================
# COPILOT PREDICTION ANSWER
# ============================================================

def _prediction_copilot_answer(
    model_name,
    prediction,
):

    if not isinstance(prediction, dict):

        return (
            "Prediction unavailable. "
            "No compatible trained model "
            "result is available for this workspace.",
            [],
            False,
        )

    status = prediction.get(
        "status"
    )

    if (
        status
        in {
            "unavailable",
            "model_not_found",
            "prediction_error",
        }
        or prediction.get("error")
    ):

        reason = (
            prediction.get("message")
            or
            "No compatible trained model "
            "and source data are installed."
        )

        return (
            f"Prediction unavailable. {reason}",
            [],
            False,
        )

    period = None

    # Bed forecast
    if (
        model_name == "bed_forecast"
        and prediction.get(
            "average_predicted_occupied_beds"
        ) is not None
    ):

        value = prediction[
            "average_predicted_occupied_beds"
        ]

        horizon = prediction.get(
            "forecast_days"
        )

        period = (
            f"{horizon}-day forecast"
            if horizon
            else
            "Forecast period returned by the model"
        )

        answer = (
            f"Predicted average occupied beds: "
            f"{value}"
            + (
                f" over {period}."
                if horizon
                else "."
            )
        )

    # Length of stay
    elif (
        model_name == "length_of_stay"
        and prediction.get(
            "predicted_length_of_stay",
            prediction.get("prediction"),
        ) is not None
    ):

        value = prediction.get(
            "predicted_length_of_stay",
            prediction.get("prediction"),
        )

        period = (
            prediction.get(
                "prediction_period"
            )
            or
            "Prediction period returned by the model"
        )

        answer = (
            f"Predicted length of stay: "
            f"{value} days."
        )

    # Equipment failure
    elif (
        model_name == "equipment_failure"
        and prediction.get("risk")
    ):

        value = prediction["risk"]

        answer = (
            "Equipment failure model "
            f"risk signal: {value}."
        )

    # Appointment no-show
    elif (
        model_name == "appointment_no_show"
        and prediction.get("status")
        == "success"
    ):

        value = prediction.get(
            "predicted_no_show_probability",
            prediction.get(
                "no_show_probability",
                prediction.get("risk"),
            ),
        )

        if value is None:

            return (
                "Prediction unavailable. "
                "The trained model did not "
                "return a no-show result.",
                [],
                False,
            )

        period = (
            prediction.get(
                "prediction_period"
            )
            or
            "Prediction period returned by the model"
        )

        answer = (
            "Predicted appointment "
            f"no-show result: {value}."
        )

    # Admission forecast
    elif (
        model_name == "admission_forecast"
        and prediction.get(
            "predicted_admissions"
        ) is not None
    ):

        value = prediction[
            "predicted_admissions"
        ]

        period = (
            prediction.get(
                "forecast_month"
            )
            or
            "Forecast period returned by the model"
        )

        answer = (
            f"Predicted admissions: "
            f"{value} for {period}."
        )

    else:

        return (
            "Prediction unavailable. "
            "The configured model did not "
            "return a compatible result.",
            [],
            False,
        )

    sources = [
        {
            "type": "Trained prediction model",
            "model": model_name,
        }
    ]

    if period:
        sources[0]["period"] = period

    return (
        answer,
        sources,
        True,
    )


# ============================================================
# DOCUMENT ROUTER
# ============================================================

app.include_router(
    documents_router
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=APP_FOLDER,
        html=True,
    ),
    name="frontend",
)