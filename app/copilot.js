document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("copilotForm");
    const question = document.getElementById("copilotQuestion");
    const sendButton = document.getElementById("copilotSendButton");
    const messages = document.getElementById("copilotMessages");
    const status = document.getElementById("copilotStatus");
    const documentSelect = document.getElementById("copilotDocument");
    const sourceHint = document.getElementById("copilotSourceHint");

    document.querySelectorAll(".suggestion-button").forEach((button) => {
        button.addEventListener("click", () => {
            question.value = button.textContent.trim();
            question.focus();
        });
    });

    documentSelect?.addEventListener("change", () => {
        sourceHint.textContent = documentSelect.value
            ? "Answers will use retrieved passages from this report."
            : "Database analytics are prioritized. The analyzed dataset is used as a fallback.";
    });

    loadDocuments();

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();

        const prompt = question.value.trim();

        if (!prompt) return;

        addMessage(messages, "You", prompt, "user");

        question.value = "";
        sendButton.disabled = true;
        sendButton.textContent = "Thinking…";

        setStatus(
            status,
            documentSelect.value
                ? "Searching the selected report…"
                : "Checking hospital database analytics…",
            "loading"
        );

        const pending = addMessage(
            messages,
            "MedaNexa",
            "Working from the available hospital data…",
            "assistant"
        );

        try {
            /*
             * Document selected:
             * Use the document/RAG endpoint directly.
             */
            const endpoint = documentSelect.value
                ? "/documents/ask"
                : "/copilot/ask";

            const payload = documentSelect.value
                ? {
                    question: prompt,
                    document_name: documentSelect.value
                }
                : {
                    question: prompt
                };

            /*
             * First priority:
             * MySQL / backend analytics.
             */
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await readJson(response);

            if (!response.ok) {
                throw new Error(
                    data.detail || "The assistant request failed."
                );
            }

            /*
             * SQL/database unavailable or unsupported:
             * fall back to the analyzed dataset.
             */
            if (
                !documentSelect.value &&
                (data.status === "unavailable" ||
                    data.status === "unsupported")
            ) {
                const datasetAnswer = answerFromCurrentDataset(prompt);

                if (datasetAnswer) {
                    pending.querySelector("p").textContent =
                        datasetAnswer.answer;

                    if (datasetAnswer.source) {
                        addSources(pending, [
                            {
                                file_name: datasetAnswer.source,
                                type: "Analyzed dataset"
                            }
                        ]);
                    }

                    setStatus(
                        status,
                        "Answered from Analyzed Dataset.",
                        "success"
                    );

                    return;
                }
            }

            /*
             * Normal backend response.
             */
            pending.querySelector("p").textContent =
                data.answer || "No answer was returned.";

            if (
                Array.isArray(data.sources) &&
                data.sources.length
            ) {
                addSources(pending, data.sources);
            }

            const routeLabels = {
                sql: "Hospital operational database",
                ml: "Trained model",
                rag: "Uploaded document",
                dataset: "Analyzed dataset",
                clarify: "Source clarification"
            };

            if (data.status === "unavailable") {
                setStatus(
                    status,
                    data.route === "ml"
                        ? "Prediction unavailable"
                        : "Structured database unavailable",
                    "error"
                );
            } else if (data.status === "no_source") {
                setStatus(
                    status,
                    "No matching document source found",
                    "error"
                );
            } else if (
                data.status === "clarification_needed"
            ) {
                setStatus(
                    status,
                    "Please clarify the source or metric",
                    ""
                );
            } else {
                setStatus(
                    status,
                    `Answered from ${
                        routeLabels[data.route] ||
                        (
                            documentSelect.value
                                ? "the selected report"
                                : "available sources"
                        )
                    }.`,
                    "success"
                );
            }

        } catch (error) {

            /*
             * If the backend itself fails completely,
             * try the analyzed dataset as a final fallback.
             */
            if (!documentSelect.value) {
                const datasetAnswer = answerFromCurrentDataset(prompt);

                if (datasetAnswer) {
                    pending.querySelector("p").textContent =
                        datasetAnswer.answer;

                    if (datasetAnswer.source) {
                        addSources(pending, [
                            {
                                file_name: datasetAnswer.source,
                                type: "Analyzed dataset"
                            }
                        ]);
                    }

                    setStatus(
                        status,
                        "Answered from Analyzed Dataset.",
                        "success"
                    );

                    return;
                }
            }

            pending.querySelector("p").textContent =
                error.message ||
                "The assistant could not process this question.";

            setStatus(
                status,
                error.message ||
                    "The assistant could not process this question.",
                "error"
            );

        } finally {

            sendButton.disabled = false;
            sendButton.textContent = "Ask";
            question.focus();

        }
    });


    async function loadDocuments() {

        try {

            const response = await fetch(
                "/documents/",
                {
                    credentials: "same-origin"
                }
            );

            const data = await readJson(response);

            if (!response.ok) return;

            (data.documents || [])
                .filter((doc) =>
                    ["pdf", "docx"].includes(
                        String(doc.file_type).toLowerCase()
                    )
                )
                .forEach((doc) => {

                    documentSelect.add(
                        new Option(
                            displayName(doc.file_name),
                            doc.file_name
                        )
                    );

                });

        } catch (error) {

            console.error(
                "Could not load document choices.",
                error
            );

        }
    }
});


