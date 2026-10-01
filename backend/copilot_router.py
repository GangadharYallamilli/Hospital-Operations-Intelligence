"""Local, deterministic intent routing for hospital questions.

Routing stays local so questions and hospital data are not sent to an external
classifier.

Supported sources:
    - SQL / hospital database
    - ML predictions
    - PDF/DOCX document RAG
    - Uploaded CSV/XLSX dataset analytics

The router does not load heavy ML dependencies during application startup.
"""

from dataclasses import dataclass
from functools import lru_cache
import re


# ============================================================
# ROUTE MODEL
# ============================================================

@dataclass(frozen=True)
class Route:
    intent: str
    confidence: float
    model: str | None = None
    department: str | None = None


# ============================================================
# ML / PREDICTION PATTERNS
# ============================================================

_ML_PATTERNS = (

    (
        "bed_forecast",
        re.compile(
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}"
            r"\b(?:bed demand|occupied beds|bed capacity)\b"
            r"|"
            r"\b(?:bed demand|occupied beds|bed capacity)\b.{0,50}"
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b",
            re.I,
        ),
    ),

    (
        "length_of_stay",
        re.compile(
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}"
            r"\b(?:length of stay|\blos\b)\b"
            r"|"
            r"\b(?:length of stay|\blos\b)\b.{0,50}"
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b",
            re.I,
        ),
    ),

    (
        "equipment_failure",
        re.compile(
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?|risk)\b.{0,50}"
            r"\b(?:equipment|device|failure)\b"
            r"|"
            r"\b(?:equipment|device)\b.{0,50}"
            r"\b(?:failure risk|risk prediction|predicted failure)\b",
            re.I,
        ),
    ),

    (
        "appointment_no_show",
        re.compile(
            r"\b(?:predict(?:ed|ion)?|risk)\b.{0,50}"
            r"\b(?:no[ -]?show|missed appointment)\b"
            r"|"
            r"\b(?:no[ -]?show|missed appointment)\b.{0,50}"
            r"\b(?:predict(?:ed|ion)?|risk)\b",
            re.I,
        ),
    ),

    (
        "admission_forecast",
        re.compile(
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}"
            r"\b(?:admissions?|admission demand)\b"
            r"|"
            r"\b(?:admissions?|admission demand)\b.{0,50}"
            r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b",
            re.I,
        ),
    ),
)


# ============================================================
# RAG / DOCUMENT PATTERNS
# ============================================================

_RAG_PATTERNS = (

    # Explicit report references
    re.compile(
        r"\b(?:annual|quality|safety|inspection|policy|incident)"
        r"\s+report\b",
        re.I,
    ),

    # Explicit uploaded document references
    re.compile(
        r"\b(?:uploaded|attached|selected)"
        r"\s+(?:document|report|file)\b",
        re.I,
    ),

    # Questions explicitly asking what a document/report says
    re.compile(
        r"\b(?:what did|what does|according to|mentioned in|"
        r"stated in|said in|summari[sz]e)\b.{0,100}"
        r"\b(?:report|document|policy|file|annual|quality|safety)\b",
        re.I,
    ),

    # Document contents
    re.compile(
        r"\b(?:report|document|policy)\b.{0,100}"
        r"\b(?:mention|say|state|recommend|patient safety|"
        r"summari[sz]e)\b",
        re.I,
    ),

    # Explicit document analysis
    re.compile(
        r"\b(?:summarize|summarise|analyze|analyse|review|"
        r"explain)\b.{0,80}"
        r"\b(?:report|document|annual report|quality report|"
        r"safety report)\b",
        re.I,
    ),

    # Based on report/document
    re.compile(
        r"\b(?:according to|based on|from)\b.{0,60}"
        r"\b(?:the\s+)?(?:report|document|annual report|"
        r"quality report|safety report)\b",
        re.I,
    ),
    
        re.compile(
        r"\b(?:summarize|summary|give\s+me\s+a\s+summary|"
        r"provide\s+a\s+summary)\b.{0,60}"
        r"\b(?:uploaded|document|report|file)\b",
        re.I,
    ),

    re.compile(
        r"\b(?:uploaded|document|report|file)\b.{0,60}"
        r"\b(?:summarize|summary)\b",
        re.I,
    ),
)


