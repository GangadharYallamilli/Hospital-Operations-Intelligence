import math

import pandas as pd

from backend.analytics import resolve_column
from backend.data_understanding import load_dataset


def _safe_number(value):
    try:
        number = float(value)
        if not math.isfinite(number):
            return None
        return round(number, 2)
    except (TypeError, ValueError):
        return None


def _safe_text(value):
    if pd.isna(value):
        return "Unknown"
    return str(value)


def _chart(title, chart_type, categories, values, dimension, metric, *, primary=False, unit=None):
    points = [
        {"label": str(label), "value": _safe_number(value)}
        for label, value in zip(categories, values)
        if _safe_number(value) is not None
    ]
    return {
        "id": title.lower().replace(" ", "-"),
        "title": title,
        "type": chart_type,
        "dimension": dimension,
        "metric": metric,
        "unit": unit,
        "primary": primary,
        "data": points,
    }


def _group(frame, dimension, metric, aggregation="sum", title=None, chart_type="bar", unit=None):
    if not dimension or dimension not in frame.columns:
        return None
    working = frame[[dimension] + ([metric] if metric else [])].copy()
    working[dimension] = working[dimension].map(_safe_text)
    if metric:
        if aggregation != "count":
            working[metric] = pd.to_numeric(working[metric], errors="coerce")
        grouped = working.groupby(dimension, dropna=False)[metric].agg(aggregation).reset_index()
    else:
        grouped = working.groupby(dimension, dropna=False).size().reset_index(name="records")
    value_column = metric if metric else "records"
    grouped = grouped.dropna(subset=[value_column]).sort_values(value_column, ascending=False).head(12)
    if grouped.empty:
        return None
    return _chart(title or f"{dimension.replace('_', ' ').title()} breakdown", chart_type, grouped[dimension], grouped[value_column], dimension, value_column, unit=unit)


def _time_chart(frame, date_column, module, roles):
    if not date_column:
        return None
    dates = pd.to_datetime(frame[date_column], errors="coerce")
    if dates.notna().sum() < 2:
        return None
    measure = None
    aggregation = "size"
    metric_label = "records"
    if module == "Admission Analytics":
        measure = roles["admission_count"]
        aggregation = "sum"
        metric_label = "admissions"
    elif module == "Appointment Analytics":
        measure = roles["appointment_count"]
        aggregation = "sum"
        metric_label = "appointments"
    elif module == "Bed & Capacity Analytics":
        measure = roles["occupied_beds"] or roles["occupancy_rate"] or roles["available_beds"] or roles["total_beds"]
        aggregation = "mean" if measure == roles["occupancy_rate"] else "sum"
        metric_label = "occupancy_rate" if measure == roles["occupancy_rate"] else "available_beds" if measure == roles["available_beds"] else "total_beds" if measure == roles["total_beds"] else "occupied_beds"
    elif module == "Equipment Analytics" and roles["failure_count"]:
        measure = roles["failure_count"]
        aggregation = "sum"
        metric_label = "failures"
    elif module == "Equipment Analytics" and roles["failure_event"]:
        measure = roles["failure_event"]
        aggregation = "sum"
        metric_label = "failures"
    if measure:
        if module == "Equipment Analytics" and measure == roles["failure_event"]:
            values = frame[measure].notna().astype("int64")
        else:
            values = pd.to_numeric(frame[measure], errors="coerce")
    else:
        values = pd.Series(1, index=frame.index, dtype="int64")
        aggregation = "sum"
    work = pd.DataFrame({"date": dates, "value": values}).dropna()
    if work.empty:
        return None
    date_span = int((work["date"].max().normalize() - work["date"].min().normalize()).days)
    if date_span > 90:
        work["period"] = work["date"].dt.to_period("M").dt.to_timestamp()
        dimension = "month"
    elif date_span > 31:
        work["period"] = work["date"].dt.to_period("W-SUN").dt.start_time
        dimension = "week"
    else:
        work["period"] = work["date"].dt.normalize()
        dimension = "date"
    grouped = work.groupby("period")["value"].agg(aggregation).reset_index().sort_values("period")
    grouped = grouped.tail(120)
    if len(grouped) < 2:
        return None
    return _chart(f"{metric_label.replace('_', ' ').title()} over time", "line", grouped["period"].dt.strftime("%Y-%m-%d"), grouped["value"], dimension, metric_label, primary=True)


