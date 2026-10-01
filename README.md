🏥 MedaNexa — AI-Powered Hospital Intelligence
Understand. Predict. Optimize.

MedaNexa is an AI-powered hospital operations intelligence platform designed to transform hospital operational data and documents into meaningful insights, predictions, and decision-support information.
Instead of relying on a fixed dashboard, MedaNexa is designed to understand uploaded hospital datasets, identify applicable analytical capabilities, and provide the appropriate analytics, ML predictions, document intelligence, and AI-assisted interaction.
🌐 Live Website: https://mednexa-w1o4.onrender.com/
🚀 What is MedaNexa?
Hospital operational information can be spread across multiple datasets and documents such as admissions, appointments, beds, departments, equipment records, and reports.
MedaNexa brings these capabilities together into one platform:
Module	Purpose
📊 NexaSight	Hospital operational analytics
🔮 NexaPredict	ML forecasting and risk prediction
📄 NexaDocs	Document intelligence
🤖 NexaCopilot	AI-assisted interaction with hospital data
⚡ NexaPriority	Prioritization of operational tasks
📈 NexaCommand	Management insights using Power BI


✨ Key Features
📊 Operational Analytics — NexaSight
Analyze hospital operational data such as:
- Admissions
- Appointments
- Beds and occupancy
- Departments
- Medical equipment
- Waiting times
- Length of stay
- Operational KPIs
The system is designed to work with uploaded datasets rather than depending only on a single predefined dashboard.
🔮 Predictive Intelligence — NexaPredict
Machine-learning capabilities include:
- 📅 Admission demand forecasting
- 🛏️ Bed demand forecasting
- ⚠️ Equipment failure-risk prediction
- 📈 Operational trend analysis
These predictions are intended to support hospital operations and planning, not medical diagnosis.
⚡ Operational Prioritization — NexaPriority
NexaPriority combines predictive results with algorithmic prioritization.
Example workflow:
Equipment Data
      ↓
ML Failure-Risk Prediction
      ↓
Priority Score
      ↓
Priority Queue / Max Heap
      ↓
Maintenance Priority List

This demonstrates how Machine Learning + DSA can work together for an operational use case.
📄 Document Intelligence — NexaDocs
MedaNexa can work with hospital documents such as:
- PDF
- DOCX
- Hospital reports
- Operational documents
The document intelligence layer extracts useful information and prepares it for AI-assisted interaction.
🤖 AI Assistant — NexaCopilot
NexaCopilot provides an AI interface for interacting with hospital information.
It is designed to support questions such as:
What was the average length of stay?

Which department had the highest admissions?

What is the current bed occupancy?

Which equipment requires attention?

The system can route questions toward relevant SQL analytics, ML results, dataset analytics, or document-based information.
📈 Management Insights — NexaCommand
MedaNexa includes Power BI dashboards for management-level reporting.
The current Power BI implementation provides:
- Executive Overview
- Operations Analytics
- Hospital KPIs
- Admissions analysis
- Appointment analysis
- Bed occupancy
- Equipment status
- Department-level insights
Note: Dynamic Power BI analytics for arbitrary uploaded datasets is planned as a future enhancement.

🧠 Dynamic Dataset Understanding
One of the key ideas behind MedaNexa is avoiding dependency on exact column names or one fixed dataset.
The intended workflow is:
Upload Dataset
      ↓
Inspect Columns & Data Types
      ↓
Understand Dataset Structure
      ↓
Semantic Column Mapping
      ↓
Identify Dataset Type
      ↓
Determine Available Capabilities
      ↓
Run Relevant Analytics / ML
      ↓
Generate Dashboard Configuration
      ↓
Store Results in Workspace

For example, different datasets may use different names:
patient_id
patientid
patient_no
patient_number

The system can use semantic mapping to identify the underlying meaning where supported.
If only partial information is available, MedaNexa can provide the applicable capabilities instead of assuming that every module is available.
🏗️ System Architecture
                    ┌──────────────────────┐
                    │      Frontend        │
                    │   HTML / CSS / JS    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI         │
                    │    Backend API       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐     ┌──────────┐
        │   SQL    │     │    ML    │     │   RAG    │
        │  MySQL   │     │ Models   │     │Documents │
        └────┬─────┘     └────┬─────┘     └────┬─────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                     ┌─────────────────┐
                     │  NexaCopilot    │
                     │  AI Interaction │
                     └─────────────────┘

                     ┌─────────────────┐
                     │    Power BI     │
                     │ NexaCommand     │
                     └─────────────────┘

🔄 End-to-End Data Flow
Hospital User
     │
     ▼
Upload CSV / Excel / PDF / DOCX
     │
     ▼
Data / Document Understanding
     │
     ▼
Capability Detection
     │
     ├──────────────► SQL Analytics
     │
     ├──────────────► ML Predictions
     │
     ├──────────────► Document Intelligence
     │
     └──────────────► AI Interaction
                           │
                           ▼
                    Operational Insights
                           │
                           ▼
                    Smarter Decisions

