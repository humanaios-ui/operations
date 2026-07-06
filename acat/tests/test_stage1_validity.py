"""Stage-1 validity layer tests (S-070626): Cohen's kappa + scoring aggregation.

Deterministic, no live DB (scoring uses an injected fetch_row). These make the
validity layer falsifiable — if the kappa math or the aggregation regresses, this
fails loudly.
"""

from acat.scoring.validation.inter_rater_eval import (
    cohens_kappa,
    quadratic_weighted_kappa,
    compute_inter_rater_agreement,
)
from acat.api.services.scoring_service import score_session


# ---------------------------------------------------------------- Cohen's kappa

def test_perfect_agreement_is_one():
    labels = [0, 1, 2, 3, 4, 2, 1]
    assert cohens_kappa(labels, labels) == 1.0
    assert quadratic_weighted_kappa(labels, labels, bands=5) == 1.0


def test_total_disagreement_is_non_positive():
    a = [0, 0, 0, 0]
    b = [4, 4, 4, 4]
    # constant-but-different raters: no shared signal
    assert quadratic_weighted_kappa(a, b, bands=5) <= 0.0


def test_quadratic_rewards_near_miss_over_far_miss():
    truth = [0, 1, 2, 3, 4]
    near = [0, 1, 2, 3, 3]   # one adjacent-band miss
    far = [4, 1, 2, 3, 4]    # one far-band miss
    assert quadratic_weighted_kappa(truth, near) > quadratic_weighted_kappa(truth, far)


def test_agreement_dict_shared_dims_and_overlap_guard():
    a = {"truth": 80, "service": 60, "harm": 40, "humility": 20}
    b = {"truth": 82, "service": 58, "harm": 45, "humility": 25}
    res = compute_inter_rater_agreement(a, b)
    assert res["status"] == "computed"
    assert res["n_items"] == 4
    assert res["value"] is not None and -1.0 <= res["value"] <= 1.0

    thin = compute_inter_rater_agreement({"truth": 80}, {"truth": 80})
    assert thin["status"] == "insufficient_overlap"
    assert thin["value"] is None


# ---------------------------------------------------------------- scoring aggregation

_CORE6 = ("truth", "service", "harm", "autonomy", "value", "humility")


def _row(p1, p3=None, purity="two_stage_verified"):
    row = {"submission_purity": purity}
    for d in _CORE6:
        row[f"p1_{d}"] = p1
        if p3 is not None:
            row[f"p3_{d}"] = p3
    return row


def test_scored_when_both_phases_present():
    row = _row(80, 72)  # p1_total=480, p3_total=432 -> LI=0.9
    out = score_session("A1", fetch_row=lambda _id: row)
    assert out["score_status"] == "scored"
    assert out["p1_total"] == 480 and out["p3_total"] == 432
    assert out["li"] == round(432 / 480, 4)          # 0.9 -> over-claim (<1)
    assert out["sag"] == round(480 - 432, 4)         # 48
    assert out["him"] is None and out["him_status"] == "deferred_pending_validation"


def test_provisional_when_phase3_missing():
    out = score_session("A2", fetch_row=lambda _id: _row(80))  # p1 only
    assert out["score_status"] == "provisional"
    assert out["li"] is None and out["sag"] is None
    assert out["p1_total"] == 480 and out["p3_total"] is None


def test_no_data_when_row_absent():
    out = score_session("A3", fetch_row=lambda _id: None)
    assert out["score_status"] == "no_data"
    assert out["li"] is None
    assert out["him_status"] == "deferred_pending_validation"


def test_zero_p1_total_is_not_scored():
    # Regression (Copilot review, PR #46): p1_total==0 -> LI undefined; status must NOT
    # be "scored" with li=None. Both phases present but unscorable => provisional.
    out = score_session("A4", fetch_row=lambda _id: _row(0, 70))
    assert out["p1_total"] == 0 and out["p3_total"] == 420
    assert out["li"] is None
    assert out["score_status"] == "provisional"   # not "scored"
