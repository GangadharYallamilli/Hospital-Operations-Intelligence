# MedaNexa

**AI-Powered Hospital Intelligence**
*Understand. Predict. Optimize.*

MedaNexa is a local FastAPI application with a browser workspace for hospital data analysis and document intelligence. Pulse accepts structured uploads; NexaSight builds a dataset-specific dashboard and can add a shared MySQL analytics view; NexaPredict and NexaCommand display only model outputs the backend can actually produce; NexaDocs processes PDF/DOCX reports; NexaCopilot routes questions to the hospital SQL reader, trained models, uploaded-document RAG, or the current user's analyzed data.

## Architecture and workspace flow

```text
Pulse CSV/XLSX upload ─→ dataset profile, analytics, dashboard configuration ─→ NexaSight
                                                                   └──────────→ NexaCommand
NexaCopilot question ─→ local intent router ─→ read-only MySQL | trained ML | document RAG | uploaded dataset
MySQL query snapshot ─────────────────────────→ NexaSight + NexaCommand + NexaCopilot SQL answers
```

- **Pulse** posts CSV/XLSX files to `POST /analyze-dataset`. It detects available admissions, appointments, beds/capacity, equipment, and department modules from column names and calculates metrics supported by those fields.
- **NexaSight** renders the returned `dashboard` configuration: KPIs, charts, tables, insights, recommendations, and model availability. Its visual selection is generated from the upload; it is the dynamic Power BI-style dashboard in the web application.
- **NexaPredict** reads `GET /ml-predictions`. After an upload, this endpoint returns that user's current analysis predictions and their unavailable reasons. It does not invent output when a model is missing.
- **NexaDocs** accepts PDF/DOCX documents and structured files. PDF/DOCX use extraction, normalization, table/paragraph chunking, embeddings, and semantic retrieval. Each authenticated account's uploads and embeddings are stored under its own directory.
- **NexaCopilot** uses a local, deterministic intent router. SQL questions call only fixed SELECT query templates; prediction questions read the existing model service and return an explicit unavailable response when a model is missing; document questions call the existing user-scoped RAG pipeline; other supported questions can use the current user's upload analytics. A selected document in the UI still goes directly through `/documents/ask`.
- **NexaSight** and **NexaCommand** receive the optional shared read-only MySQL analytics snapshot from `/workspace/context`, built by the same backend query module as SQL Copilot answers. Pulse upload analytics continue to be shown alongside the SQL snapshot when both sources are available. The source label distinguishes the uploaded file from the hospital database.
- **NexaCommand** also consumes the current-user prediction dictionary, document list, and available MySQL analytics. It does not create separate prediction or SQL values.

CSV and XLSX are the supported structured dataset formats in Pulse. PDF and DOCX are the supported document formats in NexaDocs. Uploads are limited to 25 MB. Empty or unreadable structured files return an error; a general dataset with no recognized hospital module receives generic profiling rather than invented hospital metrics.

Workspace analysis is kept in server process memory and the browser's sessionStorage. Restarting FastAPI clears the server copy; upload the file again in Pulse to rebuild it. This is a single-process local application design, not a multi-instance persistence layer.

## Power BI report

The existing [`powerbi/Hospital_Operations_Intelligence.pbix`](powerbi/Hospital_Operations_Intelligence.pbix) is preserved. Its readable report metadata contains two pages, `Executive_page` and `Operations Analytics`, with card, line, bar/column, donut/pie, and 100%-stacked column visuals. The PBIX package has a 2.46 MB `DataModel` and a `Connections` entry referencing a remote Power BI report and semantic-model/dataset IDs. The embedded DataModel is in Microsoft's binary format and was not decoded as table data in this audit.

**Can the PBIX dynamically update from a user-uploaded dataset through the current web application? No.** The FastAPI upload route does not call Power BI, refresh or replace a semantic model, or rewrite the PBIX. No Power BI Service credentials or integration code are configured. The technically honest current arrangement is to keep NexaSight as the live, schema-adaptive dashboard and the PBIX as a separate Power BI deliverable. Do not describe the PBIX as updated by a Pulse upload.

For a future Service integration, first provision a Power BI tenant/workspace and an explicitly selected semantic model, define the supported schemas and tenant-level data-access policy, and configure an approved Entra ID application/service principal with least-privilege workspace access. A backend integration would then authenticate server-side, map or load uploaded data into a compatible semantic model, trigger refresh, and use supported report/embedding APIs to obtain a short-lived embed token. See Microsoft's [Power BI import API](https://learn.microsoft.com/en-us/rest/api/power-bi/imports/post-import) and [embedded token guidance](https://learn.microsoft.com/en-us/power-bi/developer/embedded/generate-embed-token). Token secrets must stay server-side. Arbitrary user CSV schemas cannot safely be pushed into one existing semantic model without a schema/mapping strategy. The app remains functional without this optional integration.

## ML availability

There are currently no installed trained model artifacts or processed source datasets under `ml/models/` and `data/processed/`. Notebook output cells contain metrics from earlier runs; those outputs are not training rows or reusable model artifacts. The only local structured hospital file is a 20-row admissions test extract. It lacks age, gender, and bed type used by the LOS notebook, so it is not used to train a model.

