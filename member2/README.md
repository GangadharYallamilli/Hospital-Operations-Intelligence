# Member 2 — Application, AI, Documents & Frontend

## Responsibilities

Member 2 is responsible for the application and user-facing components of the
AI-Powered Hospital Operations Intelligence Platform.

### Main Responsibilities

- Hospital Registration
- Hospital Login
- Logout and Session Management
- Secure Password Hashing
- File Upload
- CSV / Excel / PDF / DOCX handling
- Dynamic Hospital Module Interface
- PDF/DOCX Document Intelligence
- AI Hospital Assistant
- Streamlit Frontend
- Power BI Integration
- Application Deployment

---

## Application Flow

Hospital Admin
↓
Register / Login
↓
Hospital Workspace
↓
Upload Hospital Files
↓
Automatic Data Understanding
↓
Dynamic Modules
↓
Analytics / ML / Documents
↓
AI Hospital Assistant
↓
Operational Recommendations

---

## Supported Files

The planned upload system supports:

- CSV
- Excel (.xlsx)
- PDF
- Word (.docx)

---

## Document Intelligence

Planned document pipeline:

Document
↓
Text Extraction
↓
Table Extraction
↓
Document Classification
↓
Chunking
↓
Embedding / Retrieval
↓
AI

Potential capabilities:

- Document summarization
- KPI extraction
- Question answering
- Important number/date extraction
- Operational issue detection
- Report comparison

The final capabilities will depend on the actual documents selected for the project.

---

## AI Hospital Assistant

The AI Assistant should be grounded in hospital-specific uploaded information.

Possible information sources:

1. SQL / structured hospital data
2. Machine Learning predictions
3. Uploaded PDF/DOCX documents
4. Document retrieval / RAG

The assistant should not answer hospital-specific questions only from
general LLM knowledge.

---

## Dynamic Modules

The application should not display every hospital module by default.

The backend will detect the available data and the Streamlit frontend will
display the corresponding modules.

Example:

Admissions + Beds
→ Admissions Analytics
→ Bed Analytics
→ Forecasting

Appointments + Equipment
→ Appointment Analytics
→ Equipment Analytics
→ Maintenance Prediction

---

## Frontend

Framework:

- Streamlit

Planned sections:

- Login
- Registration
- Hospital Workspace
- Upload Center
- Dashboard
- Analytics
- Predictions
- Documents
- AI Assistant
- Reports

---

## Power BI

Member 2 is responsible for Power BI dashboard integration.

Final dashboard pages will be decided after the project datasets are frozen.

---

## Deployment

Target:

GitHub
↓
Suitable hosting platform
↓
Public project URL

---

## Current Phase

### Phase 1 — Research

- [ ] Collect 5–10 public hospital PDF/DOCX documents
- [ ] Preserve original documents locally
- [ ] Record document metadata
- [ ] Inspect text and tables
- [ ] Identify possible AI capabilities
- [ ] Verify source and usage/license information
- [ ] Create document capability matrix

### Phase 2 — Architecture

- [ ] Finalize datasets
- [ ] Finalize database relationships
- [ ] Define dynamic module detection
- [ ] Define Member 1 ↔ Member 2 integration
- [ ] Finalize AI architecture

### Phase 3 — Development

- [ ] Authentication
- [ ] Upload Center
- [ ] Dynamic Modules
- [ ] Document Processing
- [ ] AI Assistant
- [ ] Dashboard
- [ ] Power BI
- [ ] Deployment

---

## Development Principle

# DATA → PROJECT → CODE

Features will be finalized only after inspecting the actual hospital datasets
and documents selected for the project.