def _roles(columns):
    roles = {}
    for name in (
        "date", "department", "admission_id", "admission_count", "admission_type",
        "appointment_id", "appointment_count", "appointment_status", "length_of_stay",
        "wait_time", "patient_id", "occupied_beds", "total_beds", "available_beds",
        "occupancy_rate", "equipment_id", "equipment_type", "equipment_status",
        "failure_count", "failure_event", "maintenance_count", "usage_hours", "department_type", "service",
    ):
        roles[name] = resolve_column(columns, name)
    if not roles["failure_event"]:
        roles["failure_event"] = next((column for column in columns if "fail" in column and any(token in column for token in ("date", "event", "type", "id"))), None)
    return roles


def _prediction_config(modules, predictions, charts):
    configured = []
    specs = (
        ("Admission Analytics", "length_of_stay", "Length-of-stay prediction", "predicted_length_of_stay", None),
        ("Admission Analytics", "admission_forecast", "Admission demand forecast", "admissions", "forecast_month"),
        ("Bed & Capacity Analytics", "bed_forecast", "Bed demand forecast", "predicted_occupied_beds", "forecast_days"),
        ("Appointment Analytics", "appointment_no_show", "Appointment no-show prediction", "predicted_no_show_probability", None),
        ("Equipment Analytics", "equipment_failure", "Equipment failure risk", "risk", None),
    )
    for module, key, title, value_key, period_key in specs:
        if module not in modules:
            continue
        result = predictions.get(key) if isinstance(predictions, dict) else None
        if isinstance(result, dict) and not result.get("error") and result.get("status") not in {"unavailable", "model_not_found", "prediction_error"}:
            actual_value = (
                result.get("predicted_admissions") if key == "admission_forecast"
                else result.get("average_predicted_occupied_beds") if key == "bed_forecast"
                else result.get("predicted_length_of_stay") if key == "length_of_stay"
                else result.get("predicted_no_show_probability") if key == "appointment_no_show"
                else result.get("risk")
            )
            if actual_value is not None:
                period = result.get(period_key) if period_key else None
                if key == "admission_forecast":
                    period_text = f"Forecast period: {period}." if period else "Period returned by the model."
                elif key == "bed_forecast":
                    period_text = f"Forecast period: {result.get('forecast_days', len(result.get('predictions', [])))} days."
                elif key == "length_of_stay":
                    period_text = "Predicted length of stay in days, returned by the trained model."
                elif key == "appointment_no_show":
                    period_text = "Predicted no-show probability returned by the trained model."
                else:
                    period_text = "Risk classification returned by the trained model."
                configured.append({"id": key, "title": title, "status": "available", "value": actual_value, "period": period_text, "source": "Configured trained model"})
                history = result.get("history") or []
                future = result.get("predictions") or []
                if key == "admission_forecast" and history and period:
                    forecast_value = result.get("predicted_admissions")
                    future = future or [{"date": f"{period}-01", "predicted_admissions": forecast_value}]
                    historical = [{"label": item.get("date"), "value": _safe_number(item.get("admissions"))} for item in history if item.get("date") and _safe_number(item.get("admissions")) is not None]
                    predicted = [{"label": item.get("date"), "value": _safe_number(item.get("predicted_admissions"))} for item in future if item.get("date") and _safe_number(item.get("predicted_admissions")) is not None]
                    if historical and predicted:
                        charts.append({
                            "id": "admission-forecast",
                            "title": "Admissions: historical and forecast",
                            "type": "line",
                            "dimension": "date",
                            "metric": "admissions",
                            "primary": True,
                            "prediction": True,
                            "series": [{"name": "Historical", "kind": "historical", "data": historical}, {"name": "Forecast", "kind": "forecast", "data": predicted}],
                        })
                if key == "bed_forecast" and history and future:
                    historical = [{"label": item.get("date"), "value": _safe_number(item.get("occupied_beds"))} for item in history if item.get("date") and _safe_number(item.get("occupied_beds")) is not None]
                    predicted = [{"label": item.get("date"), "value": _safe_number(item.get("predicted_occupied_beds"))} for item in future if item.get("date") and _safe_number(item.get("predicted_occupied_beds")) is not None]
                    if historical and predicted:
                        charts.append({
                            "id": "bed-forecast",
                            "title": "Occupied beds: historical and forecast",
                            "type": "line",
                            "dimension": "date",
                            "metric": "occupied_beds",
                            "primary": True,
                            "prediction": True,
                            "series": [{"name": "Historical", "kind": "historical", "data": historical}, {"name": "Forecast", "kind": "forecast", "data": predicted}],
                        })
        else:
            configured.append({
                "id": key,
                "title": title,
                "status": "unavailable",
                "message": (
                    result.get("message") if isinstance(result, dict) and result.get("message")
                    else "Prediction unavailable. A compatible trained model and sufficient data in this upload are required."
                ),
            })
    return configured


