import pandas as pd


def analyze_numeric_columns(df):
    """
    Analyze all numeric columns in a dataset.

    Returns general statistics without assuming
    any specific dataset or column names.
    """

    numeric_df = df.select_dtypes(
        include="number"
    )

    if numeric_df.empty:
        return {
            "numeric_columns": [],
            "summary": {}
        }

    summary = {}

    for column in numeric_df.columns:

        series = numeric_df[column]

        summary[str(column)] = {
            "count": int(series.count()),
            "missing_values": int(series.isna().sum()),
            "unique_values": int(series.nunique()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "minimum": float(series.min()),
            "maximum": float(series.max()),
            "standard_deviation": float(
                series.std()
            )
        }

    return {
        "numeric_columns": [
            str(column)
            for column in numeric_df.columns
        ],
        "summary": summary
    }

