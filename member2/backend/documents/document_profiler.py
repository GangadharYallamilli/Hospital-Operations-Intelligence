def profile_document(normalized_document):
    """
    Generic profiler for PDF and DOCX documents.

    Automatically summarizes document structure
    without assuming any specific document content.
    """

    data = normalized_document["data"]
    file_type = normalized_document["file_type"]

    profile = {
        "document_name": normalized_document["document_name"],
        "file_type": file_type,
        "content_type": normalized_document["content_type"],
        "total_text_characters": 0,
        "total_tables": 0,
        "total_pages": None,
        "total_paragraphs": 0
    }

    # -----------------------------
    # PDF
    # -----------------------------

    if file_type == "pdf":

        pages = data.get("pages", [])

        profile["total_pages"] = len(pages)

        for page in pages:

            text = page.get("text", "")

            profile["total_text_characters"] += len(
                text
            )

            profile["total_tables"] += len(
                page.get("tables", [])
            )

    # -----------------------------
    # DOCX
    # -----------------------------

    elif file_type == "docx":

        paragraphs = data.get(
            "paragraphs",
            []
        )

        tables = data.get(
            "tables",
            []
        )

        profile["total_paragraphs"] = len(
            paragraphs
        )

        profile["total_tables"] = len(
            tables
        )

        for paragraph in paragraphs:

            profile["total_text_characters"] += len(
                paragraph.get("text", "")
            )

    else:

        raise ValueError(
            f"Unsupported document type: {file_type}"
        )

    return profile