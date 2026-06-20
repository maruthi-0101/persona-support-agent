"""
Escalation Logic module.

Determines whether a query should be escalated to a human agent based on:

1. **Low retrieval confidence** — best score < RELEVANCE_THRESHOLD (0.45)
2. **Sensitive topic detection** — billing, refund, legal, account modification

Returns a structured handoff JSON when escalation is triggered:
    {
        "persona": str,
        "detected_issue": str,
        "retrieved_sources": list[str],
        "confidence_score": float,
        "recommended_action": str
    }
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import RELEVANCE_THRESHOLD, ESCALATION_KEYWORDS

logger = logging.getLogger(__name__)


def _detect_sensitive_issues(
    query: str,
    chunks: list[dict[str, Any]],
) -> list[str]:
    """Scan query and retrieved chunks for escalation-trigger keywords.

    Args:
        query: The original user query.
        chunks: Retrieved chunk dicts (each must have a ``text`` key).

    Returns:
        A deduplicated, sorted list of matched issue keywords.
    """
    # TODO: Use NLP-based intent detection instead of keyword matching
    # TODO: Add configurable keyword sets per deployment

    combined_text = query.lower()
    for chunk in chunks:
        combined_text += " " + chunk.get("text", "").lower()

    detected: set[str] = set()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in combined_text:
            detected.add(keyword)

    return sorted(detected)


def _best_retrieval_score(chunks: list[dict[str, Any]]) -> float:
    """Return the highest similarity score among retrieved chunks.

    Returns 0.0 if the chunk list is empty.
    """
    if not chunks:
        return 0.0
    return max(c.get("score", 0.0) for c in chunks)


def check_escalation(
    query: str,
    persona: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Evaluate whether the interaction requires human escalation.

    Args:
        query: The raw user query.
        persona: The classified persona label.
        chunks: Retrieved chunk dicts from the RAG pipeline.

    Returns:
        A handoff dict if escalation is warranted, otherwise ``None``.
    """
    # TODO: Add escalation severity levels (low / medium / high / critical)
    # TODO: Log escalation events to an analytics database
    # TODO: Add webhook notification support (Slack, PagerDuty)

    best_score = _best_retrieval_score(chunks)
    low_confidence = best_score < RELEVANCE_THRESHOLD
    detected_issues = _detect_sensitive_issues(query, chunks)

    should_escalate = low_confidence or bool(detected_issues)

    if not should_escalate:
        logger.debug("No escalation needed (score=%.4f).", best_score)
        return None

    # Build human-readable issue summary
    reasons: list[str] = []
    if low_confidence:
        reasons.append(
            f"low retrieval confidence ({best_score:.4f} < {RELEVANCE_THRESHOLD})"
        )
    if detected_issues:
        reasons.append(
            f"sensitive topics detected: {', '.join(detected_issues)}"
        )

    detected_issue_str = "; ".join(reasons)

    # Collect unique source filenames
    sources: list[str] = sorted(
        {c.get("source", "unknown") for c in chunks}
    )

    # Recommend action
    if detected_issues:
        recommended_action = (
            "Route to specialized human agent for "
            + ", ".join(detected_issues)
            + " handling."
        )
    else:
        recommended_action = (
            "Escalate to Tier-2 support — insufficient knowledge-base "
            "coverage for this query."
        )

    handoff: dict[str, Any] = {
        "persona": persona,
        "detected_issue": detected_issue_str,
        "retrieved_sources": sources,
        "confidence_score": round(best_score, 4),
        "recommended_action": recommended_action,
    }

    logger.info("Escalation triggered: %s", handoff)
    return handoff
