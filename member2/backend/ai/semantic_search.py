import os
import json
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "all-MiniLM-L6-v2"


def load_embeddings(embedding_file):
    """Load saved embeddings."""

    with open(embedding_file, "r", encoding="utf-8") as file:
        return json.load(file)


def search_documents(query, embedding_data, model, top_k=5):
    """Find the most relevant document chunks."""

    chunks = embedding_data.get("chunks", [])

    if not chunks:
        raise ValueError("No chunks found.")

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    document_embeddings = np.array([
        chunk["embedding"]
        for chunk in chunks
    ])

    similarities = cosine_similarity(
        query_embedding,
        document_embeddings
    )[0]

    ranked_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for index in ranked_indices:
        chunk = chunks[index]

        results.append({
            "chunk_id": chunk.get("chunk_id"),
            "page_number": chunk.get("page_number"),
            "page_end": chunk.get("page_end"),
            "document_name": chunk.get(
                "document_name",
                embedding_data.get("document_name", "Unknown document")
            ),
            "text": chunk.get("text", ""),
            "similarity_score": float(similarities[index])
        })

    return results


def semantic_search(query, top_k=5):
    """Load embeddings and perform semantic search."""

    documents_path = os.path.dirname(
        os.path.abspath(__file__)
    )

    project_path = os.path.abspath(
        os.path.join(
            documents_path,
            "..",
            "..",
            ".."
        )
    )

    embedding_file = os.path.join(
        project_path,
        "member2",
        "documents",
        "processed",
        "Quality_Account_2024-25_embeddings.json"
    )

    embedding_data = load_embeddings(embedding_file)

    model = SentenceTransformer(MODEL_NAME)

    return search_documents(
        query,
        embedding_data,
        model,
        top_k
    )


if __name__ == "__main__":

    print("Loading embeddings...")

    documents_path = os.path.dirname(
        os.path.abspath(__file__)
    )

    project_path = os.path.abspath(
        os.path.join(
            documents_path,
            "..",
            "..",
            ".."
        )
    )

    embedding_file = os.path.join(
        project_path,
        "member2",
        "documents",
        "processed",
        "Quality_Account_2024-25_embeddings.json"
    )

    embedding_data = load_embeddings(embedding_file)

    print(
        "Chunks found:",
        embedding_data.get("total_chunks", 0)
    )

    print("Loading model...")

    model = SentenceTransformer(MODEL_NAME)

    query = input("\nEnter your question: ")

    results = search_documents(
        query,
        embedding_data,
        model,
        top_k=5
    )

    print("\nRelevant Results:\n")

    for result in results:

        print("-" * 70)
        print("Chunk ID:", result["chunk_id"])
        print("Page:", result["page_number"])
        print(
            "Similarity:",
            round(result["similarity_score"], 4)
        )
        print("Text:")
        print(result["text"][:1000])
