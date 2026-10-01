document.addEventListener("DOMContentLoaded", initializeNexaSight);

async function initializeNexaSight() {
    const container = document.getElementById("dynamicAnalytics");
    if (!container) return;
    const cached = sessionStorage.getItem("medanexaAnalyticsData");
    let analysis = null;
    try {
        analysis = cached ? JSON.parse(cached) : null;
    } catch (error) {
        console.error("Could not read saved dataset analysis.", error);
    }

    let context = {};
    try {
        const response = await fetch("/workspace/context", { credentials: "same-origin" });
        if (response.ok) {
            context = await response.json();
            if (context.analysis?.dashboard) {
                analysis = context.analysis;
                sessionStorage.setItem("medanexaAnalyticsData", JSON.stringify(analysis));
            }
        }
    } catch (error) {
        console.warn("Could not refresh workspace intelligence.", error);
    }

    if (!analysis?.dashboard) {
        renderEmpty(container);
        renderDatabaseAnalytics(container, context.database_analytics);
        return;
    }

    renderDashboard(container, analysis.dashboard, analysis);
    renderDatabaseAnalytics(container, context.database_analytics);
}

function renderEmpty(container) {
    container.innerHTML = '<div class="analytics-empty"><div class="analytics-empty-icon">＋</div><h3>No analysis available</h3><p>Upload a CSV or XLSX dataset in Pulse to create a dashboard from its available fields.</p><a href="/index.html" class="primary-button">Go to Pulse</a></div>';
}

