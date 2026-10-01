document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const dropzone = document.getElementById("uploadDropzone");
    const fileName = document.getElementById("fileName");
    const analyzeButton = document.getElementById("analyzeButton");
    const status = document.getElementById("statusMessage");
    const analysisSection = document.getElementById("analysisSection");
    const resultFile = document.getElementById("resultFile");
    const resultRows = document.getElementById("resultRows");
    const resultColumns = document.getElementById("resultColumns");
    const resultDuplicates = document.getElementById("resultDuplicates");
    const modulesContainer = document.getElementById("modulesContainer");
    const analysisStatus = document.getElementById("analysisStatus");
    if (!fileInput || !analyzeButton) return;

    const maxBytes = 25 * 1024 * 1024;
    let selectedFile = null;

    function setStatus(message, kind = "") {
        if (!status) return;
        status.textContent = message;
        status.className = `status ${kind}`.trim();
    }

    function chooseFile(file) {
        if (!file) return;
        if (!/\.(csv|xlsx)$/i.test(file.name)) {
            fileInput.value = "";
            selectedFile = null;
            if (fileName) fileName.textContent = "No file selected";
            setStatus("Choose a CSV or XLSX dataset.", "error");
            return;
        }
        if (file.size > maxBytes) {
            fileInput.value = "";
            selectedFile = null;
            if (fileName) fileName.textContent = "No file selected";
            setStatus("The dataset exceeds the 25 MB upload limit.", "error");
            return;
        }
        selectedFile = file;
        if (fileName) fileName.textContent = `Selected file: ${file.name}`;
        setStatus("");
    }

    fileInput.addEventListener("change", () => chooseFile(fileInput.files?.[0]));

    if (dropzone) {
        dropzone.addEventListener("click", (event) => {
            if (event.target.closest("label, input, button, a")) return;
            fileInput.click();
        });
        dropzone.addEventListener("keydown", (event) => {
            if (event.target !== dropzone || !["Enter", " "].includes(event.key)) return;
            event.preventDefault();
            fileInput.click();
        });
        ["dragenter", "dragover"].forEach((type) => dropzone.addEventListener(type, (event) => {
            event.preventDefault();
            dropzone.classList.add("drag-over");
        }));
        ["dragleave", "drop"].forEach((type) => dropzone.addEventListener(type, (event) => {
            event.preventDefault();
            dropzone.classList.remove("drag-over");
        }));
        dropzone.addEventListener("drop", (event) => chooseFile(event.dataTransfer?.files?.[0]));
    }

    analyzeButton.addEventListener("click", async () => {
        const file = selectedFile || fileInput.files?.[0];
        if (!file) {
            setStatus("Please select a CSV or XLSX file first.", "error");
            return;
        }
        const formData = new FormData();
        formData.append("file", file);
        analyzeButton.disabled = true;
        analyzeButton.textContent = "Analyzing…";
        setStatus("Uploading and analyzing the dataset…", "loading");

        try {
            const response = await fetch("/analyze-dataset", {
                method: "POST",
                credentials: "same-origin",
                body: formData
            });
            const data = await readJson(response);
            if (!response.ok) throw new Error(data.detail || "Dataset analysis failed.");

            const profile = data.understanding?.profile || {};
            if (resultFile) resultFile.textContent = data.file_name || file.name;
            if (resultRows) resultRows.textContent = formatCount(profile.rows);
            if (resultColumns) resultColumns.textContent = formatCount(profile.columns);
            if (resultDuplicates) resultDuplicates.textContent = formatCount(profile.duplicate_rows);
            if (modulesContainer) {
                modulesContainer.replaceChildren(...(data.understanding?.available_modules || []).map((name) => {
                    const module = document.createElement("div");
                    module.className = "module";
                    module.textContent = name;
                    return module;
                }));
            }
            if (analysisSection) analysisSection.classList.remove("hidden");
            if (analysisStatus) analysisStatus.textContent = "Dataset understood and analyzed successfully.";

            try {
                sessionStorage.setItem("medanexaAnalyticsData", JSON.stringify(data));
            } catch {
                throw new Error("Analysis completed, but this browser could not store the result. Try a smaller dataset.");
            }
            setStatus("Analysis complete. Opening NexaSight…", "success");
            window.location.assign("/analytics.html");
        } catch (error) {
            setStatus(error.message || "Dataset analysis failed. Please try again.", "error");
        } finally {
            analyzeButton.disabled = false;
            analyzeButton.textContent = "Analyze Dataset";
        }
    });
});

async function readJson(response) {
    try { return await response.json(); }
    catch { return {}; }
}

function formatCount(value) {
    return value === undefined || value === null ? "—" : new Intl.NumberFormat().format(Number(value));
}