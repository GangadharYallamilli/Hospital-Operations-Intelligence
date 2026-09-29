import os
import json
import pdfplumber

try:
    from .document_cleaner import clean_text, clean_table
except ImportError:
    from document_cleaner import clean_text, clean_table


INPUT_FOLDER = "member2/documents/original"
OUTPUT_FOLDER = "member2/documents/processed"


def extract_pdf(pdf_path):
    """
    Extract and clean text and tables from a PDF.
    """

    document_name = os.path.basename(pdf_path)

    result = {
        "document_name": document_name,
        "file_type": "pdf",
        "total_pages": 0,
        "pages": []
    }

    with pdfplumber.open(pdf_path) as pdf:

        result["total_pages"] = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, start=1):

            # Extract and clean text
            text = page.extract_text() or ""
            text = clean_text(text)

            # Extract and clean tables
            raw_tables = page.extract_tables()

            tables = []

            for table in raw_tables:
                tables.append(clean_table(table))

            page_data = {
                "page_number": page_number,
                "text": text,
                "tables": tables
            }

            result["pages"].append(page_data)

    return result


def process_all_pdfs():
    """
    Process every PDF in the original documents folder.
    """

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    pdf_files = [
        file
        for file in os.listdir(INPUT_FOLDER)
        if file.lower().endswith(".pdf")
    ]

    print("PDF files found:", len(pdf_files))

    for file in pdf_files:

        pdf_path = os.path.join(INPUT_FOLDER, file)

        print("\nProcessing:", file)

        result = extract_pdf(pdf_path)

        output_name = os.path.splitext(file)[0] + ".json"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        with open(output_path, "w", encoding="utf-8") as output_file:
            json.dump(
                result,
                output_file,
                ensure_ascii=False,
                indent=2
            )

        print("Pages:", result["total_pages"])
        print("Saved:", output_path)


if __name__ == "__main__":
    process_all_pdfs()