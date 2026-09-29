document.addEventListener("DOMContentLoaded", function () {

    // =========================================
    // ELEMENTS
    // =========================================

    const fileInput =
        document.getElementById("fileInput");

    const analyzeButton =
        document.getElementById("analyzeButton");

    const fileName =
        document.getElementById("fileName");

    const statusMessage =
        document.getElementById("statusMessage");

    const analysisSection =
        document.getElementById("analysisSection");

    const resultFile =
        document.getElementById("resultFile");

    const resultRows =
        document.getElementById("resultRows");

    const resultColumns =
        document.getElementById("resultColumns");

    const resultDuplicates =
        document.getElementById("resultDuplicates");

    const modulesContainer =
        document.getElementById("modulesContainer");

    const analysisStatus =
        document.getElementById("analysisStatus");


    // =========================================
    // NAVIGATION
    // =========================================

    const navItems =
        document.querySelectorAll(".nav-item");

    const pages = {
        dashboard:
            document.getElementById("dashboardPage"),

        analytics:
            document.getElementById("analyticsPage"),

        ml:
            document.getElementById("mlPage"),

        documents:
            document.getElementById("documentsPage"),

        assistant:
            document.getElementById("assistantPage"),

        powerbi:
            document.getElementById("powerbiPage")
    };


    function showPage(pageName) {

        // Hide all pages
        Object.values(pages).forEach(function (page) {

            if (page) {
                page.classList.remove(
                    "active-page"
                );
            }

        });


        // Remove active from navigation
        navItems.forEach(function (item) {

            item.classList.remove("active");

        });


        // Show selected page
        if (pages[pageName]) {

            pages[pageName].classList.add(
                "active-page"
            );

        }


        // Activate selected navigation item
        navItems.forEach(function (item) {

            if (
                item.dataset.page === pageName
            ) {

                item.classList.add("active");

            }

        });

    }


    // Navigation click
    navItems.forEach(function (item) {

        item.addEventListener(
            "click",
            function () {

                const page =
                    item.dataset.page;

                showPage(page);

            }
        );

    });


    // Buttons that navigate using data-page
    document
        .querySelectorAll("[data-page]")
        .forEach(function (element) {

            if (
                !element.classList.contains(
                    "nav-item"
                )
            ) {

                element.addEventListener(
                    "click",
                    function () {

                        showPage(
                            element.dataset.page
                        );

                    }
                );

            }

        });


    // Start on Dashboard
    showPage("dashboard");


    // =========================================
    // FILE SELECTION
    // =========================================

    if (fileInput) {

        fileInput.addEventListener(
            "change",
            function () {

                if (
                    fileInput.files.length > 0
                ) {

                    fileName.textContent =
                        "Selected file: " +
                        fileInput.files[0].name;

                } else {

                    fileName.textContent =
                        "No file selected";

                }

            }
        );

    }


    // =========================================
    // ANALYZE DATASET
    // =========================================

    if (analyzeButton) {

        analyzeButton.addEventListener(
            "click",
            async function () {

                if (
                    fileInput.files.length === 0
                ) {

                    statusMessage.textContent =
                        "Please select a file first.";

                    return;

                }


                const file =
                    fileInput.files[0];


                const formData =
                    new FormData();


                formData.append(
                    "file",
                    file
                );


                analyzeButton.disabled =
                    true;

                analyzeButton.textContent =
                    "Analyzing...";


                statusMessage.textContent =
                    "Analyzing dataset...";


                try {

                    const response =
                        await fetch(
                            "/analyze-dataset",
                            {
                                method: "POST",
                                body: formData
                            }
                        );


                    const data =
                        await response.json();


                    console.log(
                        "Backend response:",
                        data
                    );


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Analysis failed."
                        );

                    }


                    // =================================
                    // DATASET INFORMATION
                    // =================================

                    analysisSection
                        .classList
                        .remove("hidden");


                    resultFile.textContent =
                        data.file_name;


                    const profile =
                        data.analysis.profile ||
                        {};


                    resultRows.textContent =
                        profile.rows ?? "-";


                    resultColumns.textContent =
                        profile.columns ?? "-";


                    resultDuplicates.textContent =
                        profile.duplicate_rows ?? 0;


                    // =================================
                    // AVAILABLE MODULES
                    // =================================

                    modulesContainer.innerHTML =
                        "";


                    const modules =
                        data.analysis
                            .available_modules ||
                        [];


                    modules.forEach(
                        function (moduleName) {

                            const element =
                                document.createElement(
                                    "div"
                                );


                            element.className =
                                "module";


                            element.textContent =
                                moduleName;


                            modulesContainer
                                .appendChild(
                                    element
                                );

                        }
                    );


                    // =================================
                    // DYNAMIC ANALYTICS
                    // =================================

                    renderDynamicAnalytics(
                        data.analytics
                    );


                    statusMessage.textContent =
                        "Analysis completed successfully.";


                    analysisStatus.textContent =
                        "Dataset analyzed successfully.";


                    // Automatically go to Analytics
                    showPage("analytics");


                }
                catch (error) {

                    console.error(error);


                    statusMessage.textContent =
                        "Error: " +
                        error.message;

                }
                finally {

                    analyzeButton.disabled =
                        false;


                    analyzeButton.textContent =
                        "Analyze Dataset";

                }

            }
        );

    }


    // =========================================
    // DYNAMIC ANALYTICS
    // =========================================

    function renderDynamicAnalytics(
        analytics
    ) {

        if (!analytics) {
            return;
        }


        // Remove previous analytics
        const oldSection =
            document.getElementById(
                "dynamicAnalytics"
            );


        if (oldSection) {

            oldSection.remove();

        }


        const section =
            document.createElement("div");


        section.id =
            "dynamicAnalytics";


        section.className =
            "section-block";


        // =================================
        // TITLE
        // =================================

        const title =
            document.createElement("h3");


        title.textContent =
            getAnalyticsTitle(
                analytics.dataset_type
            );


        section.appendChild(title);


        // =================================
        // KPI GRID
        // =================================

        const kpiGrid =
            document.createElement("div");


        kpiGrid.className =
            "kpi-grid";


        const kpis =
            analytics.kpis || [];


        kpis.forEach(
            function (kpi) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "kpi-card";


                const label =
                    document.createElement(
                        "span"
                    );


                label.textContent =
                    kpi.label;


                const value =
                    document.createElement(
                        "strong"
                    );


                value.textContent =
                    kpi.value;


                card.appendChild(label);

                card.appendChild(value);

                kpiGrid.appendChild(card);

            }
        );


        section.appendChild(kpiGrid);


        // =================================
        // TABLES
        // =================================

        const tables =
            analytics.tables || [];


        tables.forEach(
            function (tableData) {

                const tableContainer =
                    document.createElement(
                        "div"
                    );


                tableContainer.className =
                    "table-container";


                const tableTitle =
                    document.createElement(
                        "h3"
                    );


                tableTitle.textContent =
                    tableData.title;


                tableContainer.appendChild(
                    tableTitle
                );


                const table =
                    document.createElement(
                        "table"
                    );


                // Header
                const thead =
                    document.createElement(
                        "thead"
                    );


                const headerRow =
                    document.createElement(
                        "tr"
                    );


                tableData.columns.forEach(
                    function (column) {

                        const th =
                            document.createElement(
                                "th"
                            );


                        th.textContent =
                            formatColumnName(
                                column
                            );


                        headerRow.appendChild(
                            th
                        );

                    }
                );


                thead.appendChild(
                    headerRow
                );


                table.appendChild(
                    thead
                );


                // Body
                const tbody =
                    document.createElement(
                        "tbody"
                    );


                tableData.rows.forEach(
                    function (row) {

                        const tr =
                            document.createElement(
                                "tr"
                            );


                        tableData.columns.forEach(
                            function (column) {

                                const td =
                                    document.createElement(
                                        "td"
                                    );


                                let value =
                                    row[column];


                                if (
                                    typeof value ===
                                    "number"
                                ) {

                                    value =
                                        Number(
                                            value.toFixed(
                                                2
                                            )
                                        );

                                }


                                td.textContent =
                                    value ?? "-";


                                tr.appendChild(td);

                            }
                        );


                        tbody.appendChild(tr);

                    }
                );


                table.appendChild(
                    tbody
                );


                tableContainer.appendChild(
                    table
                );


                section.appendChild(
                    tableContainer
                );

            }
        );


        analysisSection.appendChild(
            section
        );

    }


    // =========================================
    // ANALYTICS TITLES
    // =========================================

    function getAnalyticsTitle(
        type
    ) {

        const titles = {

            admissions:
                "Admission Intelligence",

            appointments:
                "Appointment Intelligence",

            beds:
                "Bed & Capacity Intelligence",

            equipment:
                "Equipment & Maintenance Intelligence",

            departments:
                "Department Intelligence"

        };


        return (
            titles[type] ||
            "Hospital Analytics"
        );

    }


    // =========================================
    // TABLE COLUMN FORMAT
    // =========================================

   // =========================================