# ============================================================
# DATASET / OPERATIONAL PATTERNS
# ============================================================

_DATASET_OPERATIONAL_PATTERNS = (

    # "What are the major operational issues?"
    re.compile(
        r"\b(?:major|main|key|important|critical|top)?\s*"
        r"\b(?:operational|operations)\b.{0,30}"
        r"\b(?:issues?|problems?|challenges?|concerns?)\b",
        re.I,
    ),

    # "What are the major issues?"
    re.compile(
        r"\b(?:major|main|key|important|critical|top)\b.{0,30}"
        r"\b(?:issues?|problems?|challenges?|concerns?)\b",
        re.I,
    ),

    # "What problems are identified?"
    re.compile(
        r"\b(?:issues?|problems?|challenges?|concerns?)\b.{0,40}"
        r"\b(?:identified|reported|described|discussed|"
        r"highlighted|outlined)\b",
        re.I,
    ),

    # "What are the main problems?"
    re.compile(
        r"\bwhat\s+(?:are|were)\b.{0,50}"
        r"\b(?:major|main|key|important|critical|top)\b.{0,30}"
        r"\b(?:issues?|problems?|challenges?|concerns?)\b",
        re.I,
    ),

    # Operational performance
    re.compile(
        r"\b(?:operational|operations)\b.{0,40}"
        r"\b(?:performance|performance issues|bottlenecks?|"
        r"inefficiencies?|gaps?)\b",
        re.I,
    ),

    # Hospital operational areas
    re.compile(
        r"\b(?:admission|admissions|appointment|appointments|"
        r"bed|beds|equipment|capacity|wait|waiting)\b.{0,50}"
        r"\b(?:issue|issues|problem|problems|challenge|"
        r"challenges|concern|concerns|bottleneck|inefficienc)\b",
        re.I,
    ),
)


# ============================================================
# SQL PATTERNS
# ============================================================

_SQL_PATTERNS = (

    (
        "average_length_of_stay",
        re.compile(
            r"\b(?:average|avg)\b.{0,35}"
            r"\b(?:length of stay|\blos\b)\b"
            r"|"
            r"\b(?:length of stay|\blos\b)\b.{0,35}"
            r"\b(?:average|avg)\b",
            re.I,
        ),
    ),

    (
        "most_admissions",
        re.compile(
            r"\b(?:which|what)\s+department\b.{0,50}"
            r"\b(?:most|highest|largest|maximum)\b.{0,25}"
            r"\badmissions?\b"
            r"|"
            r"\b(?:most|highest|largest)\s+admissions?\b.{0,35}"
            r"\bdepartment\b",
            re.I,
        ),
    ),

    (
        "cancelled_appointments_last_month",
        re.compile(
            r"\b(?:how many|count|number of)\b.{0,45}"
            r"\bappointments?\b.{0,25}"
            r"\b(?:cancelled|canceled)\b"
            r"|"
            r"\b(?:cancelled|canceled)\s+appointments?\b",
            re.I,
        ),
    ),

    (
        "occupied_beds",
        re.compile(
            r"\b(?:how many|count|number of)\b.{0,35}"
            r"\bbeds?\b.{0,20}\boccupied\b"
            r"|"
            r"\b(?:occupied beds|beds occupied)\b",
            re.I,
        ),
    ),

    (
        "operational_equipment",
        re.compile(
            r"\b(?:how many|count|number of)\b.{0,40}"
            r"\bequipment\b.{0,20}"
            r"\b(?:operational|working|active)\b"
            r"|"
            r"\b(?:operational|working|active)\s+equipment\s+"
            r"(?:units?|devices?)\b",
            re.I,
        ),
    ),
)


# ============================================================
# DEPARTMENT DETECTION
# ============================================================

