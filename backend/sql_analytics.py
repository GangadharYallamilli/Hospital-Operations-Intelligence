"""Allowlisted read-only queries shared by Copilot, NexaSight and NexaCommand."""

from contextlib import contextmanager
import logging
import os
from pathlib import Path
import re

import mysql.connector
from mysql.connector import Error as MySQLError


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUERY_DIR = PROJECT_ROOT / "database" / "queries"
DATABASE_UNAVAILABLE = (
    "Structured hospital database analytics are currently unavailable because "
    "the database connection is not configured."
)


class DatabaseAnalyticsUnavailable(Exception):
    """Raised when the configured read-only analytics connection cannot run."""


# File and statement positions are fixed by the application. Question text is
# never treated as SQL. These statements reuse the reviewed analytics queries.
_QUERY_FILES = {
    "admissions_by_department": ("01_basic_analytics.sql", 0),
    "average_los_by_department": ("01_basic_analytics.sql", 1),
    "appointment_status_summary": ("02_appointment_analytics.sql", 0),
    "average_beds_by_department": ("03_bed_analytics.sql", 1),
    "equipment_status_summary": ("04_equipment_analytics.sql", 0),
}

_EXTRA_QUERIES = {
    "average_length_of_stay": (
        "SELECT ROUND(AVG(a.length_of_stay), 2) AS average_length_of_stay "
        "FROM admissions a"
    ),
    "average_length_of_stay_by_department": (
        "SELECT ROUND(AVG(a.length_of_stay), 2) AS average_length_of_stay "
        "FROM admissions a JOIN departments d ON a.department_id = d.department_id "
        "WHERE LOWER(d.department_name) = LOWER(%s)"
    ),
    "cancelled_appointments_last_month": (
        "SELECT COUNT(a.appointment_id) AS appointment_records, "
        "SUM(CASE WHEN LOWER(TRIM(a.appointment_status)) IN ('cancelled', 'canceled') THEN 1 ELSE 0 END) AS cancelled_appointments "
        "FROM appointments a "
        "WHERE a.appointment_date >= CAST(DATE_FORMAT(CURRENT_DATE - INTERVAL 1 MONTH, '%Y-%m-01') AS DATE) "
        "AND a.appointment_date < CAST(DATE_FORMAT(CURRENT_DATE, '%Y-%m-01') AS DATE)"
    ),
    "occupied_beds_latest_snapshot": (
        "SELECT MAX(b.record_date) AS record_date, SUM(b.occupied_beds) AS occupied_beds "
        "FROM beds b WHERE b.record_date = (SELECT MAX(record_date) FROM beds)"
    ),
}


def _query_from_file(key: str) -> str:
    filename, index = _QUERY_FILES[key]
    path = QUERY_DIR / filename
    statements = []
    source = path.read_text(encoding="utf-8")
    uncommented = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("--"))
    statements = [statement.strip() for statement in uncommented.split(";") if statement.strip()]
    if index >= len(statements):
        raise RuntimeError(f"Expected a reviewed SELECT statement in {filename}.")
    statement = statements[index].strip()
    if not re.match(r"(?is)^SELECT\b", statement) or ";" in statement:
        raise RuntimeError(f"Only one reviewed SELECT is permitted from {filename}.")
    return statement


def _query(key: str) -> str:
    if key in _QUERY_FILES:
        return _query_from_file(key)
    if key in _EXTRA_QUERIES:
        statement = _EXTRA_QUERIES[key]
        if not re.match(r"(?is)^SELECT\b", statement):
            raise RuntimeError("Only reviewed SELECT statements are permitted.")
        return statement
    raise KeyError("Unsupported hospital analytics query.")


@contextmanager
def _readonly_cursor():
    # Copilot intentionally never falls back to importer/admin credentials.
    user = os.getenv("MYSQL_READONLY_USER")
    password = os.getenv("MYSQL_READONLY_PASSWORD")
    if not user or not password:
        raise DatabaseAnalyticsUnavailable("Read-only credentials are not configured.")
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=user,
            password=password,
            database=os.getenv("MYSQL_DATABASE", "hospital_operations"),
            connection_timeout=3,
            autocommit=False,
        )
        connection.start_transaction(readonly=True)
        cursor = connection.cursor(dictionary=True)
        try:
            yield cursor
        finally:
            cursor.close()
            connection.rollback()
    except DatabaseAnalyticsUnavailable:
        raise
    except (MySQLError, ValueError) as error:
        logger.warning("Hospital SQL analytics unavailable (%s).", type(error).__name__)
        raise DatabaseAnalyticsUnavailable("The read-only database connection is unavailable.") from None
    finally:
        if connection is not None:
            connection.close()


def _read_rows(key: str, params=()):
    query = _query(key)
    with _readonly_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


