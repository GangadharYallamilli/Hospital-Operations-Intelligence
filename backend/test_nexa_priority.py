import pandas as pd

from backend.nexa_priority import build_nexa_priority


# Sample equipment data
equipment_data = pd.DataFrame(
    [
        {
            "equipment_id": "EQ101",
            "department_id": "ICU",
            "equipment_type": "Ventilator",
            "equipment_status": "Operational",
            "usage_hours": 45000,
            "maintenance_count": 20,
            "failure_count": 8,
            "next_maintenance_date": "2026-01-10",
        },

        {
            "equipment_id": "EQ102",
            "department_id": "CARD",
            "equipment_type": "MRI",
            "equipment_status": "Operational",
            "usage_hours": 12000,
            "maintenance_count": 5,
            "failure_count": 2,
            "next_maintenance_date": "2027-01-10",
        },

        {
            "equipment_id": "EQ103",
            "department_id": "ER",
            "equipment_type": "Monitor",
            "equipment_status": "Out of Service",
            "usage_hours": 30000,
            "maintenance_count": 30,
            "failure_count": 10,
            "next_maintenance_date": "2025-01-01",
        },
    ]
)


result = build_nexa_priority(
    equipment_data,
    top_n=10
)


print("\nStatus:")
print(result["status"])


print("\nRecords processed:")
print(result["records_processed"])


print("\nTop Maintenance Priority:\n")


for item in result["priority_list"]:

    print(
        item["equipment_id"],
        "->",
        item["equipment_type"],
        "| Score:",
        item["priority_score"],
        "| Level:",
        item["priority_level"]
    )