_DEPARTMENT_PATTERN = re.compile(
    r"\b(?:in|for)\s+"
    r"([A-Za-z][A-Za-z0-9 &'/-]{1,60}?)"
    r"(?:\s+department\b|[?.!,;]|$)",
    re.I,
)


def _department_in(question: str) -> str | None:

    match = _DEPARTMENT_PATTERN.search(
        question.strip()
    )

    if not match:
        return None

    value = re.sub(
        r"\s+",
        " ",
        match.group(1),
    ).strip(
        " \t.,?!:;-"
    )

    if not value or len(value) > 80:
        return None

    return value


# ============================================================
# SEMANTIC EXAMPLES
# ============================================================

_SEMANTIC_EXAMPLES = {

    ("sql", "average_length_of_stay"): (
        "Calculate the hospital average length of stay.",
        "How many days do patients stay on average in Cardiology?",
    ),

    ("sql", "most_admissions"): (
        "Rank departments by total admissions and identify the busiest department.",
        "Which department admitted the largest number of patients?",
    ),

    ("sql", "cancelled_appointments_last_month"): (
        "Count appointments cancelled during the previous calendar month.",
        "How many bookings were called off last month?",
    ),

    ("sql", "occupied_beds"): (
        "Report the number of beds occupied in the latest hospital snapshot.",
        "How many inpatient beds are currently in use?",
    ),

    ("sql", "operational_equipment"): (
        "Count the equipment units currently in working order.",
        "How many active medical devices are there?",
    ),

    ("ml", "bed_forecast"): (
        "Forecast hospital bed demand for the coming days.",
        "Predict the expected number of occupied beds next week.",
    ),

    ("ml", "length_of_stay"): (
        "Use a trained model to predict a patient's length of stay.",
        "Estimate how long an admission is expected to last.",
    ),

    ("ml", "equipment_failure"): (
        "Estimate equipment breakdown or failure risk using the trained model.",
        "Which device is likely to fail soon?",
    ),

    ("ml", "appointment_no_show"): (
        "Predict the probability that a patient will miss an appointment.",
        "Estimate no-show risk for the appointment.",
    ),

    ("ml", "admission_forecast"): (
        "Forecast how many hospital admissions there will be next month.",
        "Predict admission demand for a future period.",
    ),

    ("rag", None): (
        "Find and summarize a statement from an uploaded hospital report.",
        "What does the quality report say about patient safety?",
        "Summarize the equipment section of the annual report.",
        "What are the major operational issues in the hospital report?",
    ),

    ("dataset", None): (
        "Describe trends and metrics in the uploaded dataset.",
        "Show me the department statistics from the analyzed file.",
        "What are the major operational issues in the hospital data?",
        "What are the main operational challenges in the dataset?",
    ),
}


# ============================================================
# OPTIONAL LOCAL SEMANTIC ROUTER
# ============================================================

