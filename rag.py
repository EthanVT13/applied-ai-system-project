"""Retrieval-Augmented Generation (RAG) module for PawPal+.

Loads a knowledge base of pet care documents from the knowledge_base/ directory,
splits them into paragraphs, and retrieves the most relevant chunks for a given query
using TF-IDF-style keyword overlap scoring.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def load_knowledge_base(kb_dir: str = "knowledge_base") -> List[dict]:
    """Load all markdown files from kb_dir and split into paragraph-level chunks."""
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        logger.warning("Knowledge base directory '%s' not found.", kb_dir)
        return []

    docs: List[dict] = []
    for md_file in sorted(kb_path.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Could not read %s: %s", md_file, exc)
            continue

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            # Skip pure heading lines — they contain no retrieval-useful content
            if re.match(r"^#+\s", para) and "\n" not in para:
                continue
            docs.append({"source": md_file.name, "text": para})

    logger.info("Knowledge base loaded: %d chunks from %s", len(docs), kb_path)
    return docs


def _score(query_words: set, doc_text: str) -> int:
    """Count how many unique query words appear in doc_text (case-insensitive)."""
    doc_words = set(re.findall(r"\w+", doc_text.lower()))
    return len(query_words & doc_words)


def retrieve(query: str, docs: List[dict], top_k: int = 4) -> List[dict]:
    """Return up to top_k chunks most relevant to query, skipping zero-score chunks."""
    if not docs:
        return []

    # Remove common stop words so they don't dominate scoring
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "i", "my",
        "me", "we", "our", "you", "your", "what", "how", "when", "why",
        "for", "of", "in", "on", "at", "to", "and", "or", "but",
    }
    query_words = set(re.findall(r"\w+", query.lower())) - stop_words

    if not query_words:
        return docs[:top_k]

    scored = sorted(docs, key=lambda d: -_score(query_words, d["text"]))
    return [d for d in scored[:top_k] if _score(query_words, d["text"]) > 0]
