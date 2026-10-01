document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("documentFile");
    const fileName = document.getElementById("documentFileName");
    const uploadForm = document.getElementById("documentUploadForm");
    const uploadButton = document.getElementById("documentUploadButton");
    const uploadStatus = document.getElementById("documentUploadStatus");
    const refreshButton = document.getElementById("refreshDocumentsButton");
    const list = document.getElementById("documentsList");
    const select = document.getElementById("documentSelect");
    const questionForm = document.getElementById("documentQuestionForm");
    const question = document.getElementById("documentQuestion");
    const askButton = document.getElementById("documentAskButton");
    const questionStatus = document.getElementById("documentQuestionStatus");
    const answer = document.getElementById("documentAnswer");

    let documents = [];
    fileInput?.addEventListener("change", () => {
        fileName.textContent = fileInput.files?.[0]?.name || "Choose a PDF or DOCX";
    });
    refreshButton?.addEventListener("click", loadDocuments);

    uploadForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const file = fileInput?.files?.[0];
        if (!file) return setStatus(uploadStatus, "Choose a PDF or DOCX file first.", "error");
        if (!/\.(pdf|docx)$/i.test(file.name)) return setStatus(uploadStatus, "Only PDF and DOCX files are supported.", "error");
        if (file.size > 25 * 1024 * 1024) return setStatus(uploadStatus, "The file exceeds the 25 MB upload limit.", "error");
        const formData = new FormData();
        formData.append("file", file);
        uploadButton.disabled = true;
        uploadButton.textContent = "Processing…";
        setStatus(uploadStatus, "Uploading and processing the document. Larger reports may take a few minutes.", "loading");
        try {
            const response = await fetch("/documents/upload", { method: "POST", body: formData });
            const data = await readJson(response);
            if (!response.ok) throw new Error(data.detail || "Document processing failed.");
            setStatus(uploadStatus, `${data.file_name} processed. ${data.message || "Ready for search."}`, "success");
            uploadForm.reset();
            fileName.textContent = "Choose a PDF or DOCX";
            await loadDocuments();
            if (data.processing_type === "dataset" && data.analytics) {
                sessionStorage.setItem("medanexaAnalyticsData", JSON.stringify({ status: "success", file_name: data.file_name, understanding: data.understanding, analytics: data.analytics }));
            }
        } catch (error) {
            setStatus(uploadStatus, error.message || "Document processing failed.", "error");
        } finally {
            uploadButton.disabled = false;
            uploadButton.textContent = "Process document";
        }
    });

    questionForm?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!select.value) return setStatus(questionStatus, "Choose a processed PDF or DOCX first.", "error");
        if (!question.value.trim()) return setStatus(questionStatus, "Enter a question.", "error");
        askButton.disabled = true;
        askButton.textContent = "Searching…";
        answer.classList.add("hidden");
        setStatus(questionStatus, "Searching document passages and preparing a sourced answer…", "loading");
        try {
            const response = await fetch("/documents/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.value.trim(), document_name: select.value }) });
            const data = await readJson(response);
            if (!response.ok) throw new Error(data.detail || "Document search failed.");
            renderAnswer(answer, data);
            answer.classList.remove("hidden");
            setStatus(questionStatus, "Answer generated from retrieved document passages.", "success");
        } catch (error) {
            setStatus(questionStatus, error.message || "Document search failed.", "error");
        } finally {
            askButton.disabled = false;
            askButton.textContent = "Search documents";
        }
    });

    async function loadDocuments() {
        if (!list) return;
        list.innerHTML = "";
        const loading = document.createElement("p");
        loading.className = "muted-copy";
        loading.textContent = "Loading documents…";
        list.append(loading);
        try {
            const response = await fetch("/documents/", { credentials: "same-origin" });
            const data = await readJson(response);
            if (!response.ok) throw new Error(data.detail || "Could not load documents.");
            documents = (data.documents || []).filter((item) => ["pdf", "docx"].includes(String(item.file_type).toLowerCase()));
            list.replaceChildren();
            select.replaceChildren(new Option("Choose a processed PDF or DOCX", ""));
            if (!documents.length) {
                const empty = document.createElement("p");
                empty.className = "muted-copy";
                empty.textContent = "No PDF or DOCX documents are available yet.";
                list.append(empty);
                return;
            }
            documents.forEach((doc) => {
                const option = new Option(displayName(doc.file_name), doc.file_name);
                select.add(option);
                const item = document.createElement("article");
                item.className = "document-list-item";
                const details = document.createElement("div");
                const title = document.createElement("strong");
                title.textContent = displayName(doc.file_name);
                const meta = document.createElement("small");
                meta.textContent = `${String(doc.file_type).toUpperCase()} · ${formatBytes(doc.size)} · Processed for document search`;
                details.append(title, meta);
                const choose = document.createElement("button");
                choose.type = "button";
                choose.className = "secondary-button";
                choose.textContent = "Ask this report";
                choose.addEventListener("click", () => { select.value = doc.file_name; question.focus(); });
                item.append(details, choose);
                list.append(item);
            });
        } catch (error) {
            list.replaceChildren();
            const message = document.createElement("p");
            message.className = "workspace-status error";
            message.textContent = error.message || "Could not load documents.";
            list.append(message);
        }
    }

    loadDocuments();
});

function renderAnswer(container, data) {
    container.replaceChildren();
    const heading = document.createElement("h3");
    heading.textContent = "Answer";
    const text = document.createElement("p");
    text.className = "answer-copy";
    text.textContent = data.answer || "No answer was returned.";
    container.append(heading, text);
    const sources = Array.isArray(data.sources) ? data.sources : [];
    if (!sources.length) return;
    const sourceHeading = document.createElement("h4");
    sourceHeading.textContent = "Retrieved sources";
    const list = document.createElement("ol");
    sources.forEach((source) => {
        const item = document.createElement("li");
        const location = [source.page_number ? `Page ${source.page_number}` : "", source.table_number ? `Table ${source.table_number}` : "", source.section || ""].filter(Boolean).join(" · ");
        const score = Number.isFinite(Number(source.similarity_score)) ? ` · relevance ${(Number(source.similarity_score) * 100).toFixed(1)}%` : "";
        item.textContent = `${location || "Document passage"}${score}: ${source.text || ""}`;
        list.append(item);
    });
    container.append(sourceHeading, list);
}

function setStatus(target, message, type = "") {
    if (!target) return;
    target.textContent = message;
    target.className = `workspace-status ${type}`.trim();
}

async function readJson(response) {
    try { return await response.json(); }
    catch { return {}; }
}

function formatBytes(bytes) {
    const size = Number(bytes) || 0;
    return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} KB` : `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function displayName(name) {
    return String(name || "Document").replace(/^[0-9a-f]{8}-[0-9a-f-]{27}_/i, "");
}
