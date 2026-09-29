import os
import pandas as pd


def extract_xlsx(file_path):
    """
    Generic Excel extractor.

    Automatically discovers:
    - sheets
    - rows
    - columns
    - data types
    - missing values
    - unique values
    - sample records
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    excel_file = pd.ExcelFile(file_path)

    sheets = []

    for sheet_name in excel_file.sheet_names:

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )

        columns = []

        for column in df.columns:

            series = df[column]

            columns.append({
                "name": str(column),
                "data_type": str(series.dtype),
                "missing_values": int(
                    series.isna().sum()
                ),
                "unique_values": int(
                    series.nunique()
                )
            })

        sheets.append({
            "sheet_name": str(sheet_name),
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": columns,
            "sample_records": df.head(5).to_dict(
                orient="records"
            )
        })

    return {
        "document_name": os.path.basename(file_path),
        "file_type": "xlsx",
        "file_path": file_path,
        "total_sheets": len(sheets),
        "sheets": sheets
    }


if __name__ == "__main__":

    test_folder = "member2/documents/original"

    for file_name in os.listdir(test_folder):

        if not file_name.lower().endswith(
            (".xlsx", ".xls")
        ):
            continue

        file_path = os.path.join(
            test_folder,
            file_name
        )

        print("\nProcessing:", file_name)

        try:

            result = extract_xlsx(file_path)

            print(
                "Sheets:",
                result["total_sheets"]
            )

            for sheet in result["sheets"]:

                print(
                    "\nSheet:",
                    sheet["sheet_name"]
                )

                print(
                    "Rows:",
                    sheet["total_rows"]
                )

                print(
                    "Columns:",
                    sheet["total_columns"]
                )

                for column in sheet["columns"]:

                    print(
                        f"{column['name']} "
                        f"-> {column['data_type']} "
                        f"| Missing: "
                        f"{column['missing_values']} "
                        f"| Unique: "
                        f"{column['unique_values']}"
                    )

        except Exception as error:

            print("Error:", error)