function renderDashboard(container, dashboard, analysis) {
    const profile = dashboard.data_profile || analysis.understanding?.profile || {};
    const modules = dashboard.available_modules || analysis.understanding?.available_modules || [];
    const kpis = dashboard.kpis || analysis.analytics?.kpis || [];
    const charts = dashboard.charts || [];
    const tables = dashboard.tables || [];
    const predictions = dashboard.predictions || [];
    const insights = dashboard.insights || [];
    const recommendations = dashboard.recommendations || [];
    const filters = dashboard.filters || [];

    container.innerHTML = "";
    const header = document.createElement("section");
    header.className = "nexa-dashboard-overview";
    header.innerHTML = '<div class="nexa-dashboard-heading"><span class="analytics-eyebrow">LIVE DATASET DASHBOARD</span><h2>' + escapeHtml(dashboard.title || "Hospital operations overview") + '</h2><p>Visuals and operational signals are generated from the fields detected in this upload.</p><div class="nexa-module-chips">' + modules.map((module) => '<span>' + escapeHtml(formatLabel(module.replace(/ Analytics$/i, ""))) + '</span>').join("") + '</div></div><div class="nexa-dashboard-meta"><div><span>Dataset</span><strong>' + escapeHtml(dashboard.file_name || analysis.file_name || "Uploaded dataset") + '</strong></div><div><span>Rows</span><strong>' + formatNumber(profile.rows) + '</strong></div><div><span>Fields</span><strong>' + formatNumber(profile.columns) + '</strong></div><div><span>Duplicate rows</span><strong>' + formatNumber(profile.duplicate_rows ?? 0) + '</strong></div></div>';
    container.append(header);

    if (kpis.length) {
        const section = makeSection("Key measures", "KPIs calculated from available columns");
        const grid = document.createElement("div");
        grid.className = "analytics-kpi-grid";
        kpis.forEach((kpi) => {
            const card = document.createElement("article");
            card.className = "analytics-kpi-card";
            card.innerHTML = '<span class="analytics-kpi-label">' + escapeHtml(formatLabel(kpi.label || kpi.name || "Metric")) + '</span><strong class="analytics-kpi-value">' + escapeHtml(formatMetric(kpi.value ?? kpi.metric)) + '</strong>';
            grid.append(card);
        });
        section.append(grid);
        container.append(section);
    }

    if (filters.length && charts.some((chart) => chart.type === "line" && !chart.prediction)) {
        const filterBar = document.createElement("div");
        filterBar.className = "nexa-dashboard-filters";
        const label = document.createElement("label");
        label.textContent = "Time range";
        const select = document.createElement("select");
        select.id = "nexaTimeRange";
        filters[0].options.forEach((option) => {
            const item = document.createElement("option");
            item.value = option.value;
            item.textContent = option.label;
            select.append(item);
        });
        label.append(select);
        filterBar.append(label);
        container.append(filterBar);
        select.addEventListener("change", () => updateLineCharts(container, charts, select.value));
    }

    if (charts.length) {
        const section = makeSection("Operational analysis", "Charts selected from detected date, category and measure fields");
        const grid = document.createElement("div");
        grid.className = "nexa-chart-grid";
        charts.forEach((chart) => {
            const card = document.createElement("article");
            card.className = "nexa-chart-card" + (chart.primary ? " nexa-chart-card-primary" : "");
            card.dataset.chartId = chart.id || "";
            const chartHeader = document.createElement("div");
            chartHeader.className = "nexa-chart-header";
            const title = document.createElement("div");
            title.innerHTML = '<h3>' + escapeHtml(chart.title || "Dataset chart") + '</h3><p>' + escapeHtml(chart.prediction ? "Historical values and model forecast" : formatLabel(chart.unit || chart.metric || chart.dimension || "")) + '</p>';
            if (chart.prediction) {
                const badge = document.createElement("span");
                badge.className = "nexa-forecast-badge";
                badge.textContent = "MODEL FORECAST";
                chartHeader.append(title, badge);
            } else chartHeader.append(title);
            const visual = document.createElement("div");
            visual.className = "nexa-chart-visual";
            visual.dataset.chartVisual = "true";
            visual.innerHTML = renderChart(chart, "all");
            card.append(chartHeader, visual);
            grid.append(card);
        });
        section.append(grid);
        container.append(section);
    } else {
        const empty = document.createElement("div");
        empty.className = "nexa-dashboard-note";
        empty.textContent = "The uploaded fields support dataset profiling, but not a chart with a meaningful hospital measure.";
        container.append(empty);
    }

    if (predictions.length) {
        const section = makeSection("Forecasts and model signals", "Predictions appear only when a configured model can use this upload");
        const grid = document.createElement("div");
        grid.className = "nexa-prediction-grid";
        predictions.forEach((prediction) => {
            const card = document.createElement("article");
            card.className = "nexa-prediction-card " + (prediction.status === "available" ? "is-available" : "is-unavailable");
            if (prediction.status === "available") {
                card.innerHTML = '<span class="nexa-prediction-status">MODEL OUTPUT</span><h3>' + escapeHtml(prediction.title) + '</h3><strong>' + escapeHtml(formatMetric(prediction.value)) + '</strong><p>' + escapeHtml(prediction.period || prediction.source || "Returned by a configured model") + '</p>';
            } else {
                card.innerHTML = '<span class="nexa-prediction-status">MODEL NOT AVAILABLE</span><h3>' + escapeHtml(prediction.title) + '</h3><strong>Prediction unavailable</strong><p>' + escapeHtml(prediction.message || "No compatible model and input data are available.") + '</p>';
            }
            grid.append(card);
        });
        section.append(grid);
        container.append(section);
    }

    if (insights.length || recommendations.length) {
        const section = makeSection("Operational insights", "Evidence-based observations and suggested follow-up from this dataset");
        const grid = document.createElement("div");
        grid.className = "nexa-insight-grid";
        insights.forEach((item) => grid.append(makeSignalCard(item, "insight")));
        recommendations.forEach((item) => grid.append(makeSignalCard(item, "recommendation")));
        section.append(grid);
        container.append(section);
    }

    if (tables.length) {
        const section = makeSection("Detail tables", "Aggregations and sample records from the uploaded file");
        const grid = document.createElement("div");
        grid.className = "analytics-table-grid";
        tables.forEach((table) => grid.append(renderTable(table)));
        section.append(grid);
        container.append(section);
    }
}