def _insights_and_recommendations(analytics, charts, modules):
    insights = []
    recommendations = []
    for chart in charts:
        if chart.get("type") == "line" and chart.get("data"):
            values = [point["value"] for point in chart["data"] if point.get("value") is not None]
            if len(values) >= 2:
                first, last = values[0], values[-1]
                direction = "increased" if last > first else "decreased" if last < first else "was unchanged"
                if direction == "was unchanged":
                    sentence = f"{chart['title']} was unchanged across the displayed period ({last:g} at both endpoints)."
                else:
                    sentence = f"{chart['title']} {direction} from {first:g} to {last:g} across the displayed period."
                insights.append({"title": "Observed trend", "text": sentence, "source": chart["title"]})
        elif chart.get("dimension") in {"department", "department_id", "department_name", "dept_id", "dept_name"} and chart.get("data"):
            top = chart["data"][0]
            insights.append({"title": "Highest department workload", "text": f"{top['label']} has the highest recorded {chart['metric'].replace('_', ' ')} ({top['value']:g}) in this upload.", "source": chart["title"]})
            recommendations.append({"title": "Review department capacity", "text": f"Review staffing and capacity for {top['label']} against its recorded workload of {top['value']:g}.", "source": chart["title"]})
        elif chart.get("title") == "Appointment status" and chart.get("data"):
            no_show = next((point for point in chart["data"] if point["label"].strip().lower().replace("-", " ").replace("_", " ") in {"no show", "no shows", "missed"}), None)
            if no_show and no_show["value"] > 0:
                insights.append({"title": "Missed appointments recorded", "text": f"The upload records {no_show['value']:g} no-show or missed appointments.", "source": chart["title"]})
                recommendations.append({"title": "Review appointment follow-up", "text": f"Review reminder and follow-up workflows in light of the {no_show['value']:g} no-show or missed appointments recorded.", "source": chart["title"]})
    if "Bed & Capacity Analytics" in modules:
        occupancy = next((item for item in analytics.get("kpis", []) if "occupancy" in str(item.get("label", "")).lower()), None)
        if occupancy:
            value_text = str(occupancy.get("value", ""))
            insights.append({"title": "Bed utilization", "text": f"Recorded bed occupancy is {value_text}.", "source": occupancy["label"]})
            recommendations.append({"title": "Review bed capacity", "text": f"Review bed availability alongside the recorded occupancy of {value_text}.", "source": occupancy["label"]})
    if "Equipment Analytics" in modules:
        failures = next((item for item in analytics.get("kpis", []) if "failure" in str(item.get("label", "")).lower()), None)
        if failures and _safe_number(str(failures.get("value", "")).replace(",", "")) and float(str(failures["value"]).replace(",", "")) > 0:
            insights.append({"title": "Equipment failures recorded", "text": f"The upload records {failures['value']} equipment failures.", "source": failures["label"]})
            recommendations.append({"title": "Review recorded failures", "text": "Review equipment records associated with the recorded failures.", "source": failures["label"]})
    if not insights:
        names = ", ".join(module.replace(" Analytics", "") for module in modules) if modules else "general dataset"
        insights.append({"title": "Dataset coverage", "text": f"The uploaded file contains {names} data. No further pattern was generated from the available fields.", "source": "Dataset profile"})
    return insights[:6], recommendations[:6]


