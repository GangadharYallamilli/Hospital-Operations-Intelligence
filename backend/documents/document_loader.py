import os

from backend.documents.file_detector import detect_file_type
from backend.documents.document_normalizer import normalize_document


def load_document(file_path):
    """
    Universal hospital document pipeline.

    Flow:
    file
      ↓
    detect type
      ↓
    extract content
      ↓
    normalize
      ↓
    return common document format
    """

    file_type = detect_file_type(file_path)

    print(
        f"Detected file type: {file_type}"
    )


    # =========================================================
    # PDF
    # =========================================================

    if file_type == "pdf":

        from backend.documents.pdf_extractor import extract_pdf

        extracted_data = extract_pdf(
            file_path
        )


    # =========================================================
    # DOCX
    # =========================================================

    elif file_type == "docx":

        from backend.documents.docx_extractor import extract_docx

        extracted_data = extract_docx(
            file_path
        )


    # =========================================================
    # UNSUPPORTED
    # =========================================================

    else:

        raise ValueError(
            f"Unsupported document type: {file_type}. "
            f"Supported formats are PDF and DOCX."
        )


    # =========================================================
    # NORMALIZE
    # =========================================================

    normalized_data = normalize_document(
        extracted_data
    )


    return normalized_data


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    test_folder = (
        "backend/documents/uploads"
    )


    if not os.path.exists(test_folder):

        print(
            f"Folder not found: {test_folder}"
        )

        exit()


    for file_name in os.listdir(
        test_folder
    ):

        file_path = os.path.join(
            test_folder,
            file_name
        )


        if not os.path.isfile(
            file_path
        ):

            continue


        # -----------------------------------------------------
        # Detect supported file type
        # -----------------------------------------------------

        try:

            file_type = detect_file_type(
                file_path
            )

        except ValueError:

            continue


        if file_type not in [
            "pdf",
            "docx"
        ]:

            continue


        print(
            "\nProcessing:",
            file_name
        )


        # -----------------------------------------------------
        # Load document
        # -----------------------------------------------------

        try:

            document = load_document(
                file_path
            )


            print(
                "Successfully loaded:",
                file_name
            )


            print(
                "File type:",
                document.get(
                    "file_type",
                    "Unknown"
                )
            )


            print(
                "Content type:",
                document.get(
                    "content_type",
                    "Unknown"
                )
            )


        except Exception as error:

            print(
                f"Could not process "
                f"{file_name}: {error}"
            )