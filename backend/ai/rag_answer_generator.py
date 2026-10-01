# =========================================================
# RAG ANSWER GENERATOR
# =========================================================
#
# Uses the 5-key Gemini manager.
#
# Flow:
#
# User Question
#       ↓
# Retrieved Document Chunks
#       ↓
# Gemini Key Manager
#       ↓
# Key 1 → Key 2 → Key 3 → Key 4 → Key 5
#       ↓
# Gemini Answer
#
# If Gemini is unavailable:
#       ↓
# Local document-based fallback
#
# =========================================================


from backend.ai.gemini_key_manager import gemini_manager


# =========================================================
# LOCAL FALLBACK ANSWER
# =========================================================


def local_fallback_answer(question, retrieved_chunks):
    """
    Generate a simple answer from retrieved document chunks
    when Gemini is unavailable.
    """

    if not retrieved_chunks:

        return (
            "I could not find relevant information "
            "in the uploaded document."
        )

    answer_parts = []

    for chunk in retrieved_chunks[:3]:

        text = chunk.get("text", "").strip()

        if not text:
            continue

        # -------------------------------------------------
        # Determine document section
        # -------------------------------------------------

        page_number = chunk.get("page_number")

        section = chunk.get("section")

        table_number = chunk.get("table_number")

        # -------------------------------------------------
        # PDF source
        # -------------------------------------------------

        if page_number is not None:

            source_label = f"Page {page_number}"

        # -------------------------------------------------
        # DOCX table source
        # -------------------------------------------------

        elif (
            section == "table"
            and table_number is not None
        ):

            source_label = f"Table {table_number}"

        # -------------------------------------------------
        # DOCX paragraph source
        # -------------------------------------------------

        elif section == "paragraph":

            source_label = "Paragraph"

        # -------------------------------------------------
        # Other DOCX content
        # -------------------------------------------------

        else:

            source_label = "Document section"

        answer_parts.append(
            f"[{source_label}] {text[:700]}"
        )

    if not answer_parts:

        return (
            "I could not find relevant information "
            "in the uploaded document."
        )

    return (
        "Gemini is temporarily unavailable, so here is "
        "the relevant information retrieved directly "
        "from the document:\n\n"
        + "\n\n".join(answer_parts)
    )


# =========================================================
# BUILD DOCUMENT CONTEXT
# =========================================================


def build_document_context(retrieved_chunks):
    """
    Convert retrieved document chunks into a structured
    context string for Gemini.
    """

    context_parts = []

    for chunk in retrieved_chunks:

        text = chunk.get("text", "").strip()

        if not text:
            continue

        page_number = chunk.get("page_number")

        section = chunk.get("section")

        table_number = chunk.get("table_number")

        # ---------------------------------------------
        # PDF
        # ---------------------------------------------

        if page_number is not None:

            source_label = f"Page {page_number}"

        # ---------------------------------------------
        # DOCX table
        # ---------------------------------------------

        elif (
            section == "table"
            and table_number is not None
        ):

            source_label = f"Table {table_number}"

        # ---------------------------------------------
        # DOCX paragraph
        # ---------------------------------------------

        elif section == "paragraph":

            source_label = "Paragraph"

        # ---------------------------------------------
        # Other
        # ---------------------------------------------

        else:

            source_label = "Document section"

        context_parts.append(
            f"{source_label}:\n{text}"
        )

    return "\n\n".join(context_parts)


# =========================================================
# CREATE RAG ANSWER
# =========================================================


def create_rag_answer(question, retrieved_chunks):
    """
    Generate an answer using Gemini.

    Gemini requests are handled by the five-key manager.

    If all Gemini keys are unavailable, the function
    falls back to the retrieved document content.
    """

    # -----------------------------------------------------
    # No retrieved information
    # -----------------------------------------------------

    if not retrieved_chunks:

        return local_fallback_answer(
            question,
            retrieved_chunks
        )

    # =====================================================
    # BUILD DOCUMENT CONTEXT
    # =====================================================

    context = build_document_context(
        retrieved_chunks
    )

    if not context.strip():

        return local_fallback_answer(
            question,
            retrieved_chunks
        )

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are a hospital document assistant.

Answer the user's question using ONLY the
provided document context.

Do not invent information.

If the answer is not present in the context,
say:

"I could not find this information in the uploaded document."

Give a clear and concise answer.

User question:
{question}

Document context:
{context}
"""

    # =====================================================
    # GEMINI — 5 KEY ROTATION
    # =====================================================

    try:

        response_text = gemini_manager.generate(
            prompt=prompt,
            model_name="gemini-3.6-flash"
        )

        # -------------------------------------------------
        # Gemini successfully generated an answer
        # -------------------------------------------------

        if response_text:

            return response_text

        # -------------------------------------------------
        # All Gemini keys unavailable
        # -------------------------------------------------

        print(
            "All Gemini API keys are currently unavailable."
        )

        return local_fallback_answer(
            question,
            retrieved_chunks
        )

    except Exception as error:

        print(
            "Gemini manager unavailable:",
            repr(error)
        )

        # -------------------------------------------------
        # Local fallback
        # -------------------------------------------------

        return local_fallback_answer(
            question,
            retrieved_chunks
        )