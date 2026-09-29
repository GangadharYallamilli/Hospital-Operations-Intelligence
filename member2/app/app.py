import os
import sys
import hashlib

import streamlit as st


# =========================================================
# PROJECT PATHS
# =========================================================

APP_PATH = os.path.dirname(
    os.path.abspath(__file__)
)

MEMBER2_PATH = os.path.abspath(
    os.path.join(
        APP_PATH,
        ".."
    )
)

PROJECT_PATH = os.path.abspath(
    os.path.join(
        MEMBER2_PATH,
        ".."
    )
)

BACKEND_PATH = os.path.join(
    MEMBER2_PATH,
    "backend"
)

DOCUMENTS_PATH = os.path.join(
    BACKEND_PATH,
    "documents"
)

UPLOAD_PATH = os.path.join(
    MEMBER2_PATH,
    "documents",
    "original"
)

RAG_OUTPUT_PATH = os.path.join(
    MEMBER2_PATH,
    "documents",
    "processed"
)


# =========================================================
# PYTHON PATH
# =========================================================

sys.path.insert(
    0,
    DOCUMENTS_PATH
)

sys.path.insert(
    0,
    BACKEND_PATH
)


# =========================================================
# DEBUG / PATH VALIDATION
# =========================================================

ANALYZER_PATH = os.path.join(
    DOCUMENTS_PATH,
    "analyzer.py"
)

CAPABILITY_PATH = os.path.join(
    DOCUMENTS_PATH,
    "capability_detector.py"
)

if not os.path.isfile(ANALYZER_PATH):

    st.error(
        "analyzer.py not found at:\n\n"
        + ANALYZER_PATH
    )

    st.stop()

if not os.path.isfile(CAPABILITY_PATH):

    st.error(
        "capability_detector.py not found at:\n\n"
        + CAPABILITY_PATH
    )

    st.stop()


# =========================================================
# IMPORT BACKEND
# =========================================================

from analyzer import analyze_document
from capability_detector import detect_capabilities
from ai.semantic_search import load_embeddings, search_documents
from ai.rag_answer_generator import create_rag_answer
from sentence_transformers import SentenceTransformer

from ai.dynamic_rag_pipeline import (
    process_document
)


# =========================================================
# COMPONENT PATH
# =========================================================

COMPONENTS_PATH = os.path.join(
    APP_PATH,
    "components"
)

if COMPONENTS_PATH not in sys.path:

    sys.path.insert(
        0,
        COMPONENTS_PATH
    )


from components.dynamic_modules import (
    render_dynamic_modules
)


# =========================================================
# STREAMLIT CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Hospital Operations Intelligence",
    page_icon="🏥",
    layout="wide"
)


# =========================================================
# CREATE DIRECTORIES
# =========================================================

