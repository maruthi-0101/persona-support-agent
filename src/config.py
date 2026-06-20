"""
Configuration module for the Persona-Adaptive Customer Support Agent.

Loads environment variables, initializes the Gemini client, and defines
all constants used across the pipeline — model identifiers, chunking
parameters, retrieval thresholds, persona definitions, and escalation rules.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai

# ──────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. Add it to your .env file or export it."
    )

# ──────────────────────────────────────────────
# Gemini Client (singleton)
# ──────────────────────────────────────────────
client: genai.Client = genai.Client(api_key=GEMINI_API_KEY)

# ──────────────────────────────────────────────
# Model identifiers
# ──────────────────────────────────────────────
GENERATION_MODEL: str = "gemini-2.5-flash-lite"
EMBEDDING_MODEL: str = "gemini-embedding-001"

# ──────────────────────────────────────────────
# ChromaDB settings
# ──────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chroma_db",
)
CHROMA_COLLECTION_NAME: str = "support_docs"

# ──────────────────────────────────────────────
# Text-splitting parameters
# ──────────────────────────────────────────────
CHUNK_SIZE: int = 400
CHUNK_OVERLAP: int = 40

# ──────────────────────────────────────────────
# Retrieval settings
# ──────────────────────────────────────────────
TOP_K: int = 5
RELEVANCE_THRESHOLD: float = 0.45

# ──────────────────────────────────────────────
# Supported personas
# ──────────────────────────────────────────────
SUPPORTED_PERSONAS: list[str] = [
    "Technical Expert",
    "Frustrated User",
    "Business Executive",
]

# ──────────────────────────────────────────────
# Escalation trigger keywords (lowercased)
# ──────────────────────────────────────────────
ESCALATION_KEYWORDS: list[str] = [
    "billing",
    "refund",
    "legal",
    "account modification",
    "account change",
    "account deletion",
    "account cancellation",
    "invoice dispute",
    "payment issue",
    "chargeback",
    "lawsuit",
    "attorney",
    "lawyer",
    "compliance",
]

# ──────────────────────────────────────────────
# Data directory
# ──────────────────────────────────────────────
DATA_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)
