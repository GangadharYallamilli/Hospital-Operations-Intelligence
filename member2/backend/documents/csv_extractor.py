import os
import pandas as pd



def extract_csv(file_path):
    """
    Generic CSV extractor.

    Does not assume any particular column names or dataset.
    Automatically detects:
    - columns
    - rows
    - data types
    - missing values
    - sample records
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    columns = []

    for column in df.columns:
        columns.append({
            "name": str(column),
            "data_type": str(df[column].dtype),
            "missing_values": int(df[column].isna().sum()),
            "unique_values": int(df[column].nunique())
        })

    result = {
        "file_path": file_path,
        "document_name": os.path.basename(file_path),
        "file_type": "csv",
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "columns": columns,
        "sample_records": df.head(5).to_dict(
            orient="records"
        )
    }

    return result


if __name__ == "__main__":

    test_folder = "member2/documents/original"

    for file_name in os.listdir(test_folder):

        if not file_name.lower().endswith(".csv"):
            continue

        file_path = os.path.join(
            test_folder,
            file_name
        )

        print("\nProcessing:", file_name)

        try:
            result = extract_csv(file_path)

            print("Rows:", result["total_rows"])
            print("Columns:", result["total_columns"])

            print("\nColumn information:")

            for column in result["columns"]:
                print(
                    f"{column['name']} "
                    f"-> {column['data_type']} "
                    f"| Missing: {column['missing_values']} "
                    f"| Unique: {column['unique_values']}"
                )

            print("\nSample records:")

            for record in result["sample_records"]:
                print(record)

        except Exception as error:
            print("Error:", error)