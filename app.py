"""
Persona-Adaptive Customer Support Agent — Streamlit Application.

Provides a chat-style UI that:
    1. Accepts customer queries
    2. Classifies the user's persona
    3. Retrieves relevant knowledge from ChromaDB
    4. Checks escalation rules
    5. Generates a persona-adaptive response
"""

from __future__ import annotations

import json
import logging
from typing import Any

import streamlit as st

from src.classifier import classify_persona
from src.rag_pipeline import retrieve_relevant_chunks
from src.escalator import check_escalation
from src.generator import generate_response

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Persona-Adaptive Support Agent",
    page_icon="🤖",
    layout="wide",
)

# TODO: Add custom CSS for premium styling
# TODO: Add dark mode toggle


# ──────────────────────────────────────────────
# Pipeline orchestrator
# ──────────────────────────────────────────────
def handle_query(query: str) -> dict[str, Any]:
    """Run the full persona-adaptive pipeline for a single query.

    Args:
        query: The raw customer query.

    Returns:
        A dict with persona info, escalation status, response, and sources.
    """
    # Stage 1: Classify persona
    persona_result = classify_persona(query)
    persona = persona_result["persona"]
    confidence = persona_result["confidence"]
    reasoning = persona_result["reasoning"]

    # Stage 2: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(query)
    top_score = chunks[0]["score"] if chunks else 0.0
    sources = sorted({c["source"] for c in chunks})

    # Stage 3: Check escalation
    escalation = check_escalation(query, persona, chunks)
    if escalation:
        return {
            "query": query,
            "persona": persona,
            "persona_confidence": confidence,
            "persona_reasoning": reasoning,
            "escalation": escalation,
            "response": None,
            "sources": sources,
            "top_retrieval_score": top_score,
        }

    # Stage 4: Generate adaptive response
    answer = generate_response(query, persona, chunks)

    return {
        "query": query,
        "persona": persona,
        "persona_confidence": confidence,
        "persona_reasoning": reasoning,
        "escalation": None,
        "response": answer,
        "sources": sources,
        "top_retrieval_score": top_score,
    }


# ──────────────────────────────────────────────
# Persona badge styling
# ──────────────────────────────────────────────
_PERSONA_EMOJI: dict[str, str] = {
    "Technical Expert": "🔧",
    "Frustrated User": "😤",
    "Business Executive": "💼",
}

_PERSONA_COLOR: dict[str, str] = {
    "Technical Expert": "blue",
    "Frustrated User": "red",
    "Business Executive": "green",
}


# ──────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────
def main() -> None:
    """Render the Streamlit application."""
    # TODO: Add conversation history sidebar
    # TODO: Add document ingestion UI (file uploader)
    # TODO: Add settings panel for model / threshold configuration

    st.title("🤖 Persona-Adaptive Customer Support Agent")
    st.markdown(
        "Ask any support question — the agent detects your persona and "
        "tailors its response accordingly."
    )

    st.divider()

    # ── Chat input ───────────────────────────
    query = st.chat_input("Type your support question here…")

    if query:
        # Show user message
        with st.chat_message("user"):
            st.markdown(query)

        # Process through pipeline
        with st.spinner("Analyzing your query…"):
            try:
                result = handle_query(query)
            except Exception as exc:
                st.error(f"❌ Pipeline error: {exc}")
                logger.error("Pipeline error: %s", exc, exc_info=True)
                return

        # ── Response or escalation ───────────
        if result["escalation"]:
            with st.chat_message("assistant"):
                st.warning("⚠️ **This query has been escalated to a human agent.**")
                st.json(result["escalation"])
        else:
            with st.chat_message("assistant"):
                st.markdown(result["response"])

        # ── Sources ──────────────────────────
        if result["sources"]:
            with st.expander("📄 Sources used"):
                for src in result["sources"]:
                    st.markdown(f"- `{src}`")


if __name__ == "__main__":
    main()
