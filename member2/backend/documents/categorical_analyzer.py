import pandas as pd


def analyze_categorical_columns(df):
    """
    Analyze categorical columns without assuming
    any specific dataset or column names.
    """

    categorical_df = df.select_dtypes(
        include=["object", "category", "bool"]
    )

    result = {}

    for column in categorical_df.columns:

        series = categorical_df[column]

        value_counts = (
            series
            .value_counts(dropna=False)
            .to_dict()
        )

        frequencies = {}

        for value, count in value_counts.items():

            if pd.isna(value):
                category = "Missing"
            else:
                category = str(value)

            frequencies[category] = int(count)

        result[str(column)] = {
            "missing_values": int(
                series.isna().sum()
            ),
            "unique_values": int(
                series.nunique()
            ),
            "frequencies": frequencies
        }

    return {
        "categorical_columns": [
            str(column)
            for column in categorical_df.columns
        ],
        "summary": result
    }