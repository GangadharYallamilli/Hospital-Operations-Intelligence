"""Local, deterministic intent routing for hospital questions.

Routing stays local so questions and hospital data are not sent to an external
classifier. Multiword intents and required concepts are used together; a
low-confidence or conflicting question is sent for clarification.
"""

from dataclasses import dataclass
from functools import lru_cache
import re


@dataclass(frozen=True)
class Route:
    intent: str
    confidence: float
    model: str | None = None
    department: str | None = None


_ML_PATTERNS = (
    ("bed_forecast", re.compile(r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}\b(?:bed demand|occupied beds|bed capacity)\b|\b(?:bed demand|occupied beds|bed capacity)\b.{0,50}\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b", re.I)),
    ("length_of_stay", re.compile(r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}\b(?:length of stay|\blos\b)\b|\b(?:length of stay|\blos\b)\b.{0,50}\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b", re.I)),
    ("equipment_failure", re.compile(r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?|risk)\b.{0,50}\b(?:equipment|device|failure)\b|\b(?:equipment|device)\b.{0,50}\b(?:failure risk|risk prediction|predicted failure)\b", re.I)),
    ("appointment_no_show", re.compile(r"\b(?:predict(?:ed|ion)?|risk)\b.{0,50}\b(?:no[ -]?show|missed appointment)\b|\b(?:no[ -]?show|missed appointment)\b.{0,50}\b(?:predict(?:ed|ion)?|risk)\b", re.I)),
    ("admission_forecast", re.compile(r"\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b.{0,50}\b(?:admissions?|admission demand)\b|\b(?:admissions?|admission demand)\b.{0,50}\b(?:predict(?:ed|ion)?|forecast(?:ing)?)\b", re.I)),
)

_RAG_PATTERNS = (
    re.compile(r"\b(?:annual|quality|safety|inspection|policy|incident) report\b", re.I),
    re.compile(r"\b(?:uploaded|attached|selected) (?:document|report|file)\b", re.I),
    re.compile(r"\b(?:what did|what does|according to|mentioned in|stated in|said in|summari[sz]e)\b.{0,100}\b(?:report|document|policy|file|annual|quality|safety)\b", re.I),
    re.compile(r"\b(?:report|document|policy)\b.{0,100}\b(?:mention|say|state|recommend|patient safety|summari[sz]e)\b", re.I),
)

_SQL_PATTERNS = (
    ("average_length_of_stay", re.compile(r"\b(?:average|avg)\b.{0,35}\b(?:length of stay|\blos\b)\b|\b(?:length of stay|\blos\b)\b.{0,35}\b(?:average|avg)\b", re.I)),
    ("most_admissions", re.compile(r"\b(?:which|what) department\b.{0,50}\b(?:most|highest|largest|maximum)\b.{0,25}\badmissions?\b|\b(?:most|highest|largest) admissions?\b.{0,35}\bdepartment\b", re.I)),
    ("cancelled_appointments_last_month", re.compile(r"\b(?:how many|count|number of)\b.{0,45}\bappointments?\b.{0,25}\b(?:cancelled|canceled)\b|\b(?:cancelled|canceled) appointments?\b", re.I)),
    ("occupied_beds", re.compile(r"\b(?:how many|count|number of)\b.{0,35}\bbeds?\b.{0,20}\boccupied\b|\b(?:occupied beds|beds occupied)\b", re.I)),
    ("operational_equipment", re.compile(r"\b(?:how many|count|number of)\b.{0,40}\bequipment\b.{0,20}\b(?:operational|working|active)\b|\b(?:operational|working|active) equipment (?:units?|devices?)\b", re.I)),
)

_DEPARTMENT_PATTERN = re.compile(
    r"\b(?:in|for)\s+([A-Za-z][A-Za-z0-9 &'/-]{1,60}?)(?:\s+department\b|[?.!,;]|$)",
    re.I,
)

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
    ),
    ("dataset", None): (
        "Describe trends and metrics in the uploaded dataset.",
        "Show me the department statistics from the analyzed file.",
    ),
}


@lru_cache(maxsize=1)
def _local_intent_prototypes():
    """Load the already-used RAG embedding model from cache only."""
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        labels = []
        examples = []
        for label, phrases in _SEMANTIC_EXAMPLES.items():
            for phrase in phrases:
                labels.append(label)
                examples.append(phrase)
        model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        vectors = model.encode(examples, normalize_embeddings=True, convert_to_numpy=True)
        return model, np.asarray(vectors), labels
    except Exception:
        # Pattern routing remains available if the local RAG model is absent.
        return None


def _semantic_route(text: str) -> Route | None:
    prototypes = _local_intent_prototypes()
    if prototypes is None:
        return None
    try:
        import numpy as np

        model, vectors, labels = prototypes
        query = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        similarities = np.asarray(vectors) @ np.asarray(query)
        best_by_intent = {}
        for score, label in zip(similarities, labels):
            best_by_intent[label] = max(float(score), best_by_intent.get(label, -1.0))
        ranked = sorted(best_by_intent.items(), key=lambda item: item[1], reverse=True)
        if not ranked or ranked[0][1] < 0.62:
            return None
        if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.05:
            return None
        (intent, model_name), score = ranked[0]
        return Route(intent, min(0.86, max(0.62, score)), model=model_name,
                     department=_department_in(text) if model_name == "average_length_of_stay" else None)
    except Exception:
        return None


def _department_in(question: str) -> str | None:
    match = _DEPARTMENT_PATTERN.search(question.strip())
    if not match:
        return None
    value = re.sub(r"\s+", " ", match.group(1)).strip(" \t.,?!:;-")
    if not value or len(value) > 80:
        return None
    return value


def classify_question(question: str) -> Route:
    text = " ".join((question or "").split())
    if not text:
        return Route("clarify", 0.0)

    ml_matches = [model for model, pattern in _ML_PATTERNS if pattern.search(text)]
    rag_matches = [pattern for pattern in _RAG_PATTERNS if pattern.search(text)]
    sql_matches = [intent for intent, pattern in _SQL_PATTERNS if pattern.search(text)]

    # Prediction language plus an explicit supported target is a strong ML
    # signal. Report/document language wins only when it is not a model ask.
    if len(ml_matches) == 1 and not rag_matches:
        return Route("ml", 0.96, model=ml_matches[0])
    if len(ml_matches) > 1 or (ml_matches and rag_matches):
        return Route("clarify", 0.35)
    if rag_matches:
        return Route("rag", 0.94)
    if len(sql_matches) == 1:
        intent = sql_matches[0]
        return Route("sql", 0.93, model=intent, department=_department_in(text) if intent == "average_length_of_stay" else None)
    if len(sql_matches) > 1:
        return Route("clarify", 0.3)

    # Keep the previous upload-grounded assistant for questions which do not
    # match a database, model, or document intent.
    if re.search(r"\b(?:in|from|within|across) (?:the )?(?:uploaded|analyzed|current) dataset\b", text, re.I):
        return Route("dataset", 0.78)
    if re.match(r"(?is)^\s*(?:select|insert|update|delete|drop|create|alter|truncate|grant|revoke)\b", text):
        return Route("clarify", 0.1)
    semantic = _semantic_route(text)
    if semantic is not None:
        return semantic
    return Route("clarify", 0.2)
