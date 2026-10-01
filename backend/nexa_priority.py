"""
NexaPriority
------------
Dynamic equipment maintenance prioritization using:

1. Hash Map
   equipment_id -> equipment information

2. Max Heap / Priority Queue
   Highest priority equipment stays at the top

3. Sorting
   Final maintenance list can be displayed in priority order

The algorithm works on the supplied equipment dataset.
It does NOT depend on the current 5,000-row MySQL dataset.

Expected equipment fields:
    equipment_id
    department_id
    equipment_type
    installation_date
    last_maintenance_date
    next_maintenance_date
    equipment_status
    usage_hours
    maintenance_count
    failure_count

Optional field:
    failure_risk

If failure_risk is available from an ML model, it is used.
Otherwise failure history is used as the failure-risk component.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
import heapq
import math

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

# These weights can be changed later without changing the DSA.
WEIGHTS = {
    "failure": 0.40,
    "usage": 0.25,
    "maintenance_history": 0.15,
    "maintenance_urgency": 0.10,
    "status": 0.10,
}


# Status contribution.
STATUS_SCORES = {
    "out of service": 100.0,
    "out_of_service": 100.0,
    "under maintenance": 60.0,
    "under_maintenance": 60.0,
    "operational": 20.0,
    "active": 20.0,
    "working": 20.0,
    "in service": 20.0,
}


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class EquipmentPriority:
    equipment_id: str
    department_id: str | None
    equipment_type: str | None
    equipment_status: str | None

    usage_hours: float
    maintenance_count: int
    failure_count: int

    failure_score: float
    usage_score: float
    maintenance_history_score: float
    maintenance_urgency_score: float
    status_score: float

    priority_score: float

    last_maintenance_date: str | None
    next_maintenance_date: str | None

    priority_level: str


# ============================================================
# HELPERS
# ============================================================

def _clean_text(value) -> str | None:
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return None

    return text


def _to_float(value, default=0.0) -> float:
    try:
        if value is None:
            return default

        if isinstance(value, float) and math.isnan(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _to_int(value, default=0) -> int:
    try:
        if value is None:
            return default

        if isinstance(value, float) and math.isnan(value):
            return default

        return int(float(value))

    except (TypeError, ValueError):
        return default


def _parse_date(value) -> date | None:

    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return None

        return parsed.date()

    except Exception:
        return None


def _date_to_string(value) -> str | None:

    parsed = _parse_date(value)

    if parsed is None:
        return None

    return parsed.isoformat()


# ============================================================
# NORMALIZATION
# ============================================================

def _min_max_score(value: float, minimum: float, maximum: float) -> float:

    if maximum <= minimum:
        return 0.0

    score = ((value - minimum) / (maximum - minimum)) * 100

    return max(0.0, min(100.0, score))


def _maximum_score(value: float, maximum: float) -> float:

    if maximum <= 0:
        return 0.0

    score = (value / maximum) * 100

    return max(0.0, min(100.0, score))


# ============================================================
# MAINTENANCE URGENCY
# ============================================================

def _maintenance_urgency_score(
    next_maintenance_date,
    today: date,
) -> float:

    maintenance_date = _parse_date(next_maintenance_date)

    # No maintenance date available.
    if maintenance_date is None:
        return 50.0

    days_difference = (maintenance_date - today).days

    # Overdue or due today.
    if days_difference <= 0:
        return 100.0

    # Future maintenance.
    #
    # The closer the maintenance date, the higher the score.
    # A date 365+ days away receives 0.
    score = 100.0 - ((days_difference / 365.0) * 100.0)

    return max(0.0, min(100.0, score))


# ============================================================
# PRIORITY LEVEL
# ============================================================

def _priority_level(score: float) -> str:

    if score >= 80:
        return "Critical"

    if score >= 60:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:

    dataframe = df.copy()

    dataframe.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in dataframe.columns
    ]

    return dataframe


def _find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    for candidate in candidates:

        normalized = (
            candidate
            .strip()
            .lower()
            .replace(" ", "_")
        )

        if normalized in dataframe.columns:
            return normalized

    return None


# ============================================================
# MAIN DSA ENGINE
# ============================================================

def build_nexa_priority(
    dataframe: pd.DataFrame,
    top_n: int = 20,
    today: date | None = None,
) -> dict:

    """
    Build NexaPriority from the supplied equipment dataset.

    The input can contain any number of equipment records.

    DSA used:

        Hash Map:
            equipment_map[equipment_id]

        Max Heap:
            priority_heap

        Sorting:
            final maintenance list
    """

    if dataframe is None or dataframe.empty:

        return {
            "status": "unavailable",
            "message": "No equipment records are available.",
            "records_processed": 0,
            "priority_list": [],
        }

    dataframe = _normalize_columns(dataframe)

    # --------------------------------------------------------
    # Required equipment ID
    # --------------------------------------------------------

    equipment_id_column = _find_column(
        dataframe,
        [
            "equipment_id",
            "equipmentid",
            "equipment",
            "device_id",
            "deviceid",
        ],
    )

    if equipment_id_column is None:

        return {
            "status": "unavailable",
            "message": "Equipment dataset does not contain an equipment_id column.",
            "records_processed": 0,
            "priority_list": [],
        }

    # --------------------------------------------------------
    # Optional columns
    # --------------------------------------------------------

    department_column = _find_column(
        dataframe,
        ["department_id", "department", "department_name"],
    )

    type_column = _find_column(
        dataframe,
        ["equipment_type", "equipment", "device_type"],
    )

    status_column = _find_column(
        dataframe,
        ["equipment_status", "status"],
    )

    usage_column = _find_column(
        dataframe,
        ["usage_hours", "usage", "hours_used"],
    )

    maintenance_count_column = _find_column(
        dataframe,
        [
            "maintenance_count",
            "maintenance_counts",
            "number_of_maintenance",
        ],
    )

    failure_count_column = _find_column(
        dataframe,
        [
            "failure_count",
            "failure_counts",
            "number_of_failures",
        ],
    )

    last_maintenance_column = _find_column(
        dataframe,
        [
            "last_maintenance_date",
            "last_maintenance",
        ],
    )

    next_maintenance_column = _find_column(
        dataframe,
        [
            "next_maintenance_date",
            "next_maintenance",
        ],
    )

    # Optional ML output.
    failure_risk_column = _find_column(
        dataframe,
        [
            "failure_risk",
            "failure_probability",
            "predicted_failure_risk",
            "risk_score",
        ],
    )

    if today is None:
        today = date.today()

    # --------------------------------------------------------
    # Dynamic dataset ranges
    # --------------------------------------------------------

    usage_values = []

    maintenance_values = []

    failure_values = []

    failure_risk_values = []

    for _, row in dataframe.iterrows():

        if usage_column:
            usage_values.append(
                _to_float(row.get(usage_column))
            )

        if maintenance_count_column:
            maintenance_values.append(
                _to_float(row.get(maintenance_count_column))
            )

        if failure_count_column:
            failure_values.append(
                _to_float(row.get(failure_count_column))
            )

        if failure_risk_column:
            failure_risk_values.append(
                _to_float(row.get(failure_risk_column))
            )

    usage_min = min(usage_values) if usage_values else 0.0
    usage_max = max(usage_values) if usage_values else 0.0

    maintenance_min = (
        min(maintenance_values)
        if maintenance_values
        else 0.0
    )

    maintenance_max = (
        max(maintenance_values)
        if maintenance_values
        else 0.0
    )

    failure_min = (
        min(failure_values)
        if failure_values
        else 0.0
    )

    failure_max = (
        max(failure_values)
        if failure_values
        else 0.0
    )

    failure_risk_min = (
        min(failure_risk_values)
        if failure_risk_values
        else 0.0
    )

    failure_risk_max = (
        max(failure_risk_values)
        if failure_risk_values
        else 0.0
    )

    # --------------------------------------------------------
    # DSA STRUCTURE 1: HASH MAP
    # --------------------------------------------------------

    equipment_map: dict[str, EquipmentPriority] = {}

    # --------------------------------------------------------
    # DSA STRUCTURE 2: MAX HEAP
    #
    # Python heapq is a MIN heap.
    # Therefore we store negative priority scores
    # to implement MAX HEAP behavior.
    # --------------------------------------------------------

    priority_heap = []

    # --------------------------------------------------------
    # PROCESS EVERY EQUIPMENT RECORD
    # --------------------------------------------------------

    for _, row in dataframe.iterrows():

        equipment_id = _clean_text(
            row.get(equipment_id_column)
        )

        if not equipment_id:
            continue

        department_id = (
            _clean_text(row.get(department_column))
            if department_column
            else None
        )

        equipment_type = (
            _clean_text(row.get(type_column))
            if type_column
            else None
        )

        equipment_status = (
            _clean_text(row.get(status_column))
            if status_column
            else None
        )

        usage_hours = (
            _to_float(row.get(usage_column))
            if usage_column
            else 0.0
        )

        maintenance_count = (
            _to_int(row.get(maintenance_count_column))
            if maintenance_count_column
            else 0
        )

        failure_count = (
            _to_int(row.get(failure_count_column))
            if failure_count_column
            else 0
        )

        # ----------------------------------------------------
        # FAILURE SCORE
        # ----------------------------------------------------

        if failure_risk_column:

            raw_risk = _to_float(
                row.get(failure_risk_column)
            )

            failure_score = _min_max_score(
                raw_risk,
                failure_risk_min,
                failure_risk_max,
            )

        else:

            failure_score = _min_max_score(
                failure_count,
                failure_min,
                failure_max,
            )

        # ----------------------------------------------------
        # USAGE SCORE
        # ----------------------------------------------------

        usage_score = _min_max_score(
            usage_hours,
            usage_min,
            usage_max,
        )

        # ----------------------------------------------------
        # MAINTENANCE HISTORY SCORE
        # ----------------------------------------------------

        maintenance_history_score = _min_max_score(
            maintenance_count,
            maintenance_min,
            maintenance_max,
        )

        # ----------------------------------------------------
        # MAINTENANCE URGENCY
        # ----------------------------------------------------

        next_maintenance = (
            row.get(next_maintenance_column)
            if next_maintenance_column
            else None
        )

        maintenance_urgency_score = (
            _maintenance_urgency_score(
                next_maintenance,
                today,
            )
        )

        # ----------------------------------------------------
        # STATUS SCORE
        # ----------------------------------------------------

        normalized_status = (
            equipment_status.lower().replace("-", " ")
            if equipment_status
            else ""
        )

        status_score = STATUS_SCORES.get(
            normalized_status,
            50.0,
        )

        # ----------------------------------------------------
        # FINAL PRIORITY SCORE
        # ----------------------------------------------------

        priority_score = (
            failure_score
            * WEIGHTS["failure"]
            +
            usage_score
            * WEIGHTS["usage"]
            +
            maintenance_history_score
            * WEIGHTS["maintenance_history"]
            +
            maintenance_urgency_score
            * WEIGHTS["maintenance_urgency"]
            +
            status_score
            * WEIGHTS["status"]
        )

        priority_score = round(
            max(0.0, min(100.0, priority_score)),
            2,
        )

        priority = EquipmentPriority(
            equipment_id=equipment_id,
            department_id=department_id,
            equipment_type=equipment_type,
            equipment_status=equipment_status,

            usage_hours=round(
                usage_hours,
                2,
            ),

            maintenance_count=maintenance_count,
            failure_count=failure_count,

            failure_score=round(
                failure_score,
                2,
            ),

            usage_score=round(
                usage_score,
                2,
            ),

            maintenance_history_score=round(
                maintenance_history_score,
                2,
            ),

            maintenance_urgency_score=round(
                maintenance_urgency_score,
                2,
            ),

            status_score=round(
                status_score,
                2,
            ),

            priority_score=priority_score,

            last_maintenance_date=_date_to_string(
                row.get(last_maintenance_column)
                if last_maintenance_column
                else None
            ),

            next_maintenance_date=_date_to_string(
                next_maintenance
            ),

            priority_level=_priority_level(
                priority_score
            ),
        )

        # ----------------------------------------------------
        # HASH MAP INSERTION
        # ----------------------------------------------------

        equipment_map[equipment_id] = priority

        # ----------------------------------------------------
        # MAX HEAP INSERTION
        # ----------------------------------------------------

        heapq.heappush(
            priority_heap,
            (
                -priority_score,
                equipment_id,
            ),
        )

    # --------------------------------------------------------
    # EXTRACT PRIORITY ORDER
    # --------------------------------------------------------

    priority_list = []

    while priority_heap:

        negative_score, equipment_id = heapq.heappop(
            priority_heap
        )

        priority = equipment_map[equipment_id]

        priority_list.append(
            asdict(priority)
        )

    # --------------------------------------------------------
    # LIMIT TOP N FOR UI
    # --------------------------------------------------------

    top_priority = priority_list[:max(1, top_n)]

    return {
        "status": "success",

        "records_processed": len(
            equipment_map
        ),

        "unique_equipment": len(
            equipment_map
        ),

        "top_priority_count": len(
            top_priority
        ),

        "algorithm": {
            "hash_map": "equipment_id → equipment information",
            "priority_queue": "Max Heap",
            "sorting": "Priority score descending",
        },

        "weights": WEIGHTS,

        "priority_list": top_priority,

        # Useful for explaining the DSA in the UI.
        "complexity": {
            "hash_map_lookup": "Average O(1)",
            "heap_insert": "O(log n)",
            "heap_pop": "O(log n)",
            "full_priority_order": "O(n log n)",
        },
    }


# ============================================================
# FILE-BASED ENTRY POINT
# ============================================================

def build_nexa_priority_from_file(
    file_path: str,
    top_n: int = 20,
) -> dict:

    """
    Read a CSV/XLSX equipment dataset and run NexaPriority.

    This makes NexaPriority work with uploaded hospital data.
    """

    path = Path(file_path)

    if not path.exists():

        return {
            "status": "unavailable",
            "message": "Equipment dataset file was not found.",
            "records_processed": 0,
            "priority_list": [],
        }

    try:

        extension = path.suffix.lower()

        if extension == ".csv":
            dataframe = pd.read_csv(path)

        elif extension == ".xlsx":
            dataframe = pd.read_excel(path)

        else:

            return {
                "status": "unavailable",
                "message": "Only CSV and XLSX equipment datasets are supported.",
                "records_processed": 0,
                "priority_list": [],
            }

        return build_nexa_priority(
            dataframe,
            top_n=top_n,
        )

    except Exception as error:

        return {
            "status": "error",
            "message": f"Equipment priority analysis failed: {error}",
            "records_processed": 0,
            "priority_list": [],
        }