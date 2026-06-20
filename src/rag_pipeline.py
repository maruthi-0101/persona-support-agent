"""
RAG (Retrieval-Augmented Generation) Pipeline module.

Handles:
    • Embedding generation via Gemini (gemini-embedding-001)
    • ChromaDB PersistentClient initialization with cosine similarity
    • Top-K vector retrieval against ingested support documents
    • Embedding model availability verification

Each retrieved chunk includes:
    - text:   the chunk content
    - source: originating filename
    - score:  cosine similarity (1 - distance)
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings

from src.config import (
    client,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    TOP_K,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# ChromaDB client & collection (module-level singletons)
# ──────────────────────────────────────────────
_chroma_client: chromadb.ClientAPI = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False),
)

_collection: chromadb.Collection = _chroma_client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def get_collection() -> chromadb.Collection:
    """Return the singleton ChromaDB collection (used by ingest_data)."""
    return _collection


# ──────────────────────────────────────────────
# Embedding model verification
# ──────────────────────────────────────────────
def verify_embedding_model() -> bool:
    """Verify that the configured Gemini embedding model is available.

    Sends a lightweight test embedding request to confirm the model
    exists and the API key has access. Should be called before bulk
    ingestion to fail fast on configuration errors.

    Returns:
        True if the model is reachable and functional.

    Raises:
        RuntimeError: If the model is unavailable, deprecated, or the
                      API key lacks permissions.
    """
    test_text = "model availability check"
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=test_text,
        )
        if response.embeddings and len(response.embeddings[0].values) > 0:
            dim = len(response.embeddings[0].values)
            logger.info(
                "✅ Embedding model '%s' verified — %d dimensions.",
                EMBEDDING_MODEL,
                dim,
            )
            return True
        else:
            raise RuntimeError(
                f"Model '{EMBEDDING_MODEL}' returned an empty embedding."
            )
    except Exception as exc:
        logger.error(
            "❌ Embedding model '%s' verification failed: %s",
            EMBEDDING_MODEL,
            exc,
        )
        raise RuntimeError(
            f"Embedding model '{EMBEDDING_MODEL}' is not available. "
            f"Ensure your API key has access and the model ID is correct. "
            f"Error: {exc}"
        ) from exc


# ──────────────────────────────────────────────
# Embedding helper
# ──────────────────────────────────────────────
def generate_embedding(text: str) -> list[float]:
    """Generate a dense embedding vector for a single text string.

    Uses the Gemini embedding API (gemini-embedding-001).

    Args:
        text: The input text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        ValueError: If the input text is empty.
        RuntimeError: If the Gemini embedding API call fails.
    """
    # TODO: Add batch embedding support for faster ingestion
    # TODO: Implement embedding cache to avoid re-embedding identical chunks

    if not text or not text.strip():
        raise ValueError("Cannot embed an empty string.")

    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        embedding: list[float] = response.embeddings[0].values
        return embedding
    except Exception as exc:
        logger.error(
            "Embedding generation failed (model=%s): %s", EMBEDDING_MODEL, exc
        )
        raise RuntimeError(
            f"Gemini embedding API error (model={EMBEDDING_MODEL}): {exc}"
        ) from exc


# ──────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────
def retrieve_relevant_chunks(
    query: str,
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """Retrieve the top-K most relevant document chunks for a query.

    Uses cosine similarity via ChromaDB. Returns a list of dicts:
        {"text": str, "source": str, "score": float}

    Args:
        query: The user query string.
        top_k: Number of chunks to retrieve.

    Returns:
        A list of result dicts sorted by descending similarity.

    Raises:
        RuntimeError: If embedding or retrieval fails.
    """
    # TODO: Add metadata filtering (e.g., filter by document type)
    # TODO: Add hybrid search combining keyword + vector retrieval
    # TODO: Implement result re-ranking with a cross-encoder

    if _collection.count() == 0:
        logger.warning("ChromaDB collection is empty — run ingest_data first.")
        return []

    query_embedding = generate_embedding(query)

    try:
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, _collection.count()),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        raise RuntimeError(f"Vector retrieval error: {exc}") from exc

    chunks: list[dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        similarity_score = round(1.0 - dist, 4)
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": similarity_score,
            }
        )

    chunks.sort(key=lambda c: c["score"], reverse=True)

    logger.info(
        "Retrieved %d chunks (top score: %.4f)",
        len(chunks),
        chunks[0]["score"] if chunks else 0.0,
    )
    return chunks

