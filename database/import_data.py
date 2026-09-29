import mysql.connector
import pandas as pd

# Connect Python to the same MySQL account used by Workbench.
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ap39cl7889",
    database="hospital_operations"
)

print("Connected to MySQL!")


# Load the cleaned admissions CSV into Pandas.
file_path = r"D:\Hospital-Operations-Intelligence\data\processed\admissions\admissions_clean.csv"
admissions = pd.read_csv(file_path)

# Display information about the loaded CSV.
print("Rows:", len(admissions))
print("Columns:", len(admissions.columns))
print("Column names:", admissions.columns.tolist())


# Create a cursor so Python can execute SQL commands in MySQL.
cursor = connection.cursor()

# SQL statement used to insert one admission record.
insert_query = """
INSERT INTO admissions (
    admission_id,
    patient_id,
    department_id,
    admission_date,
    discharge_date,
    admission_type,
    age,
    gender,
    length_of_stay,
    bed_type,
    discharge_status
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Convert all 50,000 admission records into a list
# so they can be inserted into MySQL in bulk.
all_rows = admissions.values.tolist()

# Insert all admission records efficiently using executemany().
cursor.executemany(insert_query, all_rows)

# Save all inserted records permanently in MySQL.
connection.commit()

print("All admission records inserted successfully!")