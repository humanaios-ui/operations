"""HumanAIOS Oracle forecast replay and calibration evaluator v0.1.

This is an evaluation-only layer for empirical forecasts.  It can seal a
question and forecast, preserve a challenge/correction trail, bind an
independent outcome receipt, and calculate proper scores.  It also adapts the
existing ``CI_PREDICT_LEDGER`` into the same shape for historical replay.

It deliberately has no network, execution, admission, ratification, commit,
or merge capability.  Every output is advisory and has authority effect NONE.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "ForecastContractError",
    "adapt_ci_predict_ledger",
    "aggregate_forecasts",
    "annul_episode",
    "brier_score",
    "build_manifest",
    "challenge_episode",
    "correct_episode",
    "resolve_episode",
    "score_cohort",
    "score_episode",
    "start_episode",
    "validate_episode",
    "verify_hash_chain",
    "verify_manifest_seal",
    "verify_snapshot_seal",
]

AUTHORITY = {
    "advisory_only": True,
    "can_authorize": False,
    "authority_effect": "NONE",
}
MODES = {"EMPIRICAL", "CONDITIONAL", "SYMBOLIC"}
STAGES = {"F1", "F3"}
PROVENANCE_KINDS = {
    "PROSPECTIVE",
    "PROSPECTIVE_SOURCE_REPLAY",
    "SYNTHETIC",
}
VERIFICATION_STATUSES = {"VERIFIED", "ASSERTED", "RECORDED_NOT_REVERIFIED"}
ZERO_HASH = "0" * 64
LOG_EPSILON = 1e-15


class ForecastContractError(ValueError):
    """Raised when a forecast would violate the replay contract."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _with_authority(value: Mapping[str, Any]) -> dict[str, Any]:
    return {**copy.deepcopy(dict(value)), **AUTHORITY}


def _validate_authority(value: Mapping[str, Any], where: str) -> None:
    for key, expected in AUTHORITY.items():
        if value.get(key) != expected:
            raise ForecastContractError(
                f"{where} must carry {key}={expected!r}, got {value.get(key)!r}"
            )