🛠️ Technology Stack
Programming & Data
- Python
- Pandas
- NumPy
- SQL
- MySQL
Machine Learning
- Scikit-learn
- Random Forest
- Forecasting models
- Classification models
Backend
- FastAPI
- Uvicorn
- REST APIs
AI
- Gemini
- RAG
- Sentence Transformers
- Document processing
- AI-assisted question answering
Documents
- PDF processing
- DOCX processing
Visualization & BI
- Power BI
- HTML
- CSS
- JavaScript
Development
- Git
- GitHub
- Docker-ready architecture
- Cloud deployment
📂 Project Structure
MedaNexa/
│
├── ai/
├── app/
├── backend/
│   ├── documents/
│   ├── auth.py
│   ├── analytics.py
│   ├── data_understanding.py
│   ├── ml_service.py
│   ├── sql_analytics.py
│   ├── copilot_router.py
│   ├── nexa_priority_service.py
│   └── main.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── database/
│   └── queries/
│
├── dsa/
├── ml/
│   └── models/
│
├── notebooks/
│
├── powerbi/
│
├── research/
│
├── documents/
│
├── requirements.txt
└── README.md

📊 Development Dataset
The project uses synthetic hospital operational data for development and demonstration.
Datasets include:
- Admissions — 50,000 records
- Appointments — 60,000 records
- Beds — 15,344 records
- Departments — 14 records
- Equipment — 5,000 records
Total development records:
130,358
The datasets are designed to support:
- SQL queries
- Data cleaning
- Exploratory Data Analysis
- Data visualization
- Machine Learning
- Forecasting
- Dataset relationships
- Operational analysis
No real patient-identifiable information is used in the development datasets.

🧹 Data Processing Pipeline
Raw Data
   ↓
Validation
   ↓
Missing-Value Analysis
   ↓
Duplicate Detection
   ↓
Business-Rule Validation
   ↓
Data Cleaning
   ↓
Processed Dataset
   ↓
SQL / EDA / ML / Analytics

The project includes validation for relationships and operational business rules such as:
- Invalid department references
- Incorrect admission/discharge dates
- Appointment booking-date inconsistencies
- Invalid bed availability
- Occupancy inconsistencies
- Equipment maintenance-date inconsistencies
🤖 Machine Learning
Current ML capabilities include:
Admission Demand Forecasting
Forecasts future monthly admission demand using historical admission patterns.
Bed Demand Forecasting
Forecasts expected occupied-bed demand for upcoming days.
Equipment Failure Risk
Predicts equipment failure risk using operational equipment characteristics.
Example features include:
Equipment Type
Equipment Age
Usage Hours
Maintenance Count
Days Until Maintenance
Department

🧮 SQL & Database
MySQL is used as the structured data layer.
The database contains:
departments
admissions
appointments
beds
equipment

SQL is used for:
- KPI calculations
- Aggregations
- Joins
- Department analysis
- Appointment analysis
- Bed analysis
- Equipment analysis
- AI-assisted data queries
- ML data preparation
🔐 Multi-Hospital Architecture
MedaNexa is designed with a multi-hospital concept.
Each hospital can have its own workspace and datasets.
Hospital A
 ├── Admissions
 ├── Appointments
 ├── Beds
 └── Equipment

Hospital B
 ├── Admissions
 ├── Equipment
 └── Reports

Data isolation is handled using a hospital/user workspace context so that datasets from different hospitals are not mixed.
🎨 User Experience
We also focused on providing a clean and intuitive UI/UX rather than exposing users directly to complex technical processes.
The goal is to allow hospital users to move from:
Upload → Understand → Analyze → Predict → Ask → Decide
through a consistent interface.
☁️ Deployment
MedaNexa is being developed toward a cloud-based deployment architecture.
Current deployment components include:
- Cloud-hosted FastAPI backend
- Cloud MySQL database
- Production environment variables
- Public web application
- API-based architecture
🌐 Live Application:
https://mednexa-w1o4.onrender.com/
🔮 Future Enhancements
Planned improvements include:
- Dynamic Power BI integration for uploaded datasets
- More hospital dataset types
- Improved predictive models
- Expanded document intelligence
- More advanced operational recommendations
- Further optimization of cloud deployment
- Additional hospital management workflows
🎯 Project Objective
The objective of MedaNexa is not simply to create another hospital dashboard.
It is to build an end-to-end intelligent system that connects:
Data
 ↓
Cleaning
 ↓
EDA
 ↓
SQL
 ↓
Machine Learning
 ↓
AI / RAG
 ↓
API
 ↓
UI/UX
 ↓
Deployment

The project demonstrates how these technologies can work together as a single practical system.
👥 Team
Gangadhar Yallamilli
Data Science • Machine Learning • SQL • Backend • AI
Vennavaram Nithin Reddy
AI • RAG • Backend • Document Intelligence
📌 Disclaimer
MedaNexa is an academic/portfolio and operational intelligence project using synthetic development data.
It is designed for hospital operations and management support and is not a medical diagnosis or clinical decision-making system.
⭐ Project
MedaNexa — AI-Powered Hospital Intelligence
Understand. Predict. Optimize.

🌐 Live: https://mednexa-w1o4.onrender.com/
Built with Python • SQL • Machine Learning • FastAPI • RAG • Gemini • Power BI.
