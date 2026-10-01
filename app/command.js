document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("refreshCommandButton")?.addEventListener("click", loadCommand);
    loadCommand();
});

async function loadCommand() {
    const status = document.getElementById("commandStatus");
    const priorities = document.getElementById("commandPriorities");
    const forecasts = document.getElementById("commandForecasts");
    const sources = document.getElementById("commandSources");
    const refresh = document.getElementById("refreshCommandButton");
    refresh.disabled = true;
    status.textContent = "Loading available intelligence…";
    try {
        const [contextResponse, docsResponse] = await Promise.all([
            fetch("/workspace/context", { credentials: "same-origin" }),
            fetch("/documents/", { credentials: "same-origin" })
        ]);
        const [context, docs] = await Promise.all([readJson(contextResponse), readJson(docsResponse)]);
        if (!contextResponse.ok) throw new Error(context.detail || "Could not load workspace intelligence.");
        renderCommand(context, docs.documents || [], priorities, forecasts, sources);
        const sourceState = context.database_analytics?.status === "success" ? "Hospital database analytics are connected." : "Structured hospital database analytics are unavailable.";
        status.textContent = (context.analysis ? `Updated from ${context.analysis.file_name || "the analyzed dataset"}. ` : "No Pulse dataset has been analyzed in this session. ") + sourceState;
    } catch (error) {
        status.textContent = error.message || "Could not load available intelligence.";
        status.className = "command-status error";
    } finally { refresh.disabled = false; }
}