def build_dashboard_config(file_path, understanding, analytics, predictions=None):
    frame = load_dataset(file_path)
    columns = list(frame.columns)
    roles = _roles(columns)
    modules = understanding.get("available_modules") or analytics.get("available_modules") or []
    predictions = predictions or {}
    charts = []
    used = set()

    module_order = ["Admission Analytics", "Appointment Analytics", "Bed & Capacity Analytics", "Equipment Analytics"]
    date_candidates = {
        "Admission Analytics": ("admission_date", "admit_date", "admitted_at", "date_of_admission"),
        "Appointment Analytics": ("appointment_date", "scheduled_date", "appt_date"),
        "Bed & Capacity Analytics": ("record_date", "bed_date", "date"),
        "Equipment Analytics": ("record_date", "inspection_date", "service_date", "date"),
    }
    for module in module_order:
        if module not in modules:
            continue
        module_date = next((name for name in date_candidates[module] if name in columns), roles["date"])
        time_chart = _time_chart(frame, module_date, module, roles)
        if time_chart and time_chart["id"] not in used:
            charts.append(time_chart)
            used.add(time_chart["id"])

    if "Admission Analytics" in modules:
        if roles["department"]:
            chart = _group(frame, roles["department"], roles["admission_count"], "sum", "Admissions by Department", "bar", "admissions") if roles["admission_count"] else _group(frame, roles["department"], roles["admission_id"], "count", "Admissions by Department", "bar", "admissions") if roles["admission_id"] else _group(frame, roles["department"], None, title="Admissions by Department", unit="admissions")
            if chart:
                chart["metric"] = "admissions"
                charts.append(chart)
        if roles["admission_type"]:
            chart = _group(frame, roles["admission_type"], roles["admission_count"], "sum", "Admission type distribution", "donut", "admissions") if roles["admission_count"] else _group(frame, roles["admission_type"], None, title="Admission type distribution", chart_type="donut", unit="admissions")
            if chart:
                charts.append(chart)

    if "Appointment Analytics" in modules:
        if roles["appointment_status"]:
            chart = _group(frame, roles["appointment_status"], roles["appointment_count"], "sum", "Appointment status", "donut", "appointments") if roles["appointment_count"] else _group(frame, roles["appointment_status"], None, title="Appointment status", chart_type="donut", unit="appointments")
            if chart:
                charts.append(chart)
        if roles["department"]:
            chart = _group(frame, roles["department"], roles["appointment_count"], "sum", "Appointments by Department", "bar", "appointments") if roles["appointment_count"] else _group(frame, roles["department"], roles["appointment_id"], "count", "Appointments by Department", "bar", "appointments") if roles["appointment_id"] else _group(frame, roles["department"], None, title="Appointments by Department", unit="appointments")
            if chart:
                chart["metric"] = "appointments"
                charts.append(chart)
        if roles["service"]:
            service_count = frame[roles["service"]].nunique(dropna=True)
            service_chart_type = "donut" if service_count <= 8 else "bar"
            chart = _group(frame, roles["service"], roles["appointment_count"], "sum", "Appointments by Service", service_chart_type, "appointments") if roles["appointment_count"] else _group(frame, roles["service"], roles["appointment_id"], "count", "Appointments by Service", service_chart_type, "appointments") if roles["appointment_id"] else _group(frame, roles["service"], None, title="Appointments by Service", chart_type=service_chart_type, unit="appointments")
            if chart:
                chart["metric"] = "appointments"
                charts.append(chart)

    if "Bed & Capacity Analytics" in modules:
        bed_metric = roles["occupied_beds"] or roles["occupancy_rate"] or roles["available_beds"]
        if roles["department"] and bed_metric:
            bed_aggregation = "mean"
            bed_title = "Average occupancy by Department" if bed_metric == roles["occupancy_rate"] else "Average occupied beds by Department" if bed_metric == roles["occupied_beds"] else "Average available beds by Department"
            chart = _group(frame, roles["department"], bed_metric, bed_aggregation, bed_title, "bar", "percent" if bed_metric == roles["occupancy_rate"] else "beds")
            if chart:
                charts.append(chart)

    if "Equipment Analytics" in modules:
        if roles["equipment_status"]:
            chart = _group(frame, roles["equipment_status"], None, title="Equipment status", chart_type="donut", unit="equipment")
            if chart:
                charts.append(chart)
        if roles["equipment_type"] and (roles["failure_count"] or roles["failure_event"]):
            if roles["failure_count"]:
                chart = _group(frame, roles["equipment_type"], roles["failure_count"], "sum", "Recorded failures by equipment type", "bar", "failures")
            else:
                failure_rows = frame.loc[frame[roles["failure_event"]].notna()]
                chart = _group(failure_rows, roles["equipment_type"], None, title="Recorded failures by equipment type", chart_type="bar", unit="failures")
            if chart:
                charts.append(chart)

    if "Department Analytics" in modules and roles["department"] and not any("Department" in chart["title"] for chart in charts):
        chart = _group(frame, roles["department"], None, title="Department records", chart_type="bar", unit="records")
        if chart:
            charts.append(chart)

    # Do not render an arbitrary high-cardinality or person-level categorical field as a chart.
    if not charts:
        for column in columns:
            if any(token in column for token in ("patient", "name", "email", "mrn", "_id", "identifier")):
                continue
            if not (pd.api.types.is_object_dtype(frame[column]) or pd.api.types.is_categorical_dtype(frame[column])):
                continue
            distinct = frame[column].nunique(dropna=True)
            if 2 <= distinct <= 8:
                chart = _group(frame, column, None, title=f"{column.replace('_', ' ').title()} distribution", chart_type="donut")
                if chart:
                    charts.append(chart)
                    break

    predictions_list = _prediction_config(modules, predictions, charts)
    insights, recommendations = _insights_and_recommendations(analytics, charts, modules)
    tables = list(analytics.get("tables") or [])
    sensitive_tokens = ("patient", "mrn", "ssn", "email", "phone", "address", "date_of_birth", "dob", "first_name", "last_name")
    preview_columns = [column for column in columns if not any(token in column for token in sensitive_tokens)][:12]
    preview_rows = []
    for record in frame[preview_columns].head(8).to_dict(orient="records"):
        preview_rows.append({str(key): None if pd.isna(value) else value.isoformat() if hasattr(value, "isoformat") else value.item() if hasattr(value, "item") else value for key, value in record.items()})
    if preview_rows:
        tables.append({"title": "Dataset preview", "columns": preview_columns, "rows": preview_rows})

    filter_config = []
    if any(chart.get("type") == "line" and not chart.get("prediction") for chart in charts):
        filter_config.append({"id": "timeRange", "label": "Time range", "options": [{"value": "all", "label": "All available"}, {"value": "90", "label": "Last 90 days"}, {"value": "30", "label": "Last 30 days"}]})

    return {
        "version": 1,
        "title": "Hospital operations overview",
        "file_name": understanding.get("file_name"),
        "available_modules": modules,
        "kpis": analytics.get("kpis") or [],
        "charts": charts,
        "tables": tables,
        "predictions": predictions_list,
        "insights": insights,
        "recommendations": recommendations,
        "filters": filter_config,
        "data_profile": understanding.get("profile") or {},
    }
