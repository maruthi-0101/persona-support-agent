"""
Persona Classifier module.

Uses Google Gemini to classify incoming customer queries into one of
three supported personas:

    • Technical Expert   — uses jargon, expects deep technical answers
    • Frustrated User    — expresses anger/urgency, needs empathy
    • Business Executive — focuses on ROI, SLAs, cost efficiency

Returns structured JSON:
    {
        "persona": str,
        "confidence": float,
        "reasoning": str
    }
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.config import client, GENERATION_MODEL, SUPPORTED_PERSONAS

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Classification prompt template
# ──────────────────────────────────────────────
_CLASSIFICATION_PROMPT: str = """You are an expert customer-support persona classifier.

Analyze the following customer query and classify it into EXACTLY ONE of these personas:
{personas}

Consider these signals:
- **Technical Expert**: Uses technical jargon, asks about APIs / configurations / error codes, expects in-depth answers.
- **Frustrated User**: Expresses anger, disappointment, or urgency. Uses exclamation marks, words like "broken", "terrible", "unacceptable", or describes repeated failures.
- **Business Executive**: Focuses on ROI, cost, SLAs, compliance, scalability, or business impact. Uses concise, results-oriented language.

Customer Query:
\"\"\"
{query}
\"\"\"

Respond with ONLY a valid JSON object (no markdown fences) in this exact schema:
{{
    "persona": "<one of the personas listed above>",
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<one-sentence justification>"
}}
"""


def classify_persona(query: str) -> dict[str, Any]:
    """Classify a user query into a supported persona.

    Args:
        query: The raw customer query string.

    Returns:
        A dict with keys ``persona``, ``confidence``, and ``reasoning``.

    Raises:
        ValueError: If the model returns unparseable or invalid JSON.
        RuntimeError: If the Gemini API call fails.
    """
    # TODO: Add retry logic with exponential backoff for transient API errors
    # TODO: Cache repeated identical queries to reduce API calls
    # TODO: Add support for custom persona definitions via config

    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    prompt = _CLASSIFICATION_PROMPT.format(
        personas="\n".join(f"  - {p}" for p in SUPPORTED_PERSONAS),
        query=query.strip(),
    )

    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
        )
        raw_text: str = response.text.strip()
        logger.debug("Raw classifier response: %s", raw_text)
    except Exception as exc:
        logger.error("Gemini API call failed during classification: %s", exc)
        raise RuntimeError(f"Persona classification API error: {exc}") from exc

    # ── Parse and validate JSON ──────────────────────────────────
    try:
        cleaned = raw_text
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        result: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse classifier JSON: %s", raw_text)
        raise ValueError(
            f"Classifier returned invalid JSON: {raw_text}"
        ) from exc

    # Validate required keys
    for key in ("persona", "confidence", "reasoning"):
        if key not in result:
            raise ValueError(f"Classifier response missing key: '{key}'")

    # Validate persona value — fallback to Frustrated User if unknown
    if result["persona"] not in SUPPORTED_PERSONAS:
        logger.warning(
            "Unknown persona '%s' — defaulting to 'Frustrated User'.",
            result["persona"],
        )
        result["persona"] = "Frustrated User"
        result["confidence"] = max(0.0, result["confidence"] - 0.2)

    # Clamp confidence to [0.0, 1.0]
    result["confidence"] = round(
        min(1.0, max(0.0, float(result["confidence"]))), 2
    )

    return result
