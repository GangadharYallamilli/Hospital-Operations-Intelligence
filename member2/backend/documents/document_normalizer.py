def normalize_document(extracted_data):
    """
    Convert the output of any extractor into a common
    document representation.

    The original extracted data is preserved.
    """

    file_type = extracted_data.get("file_type")

    normalized = {
        "document_name": extracted_data.get(
            "document_name"
        ),
        "file_type": file_type,

        # Identify the kind of content
        "content_type": (
            "structured_dataset"
            if file_type in ["csv", "xlsx"]
            else "document"
        ),

        # Original extractor output
        "data": extracted_data
    }

    return normalized


if __name__ == "__main__":

    sample_csv = {
        "document_name": "example.csv",
        "file_type": "csv",
        "total_rows": 100,
        "total_columns": 5
    }

    result = normalize_document(sample_csv)

    print(result)