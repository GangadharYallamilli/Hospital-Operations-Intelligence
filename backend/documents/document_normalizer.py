def normalize_document(extracted_data):
    """
    Convert extractor output into a common document
    representation.

    The original extracted data is preserved while
    important document fields are exposed at the top level.
    """

    file_type = extracted_data.get(
        "file_type"
    )

    normalized = {

        "document_name":
            extracted_data.get(
                "document_name"
            ),

        "file_type":
            file_type,

        "content_type":
            (
                "structured_dataset"
                if file_type in ["csv", "xlsx"]
                else "document"
            ),

        # Preserve original extractor output
        "data":
            extracted_data
    }


    # =====================================================
    # PDF
    # =====================================================

    if file_type == "pdf":

        normalized["pages"] = extracted_data.get(
            "pages",
            []
        )


    # =====================================================
    # DOCX
    # =====================================================

    elif file_type == "docx":

        normalized["paragraphs"] = extracted_data.get(
            "paragraphs",
            []
        )

        normalized["tables"] = extracted_data.get(
            "tables",
            []
        )

        normalized["total_paragraphs"] = extracted_data.get(
            "total_paragraphs",
            len(normalized["paragraphs"])
        )

        normalized["total_tables"] = extracted_data.get(
            "total_tables",
            len(normalized["tables"])
        )


    return normalized


if __name__ == "__main__":

    sample_docx = {

        "document_name":
            "hospital_report.docx",

        "file_type":
            "docx",

        "total_paragraphs":
            10,

        "total_tables":
            2,

        "paragraphs": [
            {
                "text":
                    "Hospital operations report",
                "style":
                    "Title"
            }
        ],

        "tables": [
            {
                "table_number":
                    1,
                "rows": [
                    [
                        "Department",
                        "Patients"
                    ],
                    [
                        "Cardiology",
                        "120"
                    ]
                ]
            }
        ]
    }


    result = normalize_document(
        sample_docx
    )


    print(
        "Document:",
        result["document_name"]
    )

    print(
        "File type:",
        result["file_type"]
    )

    print(
        "Paragraphs:",
        len(
            result.get(
                "paragraphs",
                []
            )
        )
    )

    print(
        "Tables:",
        len(
            result.get(
                "tables",
                []
            )
        )
    )