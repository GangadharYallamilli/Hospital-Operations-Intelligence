document.addEventListener("DOMContentLoaded", async () => {
    renderDatasetIntelligence();

    const section = document.getElementById("predictionSection");
    if (!section) return;

    section.innerHTML = '<div class="predict-empty-state"><h3>Loading prediction results…</h3><p>Connecting to the existing prediction service.</p></div>';
    try {
        const response = await fetch("/ml-predictions", { credentials: "same-origin" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Prediction request failed.");
        if (data.status !== "success" || !data.predictions) throw new Error("No prediction results were returned.");
        renderPredictions(data.predictions, data.source);
    } catch (error) {
        renderPredictionMessage("Prediction service unavailable", error.message || "Unable to retrieve results from the ML service.");
    }
});

const PREDICTION_MODELS = [
    { key: "length_of_stay", label: "Length of stay", statusId: "lengthOfStayStatus", valueKeys: ["predicted_length_of_stay", "prediction"], unit: "days" },
    { key: "bed_forecast", label: "Bed demand", statusId: "bedDemandStatus", valueKeys: ["average_predicted_occupied_beds"], unit: "average occupied beds", period: (item) => `${item.forecast_days || (item.predictions || []).length} day forecast` },
    { key: "appointment_no_show", label: "Appointment no-show", statusId: "noShowStatus", valueKeys: ["predicted_no_show_probability", "no_show_probability", "risk"], unit: "" },
    { key: "equipment_failure", label: "Equipment failure risk", statusId: "equipmentStatus", valueKeys: ["risk"], unit: "" },
];

function renderPredictions(predictions, source) {
    const results = [];
    PREDICTION_MODELS.forEach((model) => {
        const result = predictions[model.key] || {};
        const valueKey = model.valueKeys.find((key) => result[key] !== undefined && result[key] !== null);
        const available = result.status === "success" && valueKey;
        updateModelStatus(model.statusId, available ? "Results available" : "Prediction unavailable");
        results.push({
            label: model.label,
            status: available ? "available" : "unavailable",
            value: available ? formatValue(result[valueKey], model.unit) : "Prediction unavailable",
            detail: available ? model.period?.(result) || result.prediction_period || result.forecast_month || "Returned by the trained model" : result.message || "No compatible trained model and data are available.",
        });
    });

    const admission = predictions.admission_forecast || {};
    const hasAdmission = admission.status === "success" && admission.predicted_admissions !== undefined;
    if (hasAdmission) {
        results.unshift({
            label: "Admission demand forecast",
            status: "available",
            value: formatValue(admission.predicted_admissions, "admissions"),
            detail: admission.forecast_month ? `Forecast period · ${admission.forecast_month}` : "Returned by the trained model",
        });
    }

    updateModelStatus("modelStatus", source ? `Dataset · ${source}` : results.some((item) => item.status === "available") ? "Trained model output available" : "No trained model output available");
    const section = document.getElementById("predictionSection");
    section.replaceChildren();
    const header = document.createElement("div");
    header.className = "prediction-results-header";
    const h = document.createElement("h3"); h.textContent = "Prediction model status";
    const badge = document.createElement("span"); badge.className = "prediction-live-status"; badge.textContent = source ? "CURRENT UPLOAD" : "MODEL AVAILABILITY";
    header.append(h, badge);
    const grid = document.createElement("div"); grid.className = "prediction-results-grid";
    results.forEach((item) => {
        const card = document.createElement("article"); card.className = `nexa-prediction-card ${item.status === "available" ? "is-available" : "is-unavailable"}`;
        const state = document.createElement("span"); state.className = "nexa-prediction-status"; state.textContent = item.status === "available" ? "MODEL OUTPUT" : "MODEL NOT AVAILABLE";
        const label = document.createElement("h3"); label.textContent = item.label;
        const value = document.createElement("strong"); value.textContent = item.value;
        const detail = document.createElement("p"); detail.textContent = item.detail;
        card.append(state, label, value, detail); grid.append(card);
    });
    section.append(header, grid);
}

function formatValue(value, unit) {
    const formatted = typeof value === "number" ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value) : String(value);
    return unit ? `${formatted} ${unit}` : formatted;
}

function updateModelStatus(id, text) { const node = document.getElementById(id); if (node) node.textContent = text; }
function renderPredictionMessage(title, message) {
    updateModelStatus("modelStatus", "Prediction service unavailable");
    const section = document.getElementById("predictionSection");
    if (!section) return;
    const state = document.createElement("div"); state.className = "predict-empty-state";
    const heading = document.createElement("h3"); heading.textContent = title;
    const copy = document.createElement("p"); copy.textContent = message;
    state.append(heading, copy); section.replaceChildren(state);
    PREDICTION_MODELS.forEach((model) => updateModelStatus(model.statusId, "Status unavailable"));
}


function renderDatasetIntelligence() {
    const grid = document.getElementById("datasetIntelligenceGrid");
    const status = document.getElementById("datasetIntelligenceStatus");

    if (!grid) return;

    try {
        const raw = sessionStorage.getItem("medanexaAnalyticsData");

        if (!raw) {
            grid.innerHTML = `
                <article class="predict-model-card">
                    <div class="predict-model-icon">DATA</div>
                    <div>
                        <h4>No analyzed dataset</h4>
                        <p>Upload and analyze a hospital dataset in Pulse to view current dataset intelligence.</p>
                    </div>
                </article>
            `;

            if (status) status.textContent = "No upload";
            return;
        }

        const data = JSON.parse(raw);
        const dashboard = data.dashboard || {};
        const kpis = dashboard.kpis || [];
        const charts = dashboard.charts || [];

        const cards = [];

        function findKpi(pattern) {
            return kpis.find((item) =>
                pattern.test(String(item.label || item.name || ""))
            );
        }

        function addKpi(pattern, label, unit = "") {
            const kpi = findKpi(pattern);

            if (!kpi) return;

            const value = kpi.value ?? kpi.metric;

            cards.push({
                label,
                value: formatDatasetValue(value, unit)
            });
        }

        addKpi(/total.*admission/i, "Total Admissions");
        addKpi(/average.*(los|length of stay)/i, "Average Length of Stay", "days");
        addKpi(/peak.*(los|length of stay)/i, "Peak Length of Stay", "days");
        addKpi(/unique.*patient/i, "Unique Patients");
        addKpi(/^departments?$/i, "Departments");

        const departmentChart = charts.find((chart) =>
            /admission.*department|department.*admission/i.test(
                String(chart.title || chart.dimension || "")
            )
        );

        if (departmentChart?.data?.length) {
            const sorted = departmentChart.data
                .filter((item) => Number.isFinite(Number(item.value)))
                .sort((a, b) => Number(b.value) - Number(a.value));

            if (sorted.length) {
                cards.push({
                    label: "Highest Department Workload",
                    value: `${sorted[0].label} — ${formatDatasetValue(sorted[0].value)}`
                });
            }
        }

        const fileName =
            dashboard.file_name ||
            data.file_name ||
            data?.analytics?.file_name ||
            "Current upload";

        if (status) {
            status.textContent = fileName;
        }

        if (!cards.length) {
            grid.innerHTML = `
                <article class="predict-model-card">
                    <div class="predict-model-icon">DATA</div>
                    <div>
                        <h4>No dataset metrics available</h4>
                        <p>The current upload does not contain recognized analytics for this section.</p>
                    </div>
                </article>
            `;
            return;
        }

        grid.replaceChildren();

        cards.forEach((item) => {
            const card = document.createElement("article");
            card.className = "predict-model-card";

            const icon = document.createElement("div");
            icon.className = "predict-model-icon";
            icon.textContent = "DATA";

            const content = document.createElement("div");

            const title = document.createElement("h4");
            title.textContent = item.label;

            const value = document.createElement("p");
            value.className = "dataset-intelligence-value";
            value.textContent = item.value;

            content.append(title, value);
            card.append(icon, content);

            grid.append(card);
        });

    } catch (error) {
        console.error("Could not render dataset intelligence.", error);

        grid.innerHTML = `
            <article class="predict-model-card">
                <div class="predict-model-icon">DATA</div>
                <div>
                    <h4>Dataset intelligence unavailable</h4>
                    <p>The current analyzed dataset could not be read.</p>
                </div>
            </article>
        `;
    }
}

function formatDatasetValue(value, unit = "") {
    let formatted;

    if (typeof value === "number" && Number.isFinite(value)) {
        formatted = new Intl.NumberFormat(undefined, {
            maximumFractionDigits: 2
        }).format(value);
    } else {
        formatted = value === null || value === undefined || value === ""
            ? "—"
            : String(value);
    }

    return unit ? `${formatted} ${unit}` : formatted;
}

// ============================================================
// NEXA PRIORITY
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    loadNexaPriority();
});


