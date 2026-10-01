import os
import re
import json


def clean_chunk_text(text):
    """Clean text before creating chunks."""

    if not text:
        return ""

    text = re.sub(r"\s+", " ", str(text))

    return text.strip()


def split_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks."""

    text = clean_chunk_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


# =========================================================
# PDF CHUNKING
# =========================================================

def chunk_pdf_document(
    document,
    chunk_size=1000,
    overlap=200
):
    """
    Create chunks from the extracted PDF document.
    """

    chunks = []

    pages = document.get(
        "pages",
        []
    )

    chunk_id = 1

    for page in pages:

        page_number = page.get(
            "page_number"
        )

        text = page.get(
            "text",
            ""
        )

        page_chunks = split_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:

            chunks.append({

                "chunk_id":
                    chunk_id,

                "page_number":
                    page_number,

                "text":
                    chunk

            })

            chunk_id += 1

    return {

        "document_name":
            document.get(
                "document_name"
            ),

        "file_type":
            document.get(
                "file_type"
            ),

        "total_chunks":
            len(chunks),

        "chunk_size":
            chunk_size,

        "overlap":
            overlap,

        "chunks":
            chunks

    }


# =========================================================
# DOCX CHUNKING
# =========================================================

def chunk_docx_document(
    document,
    chunk_size=1000,
    overlap=200
):
    """
    Create chunks from the extracted DOCX document.

    Includes:
    - paragraphs
    - headings
    - tables
    """

    chunks = []

    chunk_id = 1

    # -----------------------------------------------------
    # Paragraphs
    # -----------------------------------------------------

    paragraphs = document.get(
        "paragraphs",
        []
    )

    for paragraph in paragraphs:

        text = paragraph.get(
            "text",
            ""
        )

        style = paragraph.get(
            "style",
            ""
        )

        if style:
            text = f"{style}: {text}"

        paragraph_chunks = split_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in paragraph_chunks:

            chunks.append({

                "chunk_id":
                    chunk_id,

                "page_number":
                    None,

                "section":
                    "paragraph",

                "text":
                    chunk

            })

            chunk_id += 1


    # -----------------------------------------------------
    # Tables
    # -----------------------------------------------------

    tables = document.get(
        "tables",
        []
    )

    for table in tables:

        table_number = table.get(
            "table_number"
        )

        rows = table.get(
            "rows",
            []
        )

        for row in rows:

            if not row:
                continue

            # Convert table cells into readable text
            row_text = " | ".join(
                clean_chunk_text(cell)
                for cell in row
                if clean_chunk_text(cell)
            )

            if not row_text:
                continue

            table_text = (
                f"Table {table_number}: "
                f"{row_text}"
            )

            table_chunks = split_text(
                table_text,
                chunk_size=chunk_size,
                overlap=overlap
            )

            for chunk in table_chunks:

                chunks.append({

                    "chunk_id":
                        chunk_id,

                    "page_number":
                        None,

                    "section":
                        "table",

                    "table_number":
                        table_number,

                    "text":
                        chunk

                })

                chunk_id += 1


    return {

        "document_name":
            document.get(
                "document_name"
            ),

        "file_type":
            document.get(
                "file_type"
            ),

        "total_chunks":
            len(chunks),

        "chunk_size":
            chunk_size,

        "overlap":
            overlap,

        "chunks":
            chunks

    }


# =========================================================
# UNIVERSAL DOCUMENT CHUNKER
# =========================================================

def chunk_document(
    document,
    chunk_size=1000,
    overlap=200
):
    """
    Universal document chunker.

    Supports:
    - PDF
    - DOCX
    """

    file_type = document.get(
        "file_type"
    )

    if file_type == "pdf":

        return chunk_pdf_document(
            document,
            chunk_size=chunk_size,
            overlap=overlap
        )

    elif file_type == "docx":

        return chunk_docx_document(
            document,
            chunk_size=chunk_size,
            overlap=overlap
        )

    raise ValueError(
        f"Chunking is not implemented "
        f"for file type: {file_type}"
    )


# =========================================================
# SAVE CHUNKS
# =========================================================

def save_chunks(
    chunked_document,
    output_folder
):
    """
    Save generated chunks as a JSON file.
    """

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    document_name = (
        chunked_document.get(
            "document_name",
            "document"
        )
    )

    base_name = os.path.splitext(
        document_name
    )[0]

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