os.makedirs(
    UPLOAD_PATH,
    exist_ok=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "analysis_results" not in st.session_state:

    st.session_state.analysis_results = {}

if "rag_processed" not in st.session_state:
    st.session_state.rag_processed = {}


# =========================================================
# FILE HASH
# =========================================================

def get_file_hash(
    uploaded_file
):

    file_bytes = (
        uploaded_file.getvalue()
    )

    return hashlib.md5(
        file_bytes
    ).hexdigest()


# =========================================================
# SAVE UPLOADED FILE
# =========================================================

def save_uploaded_file(
    uploaded_file
):

    file_path = os.path.join(
        UPLOAD_PATH,
        uploaded_file.name
    )

    new_hash = get_file_hash(
        uploaded_file
    )

    # -----------------------------------------------------
    # Existing file
    # -----------------------------------------------------

    if os.path.exists(file_path):

        with open(
            file_path,
            "rb"
        ) as existing_file:

            existing_hash = hashlib.md5(
                existing_file.read()
            ).hexdigest()

        if existing_hash == new_hash:

            return file_path

    # -----------------------------------------------------
    # Save new file
    # -----------------------------------------------------

    with open(
        file_path,
        "wb"
    ) as output_file:

        output_file.write(
            uploaded_file.getvalue()
        )

    return file_path


# =========================================================
# CACHED ANALYSIS
# =========================================================

@st.cache_data(
    show_spinner=False
)
def analyze_uploaded_file(
    file_path,
    file_hash
):

    return analyze_document(
        file_path
    )


# =========================================================
# HEADER
# =========================================================

st.title(
    "🏥 Hospital Operations Intelligence"
)

st.write(
    "Upload hospital datasets or documents and "
    "the system will automatically detect, extract "
    "and analyze them."
)


# =========================================================
# UPLOAD CENTER
# =========================================================

st.subheader(
    "📂 Upload Center"
)

uploaded_files = st.file_uploader(
    "Upload CSV, XLSX, PDF or DOCX files",
    type=[
        "csv",
        "xlsx",
        "pdf",
        "docx"
    ],
    accept_multiple_files=True
)


# =========================================================
# NO FILE
# =========================================================

if not uploaded_files:

    st.info(
        "Upload one or more hospital datasets "
        "or documents to begin."
    )

    st.stop()


# =========================================================
# UPLOADED FILES
# =========================================================

st.subheader(
    "Uploaded Files"
)

for uploaded_file in uploaded_files:

    st.write(
        f"📄 {uploaded_file.name} "
        f"({uploaded_file.size:,} bytes)"
    )


# =========================================================
# ANALYSIS
# =========================================================

st.subheader(
    "Analysis Results"
)


for uploaded_file in uploaded_files:

    # -----------------------------------------------------
    # File hash
    # -----------------------------------------------------

    file_hash = get_file_hash(
        uploaded_file
    )

    cache_key = (
        uploaded_file.name
        + "_"
        + file_hash
    )


    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    file_path = save_uploaded_file(
        uploaded_file
    )

    # -----------------------------------------------------
     # Dynamic RAG Processing (PDF only)
    # -----------------------------------------------------

    if uploaded_file.name.lower().endswith(".pdf"):

        if cache_key not in st.session_state.rag_processed:

            try:

                with st.spinner(
                    f"Preparing RAG for {uploaded_file.name}..."
                ):

                    embedding_path = process_document(
                        file_path,
                        RAG_OUTPUT_PATH
                    )

                    st.session_state.rag_processed[
                        cache_key
                    ] = embedding_path

                st.success(
                    f"✓ RAG prepared for {uploaded_file.name}"
                )

            except Exception as error:

                st.error(
                   f"RAG processing failed for "
                   f"{uploaded_file.name}: {error}"
            )


    # -----------------------------------------------------
    # Analyze only once
    # -----------------------------------------------------

    if cache_key not in (
        st.session_state.analysis_results
    ):

        try:

            with st.spinner(
                f"Analyzing {uploaded_file.name}..."
            ):

                result = analyze_uploaded_file(
                    file_path,
                    file_hash
                )

                capabilities = (
                    detect_capabilities(
                        result
                    )
                )

                st.session_state.analysis_results[
                    cache_key
                ] = {
                    "result": result,
                    "capabilities": capabilities
                }

        except Exception as error:

            st.error(
                f"Could not analyze "
                f"{uploaded_file.name}: {error}"
            )

            continue


    # -----------------------------------------------------
    # Retrieve cached result
    # -----------------------------------------------------

    stored_data = (
        st.session_state
        .analysis_results[
            cache_key
        ]
    )

    result = stored_data[
        "result"
    ]

    capabilities = stored_data[
        "capabilities"
    ]


    # -----------------------------------------------------
    # Render modules
    # -----------------------------------------------------

    render_dynamic_modules(
        capabilities,
        result
    )

    # -----------------------------------------------------
# Document Question Answering
# -----------------------------------------------------

if cache_key in st.session_state.rag_processed:

    st.subheader("🧠 Ask Questions About This Document")

    question = st.text_input(
        "Enter your question:",
        key=f"question_{cache_key}"
    )

    if st.button(
        "Ask Question",
        key=f"ask_{cache_key}"
    ):

        if question.strip():

            try:

                with st.spinner("Searching document..."):

                    embedding_path = (
                        st.session_state
                        .rag_processed
                        .get(cache_key)
                    )

                    if not embedding_path:
                        st.error("RAG is not prepared.")
                    else:

                        embedding_data = load_embeddings(
                            embedding_path
                        )

                        model = SentenceTransformer(
                            "all-MiniLM-L6-v2"
                        )

                        retrieved_chunks = search_documents(
                            question,
                            embedding_data,
                            model,
                            top_k=5
                        )

                        answer = create_rag_answer(
                            question,
                            retrieved_chunks
                        )

                        st.markdown("### 💬 Answer")
                        st.write(answer)

                        st.markdown("### 📚 Retrieved Sources")

                        for index, chunk in enumerate(retrieved_chunks):

                            page = chunk.get("page_number", "N/A")
                            similarity = chunk.get("similarity_score", 0)
                            source = chunk.get("document_name", "Unknown")
                            text = chunk.get("text", "")

                            with st.expander(
                                f"📄 Page {page} | 🎯 Similarity: {similarity:.3f}"
                            ):

                                st.write(f"**Source:** {source}")

                                st.write(f"**Page:** {page}")

                                st.write(f"**Similarity Score:** {similarity:.3f}")

                                st.markdown("### Retrieved Text")

                                st.write(text)

            except Exception as error:

                error_message = str(error)

                if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:

                    st.warning(
                        "⚠️ Gemini API quota exceeded. "
                        "Please try again later."
                    )

                elif "503" in error_message:

                    st.warning(
                        "⚠️ Gemini service is temporarily busy. "
                        "Please try again."
                    )

                else:

                    st.error(
                        f"Question answering failed: {error}"
                    )

        else:

            st.warning("Please enter a question.")


    # -----------------------------------------------------
    # Completion
    # -----------------------------------------------------

    st.success(
        f"✓ {uploaded_file.name} analyzed"
    )