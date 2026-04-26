"""Unit tests for the RAG retrieval layer (rag.py).

All tests are deterministic — no API calls, no network access.
Run from the project root so that knowledge_base/ is resolvable:

    python -m pytest tests/test_rag.py -v
"""
import pytest
from rag import load_knowledge_base, retrieve, _score


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def docs():
    """Load the knowledge base once for the whole test module."""
    return load_knowledge_base()


# ---------------------------------------------------------------------------
# load_knowledge_base
# ---------------------------------------------------------------------------

def test_knowledge_base_loads_nonempty(docs):
    assert len(docs) > 0, "Knowledge base should contain at least one chunk."


def test_knowledge_base_chunks_have_required_keys(docs):
    for chunk in docs:
        assert "source" in chunk, "Each chunk must have a 'source' key."
        assert "text" in chunk, "Each chunk must have a 'text' key."


def test_knowledge_base_sources_are_known_files(docs):
    known = {"dogs.md", "cats.md", "medications.md", "scheduling.md"}
    found = {d["source"] for d in docs}
    assert found == known, f"Unexpected or missing sources: {found ^ known}"


def test_knowledge_base_no_empty_chunks(docs):
    empty = [d for d in docs if not d["text"].strip()]
    assert empty == [], f"Found {len(empty)} empty chunk(s)."


def test_missing_kb_directory_returns_empty():
    result = load_knowledge_base(kb_dir="nonexistent_directory_xyz")
    assert result == [], "Missing KB directory should return an empty list, not raise."


# ---------------------------------------------------------------------------
# _score helper
# ---------------------------------------------------------------------------

def test_score_exact_match():
    assert _score({"walk", "dog"}, "morning walk with the dog") == 2


def test_score_partial_match():
    assert _score({"walk", "cat", "fish"}, "morning walk") == 1


def test_score_no_match():
    assert _score({"zzz", "xyzzy"}, "morning walk with the dog") == 0


# ---------------------------------------------------------------------------
# retrieve — source routing
# ---------------------------------------------------------------------------

def test_retrieve_dog_query_hits_dog_source(docs):
    results = retrieve("morning walk dog exercise daily", docs)
    sources = [r["source"] for r in results]
    assert "dogs.md" in sources or "scheduling.md" in sources, (
        f"Dog walk query should hit dogs.md or scheduling.md; got {sources}"
    )


def test_retrieve_medication_query_hits_medication_source(docs):
    results = retrieve("heartworm pill monthly medication dose missed", docs)
    sources = [r["source"] for r in results]
    assert "medications.md" in sources, (
        f"Medication query should hit medications.md; got {sources}"
    )


def test_retrieve_cat_eye_drops_hits_cats_or_meds(docs):
    results = retrieve("eye drops cat medication routine", docs)
    sources = [r["source"] for r in results]
    assert "cats.md" in sources or "medications.md" in sources, (
        f"Eye-drops query should hit cats.md or medications.md; got {sources}"
    )


def test_retrieve_scheduling_conflict_query(docs):
    results = retrieve("scheduling conflict overlap priority task", docs)
    sources = [r["source"] for r in results]
    assert "scheduling.md" in sources, (
        f"Conflict query should hit scheduling.md; got {sources}"
    )


# ---------------------------------------------------------------------------
# retrieve — edge cases
# ---------------------------------------------------------------------------

def test_retrieve_empty_docs_returns_empty():
    assert retrieve("dog walk", []) == []


def test_retrieve_nonsense_query_returns_empty(docs):
    results = retrieve("xyzzy qqqqq zzzzplork", docs)
    assert results == [], "Nonsense query with zero-score results should return empty."


def test_retrieve_stop_words_only_does_not_crash(docs):
    # All words are in the stop list — should fall back gracefully
    result = retrieve("the a is and for of", docs)
    # May return top_k items (fallback) or empty — just must not raise
    assert isinstance(result, list)


def test_retrieve_respects_top_k(docs):
    results = retrieve("dog cat medication walk", docs, top_k=2)
    assert len(results) <= 2, "retrieve() must not exceed top_k results."


def test_retrieve_returns_unique_chunks(docs):
    results = retrieve("medication pill dose", docs, top_k=4)
    texts = [r["text"] for r in results]
    assert len(texts) == len(set(texts)), "retrieve() should not return duplicate chunks."