def _number(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else round(number, 2)


def run_sql_question(intent: str, department: str | None = None):
    """Return an answer only from a fixed, parameterized query or query file."""
    try:
        if intent == "average_length_of_stay":
            if department:
                rows = _read_rows("average_length_of_stay_by_department", (department[:80],))
                value = rows[0].get("average_length_of_stay") if rows else None
                answer = (f"Average length of stay in {department}: {_number(value)} days." if value is not None
                          else f"No admissions with a recorded length of stay were found for department '{department}'.")
                detail = "database/queries/01_basic_analytics.sql"
            else:
                rows = _read_rows("average_length_of_stay")
                value = rows[0].get("average_length_of_stay") if rows else None
                answer = (f"Average length of stay: {_number(value)} days." if value is not None
                          else "No admissions with a recorded length of stay were found.")
                detail = "database/queries/01_basic_analytics.sql"
            return _response(answer, detail)

        if intent == "most_admissions":
            rows = _read_rows("admissions_by_department")
            if not rows:
                return _response("No department admission records were found.", "database/queries/01_basic_analytics.sql")
            first = rows[0]
            name = first.get("department_name")
            count = _number(first.get("total_admissions"))
            return _response(f"{name} has the most admissions ({count}).", "database/queries/01_basic_analytics.sql", rows=rows)

        if intent == "cancelled_appointments_last_month":
            rows = _read_rows(intent)
            if not rows or not rows[0].get("appointment_records"):
                return _response("No appointment records were available for last month.", "database/queries/02_appointment_analytics.sql")
            value = rows[0].get("cancelled_appointments")
            value = 0 if value is None else value
            return _response(f"{_number(value)} appointments were cancelled last calendar month.", "database/queries/02_appointment_analytics.sql")

        if intent == "occupied_beds":
            rows = _read_rows("occupied_beds_latest_snapshot")
            value = rows[0].get("occupied_beds") if rows else None
            if value is None:
                return _response("No bed occupancy records were found.", "database/queries/03_bed_analytics.sql")
            stamp = rows[0].get("record_date")
            period = f" in the latest snapshot ({stamp})" if stamp else " in the latest snapshot"
            return _response(f"{_number(value)} beds were occupied{period}.", "database/queries/03_bed_analytics.sql")

        if intent == "operational_equipment":
            rows = _read_rows("equipment_status_summary")
            if not rows:
                return _response("No equipment records were found.", "database/queries/04_equipment_analytics.sql")
            count = sum(
                int(row.get("total_equipment") or 0)
                for row in rows
                if str(row.get("equipment_status") or "").strip().lower() in {"operational", "active", "working", "in service"}
            )
            return _response(f"{count} equipment units are operational.", "database/queries/04_equipment_analytics.sql", rows=rows)
    except DatabaseAnalyticsUnavailable:
        return {"status": "unavailable", "answer": DATABASE_UNAVAILABLE, "sources": []}

    return {"status": "unsupported", "answer": "That structured hospital metric is not available through the SQL analytics reader.", "sources": []}


def _response(answer: str, query_file: str, rows=None):
    sources = [{"type": "Hospital operational database", "query_file": query_file}]
    response = {"status": "success", "answer": answer, "sources": sources}
    if rows is not None:
        response["data"] = rows
    return response


def get_database_analytics():
    """Build the shared optional MySQL dashboard for NexaSight and NexaCommand."""
    snapshot = {"status": "success", "source": "Hospital operational database", "kpis": [], "charts": [], "tables": []}
    try:
        with _readonly_cursor() as cursor:
            def read(key):
                cursor.execute(_query(key), ())
                return cursor.fetchall()

            admissions = read("admissions_by_department")
            if admissions:
                total = sum(int(row.get("total_admissions") or 0) for row in admissions)
                snapshot["kpis"].append({"label": "Database admissions", "value": total})
                snapshot["charts"].append({"id": "db-admissions-by-department", "title": "Admissions by department · database", "type": "bar", "unit": "admissions", "data": [{"label": row.get("department_name"), "value": _number(row.get("total_admissions"))} for row in admissions if row.get("department_name") is not None and row.get("total_admissions") is not None]})
                snapshot["tables"].append({"title": "Admissions by department", "columns": ["department_name", "total_admissions"], "rows": admissions})
            avg_rows = read("average_los_by_department")
            if avg_rows:
                snapshot["tables"].append({"title": "Average length of stay by department", "columns": ["department_name", "average_length_of_stay"], "rows": avg_rows})
            hospital_avg = read("average_length_of_stay")
            if hospital_avg and hospital_avg[0].get("average_length_of_stay") is not None:
                snapshot["kpis"].append({"label": "Average length of stay", "value": _number(hospital_avg[0]["average_length_of_stay"]), "unit": "days"})
            appointment_rows = read("appointment_status_summary")
            if appointment_rows:
                snapshot["charts"].append({"id": "db-appointment-status", "title": "Appointment status · database", "type": "donut", "unit": "appointments", "data": [{"label": row.get("appointment_status") or "Unknown", "value": _number(row.get("total_appointments"))} for row in appointment_rows if row.get("total_appointments") is not None]})
                snapshot["tables"].append({"title": "Appointment status", "columns": ["appointment_status", "total_appointments", "percentage"], "rows": appointment_rows})
            bed_rows = read("average_beds_by_department")
            if bed_rows:
                snapshot["charts"].append({"id": "db-occupied-beds-by-department", "title": "Average occupied beds by department · database", "type": "bar", "unit": "beds", "data": [{"label": row.get("department_name"), "value": _number(row.get("average_occupied_beds"))} for row in bed_rows if row.get("department_name") is not None and row.get("average_occupied_beds") is not None]})
                snapshot["tables"].append({"title": "Bed availability by department", "columns": ["department_name", "average_occupied_beds", "average_available_beds"], "rows": bed_rows})
            equipment_rows = read("equipment_status_summary")
            if equipment_rows:
                snapshot["charts"].append({"id": "db-equipment-status", "title": "Equipment status · database", "type": "donut", "unit": "equipment units", "data": [{"label": row.get("equipment_status") or "Unknown", "value": _number(row.get("total_equipment"))} for row in equipment_rows if row.get("total_equipment") is not None]})
                snapshot["tables"].append({"title": "Equipment status", "columns": ["equipment_status", "total_equipment", "percentage"], "rows": equipment_rows})
        if not snapshot["kpis"] and not snapshot["charts"] and not snapshot["tables"]:
            return {"status": "unavailable", "message": "No hospital database records are available for these analytics."}
        return snapshot
    except DatabaseAnalyticsUnavailable:
        return {"status": "unavailable", "message": DATABASE_UNAVAILABLE}


def _format(value):
    return "—" if value is None else str(value)