async function loadNexaPriority() {

    const status = document.getElementById(
        "nexaPriorityStatus"
    );

    const tableBody = document.getElementById(
        "nexaPriorityTableBody"
    );

    if (!tableBody) {
        return;
    }

    try {

        if (status) {
            status.textContent = "Loading…";
        }

        const response = await fetch(
            "/nexa-priority?top_n=20",
            {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json"
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Unable to load equipment priorities."
            );
        }

        if (
            data.status !== "success" ||
            !Array.isArray(data.priority_list)
        ) {
            throw new Error(
                "No NexaPriority results were returned."
            );
        }

        renderNexaPriority(
            data.priority_list,
            data.records
        );

    } catch (error) {

        console.error(
            "NexaPriority error:",
            error
        );

        if (status) {
            status.textContent =
                "Priority service unavailable";
        }

        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="nexa-priority-error">
                    ${escapeNexaPriorityHtml(
                        error.message ||
                        "Unable to load maintenance priorities."
                    )}
                </td>
            </tr>
        `;
    }
}


function renderNexaPriority(
    priorityList,
    records
) {

    const status = document.getElementById(
        "nexaPriorityStatus"
    );

    const tableBody = document.getElementById(
        "nexaPriorityTableBody"
    );

    if (!tableBody) {
        return;
    }

    tableBody.replaceChildren();

    if (!priorityList.length) {

        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="nexa-priority-empty">
                    No equipment priority records are available.
                </td>
            </tr>
        `;

        if (status) {
            status.textContent = "No equipment data";
        }

        return;
    }

    priorityList.forEach(
        (equipment, index) => {

            const row =
                document.createElement("tr");

            const rank =
                document.createElement("td");

            rank.className =
                "nexa-priority-rank";

            rank.textContent =
                String(index + 1);


            const equipmentId =
                document.createElement("td");

            equipmentId.className =
                "nexa-priority-id";

            equipmentId.textContent =
                equipment.equipment_id ||
                "—";


            const equipmentType =
                document.createElement("td");

            equipmentType.textContent =
                equipment.equipment_type ||
                "—";


            const score =
                document.createElement("td");

            score.className =
                "nexa-priority-score";

            score.textContent =
                formatNexaPriorityScore(
                    equipment.priority_score
                );


            const level =
                document.createElement("td");

            const badge =
                document.createElement("span");

            badge.className =
                `nexa-priority-badge ${getNexaPriorityClass(
                    equipment.priority_level
                )}`;

            badge.textContent =
                equipment.priority_level ||
                "Unknown";

            level.appendChild(badge);


            row.append(
                rank,
                equipmentId,
                equipmentType,
                score,
                level
            );

            tableBody.appendChild(row);
        }
    );

    if (status) {

        status.textContent =
            `${priorityList.length} of ${records || "available"} equipment records`;
    }
}


function formatNexaPriorityScore(
    value
) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toFixed(2);
}


function getNexaPriorityClass(
    level
) {

    const normalized =
        String(level || "")
            .toLowerCase()
            .replace(/\s+/g, "-");

    if (normalized === "critical") {
        return "is-critical";
    }

    if (normalized === "high") {
        return "is-high";
    }

    if (normalized === "medium") {
        return "is-medium";
    }

    if (normalized === "low") {
        return "is-low";
    }

    return "is-default";
}


function escapeNexaPriorityHtml(
    value
) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}