import pandas as pd


def analyze_correlations(df):
    """
    Calculate correlations between numeric columns.

    Does not assume any specific dataset or column names.
    """

    numeric_df = df.select_dtypes(
        include="number"
    )

    if numeric_df.shape[1] < 2:
        return {
            "correlation_matrix": pd.DataFrame(),
            "numeric_columns": list(
                numeric_df.columns
            )
        }

    correlation_matrix = numeric_df.corr(
        method="pearson"
    )

    return {
        "correlation_matrix": correlation_matrix,
        "numeric_columns": [
            str(column)
            for column in numeric_df.columns
        ]
    }