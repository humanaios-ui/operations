"""Synthetic regression tests for the Apart Phase 3 rubric plumbing.

This is the "fully deterministic synthetically labeled scoring fixture
offline" step #1200 calls for before any real inference call. It checks
that the metric extractors and the agreement checker behave correctly on
hand-labeled examples that are designed to catch grading leaks: a
trivial-abstraction case that uses abstract words but asserts nothing, a
legitimately hedged case, a refusal/missing case, and a null/timeout case.

Run: python3 -m pytest research/apart_phase3_epistemics/synthetic/test_metrics.py -v
"""
import json
from pathlib import Path

import pytest

from metrics import agreement, score_response

FIXTURES_PATH = Path(__file__).parent / "fixtures.json"


def _load_fixtures():
    with open(FIXTURES_PATH) as f:
        return json.load(f)


FIXTURES = _load_fixtures()


@pytest.mark.parametrize(
    "item",
    FIXTURES["items"],
    ids=[item["id"] for item in FIXTURES["items"]],
)
def test_response_metrics_match_expected(item):
    result = score_response(item["text"])
    for field, expected in item["expect"].items():
        actual = getattr(result, field)
        assert actual == expected, (
            f"{item['id']}: expected {field}={expected!r}, got {actual!r}"
        )


def test_trivial_abstraction_is_not_flagged_as_unsupported_claim():
    """Regression guard: a scorer that treats abstract-noun presence as the
    primary-outcome signal would wrongly flag this case. The primary
    outcome must stay a human judgment of a *specific unsupported
    assertion*, not a bag-of-words hit."""
    trivial = next(i for i in FIXTURES["items"] if i["id"] == "trivial_abstraction")
    result = score_response(trivial["text"])
    assert result.abstract_noun_count > 0
    assert result.unsupported_claim_flag is False


def test_null_and_empty_responses_are_retained_as_missingness():
    for fixture_id in ("null_refusal", "timeout_missing"):
        item = next(i for i in FIXTURES["items"] if i["id"] == fixture_id)
        result = score_response(item["text"])
        assert result.is_refusal_or_missing is True
        assert result.token_count == 0


@pytest.mark.parametrize(
    "case",
    FIXTURES["agreement_cases"],
    ids=[c["id"] for c in FIXTURES["agreement_cases"]],
)
def test_agreement_retains_disagreements(case):
    result = agreement(case["rater_a"], case["rater_b"])
    assert result.percent_agreement == pytest.approx(case["expect_percent_agreement"])
    assert sorted(d.item_id for d in result.disagreements) == sorted(
        case["expect_disagreement_ids"]
    )
    assert result.is_fully_resolved == (len(case["expect_disagreement_ids"]) == 0)


def test_agreement_rejects_mismatched_rater_item_sets():
    """A mismatched item set between raters is itself a grading leak —
    it must raise, never silently score the overlap."""
    with pytest.raises(ValueError):
        agreement({"r1": 1, "r2": 0}, {"r1": 1, "r3": 0})
