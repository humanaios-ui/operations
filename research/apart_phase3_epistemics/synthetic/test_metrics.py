"""Synthetic regression tests for the Apart Phase 3 rubric plumbing.

This is the "fully deterministic synthetically labeled scoring fixture
offline" step #1200 calls for before any real inference call. It checks
that the metric extractors and the agreement checker behave correctly on
hand-labeled examples that are designed to catch grading leaks: a
trivial-abstraction case that uses abstract words but asserts nothing, a
legitimately hedged case with a repeated hedge phrase, a refusal/missing
case, a null/timeout case, and a skewed-base-rate agreement case where
percent agreement and chance-corrected kappa diverge.

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
        assert result.is_missing_response is True
        assert result.word_count == 0


def test_textual_refusal_is_not_conflated_with_missing_response():
    """A model returning actual refusal TEXT is not `is_missing_response`
    — that field is strictly for the transport-level None/empty case.
    Refusal-vs-error classification is a live-call attempt-ledger concern,
    out of scope for this offline scorer."""
    result = score_response("I can't help with that request.")
    assert result.is_missing_response is False


def test_repeated_hedge_phrase_counts_each_occurrence():
    item = next(i for i in FIXTURES["items"] if i["id"] == "repeated_hedge_phrase")
    result = score_response(item["text"])
    assert result.hedge_count == item["expect"]["hedge_count"]


@pytest.mark.parametrize(
    "case",
    FIXTURES["agreement_cases"],
    ids=[c["id"] for c in FIXTURES["agreement_cases"]],
)
def test_agreement_retains_disagreements_and_computes_kappa(case):
    result = agreement(case["rater_a"], case["rater_b"])
    assert result.percent_agreement == pytest.approx(case["expect_percent_agreement"])
    assert result.kappa == pytest.approx(case["expect_kappa"])
    assert sorted(d.item_id for d in result.disagreements) == sorted(
        case["expect_disagreement_ids"]
    )
    assert result.is_fully_resolved == (len(case["expect_disagreement_ids"]) == 0)


def test_kappa_exposes_what_percent_agreement_hides_on_skewed_labels():
    """The whole reason to report kappa alongside percent agreement: on a
    skewed 0/1 base rate, 80% percent agreement can still be worse than
    chance (negative kappa). A pilot that only reported percent agreement
    would misread this cell as reliable."""
    case = next(
        c for c in FIXTURES["agreement_cases"]
        if c["id"] == "skewed_base_rate_inflates_percent_not_kappa"
    )
    result = agreement(case["rater_a"], case["rater_b"])
    assert result.percent_agreement >= 0.8
    assert result.kappa < 0


def test_agreement_rejects_mismatched_rater_item_sets():
    """A mismatched item set between raters is itself a grading leak —
    it must raise, never silently score the overlap."""
    with pytest.raises(ValueError):
        agreement({"r1": 1, "r2": 0}, {"r1": 1, "r3": 0})


def test_agreement_rejects_out_of_scale_labels():
    """A rating outside {0, 1} must raise, never be silently treated as a
    resolved score."""
    with pytest.raises(ValueError):
        agreement({"r1": 1, "r2": 2}, {"r1": 1, "r2": 0})


def test_agreement_rejects_empty_item_set():
    """Zero rated items is not 'fully resolved' — it's nothing to resolve.
    agreement() must refuse rather than let callers read an empty set as
    agreement."""
    with pytest.raises(ValueError):
        agreement({}, {})