@lru_cache(maxsize=1)
def _local_intent_prototypes():
    """
    Load the local embedding model only if it is already available.

    IMPORTANT:
    This function is never executed during normal application startup.
    """

    try:

        import numpy as np
        from sentence_transformers import SentenceTransformer

        labels = []
        examples = []

        for label, phrases in _SEMANTIC_EXAMPLES.items():

            for phrase in phrases:

                labels.append(label)
                examples.append(phrase)

        model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            local_files_only=True,
        )

        vectors = model.encode(
            examples,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return (
            model,
            np.asarray(vectors),
            labels,
        )

    except Exception:

        return None


def _semantic_route(
    text: str,
) -> Route | None:

    prototypes = _local_intent_prototypes()

    if prototypes is None:
        return None

    try:

        import numpy as np

        model, vectors, labels = prototypes

        query = model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]

        similarities = (
            np.asarray(vectors)
            @ np.asarray(query)
        )

        best_by_intent = {}

        for score, label in zip(
            similarities,
            labels,
        ):

            best_by_intent[label] = max(
                float(score),
                best_by_intent.get(
                    label,
                    -1.0,
                ),
            )

        ranked = sorted(
            best_by_intent.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        if not ranked:
            return None

        if ranked[0][1] < 0.62:
            return None

        if (
            len(ranked) > 1
            and ranked[0][1] - ranked[1][1] < 0.05
        ):
            return None

        (
            intent,
            model_name,
        ), score = ranked[0]

        return Route(
            intent,
            min(
                0.86,
                max(
                    0.62,
                    score,
                ),
            ),
            model=model_name,
            department=(
                _department_in(text)
                if model_name
                == "average_length_of_stay"
                else None
            ),
        )

    except Exception:

        return None


# ============================================================
# MAIN CLASSIFIER
# ============================================================

def classify_question(
    question: str,
) -> Route:

    text = " ".join(
        (question or "").split()
    )

    if not text:

        return Route(
            "clarify",
            0.0,
        )

    # ========================================================
    # MATCH INTENTS
    # ========================================================

    ml_matches = [
        model
        for model, pattern in _ML_PATTERNS
        if pattern.search(text)
    ]

    rag_matches = [
        pattern
        for pattern in _RAG_PATTERNS
        if pattern.search(text)
    ]

    dataset_operational_matches = [
        pattern
        for pattern in _DATASET_OPERATIONAL_PATTERNS
        if pattern.search(text)
    ]

    sql_matches = [
        intent
        for intent, pattern in _SQL_PATTERNS
        if pattern.search(text)
    ]

    # ========================================================
    # ML
    # ========================================================

    if (
        len(ml_matches) == 1
        and not rag_matches
    ):

        return Route(
            "ml",
            0.96,
            model=ml_matches[0],
        )

    if (
        len(ml_matches) > 1
        or (
            ml_matches
            and rag_matches
        )
    ):

        return Route(
            "clarify",
            0.35,
        )

    # ========================================================
    # EXPLICIT DOCUMENT / RAG
    # ========================================================

    # Explicit document wording always takes priority.
    #
    # Example:
    # "What are the major operational issues in the annual report?"
    #
    # This should use RAG, not dataset analytics.

    if rag_matches:

        return Route(
            "rag",
            0.94,
        )

    # ========================================================
    # DATASET OPERATIONAL QUESTIONS
    # ========================================================

    # If the question talks about operational problems but does
    # NOT mention a report/document, use the uploaded dataset.

    if dataset_operational_matches:

        return Route(
            "dataset",
            0.90,
        )

    # ========================================================
    # SQL
    # ========================================================

    if len(sql_matches) == 1:

        intent = sql_matches[0]

        return Route(
            "sql",
            0.93,
            model=intent,
            department=(
                _department_in(text)
                if intent
                == "average_length_of_stay"
                else None
            ),
        )

    if len(sql_matches) > 1:

        return Route(
            "clarify",
            0.30,
        )

    # ========================================================
    # EXPLICIT DATASET QUESTIONS
    # ========================================================

    if re.search(
        r"\b(?:in|from|within|across)\s+"
        r"(?:the\s+)?"
        r"(?:uploaded|analyzed|analysed|current)\s+dataset\b",
        text,
        re.I,
    ):

        return Route(
            "dataset",
            0.78,
        )

    if re.search(
        r"\b(?:uploaded|analyzed|analysed)\s+"
        r"(?:data|dataset|file)\b",
        text,
        re.I,
    ):

        return Route(
            "dataset",
            0.78,
        )

    # ========================================================
    # RAW SQL
    # ========================================================

    if re.match(
        r"(?is)^\s*"
        r"(?:select|insert|update|delete|drop|create|"
        r"alter|truncate|grant|revoke)\b",
        text,
    ):

        return Route(
            "clarify",
            0.10,
        )

    # ========================================================
    # SEMANTIC FALLBACK
    # ========================================================

    semantic = _semantic_route(
        text
    )

    if semantic is not None:

        return semantic

    # ========================================================
    # UNKNOWN
    # ========================================================

    return Route(
        "clarify",
        0.20,
    )