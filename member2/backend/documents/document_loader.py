import os

from file_detector import detect_file_type
from document_normalizer import normalize_document


def load_document(file_path):
    """
    Universal document pipeline.

    Flow:
    file → detect → extract → normalize
    """

    file_type = detect_file_type(file_path)

    print(f"Detected file type: {file_type}")

    if file_type == "pdf":

        from pdf_extractor import extract_pdf

        extracted_data = extract_pdf(file_path)

    elif file_type == "csv":

        from csv_extractor import extract_csv

        extracted_data = extract_csv(file_path)

    elif file_type == "xlsx":

        from xlsx_extractor import extract_xlsx

        extracted_data = extract_xlsx(file_path)

    elif file_type == "docx":

        from docx_extractor import extract_docx

        extracted_data = extract_docx(file_path)

    else:

        raise ValueError(
            f"Unsupported document type: {file_type}"
        )

    # Convert extractor output into common format
    normalized_data = normalize_document(
        extracted_data
    )

    return normalized_data


if __name__ == "__main__":

    test_folder = "member2/documents/original"

    for file_name in os.listdir(test_folder):

        file_path = os.path.join(
            test_folder,
            file_name
        )

        if not os.path.isfile(file_path):
            continue

        # Ignore unsupported/internal files
        try:
            detect_file_type(file_path)
        except ValueError:
            continue

        print("\nProcessing:", file_name)

        try:

            document = load_document(file_path)

            print(
                "Successfully loaded:",
                file_name
            )

            print(
                "File type:",
                document["file_type"]
            )

            print(
                "Content type:",
                document["content_type"]
            )

        except Exception as error:

            print(
                f"Could not process "
                f"{file_name}: {error}"
            )