def _probability(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ForecastContractError(f"{where} probability must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ForecastContractError(f"{where} probability must be finite and in [0,1]")
    return result


def _timestamp(value: str, where: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ForecastContractError(f"{where} timestamp is required")
    normalized = value.strip()
    if len(normalized) == 10:
        normalized += "T00:00:00+00:00"
    elif normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ForecastContractError(f"{where} has invalid ISO timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        raise ForecastContractError(f"{where} timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _normalized_timestamp(value: str) -> str:
    parsed = _timestamp(value, "source event")
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _required_text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ForecastContractError(f"{where} must be a non-empty string")
    return value.strip()


def _required_text_list(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ForecastContractError(f"{where} must be a non-empty list")
    result = [_required_text(item, where) for item in value]
    if len(set(result)) != len(result):
        raise ForecastContractError(f"{where} must not contain duplicates")
    return result


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(value))
    sealed.pop("seal_sha256", None)
    sealed["seal_sha256"] = _sha256(sealed)
    return sealed


def _verify_seal(value: Mapping[str, Any], where: str) -> None:
    seal = value.get("seal_sha256")
    if not isinstance(seal, str) or len(seal) != 64:
        raise ForecastContractError(f"{where} has no valid SHA-256 seal")
    body = copy.deepcopy(dict(value))
    body.pop("seal_sha256", None)
    if _sha256(body) != seal:
        raise ForecastContractError(f"{where} seal does not match its content")


def build_manifest(
    *,
    forecast_id: str,
    question_key: str,
    question: str,
    subject_ref: str,
    created_at: str,
    closes_at: str | None,
    evidence_cutoff: Mapping[str, Any],
    resolution_rule: str,
    resolution_sources: Sequence[str],
    owner: str,
    mode: str = "EMPIRICAL",
    affected_parties: Sequence[str] = (),
    privacy_class: str = "PUBLIC_REPOSITORY",
    reflexivity: str = "LOW",
    ambiguity_rule: str = "ANNUL_IF_OUTCOME_IS_NOT_UNAMBIGUOUS",
    annul_rules: Sequence[str] = (
        "resolution source unavailable",
        "question became ambiguous before close",
    ),
    provenance_kind: str = "PROSPECTIVE",
    provenance_refs: Sequence[str] = (),
) -> dict[str, Any]:
    """Build and seal the immutable question contract for one binary forecast."""
    mode = _required_text(mode, "mode").upper()
    if mode not in MODES:
        raise ForecastContractError(f"unsupported forecast mode {mode!r}")
    if provenance_kind not in PROVENANCE_KINDS:
        raise ForecastContractError(f"unsupported provenance kind {provenance_kind!r}")
    created = _timestamp(created_at, "created_at")
    if closes_at is not None and _timestamp(closes_at, "closes_at") < created:
        raise ForecastContractError("closes_at cannot precede created_at")

    cutoff = copy.deepcopy(dict(evidence_cutoff))
    if cutoff.get("kind") not in {"LEDGER_EVENT", "TIMESTAMP", "COMMIT"}:
        raise ForecastContractError("evidence_cutoff.kind is unsupported")
    if not isinstance(cutoff.get("sequence"), int) or cutoff["sequence"] < 0:
        raise ForecastContractError("evidence_cutoff.sequence must be a non-negative integer")
    _required_text(cutoff.get("ref"), "evidence_cutoff.ref")

    manifest = _with_authority({
        "schema_version": "0.1",
        "forecast_id": _required_text(forecast_id, "forecast_id"),
        "question_key": _required_text(question_key, "question_key"),
        "question": _required_text(question, "question"),
        "subject_ref": _required_text(subject_ref, "subject_ref"),
        "mode": mode,
        "outcome_space": ["NO", "YES"],
        "created_at": _normalized_timestamp(created_at),
        "closes_at": _normalized_timestamp(closes_at) if closes_at else None,
        "evidence_cutoff": cutoff,
        "resolution_rule": _required_text(resolution_rule, "resolution_rule"),
        "resolution_sources": _required_text_list(
            list(resolution_sources), "resolution_sources"
        ),
        "ambiguity_rule": _required_text(ambiguity_rule, "ambiguity_rule"),
        "annul_rules": _required_text_list(list(annul_rules), "annul_rules"),
        "owner": _required_text(owner, "owner"),
        "affected_parties": [
            _required_text(item, "affected_parties") for item in affected_parties
        ],
        "privacy_class": _required_text(privacy_class, "privacy_class"),
        "reflexivity": _required_text(reflexivity, "reflexivity"),
        "scoring": {
            "metrics": ["BRIER", "LOG_LOSS"],
            "only_empirical": True,
        },
        "provenance": {
            "kind": provenance_kind,
            "source_refs": [
                _required_text(item, "provenance_refs") for item in provenance_refs
            ],
        },
        "state": "SEALED",
    })
    return _seal(manifest)


def verify_manifest_seal(manifest: Mapping[str, Any]) -> None:
    _validate_authority(manifest, "manifest")
    if manifest.get("state") != "SEALED":
        raise ForecastContractError("manifest must remain SEALED")
    if manifest.get("mode") not in MODES:
        raise ForecastContractError("manifest mode is invalid")
    if manifest.get("outcome_space") != ["NO", "YES"]:
        raise ForecastContractError("v0.1 supports the exact binary outcome space NO/YES")
    for field in (
        "forecast_id",
        "question_key",
        "question",
        "subject_ref",
        "resolution_rule",
        "ambiguity_rule",
        "owner",
        "privacy_class",
        "reflexivity",
    ):
        _required_text(manifest.get(field), f"manifest.{field}")
    created = _timestamp(str(manifest.get("created_at") or ""), "manifest.created_at")
    closes_at = manifest.get("closes_at")
    if closes_at is not None and _timestamp(str(closes_at), "manifest.closes_at") < created:
        raise ForecastContractError("manifest closes_at cannot precede created_at")
    cutoff = manifest.get("evidence_cutoff")
    if not isinstance(cutoff, Mapping):
        raise ForecastContractError("manifest evidence_cutoff is required")
    if cutoff.get("kind") not in {"LEDGER_EVENT", "TIMESTAMP", "COMMIT"}:
        raise ForecastContractError("manifest evidence_cutoff.kind is unsupported")
    if not isinstance(cutoff.get("sequence"), int) or cutoff["sequence"] < 0:
        raise ForecastContractError("manifest evidence_cutoff.sequence is invalid")
    _required_text(cutoff.get("ref"), "manifest.evidence_cutoff.ref")
    _required_text_list(
        list(manifest.get("resolution_sources") or []),
        "manifest.resolution_sources",
    )
    _required_text_list(list(manifest.get("annul_rules") or []), "manifest.annul_rules")
    affected = manifest.get("affected_parties")
    if not isinstance(affected, list):
        raise ForecastContractError("manifest affected_parties must be a list")
    for item in affected:
        _required_text(item, "manifest.affected_parties")
    scoring = manifest.get("scoring")
    if scoring != {"metrics": ["BRIER", "LOG_LOSS"], "only_empirical": True}:
        raise ForecastContractError("manifest scoring contract is invalid")
    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ForecastContractError("manifest provenance is required")
    if provenance.get("kind") not in PROVENANCE_KINDS:
        raise ForecastContractError("manifest provenance kind is invalid")
    source_refs = provenance.get("source_refs")
    if not isinstance(source_refs, list):
        raise ForecastContractError("manifest provenance source_refs must be a list")
    for item in source_refs:
        _required_text(item, "manifest.provenance.source_refs")
    _verify_seal(manifest, "manifest")


def _sealed_snapshot(
    *,
    stage: str,
    predictor_id: str,
    probability: float,
    recorded_at: str,
    evidence_refs: Sequence[str],
    prior_seal_sha256: str | None = None,
    manifest_seal_sha256: str,
    challenge_ids: Sequence[str] = (),
    source_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage = _required_text(stage, "forecast stage").upper()
    if stage not in STAGES:
        raise ForecastContractError(f"unsupported forecast stage {stage!r}")
    _timestamp(recorded_at, f"{stage}.recorded_at")
    if stage == "F1" and (prior_seal_sha256 or challenge_ids):
        raise ForecastContractError("F1 cannot claim a prior seal or challenge")
    if stage == "F3":
        if not prior_seal_sha256 or len(prior_seal_sha256) != 64:
            raise ForecastContractError("F3 must reference the F1 seal")
        if not challenge_ids:
            raise ForecastContractError("F3 requires at least one F2 challenge")
    snapshot = _with_authority({
        "stage": stage,
        "predictor_id": _required_text(predictor_id, "predictor_id"),
        "probability": _probability(probability, stage),
        "recorded_at": recorded_at,
        "evidence_refs": [
            _required_text(item, "evidence_refs") for item in evidence_refs
        ],
        "prior_seal_sha256": prior_seal_sha256,
        "manifest_seal_sha256": manifest_seal_sha256,
        "challenge_ids": list(challenge_ids),
        "source_binding": copy.deepcopy(dict(source_binding)) if source_binding else None,
        "state": "SEALED",
    })
    return _seal(snapshot)


def verify_snapshot_seal(snapshot: Mapping[str, Any]) -> None:
    _validate_authority(snapshot, "forecast snapshot")
    if snapshot.get("state") != "SEALED":
        raise ForecastContractError("forecast snapshot must remain SEALED")
    if snapshot.get("stage") not in STAGES:
        raise ForecastContractError("forecast snapshot stage is invalid")
    _required_text(snapshot.get("predictor_id"), "forecast predictor_id")
    _probability(snapshot.get("probability"), str(snapshot.get("stage")))
    if not isinstance(snapshot.get("manifest_seal_sha256"), str) or len(snapshot["manifest_seal_sha256"]) != 64:
        raise ForecastContractError("forecast missing manifest binding")
    _timestamp(str(snapshot.get("recorded_at") or ""), "forecast snapshot")
    _required_text_list(
        list(snapshot.get("evidence_refs") or []), "forecast evidence_refs"
    )
    if snapshot.get("stage") == "F1":
        if snapshot.get("prior_seal_sha256") is not None:
            raise ForecastContractError("F1 cannot reference a prior forecast seal")
        if snapshot.get("challenge_ids") != []:
            raise ForecastContractError("F1 cannot bind challenges")
    else:
        prior = snapshot.get("prior_seal_sha256")
        if not isinstance(prior, str) or len(prior) != 64:
            raise ForecastContractError("F3 must bind a valid F1 seal")
        _required_text_list(list(snapshot.get("challenge_ids") or []), "F3 challenge_ids")
    _verify_seal(snapshot, "forecast snapshot")


def start_episode(
    manifest: Mapping[str, Any],
    *,
    predictor_id: str,
    probability: float,
    recorded_at: str,
    evidence_refs: Sequence[str],
    source_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    verify_manifest_seal(manifest)
    f1 = _sealed_snapshot(
        stage="F1",
        manifest_seal_sha256=manifest["seal_sha256"],
        predictor_id=predictor_id,
        probability=probability,
        recorded_at=recorded_at,
        evidence_refs=evidence_refs,
        source_binding=source_binding,
    )
    episode = {
        "schema_version": "0.1",
        "manifest": copy.deepcopy(dict(manifest)),
        "forecasts": [f1],
        "challenges": [],
        "resolution": None,
        "authority": dict(AUTHORITY),
    }
    validate_episode(episode)
    return episode


def challenge_episode(
    episode: Mapping[str, Any],
    *,
    challenger_id: str,
    reasons: Sequence[str],
    evidence_refs: Sequence[str],
    recorded_at: str,
) -> dict[str, Any]:
    validate_episode(episode)
    if episode.get("resolution") is not None:
        raise ForecastContractError("a resolved or annulled episode cannot be challenged")
    f1 = next(iter(episode["forecasts"]))
    challenger = _required_text(challenger_id, "challenger_id")
    if challenger in {item["predictor_id"] for item in episode["forecasts"]}:
        raise ForecastContractError("a forecaster cannot challenge its own forecast")
    at = _timestamp(recorded_at, "challenge.recorded_at")
    if at < _timestamp(f1["recorded_at"], "F1.recorded_at"):
        raise ForecastContractError("F2 challenge cannot precede F1")
    reason_list = _required_text_list(list(reasons), "challenge reasons")
    challenge = _seal(_with_authority({
        "challenge_id": _stable_id(
            "F2", episode["manifest"]["forecast_id"], challenger, recorded_at, *reason_list
        ),
        "stage": "F2",
        "manifest_seal_sha256": episode["manifest"]["seal_sha256"],
        "f1_seal_sha256": f1["seal_sha256"],
        "challenger_id": challenger,
        "reasons": reason_list,
        "evidence_refs": [
            _required_text(item, "challenge evidence_refs") for item in evidence_refs
        ],
        "recorded_at": recorded_at,
    }))
    updated = copy.deepcopy(dict(episode))
    updated["challenges"].append(challenge)
    validate_episode(updated)
    return updated


def correct_episode(
    episode: Mapping[str, Any],
    *,
    predictor_id: str,
    probability: float,
    recorded_at: str,
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    validate_episode(episode)
    if episode.get("resolution") is not None:
        raise ForecastContractError("a resolved or annulled episode cannot be corrected")
    if len(episode.get("forecasts") or []) != 1:
        raise ForecastContractError("v0.1 permits one F3 correction only")
    challenges = list(episode.get("challenges") or [])
    if not challenges:
        raise ForecastContractError("F3 requires an F2 challenge")
    last_challenge_at = max(
        _timestamp(item["recorded_at"], "F2.recorded_at") for item in challenges
    )
    if _timestamp(recorded_at, "F3.recorded_at") < last_challenge_at:
        raise ForecastContractError("F3 cannot precede its F2 challenge")
    if predictor_id in {item["challenger_id"] for item in challenges}:
        raise ForecastContractError("an F2 challenger cannot issue the F3 forecast")
    f1 = episode["forecasts"][0]
    f3 = _sealed_snapshot(
        stage="F3",
        manifest_seal_sha256=episode["manifest"]["seal_sha256"],
        predictor_id=predictor_id,
        probability=probability,
        recorded_at=recorded_at,
        evidence_refs=evidence_refs,
        prior_seal_sha256=f1["seal_sha256"],
        challenge_ids=[item["challenge_id"] for item in challenges],
    )
    updated = copy.deepcopy(dict(episode))
    updated["forecasts"].append(f3)
    validate_episode(updated)
    return updated


def resolve_episode(
    episode: Mapping[str, Any],
    *,
    outcome: int,
    resolver_id: str,
    source_refs: Sequence[str],
    resolved_at: str,
    witness_role: str = "INDEPENDENT_EXECUTION_WITNESS",
    verification_status: str = "ASSERTED",
    source_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validate_episode(episode)
    if episode.get("resolution") is not None:
        raise ForecastContractError("episode already has a terminal resolution")
    if isinstance(outcome, bool) or outcome not in (0, 1):
        raise ForecastContractError("binary outcome must be the integer 0 or 1")
    resolver = _required_text(resolver_id, "resolver_id")
    predictors = {item["predictor_id"] for item in episode["forecasts"]}
    if resolver in predictors:
        raise ForecastContractError("a forecaster cannot resolve its own forecast")
    challengers = {item["challenger_id"] for item in episode.get("challenges") or []}
    if resolver in challengers:
        raise ForecastContractError("a challenger cannot witness the outcome")
    latest_activity = max(
        _timestamp(item["recorded_at"], "forecast.recorded_at")
        for item in episode["forecasts"]
    )
    if episode.get("challenges"):
        latest_activity = max(
            latest_activity,
            max(
                _timestamp(item["recorded_at"], "challenge.recorded_at")
                for item in episode["challenges"]
            ),
        )
    if _timestamp(resolved_at, "resolved_at") < latest_activity:
        raise ForecastContractError("resolution cannot precede forecast or challenge activity")
    refs = _required_text_list(list(source_refs), "resolution source_refs")
    verification_status = _required_text(
        verification_status, "verification_status"
    ).upper()
    if verification_status not in VERIFICATION_STATUSES:
        raise ForecastContractError("verification_status is unsupported")
    receipt = _seal(_with_authority({
        "receipt_id": _stable_id(
            "OUTCOME",
            episode["manifest"]["forecast_id"],
            outcome,
            resolver,
            resolved_at,
            *refs,
        ),
        "status": "RESOLVED",
        "manifest_seal_sha256": episode["manifest"]["seal_sha256"],
        "terminal_forecast_seal_sha256": episode["forecasts"][-1]["seal_sha256"],
        "challenge_seals": [item["seal_sha256"] for item in episode["challenges"]],
        "outcome": outcome,
        "resolver_id": resolver,
        "witness_role": _required_text(witness_role, "witness_role"),
        "verification_status": verification_status,
        "source_refs": refs,
        "resolved_at": resolved_at,
        "source_binding": copy.deepcopy(dict(source_binding)) if source_binding else None,
    }))
    updated = copy.deepcopy(dict(episode))
    updated["resolution"] = receipt
    validate_episode(updated)
    return updated


def annul_episode(
    episode: Mapping[str, Any],
    *,
    resolver_id: str,
    reason: str,
    source_refs: Sequence[str],
    resolved_at: str,
) -> dict[str, Any]:
    validate_episode(episode)
    if episode.get("resolution") is not None:
        raise ForecastContractError("episode already has a terminal resolution")
    resolver = _required_text(resolver_id, "resolver_id")
    if resolver in {item["predictor_id"] for item in episode["forecasts"]}:
        raise ForecastContractError("a forecaster cannot annul its own forecast")
    if resolver in {item["challenger_id"] for item in episode.get("challenges") or []}:
        raise ForecastContractError("a challenger cannot witness the annulment")
    latest_activity = max(
        _timestamp(item["recorded_at"], "forecast.recorded_at")
        for item in episode["forecasts"]
    )
    if episode.get("challenges"):
        latest_activity = max(
            latest_activity,
            max(
                _timestamp(item["recorded_at"], "challenge.recorded_at")
                for item in episode["challenges"]
            ),
        )
    if _timestamp(resolved_at, "resolved_at") < latest_activity:
        raise ForecastContractError("annulment cannot precede forecast or challenge activity")
    updated = copy.deepcopy(dict(episode))
    updated["resolution"] = _seal(_with_authority({
        "receipt_id": _stable_id(
            "ANNUL", episode["manifest"]["forecast_id"], resolver, resolved_at
        ),
        "status": "ANNULLED",
        "manifest_seal_sha256": episode["manifest"]["seal_sha256"],
        "terminal_forecast_seal_sha256": episode["forecasts"][-1]["seal_sha256"],
        "challenge_seals": [item["seal_sha256"] for item in episode["challenges"]],
        "outcome": None,
        "resolver_id": resolver,
        "witness_role": "INDEPENDENT_RESOLUTION_WITNESS",
        "verification_status": "ASSERTED",
        "source_refs": _required_text_list(list(source_refs), "annul source_refs"),
        "resolved_at": resolved_at,
        "reason": _required_text(reason, "annul reason"),
        "source_binding": None,
    }))
    validate_episode(updated)
    return updated


def validate_episode(episode: Mapping[str, Any]) -> None:
    authority = episode.get("authority") or {}
    _validate_authority(authority, "episode")
    manifest = episode.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ForecastContractError("episode manifest is required")
    verify_manifest_seal(manifest)

    forecasts = episode.get("forecasts")
    if not isinstance(forecasts, list) or not forecasts:
        raise ForecastContractError("episode requires a sealed F1 forecast")
    if len(forecasts) > 2:
        raise ForecastContractError("v0.1 permits F1 and at most one F3")
    for snapshot in forecasts:
        verify_snapshot_seal(snapshot)
        if snapshot.get("manifest_seal_sha256") != manifest["seal_sha256"]:
            raise ForecastContractError("forecast snapshot belongs to a different manifest")
        recorded_at = _timestamp(snapshot["recorded_at"], "forecast.recorded_at")
        if manifest["evidence_cutoff"]["kind"] == "TIMESTAMP":
            cutoff = _timestamp(manifest["evidence_cutoff"]["ref"], "evidence_cutoff.ref")
            if cutoff > recorded_at:
                raise ForecastContractError("future evidence cutoff exceeds forecast recording")
        created_at = _timestamp(manifest["created_at"], "manifest.created_at")
        if recorded_at < created_at:
            raise ForecastContractError("forecast cannot precede its manifest")
        if manifest.get("closes_at") is not None and recorded_at > _timestamp(
            manifest["closes_at"], "manifest.closes_at"
        ):
            raise ForecastContractError("forecast cannot be sealed after the close")
    if forecasts[0].get("stage") != "F1":
        raise ForecastContractError("first forecast must be F1")
    if len(forecasts) == 2:
        f1, f3 = forecasts
        if f3.get("stage") != "F3":
            raise ForecastContractError("second forecast must be F3")
        if f3.get("prior_seal_sha256") != f1.get("seal_sha256"):
            raise ForecastContractError("F3 does not preserve the F1 lineage")

    challenges = episode.get("challenges")
    if not isinstance(challenges, list):
        raise ForecastContractError("episode challenges must be a list")
    challenge_ids: set[str] = set()
    predictors = {item["predictor_id"] for item in forecasts}
    for item in challenges:
        _validate_authority(item, "challenge")
        _verify_seal(item, "challenge")
        if (item.get("manifest_seal_sha256") != manifest["seal_sha256"]
                or item.get("f1_seal_sha256") != forecasts[0]["seal_sha256"]):
            raise ForecastContractError("challenge belongs to another forecast manifest or F1")
        if item.get("stage") != "F2":
            raise ForecastContractError("challenge stage must be F2")
        if item.get("challenger_id") in predictors:
            raise ForecastContractError("a forecaster cannot challenge its own forecast")
        _required_text(item.get("challenger_id"), "challenge.challenger_id")
        _required_text_list(list(item.get("reasons") or []), "challenge reasons")
        evidence_refs = item.get("evidence_refs")
        if not isinstance(evidence_refs, list):
            raise ForecastContractError("challenge evidence_refs must be a list")
        for ref in evidence_refs:
            _required_text(ref, "challenge evidence_refs")
        challenge_id = _required_text(item.get("challenge_id"), "challenge_id")
        if challenge_id in challenge_ids:
            raise ForecastContractError("duplicate challenge_id")
        challenge_ids.add(challenge_id)
        challenge_at = _timestamp(item["recorded_at"], "F2.recorded_at")
        if challenge_at < _timestamp(forecasts[0]["recorded_at"], "F1.recorded_at"):
            raise ForecastContractError("F2 cannot precede F1")
        if manifest.get("closes_at") is not None and challenge_at > _timestamp(
            manifest["closes_at"], "manifest.closes_at"
        ):
            raise ForecastContractError("F2 cannot be admitted after the close")
    if len(forecasts) == 2:
        if set(forecasts[1].get("challenge_ids") or []) != challenge_ids:
            raise ForecastContractError("F3 must bind every admitted F2 challenge")
        if not challenge_ids:
            raise ForecastContractError("F3 requires an F2 challenge")
        f3_at = _timestamp(forecasts[1]["recorded_at"], "F3.recorded_at")
        if any(_timestamp(item["recorded_at"], "F2.recorded_at") > f3_at for item in challenges):
            raise ForecastContractError("F3 cannot precede its F2 challenge")

    resolution = episode.get("resolution")
    if resolution is None:
        return
    if not isinstance(resolution, Mapping):
        raise ForecastContractError("resolution must be an object or null")
    _validate_authority(resolution, "resolution")
    _verify_seal(resolution, "resolution")
    if resolution.get("manifest_seal_sha256") != manifest["seal_sha256"]:
        raise ForecastContractError("resolution belongs to a different manifest")
    if resolution.get("terminal_forecast_seal_sha256") != forecasts[-1]["seal_sha256"]:
        raise ForecastContractError("resolution belongs to a different forecast lineage")
    if resolution.get("challenge_seals") != [item["seal_sha256"] for item in challenges]:
        raise ForecastContractError("resolution challenge lineage is inconsistent")
    if resolution.get("status") not in {"RESOLVED", "ANNULLED"}:
        raise ForecastContractError("resolution status must be RESOLVED or ANNULLED")
    if resolution.get("resolver_id") in predictors:
        raise ForecastContractError("a forecaster cannot resolve its own forecast")
    if resolution.get("resolver_id") in {
        item["challenger_id"] for item in challenges
    }:
        raise ForecastContractError("a challenger cannot witness the outcome")
    _required_text(resolution.get("resolver_id"), "resolution.resolver_id")
    _required_text(resolution.get("witness_role"), "resolution.witness_role")
    if resolution.get("verification_status") not in VERIFICATION_STATUSES:
        raise ForecastContractError("resolution verification_status is invalid")
    latest_activity = max(
        _timestamp(item["recorded_at"], "forecast.recorded_at") for item in forecasts
    )
    if challenges:
        latest_activity = max(
            latest_activity,
            max(
                _timestamp(item["recorded_at"], "challenge.recorded_at")
                for item in challenges
            ),
        )
    if _timestamp(resolution["resolved_at"], "resolved_at") < latest_activity:
        raise ForecastContractError("terminal resolution precedes forecast or challenge activity")
    _required_text_list(list(resolution.get("source_refs") or []), "resolution source_refs")
    if resolution["status"] == "RESOLVED":
        if isinstance(resolution.get("outcome"), bool) or resolution.get("outcome") not in (0, 1):
            raise ForecastContractError("resolved outcome must be 0 or 1")
    else:
        if resolution.get("outcome") is not None:
            raise ForecastContractError("annulled episode cannot carry an outcome")
        _required_text(resolution.get("reason"), "annul reason")


def brier_score(probability: float, outcome: int) -> float:
    """Scalar binary Brier score; 0 is perfect and 1 is worst."""
    p = _probability(probability, "Brier")
    if isinstance(outcome, bool) or outcome not in (0, 1):
        raise ForecastContractError("Brier outcome must be integer 0 or 1")
    return (p - float(outcome)) ** 2


def _log_loss(probability: float, outcome: int) -> float:
    p = min(max(_probability(probability, "log loss"), LOG_EPSILON), 1 - LOG_EPSILON)
    return -(outcome * math.log(p) + (1 - outcome) * math.log(1 - p))


def _logit(probability: float) -> float:
    p = min(max(probability, LOG_EPSILON), 1 - LOG_EPSILON)
    return math.log(p / (1 - p))


def score_episode(episode: Mapping[str, Any]) -> dict[str, Any]:
    validate_episode(episode)
    manifest = episode["manifest"]
    resolution = episode.get("resolution")
    base = {
        "forecast_id": manifest["forecast_id"],
        "question_key": manifest["question_key"],
        "provenance_kind": manifest["provenance"]["kind"],
        **AUTHORITY,
    }
    if manifest["mode"] != "EMPIRICAL":
        return _seal({**base, "status": "NOT_SCORED", "reason": "MODE_NOT_EMPIRICAL"})
    if resolution is None:
        return _seal({**base, "status": "NOT_SCORED", "reason": "OUTCOME_PENDING"})
    if resolution["status"] == "ANNULLED":
        return _seal({**base, "status": "NOT_SCORED", "reason": "ANNULLED"})

    selected = episode["forecasts"][-1]
    probability = float(selected["probability"])
    outcome = int(resolution["outcome"])
    receipt = {
        **base,
        "receipt_id": _stable_id(
            "CALIBRATION",
            manifest["forecast_id"],
            selected["seal_sha256"],
            resolution["receipt_id"],
        ),
        "status": "SCORED",
        "selected_stage": selected["stage"],
        "forecast_seal_sha256": selected["seal_sha256"],
        "outcome_receipt_id": resolution["receipt_id"],
        "probability": probability,
        "outcome": outcome,
        "brier": brier_score(probability, outcome),
        "log_loss": _log_loss(probability, outcome),
    }
    if len(episode["forecasts"]) == 2:
        receipt["f1_probability"] = float(episode["forecasts"][0]["probability"])
        receipt["odds_log_change_f3_minus_f1"] = (
            _logit(probability) - _logit(receipt["f1_probability"])
        )
    else:
        receipt["f1_probability"] = probability
        receipt["odds_log_change_f3_minus_f1"] = 0.0
    return _seal(receipt)


def aggregate_forecasts(members: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Linear pool whose independence-group weight is capped at its strongest member.

    Each member supplies a sealed ``forecast`` plus optional weights for past
    calibration, domain fit, evidence quality, freshness, and manipulation
    resistance.  Correlated voices sharing ``independence_group`` divide a
    capped group weight instead of multiplying influence by repetition.
    """
    if not members:
        raise ForecastContractError("aggregation requires at least one member")
    prepared: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    weight_names = (
        "calibration_weight",
        "domain_weight",
        "evidence_weight",
        "freshness_weight",
        "manipulation_resistance_weight",
    )
    seen_predictors: set[str] = set()
    seen_seals: set[str] = set()
    manifest_seals: set[str] = set()
    for member in members:
        snapshot = member.get("forecast")
        if not isinstance(snapshot, Mapping):
            raise ForecastContractError("aggregation member requires a sealed forecast")
        verify_snapshot_seal(snapshot)
        if snapshot["seal_sha256"] in seen_seals or snapshot["predictor_id"] in seen_predictors:
            raise ForecastContractError("duplicate forecaster or forecast seal in aggregation")
        seen_predictors.add(snapshot["predictor_id"])
        seen_seals.add(snapshot["seal_sha256"])
        manifest_seals.add(snapshot["manifest_seal_sha256"])
        if len(manifest_seals) > 1:
            raise ForecastContractError("cannot aggregate forecasts for different manifests")
        group = _required_text(member.get("independence_group"), "independence_group")
        raw = 1.0
        for name in weight_names:
            raw *= _probability(member.get(name, 1.0), name)
        item = {
            "predictor_id": snapshot["predictor_id"],
            "probability": float(snapshot["probability"]),
            "independence_group": group,
            "raw_weight": raw,
        }
        prepared.append(item)
        groups[group].append(item)

    effective_total = 0.0
    weighted_probability = 0.0
    for group_members in groups.values():
        raw_total = sum(item["raw_weight"] for item in group_members)
        if raw_total == 0:
            for item in group_members:
                item["effective_weight"] = 0.0
            continue
        group_cap = max(item["raw_weight"] for item in group_members)
        scale = group_cap / raw_total
        for item in group_members:
            effective = item["raw_weight"] * scale
            item["effective_weight"] = effective
            effective_total += effective
            weighted_probability += effective * item["probability"]
    if effective_total == 0:
        raise ForecastContractError("all aggregation weights are zero")
    return {
        "probability": weighted_probability / effective_total,
        "member_count": len(prepared),
        "independence_group_count": len(groups),
        "members": prepared,
        **AUTHORITY,
    }


def _calibration_bins(receipts: Sequence[Mapping[str, Any]], width: float = 0.2) -> list[dict[str, Any]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    count = round(1.0 / width)
    for receipt in receipts:
        index = min(count - 1, math.floor(float(receipt["probability"]) * count + 1e-9))
        grouped[index].append(receipt)
    bins = []
    for index in sorted(grouped):
        rows = grouped[index]
        bins.append({
            "lower": round(index * width, 10),
            "upper": round((index + 1) * width, 10),
            "n": len(rows),
            "mean_probability": sum(float(row["probability"]) for row in rows) / len(rows),
            "observed_rate": sum(int(row["outcome"]) for row in rows) / len(rows),
        })
    return bins


def score_cohort(
    episodes: Sequence[Mapping[str, Any]],
    *,
    eligible_forecast_ids: Iterable[str] | None = None,
    sampling_frame_ref: str | None = None,
    sampling_frame_sealed_before_outcomes: bool = False,
    minimum_claim_n: int = 20,
) -> dict[str, Any]:
    """Score a cohort while keeping accuracy claims fail-closed.

    Metrics remain descriptive unless the caller supplies the complete eligible
    sampling frame, every eligible item is resolved, the question contract is
    homogeneous, no record is synthetic, and ``minimum_claim_n`` is met.
    """
    if minimum_claim_n < 1:
        raise ForecastContractError("minimum_claim_n must be positive")
    all_ids: list[str] = []
    question_keys: set[str] = set()
    question_contracts: set[str] = set()
    provenance_kinds: set[str] = set()
    outcome_receipts_verified = True
    receipts: list[dict[str, Any]] = []
    not_scored: list[dict[str, Any]] = []
    for episode in episodes:
        validate_episode(episode)
        manifest = episode["manifest"]
        all_ids.append(manifest["forecast_id"])
        question_keys.add(manifest["question_key"])
        question_contracts.add(_sha256({
            "question_key": manifest["question_key"],
            "mode": manifest["mode"],
            "outcome_space": manifest["outcome_space"],
            "resolution_rule": manifest["resolution_rule"],
            "resolution_sources": manifest["resolution_sources"],
            "ambiguity_rule": manifest["ambiguity_rule"],
            "scoring": manifest["scoring"],
        }))
        provenance_kinds.add(manifest["provenance"]["kind"])
        receipt = score_episode(episode)
        if receipt["status"] == "SCORED":
            receipts.append(receipt)
            if episode["resolution"].get("verification_status") != "VERIFIED":
                outcome_receipts_verified = False
        else:
            not_scored.append(receipt)
    if len(set(all_ids)) != len(all_ids):
        raise ForecastContractError("cohort contains duplicate forecast ids")

    eligible_list = list(eligible_forecast_ids) if eligible_forecast_ids is not None else None
    eligible: set[str] | None = None
    sampling_unique = False
    if eligible_list is not None:
        eligible = set(eligible_list)
        sampling_unique = len(eligible) == len(eligible_list)
    sampling_complete = sampling_unique and eligible == set(all_ids)
    sampling_provenance_present = bool(
        isinstance(sampling_frame_ref, str) and sampling_frame_ref.strip()
    )
    homogeneous = len(question_keys) == 1 and len(question_contracts) == 1
    synthetic = "SYNTHETIC" in provenance_kinds
    # No independent frame/witness attestation is checked by this module.
    # Self-declared bools, hash strings and even a content-sealed frame are not
    # proof of pre-outcome independent registration. Fail closed on readiness.
    claim_ready = False
    report: dict[str, Any] = {
        "status": "SCORED" if receipts else "NO_SCOREABLE_FORECASTS",
        "claim_status": (
            "CALIBRATION_CLAIM_READY" if claim_ready else "DESCRIPTIVE_ONLY"
        ),
        "claim_blockers": [],
        "episode_count": len(episodes),
        "scored_count": len(receipts),
        "not_scored_count": len(not_scored),
        "sampling_frame_complete": sampling_complete,
        "sampling_frame_ref": sampling_frame_ref,
        "sampling_frame_sealed_before_outcomes": sampling_frame_sealed_before_outcomes,
        "homogeneous_question": homogeneous,
        "outcome_receipts_verified": outcome_receipts_verified,
        "question_keys": sorted(question_keys),
        "provenance_kinds": sorted(provenance_kinds),
        "minimum_claim_n": minimum_claim_n,
        "receipts": receipts,
        "not_scored": not_scored,
        **AUTHORITY,
    }
    if not sampling_complete:
        report["claim_blockers"].append("INCOMPLETE_OR_UNDECLARED_SAMPLING_FRAME")
    if not sampling_provenance_present:
        report["claim_blockers"].append("SAMPLING_FRAME_PROVENANCE_MISSING")
    if not sampling_frame_sealed_before_outcomes:
        report["claim_blockers"].append("SAMPLING_FRAME_NOT_PRECOMMITTED")
    report["claim_blockers"].append("INDEPENDENT_COHORT_ATTESTATION_UNAVAILABLE")
    if not homogeneous:
        report["claim_blockers"].append("MIXED_QUESTION_CONTRACTS")
    if synthetic:
        report["claim_blockers"].append("SYNTHETIC_RECORDS_PRESENT")
    if not outcome_receipts_verified:
        report["claim_blockers"].append("OUTCOME_RECEIPTS_NOT_INDEPENDENTLY_VERIFIED")
    if not_scored:
        report["claim_blockers"].append("UNRESOLVED_ANNULLED_OR_NONEMPIRICAL_RECORDS")
    if len(receipts) < minimum_claim_n:
        report["claim_blockers"].append("MINIMUM_SAMPLE_NOT_MET")
    if receipts:
        report.update({
            "mean_brier": sum(item["brier"] for item in receipts) / len(receipts),
            "mean_log_loss": sum(item["log_loss"] for item in receipts) / len(receipts),
            "mean_probability": (
                sum(item["probability"] for item in receipts) / len(receipts)
            ),
            "observed_rate": sum(item["outcome"] for item in receipts) / len(receipts),
            "calibration_bins": _calibration_bins(receipts),
        })
    return report


def verify_hash_chain(rows: Sequence[Mapping[str, Any]]) -> None:
    """Verify the existing NF/CI ledger SHA-256 and sequence chain."""
    previous_hash = ZERO_HASH
    previous_sequence = 0
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ForecastContractError(f"ledger row {index + 1} is not an object")
        sequence = row.get("seq")
        if not isinstance(sequence, int) or sequence != previous_sequence + 1:
            raise ForecastContractError(f"ledger sequence break at row {index + 1}")
        if row.get("prev_hash") != previous_hash:
            raise ForecastContractError(f"ledger prev_hash break at sequence {sequence}")
        recorded_hash = row.get("hash")
        body = {key: value for key, value in row.items() if key != "hash"}
        # NF ledger hashes use json.dumps(..., ensure_ascii=True) by default;
        # Oracle's own seals use ensure_ascii=False. They are separate contracts.
        legacy_encoded = json.dumps(body, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True).encode("utf-8")
        legacy_hash = hashlib.sha256(legacy_encoded).hexdigest()
        if not isinstance(recorded_hash, str) or legacy_hash != recorded_hash:
            raise ForecastContractError(f"ledger content hash break at sequence {sequence}")
        previous_hash = recorded_hash
        previous_sequence = sequence


def adapt_ci_predict_ledger(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Replay the existing prospective CI PIN/RESOLVE ledger as Oracle episodes."""
    verify_hash_chain(rows)
    tokens: dict[str, Mapping[str, Any]] = {}
    resolutions: dict[str, Mapping[str, Any]] = {}
    pins: list[Mapping[str, Any]] = []
    for row in rows:
        event_type = row.get("type")
        if event_type == "TOKEN":
            token_id = _required_text(row.get("token_id"), "TOKEN.token_id")
            if token_id in tokens:
                raise ForecastContractError(f"duplicate TOKEN {token_id!r}")
            tokens[token_id] = row
        elif event_type == "PIN":
            pins.append(row)
        elif event_type == "RESOLVE":
            token_id = _required_text(row.get("token_id"), "RESOLVE.token_id")
            if token_id in resolutions:
                raise ForecastContractError(f"duplicate RESOLVE {token_id!r}")
            resolutions[token_id] = row

    episodes: list[dict[str, Any]] = []
    for pin in pins:
        token_id = _required_text(pin.get("target"), "PIN.target")
        token = tokens.get(token_id)
        if token is None:
            raise ForecastContractError(f"PIN target {token_id!r} has no TOKEN")
        if token["seq"] >= pin["seq"]:
            raise ForecastContractError(f"PIN {pin.get('pin_id')!r} precedes its TOKEN")
        pin_id = _required_text(pin.get("pin_id"), "PIN.pin_id")
        claim = _required_text(pin.get("claim"), "PIN.claim")
        source_ref = f"ledgers/CI_PREDICT_LEDGER.jsonl#sha256={pin['hash']}"
        manifest = build_manifest(
            forecast_id=pin_id,
            question_key="ci_check_expected_conclusion_v1",
            question=claim,
            subject_ref=token_id,
            created_at=_normalized_timestamp(str(pin.get("at") or "")),
            closes_at=None,
            evidence_cutoff={
                "kind": "LEDGER_EVENT",
                "sequence": pin["seq"],
                "ref": pin["hash"],
            },
            resolution_rule=(
                "YES iff the matching completed GitHub Actions check concludes with "
                "the conclusion named in the sealed PIN; NO iff it completes with a "
                "different conclusion; missing or incomplete checks remain unscored."
            ),
            resolution_sources=["GITHUB_ACTIONS_JOB_RECEIPT"],
            owner="oracles/engine/forecast_replay_v0_1.py",
            privacy_class="PUBLIC_REPOSITORY",
            reflexivity="LOW",
            annul_rules=(
                "matching check never completes",
                "outcome source is not bound to the predicted check and head",
            ),
            provenance_kind="PROSPECTIVE_SOURCE_REPLAY",
            provenance_refs=[source_ref],
        )
        episode = start_episode(
            manifest,
            predictor_id=_required_text(pin.get("predictor"), "PIN.predictor"),
            probability=_probability(pin.get("p"), "PIN"),
            recorded_at=_normalized_timestamp(str(pin.get("at") or "")),
            evidence_refs=[source_ref],
            source_binding={
                "kind": "HASH_CHAIN_EVENT",
                "sequence": pin["seq"],
                "event_sha256": pin["hash"],
            },
        )
        resolution = resolutions.get(token_id)
        if resolution is not None:
            if resolution["seq"] <= pin["seq"]:
                raise ForecastContractError(f"RESOLVE for {token_id!r} precedes its PIN")
            outcome_name = resolution.get("outcome")
            if outcome_name not in {"YES", "NO"}:
                raise ForecastContractError(f"unsupported CI outcome {outcome_name!r}")
            episode = resolve_episode(
                episode,
                outcome=1 if outcome_name == "YES" else 0,
                resolver_id=_required_text(resolution.get("by"), "RESOLVE.by"),
                source_refs=[_required_text(resolution.get("source"), "RESOLVE.source")],
                resolved_at=_normalized_timestamp(str(resolution.get("at") or "")),
                witness_role="RECORDED_GITHUB_ACTIONS_JOB_REFERENCE",
                verification_status="RECORDED_NOT_REVERIFIED",
                source_binding={
                    "kind": "HASH_CHAIN_EVENT",
                    "sequence": resolution["seq"],
                    "event_sha256": resolution["hash"],
                },
            )
        episodes.append(episode)
    return episodes
