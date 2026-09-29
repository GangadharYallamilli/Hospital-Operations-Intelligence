import os
import json

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


def load_embedding_model():
    """Load the sentence-transformer embedding model."""

    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded.")

    return model


def load_chunks(chunks_file):
    with open(chunks_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        normalized_chunks = []

        for index, chunk in enumerate(data):
            normalized_chunks.append({
                "chunk_id": index + 1,
                "page_number": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "text": chunk.get("text", ""),
                "document_name": chunk.get("document_name"),
                "source_type": chunk.get("source_type")
            })

        return {
            "document_name": data[0].get(
                "document_name",
                os.path.basename(chunks_file)
            ).replace("_chunks.json", ".pdf"),
            "file_type": "pdf",
            "total_chunks": len(normalized_chunks),
            "chunks": normalized_chunks
        }

    if isinstance(data, dict):
        return data

    raise ValueError("Unsupported chunks JSON format.")


def generate_embeddings(chunks_data, model):
    """Generate embeddings for document chunks."""

    chunks = chunks_data.get("chunks", [])

    if not chunks:
        raise ValueError("No chunks found.")

    texts = [
        chunk.get("text", "")
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    result = []

    for chunk, embedding in zip(chunks, embeddings):

        result.append({
            "chunk_id": chunk.get("chunk_id"),
            "page_number": chunk.get("page_number"),
            "page_end": chunk.get("page_end"),
            "document_name": chunk.get("document_name"),
            "source_type": chunk.get("source_type"),
            "text": chunk.get("text"),
            "embedding": embedding.tolist()
        })

    return {
        "document_name": chunks_data.get("document_name"),
        "file_type": chunks_data.get("file_type"),
        "total_chunks": len(result),
        "model": MODEL_NAME,
        "embedding_dimension": len(result[0]["embedding"]),
        "chunks": result
    }


def save_embeddings(embedding_data, output_folder):
    """Save embeddings to JSON."""

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    document_name = embedding_data.get(
        "document_name",
        "document"
    )

    base_name = os.path.splitext(document_name)[0]

    output_path = os.path.join(
        output_folder,
        base_name + "_embeddings.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embedding_data,
            file,
            ensure_ascii=False
        )

    return output_path


if __name__ == "__main__":

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

    chunks_file = os.path.join(
        PROJECT_PATH,
        "member2",
        "documents",
        "chunks",
        "Quality_Account_2024-25_chunks.json"
    )

    output_folder = os.path.join(
        PROJECT_PATH,
        "member2",
        "documents",
        "processed"
    )

    print("Loading chunks...")

    chunks_data = load_chunks(chunks_file)

    print(
        "Chunks found:",
        chunks_data.get("total_chunks", 0)
    )

    model = load_embedding_model()

    print("Generating embeddings...")

    embedding_data = generate_embeddings(
        chunks_data,
        model
    )

    print(
        "\nEmbedding dimension:",
        embedding_data["embedding_dimension"]
    )

    output_path = save_embeddings(
        embedding_data,
        output_folder
    )

    print("\nEmbeddings saved to:")
    print(output_path)