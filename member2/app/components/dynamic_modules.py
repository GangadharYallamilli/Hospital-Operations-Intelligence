import os
import sys

import pandas as pd
import streamlit as st
import plotly.express as px

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from sklearn.linear_model import (
    LogisticRegression,
    LinearRegression
)

from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# =========================================================
# Backend document module path
# =========================================================

DOCUMENTS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "backend",
        "documents"
    )
)

if DOCUMENTS_PATH not in sys.path:
    sys.path.insert(0, DOCUMENTS_PATH)


# =========================================================
# Analytics imports
# =========================================================

from numeric_analyzer import analyze_numeric_columns
from categorical_analyzer import analyze_categorical_columns
from correlation_analyzer import analyze_correlations
from distribution_analyzer import analyze_distributions
from trend_analyzer import (
    detect_date_columns,
    analyze_trends
)


# =========================================================
# Helper: Load Dataset
# =========================================================

def load_dataframe(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension == ".csv":

        return pd.read_csv(
            file_path
        )

    elif extension == ".xlsx":

        excel_file = pd.ExcelFile(
            file_path
        )

        # Single sheet
        if len(excel_file.sheet_names) == 1:

            return pd.read_excel(
                file_path,
                sheet_name=excel_file.sheet_names[0]
            )

        # Multiple sheets
        frames = []

        for sheet_name in excel_file.sheet_names:

            sheet_df = pd.read_excel(
                file_path,
                sheet_name=sheet_name
            )

            if not sheet_df.empty:
                frames.append(sheet_df)

        if not frames:
            return pd.DataFrame()

        return pd.concat(
            frames,
            ignore_index=True
        )

    else:

        raise ValueError(
            f"Unsupported dataset format: {extension}"
        )


# =========================================================
# Helper: Detect ML Problem Type
# =========================================================

def detect_ml_problem_type(
    target_series
):
    """
    Automatically detect whether the target
    is a classification or regression problem.
    """

    target_series = target_series.dropna()

    if target_series.empty:
        return None

    unique_values = target_series.nunique()

    total_values = len(target_series)

    # Object/category/bool -> classification
    if (
        pd.api.types.is_object_dtype(
            target_series
        )
        or pd.api.types.is_categorical_dtype(
            target_series
        )
        or pd.api.types.is_bool_dtype(
            target_series
        )
    ):

        return "Classification"

    # Numeric target with small number of classes
    if pd.api.types.is_numeric_dtype(
        target_series
    ):

        if unique_values <= 10:

            return "Classification"

        # Numeric target with many unique values
        return "Regression"

    return None


# =========================================================
# Helper: Build ML Preprocessor
# =========================================================

def build_preprocessor(
    X
):

    numeric_columns = (
        X
        .select_dtypes(
            include="number"
        )
        .columns
        .tolist()
    )

    categorical_columns = (
        X
        .select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
        )
        .columns
        .tolist()
    )

    transformers = []

    # Numeric preprocessing
    if numeric_columns:

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    )
                ),
                (
                    "scaler",
                    StandardScaler()
                )
            ]
        )

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_columns
            )
        )

    # Categorical preprocessing
    if categorical_columns:

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    )
                ),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False
                    )
                )
            ]
        )

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop"
    )


# =========================================================
# Helper: Train Classification Models
# =========================================================

def train_classification_models(
    X_train,
    X_test,
    y_train,
    y_test
):

    preprocessor = build_preprocessor(
        X_train
    )

    models = {
        "Logistic Regression":
            LogisticRegression(
                max_iter=1000
            ),

        "Random Forest":
            RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
    }

    results = []

    trained_models = {}

    for model_name, model in models.items():

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "model",
                    model
                )
            ]
        )

        pipeline.fit(
            X_train,
            y_train
        )

        predictions = pipeline.predict(
            X_test
        )

        accuracy = accuracy_score(
            y_test,
            predictions
        )

        precision = precision_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0
        )

        recall = recall_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0
        )

        f1 = f1_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0
        )

        results.append({
            "Model": model_name,
            "Accuracy": round(
                accuracy,
                4
            ),
            "Precision": round(
                precision,
                4
            ),
            "Recall": round(
                recall,
                4
            ),
            "F1 Score": round(
                f1,
                4
            )
        })

        trained_models[
            model_name
        ] = pipeline

    return (
        pd.DataFrame(results),
        trained_models
    )


