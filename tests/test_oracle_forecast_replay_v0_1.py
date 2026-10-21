"""Adversarial tests for the evaluation-only Oracle forecast replay model."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

import oracles.engine.forecast_replay_v0_1 as oracle

from oracles.engine.forecast_replay_v0_1 import (
    ForecastContractError,
    adapt_ci_predict_ledger,
    aggregate_forecasts,
    annul_episode,
    build_manifest,
    challenge_episode,
    correct_episode,
    resolve_episode,
    score_cohort,
    score_episode,
    start_episode,
    validate_episode,
    verify_manifest_seal,
)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledgers" / "CI_PREDICT_LEDGER.jsonl"
SCHEMA = ROOT / "oracles" / "schemas" / "oracle_forecast_manifest_v0_1.schema.json"


def _ledger_rows() -> list[dict]:
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line]


def _episode(
    forecast_id: str = "FC-TEST-001",
    probability: float = 0.7,
    *,
    mode: str = "EMPIRICAL",
    question_key: str = "test_binary_v1",
    provenance_kind: str = "PROSPECTIVE",
) -> dict:
    manifest = build_manifest(
        forecast_id=forecast_id,
        question_key=question_key,
        question="Will the bounded test event occur?",
        subject_ref="test:event:1",
        created_at="2026-10-20T10:00:00Z",
        closes_at="2026-10-21T10:00:00Z",
        evidence_cutoff={"kind": "TIMESTAMP", "sequence": 0, "ref": "2026-10-20T10:00:00Z"},
        resolution_rule="YES iff the witness fixture records event=true before close.",
        resolution_sources=["TEST_WITNESS"],
        owner="test-suite",
        mode=mode,
        annul_rules=["witness fixture is unavailable"],
        provenance_kind=provenance_kind,
    )
    return start_episode(
        manifest,
        predictor_id="oracle-assembly",
        probability=probability,
        recorded_at="2026-10-20T10:00:00Z",
        evidence_refs=["fixture:before-outcome"],
    )


def _resolved_episode(
    forecast_id: str = "FC-TEST-001",
    probability: float = 0.7,
    outcome: int = 1,
    **kwargs,
) -> dict:
    return resolve_episode(
        _episode(forecast_id, probability, **kwargs),
        outcome=outcome,
        resolver_id="independent-witness",
        source_refs=["fixture:outcome"],
        resolved_at="2026-10-21T10:00:00Z",
        verification_status="VERIFIED",
    )


def test_manifest_matches_schema_and_seal() -> None:
    manifest = _episode()["manifest"]
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
    verify_manifest_seal(manifest)


def test_manifest_tampering_breaks_seal() -> None:
    episode = _episode()
    episode["manifest"]["question"] = "A different question after the outcome"
    with pytest.raises(ForecastContractError, match="seal"):
        validate_episode(episode)


def test_forecast_tampering_breaks_seal() -> None:
    episode = _episode()
    episode["forecasts"][0]["probability"] = 0.99
    with pytest.raises(ForecastContractError, match="seal"):
        validate_episode(episode)


def test_self_resolution_is_refused() -> None:
    with pytest.raises(ForecastContractError, match="cannot resolve its own"):
        resolve_episode(
            _episode(),
            outcome=1,
            resolver_id="oracle-assembly",
            source_refs=["fixture:outcome"],
            resolved_at="2026-10-21T10:00:00Z",
        )


def test_self_challenge_is_refused() -> None:
    with pytest.raises(ForecastContractError, match="cannot challenge its own"):
        challenge_episode(
            _episode(),
            challenger_id="oracle-assembly",
            reasons=["self-generated objection"],
            evidence_refs=["fixture:self"],
            recorded_at="2026-10-20T11:00:00Z",
        )


def test_challenge_after_close_is_refused() -> None:
    with pytest.raises(ForecastContractError, match="after the close"):
        challenge_episode(
            _episode(),
            challenger_id="jester",
            reasons=["too late to alter the forecast"],
            evidence_refs=["fixture:late"],
            recorded_at="2026-10-22T11:00:00Z",
        )


def test_resolution_before_forecast_is_refused() -> None:
    with pytest.raises(ForecastContractError, match="cannot precede"):
        resolve_episode(
            _episode(),
            outcome=1,
            resolver_id="independent-witness",
            source_refs=["fixture:outcome"],
            resolved_at="2026-10-19T10:00:00Z",
        )


def test_resolution_before_a_later_challenge_is_refused() -> None:
    episode = challenge_episode(
        _episode(),
        challenger_id="jester",
        reasons=["late challenge"],
        evidence_refs=["fixture:challenge"],
        recorded_at="2026-10-20T12:00:00Z",
    )
    with pytest.raises(ForecastContractError, match="challenge activity"):
        resolve_episode(
            episode,
            outcome=1,
            resolver_id="independent-witness",
            source_refs=["fixture:outcome"],
            resolved_at="2026-10-20T11:00:00Z",
            verification_status="VERIFIED",
        )


def test_resolution_requires_provenance() -> None:
    with pytest.raises(ForecastContractError, match="source_refs"):
        resolve_episode(
            _episode(),
            outcome=1,
            resolver_id="independent-witness",
            source_refs=[],
            resolved_at="2026-10-21T10:00:00Z",
        )


def test_outcome_receipt_tampering_breaks_its_seal() -> None:
    episode = _resolved_episode()
    episode["resolution"]["outcome"] = 0
    with pytest.raises(ForecastContractError, match="resolution seal"):
        validate_episode(episode)


def test_challenge_tampering_breaks_its_seal() -> None:
    episode = challenge_episode(
        _episode(),
        challenger_id="jester",
        reasons=["base rate omitted"],
        evidence_refs=["fixture:base-rate"],
        recorded_at="2026-10-20T11:00:00Z",
    )
    episode["challenges"][0]["reasons"] = ["rewritten after correction"]
    with pytest.raises(ForecastContractError, match="challenge seal"):
        validate_episode(episode)


def test_f1_f2_f3_preserves_versions_and_scores_corrected_forecast() -> None:
    episode = _episode(probability=0.8)
    f1_seal = episode["forecasts"][0]["seal_sha256"]
    episode = challenge_episode(
        episode,
        challenger_id="jester",
        reasons=["base rate omitted"],
        evidence_refs=["fixture:base-rate"],
        recorded_at="2026-10-20T11:00:00Z",
    )
    episode = correct_episode(
        episode,
        predictor_id="oracle-assembly",
        probability=0.6,
        recorded_at="2026-10-20T12:00:00Z",
        evidence_refs=["fixture:before-outcome", "fixture:base-rate"],
    )
    assert episode["forecasts"][0]["seal_sha256"] == f1_seal
    assert episode["forecasts"][1]["prior_seal_sha256"] == f1_seal
    episode = resolve_episode(
        episode,
        outcome=1,
        resolver_id="independent-witness",
        source_refs=["fixture:outcome"],
        resolved_at="2026-10-21T10:00:00Z",
    )
    receipt = score_episode(episode)
    assert receipt["selected_stage"] == "F3"
    assert receipt["probability"] == pytest.approx(0.6)
    assert receipt["brier"] == pytest.approx(0.16)
    assert receipt["odds_log_change_f3_minus_f1"] < 0


def test_f3_without_challenge_is_refused() -> None:
    with pytest.raises(ForecastContractError, match="requires an F2"):
        correct_episode(
            _episode(),
            predictor_id="oracle-assembly",
            probability=0.5,
            recorded_at="2026-10-20T12:00:00Z",
            evidence_refs=["fixture:new"],
        )


@pytest.mark.parametrize("mode", ["CONDITIONAL", "SYMBOLIC"])
def test_nonempirical_modes_are_never_scored(mode: str) -> None:
    receipt = score_episode(_resolved_episode(mode=mode))
    assert receipt["status"] == "NOT_SCORED"
    assert receipt["reason"] == "MODE_NOT_EMPIRICAL"


def test_annulment_is_preserved_but_not_scored() -> None:
    episode = annul_episode(
        _episode(),
        resolver_id="independent-witness",
        reason="the only named witness source was unavailable",
        source_refs=["fixture:source-unavailable"],
        resolved_at="2026-10-21T10:00:00Z",
    )
    receipt = score_episode(episode)
    assert receipt["status"] == "NOT_SCORED"
    assert receipt["reason"] == "ANNULLED"
    assert episode["resolution"]["reason"]


def test_aggregation_caps_correlated_duplicate_influence() -> None:
    high = _episode("FC-HIGH", 0.8)["forecasts"][0]
    low = oracle._seal({**high, "predictor_id": "independent-model-b", "probability": 0.2})
    two_voice = aggregate_forecasts([
        {"forecast": high, "independence_group": "model-family-a"},
        {"forecast": low, "independence_group": "model-family-b"},
    ])
    assert two_voice["probability"] == pytest.approx(0.5)
    with pytest.raises(ForecastContractError, match="duplicate"):
        aggregate_forecasts([
            {"forecast": high, "independence_group": "model-family-a"},
            {"forecast": copy.deepcopy(high), "independence_group": "model-family-a"},
            {"forecast": low, "independence_group": "model-family-b"},
        ])
    with pytest.raises(ForecastContractError, match="different manifests"):
        aggregate_forecasts([
            {"forecast": high, "independence_group": "model-family-a"},
            {"forecast": _episode("FC-OTHER", 0.2)["forecasts"][0], "independence_group": "model-family-b"},
        ])


def test_cohort_metrics_are_descriptive_without_sampling_frame() -> None:
    episodes = [
        _resolved_episode("FC-A", 0.8, 1),
        _resolved_episode("FC-B", 0.7, 0),
    ]
    report = score_cohort(episodes, minimum_claim_n=2)
    assert report["scored_count"] == 2
    assert report["mean_brier"] == pytest.approx((0.04 + 0.49) / 2)
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "INCOMPLETE_OR_UNDECLARED_SAMPLING_FRAME" in report["claim_blockers"]


def test_complete_homogeneous_prospective_cohort_can_be_claim_ready() -> None:
    episodes = [
        _resolved_episode("FC-A", 0.8, 1),
        _resolved_episode("FC-B", 0.7, 0),
    ]
    report = score_cohort(
        episodes,
        eligible_forecast_ids={"FC-A", "FC-B"},
        sampling_frame_ref="fixture:sampling-frame:sha256:abc",
        sampling_frame_sealed_before_outcomes=True,
        minimum_claim_n=2,
    )
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "INDEPENDENT_COHORT_ATTESTATION_UNAVAILABLE" in report["claim_blockers"]


def test_asserted_outcome_receipt_blocks_a_calibration_claim() -> None:
    episode = resolve_episode(
        _episode("FC-ASSERTED", 0.8),
        outcome=1,
        resolver_id="independent-witness",
        source_refs=["fixture:asserted-only"],
        resolved_at="2026-10-21T10:00:00Z",
    )
    report = score_cohort(
        [episode],
        eligible_forecast_ids={"FC-ASSERTED"},
        sampling_frame_ref="fixture:sampling-frame:sha256:asserted",
        sampling_frame_sealed_before_outcomes=True,
        minimum_claim_n=1,
    )
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "OUTCOME_RECEIPTS_NOT_INDEPENDENTLY_VERIFIED" in report["claim_blockers"]


def test_mixed_question_contracts_block_a_cohort_claim() -> None:
    episodes = [
        _resolved_episode("FC-A", 0.8, 1),
        _resolved_episode("FC-B", 0.7, 0, question_key="different_question_v1"),
    ]
    report = score_cohort(
        episodes,
        eligible_forecast_ids={"FC-A", "FC-B"},
        sampling_frame_ref="fixture:sampling-frame:sha256:mixed",
        sampling_frame_sealed_before_outcomes=True,
        minimum_claim_n=2,
    )
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "MIXED_QUESTION_CONTRACTS" in report["claim_blockers"]


def test_synthetic_records_cannot_support_an_accuracy_claim() -> None:
    episode = _resolved_episode("FC-SYN", 0.8, 1, provenance_kind="SYNTHETIC")
    report = score_cohort(
        [episode],
        eligible_forecast_ids={"FC-SYN"},
        sampling_frame_ref="fixture:sampling-frame:sha256:synthetic",
        sampling_frame_sealed_before_outcomes=True,
        minimum_claim_n=1,
    )
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "SYNTHETIC_RECORDS_PRESENT" in report["claim_blockers"]


def test_real_ci_ledger_replays_with_hits_and_misses() -> None:
    episodes = adapt_ci_predict_ledger(_ledger_rows())
    assert episodes
    receipts = [score_episode(episode) for episode in episodes]
    scored = [item for item in receipts if item["status"] == "SCORED"]
    assert scored
    assert {item["outcome"] for item in scored} == {0, 1}
    assert all(item["provenance_kind"] == "PROSPECTIVE_SOURCE_REPLAY" for item in scored)


def test_first_real_ci_replay_has_known_proper_scores() -> None:
    episodes = [
        episode
        for episode in adapt_ci_predict_ledger(_ledger_rows())
        if "8efd40edb60f" in episode["manifest"]["subject_ref"]
    ]
    receipts = [score_episode(episode) for episode in episodes]
    assert [item["outcome"] for item in receipts] == [1, 1, 0, 1]
    assert [item["brier"] for item in receipts] == pytest.approx([0.0225, 0.01, 0.81, 0.01])
    report = score_cohort(episodes, minimum_claim_n=4)
    assert report["mean_brier"] == pytest.approx(0.213125)
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "OUTCOME_RECEIPTS_NOT_INDEPENDENTLY_VERIFIED" in report["claim_blockers"]


def test_real_ci_resolutions_follow_pins_and_bind_sources() -> None:
    for episode in adapt_ci_predict_ledger(_ledger_rows()):
        resolution = episode["resolution"]
        if resolution is None:
            continue
        pin_sequence = episode["forecasts"][0]["source_binding"]["sequence"]
        resolution_sequence = resolution["source_binding"]["sequence"]
        assert resolution_sequence > pin_sequence
        assert resolution["resolver_id"] != episode["forecasts"][0]["predictor_id"]
        assert resolution["source_refs"][0].startswith("https://github.com/")


def test_real_ci_ledger_tampering_is_refused_before_scoring() -> None:
    rows = _ledger_rows()
    rows[1]["p"] = 0.01
    with pytest.raises(ForecastContractError, match="content hash"):
        adapt_ci_predict_ledger(rows)


def test_resealed_manifest_from_another_episode_is_rejected() -> None:
    episode = _resolved_episode()
    other = _episode("FC-OTHER")["manifest"]
    episode["manifest"] = other  # Both manifests have individually valid seals.
    with pytest.raises(ForecastContractError, match="different manifest"):
        validate_episode(episode)


def test_resolution_cannot_be_transplanted_from_another_episode() -> None:
    one = _resolved_episode("FC-ONE")
    other = _resolved_episode("FC-TWO")
    one["resolution"] = copy.deepcopy(other["resolution"])
    with pytest.raises(ForecastContractError, match="different manifest"):
        validate_episode(one)


def test_future_evidence_window_is_rejected_even_with_valid_seal() -> None:
    episode = _episode()
    manifest = episode["manifest"]
    manifest["evidence_cutoff"]["ref"] = "2026-10-22T10:00:00Z"
    episode["manifest"] = oracle._seal(manifest)
    episode["forecasts"][0]["manifest_seal_sha256"] = episode["manifest"]["seal_sha256"]
    episode["forecasts"][0] = oracle._seal(episode["forecasts"][0])
    with pytest.raises(ForecastContractError, match="future evidence cutoff"):
        validate_episode(episode)


def test_imported_f3_before_its_challenge_rejected() -> None:
    episode = challenge_episode(
        _episode(), challenger_id="jester", reasons=["test"],
        evidence_refs=["fixture:challenger"], recorded_at="2026-10-20T11:00:00Z",
    )
    episode = correct_episode(
        episode, predictor_id="oracle-assembly", probability=0.5,
        recorded_at="2026-10-20T12:00:00Z", evidence_refs=["fixture:corrected"],
    )
    episode["forecasts"][1]["recorded_at"] = "2026-10-20T10:30:00Z"
    episode["forecasts"][1] = oracle._seal(episode["forecasts"][1])
    with pytest.raises(ForecastContractError, match="F3 cannot precede"):
        validate_episode(episode)


def test_caller_only_frame_and_verified_flag_never_grant_claim_readiness() -> None:
    episodes = [_resolved_episode("FC-ONE"), _resolved_episode("FC-TWO")]
    report = score_cohort(
        episodes, eligible_forecast_ids={"FC-ONE", "FC-TWO"},
        sampling_frame_ref="caller:says:precommitted",
        sampling_frame_sealed_before_outcomes=True, minimum_claim_n=2,
    )
    assert report["claim_status"] == "DESCRIPTIVE_ONLY"
    assert "INDEPENDENT_COHORT_ATTESTATION_UNAVAILABLE" in report["claim_blockers"]


def test_calibration_bin_boundary_at_point_six() -> None:
    rows = [{"probability": 0.6, "outcome": 1}]
    bins = oracle._calibration_bins(rows)
    assert bins[0]["lower"] == pytest.approx(0.6)


def test_annulment_must_not_self_attest_as_verified() -> None:
    episode = annul_episode(
        _episode(), resolver_id="independent-witness", reason="unresolved",
        source_refs=["fixture:unverified"], resolved_at="2026-10-21T10:00:00Z",
    )
    assert episode["resolution"]["verification_status"] == "ASSERTED"

