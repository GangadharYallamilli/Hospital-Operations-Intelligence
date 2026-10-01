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
    admissions_path = DATA_ROOT / "admissions" / "admissions_clean.csv"
    admissions = pd.read_csv(admissions_path)
    print("Rows:", len(admissions))
    print("Columns:", admissions.columns.tolist())

    query = """
    INSERT INTO admissions (
        admission_id, patient_id, department_id, admission_date,
        discharge_date, admission_type, age, gender, length_of_stay,
        bed_type, discharge_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    connection = connect_database()
    try:
        cursor = connection.cursor()
        try:
            cursor.executemany(query, admissions.values.tolist())
            connection.commit()
            print("All admission records inserted successfully!")
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
