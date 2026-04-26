"""AI advisor module for PawPal+.

Uses Retrieval-Augmented Generation (RAG) to answer owner questions about their
pet care schedule. Retrieved knowledge-base passages are injected into the prompt
so Claude answers with pet-care-specific context rather than generic responses.

Requires the ANTHROPIC_API_KEY environment variable.
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache

import anthropic

from rag import load_knowledge_base, retrieve

# ---------------------------------------------------------------------------
# Logging — all advisor activity is written to pawpal_ai.log
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename="pawpal_ai.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 600

SYSTEM_PROMPT = (
    "You are PawPal+, a friendly and knowledgeable AI assistant for pet owners. "
    "You help owners understand their pet care schedules and give practical, "
    "specific advice based on the provided schedule context and pet care guidelines. "
    "Keep your advice to 3–6 sentences. If the question falls outside pet care, "
    "politely redirect the owner back to their pets.\n\n"
    "Always end your response with exactly one of these lines (nothing after it):\n"
    "Confidence: HIGH   — the retrieved guidelines directly answer the question.\n"
    "Confidence: MEDIUM — you have partial relevant information.\n"
    "Confidence: LOW    — you are reasoning from general knowledge without direct guidelines."
)

_CONFIDENCE_RE = re.compile(r"Confidence:\s*(HIGH|MEDIUM|LOW)", re.IGNORECASE)


@lru_cache(maxsize=1)
def _get_docs() -> tuple:
    """Load knowledge base once and cache it for the process lifetime."""
    return tuple(load_knowledge_base())


def _build_schedule_context(schedule_text: str) -> str:
    return schedule_text.strip() or "No schedule context provided."


def _parse_confidence(raw_answer: str) -> tuple[str, str]:
    """Split the confidence line from the answer body.

    Returns (clean_answer, confidence) where confidence is HIGH/MEDIUM/LOW/UNKNOWN.
    """
    lines = raw_answer.strip().splitlines()
    for i in range(len(lines) - 1, max(len(lines) - 4, -1), -1):
        match = _CONFIDENCE_RE.search(lines[i])
        if match:
            clean = "\n".join(lines[:i]).strip()
            return clean, match.group(1).upper()
    return raw_answer.strip(), "UNKNOWN"


def ask_advisor(
    question: str,
    schedule_context: str,
    top_k: int = 4,
) -> dict:
    """Query the AI advisor with RAG-enhanced context.

    Args:
        question: The owner's natural-language question.
        schedule_context: A text summary of the current schedule state.
        top_k: Number of knowledge-base chunks to retrieve.

    Returns:
        dict with keys:
            answer (str | None): The AI-generated response (confidence line stripped).
            sources (list[str]): Knowledge base files used.
            confidence (str): HIGH / MEDIUM / LOW / UNKNOWN — model's self-rating.
            retrieval_coverage (float): Fraction of top_k slots that had a keyword match.
            error (str | None): Error message if the call failed.
    """
    empty_result = {"answer": None, "sources": [], "confidence": "UNKNOWN",
                    "retrieval_coverage": 0.0, "error": None}

    if not question.strip():
        return {**empty_result, "error": "Question cannot be empty."}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        msg = "ANTHROPIC_API_KEY is not set. Add it to your environment variables."
        logger.error(msg)
        return {**empty_result, "error": msg}

    # --- RAG retrieval ---
    docs = list(_get_docs())
    retrieved = retrieve(question, docs, top_k=top_k)
    sources = sorted({d["source"] for d in retrieved})
    retrieval_coverage = len(retrieved) / top_k if top_k > 0 else 0.0

    knowledge_block = (
        "\n\n---\n\n".join(f"[{d['source']}]\n{d['text']}" for d in retrieved)
        if retrieved
        else "No relevant guidelines found in the knowledge base."
    )

    # --- Prompt construction ---
    user_message = (
        f"## Current Schedule\n{_build_schedule_context(schedule_context)}\n\n"
        f"## Relevant Pet Care Guidelines\n{knowledge_block}\n\n"
        f"## Owner's Question\n{question}"
    )

    logger.info(
        "Query: %r | Sources: %s | Coverage: %.2f",
        question, sources, retrieval_coverage,
    )

    # --- Claude API call with prompt caching on the system turn ---
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        raw_answer = response.content[0].text
        answer, confidence = _parse_confidence(raw_answer)

        logger.info(
            "Response OK | confidence=%s coverage=%.2f input_tokens=%d "
            "output_tokens=%d cache_hit=%s",
            confidence,
            retrieval_coverage,
            response.usage.input_tokens,
            response.usage.output_tokens,
            getattr(response.usage, "cache_read_input_tokens", "n/a"),
        )
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "retrieval_coverage": retrieval_coverage,
            "error": None,
        }

    except anthropic.AuthenticationError:
        msg = "Invalid API key. Check your ANTHROPIC_API_KEY."
        logger.error(msg)
        return {**empty_result, "error": msg}
    except anthropic.RateLimitError:
        msg = "Rate limit reached. Please wait a moment and try again."
        logger.warning(msg)
        return {**empty_result, "error": msg}
    except anthropic.APIStatusError as exc:
        msg = f"API error {exc.status_code}: {exc.message}"
        logger.error(msg)
        return {**empty_result, "error": msg}
    except Exception as exc:  # noqa: BLE001
        msg = f"Unexpected error: {exc}"
        logger.exception(msg)
        return {**empty_result, "error": msg}


def build_schedule_summary(owner_name: str, schedule_lines: list[str], conflicts: list[str]) -> str:
    """Format a plain-text schedule summary to pass as context to the advisor."""
    parts = [f"Owner: {owner_name}", "Scheduled tasks:"]
    parts.extend(f"  - {line}" for line in schedule_lines)
    if conflicts:
        parts.append("Conflicts detected:")
        parts.extend(f"  ! {c}" for c in conflicts)
    return "\n".join(parts)
