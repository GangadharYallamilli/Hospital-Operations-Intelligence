import os
import pandas as pd

from document_loader import load_document
from dataset_profiler import profile_dataset
from document_profiler import profile_document


def analyze_document(file_path):
    """
    Universal analysis pipeline.

    Automatically:
    1. Detects file type
    2. Extracts content
    3. Normalizes the result
    4. Selects the correct profiler
    """

    document = load_document(file_path)

    file_type = document["file_type"]
    content_type = document["content_type"]

    print(f"File type: {file_type}")
    print(f"Content type: {content_type}")

    # =====================================================
    # Structured datasets
    # =====================================================

    if content_type == "structured_dataset":

        data = document["data"]

        original_file_path = data.get(
            "file_path",
            file_path
        )

        # -------------------------------------------------
        # CSV
        # -------------------------------------------------

        if file_type == "csv":

            df = pd.read_csv(
                original_file_path
            )

            profile = profile_dataset(df)

            return {
                "document": document,
                "analysis_type": "dataset",
                "content_type": "structured_dataset",
                "file_type": file_type,
                "file_path": original_file_path,
                "profile": profile
            }

        # -------------------------------------------------
        # XLSX
        # -------------------------------------------------

        elif file_type == "xlsx":

            excel_file = pd.ExcelFile(
                original_file_path
            )

            sheet_profiles = []

            for sheet_name in excel_file.sheet_names:

                df = pd.read_excel(
                    original_file_path,
                    sheet_name=sheet_name
                )

                profile = profile_dataset(df)

                sheet_profiles.append({
                    "sheet_name": sheet_name,
                    "profile": profile
                })

            return {
                "document": document,
                "analysis_type": "dataset",
                "content_type": "structured_dataset",
                "file_type": file_type,
                "file_path": original_file_path,
                "total_sheets": len(sheet_profiles),
                "sheets": sheet_profiles
            }

    # =====================================================
    # Documents
    # =====================================================

    elif content_type == "document":

        profile = profile_document(
            document
        )

        return {
            "document": document,
            "analysis_type": "document",
            "content_type": "document",
            "file_type": file_type,
            "file_path": file_path,
            "profile": profile
        }

    # =====================================================
    # Unknown content type
    # =====================================================

    raise ValueError(
        f"Unable to analyze content type: {content_type}"
    )


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    test_folder = (
        "member2/documents/original"
    )

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

        try:

            print(
                "\n=============================="
            )

            print(
                "Processing:",
                file_name
            )

            print(
                "=============================="
            )

            result = analyze_document(
                file_path
            )

            print(
                "Analysis type:",
                result["analysis_type"]
            )

            print(
                "Content type:",
                result["content_type"]
            )

            profile = result["profile"]

            # -------------------------------------------------
            # Dataset
            # -------------------------------------------------

            if result["analysis_type"] == "dataset":

                if "sheets" in result:

                    print(
                        "Excel sheets:",
                        result["total_sheets"]
                    )

                    for sheet in result["sheets"]:

                        print(
                            "\nSheet:",
                            sheet["sheet_name"]
                        )

                        sheet_profile = (
                            sheet["profile"]
                        )

                        print(
                            "Rows:",
                            sheet_profile[
                                "total_rows"
                            ]
                        )

                        print(
                            "Columns:",
                            sheet_profile[
                                "total_columns"
                            ]
                        )

                else:

                    print(
                        "Rows:",
                        profile["total_rows"]
                    )

                    print(
                        "Columns:",
                        profile["total_columns"]
                    )

                    print(
                        "Numeric columns:",
                        len(
                            profile[
                                "numeric_columns"
                            ]
                        )
                    )

                    print(
                        "Categorical columns:",
                        len(
                            profile[
                                "categorical_columns"
                            ]
                        )
                    )

                    print(
                        "Possible ID columns:",
                        profile[
                            "possible_id_columns"
                        ]
                    )

            # -------------------------------------------------
            # Document
            # -------------------------------------------------

            else:

                print(
                    "Pages:",
                    profile["total_pages"]
                )

                print(
                    "Tables:",
                    profile["total_tables"]
                )

                print(
                    "Text characters:",
                    profile[
                        "total_text_characters"
                    ]
                )

        except ValueError:

            # Ignore unsupported files
            # such as .gitkeep

            continue

        except Exception as error:

            print(
                "Error:",
                error
            )