function renderDatabaseAnalytics(container, database) {
    if (!database || database.status !== "success") {
        const note = document.createElement("section");
        note.className = "nexa-dashboard-note database-analytics-unavailable";
        note.textContent = database?.message || "Structured hospital database analytics are currently unavailable because the database connection is not configured.";
        container.append(note);
        return;
    }
    const section = makeSection("Hospital database analytics", "Shared read-only MySQL results also used by NexaCopilot and NexaCommand");
    const source = document.createElement("p");
    source.className = "database-analytics-source";
    source.textContent = "Source: " + (database.source || "Hospital operational database");
    section.append(source);

    if (database.kpis?.length) {
        const grid = document.createElement("div");
        grid.className = "analytics-kpi-grid";
        database.kpis.forEach((kpi) => {
            const card = document.createElement("article");
            card.className = "analytics-kpi-card";
            card.innerHTML = '<span class="analytics-kpi-label">' + escapeHtml(formatLabel(kpi.label || "Metric")) + '</span><strong class="analytics-kpi-value">' + escapeHtml(formatMetric(kpi.value)) + '</strong>';
            grid.append(card);
        });
        section.append(grid);
    }
    if (database.charts?.length) {
        const grid = document.createElement("div");
        grid.className = "nexa-chart-grid";
        database.charts.forEach((chart) => {
            const card = document.createElement("article");
            card.className = "nexa-chart-card";
            const heading = document.createElement("div");
            heading.className = "nexa-chart-header";
            heading.innerHTML = '<div><h3>' + escapeHtml(chart.title || "Database chart") + '</h3><p>' + escapeHtml(formatLabel(chart.unit || "records")) + '</p></div>';
            const visual = document.createElement("div");
            visual.className = "nexa-chart-visual";
            visual.innerHTML = renderChart(chart, "all");
            card.append(heading, visual);
            grid.append(card);
        });
        section.append(grid);
    }
    if (database.tables?.length) {
        const grid = document.createElement("div");
        grid.className = "analytics-table-grid";
        database.tables.forEach((table) => grid.append(renderTable(table)));
        section.append(grid);
    }
    container.append(section);
}

function makeSection(title, subtitle) {
    const section = document.createElement("section");
    section.className = "analytics-section nexa-dashboard-section";
    section.innerHTML = '<div class="analytics-section-heading"><div><h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(subtitle) + '</p></div></div>';
    return section;
}

function makeSignalCard(item, kind) {
    const card = document.createElement("article");
    card.className = "nexa-insight-card " + (kind === "recommendation" ? "is-recommendation" : "");
    card.innerHTML = '<span>' + (kind === "recommendation" ? "SUGGESTED ACTION" : "OBSERVED IN DATA") + '</span><h4>' + escapeHtml(item.title || (kind === "recommendation" ? "Recommendation" : "Insight")) + '</h4><p>' + escapeHtml(item.text || "") + '</p><small>Source: ' + escapeHtml(item.source || "Dataset analytics") + '</small>';
    return card;
}

function updateLineCharts(container, charts, range) {
    container.querySelectorAll("[data-chart-visual='true']").forEach((visual) => {
        const card = visual.closest(".nexa-chart-card");
        const chart = charts.find((item) => item.id === card?.dataset.chartId);
        if (chart) visual.innerHTML = renderChart(chart, range);
    });
}

function renderChart(chart, range) {
    if (chart.series?.length) return renderLine(chart, range);
    const data = (chart.data || []).filter((point) => Number.isFinite(Number(point.value)));
    if (!data.length) return '<div class="nexa-chart-empty">No numeric values are available for this chart.</div>';
    if (chart.type === "donut") return renderDonut(data, chart.unit);
    if (chart.type === "line" || chart.type === "area") return renderLine(Object.assign({}, chart, { data: data }), range);
    return renderBars(data, chart.unit);
}

function renderBars(data, unit) {
    const height = Math.max(230, data.length * 31 + 40);
    const maxValue = Math.max(...data.map((point) => Number(point.value)), 0) || 1;
    const rows = data.map((point, index) => {
        const y = 20 + index * 31;
        const width = Math.max(2, Number(point.value) / maxValue * 400);
        const label = String(point.label).length > 23 ? String(point.label).slice(0, 21) + "…" : String(point.label);
        return '<text x="12" y="' + (y + 15) + '" class="nexa-svg-label">' + escapeHtml(label) + '</text><rect x="190" y="' + y + '" width="' + width + '" height="19" rx="5" fill="#168f7a"><title>' + escapeHtml(point.label) + ': ' + escapeHtml(formatMetric(point.value)) + '</title></rect><text x="' + (198 + width) + '" y="' + (y + 15) + '" class="nexa-svg-value">' + escapeHtml(formatMetric(point.value)) + '</text>';
    }).join("");
    return '<svg class="nexa-chart-svg" viewBox="0 0 680 ' + height + '" role="img" aria-label="Horizontal bar chart">' + rows + '</svg>';
}

