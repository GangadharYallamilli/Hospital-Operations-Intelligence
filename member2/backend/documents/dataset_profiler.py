import pandas as pd


def detect_date_columns(df):
    """
    Automatically detect columns that contain date/time values.

    Does not depend on specific column names.
    """

    date_columns = []

    for column in df.columns:

        series = df[column]

        # Already a datetime column
        if pd.api.types.is_datetime64_any_dtype(series):

            date_columns.append(str(column))
            continue

        # Don't try to interpret numeric columns as dates
        if pd.api.types.is_numeric_dtype(series):

            continue

        non_empty = series.dropna()

        if len(non_empty) == 0:
            continue

        converted = pd.to_datetime(
            non_empty,
            errors="coerce"
        )

        valid_ratio = converted.notna().mean()

        # Consider it a date column if at least 90%
        # of non-empty values can be interpreted as dates.
        if valid_ratio >= 0.90:

            date_columns.append(str(column))

    return date_columns


def profile_dataset(df):
    """
    Generic dataset profiler.

    Automatically analyzes:
    - rows and columns
    - data types
    - missing values
    - unique values
    - numeric columns
    - categorical columns
    - date/time columns
    - possible ID columns
    - possible target columns
    """

    profile = {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "columns": [],
        "numeric_columns": [],
        "categorical_columns": [],
        "date_columns": [],
        "possible_id_columns": [],
        "possible_target_columns": []
    }

    # Detect dates first
    date_columns = detect_date_columns(df)

    profile["date_columns"] = date_columns

    for column in df.columns:

        series = df[column]

        # Try numeric conversion
        numeric_series = pd.to_numeric(
            series,
            errors="coerce"
        )

        numeric_count = numeric_series.notna().sum()

        non_empty_count = series.notna().sum()

        is_numeric = (
            non_empty_count > 0
            and numeric_count / non_empty_count >= 0.90
        )

        # Date columns have priority
        if str(column) in date_columns:

            data_type = "date/time"

        elif is_numeric:

            data_type = "numeric"

        else:

            data_type = "categorical/text"

        column_info = {
            "name": str(column),
            "original_dtype": str(series.dtype),
            "detected_type": data_type,
            "missing_values": int(
                series.isna().sum()
            ),
            "unique_values": int(
                series.nunique()
            )
        }

        # Numeric statistics
        if data_type == "numeric":

            numeric_values = numeric_series.dropna()

            if len(numeric_values) > 0:

                column_info["min"] = float(
                    numeric_values.min()
                )

                column_info["max"] = float(
                    numeric_values.max()
                )

                column_info["mean"] = float(
                    numeric_values.mean()
                )

                column_info["median"] = float(
                    numeric_values.median()
                )

            profile["numeric_columns"].append(
                str(column)
            )

        elif data_type == "date/time":

            profile["date_columns"].append(
                str(column)
            )

        else:

            profile["categorical_columns"].append(
                str(column)
            )

        profile["columns"].append(
            column_info
        )

    # Remove duplicate date names
    profile["date_columns"] = list(
        dict.fromkeys(
            profile["date_columns"]
        )
    )

    # -----------------------------
    # Possible ID columns
    # -----------------------------

    for column in df.columns:

        unique_count = df[column].nunique()
        total_count = len(df)

        if total_count == 0:
            continue

        uniqueness_ratio = (
            unique_count / total_count
        )

        if uniqueness_ratio >= 0.95:

            profile["possible_id_columns"].append(
                str(column)
            )

    # -----------------------------
    # Possible target columns
    # -----------------------------

    for column in df.columns:

        # Never suggest date columns as targets
        if str(column) in profile["date_columns"]:
            continue

        # Never suggest obvious ID columns
        if str(column) in profile["possible_id_columns"]:
            continue

        unique_count = df[column].nunique()

        if 2 <= unique_count <= 10:

            profile["possible_target_columns"].append(
                str(column)
            )

    return profile


if __name__ == "__main__":

    file_path = (
        "member2/documents/original/"
        "kidney_disease.csv"
    )

    df = pd.read_csv(file_path)

    profile = profile_dataset(df)

    print("\n===== DATASET PROFILE =====")

    print(
        "Rows:",
        profile["total_rows"]
    )

    print(
        "Columns:",
        profile["total_columns"]
    )

    print("\n===== COLUMNS =====")

    for column in profile["columns"]:

        print(
            f"{column['name']} "
            f"-> {column['detected_type']} "
            f"| Missing: {column['missing_values']} "
            f"| Unique: {column['unique_values']}"
        )

    print("\n===== NUMERIC COLUMNS =====")

    print(
        profile["numeric_columns"]
    )

    print("\n===== CATEGORICAL/TEXT COLUMNS =====")

    print(
        profile["categorical_columns"]
    )

    print("\n===== DATE/TIME COLUMNS =====")

    print(
        profile["date_columns"]
    )

    print("\n===== POSSIBLE ID COLUMNS =====")

    print(
        profile["possible_id_columns"]
    )

    print("\n===== POSSIBLE TARGET COLUMNS =====")

    print(
        profile["possible_target_columns"]
    )