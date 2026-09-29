# ==========================================================
# Dynamic Data Understanding
# ==========================================================
# Purpose:
# Automatically understand uploaded CSV and Excel hospital
# datasets and detect which hospital analytics modules
# are available.
#
# Supported structured files:
# - CSV
# - Excel (.xlsx)
#
# PDF and DOCX will be handled separately later through
# the Document Intelligence module.
# ==========================================================


import pandas as pd


# ==========================================================
# 1. LOAD DATASET
# ==========================================================

def load_dataset(file_path):

    if file_path.lower().endswith(".csv"):

        return pd.read_csv(file_path)

    elif file_path.lower().endswith(".xlsx"):

        return pd.read_excel(file_path)

    else:

        raise ValueError(
            "Unsupported file format. "
            "Only CSV and Excel files are supported."
        )


# ==========================================================
# 2. NORMALIZE COLUMN NAMES
# ==========================================================

def normalize_columns(df):

    columns = []

    for column in df.columns:

        normalized = (
            str(column)
            .lower()
            .strip()
            .replace(" ", "_")
            .replace("-", "_")
        )

        columns.append(normalized)

    return columns


# ==========================================================
# 3. DETECT AVAILABLE HOSPITAL MODULES
# ==========================================================

def detect_modules(df):

    columns = normalize_columns(df)

    modules = []


    # ------------------------------------------------------
    # Admission Analytics
    # ------------------------------------------------------

    admission_keywords = [
        "admission_id",
        "admission_date",
        "admission_type",
        "discharge_date",
        "length_of_stay"
    ]

    admission_matches = sum(
        keyword in columns
        for keyword in admission_keywords
    )

    if admission_matches >= 2:

        modules.append("Admission Analytics")


    # ------------------------------------------------------
    # Appointment Analytics
    # ------------------------------------------------------

    appointment_keywords = [
        "appointment_id",
        "appointment_date",
        "appointment_type",
        "appointment_status",
        "wait_time_days"
    ]

    appointment_matches = sum(
        keyword in columns
        for keyword in appointment_keywords
    )

    if appointment_matches >= 2:

        modules.append("Appointment Analytics")


    # ------------------------------------------------------
    # Bed & Capacity Analytics
    # ------------------------------------------------------

    bed_keywords = [
        "total_beds",
        "occupied_beds",
        "available_beds",
        "occupancy_rate"
    ]

    bed_matches = sum(
        keyword in columns
        for keyword in bed_keywords
    )

    if bed_matches >= 2:

        modules.append("Bed & Capacity Analytics")


    # ------------------------------------------------------
    # Equipment Analytics
    # ------------------------------------------------------

    equipment_keywords = [
        "equipment_id",
        "equipment_type",
        "equipment_status",
        "usage_hours",
        "maintenance_count",
        "failure_count"
    ]

    equipment_matches = sum(
        keyword in columns
        for keyword in equipment_keywords
    )

    if equipment_matches >= 2:

        modules.append("Equipment Analytics")


    # ------------------------------------------------------
    # Department Analytics
    # ------------------------------------------------------

    if "department_id" in columns:

        modules.append("Department Analytics")


    return modules


# ==========================================================
# 4. PROFILE DATASET
# ==========================================================

def profile_dataset(df):

    profile = {

        "rows": len(df),

        "columns": len(df.columns),

        "column_names": df.columns.tolist(),

        "data_types": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },

        "missing_values": {
            column: int(value)
            for column, value in df.isnull().sum().items()
        },

        "duplicate_rows": int(
            df.duplicated().sum()
        )
    }

    return profile


# ==========================================================
# 5. UNDERSTAND DATASET
# ==========================================================

def understand_dataset(file_path):

    # Load dataset
    df = load_dataset(file_path)

    # Create dataset profile
    profile = profile_dataset(df)

    # Detect available modules
    modules = detect_modules(df)

    # Return complete result
    result = {

        "profile": profile,

        "available_modules": modules
    }

    return result


# ==========================================================
# 6. TEST THE MODULE
# ==========================================================
# This runs only when this Python file is executed directly.
#
# IMPORTANT:
# We run the command from the project root:
#
# python backend/data_understanding.py
#
# Therefore the correct path starts with:
#
# data/...
# ==========================================================

if __name__ == "__main__":

    datasets = {
        "Admissions": "data/processed/admissions/admissions_clean.csv",
        "Appointments": "data/processed/appointments/appointments_clean.csv",
        "Beds": "data/processed/beds/beds_clean.csv",
        "Equipment": "data/processed/equipment/equipment_clean.csv",
        "Departments": "data/processed/departments/departments_clean.csv"
    }

    print("\n==========================================")
    print("     HOSPITAL DATASET MODULE DETECTION")
    print("==========================================")

    for dataset_name, file_path in datasets.items():

        print(f"\n\n========== {dataset_name.upper()} ==========")

        try:

            result = understand_dataset(file_path)

            print("Rows:", result["profile"]["rows"])
            print("Columns:", result["profile"]["columns"])

            print("\nDetected Modules:")

            if result["available_modules"]:

                for module in result["available_modules"]:
                    print("✓", module)

            else:
                print("No modules detected.")

        except Exception as error:

            print("Error:", error)