| Model | Current status | Source data / artifact expected by this project |
| --- | --- | --- |
| Length of stay | Unavailable | Admissions cohort with LOS target and model features; the notebook has no model-save step. |
| Admission demand | Unavailable | `data/processed/admissions/admissions_clean.csv`; `ml/models/admission_demand_forecasting_model.pkl`. |
| Bed demand | Unavailable | `data/processed/beds/beds_clean.csv`; `ml/models/bed_demand_forecasting_model.pkl`. |
| Appointment no-show | Unavailable | Labeled `data/processed/appointments/appointments_clean.csv`; the notebook has no model-save step. |
| Equipment failure/risk | Unavailable | Labeled `data/processed/equipment/equipment_clean.csv`; `ml/models/equipment_failure_model.pkl`. |

The admission/bed/equipment services already have artifact-loading paths; no matching artifacts are present. LOS and no-show currently return an explicit unavailable status. To train when real source data is supplied, populate the cleaned inputs under `data/processed/{admissions,beds,appointments,equipment}/` and run the corresponding admission and bed notebooks from `notebooks/`; run equipment training with `.\.venv\Scripts\python.exe backend\train_equipment_model.py` from the repository root. These workflows must be checked against the actual target labels and held-out evaluation before their artifacts are used. The appointment notebook currently does not persist its trained pipeline, and the LOS notebook currently does not persist its trained estimator, so those models also need compatible save and inference steps in `backend/ml_service.py` before they can become available. Do not reuse the notebook's old metric output as a live prediction or performance guarantee.

## Document AI and external services

PDF extraction uses `pdfplumber`; DOCX extraction uses `python-docx`. Extracted text and tables retain page/table/section metadata through chunking, embeddings, and search results. Sentence Transformers uses `all-MiniLM-L6-v2`; its model files must already be cached or be obtained from the model registry on first use. Without an available model, document processing cannot complete.

If `GEMINI_API_KEY` is configured, NexaDocs can request a concise answer from Gemini using retrieved document passages and a prompt that limits the answer to that context. Without the key or if the provider call fails, it returns retrieved passages with page/table/section labels instead. This external provider path is not required for the rest of the application. Do not send hospital documents to an external provider unless the hospital has approved that processing.

## Authentication and data handling

Registration and login are stored in local SQLite (`database/auth.db`). Passwords use salted PBKDF2-HMAC-SHA256 hashes; the signed session cookie contains only the user ID. Workspace pages and protected APIs require an authenticated session. Document uploads and generated embeddings are isolated into per-user directories. Legacy files in the old shared `backend/documents/uploads/` or `processed/` root are not assigned to an account automatically; they remain on disk but are not included in a user's document list.

For local development, the app generates a temporary session-signing key if `SESSION_SECRET_KEY` is unset; sessions will not survive a server restart. Before deployment, configure a stable, private `SESSION_SECRET_KEY` and set `SESSION_HTTPS_ONLY=true` behind HTTPS. `.env` and `.env.*` are ignored by Git; `.env.example` may be committed only when it contains placeholders and no secrets.

Optional MySQL import scripts use `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE`. For those imports, `MEDANEXA_PROCESSED_DATA` can point to a directory containing the expected cleaned CSV subfolders. The current ML training and inference code reads from the project `data/processed/` paths listed above.

### Optional read-only SQL analytics

The SQL reader uses a dedicated account and does not fall back to importer credentials. Configure `MYSQL_READONLY_USER` and `MYSQL_READONLY_PASSWORD` plus `MYSQL_HOST` (default `127.0.0.1`), `MYSQL_PORT` (default `3306`), and `MYSQL_DATABASE` (default `hospital_operations`) in the application environment. Grant that account only `SELECT` on the five analytics tables (`departments`, `admissions`, `appointments`, `beds`, `equipment`); the reader also opens read-only transactions. Do not use the import/admin account as the Copilot reader. If the read-only credentials or connection are absent, the app remains available and reports structured database analytics as unavailable.

Supported Copilot database questions include average length of stay (optionally for a department), department with the most admissions, cancelled appointments in the previous calendar month, occupied beds in the latest recorded bed snapshot, and equipment units with an operational status. Query logic is reused from `database/queries/01_basic_analytics.sql` through `04_equipment_analytics.sql` where those files already define the aggregation. The appointment last-month count and latest bed snapshot use additional fixed SELECT statements because the query files do not currently define those exact time scopes. User text is never executed as SQL; department text is passed as a bound parameter. `NexaSight` and `NexaCommand` use the same backend query module and identify the MySQL source separately from an uploaded Pulse file.

Intent classification stays local to avoid transmitting hospital questions for routing. High-confidence multiword patterns route the documented SQL and model intents; paraphrases that do not match those patterns can be scored against fixed intent examples with the locally cached `all-MiniLM-L6-v2` Sentence Transformer already used by RAG. The model is loaded with local-only files, never downloaded as part of routing, and close or low-confidence matches receive a clarification prompt. A document selected in the Copilot UI continues to invoke `/documents/ask` directly. RAG extraction, embeddings, semantic retrieval, and grounded answer generation remain unchanged.

## Run locally

The current project virtual environment is Python 3.12.14. From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), register a local account, then sign in. The workspace is protected; `/home.html`, `/login.html`, and `/register.html` are public.

## Repository map

- `app/` — public and authenticated workspace HTML, JavaScript, and CSS
- `backend/` — FastAPI routes, authentication, dataset understanding, analytics, dashboard configuration, ML service, and document/RAG pipeline
- `database/` — local authentication database (ignored) and optional SQL/MySQL scripts
- `notebooks/` — historical exploration and model-training notebooks
- `powerbi/` — separate Power BI report deliverable
- `data/processed/`, `ml/models/` — expected input and output locations when real training datasets/artifacts are supplied
