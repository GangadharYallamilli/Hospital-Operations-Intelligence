from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pathlib import Path
import logging
import shutil
import uuid

from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from backend.ai.dynamic_rag_pipeline import process_document

from backend.ai.semantic_search import (
    load_embeddings,
    search_documents
)

from backend.ai.rag_answer_generator import (
    create_rag_answer
)

from backend.data_understanding import understand_dataset
from backend.analytics import calculate_analytics


# =========================================================
# ROUTER
# =========================================================

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"

PROCESSED_DIR = BASE_DIR / "processed"


UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def user_storage_dirs(request: Request):
    """Return private document folders for the authenticated account."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        user_folder = str(int(user_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Authentication required.")

    upload_dir = UPLOAD_DIR / user_folder
    processed_dir = PROCESSED_DIR / user_folder
    upload_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir, processed_dir


# =========================================================
# REQUEST MODEL
# =========================================================

class DocumentQuestion(BaseModel):

    question: str

    document_name: str | None = None


# =========================================================
# UPLOAD DOCUMENT / DATASET
# =========================================================

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):

    # -----------------------------------------------------
    # Check filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )


    # -----------------------------------------------------
    # Get extension
    # -----------------------------------------------------

    extension = (
        Path(file.filename)
        .suffix
        .lower()
    )


    # -----------------------------------------------------
    # Supported formats
    # -----------------------------------------------------

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".csv",
        ".xlsx"
    }


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported document format. "
                "Please upload a PDF, DOCX, CSV, or XLSX file."
            )
        )


    # -----------------------------------------------------
    file.file.seek(0, 2)
    upload_size = file.file.tell()
    file.file.seek(0)
    if upload_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 25 MB upload limit.")
    # Generate document ID
    # -----------------------------------------------------

    document_id = str(
        uuid.uuid4()
    )

    upload_dir, processed_dir = user_storage_dirs(request)


    # -----------------------------------------------------
    # Keep original filename safe
    # -----------------------------------------------------

    safe_name = Path(
        file.filename
    ).name


    # -----------------------------------------------------
    # Store UUID with filename
    # -----------------------------------------------------

    stored_name = (
        f"{document_id}_{safe_name}"
    )


    file_path = (
        upload_dir /
        stored_name
    )


    try:

        # =================================================
        # SAVE UPLOADED FILE
        # =================================================

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        print(
            f"File uploaded: {safe_name}"
        )


        # =================================================
        # PDF / DOCX
        # =================================================

        if extension in {
            ".pdf",
            ".docx"
        }:

            print(
                "Processing as document using RAG..."
            )


            process_document(
                str(file_path),
                str(processed_dir)
            )


            # ---------------------------------------------
            # SUCCESS RESPONSE
            # ---------------------------------------------

            return {

                "status":
                    "success",

                "document_id":
                    document_id,

                "file_name":
                    safe_name,

                "file_type":
                    extension.replace(
                        ".",
                        ""
                    ),

                "processing_type":
                    "rag",

                "message":
                    "Document uploaded and processed successfully."
            }


        # =================================================
        # CSV / XLSX
        # =================================================

        elif extension in {
            ".csv",
            ".xlsx"
        }:

            print(
                "Processing as structured dataset..."
            )


            # ---------------------------------------------
            # DATA UNDERSTANDING
            # ---------------------------------------------

            understanding = understand_dataset(
                str(file_path)
            )


            # ---------------------------------------------
            # ANALYTICS
            # ---------------------------------------------

            analytics = calculate_analytics(
                str(file_path)
            )


            # ---------------------------------------------
            # SUCCESS RESPONSE
            # ---------------------------------------------

            return {

                "status":
                    "success",

                "document_id":
                    document_id,

                "file_name":
                    safe_name,

                "file_type":
                    extension.replace(
                        ".",
                        ""
                    ),

                "processing_type":
                    "dataset",

                "message":
                    "Dataset uploaded and analyzed successfully.",

                "understanding":
                    understanding,

                "analytics":
                    analytics

            }


    except Exception as error:

        logger.exception("Document processing failed")


        # -------------------------------------------------
        # Remove failed upload
        # -------------------------------------------------

        if file_path.exists():

            try:

                file_path.unlink()

            except Exception:

                pass


        raise HTTPException(

            status_code=500,

            detail="Document processing failed. Check that the file is a valid PDF or DOCX document."

        )


# =========================================================
# LIST DOCUMENTS
# =========================================================

@router.get("/")
def list_documents(request: Request):

    documents = []

    upload_dir, _ = user_storage_dirs(request)


    for file in upload_dir.iterdir():

        if not file.is_file():

            continue


        extension = (
            file.suffix
            .lower()
        )


        if extension not in {
            ".pdf",
            ".docx",
            ".csv",
            ".xlsx"
        }:

            continue


        # Determine processing type

        if extension in {
            ".pdf",
            ".docx"
        }:

            processing_type = "rag"

        else:

            processing_type = "dataset"


        documents.append({

            "file_name":
                file.name,

            "size":
                file.stat().st_size,

            "file_type":
                extension.replace(
                    ".",
                    ""
                ),

            "processing_type":
                processing_type

        })


    return {

        "status":
            "success",

        "documents":
            documents

    }


# =========================================================
# ASK DOCUMENT QUESTION
# =========================================================

@router.post("/ask")
def ask_document_question(
    payload: DocumentQuestion,
    http_request: Request,
):

    # -----------------------------------------------------
    # Validate question
    # -----------------------------------------------------

    question = (
        payload.question or ""
    ).strip()


    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )


    # -----------------------------------------------------
    # Find processed documents
    # -----------------------------------------------------

    _, processed_dir = user_storage_dirs(http_request)
    embedding_files = list(
        processed_dir.glob(
            "*_embeddings.json"
        )
    )


    if not embedding_files:

        raise HTTPException(

            status_code=404,

            detail=(
                "No processed documents found. "
                "Please upload a PDF or DOCX document first."
            )

        )


    # -----------------------------------------------------
    # Select requested document
    # -----------------------------------------------------

    embedding_file = None


    if payload.document_name:

        requested_name = (
            Path(
                payload.document_name
            )
            .name
            .lower()
        )


        # =================================================
        # CHECK EACH EMBEDDING FILE
        # =================================================

        for file in embedding_files:

            try:

                embedding_data = load_embeddings(
                    str(file)
                )


                embedding_document_name = str(
                    embedding_data.get(
                        "document_name",
                        ""
                    )
                ).lower()


                # -------------------------------------------------
                # Match original filename
                # -------------------------------------------------

                if (
                    embedding_document_name
                    == requested_name

                    or

                    embedding_document_name.endswith(
                        "_" + requested_name
                    )
                ):

                    embedding_file = file

                    break


            except Exception as error:

                print(
                    "Could not inspect embedding file:",
                    file.name,
                    repr(error)
                )


        # -------------------------------------------------
        # Requested document not found
        # -------------------------------------------------

        if embedding_file is None:

            raise HTTPException(

                status_code=404,

                detail=(
                    f"No processed document found for "
                    f"'{payload.document_name}'."
                )

            )


    else:

        # -------------------------------------------------
        # Backward-compatible fallback
        # -------------------------------------------------

        embedding_file = embedding_files[-1]


    try:

        print(
            "Loading embeddings:",
            embedding_file.name
        )


        # =================================================
        # LOAD EMBEDDINGS
        # =================================================

        embedding_data = load_embeddings(
            str(embedding_file)
        )


        # =================================================
        # LOAD SEARCH MODEL
        # =================================================

        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )


        # =================================================
        # SEMANTIC SEARCH
        # =================================================

        results = search_documents(

            question,

            embedding_data,

            model,

            top_k=5

        )


        # =================================================
        # GENERATE ANSWER
        # =================================================

        answer = create_rag_answer(

            question,

            results

        )


        # =================================================
        # RESPONSE
        # =================================================

        return {

            "status":
                "success",

            "question":
                question,

            "answer":
                answer,

            "sources":
                results

        }


    except Exception as error:

        logger.exception("Document question processing failed")


        raise HTTPException(

            status_code=500,

            detail="Question processing failed. Please retry or choose a different processed document."

        )






