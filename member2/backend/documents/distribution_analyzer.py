import pandas as pd


def analyze_distributions(df, exclude_columns=None):
    """
    Analyze numeric and categorical distributions.

    exclude_columns can contain columns such as IDs
    that should not be treated as analytical variables.
    """

    if exclude_columns is None:
        exclude_columns = []

    result = {
        "numeric_columns": [],
        "categorical_columns": []
    }

    # -----------------------------------------------------
    # Numeric distributions
    # -----------------------------------------------------

    numeric_df = df.select_dtypes(
        include="number"
    )

    numeric_df = numeric_df.drop(
        columns=[
            column
            for column in exclude_columns
            if column in numeric_df.columns
        ],
        errors="ignore"
    )

    for column in numeric_df.columns:

        series = numeric_df[column].dropna()

        result["numeric_columns"].append({
            "column": str(column),
            "values": series.tolist()
        })

    # -----------------------------------------------------
    # Categorical distributions
    # -----------------------------------------------------

    categorical_df = df.select_dtypes(
        include=[
            "object",
            "category",
            "bool"
        ]
    )

    categorical_df = categorical_df.drop(
        columns=[
            column
            for column in exclude_columns
            if column in categorical_df.columns
        ],
        errors="ignore"
    )

    for column in categorical_df.columns:

        counts = (
            categorical_df[column]
            .fillna("Missing")
            .value_counts()
        )

        result["categorical_columns"].append({
            "column": str(column),
            "counts": counts.to_dict()
        })

    return result