function addMessage(
    container,
    speaker,
    text,
    kind
) {

    const article = document.createElement("article");

    article.className = `copilot-message ${kind}`;

    const title = document.createElement("strong");

    title.textContent = speaker;

    const content = document.createElement("p");

    content.textContent = text;

    article.append(title, content);

    container.append(article);

    article.scrollIntoView({
        block: "nearest",
        behavior: "smooth"
    });

    return article;
}


function addSources(message, sources) {

    const heading = document.createElement("strong");

    heading.className = "source-heading";

    heading.textContent = "Sources";

    const list = document.createElement("ul");

    sources.forEach((source) => {

        const item = document.createElement("li");

        const location = [
            source.page_number
                ? `Page ${source.page_number}`
                : "",

            source.table_number
                ? `Table ${source.table_number}`
                : "",

            source.type ||
                source.section ||
                "",

            source.query_file ||
                "",

            source.period ||
                ""
        ]
            .filter(Boolean)
            .join(" · ");

        item.textContent =
            `${source.file_name ||
                source.document_name ||
                "Hospital source"}${
                location
                    ? ` · ${location}`
                    : ""
            }${
                source.text
                    ? `: ${source.text}`
                    : ""
            }`;

        list.append(item);

    });

    message.append(heading, list);
}


function setStatus(
    target,
    message,
    type
) {

    target.textContent = message;

    target.className =
        `workspace-status ${type || ""}`.trim();
}


async function readJson(response) {

    try {

        return await response.json();

    } catch {

        return {};

    }
}


function displayName(name) {

    return String(
        name || "Document"
    ).replace(
        /^[0-9a-f]{8}-[0-9a-f-]{27}_/i,
        ""
    );

}


/*
 * =========================================================
 * ANALYZED DATASET FALLBACK
 * =========================================================
 *
 * This is NOT the primary source anymore.
 *
 * Priority:
 *
 * 1. MySQL / backend SQL analytics
 * 2. Analyzed dataset
 *
 */


