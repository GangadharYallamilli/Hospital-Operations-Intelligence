# Import Pandas for reading CSV files and MySQL Connector for database access.
import pandas as pd
import mysql.connector

# Connect Python to our hospital_operations database.
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ap39cl7889",
    database="hospital_operations"
)

# Create a cursor for executing SQL commands.
cursor = connection.cursor()

print("Connected to MySQL!")


# Import appointments data into the appointments table.
appointments = pd.read_csv(
    r"D:\Hospital-Operations-Intelligence\data\processed\appointments\appointments_clean.csv"
)

appointment_query = """
INSERT INTO appointments (
    appointment_id, patient_id, department_id, appointment_date,
    appointment_type, booking_date, wait_time_days, appointment_status
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

# Insert all appointment records in bulk.
cursor.executemany(
    appointment_query,
    appointments.values.tolist()
)

connection.commit()

print("Appointments:", len(appointments), "rows inserted")


# Import beds data into the beds table.
beds = pd.read_csv(
    r"D:\Hospital-Operations-Intelligence\data\processed\beds\beds_clean.csv"
)

beds_query = """
INSERT INTO beds (
    bed_record_id, department_id, record_date, bed_type,
    total_beds, occupied_beds, available_beds, occupancy_rate
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

# Insert all bed records in bulk.
cursor.executemany(
    beds_query,
    beds.values.tolist()
)

connection.commit()

print("Beds:", len(beds), "rows inserted")


# Import equipment data into the equipment table.
equipment = pd.read_csv(
    r"D:\Hospital-Operations-Intelligence\data\processed\equipment\equipment_clean.csv"
)

equipment_query = """
INSERT INTO equipment (
    equipment_id, department_id, equipment_type, installation_date,
    last_maintenance_date, next_maintenance_date, equipment_status,
    usage_hours, maintenance_count, failure_count
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Insert all equipment records in bulk.
cursor.executemany(
    equipment_query,
    equipment.values.tolist()
)

connection.commit()

print("Equipment:", len(equipment), "rows inserted")


# Close the database connection after all imports are complete.
cursor.close()
connection.close()

print("All remaining datasets imported successfully!")