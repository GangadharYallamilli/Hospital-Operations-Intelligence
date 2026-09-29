import pandas as pd


def load_file(file_path):
    if file_path.lower().endswith(".xlsx"):
        return pd.read_excel(file_path)

    return pd.read_csv(file_path)


def calculate_analytics(file_path):
    df = load_file(file_path)

    columns = set(df.columns)

    # -----------------------------------------
    # BED ANALYTICS
    # -----------------------------------------

    if {
        "total_beds",
        "occupied_beds",
        "available_beds",
        "occupancy_rate"
    }.issubset(columns):

        department_occupancy = (
            df.groupby("department_id")
            .agg(
                average_occupancy=("occupancy_rate", "mean"),
                average_occupied_beds=("occupied_beds", "mean"),
                average_available_beds=("available_beds", "mean")
            )
            .reset_index()
        )

        department_occupancy["average_occupancy"] = (
            department_occupancy["average_occupancy"].round(2)
        )

        department_occupancy["average_occupied_beds"] = (
            department_occupancy["average_occupied_beds"].round(2)
        )

        department_occupancy["average_available_beds"] = (
            department_occupancy["average_available_beds"].round(2)
        )

        return {
            "dataset_type": "beds",

            "kpis": [
                {
                    "label": "Average Daily Beds",
                    "value": round(df["total_beds"].mean(), 2)
                },
                {
                    "label": "Average Occupied Beds",
                    "value": round(df["occupied_beds"].mean(), 2)
                },
                {
                    "label": "Average Available Beds",
                    "value": round(df["available_beds"].mean(), 2)
                },
                {
                    "label": "Average Occupancy",
                    "value": f'{df["occupancy_rate"].mean():.2f}%'
                },
                {
                    "label": "Peak Occupied Beds",
                    "value": int(df["occupied_beds"].max())
                }
            ],

            "tables": [
                {
                    "title": "Department Occupancy",
                    "columns": [
                        "department_id",
                        "average_occupancy",
                        "average_occupied_beds",
                        "average_available_beds"
                    ],
                    "rows": department_occupancy.to_dict(orient="records")
                }
            ]
        }


    # -----------------------------------------
    # ADMISSION ANALYTICS
    # -----------------------------------------

    if {
        "admission_id",
        "admission_date",
        "admission_type",
        "length_of_stay"
    }.issubset(columns):

        admission_types = (
            df["admission_type"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        admission_types.columns = [
            "admission_type",
            "admission_count"
        ]

        department_stats = (
            df.groupby("department_id")
            .agg(
                admissions=("admission_id", "count"),
                average_los=("length_of_stay", "mean")
            )
            .reset_index()
        )

        department_stats["average_los"] = (
            department_stats["average_los"].round(2)
        )

        return {
            "dataset_type": "admissions",

            "kpis": [
                {
                    "label": "Total Admissions",
                    "value": len(df)
                },
                {
                    "label": "Average Length of Stay",
                    "value": round(df["length_of_stay"].mean(), 2)
                },
                {
                    "label": "Peak Length of Stay",
                    "value": int(df["length_of_stay"].max())
                },
                {
                    "label": "Emergency Admissions",
                    "value": int(
                        (df["admission_type"] == "Emergency").sum()
                    )
                },
                {
                    "label": "Unique Patients",
                    "value": df["patient_id"].nunique()
                    if "patient_id" in columns else "-"
                }
            ],

            "tables": [
                {
                    "title": "Admissions by Type",
                    "columns": [
                        "admission_type",
                        "admission_count"
                    ],
                    "rows": admission_types.to_dict(
                        orient="records"
                    )
                },
                {
                    "title": "Department Performance",
                    "columns": [
                        "department_id",
                        "admissions",
                        "average_los"
                    ],
                    "rows": department_stats.to_dict(
                        orient="records"
                    )
                }
            ]
        }


    # -----------------------------------------
    # APPOINTMENT ANALYTICS
    # -----------------------------------------

    if {
        "appointment_id",
        "appointment_date",
        "appointment_status",
        "wait_time_days"
    }.issubset(columns):

        status_counts = (
            df["appointment_status"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "appointment_status",
            "appointment_count"
        ]

        no_show_count = int(
            (df["appointment_status"] == "No-Show").sum()
        )

        cancelled_count = int(
            (df["appointment_status"] == "Cancelled").sum()
        )

        no_show_rate = (
            no_show_count / len(df) * 100
            if len(df) > 0 else 0
        )

        department_wait = (
            df.groupby("department_id")
            .agg(
                average_wait_days=("wait_time_days", "mean"),
                appointments=("appointment_id", "count")
            )
            .reset_index()
        )

        department_wait["average_wait_days"] = (
            department_wait["average_wait_days"].round(2)
        )

        return {
            "dataset_type": "appointments",

            "kpis": [
                {
                    "label": "Total Appointments",
                    "value": len(df)
                },
                {
                    "label": "Completed",
                    "value": int(
                        (df["appointment_status"] == "Completed").sum()
                    )
                },
                {
                    "label": "No-Shows",
                    "value": no_show_count
                },
                {
                    "label": "Cancelled",
                    "value": cancelled_count
                },
                {
                    "label": "No-Show Rate",
                    "value": f"{no_show_rate:.2f}%"
                },
                {
                    "label": "Average Wait",
                    "value": f'{df["wait_time_days"].mean():.2f} days'
                }
            ],

            "tables": [
                {
                    "title": "Appointment Status",
                    "columns": [
                        "appointment_status",
                        "appointment_count"
                    ],
                    "rows": status_counts.to_dict(
                        orient="records"
                    )
                },
                {
                    "title": "Department Waiting Time",
                    "columns": [
                        "department_id",
                        "average_wait_days",
                        "appointments"
                    ],
                    "rows": department_wait.to_dict(
                        orient="records"
                    )
                }
            ]
        }


    # -----------------------------------------
    # EQUIPMENT ANALYTICS
    # -----------------------------------------

    if {
        "equipment_id",
        "equipment_type",
        "equipment_status",
        "usage_hours",
        "maintenance_count",
        "failure_count"
    }.issubset(columns):

        status_counts = (
            df["equipment_status"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        status_counts.columns = [
            "equipment_status",
            "equipment_count"
        ]

        equipment_types = (
            df.groupby("equipment_type")
            .agg(
                equipment_count=("equipment_id", "count"),
                average_usage_hours=("usage_hours", "mean"),
                total_failures=("failure_count", "sum"),
                total_maintenance=("maintenance_count", "sum")
            )
            .reset_index()
        )

        equipment_types["average_usage_hours"] = (
            equipment_types["average_usage_hours"].round(2)
        )

        return {
            "dataset_type": "equipment",

            "kpis": [
                {
                    "label": "Total Equipment",
                    "value": len(df)
                },
                {
                    "label": "Operational",
                    "value": int(
                        (df["equipment_status"] == "Operational").sum()
                    )
                },
                {
                    "label": "Under Maintenance",
                    "value": int(
                        (df["equipment_status"] == "Under Maintenance").sum()
                    )
                },
                {
                    "label": "Out of Service",
                    "value": int(
                        (df["equipment_status"] == "Out of Service").sum()
                    )
                },
                {
                    "label": "Total Failures",
                    "value": int(df["failure_count"].sum())
                },
                {
                    "label": "Total Maintenance",
                    "value": int(df["maintenance_count"].sum())
                }
            ],

            "tables": [
                {
                    "title": "Equipment Status",
                    "columns": [
                        "equipment_status",
                        "equipment_count"
                    ],
                    "rows": status_counts.to_dict(
                        orient="records"
                    )
                },
                {
                    "title": "Equipment Type Analysis",
                    "columns": [
                        "equipment_type",
                        "equipment_count",
                        "average_usage_hours",
                        "total_failures",
                        "total_maintenance"
                    ],
                    "rows": equipment_types.to_dict(
                        orient="records"
                    )
                }
            ]
        }


    # -----------------------------------------
    # DEPARTMENT ANALYTICS
    # -----------------------------------------

    if {
        "department_id",
        "department_name",
        "department_type"
    }.issubset(columns):

        department_types = (
            df["department_type"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        department_types.columns = [
            "department_type",
            "department_count"
        ]

        return {
            "dataset_type": "departments",

            "kpis": [
                {
                    "label": "Total Departments",
                    "value": len(df)
                },
                {
                    "label": "Department Types",
                    "value": df["department_type"].nunique()
                },
                {
                    "label": "Hospital Areas",
                    "value": df["hospital_area"].nunique()
                    if "hospital_area" in columns else "-"
                }
            ],

            "tables": [
                {
                    "title": "Department Types",
                    "columns": [
                        "department_type",
                        "department_count"
                    ],
                    "rows": department_types.to_dict(
                        orient="records"
                    )
                }
            ]
        }


    # -----------------------------------------
    # UNKNOWN DATASET
    # -----------------------------------------

    return {
        "dataset_type": "unknown",
        "kpis": [],
        "tables": []
    }


# -----------------------------------------
# Backward compatibility for current beds
# -----------------------------------------

def calculate_bed_analytics(file_path):

    result = calculate_analytics(file_path)

    if result["dataset_type"] != "beds":
        return None

    kpis = {
        item["label"]: item["value"]
        for item in result["kpis"]
    }

    department_table = result["tables"][0]

    return {
        "total_beds": kpis.get("Average Daily Beds"),
        "occupied_beds": kpis.get("Average Occupied Beds"),
        "available_beds": kpis.get("Average Available Beds"),
        "average_occupancy": float(
            str(kpis.get("Average Occupancy", "0")).replace("%", "")
        ),
        "peak_occupied_beds": kpis.get("Peak Occupied Beds"),
        "department_occupancy": department_table["rows"]
    }