function answerFromCurrentDataset(prompt) {

    try {

        const raw =
            sessionStorage.getItem(
                "medanexaAnalyticsData"
            );

        if (!raw) return null;

        const analysis =
            JSON.parse(raw);

        const dashboard =
            analysis?.dashboard;

        if (!dashboard) return null;

        const question =
            prompt.toLowerCase();

        const fileName =
            dashboard.file_name ||
            analysis.file_name ||
            "the analyzed dataset";

        const kpis =
            dashboard.kpis || [];

        const charts =
            dashboard.charts || [];


        /*
         * Average LOS
         */

        if (
            question.includes("average los") ||
            question.includes("average length of stay") ||
            question.includes("mean los")
        ) {

            const kpi =
                kpis.find((item) =>
                    /average.*(los|length of stay)/i.test(
                        String(
                            item.label ||
                            item.name ||
                            ""
                        )
                    )
                );

            if (kpi) {

                return {

                    answer:
                        `The average length of stay in the analyzed dataset is ${
                            formatCopilotMetric(
                                kpi.value ??
                                kpi.metric
                            )
                        } days.`,

                    source: fileName

                };

            }

        }


        /*
         * Total admissions
         */

        if (
            question.includes("total admissions") ||
            question.includes("how many admissions") ||
            question.includes("number of admissions")
        ) {

            const kpi =
                kpis.find((item) =>
                    /total.*admission/i.test(
                        String(
                            item.label ||
                            item.name ||
                            ""
                        )
                    )
                );

            if (kpi) {

                return {

                    answer:
                        `The analyzed dataset contains ${
                            formatCopilotMetric(
                                kpi.value ??
                                kpi.metric
                            )
                        } admissions.`,

                    source: fileName

                };

            }

        }


        /*
         * Highest department admissions
         */

        if (
            question.includes("highest admissions") ||
            question.includes("most admissions") ||
            question.includes("highest admission department") ||
            question.includes("department has the highest")
        ) {

            const chart =
                charts.find((item) =>
                    /admission.*department|department.*admission/i.test(
                        String(
                            item.title ||
                            item.dimension ||
                            ""
                        )
                    )
                );

            if (
                chart?.data?.length
            ) {

                const sorted =
                    chart.data
                        .filter((item) =>
                            Number.isFinite(
                                Number(item.value)
                            )
                        )
                        .sort(
                            (a, b) =>
                                Number(b.value) -
                                Number(a.value)
                        );

                if (sorted.length) {

                    const top =
                        sorted[0];

                    return {

                        answer:
                            `${top.label} has the highest recorded admissions with ${
                                formatCopilotMetric(
                                    top.value
                                )
                            } admissions.`,

                        source: fileName

                    };

                }

            }

        }


        /*
         * Highest admission type
         */

        if (
            question.includes("most common admission type") ||
            question.includes("highest admission type") ||
            question.includes("most common type")
        ) {

            const chart =
                charts.find((item) =>
                    /admission.*type|type.*admission/i.test(
                        String(
                            item.title ||
                            item.dimension ||
                            ""
                        )
                    )
                );

            if (
                chart?.data?.length
            ) {

                const sorted =
                    chart.data
                        .filter((item) =>
                            Number.isFinite(
                                Number(item.value)
                            )
                        )
                        .sort(
                            (a, b) =>
                                Number(b.value) -
                                Number(a.value)
                        );

                if (sorted.length) {

                    const top =
                        sorted[0];

                    return {

                        answer:
                            `${top.label} is the most common admission type with ${
                                formatCopilotMetric(
                                    top.value
                                )
                            } admissions.`,

                        source: fileName

                    };

                }

            }

        }


        /*
         * Peak LOS
         */

        if (
            question.includes("peak los") ||
            question.includes("maximum los") ||
            question.includes("highest length of stay")
        ) {

            const kpi =
                kpis.find((item) =>
                    /peak.*(los|length of stay)|maximum.*(los|length of stay)/i.test(
                        String(
                            item.label ||
                            item.name ||
                            ""
                        )
                    )
                );

            if (kpi) {

                return {

                    answer:
                        `The peak length of stay in the analyzed dataset is ${
                            formatCopilotMetric(
                                kpi.value ??
                                kpi.metric
                            )
                        } days.`,

                    source: fileName

                };

            }

        }


        /*
         * Unique patients
         */

        if (
            question.includes("unique patients") ||
            question.includes("number of unique patients")
        ) {

            const kpi =
                kpis.find((item) =>
                    /unique.*patient/i.test(
                        String(
                            item.label ||
                            item.name ||
                            ""
                        )
                    )
                );

            if (kpi) {

                return {

                    answer:
                        `The analyzed dataset contains ${
                            formatCopilotMetric(
                                kpi.value ??
                                kpi.metric
                            )
                        } unique patients.`,

                    source: fileName

                };

            }

        }


        /*
         * Department count
         */

        if (
            question.includes("how many departments") ||
            question.includes("number of departments")
        ) {

            const kpi =
                kpis.find((item) =>
                    /^departments?$/i.test(
                        String(
                            item.label ||
                            item.name ||
                            ""
                        )
                    )
                );

            if (kpi) {

                return {

                    answer:
                        `The analyzed dataset contains ${
                            formatCopilotMetric(
                                kpi.value ??
                                kpi.metric
                            )
                        } departments.`,

                    source: fileName

                };

            }

        }


        return null;

    } catch (error) {

        console.warn(
            "Could not answer from current dataset.",
            error
        );

        return null;

    }

}


function formatCopilotMetric(value) {

    if (
        typeof value === "number" &&
        Number.isFinite(value)
    ) {

        return new Intl.NumberFormat(
            undefined,
            {
                maximumFractionDigits: 2
            }
        ).format(value);

    }

    return (
        value === null ||
        value === undefined ||
        value === ""
    )
        ? "—"
        : String(value);

}