// ML PREDICTIONS
// =========================================

async function loadMLPredictions() {

    const mlStatus =
        document.getElementById("mlStatus");

    try {

        mlStatus.textContent =
            "Loading ML predictions...";

        const response =
            await fetch("/ml-predictions");

        const data =
            await response.json();

        console.log(
            "ML predictions:",
            data
        );

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "ML prediction failed."
            );

        }

        const predictions =
            data.predictions;


        // -----------------------------
        // Admission Forecast
        // -----------------------------

        if (
            predictions.admission_forecast &&
            !predictions.admission_forecast.error
        ) {

            document.getElementById(
                "admissionForecast"
            ).textContent =
                predictions
                    .admission_forecast
                    .predicted_admissions;


            document.getElementById(
                "forecastMonth"
            ).textContent =
                predictions
                    .admission_forecast
                    .forecast_month;

        }


        // -----------------------------
        // Bed Forecast
        // -----------------------------

        if (
            predictions.bed_forecast &&
            !predictions.bed_forecast.error
        ) {

            document.getElementById(
                "bedForecast"
            ).textContent =
                predictions
                    .bed_forecast
                    .average_predicted_occupied_beds;


            renderBedForecast(
                predictions
                    .bed_forecast
                    .predictions
            );

        }


        // -----------------------------
        // Equipment Risk
        // -----------------------------

        if (
            predictions.equipment_failure &&
            predictions.equipment_failure.risk
        ) {

            document.getElementById(
                "equipmentRisk"
            ).textContent =
                predictions
                    .equipment_failure
                    .risk;

        }


        mlStatus.textContent =
            "ML predictions loaded successfully.";

    }
    catch (error) {

        console.error(
            "ML ERROR:",
            error
        );

        mlStatus.textContent =
            "ML prediction error: " +
            error.message;

    }

}


// =========================================
// BED FORECAST TABLE
// =========================================

function renderBedForecast(predictions) {

    const container =
        document.getElementById(
            "bedForecastTable"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";


    if (!predictions) {
        return;
    }


    const table =
        document.createElement("table");


    table.innerHTML = `
        <thead>
            <tr>
                <th>Date</th>
                <th>Predicted Occupied Beds</th>
            </tr>
        </thead>
    `;


    const tbody =
        document.createElement("tbody");


    predictions.forEach(function (item) {

        const row =
            document.createElement("tr");


        row.innerHTML = `
            <td>${item.date}</td>
            <td>${item.predicted_occupied_beds}</td>
        `;


        tbody.appendChild(row);

    });


    table.appendChild(tbody);

    container.appendChild(table);

}


// =========================================
// ML PAGE CLICK
// =========================================

navItems.forEach(function (item) {

    item.addEventListener(
        "click",
        function () {

            const page =
                item.dataset.page;

            showPage(page);


            if (page === "ml") {

                loadMLPredictions();

            }

        }
    );

});


});