# =========================================================
# Helper: Train Regression Models
# =========================================================

def train_regression_models(
    X_train,
    X_test,
    y_train,
    y_test
):

    preprocessor = build_preprocessor(
        X_train
    )

    models = {
        "Linear Regression":
            LinearRegression(),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
    }

    results = []

    trained_models = {}

    for model_name, model in models.items():

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "model",
                    model
                )
            ]
        )

        pipeline.fit(
            X_train,
            y_train
        )

        predictions = pipeline.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        mse = mean_squared_error(
            y_test,
            predictions
        )

        rmse = mse ** 0.5

        r2 = r2_score(
            y_test,
            predictions
        )

        results.append({
            "Model": model_name,
            "MAE": round(
                mae,
                4
            ),
            "MSE": round(
                mse,
                4
            ),
            "RMSE": round(
                rmse,
                4
            ),
            "R2 Score": round(
                r2,
                4
            )
        })

        trained_models[
            model_name
        ] = pipeline

    return (
        pd.DataFrame(results),
        trained_models
    )


# =========================================================
# Main Dynamic Module Renderer
# =========================================================

def render_dynamic_modules(
    capabilities,
    analysis_result
):

    # -----------------------------------------------------
    # Detected capabilities
    # -----------------------------------------------------

    detected_capabilities = capabilities.get(
        "capabilities",
        []
    )

    # -----------------------------------------------------
    # Content type
    # -----------------------------------------------------

    content_type = analysis_result.get(
        "content_type"
    )

    st.subheader(
        "📊 Available Analysis Modules"
    )


    # =====================================================
    # DATASET
    # =====================================================

    if content_type == "structured_dataset":

        file_path = analysis_result.get(
            "file_path"
        )

        if not file_path:

            st.error(
                "Dataset file path is not available."
            )

            return

        # -------------------------------------------------
        # Load dataframe
        # -------------------------------------------------

        try:

            df = load_dataframe(
                file_path
            )

        except Exception as error:

            st.error(
                f"Could not load dataset: {error}"
            )

            return

        if df.empty:

            st.warning(
                "The uploaded dataset is empty."
            )

            return

        # -------------------------------------------------
        # Profile
        # -------------------------------------------------

        profile = analysis_result.get(
            "profile",
            {}
        )

        possible_id_columns = profile.get(
            "possible_id_columns",
            []
        )

        date_columns_from_profile = profile.get(
            "date_columns",
            []
        )


        # =================================================
        # 1. Dataset Overview
        # =================================================

        if (
            "Descriptive statistics"
            in detected_capabilities
        ):

            st.markdown(
                "### 📋 Dataset Overview"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Rows",
                    len(df)
                )

            with col2:

                st.metric(
                    "Columns",
                    len(df.columns)
                )

            with col3:

                st.metric(
                    "Missing Values",
                    int(
                        df.isna()
                        .sum()
                        .sum()
                    )
                )

            with st.expander(
                "View Dataset"
            ):

                st.dataframe(
                    df.head(100),
                    use_container_width=True
                )


        # =================================================
        # 2. Missing Values
        # =================================================

        if (
            "Missing-value analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### ⚠️ Missing-Value Analysis"
            )

            missing_df = pd.DataFrame({
                "Column": df.columns,
                "Missing Values": [
                    int(
                        df[column]
                        .isna()
                        .sum()
                    )
                    for column in df.columns
                ],
                "Missing %": [
                    round(
                        df[column]
                        .isna()
                        .mean()
                        * 100,
                        2
                    )
                    for column in df.columns
                ]
            })

            missing_df = missing_df[
                missing_df[
                    "Missing Values"
                ] > 0
            ]

            if missing_df.empty:

                st.success(
                    "No missing values detected."
                )

            else:

                st.dataframe(
                    missing_df,
                    use_container_width=True
                )


        # =================================================
        # 3. Numeric Analysis
        # =================================================

        if (
            "Numeric analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 🔢 Numeric Analysis"
            )

            numeric_result = (
                analyze_numeric_columns(
                    df
                )
            )

            numeric_columns = (
                numeric_result.get(
                    "numeric_columns",
                    []
                )
            )

            numeric_columns = [
                column
                for column in numeric_columns
                if column
                not in possible_id_columns
            ]

            if numeric_columns:

                selected_numeric = (
                    st.selectbox(
                        "Select Numeric Column",
                        numeric_columns,
                        key="numeric_analysis_column"
                    )
                )

                summary = (
                    numeric_result[
                        "summary"
                    ][selected_numeric]
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Mean",
                        round(
                            summary["mean"],
                            2
                        )
                    )

                with col2:

                    st.metric(
                        "Median",
                        round(
                            summary["median"],
                            2
                        )
                    )

                with col3:

                    st.metric(
                        "Standard Deviation",
                        round(
                            summary[
                                "standard_deviation"
                            ],
                            2
                        )
                    )

                st.write(
                    "Minimum:",
                    summary["minimum"]
                )

                st.write(
                    "Maximum:",
                    summary["maximum"]
                )

                st.write(
                    "Missing Values:",
                    summary[
                        "missing_values"
                    ]
                )

            else:

                st.info(
                    "No analytical numeric columns found."
                )


        # =================================================
        # 4. Categorical Analysis
        # =================================================

        if (
            "Categorical analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 🏷️ Categorical Analysis"
            )

            categorical_result = (
                analyze_categorical_columns(
                    df
                )
            )

            categorical_columns = (
                categorical_result.get(
                    "categorical_columns",
                    []
                )
            )

            if categorical_columns:

                selected_category = (
                    st.selectbox(
                        "Select Categorical Column",
                        categorical_columns,
                        key="categorical_analysis_column"
                    )
                )

                category_summary = (
                    categorical_result[
                        "summary"
                    ][selected_category]
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Unique Values",
                        category_summary[
                            "unique_values"
                        ]
                    )

                with col2:

                    st.metric(
                        "Missing Values",
                        category_summary[
                            "missing_values"
                        ]
                    )

                frequency_df = pd.DataFrame(
                    list(
                        category_summary[
                            "frequencies"
                        ].items()
                    ),
                    columns=[
                        "Category",
                        "Count"
                    ]
                )

                st.dataframe(
                    frequency_df,
                    use_container_width=True
                )


        # =================================================
        # 5. Correlation
        # =================================================

        if (
            "Correlation analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 🔗 Correlation Analysis"
            )

            correlation_result = (
                analyze_correlations(
                    df
                )
            )

            correlation_matrix = (
                correlation_result[
                    "correlation_matrix"
                ]
            )

            if not correlation_matrix.empty:

                # Remove ID columns
                correlation_matrix = (
                    correlation_matrix.drop(
                        index=[
                            column
                            for column
                            in possible_id_columns
                            if column
                            in correlation_matrix.index
                        ],
                        columns=[
                            column
                            for column
                            in possible_id_columns
                            if column
                            in correlation_matrix.columns
                        ],
                        errors="ignore"
                    )
                )

                if not correlation_matrix.empty:

                    fig = px.imshow(
                        correlation_matrix,
                        text_auto=True,
                        aspect="auto",
                        title=(
                            "Pearson Correlation Matrix"
                        )
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                else:

                    st.info(
                        "No analytical numeric columns "
                        "available for correlation."
                    )

            else:

                st.info(
                    "Not enough numeric columns "
                    "for correlation analysis."
                )


        # =================================================
        # 6. Distribution
        # =================================================

        if (
            "Data distribution analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 📈 Data Distribution"
            )

            distribution_result = (
                analyze_distributions(
                    df,
                    exclude_columns=
                    possible_id_columns
                )
            )

            numeric_distributions = (
                distribution_result[
                    "numeric_columns"
                ]
            )

            if numeric_distributions:

                numeric_names = [
                    item["column"]
                    for item
                    in numeric_distributions
                ]

                selected_distribution = (
                    st.selectbox(
                        "Select Numeric Column",
                        numeric_names,
                        key="distribution_numeric_column"
                    )
                )

                selected_data = next(
                    item
                    for item
                    in numeric_distributions
                    if item["column"]
                    == selected_distribution
                )

                fig = px.histogram(
                    x=selected_data[
                        "values"
                    ],
                    nbins=30,
                    title=(
                        f"Distribution of "
                        f"{selected_distribution}"
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


            categorical_distributions = (
                distribution_result[
                    "categorical_columns"
                ]
            )

            if categorical_distributions:

                category_names = [
                    item["column"]
                    for item
                    in categorical_distributions
                ]

                selected_category_distribution = (
                    st.selectbox(
                        "Select Categorical Column",
                        category_names,
                        key="distribution_category_column"
                    )
                )

                selected_category_data = next(
                    item
                    for item
                    in categorical_distributions
                    if item["column"]
                    == selected_category_distribution
                )

                category_chart_df = pd.DataFrame(
                    list(
                        selected_category_data[
                            "counts"
                        ].items()
                    ),
                    columns=[
                        "Category",
                        "Count"
                    ]
                )

                fig = px.bar(
                    category_chart_df,
                    x="Category",
                    y="Count",
                    title=(
                        f"Distribution of "
                        f"{selected_category_distribution}"
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


        # =================================================
        # 7. Date / Time
        # =================================================

        if (
            "Date/time analysis"
            in detected_capabilities
            or
            "Trend analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 🗓️ Date/Time Analysis"
            )

            detected_dates = (
                detect_date_columns(
                    df
                )
            )

            if detected_dates:

                st.success(
                    "Detected date/time columns: "
                    + ", ".join(
                        detected_dates
                    )
                )

            else:

                st.info(
                    "No date/time column detected "
                    "in this dataset."
                )


        # =================================================
        # 8. Trend Analysis
        # =================================================

        if (
            "Trend analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 📈 Trend Analysis"
            )

            date_columns = (
                detect_date_columns(
                    df
                )
            )

            if not date_columns:

                st.info(
                    "No date/time column detected "
                    "for trend analysis."
                )

            else:

                selected_date_column = (
                    st.selectbox(
                        "Select Date/Time Column",
                        date_columns,
                        key="trend_date_column"
                    )
                )

                aggregation = (
                    st.selectbox(
                        "Select Trend Calculation",
                        [
                            "count",
                            "sum",
                            "mean"
                        ],
                        key="trend_aggregation"
                    )
                )

                value_column = None

                if aggregation == "count":

                    st.caption(
                        "Counts the number of records "
                        "for each date."
                    )

                else:

                    numeric_columns = (
                        df
                        .select_dtypes(
                            include="number"
                        )
                        .columns
                        .tolist()
                    )

                    numeric_columns = [
                        column
                        for column
                        in numeric_columns
                        if column
                        not in possible_id_columns
                    ]

                    if not numeric_columns:

                        st.warning(
                            "No numeric column is available "
                            "for Sum/Mean trend analysis."
                        )

                    else:

                        value_column = (
                            st.selectbox(
                                "Select Numeric Column",
                                numeric_columns,
                                key="trend_value_column"
                            )
                        )

                if (
                    aggregation == "count"
                    or
                    value_column is not None
                ):

                    try:

                        trend_data = analyze_trends(
                            df,
                            selected_date_column,
                            value_column,
                            aggregation
                        )

                        if trend_data.empty:

                            st.info(
                                "No valid data available "
                                "for trend analysis."
                            )

                        else:

                            fig = px.line(
                                trend_data,
                                x="date",
                                y="value",
                                markers=True,
                                title=(
                                    f"{aggregation.title()} "
                                    f"Trend"
                                )
                            )

                            fig.update_layout(
                                xaxis_title="Date",
                                yaxis_title="Value"
                            )

                            st.plotly_chart(
                                fig,
                                use_container_width=True
                            )

                            with st.expander(
                                "View Trend Data"
                            ):

                                st.dataframe(
                                    trend_data,
                                    use_container_width=True
                                )

                    except Exception as error:

                        st.error(
                            f"Trend analysis failed: "
                            f"{error}"
                        )


        # =================================================
        # 9. MACHINE LEARNING
        # =================================================

        if (
            "Machine learning candidate analysis"
            in detected_capabilities
        ):

            st.markdown(
                "### 🤖 Machine Learning"
            )

            st.write(
                "Select a target column and the system "
                "will automatically determine whether "
                "the problem is classification or regression."
            )

            # -------------------------------------------------
            # Remove ID and date columns from target candidates
            # -------------------------------------------------

            excluded_columns = set(
                possible_id_columns
            )

            detected_dates = detect_date_columns(
                df
            )

            excluded_columns.update(
                detected_dates
            )

            target_candidates = [
                column
                for column
                in df.columns
                if column
                not in excluded_columns
            ]

            if not target_candidates:

                st.warning(
                    "No suitable target columns detected."
                )

            else:

                selected_target = (
                    st.selectbox(
                        "Select Target Column",
                        target_candidates,
                        key="ml_target_column"
                    )
                )

                target_series = (
                    df[selected_target]
                )

                problem_type = (
                    detect_ml_problem_type(
                        target_series
                    )
                )

                if problem_type is None:

                    st.warning(
                        "Unable to determine the ML problem type."
                    )

                else:

                    st.success(
                        f"Detected Problem Type: "
                        f"{problem_type}"
                    )

                    # -----------------------------------------
                    # Prepare dataset
                    # -----------------------------------------

                    ml_df = df.copy()

                    # Remove target-missing rows
                    ml_df = ml_df.dropna(
                        subset=[
                            selected_target
                        ]
                    )

                    y = ml_df[
                        selected_target
                    ]

                    X = ml_df.drop(
                        columns=[
                            selected_target
                        ]
                    )

                    # Remove IDs
                    X = X.drop(
                        columns=[
                            column
                            for column
                            in possible_id_columns
                            if column in X.columns
                        ],
                        errors="ignore"
                    )

                    # Remove detected dates
                    X = X.drop(
                        columns=[
                            column
                            for column
                            in detected_dates
                            if column in X.columns
                        ],
                        errors="ignore"
                    )

                    # Remove completely empty columns
                    empty_columns = [
                        column
                        for column in X.columns
                        if X[column].isna().all()
                    ]

                    if empty_columns:

                        X = X.drop(
                            columns=empty_columns
                        )

                    # -----------------------------------------
                    # Check dataset size
                    # -----------------------------------------

                    if len(X) < 20:

                        st.warning(
                            "At least 20 usable records "
                            "are recommended for ML training."
                        )

                    elif X.shape[1] == 0:

                        st.warning(
                            "No usable feature columns "
                            "remain after preprocessing."
                        )

                    else:

                        # -------------------------------------
                        # Classification
                        # -------------------------------------

                        if (
                            problem_type
                            == "Classification"
                        ):

                            class_counts = (
                                y.value_counts()
                            )

                            if (
                                len(class_counts) < 2
                            ):

                                st.warning(
                                    "Classification requires "
                                    "at least two target classes."
                                )

                            elif (
                                class_counts.min()
                                < 2
                            ):

                                st.warning(
                                    "Each target class needs "
                                    "at least two records."
                                )

                            else:

                                test_size = 0.20

                                try:

                                    (
                                        X_train,
                                        X_test,
                                        y_train,
                                        y_test
                                    ) = train_test_split(
                                        X,
                                        y,
                                        test_size=test_size,
                                        random_state=42,
                                        stratify=y
                                    )

                                    if st.button(
                                        "🚀 Train Classification Models",
                                        key="train_classification"
                                    ):

                                        with st.spinner(
                                            "Training classification models..."
                                        ):

                                            (
                                                results_df,
                                                trained_models
                                            ) = (
                                                train_classification_models(
                                                    X_train,
                                                    X_test,
                                                    y_train,
                                                    y_test
                                                )
                                            )

                                        st.success(
                                            "Models trained successfully."
                                        )

                                        st.markdown(
                                            "#### 📊 Model Performance"
                                        )

                                        st.dataframe(
                                            results_df,
                                            use_container_width=True
                                        )

                                        # -----------------------------
                                        # Accuracy chart
                                        # -----------------------------

                                        fig = px.bar(
                                            results_df,
                                            x="Model",
                                            y="Accuracy",
                                            title=(
                                                "Classification "
                                                "Model Accuracy"
                                            )
                                        )

                                        st.plotly_chart(
                                            fig,
                                            use_container_width=True
                                        )

                                        # -----------------------------
                                        # Best model by accuracy
                                        # -----------------------------

                                        best_model = (
                                            results_df
                                            .sort_values(
                                                "Accuracy",
                                                ascending=False
                                            )
                                            .iloc[0]
                                        )

                                        st.info(
                                            f"Highest test-set "
                                            f"accuracy in this run: "
                                            f"{best_model['Model']} "
                                            f"({best_model['Accuracy']:.4f})"
                                        )


                                except Exception as error:

                                    st.error(
                                        "Classification training "
                                        f"failed: {error}"
                                    )


                        # -----------------------------------------
                        # Regression
                        # -----------------------------------------

                        elif (
                            problem_type
                            == "Regression"
                        ):

                            try:

                                (
                                    X_train,
                                    X_test,
                                    y_train,
                                    y_test
                                ) = train_test_split(
                                    X,
                                    y,
                                    test_size=0.20,
                                    random_state=42
                                )

                                if st.button(
                                    "🚀 Train Regression Models",
                                    key="train_regression"
                                ):

                                    with st.spinner(
                                        "Training regression models..."
                                    ):

                                        (
                                            results_df,
                                            trained_models
                                        ) = (
                                            train_regression_models(
                                                X_train,
                                                X_test,
                                                y_train,
                                                y_test
                                            )
                                        )

                                    st.success(
                                        "Models trained successfully."
                                    )

                                    st.markdown(
                                        "#### 📊 Model Performance"
                                    )

                                    st.dataframe(
                                        results_df,
                                        use_container_width=True
                                    )

                                    # -----------------------------
                                    # R2 chart
                                    # -----------------------------

                                    fig = px.bar(
                                        results_df,
                                        x="Model",
                                        y="R2 Score",
                                        title=(
                                            "Regression "
                                            "Model R² Score"
                                        )
                                    )

                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True
                                    )

                                    best_model = (
                                        results_df
                                        .sort_values(
                                            "R2 Score",
                                            ascending=False
                                        )
                                        .iloc[0]
                                    )

                                    st.info(
                                        f"Highest test-set "
                                        f"R² in this run: "
                                        f"{best_model['Model']} "
                                        f"({best_model['R2 Score']:.4f})"
                                    )

                            except Exception as error:

                                st.error(
                                    "Regression training "
                                    f"failed: {error}"
                                )


    # =====================================================
    # DOCUMENT
    # =====================================================

    elif content_type == "document":

        st.markdown(
            "### 📄 Document Intelligence"
        )

        # IMPORTANT:
        # The document profiler result is stored
        # inside analysis_result["profile"].

        profile = analysis_result.get(
            "profile",
            {}
        )

        total_pages = profile.get(
            "total_pages",
            0
        )

        total_tables = profile.get(
            "total_tables",
            0
        )

        total_text_characters = profile.get(
            "total_text_characters",
            0
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Pages",
                total_pages
            )

        with col2:

            st.metric(
                "Tables",
                total_tables
            )

        with col3:

            st.metric(
                "Text Characters",
                total_text_characters
            )


        # -------------------------------------------------
        # Document Capabilities
        # -------------------------------------------------

        st.markdown(
            "### 🧠 Document Capabilities"
        )

        if detected_capabilities:

            for capability in detected_capabilities:

                st.write(
                    f"✓ {capability}"
                )

        else:

            st.info(
                "No document capabilities detected."
            )


    # =====================================================
    # UNKNOWN
    # =====================================================

    else:

        st.warning(
            "Unknown content type. "
            "Unable to determine available modules."
        )