"""Unit tests for ai_advisor.py.

All tests are deterministic — Anthropic API calls are mocked so no key is needed.
Run from the project root:

    python -m pytest tests/test_advisor.py -v
"""
from unittest.mock import MagicMock, patch

import ai_advisor
from ai_advisor import ask_advisor, build_schedule_summary, _parse_confidence


# ---------------------------------------------------------------------------
# build_schedule_summary
# ---------------------------------------------------------------------------

def test_summary_contains_owner_name():
    out = build_schedule_summary("Jordan", ["Walk for Buddy @ 08:00"], [])
    assert "Jordan" in out


def test_summary_contains_task_lines():
    out = build_schedule_summary("Jordan", ["Walk for Buddy @ 08:00", "Meds @ 09:00"], [])
    assert "Walk for Buddy" in out
    assert "Meds" in out


def test_summary_omits_conflict_section_when_none():
    out = build_schedule_summary("Jordan", ["Walk"], [])
    assert "Conflict" not in out


def test_summary_includes_conflicts_when_present():
    out = build_schedule_summary("Jordan", ["Walk"], ["Walk overlaps Meds"])
    assert "Walk overlaps Meds" in out


# ---------------------------------------------------------------------------
# _parse_confidence
# ---------------------------------------------------------------------------

def test_parse_confidence_high():
    answer, conf = _parse_confidence("Give the pill with food.\nConfidence: HIGH")
    assert conf == "HIGH"
    assert "Confidence" not in answer


def test_parse_confidence_medium():
    _, conf = _parse_confidence("Some advice here.\nConfidence: MEDIUM")
    assert conf == "MEDIUM"


def test_parse_confidence_low():
    _, conf = _parse_confidence("General advice.\nConfidence: LOW")
    assert conf == "LOW"


def test_parse_confidence_missing_returns_unknown():
    answer, conf = _parse_confidence("Some advice with no confidence line.")
    assert conf == "UNKNOWN"
    assert answer == "Some advice with no confidence line."


def test_parse_confidence_strips_line_from_answer():
    answer, _ = _parse_confidence("Paragraph one.\n\nParagraph two.\nConfidence: HIGH")
    assert "Confidence" not in answer
    assert "Paragraph one" in answer


# ---------------------------------------------------------------------------
# ask_advisor — input validation (no API call)
# ---------------------------------------------------------------------------

def test_ask_advisor_empty_question_returns_error():
    result = ask_advisor(question="   ", schedule_context="Owner: Test")
    assert result["error"] is not None
    assert result["answer"] is None


def test_ask_advisor_missing_api_key_returns_error():
    with patch.dict("os.environ", {}, clear=True):
        # Ensure ANTHROPIC_API_KEY is absent
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        result = ask_advisor(question="Should I walk my dog?", schedule_context="")
    assert result["error"] is not None
    assert "ANTHROPIC_API_KEY" in result["error"]


# ---------------------------------------------------------------------------
# ask_advisor — mocked API call
# ---------------------------------------------------------------------------

def _make_mock_response(text: str):
    """Build a minimal mock that looks like an anthropic.Message."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=text)]
    mock_resp.usage.input_tokens = 120
    mock_resp.usage.output_tokens = 40
    return mock_resp


def test_ask_advisor_returns_answer_and_confidence():
    mock_resp = _make_mock_response(
        "Give the heartworm pill with food right after breakfast.\nConfidence: HIGH"
    )
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-fake"}):
        with patch("ai_advisor.anthropic.Anthropic") as MockClass:
            MockClass.return_value.messages.create.return_value = mock_resp
            result = ask_advisor(
                question="When should I give the heartworm pill?",
                schedule_context="Owner: Jordan\nScheduled tasks:\n  - Breakfast @ 07:30",
            )

    assert result["error"] is None
    assert "heartworm" in result["answer"].lower() or result["answer"] != ""
    assert result["confidence"] == "HIGH"
    assert 0.0 <= result["retrieval_coverage"] <= 1.0


def test_ask_advisor_includes_retrieval_coverage():
    mock_resp = _make_mock_response("Some advice.\nConfidence: MEDIUM")
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-fake"}):
        with patch("ai_advisor.anthropic.Anthropic") as MockClass:
            MockClass.return_value.messages.create.return_value = mock_resp
            result = ask_advisor(
                question="dog walk morning exercise",
                schedule_context="Owner: Test",
            )

    assert "retrieval_coverage" in result
    assert isinstance(result["retrieval_coverage"], float)


def test_ask_advisor_handles_generic_exception():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-fake"}):
        with patch("ai_advisor.anthropic.Anthropic") as MockClass:
            MockClass.return_value.messages.create.side_effect = RuntimeError("network down")
            result = ask_advisor(
                question="What should I feed my dog?",
                schedule_context="Owner: Test",
            )

    assert result["error"] is not None
    assert result["answer"] is None
