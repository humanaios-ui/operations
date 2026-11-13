"""
test_governance_blocker_conflation_check.py
Builder v1.7 compliant - governance_blocker_conflation_check tests.

Proves the tool flags IC-033's documented bundled-gate shape, does not flag
a line already decomposed beneath it, and that candidate completeness
checking actually distinguishes a candidate that drops a source requirement
from one that covers it.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from governance_blocker_conflation_check import (
    analyze,
    check_completeness,
    detect_bundled_gates,
    extract_requirement_lines,
    normalize_tokens,
    run_smoke_test,
)

TOOL_NAME = "test_governance_blocker_conflation_check"
TOOL_VERSION = "1.0.0"


def test_smoke_test_passes():
    assert run_smoke_test() is True


def test_flags_ic033_shaped_bundled_gate():
    text = "- [ ] Z2: admit bounded protocol, budget, reviewer/ethics controls; no unapproved live model calls.\n"
    found = detect_bundled_gates(text, "src")
    assert len(found) == 1
    assert found[0].verb == "admit"


def test_does_not_flag_gate_already_decomposed_beneath_it():
    text = (
        "Z2: admit bounded protocol, budget, reviewer/ethics controls.\n"
        "1. Budget decision\n"
        "2. Reviewer decision\n"
        "3. Ethics decision\n"
    )
    assert detect_bundled_gates(text, "src") == []


def test_does_not_flag_single_ask_line():
    text = "- [ ] Confirm sprint signup and submission UI state with provider.\n"
    # "and" appears once, "admit"/"ratify"/etc. verbs are absent -> no flag
    assert detect_bundled_gates(text, "src") == []


def test_extract_requirement_lines_covers_checklist_and_decision_needed():
    text = (
        "- [ ] First checklist item\n"
        "**Decision needed:** name the raters\n"
    )
    reqs = extract_requirement_lines(text, "src")
    kinds = {r.kind for r in reqs}
    assert kinds == {"checklist", "decision_needed"}


def test_completeness_reports_a_dropped_requirement_as_unrepresented():
    sources = {"issue": "- [ ] Z2: admit bounded protocol, budget, reviewer/ethics controls.\n"}
    candidate_missing_ethics = "Decision needed: name the provider and a dollar ceiling for budget.\n"
    result = check_completeness(sources, candidate_missing_ethics, threshold=0.5)
    assert result["unrepresented"], result


def test_completeness_marks_a_covered_requirement_as_represented():
    sources = {"issue": "- [ ] Name the budget provider and dollar ceiling.\n"}
    candidate = "Decision needed: name the budget provider and set a dollar ceiling for spend.\n"
    result = check_completeness(sources, candidate, threshold=0.5)
    assert result["represented"], result
    assert not result["unrepresented"], result


def test_normalize_tokens_drops_stopwords_and_punctuation():
    tokens = normalize_tokens("Decision needed: admit the budget, reviewer, and ethics controls.")
    assert "the" not in tokens
    assert "and" not in tokens
    assert "budget" in tokens
    assert "ethics" in tokens


def test_analyze_end_to_end_on_a_snapshot_without_candidate():
    snapshot = {
        "sources": {
            "1114": "- [ ] Z2: admit bounded protocol, budget, reviewer/ethics controls; no unapproved live model calls.\n"
        },
        "candidate": None,
    }
    report = analyze(snapshot)
    assert report["bundled_gate_candidates"]
    assert "completeness" not in report
