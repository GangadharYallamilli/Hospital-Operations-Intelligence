import os
from pathlib import Path

import mysql.connector
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.getenv("MEDANEXA_PROCESSED_DATA", PROJECT_ROOT / "data" / "processed"))


def connect_database():
    required = {"MYSQL_USER": os.getenv("MYSQL_USER"), "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD")}
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise SystemExit("Set " + " and ".join(missing) + " before importing data.")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=required["MYSQL_USER"],
        password=required["MYSQL_PASSWORD"],
        database=os.getenv("MYSQL_DATABASE", "hospital_operations"),
    )


def main():
    imports = [
        ("appointments", """
            INSERT INTO appointments (
                appointment_id, patient_id, department_id, appointment_date,
                appointment_type, booking_date, wait_time_days, appointment_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """),
        ("beds", """
            INSERT INTO beds (
                bed_record_id, department_id, record_date, bed_type,
                total_beds, occupied_beds, available_beds, occupancy_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """),
        ("equipment", """
            INSERT INTO equipment (
                equipment_id, department_id, equipment_type, installation_date,
                last_maintenance_date, next_maintenance_date, equipment_status,
                usage_hours, maintenance_count, failure_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """),
    ]
    connection = connect_database()
    try:
        cursor = connection.cursor()
        try:
            for dataset, query in imports:
                data = pd.read_csv(DATA_ROOT / dataset / f"{dataset}_clean.csv")
                cursor.executemany(query, data.values.tolist())
                connection.commit()
                print(f"{dataset.title()}: {len(data)} rows inserted")
        finally:
            cursor.close()
    finally:
        connection.close()
    print("All remaining datasets imported successfully!")


if __name__ == "__main__":
    main()
