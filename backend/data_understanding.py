import re
from pathlib import Path

import pandas as pd


def normalize_column_name(value):
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "unnamed"


def normalize_frame_columns(frame):
    names = []
    counts = {}
    for original in frame.columns:
        name = normalize_column_name(original)
        counts[name] = counts.get(name, 0) + 1
        names.append(name if counts[name] == 1 else f"{name}_{counts[name]}")
    frame.columns = names
    return frame


def load_dataset(file_path):
    path = str(file_path)
    if path.lower().endswith(".csv"):
        try:
            frame = pd.read_csv(path, low_memory=False)
        except UnicodeDecodeError:
            frame = pd.read_csv(path, encoding="latin-1", low_memory=False)
    elif path.lower().endswith(".xlsx"):
        frame = pd.read_excel(path)
    else:
        raise ValueError("Only CSV and XLSX datasets are supported.")
    if frame.empty:
        raise ValueError("The uploaded dataset has no rows.")
    return normalize_frame_columns(frame)


def _contains(columns, words):
    return [column for column in columns if any(word in column for word in words)]


def detect_modules(frame):
    columns = [normalize_column_name(c) for c in frame.columns]
    joined = " ".join(columns)
    modules = []

    admission_signals = _contains(columns, ("admission", "admit_date", "admitted", "length_of_stay", "los_days"))
    if admission_signals or any(c in columns for c in ("admissions", "admission_count", "total_admissions")):
        modules.append("Admission Analytics")

    appointment_signals = _contains(columns, ("appointment", "appt_", "no_show", "noshow"))
    if appointment_signals:
        modules.append("Appointment Analytics")

    bed_signals = _contains(columns, ("bed", "occupancy", "capacity"))
    if bed_signals and any(any(token in c for token in ("total", "occupied", "available", "occupancy", "capacity")) for c in bed_signals):
        modules.append("Bed & Capacity Analytics")

    equipment_identity = _contains(columns, ("equipment", "device", "asset"))
    equipment_signals = _contains(columns, ("failure", "maintenance", "usage"))
    equipment_attributes = _contains(columns, ("status", "state", "type", "condition", "failure", "maintenance", "usage"))
    if equipment_identity or equipment_signals or (equipment_identity and equipment_attributes):
        modules.append("Equipment Analytics")

    if _contains(columns, ("department", "dept_")):
        modules.append("Department Analytics")

    return modules


def profile_dataset(frame):
    dates = []
    for column in frame.columns:
        name = str(column).lower()
        if any(token in name for token in ("date", "time", "timestamp")):
            parsed = pd.to_datetime(frame[column], errors="coerce")
            if len(frame) and parsed.notna().mean() >= 0.7:
                dates.append(column)
    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "column_names": [str(c) for c in frame.columns],
        "data_types": {str(c): str(dtype) for c, dtype in frame.dtypes.items()},
        "missing_values": {str(c): int(value) for c, value in frame.isna().sum().items()},
        "duplicate_rows": int(frame.duplicated().sum()),
        "date_columns": dates,
        "numeric_columns": [str(c) for c in frame.select_dtypes(include="number").columns],
    }


def understand_dataset(file_path):
    frame = load_dataset(file_path)
    profile = profile_dataset(frame)
    modules = detect_modules(frame)
    return {
        "profile": profile,
        "available_modules": modules,
        "dataset_type": modules[0].replace(" Analytics", "").lower() if len(modules) == 1 else ("hospital operations" if modules else "general dataset"),
    }
