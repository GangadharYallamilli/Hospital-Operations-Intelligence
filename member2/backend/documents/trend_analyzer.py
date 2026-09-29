import pandas as pd


def detect_date_columns(df):
    """
    Detect columns that contain date/time values.
    Works with generic datasets without assuming
    specific hospital column names.
    """

    date_columns = []

    for column in df.columns:
        series = df[column]

        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(str(column))
            continue

        # Skip numeric columns
        if pd.api.types.is_numeric_dtype(series):
            continue

        non_empty = series.dropna()

        if len(non_empty) < 3:
            continue

        converted = pd.to_datetime(
            non_empty,
            errors="coerce",
            format="mixed"
        )

        valid_ratio = converted.notna().mean()

        if valid_ratio >= 0.90 and converted.nunique() >= 2:
            date_columns.append(str(column))

    return date_columns


def analyze_trends(df, date_column, value_column=None, aggregation="count"):
    """
    Analyze data over time.

    aggregation:
        count -> number of records
        sum   -> sum of selected numeric column
        mean  -> average of selected numeric column
    """

    if date_column not in df.columns:
        raise ValueError(
            f"Date column not found: {date_column}"
        )

    data = df.copy()

    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce",
        format="mixed"
    )

    data = data.dropna(subset=[date_column])

    if data.empty:
        return pd.DataFrame()

    # Count records by date
    if aggregation == "count":
        trend = (
            data
            .groupby(data[date_column].dt.date)
            .size()
            .reset_index(name="record_count")
        )

        trend.columns = ["date", "value"]

        return trend

    # Numeric aggregation
    if value_column is None:
        raise ValueError(
            "A numeric value column is required."
        )

    if value_column not in data.columns:
        raise ValueError(
            f"Value column not found: {value_column}"
        )

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce"
    )

    data = data.dropna(subset=[value_column])

    if data.empty:
        return pd.DataFrame()

    if aggregation == "sum":
        trend = (
            data
            .groupby(data[date_column].dt.date)[value_column]
            .sum()
            .reset_index()
        )

    elif aggregation == "mean":
        trend = (
            data
            .groupby(data[date_column].dt.date)[value_column]
            .mean()
            .reset_index()
        )

    else:
        raise ValueError(
            "Aggregation must be count, sum or mean."
        )

    trend.columns = ["date", "value"]

    return trend