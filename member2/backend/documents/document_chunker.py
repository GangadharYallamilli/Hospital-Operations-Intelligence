import os
import re
import json


def clean_chunk_text(text):
    """Clean text before creating chunks."""

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""

    text = clean_chunk_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def chunk_pdf_document(document, chunk_size=1000, overlap=200):
    """
    Create chunks from the extracted PDF document.
    """

    chunks = []

    pages = document.get("pages", [])

    chunk_id = 1

    for page in pages:

        page_number = page.get("page_number")
        text = page.get("text", "")

        page_chunks = split_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:

            chunks.append({
                "chunk_id": chunk_id,
                "page_number": page_number,
                "text": chunk
            })

            chunk_id += 1

    return {
        "document_name": document.get("document_name"),
        "file_type": document.get("file_type"),
        "total_chunks": len(chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks": chunks
    }


def chunk_document(document, chunk_size=1000, overlap=200):
    """Universal document chunker."""

    file_type = document.get("file_type")

    if file_type == "pdf":
        return chunk_pdf_document(
            document,
            chunk_size=chunk_size,
            overlap=overlap
        )

    raise ValueError(
        f"Chunking is not implemented for file type: {file_type}"
    )


def save_chunks(chunked_document, output_folder):
    """
    Save generated chunks as a JSON file.
    """

    os.makedirs(output_folder, exist_ok=True)

    document_name = chunked_document.get(
        "document_name",
        "document"
    )

    base_name = os.path.splitext(document_name)[0]

    output_path = os.path.join(
        output_folder,
        base_name + "_chunks.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunked_document,
            file,
            ensure_ascii=False,
            indent=2
        )

    return output_path


if __name__ == "__main__":

    import sys

    DOCUMENTS_PATH = os.path.dirname(
        os.path.abspath(__file__)
    )

    PROJECT_PATH = os.path.abspath(
        os.path.join(
            DOCUMENTS_PATH,
            "..",
            "..",
            ".."
        )
    )

    if DOCUMENTS_PATH not in sys.path:
        sys.path.insert(0, DOCUMENTS_PATH)

    from pdf_extractor import extract_pdf

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
        "chunks"
    )

    print("Extracting PDF...")

    extracted_document = extract_pdf(pdf_path)

    print("Creating chunks...")

    chunked_document = chunk_pdf_document(
        extracted_document,
        chunk_size=1000,
        overlap=200
    )

    print("\nDocument:", chunked_document["document_name"])
    print("Total chunks:", chunked_document["total_chunks"])

    print("\nSaving chunks...")

    output_path = save_chunks(
        chunked_document,
        output_folder
    )

    print("Chunks saved to:")
    print(output_path)

    print("\nFirst 3 chunks:\n")

    for chunk in chunked_document["chunks"][:3]:

        print("-" * 60)
        print("Chunk ID:", chunk["chunk_id"])
        print("Page:", chunk["page_number"])
        print("Text:")
        print(chunk["text"][:500])