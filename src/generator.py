"""
Adaptive Response Generator module.

Generates persona-tailored responses by combining the classified persona
with retrieved context chunks and sending them to Gemini for synthesis.

Persona → Response style:
    • Technical Expert   → detailed, code-aware, structured
    • Frustrated User    → empathetic, bullet-point, action-oriented
    • Business Executive → concise, metrics-driven, ROI-focused
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import client, GENERATION_MODEL

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Persona-specific system instructions
# ──────────────────────────────────────────────
_PERSONA_INSTRUCTIONS: dict[str, str] = {
    "Technical Expert": (
        "You are a senior technical support engineer. "
        "Provide a detailed, technically precise response. "
        "Include specific configuration steps, code snippets, CLI commands, "
        "or architecture details where applicable. "
        "Use technical terminology appropriate for an experienced developer. "
        "Structure your answer with clear headings and numbered steps."
    ),
    "Frustrated User": (
        "You are an empathetic, patient customer support specialist. "
        "The customer is frustrated — acknowledge their feelings first. "
        "Respond using SHORT, easy-to-follow bullet points. "
        "Focus on immediate, actionable solutions. "
        "Avoid jargon. Keep the tone warm, supportive, and reassuring. "
        "End with a clear next step and an offer for further help."
    ),
    "Business Executive": (
        "You are a strategic customer success advisor. "
        "Provide a concise, business-focused response. "
        "Emphasize ROI, SLAs, uptime guarantees, cost implications, and "
        "competitive advantages. Use bullet points sparingly and keep the "
        "language professional and results-oriented. "
        "Limit your response to the most impactful information only."
    ),
}

# ──────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────
_GENERATION_PROMPT: str = """
{persona_instruction}

Use ONLY the context provided below to answer the customer's question.
If the context does not contain enough information, say so honestly — do NOT
fabricate details.

--- CONTEXT START ---
{context}
--- CONTEXT END ---

Customer Question:
\"\"\"{query}\"\"\"

Provide your response now.
"""


def generate_response(
    query: str,
    persona: str,
    chunks: list[dict[str, Any]],
) -> str:
    """Generate a persona-adaptive response using retrieved context.

    Args:
        query: The original customer query.
        persona: One of the three supported persona labels.
        chunks: Retrieved context chunks (each has ``text``, ``source``, ``score``).

    Returns:
        The generated response string.

    Raises:
        RuntimeError: If the Gemini API call fails.
    """
    # TODO: Add streaming support for real-time token output
    # TODO: Add response length control per persona
    # TODO: Add citation formatting (link back to source documents)
    # TODO: Add conversation history for multi-turn context

    persona_instruction = _PERSONA_INSTRUCTIONS.get(
        persona,
        _PERSONA_INSTRUCTIONS["Frustrated User"],
    )

    # Build context block from retrieved chunks
    if chunks:
        context_parts: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "unknown")
            score = chunk.get("score", 0.0)
            text = chunk.get("text", "")
            context_parts.append(
                f"[Chunk {i} | source: {source} | relevance: {score:.4f}]\n{text}"
            )
        context_block = "\n\n".join(context_parts)
    else:
        context_block = "(No relevant context was found in the knowledge base.)"

    prompt = _GENERATION_PROMPT.format(
        persona_instruction=persona_instruction,
        context=context_block,
        query=query.strip(),
    )

    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
        )
        answer: str = response.text.strip()
        logger.info(
            "Generated %d-char response for persona '%s'.",
            len(answer),
            persona,
        )
        return answer
    except Exception as exc:
        logger.error("Response generation failed: %s", exc)
        raise RuntimeError(f"Response generation API error: {exc}") from exc
