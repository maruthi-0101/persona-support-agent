"""
Document Ingestion module.

Reads TXT, MD, and PDF files from the data directory, splits them into
chunks using LangChain's RecursiveCharacterTextSplitter, generates
embeddings via Gemini (gemini-embedding-001), and upserts them into ChromaDB.

Verifies embedding model availability before starting ingestion.
Supports idempotent re-ingestion via deterministic chunk IDs.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR
from src.rag_pipeline import generate_embedding, get_collection, verify_embedding_model

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Supported file extensions
# ──────────────────────────────────────────────
_SUPPORTED_EXTENSIONS: set[str] = {".txt", ".md", ".pdf"}


# ──────────────────────────────────────────────
# File readers
# ──────────────────────────────────────────────
def _read_text_file(filepath: str) -> str:
    """Read a plain-text or markdown file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _read_pdf_file(filepath: str) -> str:
    """Extract all text from a PDF file."""
    # TODO: Add OCR fallback for scanned PDFs
    reader = PdfReader(filepath)
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _read_file(filepath: str) -> str:
    """Dispatch to the appropriate reader based on file extension.

    Args:
        filepath: Absolute path to the document.

    Returns:
        The extracted text content.

    Raises:
        ValueError: If the file extension is unsupported.
    """
    ext = Path(filepath).suffix.lower()
    if ext in {".txt", ".md"}:
        return _read_text_file(filepath)
    elif ext == ".pdf":
        return _read_pdf_file(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ──────────────────────────────────────────────
# Chunking
# ──────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    return _splitter.split_text(text)


# ──────────────────────────────────────────────
# Deterministic chunk ID
# ──────────────────────────────────────────────
def _make_chunk_id(source: str, index: int) -> str:
    """Generate a deterministic, unique ID for a chunk.

    Uses MD5 hash of source + index for idempotent upsert semantics.
    """
    raw = f"{source}::chunk::{index}"
    return hashlib.md5(raw.encode()).hexdigest()


# ──────────────────────────────────────────────
# Ingestion entry-point
# ──────────────────────────────────────────────
def ingest_documents(data_dir: str | None = None) -> dict[str, Any]:
    """Ingest all supported documents from *data_dir* into ChromaDB.

    Args:
        data_dir: Path to the directory containing documents.
                  Defaults to ``config.DATA_DIR``.

    Returns:
        A summary dict with ``files_processed``, ``total_chunks``, ``errors``.
    """
    # TODO: Add incremental ingestion (skip unchanged files)
    # TODO: Add progress callback for UI progress bars
    # TODO: Add parallel embedding generation for faster ingestion

    data_dir = data_dir or DATA_DIR
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    collection = get_collection()
    files_processed: int = 0
    total_chunks: int = 0
    errors: list[str] = []

    for filename in sorted(os.listdir(data_dir)):
        filepath = os.path.join(data_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if Path(filename).suffix.lower() not in _SUPPORTED_EXTENSIONS:
            logger.debug("Skipping unsupported file: %s", filename)
            continue

        logger.info("Processing: %s", filename)
        try:
            text = _read_file(filepath)
            if not text.strip():
                logger.warning("Empty file skipped: %s", filename)
                continue

            chunks = _chunk_text(text)
            logger.info("  → %d chunks from %s", len(chunks), filename)

            ids: list[str] = []
            embeddings: list[list[float]] = []
            documents: list[str] = []
            metadatas: list[dict[str, str]] = []

            for idx, chunk in enumerate(chunks):
                chunk_id = _make_chunk_id(filename, idx)
                embedding = generate_embedding(chunk)

                ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(chunk)
                metadatas.append({"source": filename, "chunk_index": str(idx)})

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            files_processed += 1
            total_chunks += len(chunks)

        except Exception as exc:
            error_msg = f"Error processing {filename}: {exc}"
            logger.error(error_msg)
            errors.append(error_msg)

    summary = {
        "files_processed": files_processed,
        "total_chunks": total_chunks,
        "errors": errors,
    }
    logger.info("Ingestion complete: %s", summary)
    return summary


# ──────────────────────────────────────────────
# CLI entry-point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    target_dir = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR
    print(f"📥 Ingesting documents from: {target_dir}")
    result = ingest_documents(target_dir)
    print(
        f"\n✅ Ingestion summary:\n"
        f"   Files processed : {result['files_processed']}\n"
        f"   Total chunks    : {result['total_chunks']}\n"
        f"   Errors          : {len(result['errors'])}"
    )
    if result["errors"]:
        for err in result["errors"]:
            print(f"   ⚠  {err}")