function renderDonut(data, unit) {
    const total = data.reduce((sum, point) => sum + Math.max(0, Number(point.value)), 0);
    if (!total) return '<div class="nexa-chart-empty">No positive category values are available.</div>';
    const colors = ["#168f7a", "#1d6a88", "#78b7a4", "#a4cfbf", "#f1b95b", "#8797a8", "#d77966", "#546f7a"];
    const radius = 68;
    const circumference = Math.PI * 2 * radius;
    let offset = 0;
    const circles = data.map((point, index) => {
        const length = Math.max(0, Number(point.value)) / total * circumference;
        const circle = '<circle cx="112" cy="108" r="' + radius + '" fill="none" stroke="' + colors[index % colors.length] + '" stroke-width="24" stroke-dasharray="' + length + ' ' + (circumference - length) + '" stroke-dashoffset="' + (-offset) + '" transform="rotate(-90 112 108)"><title>' + escapeHtml(point.label) + ': ' + escapeHtml(formatMetric(point.value)) + '</title></circle>';
        offset += length;
        return circle;
    }).join("");
    const legend = data.map((point, index) => '<li><i style="--legend-color:' + colors[index % colors.length] + '"></i><span>' + escapeHtml(point.label) + '</span><strong>' + escapeHtml(formatMetric(point.value)) + '</strong></li>').join("");
    return '<div class="nexa-donut-layout"><svg class="nexa-donut-svg" viewBox="0 0 224 216" role="img" aria-label="Donut chart"><circle cx="112" cy="108" r="' + radius + '" fill="none" stroke="#edf3f1" stroke-width="24"/>' + circles + '<text x="112" y="104" text-anchor="middle" class="nexa-donut-total">' + escapeHtml(formatMetric(total)) + '</text><text x="112" y="124" text-anchor="middle" class="nexa-donut-caption">' + escapeHtml(unit || "records") + '</text></svg><ul class="nexa-donut-legend">' + legend + '</ul></div>';
}

