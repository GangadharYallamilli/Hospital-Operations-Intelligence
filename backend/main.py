from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
import shutil
import tempfile

from backend.data_understanding import understand_dataset
from backend.analytics import calculate_analytics
from backend.ml_service import get_ml_predictions

app = FastAPI(
    title="Hospital Operations Intelligence API",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

APP_FOLDER = PROJECT_ROOT / "app"


@app.get("/")
def home():
    return FileResponse(APP_FOLDER / "index.html")


@app.post("/analyze-dataset")
async def analyze_dataset(
    file: UploadFile = File(...)
):

    allowed_extensions = {
        ".csv",
        ".xlsx"
    }

    original_filename = file.filename or ""

    file_extension = Path(
        original_filename
    ).suffix.lower()


    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel (.xlsx) files are supported."
        )


    temp_folder = Path(
        tempfile.mkdtemp(
            prefix="hospital_upload_"
        )
    )


    safe_filename = Path(
        original_filename
    ).name


    file_path = temp_folder / safe_filename


    try:

        # Save uploaded file
        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        # --------------------------------
        # Dataset Understanding
        # --------------------------------

        result = understand_dataset(
            str(file_path)
        )


        # --------------------------------
        # Dynamic Analytics
        # --------------------------------

        analytics = calculate_analytics(
            str(file_path)
        )


        return {

            "file_name": safe_filename,

            "status": "success",

            "analysis": result,

            "analytics": analytics

        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing dataset: {str(e)}"
        )


    finally:

        try:

            if file_path.exists():
                file_path.unlink()

            if temp_folder.exists():
                temp_folder.rmdir()

        except Exception:
            pass
# =========================================
# ML PREDICTIONS
# =========================================

@app.get("/ml-predictions")
def ml_predictions():

    try:

        result = get_ml_predictions()

        return {
            "status": "success",
            "predictions": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

app.mount(
    "/",
    StaticFiles(
        directory=APP_FOLDER,
        html=True
    ),
    name="frontend"
)