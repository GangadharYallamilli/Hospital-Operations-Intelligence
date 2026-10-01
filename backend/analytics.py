import math

import pandas as pd

from backend.data_understanding import detect_modules, load_dataset


ALIASES = {
    "date": ("admission_date", "appointment_date", "record_date", "date", "event_date", "service_date", "timestamp", "datetime"),
    "department": ("department_id", "department_name", "department", "dept_id", "dept_name", "dept"),
    "admission_id": ("admission_id", "admission_number", "admission_no", "encounter_id"),
    "admission_count": ("admission_count", "total_admissions", "number_of_admissions", "admissions"),
    "admission_type": ("admission_type", "admit_type", "admission_category"),
    "appointment_id": ("appointment_id", "appointment_number", "appointment_no", "appt_id"),
    "appointment_count": ("appointment_count", "total_appointments", "number_of_appointments", "appointments"),
    "appointment_status": ("appointment_status", "appt_status", "status"),
    "length_of_stay": ("length_of_stay", "los_days", "stay_length", "length_stay"),
    "wait_time": ("wait_time_days", "wait_days", "waiting_time", "wait_time"),
    "patient_id": ("patient_id", "patient_number", "patient_no"),
    "total_beds": ("total_beds", "bed_capacity", "total_bed_count", "beds_available_total", "total_capacity"),
    "available_beds": ("available_beds", "beds_available", "available_bed_count", "available_capacity"),
    "occupied_beds": ("occupied_beds", "beds_occupied", "occupied_bed_count", "occupied", "occupied_capacity"),
    "occupancy_rate": ("occupancy_rate", "occupancy_percentage", "bed_occupancy_rate"),
    "equipment_id": ("equipment_id", "device_id", "asset_id"),
    "equipment_type": ("equipment_type", "device_type", "asset_type"),
    "equipment_status": ("equipment_status", "device_status", "operational_status"),
    "failure_count": ("failure_count", "failures", "number_of_failures"),
    "maintenance_count": ("maintenance_count", "maintenance_events"),
    "usage_hours": ("usage_hours", "hours_used"),
    "department_type": ("department_type", "dept_type"),
    "service": ("service", "service_line", "service_type", "clinic", "clinic_name", "specialty", "specialty_name", "appointment_service"),
}


def resolve_column(columns, role):
    names = [str(column) for column in columns]
    aliases = ALIASES.get(role, ())
    for alias in aliases:
        if alias in names:
            return alias
    patterns = {
        "admission_id": lambda name: any(token in name for token in ("admission", "admit", "encounter")) and (name.endswith("_id") or name.endswith("_number")),
        "admission_count": lambda name: "admission" in name and any(token in name for token in ("count", "total", "number")),
        "admission_type": lambda name: "admission" in name and any(token in name for token in ("type", "category")),
        "appointment_id": lambda name: any(token in name for token in ("appointment", "appt")) and (name.endswith("_id") or name.endswith("_number")),
        "appointment_count": lambda name: any(token in name for token in ("appointment", "appt")) and any(token in name for token in ("count", "total", "number")),
        "appointment_status": lambda name: any(token in name for token in ("appointment", "appt")) and any(token in name for token in ("status", "state")),
        "length_of_stay": lambda name: ("stay" in name and ("length" in name or "duration" in name)) or name in {"los", "los_days"},
        "wait_time": lambda name: "wait" in name and any(token in name for token in ("time", "day", "duration")),
        "patient_id": lambda name: "patient" in name and (name.endswith("_id") or name.endswith("_number")),
        "occupied_beds": lambda name: ("bed" in name and ("occup" in name or "occupied" in name)) or "occupied_capacity" in name,
        "total_beds": lambda name: ("bed" in name and any(token in name for token in ("total", "capacity"))) or ("capacity" in name and not any(token in name for token in ("available", "occupied"))),
        "available_beds": lambda name: ("bed" in name and "available" in name) or "available_capacity" in name,
        "occupancy_rate": lambda name: "occupancy" in name or ("utilization" in name and any(token in name for token in ("rate", "percent"))),
        "equipment_id": lambda name: any(token in name for token in ("equipment", "device", "asset")) and (name.endswith("_id") or name.endswith("_number")),
        "equipment_type": lambda name: any(token in name for token in ("equipment", "device", "asset")) and "type" in name,
        "equipment_status": lambda name: any(token in name for token in ("equipment", "device", "asset")) and any(token in name for token in ("status", "state", "condition")),
        "failure_count": lambda name: "fail" in name and (any(token in name for token in ("count", "total", "number", "quantity")) or name in {"failures", "equipment_failures"}),
        "maintenance_count": lambda name: "maint" in name and any(token in name for token in ("count", "event", "number")),
        "usage_hours": lambda name: any(token in name for token in ("usage", "used", "operating")) and "hour" in name,
        "department_type": lambda name: any(token in name for token in ("department", "dept")) and "type" in name,
        "service": lambda name: any(token in name for token in ("service", "clinic", "specialty")),
        "department": lambda name: "department" in name or name.startswith("dept_"),
        "date": lambda name: any(token in name for token in ("date", "timestamp", "datetime")),
    }
    matcher = patterns.get(role)
    if matcher:
        match = next((name for name in names if matcher(name)), None)
        if match:
            return match
    equipment_columns = any(any(token in name for token in ("equipment", "device", "asset")) for name in names)
    if role == "equipment_status" and equipment_columns:
        return next((name for name in names if name in {"status", "state", "condition"}), None)
    if role == "equipment_type" and equipment_columns:
        return next((name for name in names if name in {"type", "category"}), None)
    return None