function renderLine(chart, range) {
    let series = chart.series?.length ? chart.series : [{ name: chart.metric || "Value", kind: "historical", data: chart.data || [] }];
    const dates = series.flatMap((line) => line.data || []).map((point) => ({ ...point, parsed: Date.parse(point.label) })).filter((point) => Number.isFinite(point.parsed) && Number.isFinite(Number(point.value)));
    if (range !== "all" && dates.length) {
        const days = Number(range);
        const cutoff = Math.max(...dates.map((point) => point.parsed)) - days * 86400000;
        series = series.map((line) => Object.assign({}, line, { data: (line.data || []).filter((point) => Date.parse(point.label) >= cutoff) }));
    }
    const active = series.map((line) => Object.assign({}, line, { data: (line.data || []).filter((point) => Number.isFinite(Number(point.value))) })).filter((line) => line.data.length);
    const all = active.flatMap((line) => line.data);
    if (!all.length) return '<div class="nexa-chart-empty">No dated values are available for this chart.</div>';
    const dateValues = all.map((point) => Date.parse(point.label)).filter(Number.isFinite);
    const chronological = dateValues.length === all.length;
    const xValues = chronological ? all.map((point) => Date.parse(point.label)) : all.map((_, index) => index);
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues) || minX + 1;
    const values = all.map((point) => Number(point.value));
    const minY = Math.min(0, ...values);
    const maxY = Math.max(...values) || 1;
    const pad = { left: 55, right: 20, top: 20, bottom: 48 };
    const width = 680, height = 290;
    const plotW = width - pad.left - pad.right, plotH = height - pad.top - pad.bottom;
    const sx = (value) => pad.left + ((value - minX) / (maxX - minX || 1)) * plotW;
    const sy = (value) => pad.top + (1 - (value - minY) / (maxY - minY || 1)) * plotH;
    let grid = "";
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + (plotH * i / 4);
        const label = maxY - (maxY - minY) * i / 4;
        grid += '<line x1="' + pad.left + '" y1="' + y + '" x2="' + (width - pad.right) + '" y2="' + y + '" class="nexa-svg-grid"/><text x="' + (pad.left - 8) + '" y="' + (y + 4) + '" text-anchor="end" class="nexa-svg-axis">' + escapeHtml(formatMetric(label)) + '</text>';
    }
    const paths = active.map((line, index) => {
        const points = line.data.map((point) => {
            const parsed = Date.parse(point.label);
            const xValue = chronological ? parsed : all.indexOf(point);
            return [sx(xValue), sy(Number(point.value))];
        });
        const path = points.map((point, idx) => (idx ? "L" : "M") + point[0].toFixed(1) + "," + point[1].toFixed(1)).join(" ");
        const forecast = line.kind === "forecast";
        const color = forecast ? "#d48a21" : ["#168f7a", "#1d6a88", "#6d8db0"][index % 3];
        const dash = forecast ? ' stroke-dasharray="7 5"' : "";
        const circles = points.map((point, idx) => '<circle cx="' + point[0].toFixed(1) + '" cy="' + point[1].toFixed(1) + '" r="3.5" fill="' + color + '"><title>' + escapeHtml(line.data[idx].label + ": " + formatMetric(line.data[idx].value)) + '</title></circle>').join("");
        return '<path d="' + path + '" fill="none" stroke="' + color + '" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"' + dash + '/>' + circles;
    }).join("");
    const labelPoints = active[0].data;
    const ticks = [];
    const tickCount = Math.min(5, labelPoints.length);
    for (let i = 0; i < tickCount; i++) {
        const index = Math.round(i * (labelPoints.length - 1) / Math.max(tickCount - 1, 1));
        const point = labelPoints[index];
        const parsed = Date.parse(point.label);
        const xValue = chronological ? parsed : all.indexOf(point);
        const x = sx(xValue);
        const label = String(point.label).length > 10 ? String(point.label).slice(0, 10) : String(point.label);
        ticks.push('<text x="' + x + '" y="' + (height - 18) + '" text-anchor="middle" class="nexa-svg-axis">' + escapeHtml(label) + '</text>');
    }
    const legend = active.length > 1 ? '<div class="nexa-chart-legend">' + active.map((line, index) => '<span><i class="' + (line.kind === "forecast" ? "is-forecast" : "") + '"></i>' + escapeHtml(line.name || "Series") + '</span>').join("") + '</div>' : "";
    return legend + '<svg class="nexa-chart-svg" viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="Time series line chart">' + grid + paths + ticks.join("") + '</svg>';
}

function renderTable(table) {
    const card = document.createElement("article");
    card.className = "analytics-table-card";
    const columns = table.columns || table.headers || [];
    const rows = table.rows || table.data || [];
    const header = document.createElement("div");
    header.className = "analytics-table-header";
    header.innerHTML = '<h4>' + escapeHtml(formatLabel(table.title || "Dataset details")) + '</h4>';
    card.append(header);
    const wrapper = document.createElement("div");
    wrapper.className = "analytics-table-wrapper";
    if (!columns.length || !rows.length) {
        wrapper.innerHTML = '<div class="analytics-table-empty">No rows are available.</div>';
    } else {
        const thead = '<thead><tr>' + columns.map((column) => '<th>' + escapeHtml(formatLabel(column)) + '</th>').join("") + '</tr></thead>';
        const tbody = rows.map((row) => '<tr>' + columns.map((column, index) => {
            const value = Array.isArray(row) ? row[index] : row?.[column];
            return '<td>' + escapeHtml(value === null || value === undefined ? "—" : formatMetric(value)) + '</td>';
        }).join("") + '</tr>').join("");
        wrapper.innerHTML = '<table>' + thead + '<tbody>' + tbody + '</tbody></table>';
    }
    card.append(wrapper);
    return card;
}

function formatLabel(value) {
    return String(value || "")
        .replace(/_/g, " ")
        .replace(/-/g, " ")
        .split(/\s+/)
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}
function formatMetric(value) {
    if (typeof value === "number" && Number.isFinite(value)) return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
    return value === null || value === undefined || value === "" ? "—" : String(value);
}
function formatNumber(value) {
    const number = Number(value);
    return value === null || value === undefined || !Number.isFinite(number) ? "—" : new Intl.NumberFormat().format(number);
}
function escapeHtml(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