function renderCommand(context, documents, priorities, forecasts, sources) {
    priorities.replaceChildren(); forecasts.replaceChildren(); sources.replaceChildren();
    const analysis = context.analysis;
    const dashboard = context.dashboard || analysis?.dashboard || {};
    const analytics = analysis?.analytics || {};
    const profile = analysis?.understanding?.profile || {};
    (dashboard.insights || []).slice(0, 3).forEach((item) => {
        addCard(priorities, item.title || "Observed in dataset", item.text || "", "Source: " + (item.source || "NexaSight analytics"));
    });
    (dashboard.recommendations || []).slice(0, 3).forEach((item) => {
        addCard(priorities, item.title || "Suggested action", item.text || "", "Source: " + (item.source || "NexaSight analytics"));
    });
    if (analysis) {
        addCard(priorities, "Dataset overview", `${analysis.file_name || "Uploaded dataset"} · ${formatNumber(profile.rows)} rows · ${formatNumber(profile.columns)} columns`, "Source: Pulse dataset analysis");
        (analytics.kpis || []).forEach((kpi) => {
            const label = kpi.label || kpi.name || "Metric";
            addCard(priorities, label, String(kpi.value ?? kpi.metric ?? "—"), "Measured in the analyzed dataset");
        });
        (analytics.tables || []).forEach((table) => {
            const title = table.title || table.name || "Analysis table";
            const columns = table.columns || table.headers || [];
            const rows = table.rows || table.data || [];
            const firstRows = rows.slice(0, 3).map((row) => Array.isArray(row) ? row.join(" · ") : Object.values(row || {}).join(" · ")).join("\n");
            addCard(priorities, title, firstRows || `${rows.length} result row(s)`, "See the full analysis in NexaSight");
        });
    } else addCard(priorities, "Dataset analysis", "No analyzed dataset is available.", "Upload a CSV or XLSX file in Pulse to generate operational metrics.");

    const database = context.database_analytics || {};
    if (database.status === "success") {
        (database.kpis || []).forEach((kpi) => addCard(priorities, kpi.label || "Database metric", String(kpi.value ?? "—"), "Source: Hospital operational database"));
        const admissionsChart = (database.charts || []).find((chart) => chart.id === "db-admissions-by-department");
        const leaders = (admissionsChart?.data || []).filter((point) => point.label !== null && Number.isFinite(Number(point.value))).sort((a, b) => Number(b.value) - Number(a.value));
        if (leaders.length) addCard(priorities, "Highest admissions department", `${leaders[0].label} · ${formatNumber(leaders[0].value)} admissions`, "Source: shared MySQL analytics also shown in NexaSight and used by NexaCopilot");
        addCard(sources, "SQL analytics source", database.source || "Hospital operational database", "Shared read-only queries power NexaSight, NexaCopilot, and NexaCommand.");
    } else {
        addCard(sources, "SQL analytics source", "Unavailable", database.message || "Configure MYSQL_READONLY_USER and MYSQL_READONLY_PASSWORD for hospital database analytics.");
    }

    const predictions = context.predictions || {};
    let availableCount = 0;
    const admission = predictions.admission_forecast;
    if (admission?.status === "success" && admission.predicted_admissions !== undefined) {
        availableCount++;
        addCard(forecasts, "Admission forecast", `${admission.predicted_admissions} predicted admissions`, admission.forecast_month ? `Forecast period: ${admission.forecast_month}` : "Returned by the trained model");
    } else if (admission) addModelUnavailable(forecasts, "Admission forecast", admission);
    const los = predictions.length_of_stay;
    if (los?.status === "success" && (los.predicted_length_of_stay !== undefined || los.prediction !== undefined)) {
        availableCount++;
        addCard(forecasts, "Length-of-stay prediction", `${los.predicted_length_of_stay ?? los.prediction} days`, los.prediction_period || "Returned by the trained model");
    } else addModelUnavailable(forecasts, "Length-of-stay prediction", los);
    const beds = predictions.bed_forecast;
    if (beds?.status === "success" && beds.average_predicted_occupied_beds !== undefined) {
        availableCount++;
        addCard(forecasts, "Bed demand", `${beds.average_predicted_occupied_beds} average occupied beds`, `${beds.forecast_days || (beds.predictions || []).length} day forecast`);
    } else addModelUnavailable(forecasts, "Bed demand forecast", beds);
    const noShow = predictions.appointment_no_show;
    const noShowValue = noShow?.predicted_no_show_probability ?? noShow?.no_show_probability ?? noShow?.risk;
    if (noShow?.status === "success" && noShowValue !== undefined) {
        availableCount++;
        addCard(forecasts, "Appointment no-show prediction", String(noShowValue), noShow.prediction_period || "Returned by the trained model");
    } else addModelUnavailable(forecasts, "Appointment no-show prediction", noShow);
    const equipment = predictions.equipment_failure;
    if (equipment?.risk && equipment.status === "success") {
        availableCount++;
        addCard(forecasts, "Equipment risk", equipment.risk, "Returned by the equipment prediction model");
    } else addModelUnavailable(forecasts, "Equipment failure risk", equipment);
    if (availableCount) addCard(forecasts, "Model output count", String(availableCount), "Real predictions returned for the current analysis.");

    if (analysis) addCard(sources, "Dataset source", analysis.file_name || "Uploaded dataset", `${formatNumber(profile.rows)} rows · ${formatNumber(profile.columns)} columns`);
    const ragDocuments = documents.filter((doc) => ["pdf", "docx"].includes(String(doc.file_type).toLowerCase()));
    ragDocuments.forEach((doc) => addCard(sources, displayName(doc.file_name), String(doc.file_type).toUpperCase(), "Available through NexaDocs document retrieval"));
    if (!analysis && !ragDocuments.length) addCard(sources, "No connected sources", "No dataset or processed report is available.", "Upload data in Pulse or a PDF/DOCX report in NexaDocs.");
}

function addModelUnavailable(container, title, result) {
    addCard(container, title, "Prediction unavailable", result?.message || "No compatible trained model and data are available for this prediction.");
}

function addCard(container, title, value, detail) {
    const card = document.createElement("article"); card.className = "command-card";
    const heading = document.createElement("span"); heading.className = "section-label"; heading.textContent = title;
    const main = document.createElement("strong"); main.className = "command-card-value"; main.textContent = value;
    const note = document.createElement("p"); note.textContent = detail;
    card.append(heading, main, note); container.append(card);
}
function formatNumber(value) { return value === undefined || value === null ? "—" : new Intl.NumberFormat().format(Number(value)); }
function displayName(name) { return String(name || "Document").replace(/^[0-9a-f]{8}-[0-9a-f-]{27}_/i, ""); }
async function readJson(response) { try { return await response.json(); } catch { return {}; } }
