import os

from backend.documents.document_loader import load_document
from backend.documents.document_chunker import chunk_document

from backend.ai.embedding_generator import (
    load_embedding_model,
    generate_embeddings,
    save_embeddings
)


def process_document(
    file_path,
    output_folder
):
    """
    Universal document processing pipeline.

    Supports:
        PDF
        DOCX

    Flow:

    document
        ↓
    detect file type
        ↓
    extract content
        ↓
    normalize document
        ↓
    create chunks
        ↓
    generate embeddings
        ↓
    save embeddings
    """

    print(
        f"Processing document: "
        f"{os.path.basename(file_path)}"
    )


    # =========================================================
    # STEP 1: LOAD DOCUMENT
    # =========================================================

    document_data = load_document(
        file_path
    )


    print(
        "Document loaded successfully."
    )


    # =========================================================
    # STEP 2: CREATE CHUNKS
    # =========================================================

    chunks_data = chunk_document(
        document_data
    )


    # =========================================================
    # STEP 3: PRESERVE DOCUMENT NAME
    # =========================================================

    document_name = os.path.basename(
        file_path
    )


    chunks_data["document_name"] = (
        document_name
    )


    for chunk in chunks_data.get(
        "chunks",
        []
    ):

        if not chunk.get(
            "document_name"
        ):

            chunk["document_name"] = (
                document_name
            )


    # =========================================================
    # STEP 4: LOAD EMBEDDING MODEL
    # =========================================================

    print(
        "Loading embedding model..."
    )


    model = load_embedding_model()


    # =========================================================
    # STEP 5: GENERATE EMBEDDINGS
    # =========================================================

    print(
        "Generating embeddings..."
    )


    embedding_data = generate_embeddings(
        chunks_data,
        model
    )


    # =========================================================
    # STEP 6: SAVE EMBEDDINGS
    # =========================================================

    output_path = save_embeddings(
        embedding_data,
        output_folder
    )


    print(
        "Document processed successfully."
    )


    print(
        f"Embeddings saved to: "
        f"{output_path}"
    )


    return output_path


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    PROJECT_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        )
    )


    # ---------------------------------------------------------
    # Test PDF
    # ---------------------------------------------------------

    pdf_path = os.path.join(
        PROJECT_PATH,
        "backend",
        "documents",
        "uploads",
        "sample.pdf"
    )


    # ---------------------------------------------------------
    # Test DOCX
    # ---------------------------------------------------------

    docx_path = os.path.join(
        PROJECT_PATH,
        "backend",
        "documents",
        "uploads",
        "sample.docx"
    )


    # ---------------------------------------------------------
    # Output folder
    # ---------------------------------------------------------

    output_folder = os.path.join(
        PROJECT_PATH,
        "backend",
        "documents",
        "processed"
    )


    # ---------------------------------------------------------
    # Select an existing test document
    # ---------------------------------------------------------

    test_file = None


    if os.path.exists(pdf_path):

        test_file = pdf_path

    elif os.path.exists(docx_path):

        test_file = docx_path


    if test_file:

        process_document(
            test_file,
            output_folder
        )

    else:

        print(
            "No sample.pdf or sample.docx "
            "found in backend/documents/uploads."
        )