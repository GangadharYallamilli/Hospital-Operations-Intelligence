import os
from google import genai


def create_rag_answer(question, retrieved_chunks):
    """
    Generate an answer using retrieved hospital document context.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set."
        )

    client = genai.Client(api_key=api_key)
    # Keep only relevant chunks
    filtered_chunks = [
        chunk
        for chunk in retrieved_chunks
        if chunk.get("similarity_score", 0) >= 0.45
    ]

    # Use retrieved chunks if none pass the threshold
    if not filtered_chunks:
        filtered_chunks = retrieved_chunks

    context = "\n\n".join(
    [
        f"""
    Source: {chunk.get('document_name', 'Unknown document')}
    Page: {chunk.get('page_number', 'Unknown')}

    Text:
    {chunk.get('text', '')}
    """
        for chunk in filtered_chunks
    ]
)

    prompt = f"""
You are an AI Hospital Operations Assistant.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not invent information.
2. If the answer is not available, say so clearly.
3. Provide a concise and factual response.
4. Mention the source document and relevant page numbers when possible.
5. Do not create citations that are not present in the context.

Document Context:
{context}

User Question:
{question}
"""

    import time

    response = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            break

        except Exception as error:
            if "503" in str(error) and attempt < 2:
                time.sleep(5)
            else:
                raise error

    return response.text


if __name__ == "__main__":
    print("RAG Answer Generator created successfully.")
