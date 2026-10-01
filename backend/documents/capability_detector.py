def detect_dataset_capabilities(profile):

    capabilities = []

    total_rows = profile.get(
        "total_rows",
        0
    )

    total_columns = profile.get(
        "total_columns",
        0
    )

    numeric_columns = profile.get(
        "numeric_columns",
        []
    )

    categorical_columns = profile.get(
        "categorical_columns",
        []
    )

    possible_id_columns = profile.get(
        "possible_id_columns",
        []
    )

    possible_target_columns = profile.get(
        "possible_target_columns",
        []
    )

    date_columns = profile.get(
        "date_columns",
        []
    )


    # =====================================================
    # Dataset overview
    # =====================================================

    if (
        total_rows > 0
        and total_columns > 0
    ):

        capabilities.append(
            "Descriptive statistics"
        )


    # =====================================================
    # Missing values
    # =====================================================

    columns = profile.get(
        "columns",
        []
    )

    has_missing_values = any(
        column.get(
            "missing_values",
            0
        ) > 0
        for column in columns
    )

    if has_missing_values:

        capabilities.append(
            "Missing-value analysis"
        )


    # =====================================================
    # Numeric analysis
    # =====================================================

    if len(numeric_columns) >= 1:

        capabilities.append(
            "Numeric analysis"
        )


    # =====================================================
    # Correlation
    # =====================================================

    if len(numeric_columns) >= 2:

        capabilities.append(
            "Correlation analysis"
        )

        capabilities.append(
            "Numeric visualizations"
        )


    # =====================================================
    # Categorical analysis
    # =====================================================

    if len(categorical_columns) >= 1:

        capabilities.append(
            "Categorical analysis"
        )

        capabilities.append(
            "Categorical visualizations"
        )


    # =====================================================
    # Distribution
    # =====================================================

    if total_rows >= 10:

        capabilities.append(
            "Data distribution analysis"
        )


    # =====================================================
    # Date / Time
    # =====================================================

    if len(date_columns) >= 1:

        capabilities.append(
            "Date/time analysis"
        )

        capabilities.append(
            "Trend analysis"
        )

        capabilities.append(
            "Time-series visualizations"
        )


    # =====================================================
    # Machine Learning
    # =====================================================

    # Remove IDs and dates from target candidates

    non_id_targets = [

        target

        for target
        in possible_target_columns

        if target
        not in possible_id_columns

        and target
        not in date_columns
    ]


    # A dataset needs:
    # - enough rows
    # - at least one feature
    # - at least one possible target

    if (
        total_rows >= 20
        and total_columns >= 2
        and len(non_id_targets) >= 1
    ):

        capabilities.append(
            "Machine learning candidate analysis"
        )


    return {

        "capabilities":
            capabilities,

        "possible_target_columns":
            non_id_targets
    }


# =========================================================
# Document capabilities
# =========================================================

def detect_document_capabilities(profile):

    capabilities = []

    text_characters = profile.get(
        "total_text_characters",
        0
    )

    total_tables = profile.get(
        "total_tables",
        0
    )


    # Text capabilities

    if text_characters > 0:

        capabilities.extend([
            "Document summarization",
            "Document question answering",
            "Document search / RAG"
        ])


    # Table capabilities

    if total_tables > 0:

        capabilities.extend([
            "Table analysis",
            "KPI extraction candidate"
        ])


    # Comparison

    if text_characters > 0:

        capabilities.append(
            "Document comparison"
        )


    return {
        "capabilities":
            capabilities
    }


# =========================================================
# Universal capability detector
# =========================================================

def detect_capabilities(
    analysis_result
):

    analysis_type = analysis_result.get(
        "analysis_type"
    )


    # Dataset

    if analysis_type == "dataset":

        profile = analysis_result.get(
            "profile",
            {}
        )

        return detect_dataset_capabilities(
            profile
        )


    # Document

    elif analysis_type == "document":

        profile = analysis_result.get(
            "profile",
            {}
        )

        return detect_document_capabilities(
            profile
        )


    return {
        "capabilities": []
    }