def _number(value, digits=2):
    try:
        result = float(value)
        if not math.isfinite(result):
            return None
        rounded = round(result, digits)
        return int(rounded) if rounded.is_integer() else rounded
    except (TypeError, ValueError):
        return None


def _group_table(frame, dimension, value, title, aggregation="sum", metric_name=None):
    data = frame[[dimension] + ([value] if value else [])].copy()
    data[dimension] = data[dimension].fillna("Unknown").astype(str)
    if value:
        if aggregation != "count":
            data[value] = pd.to_numeric(data[value], errors="coerce")
        grouped = data.groupby(dimension, dropna=False)[value].agg(aggregation).reset_index(name=metric_name or value)
        if aggregation != "count":
            grouped[metric_name or value] = grouped[metric_name or value].map(_number)
    else:
        grouped = data.groupby(dimension, dropna=False).size().reset_index(name=metric_name or "records")
    grouped = grouped.sort_values(grouped.columns[-1], ascending=False).head(20)
    return {"title": title, "columns": list(grouped.columns), "rows": grouped.to_dict(orient="records")}


def _add_kpi(kpis, label, value):
    if value is not None and value != "":
        kpis.append({"label": label, "value": value})


def calculate_analytics(file_path):
    frame = load_dataset(file_path)
    columns = list(frame.columns)
    modules = detect_modules(frame)
    kpis = []
    tables = []
    date_col = resolve_column(columns, "date")
    department_col = resolve_column(columns, "department")
    admission_count = resolve_column(columns, "admission_count")
    appointment_count = resolve_column(columns, "appointment_count")
    admission_id = resolve_column(columns, "admission_id")
    appointment_id = resolve_column(columns, "appointment_id")

    if "Admission Analytics" in modules:
        count = _number(pd.to_numeric(frame[admission_count], errors="coerce").fillna(0).sum()) if admission_count else int(frame[admission_id].notna().sum()) if admission_id else int(len(frame))
        _add_kpi(kpis, "Total Admissions", count)
        los = resolve_column(columns, "length_of_stay")
        if los:
            values = pd.to_numeric(frame[los], errors="coerce").dropna()
            if not values.empty:
                _add_kpi(kpis, "Average Length of Stay", _number(values.mean()))
                _add_kpi(kpis, "Peak Length of Stay", _number(values.max()))
        patient = resolve_column(columns, "patient_id")
        if patient:
            _add_kpi(kpis, "Unique Patients", int(frame[patient].nunique(dropna=True)))
        kind = resolve_column(columns, "admission_type")
        if kind:
            tables.append(_group_table(frame, kind, admission_count, "Admissions by Type", metric_name="admissions") if admission_count else _group_table(frame, kind, None, "Admissions by Type", metric_name="admissions"))
        if department_col:
            tables.append(_group_table(frame, department_col, admission_count, "Admissions by Department", metric_name="admissions") if admission_count else _group_table(frame, department_col, admission_id, "Admissions by Department", "count", "admissions") if admission_id else _group_table(frame, department_col, None, "Admissions by Department", metric_name="admissions"))

    if "Appointment Analytics" in modules:
        count = _number(pd.to_numeric(frame[appointment_count], errors="coerce").fillna(0).sum()) if appointment_count else int(frame[appointment_id].notna().sum()) if appointment_id else int(len(frame))
        _add_kpi(kpis, "Total Appointments", count)
        status = resolve_column(columns, "appointment_status")
        if status:
            normalized = frame[status].fillna("").astype(str).str.strip().str.lower().str.replace(r"[^a-z]", "", regex=True)
            weights = pd.to_numeric(frame[appointment_count], errors="coerce").fillna(0) if appointment_count else pd.Series(1, index=frame.index)
            denominator = _number(weights.sum())
            no_show = _number(weights[normalized.isin(("noshow", "missed", "didnotattend"))].sum()) or 0
            completed = _number(weights[normalized.isin(("completed", "complete", "attended"))].sum()) or 0
            _add_kpi(kpis, "Completed Appointments", completed)
            _add_kpi(kpis, "No-Shows", no_show)
            if denominator:
                _add_kpi(kpis, "No-Show Rate", f"{no_show / float(denominator) * 100:.1f}%")
            tables.append(_group_table(frame, status, appointment_count, "Appointment Status", metric_name="appointments") if appointment_count else _group_table(frame, status, None, "Appointment Status", metric_name="appointments"))
        wait = resolve_column(columns, "wait_time")
        if wait:
            vals = pd.to_numeric(frame[wait], errors="coerce").dropna()
            _add_kpi(kpis, "Average Wait (days)", _number(vals.mean()))
        if department_col:
            tables.append(_group_table(frame, department_col, appointment_count, "Appointments by Department", metric_name="appointments") if appointment_count else _group_table(frame, department_col, appointment_id, "Appointments by Department", "count", "appointments") if appointment_id else _group_table(frame, department_col, None, "Appointments by Department", metric_name="appointments"))
        service = resolve_column(columns, "service")
        if service:
            tables.append(_group_table(frame, service, appointment_count, "Appointments by Service", metric_name="appointments") if appointment_count else _group_table(frame, service, appointment_id, "Appointments by Service", "count", "appointments") if appointment_id else _group_table(frame, service, None, "Appointments by Service", metric_name="appointments"))

    if "Bed & Capacity Analytics" in modules:
        occupied = resolve_column(columns, "occupied_beds")
        total = resolve_column(columns, "total_beds")
        available = resolve_column(columns, "available_beds")
        occupancy = resolve_column(columns, "occupancy_rate")
        bed_date = resolve_column(columns, "date")
        measured = {}
        if bed_date:
            dates = pd.to_datetime(frame[bed_date], errors="coerce")
            valid = frame.loc[dates.notna()].copy()
            valid["_bed_date"] = dates.loc[dates.notna()]
            daily = {}
            for role, column in (("occupied", occupied), ("total", total), ("available", available)):
                if column:
                    values = pd.to_numeric(valid[column], errors="coerce")
                    daily[role] = pd.DataFrame({"date": valid["_bed_date"], "value": values}).groupby("date")["value"].sum(min_count=1)
            if daily:
                daily_frame = pd.concat(daily, axis=1)
                for role in ("occupied", "total", "available"):
                    if role in daily_frame:
                        measured[role] = daily_frame[role].dropna()
                if "occupied" in measured and "total" in measured:
                    valid_capacity = daily_frame[["occupied", "total"]].dropna()
                    valid_capacity = valid_capacity[valid_capacity["total"] > 0]
                    measured["occupancy"] = valid_capacity["occupied"].div(valid_capacity["total"]).mul(100)
        for role, column, label in (
            ("total", total, "Average Bed Capacity"),
            ("occupied", occupied, "Average Occupied Beds"),
            ("available", available, "Average Available Beds"),
        ):
            values = measured.get(role)
            if values is None and column:
                values = pd.to_numeric(frame[column], errors="coerce").dropna()
            if values is not None and not values.empty:
                _add_kpi(kpis, label, _number(values.mean()))
        if not available and total and occupied:
            if "total" in measured and "occupied" in measured:
                avail_values = (measured["total"] - measured["occupied"]).dropna()
            else:
                avail_values = (pd.to_numeric(frame[total], errors="coerce") - pd.to_numeric(frame[occupied], errors="coerce")).dropna()
            if not avail_values.empty:
                _add_kpi(kpis, "Average Available Beds (derived)", _number(avail_values.mean()))
        if occupancy:
            occupancy_values = measured.get("occupancy")
            if occupancy_values is None:
                occupancy_values = pd.to_numeric(frame[occupancy], errors="coerce").dropna()
                if not occupancy_values.empty and occupancy_values.max() <= 1:
                    occupancy_values = occupancy_values * 100
            if occupancy_values is not None and not occupancy_values.empty:
                _add_kpi(kpis, "Average Occupancy", f"{_number(occupancy_values.mean())}%")
        elif "occupancy" in measured and not measured["occupancy"].empty:
            _add_kpi(kpis, "Average Occupancy (derived)", f"{_number(measured['occupancy'].mean())}%")
        if occupied:
            values = measured.get("occupied")
            if values is None:
                values = pd.to_numeric(frame[occupied], errors="coerce").dropna()
            if not values.empty:
                _add_kpi(kpis, "Peak Occupied Beds", _number(values.max()))
        if department_col and occupied:
            tables.append(_group_table(frame, department_col, occupied, "Average Occupied Beds by Department", "mean", "average_occupied_beds"))

    if "Equipment Analytics" in modules:
        equipment_id = resolve_column(columns, "equipment_id")
        equipment_status = resolve_column(columns, "equipment_status")
        equipment_type = resolve_column(columns, "equipment_type")
        failure = resolve_column(columns, "failure_count")
        failure_event = next((name for name in columns if "fail" in name and any(token in name for token in ("date", "event", "type", "id"))), None)
        _add_kpi(kpis, "Equipment Records", int(frame[equipment_id].nunique(dropna=True)) if equipment_id else int(len(frame)))
        if equipment_status:
            status_norm = frame[equipment_status].fillna("").astype(str).str.lower()
            operational = int(status_norm.str.contains("operational|active|working").sum())
            _add_kpi(kpis, "Operational Equipment", operational)
            tables.append(_group_table(frame, equipment_status, None, "Equipment Status", metric_name="equipment"))
        if failure:
            values = pd.to_numeric(frame[failure], errors="coerce").dropna()
            if not values.empty:
                _add_kpi(kpis, "Recorded Equipment Failures", _number(values.sum()))
        elif failure_event:
            _add_kpi(kpis, "Recorded Equipment Failures", int(frame[failure_event].notna().sum()))
        if equipment_type:
            tables.append(_group_table(frame, equipment_type, None, "Equipment by Type", metric_name="equipment"))

    if "Department Analytics" in modules and department_col:
        _add_kpi(kpis, "Departments", int(frame[department_col].nunique(dropna=True)))
        if not any("Department" in table.get("title", "") for table in tables):
            tables.append(_group_table(frame, department_col, None, "Department Workload", metric_name="records"))

    if not modules:
        _add_kpi(kpis, "Records", int(len(frame)))

    return {
        "dataset_type": modules[0].replace(" Analytics", "").lower() if len(modules) == 1 else ("hospital_operations" if modules else "general"),
        "available_modules": modules,
        "kpis": kpis,
        "tables": tables,
    }


def calculate_bed_analytics(file_path):
    result = calculate_analytics(file_path)
    if "Bed & Capacity Analytics" not in result.get("available_modules", []):
        return None
    kpis = {item["label"]: item["value"] for item in result.get("kpis", [])}
    def percent(value):
        try:
            return float(str(value).replace("%", "").replace(",", ""))
        except (TypeError, ValueError):
            return None
    occupancy_table = next((table for table in result.get("tables", []) if "Occupied Beds by Department" in table.get("title", "")), None)
    return {
        "total_beds": kpis.get("Average Bed Capacity", kpis.get("Average Daily Beds")),
        "occupied_beds": kpis.get("Average Occupied Beds"),
        "available_beds": kpis.get("Average Available Beds", kpis.get("Average Available Beds (derived)")),
        "average_occupancy": percent(kpis.get("Average Occupancy", kpis.get("Average Occupancy (derived)"))),
        "peak_occupied_beds": kpis.get("Peak Occupied Beds"),
        "department_occupancy": occupancy_table.get("rows", []) if occupancy_table else [],
    }
