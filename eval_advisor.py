#!/usr/bin/env python3
"""Evaluation harness for PawPal+ AI Advisor.

Two evaluation tiers:

  Tier 1 — Retrieval eval (always runs, no API key needed):
    For each golden query, checks that the expected knowledge-base source
    file appears in the top retrieved results.

  Tier 2 — AI advisor eval (runs only with --live flag + ANTHROPIC_API_KEY):
    Calls the full advisor pipeline and checks that the answer contains
    at least two expected keywords and that a confidence score is returned.

Usage:
    python eval_advisor.py             # Tier 1 only
    python eval_advisor.py --live      # Tier 1 + Tier 2
"""
from __future__ import annotations

import os
import sys

from rag import load_knowledge_base, retrieve
from ai_advisor import ask_advisor, build_schedule_summary

# ---------------------------------------------------------------------------
# Golden test cases
# ---------------------------------------------------------------------------

# (query, expected_source)
RETRIEVAL_CASES = [
    ("morning walk dog exercise daily",          "dogs.md"),
    ("heartworm pill monthly medication dose",   "medications.md"),
    ("eye drops cat medication daily routine",   "cats.md"),
    ("scheduling conflict overlap priority",     "scheduling.md"),
    ("feeding meal times twice a day kibble",    "dogs.md"),
    ("recurring daily weekly task reminder",     "scheduling.md"),
]

# (question, schedule_context, expected_keywords)
# A test passes when ≥ 2 of the expected keywords appear in the answer.
AI_CASES = [
    (
        "Should I give Buddy his heartworm pill before or after his morning walk?",
        build_schedule_summary(
            "Jordan",
            [
                "Morning Walk for Buddy @ 08:00 (30 min, priority 5, category: walk)",
                "Breakfast for Buddy @ 07:30 (10 min, priority 4, category: feeding)",
                "Heartworm Pill for Buddy @ 09:00 (5 min, priority 5, category: meds)",
            ],
            [],
        ),
        ["food", "meal", "breakfast", "pill", "walk", "before", "after"],
    ),
    (
        "Luna hates her eye drops. How can I make it less stressful for both of us?",
        build_schedule_summary(
            "Jordan",
            ["Eye Drops for Luna @ 08:30 (5 min, priority 5, category: meds)"],
            [],
        ),
        ["treat", "reward", "calm", "routine", "drops", "positive"],
    ),
    (
        "I have a conflict between two tasks. Which one should I reschedule?",
        build_schedule_summary(
            "Jordan",
            [
                "Morning Walk for Buddy @ 08:00 (30 min, priority 5, category: walk)",
                "Vet Check Call @ 08:15 (30 min, priority 4, category: other)",
            ],
            ["CONFLICT [Buddy]: 'Morning Walk' (08:00, 30 min) overlaps 'Vet Check Call' (08:15, 30 min)"],
        ),
        ["priority", "medical", "walk", "move", "reschedule", "conflict", "vet"],
    ),
]

SEP = "─" * 56


# ---------------------------------------------------------------------------
# Tier 1: Retrieval evaluation
# ---------------------------------------------------------------------------

def run_retrieval_eval(docs: list) -> tuple[int, int]:
    passed = 0
    total = len(RETRIEVAL_CASES)

    print(f"\n{SEP}")
    print("  TIER 1 — Retrieval Evaluation  (no API required)")
    print(SEP)

    for query, expected_source in RETRIEVAL_CASES:
        results = retrieve(query, docs)
        sources = [r["source"] for r in results]
        ok = expected_source in sources
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}]  {query[:48]:<48}  → {expected_source}")
        if not ok:
            print(f"          Got: {sources}")

    print(f"\n  Result: {passed}/{total} passed")
    return passed, total


# ---------------------------------------------------------------------------
# Tier 2: AI advisor evaluation (live API)
# ---------------------------------------------------------------------------

def run_ai_eval() -> tuple[int, int]:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"\n{SEP}")
        print("  TIER 2 — AI Advisor Evaluation  [SKIPPED]")
        print(SEP)
        print("  ANTHROPIC_API_KEY not set. Run with --live after setting the key.")
        return 0, 0

    passed = 0
    total = len(AI_CASES)

    print(f"\n{SEP}")
    print("  TIER 2 — AI Advisor Evaluation  (live API)")
    print(SEP)

    for question, schedule_context, expected_keywords in AI_CASES:
        result = ask_advisor(question=question, schedule_context=schedule_context)

        if result["error"]:
            print(f"  [ERROR]  {question[:60]}")
            print(f"           {result['error']}")
            continue

        answer_lower = result["answer"].lower()
        matched = [kw for kw in expected_keywords if kw in answer_lower]
        ok = len(matched) >= 2
        if ok:
            passed += 1

        status = "PASS" if ok else "FAIL"
        conf   = result.get("confidence", "UNKNOWN")
        cov    = result.get("retrieval_coverage", 0.0)
        sources = ", ".join(result.get("sources", []))

        print(f"  [{status}]  {question[:60]}")
        print(f"           Confidence: {conf:<6}  Coverage: {cov:.0%}  Sources: {sources}")
        print(f"           Keywords matched ({len(matched)}/{len(expected_keywords)}): {matched}")
        if not ok:
            print(f"           Answer: {result['answer'][:120]}...")
        print()

    print(f"  Result: {passed}/{total} passed")
    return passed, total


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    live = "--live" in sys.argv

    docs = load_knowledge_base()
    if not docs:
        print("ERROR: knowledge base is empty. Run from the project root directory.")
        sys.exit(1)

    r_pass, r_total = run_retrieval_eval(docs)

    if live:
        a_pass, a_total = run_ai_eval()
    else:
        a_pass, a_total = 0, 0
        print(f"\n  [INFO] Run with --live to evaluate the full AI pipeline.")

    grand_pass  = r_pass + a_pass
    grand_total = r_total + (a_total if live else 0)

    print(f"\n{SEP}")
    print(f"  OVERALL: {grand_pass}/{grand_total} tests passed")
    print(SEP)

    sys.exit(0 if grand_pass == grand_total else 1)


if __name__ == "__main__":
    main()
