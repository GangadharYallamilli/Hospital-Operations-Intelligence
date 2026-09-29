import os

from documents.pdf_extractor import extract_pdf
from documents.document_chunker import chunk_document
from ai.embedding_generator import (
    load_embedding_model,
    generate_embeddings,
    save_embeddings
)


def process_document(pdf_path, output_folder):
    """
    Extract, chunk, and generate embeddings
    for any uploaded PDF document.
    """

    print(f"Processing document: {os.path.basename(pdf_path)}")

    # Step 1: Extract PDF content
    document_data = extract_pdf(pdf_path)

    # Step 2: Create chunks
    chunks_data = chunk_document(document_data)

    # Ensure document name is preserved
    document_name = os.path.basename(pdf_path)

    chunks_data["document_name"] = document_name

    for chunk in chunks_data.get("chunks", []):
       if not chunk.get("document_name"):
            chunk["document_name"] = document_name

    # Step 3: Load embedding model
    model = load_embedding_model()

    # Step 4: Generate embeddings
    embedding_data = generate_embeddings(
        chunks_data,
        model
    )

    # Step 5: Save embeddings
    output_path = save_embeddings(
        embedding_data,
        output_folder
    )

    print("Document processed successfully.")
    print(f"Embeddings saved to: {output_path}")

    return output_path


if __name__ == "__main__":

    PROJECT_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            ".."
        )
    )

    pdf_path = os.path.join(
        PROJECT_PATH,
        "member2",
        "documents",
        "original",
        "Quality_Account_2024-25.pdf"
    )

    output_folder = os.path.join(
        PROJECT_PATH,
        "member2",
        "documents",
        "processed"
    )

    process_document(
        pdf_path,
        output_folder
    )