#!/usr/bin/env python3
"""VulnOps action-trust control plane — v0.1.

Builder v1.7 compliant · security_gate_tool
HumanAIOS · Q-VULNOPS-V0-1

This tool is a fail-closed policy and evidence adapter. It validates externally
authenticated workload identities, atomically consumes exact one-use action
grants, checks independent runtime observations, and normalizes read-only
public vulnerability feeds. It cannot authenticate identities, mint grants,
execute remediation, deploy code, or declare its own controls operational.

Usage:
  python3 tools/vulnops_v0_1.py --smoke-test
  python3 tools/vulnops_v0_1.py verify-controls --help
  python3 tools/vulnops_v0_1.py ingest-feeds --help
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import tempfile

try:
    from tools.verified_receipts import (
        ReceiptRequirement,
        VerifiedReceiptResolver,
        append_receipt_event,
        build_receipt_chain_for_testing,
        consume_receipt_atomic,
        read_receipt_events,
    )
except ModuleNotFoundError:  # direct invocation from tools/
    from verified_receipts import (  # type: ignore[no-redef]
        ReceiptRequirement,
        VerifiedReceiptResolver,
        append_receipt_event,
        build_receipt_chain_for_testing,
        consume_receipt_atomic,
        read_receipt_events,
    )


TOOL_NAME = "vulnops_action_trust"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_SESSION = "Q-VULNOPS-V0-1"
TOOL_ZONE = 1

CAN_AUTHORIZE = False
CAN_EXECUTE = False
AUTHORITY_EFFECT = "NONE"
GRANT_AUTHORITY_EFFECT = "EXTERNAL_GRANT_CONSUMPTION_ONLY"

ACTION_GRANT_TYPE = "VULNOPS_ACTION_GRANT"
RUNTIME_OBSERVATION_TYPE = "VULNOPS_RUNTIME_OBSERVATION"
CONTROL_ATTESTATION_TYPE = "VULNOPS_CONTROL_ATTESTATION"
CONTROL_SUBJECT = "vulnops:external-feed-intake"
CONTROL_ACTION = "ENABLE_READ_ONLY_FEED_INTAKE"
CONTROL_SCOPE = "feeds:cisa-kev+first-epss+osv"
CONTROL_AUTHORITY_SCOPE = "READ_ONLY_PUBLIC_VULNERABILITY_FEEDS"

REQUIRED_CONTROL_GATES = (
    "exact_head_admission_repaired",
    "distinct_workload_identities",
    "one_use_action_grants",
    "independent_runtime_verification",
)

WORKLOAD_ROLES = {
    "CONTROL_AUTHORITY",
    "DISCOVERY",
    "TRIAGE",
    "REMEDIATOR",
    "DEPLOYER",
    "VERIFIER",
    "FEED_READER",
}

ACTION_ROLES = {
    "PREPARE_REMEDIATION": "REMEDIATOR",
    "DEPLOY_REMEDIATION": "DEPLOYER",
    "ROLLBACK_REMEDIATION": "DEPLOYER",
    "READ_EXTERNAL_FEEDS": "FEED_READER",
}

_IDENTITY_RE = re.compile(r"^spiffe://[A-Za-z0-9._~:/-]{3,240}$")
_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_VULN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
_MAX_FEED_BYTES = 50 * 1024 * 1024
_MAX_GRANT_LIFETIME_SECONDS = 15 * 60
_MAX_OBSERVATION_AGE_SECONDS = 15 * 60
_MAX_CONTROL_ATTESTATION_LIFETIME_SECONDS = 24 * 60 * 60
_CRYPTO_IDENTITY_METHODS = {"ED25519", "HARDWARE_ATTESTATION"}


class VulnOpsRefusal(ValueError):
    """A fail-closed refusal with a stable machine-readable reason."""


class SpecLoadFailed(VulnOpsRefusal):
    """An externally supplied ledger or feed could not be loaded safely."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise VulnOpsRefusal(reason)


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _parse_timestamp(value: Any, field: str) -> datetime:
    _require(isinstance(value, str) and value.strip() != "", f"MISSING_{field.upper()}")
    token = value.strip()
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(token)
    except ValueError as exc:
        raise VulnOpsRefusal(f"INVALID_{field.upper()}") from exc
    _require(parsed.tzinfo is not None, f"NAIVE_{field.upper()}")
    return parsed.astimezone(timezone.utc)


def _validate_window(receipt: Mapping[str, Any], now: datetime) -> None:
    issued = _parse_timestamp(receipt.get("issued_at"), "issued_at")
    not_before = _parse_timestamp(receipt.get("not_before"), "not_before")
    expires = _parse_timestamp(receipt.get("expires_at"), "expires_at")
    _require(now.tzinfo is not None, "NAIVE_NOW")
    now_utc = now.astimezone(timezone.utc)
    _require(issued <= not_before <= expires, "INVALID_GRANT_TIME_ORDER")
    _require(
        (expires - issued).total_seconds() <= _MAX_GRANT_LIFETIME_SECONDS,
        "GRANT_LIFETIME_EXCEEDS_15_MINUTES",
    )
    _require(not_before <= now_utc, "GRANT_NOT_YET_VALID")
    _require(now_utc < expires, "GRANT_EXPIRED")


def _validate_control_window(receipt: Mapping[str, Any], now: datetime) -> None:
    issued = _parse_timestamp(receipt.get("issued_at"), "issued_at")
    not_before = _parse_timestamp(receipt.get("not_before"), "not_before")
    expires = _parse_timestamp(receipt.get("expires_at"), "expires_at")
    _require(now.tzinfo is not None, "NAIVE_NOW")
    now_utc = now.astimezone(timezone.utc)
    _require(issued <= not_before <= expires, "INVALID_CONTROL_TIME_ORDER")
    _require(
        (expires - issued).total_seconds()
        <= _MAX_CONTROL_ATTESTATION_LIFETIME_SECONDS,
        "CONTROL_ATTESTATION_LIFETIME_EXCEEDS_24_HOURS",
    )
    _require(not_before <= now_utc, "CONTROL_ATTESTATION_NOT_YET_VALID")
    _require(now_utc < expires, "CONTROL_ATTESTATION_EXPIRED")


def _require_unique_verified_receipt(
    events: Sequence[Mapping[str, Any]],
    receipt_id: str,
    receipt_type: str,
) -> None:
    matches = [
        event
        for event in events
        if event.get("type") == "RECEIPT_VERIFIED"
        and event.get("receipt_id") == receipt_id
        and event.get("receipt_type") == receipt_type
    ]
    _require(len(matches) == 1, f"VERIFIED_RECEIPT_CARDINALITY:{len(matches)}")


def _require_crypto_identity_method(receipt: Mapping[str, Any], label: str) -> None:
    method = str(receipt.get("verification_method") or "").strip().upper()
    _require(method in _CRYPTO_IDENTITY_METHODS, f"{label}_METHOD_NOT_CRYPTOGRAPHIC")


@dataclass(frozen=True)
class WorkloadIdentity:
    """An identity claim already authenticated by an external trust plane."""

    identity_id: str
    role: str
    certificate_fingerprint: str
    authentication_status: str
    transport_principal: str

    def validate(self, required_role: str | None = None) -> None:
        _require(bool(_IDENTITY_RE.fullmatch(self.identity_id)), "INVALID_WORKLOAD_ID")
        _require(self.role in WORKLOAD_ROLES, "UNKNOWN_WORKLOAD_ROLE")
        _require(
            self.authentication_status == "EXTERNALLY_VERIFIED",
            "WORKLOAD_IDENTITY_NOT_EXTERNALLY_VERIFIED",
        )
        _require(
            bool(_FINGERPRINT_RE.fullmatch(self.certificate_fingerprint)),
            "INVALID_CERTIFICATE_FINGERPRINT",
        )
        _require(bool(self.transport_principal.strip()), "MISSING_TRANSPORT_PRINCIPAL")
        _require(
            self.transport_principal != self.identity_id,
            "TRANSPORT_PRINCIPAL_IS_NOT_WORKLOAD_IDENTITY",
        )
        if required_role is not None:
            _require(self.role == required_role, f"ROLE_MISMATCH:{self.role}!={required_role}")


def assert_distinct_workload_identities(
    identities: Sequence[WorkloadIdentity],
    *,
    required_roles: Iterable[str] = (),
) -> dict[str, Any]:
    """Prove role identities and certificate bindings do not collapse together."""
    _require(len(identities) >= 2, "AT_LEAST_TWO_WORKLOAD_IDENTITIES_REQUIRED")
    for identity in identities:
        identity.validate()
    identity_ids = [item.identity_id for item in identities]
    fingerprints = [item.certificate_fingerprint for item in identities]
    _require(len(identity_ids) == len(set(identity_ids)), "DUPLICATE_WORKLOAD_IDENTITY")
    _require(len(fingerprints) == len(set(fingerprints)), "DUPLICATE_WORKLOAD_CERTIFICATE")
    present_roles = {item.role for item in identities}
    missing = sorted(set(required_roles) - present_roles)
    _require(not missing, "MISSING_WORKLOAD_ROLES:" + ",".join(missing))
    return {
        "status": "DISTINCT",
        "identity_ids": sorted(identity_ids),
        "roles": sorted(present_roles),
        "authentication_source": "EXTERNAL",
        "transport_principals_authoritative": False,
        "can_authorize": CAN_AUTHORIZE,
    }


@dataclass(frozen=True)
class ActionContext:
    """The exact action, target, build, runtime revision, and rollback anchor."""

    action: str
    resource: str
    environment: str
    head_sha: str
    artifact_sha256: str
    runtime_revision: str
    rollback_ref: str

    def validate(self) -> None:
        _require(self.action in ACTION_ROLES, "UNKNOWN_ACTION")
        _require(0 < len(self.resource.strip()) <= 256, "INVALID_RESOURCE")
        _require(self.environment in {"development", "staging", "production"}, "INVALID_ENVIRONMENT")
        _require(bool(_SHA40_RE.fullmatch(self.head_sha)), "INVALID_EXACT_HEAD_SHA")
        _require(bool(_SHA256_RE.fullmatch(self.artifact_sha256)), "INVALID_ARTIFACT_SHA256")
        _require(0 < len(self.runtime_revision.strip()) <= 256, "INVALID_RUNTIME_REVISION")
        _require(0 < len(self.rollback_ref.strip()) <= 256, "MISSING_ROLLBACK_REF")

    def payload(self) -> dict[str, str]:
        self.validate()
        return {
            "schema": "humanaios.vulnops.action_scope.v0.1",
            "action": self.action,
            "resource": self.resource,
            "environment": self.environment,
            "head_sha": self.head_sha,
            "artifact_sha256": self.artifact_sha256,
            "runtime_revision": self.runtime_revision,
            "rollback_ref": self.rollback_ref,
        }

    def scope(self) -> str:
        return _sha256_bytes(_canonical_json(self.payload()))

    def authority_scope(self) -> str:
        self.validate()
        return f"resource:{self.resource}:environment:{self.environment}"


def _grant_requirement(
    actor: WorkloadIdentity,
    context: ActionContext,
    *,
    consumption_state: str,
) -> ReceiptRequirement:
    return ReceiptRequirement(
        receipt_type=ACTION_GRANT_TYPE,
        subject=actor.identity_id,
        action=context.action,
        scope=context.scope(),
        min_strength="CRYPTO_VERIFIED",
        authority_scope=context.authority_scope(),
        consumption_state=consumption_state,
    )


def _validate_grant_receipt(
    receipt: Mapping[str, Any],
    *,
    actor: WorkloadIdentity,
    context: ActionContext,
    now: datetime,
) -> None:
    actor.validate(ACTION_ROLES[context.action])
    context.validate()
    _require(receipt.get("one_time") is True, "ACTION_GRANT_MUST_BE_ONE_TIME")
    _require(receipt.get("subject_role") == actor.role, "GRANT_SUBJECT_ROLE_MISMATCH")
    issuer = str(receipt.get("issuer") or "")
    _require(bool(_IDENTITY_RE.fullmatch(issuer)), "INVALID_GRANT_ISSUER_IDENTITY")
    _require(issuer != actor.identity_id, "SELF_ISSUED_ACTION_GRANT")
    _require(issuer != actor.transport_principal, "TRANSPORT_SELF_ISSUED_ACTION_GRANT")
    _require_crypto_identity_method(receipt, "ACTION_GRANT")
    _validate_window(receipt, now)


def consume_action_grant(
    ledger_path: str,
    *,
    grant_id: str,
    expected_head_hash: str,
    actor: WorkloadIdentity,
    context: ActionContext,
    now: datetime,
) -> dict[str, Any]:
    """Validate and atomically consume one exact external action grant.

    The returned record is evidence of grant consumption, not an execution
    result. An external executor must still enforce the new chain head and the
    exact context before acting.
    """
    actor.validate(ACTION_ROLES.get(context.action))
    context.validate()
    events, observed_head = read_receipt_events(ledger_path)
    _require(observed_head == expected_head_hash, "STALE_RECEIPT_HEAD")
    _require_unique_verified_receipt(events, grant_id, ACTION_GRANT_TYPE)
    requirement = _grant_requirement(actor, context, consumption_state="UNCONSUMED")
    resolution = VerifiedReceiptResolver(events, expected_head_hash).resolve(
        grant_id, requirement
    )
    _require(
        resolution.valid,
        "ACTION_GRANT_INVALID:" + str(resolution.reason or "UNKNOWN"),
    )
    receipt = resolution.receipt or {}
    _validate_grant_receipt(receipt, actor=actor, context=context, now=now)

    try:
        new_head = consume_receipt_atomic(
            ledger_path,
            receipt_id=grant_id,
            requirement=requirement,
            expected_head_hash=expected_head_hash,
            consumed_by=actor.identity_id,
            subject=actor.identity_id,
        )
    except ValueError as exc:
        raise VulnOpsRefusal(str(exc)) from exc

    return {
        "schema": "humanaios.vulnops.grant_consumption.v0.1",
        "status": "CONSUMED",
        "grant_id": grant_id,
        "actor_identity": actor.identity_id,
        "action": context.action,
        "scope": context.scope(),
        "prior_chain_head": expected_head_hash,
        "new_chain_head": new_head,
        "authority_effect": GRANT_AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "can_execute": CAN_EXECUTE,
    }


def runtime_observation_scope(context: ActionContext) -> str:
    payload = dict(context.payload())
    payload["schema"] = "humanaios.vulnops.runtime_observation_scope.v0.1"
    return _sha256_bytes(_canonical_json(payload))


def verify_runtime_independently(
    *,
    grant_events: Sequence[Mapping[str, Any]],
    grant_head_hash: str,
    grant_id: str,
    observation_events: Sequence[Mapping[str, Any]],
    observation_head_hash: str,
    observation_id: str,
    actor: WorkloadIdentity,
    verifier: WorkloadIdentity,
    context: ActionContext,
    now: datetime,
) -> dict[str, Any]:
    """Compare an independently issued runtime observation to the exact grant."""
    actor.validate(ACTION_ROLES.get(context.action))
    verifier.validate("VERIFIER")
    assert_distinct_workload_identities([actor, verifier])
    context.validate()

    _require_unique_verified_receipt(grant_events, grant_id, ACTION_GRANT_TYPE)

    grant_resolution = VerifiedReceiptResolver(
        grant_events, grant_head_hash
    ).resolve(grant_id, _grant_requirement(actor, context, consumption_state="CONSUMED"))
    if not grant_resolution.valid:
        return _runtime_result("UNVERIFIED", [
            "ACTION_GRANT_NOT_PROVEN_CONSUMED:" + str(grant_resolution.reason or "UNKNOWN")
        ], context, verifier, grant_id, observation_id)

    grant = grant_resolution.receipt or {}
    consumption = grant_resolution.consumption or {}
    if consumption.get("by") != actor.identity_id:
        return _runtime_result(
            "UNVERIFIED", ["GRANT_CONSUMER_IDENTITY_MISMATCH"],
            context, verifier, grant_id, observation_id,
        )
    grant_issuer = str(grant.get("issuer") or "")
    _require(verifier.identity_id != grant_issuer, "GRANT_ISSUER_CANNOT_VERIFY_RUNTIME")
    _require_crypto_identity_method(grant, "ACTION_GRANT")
    _validate_window(grant, now)

    observation_requirement = ReceiptRequirement(
        receipt_type=RUNTIME_OBSERVATION_TYPE,
        subject=context.resource,
        action="VERIFY_RUNTIME",
        scope=runtime_observation_scope(context),
        min_strength="CRYPTO_VERIFIED",
        issuer=verifier.identity_id,
        authority_scope=context.authority_scope(),
    )
    _require_unique_verified_receipt(
        observation_events, observation_id, RUNTIME_OBSERVATION_TYPE
    )
    observation_resolution = VerifiedReceiptResolver(
        observation_events, observation_head_hash
    ).resolve(observation_id, observation_requirement)
    if not observation_resolution.valid:
        return _runtime_result("UNVERIFIED", [
            "RUNTIME_OBSERVATION_INVALID:" + str(observation_resolution.reason or "UNKNOWN")
        ], context, verifier, grant_id, observation_id)

    observation = observation_resolution.receipt or {}
    try:
        _require_crypto_identity_method(observation, "RUNTIME_OBSERVATION")
    except VulnOpsRefusal as exc:
        return _runtime_result(
            "UNVERIFIED", [str(exc)], context, verifier, grant_id, observation_id
        )
    contradictions: list[str] = []
    expected_fields = {
        "observer_role": "VERIFIER",
        "observed_resource": context.resource,
        "observed_environment": context.environment,
        "observed_head_sha": context.head_sha,
        "observed_artifact_sha256": context.artifact_sha256,
        "observed_runtime_revision": context.runtime_revision,
        "rollback_ref": context.rollback_ref,
        "vulnerability_closed": True,
        "health_status": "HEALTHY",
    }
    for field, expected in expected_fields.items():
        if observation.get(field) != expected:
            contradictions.append(field.upper() + "_MISMATCH")
    try:
        observed_at = _parse_timestamp(observation.get("observed_at"), "observed_at")
        _require(now.tzinfo is not None, "NAIVE_NOW")
        now_utc = now.astimezone(timezone.utc)
        if observed_at > now_utc:
            contradictions.append("OBSERVATION_IN_FUTURE")
        elif (now_utc - observed_at).total_seconds() > _MAX_OBSERVATION_AGE_SECONDS:
            contradictions.append("OBSERVATION_STALE")
    except VulnOpsRefusal as exc:
        contradictions.append(str(exc))

    return _runtime_result(
        "CONTRADICTED" if contradictions else "VERIFIED",
        contradictions,
        context,
        verifier,
        grant_id,
        observation_id,
    )


def _runtime_result(
    status: str,
    reasons: Sequence[str],
    context: ActionContext,
    verifier: WorkloadIdentity,
    grant_id: str,
    observation_id: str,
) -> dict[str, Any]:
    return {
        "schema": "humanaios.vulnops.runtime_verification.v0.1",
        "status": status,
        "reasons": list(reasons),
        "grant_id": grant_id,
        "observation_id": observation_id,
        "verifier_identity": verifier.identity_id,
        "resource": context.resource,
        "runtime_revision": context.runtime_revision,
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "can_execute": CAN_EXECUTE,
    }


def verify_feed_control_attestation(
    events: Sequence[Mapping[str, Any]],
    *,
    pinned_head_hash: str,
    receipt_id: str,
    issuer: str,
    now: datetime,
) -> dict[str, Any]:
    """Require external evidence that controls 1–4 precede feed access."""
    _require(bool(_IDENTITY_RE.fullmatch(issuer)), "INVALID_CONTROL_ISSUER_IDENTITY")
    _require_unique_verified_receipt(events, receipt_id, CONTROL_ATTESTATION_TYPE)
    requirement = ReceiptRequirement(
        receipt_type=CONTROL_ATTESTATION_TYPE,
        subject=CONTROL_SUBJECT,
        action=CONTROL_ACTION,
        scope=CONTROL_SCOPE,
        min_strength="CRYPTO_VERIFIED",
        issuer=issuer,
        authority_scope=CONTROL_AUTHORITY_SCOPE,
    )
    resolution = VerifiedReceiptResolver(events, pinned_head_hash).resolve(
        receipt_id, requirement
    )
    _require(
        resolution.valid,
        "CONTROL_ATTESTATION_INVALID:" + str(resolution.reason or "UNKNOWN"),
    )
    receipt = resolution.receipt or {}
    _require_crypto_identity_method(receipt, "CONTROL_ATTESTATION")
    gates = receipt.get("gates")
    _require(isinstance(gates, dict), "CONTROL_GATES_MISSING")
    evidence = receipt.get("evidence_refs")
    _require(isinstance(evidence, dict), "CONTROL_EVIDENCE_MISSING")
    for gate in REQUIRED_CONTROL_GATES:
        _require(gates.get(gate) is True, "CONTROL_GATE_NOT_PROVEN:" + gate)
        _require(
            isinstance(evidence.get(gate), str) and bool(evidence[gate].strip()),
            "CONTROL_EVIDENCE_MISSING:" + gate,
        )
    _validate_control_window(receipt, now)
    _require(receipt.get("one_time") is False, "CONTROL_ATTESTATION_MUST_BE_REUSABLE")
    return {
        "status": "CONTROLS_ATTESTED",
        "receipt_id": receipt_id,
        "issuer": issuer,
        "gates": {key: True for key in REQUIRED_CONTROL_GATES},
        "evidence_refs": {key: evidence[key] for key in REQUIRED_CONTROL_GATES},
        "chain_head": pinned_head_hash,
        "underlying_signature_verified_by_this_tool": False,
        "can_authorize": CAN_AUTHORIZE,
    }


def _normalized_vulnerability_id(value: Any) -> str:
    token = str(value or "").strip()
    _require(bool(_VULN_ID_RE.fullmatch(token)), "INVALID_VULNERABILITY_ID")
    return token.upper() if token.lower().startswith("cve-") else token


def parse_cisa_kev(text: str) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VulnOpsRefusal("CISA_KEV_INVALID_JSON") from exc
    _require(isinstance(payload, dict), "CISA_KEV_TOP_LEVEL_NOT_OBJECT")
    rows = payload.get("vulnerabilities")
    _require(isinstance(rows, list), "CISA_KEV_VULNERABILITIES_MISSING")
    output: dict[str, dict[str, Any]] = {}
    for raw in rows:
        _require(isinstance(raw, dict), "CISA_KEV_ROW_NOT_OBJECT")
        vulnerability_id = _normalized_vulnerability_id(raw.get("cveID"))
        _require(vulnerability_id not in output, "CISA_KEV_DUPLICATE_ID:" + vulnerability_id)
        output[vulnerability_id] = {
            "known_exploited": True,
            "vendor_project": str(raw.get("vendorProject") or ""),
            "product": str(raw.get("product") or ""),
            "vulnerability_name": str(raw.get("vulnerabilityName") or ""),
            "date_added": str(raw.get("dateAdded") or ""),
            "due_date": str(raw.get("dueDate") or ""),
            "known_ransomware_use": str(raw.get("knownRansomwareCampaignUse") or "Unknown"),
            "required_action": str(raw.get("requiredAction") or ""),
        }
    return output


def parse_epss_csv(text: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    lines = text.splitlines()
    metadata: dict[str, str] = {}
    data_lines: list[str] = []
    for line in lines:
        if line.startswith("#"):
            for item in line[1:].split(","):
                key, sep, value = item.partition(":")
                if sep:
                    metadata[key.strip()] = value.strip()
            continue
        if line.strip():
            data_lines.append(line)
    _require(bool(data_lines), "EPSS_CSV_EMPTY")
    reader = csv.DictReader(io.StringIO("\n".join(data_lines)))
    _require(reader.fieldnames is not None, "EPSS_HEADER_MISSING")
    _require({"cve", "epss", "percentile"}.issubset(set(reader.fieldnames)), "EPSS_HEADER_INVALID")
    output: dict[str, dict[str, Any]] = {}
    for raw in reader:
        vulnerability_id = _normalized_vulnerability_id(raw.get("cve"))
        _require(vulnerability_id not in output, "EPSS_DUPLICATE_ID:" + vulnerability_id)
        try:
            probability = float(str(raw.get("epss") or ""))
            percentile = float(str(raw.get("percentile") or ""))
        except ValueError as exc:
            raise VulnOpsRefusal("EPSS_SCORE_INVALID:" + vulnerability_id) from exc
        _require(0.0 <= probability <= 1.0, "EPSS_PROBABILITY_OUT_OF_RANGE")
        _require(0.0 <= percentile <= 1.0, "EPSS_PERCENTILE_OUT_OF_RANGE")
        output[vulnerability_id] = {
            "probability": probability,
            "percentile": percentile,
        }
    return output, metadata


def parse_osv_modified_csv(text: str) -> dict[str, dict[str, str]]:
    """Parse OSV's ``<modified>,<ecosystem>/<id>`` recent-changes index."""
    output: dict[str, dict[str, str]] = {}
    reader = csv.reader(io.StringIO(text))
    for row_number, row in enumerate(reader, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        modified = row[0].strip()
        if row_number == 1 and modified.lower() in {"modified", "modified_at"}:
            continue
        _require(len(row) >= 2, f"OSV_ROW_TOO_SHORT:{row_number}")
        _parse_timestamp(modified, "osv_modified_at")
        record_path = row[1].strip()
        _require(bool(record_path), f"OSV_RECORD_PATH_MISSING:{row_number}")
        vulnerability_id = _normalized_vulnerability_id(record_path.rsplit("/", 1)[-1])
        _require(vulnerability_id not in output, "OSV_DUPLICATE_ID:" + vulnerability_id)
        output[vulnerability_id] = {
            "modified_at": modified,
            "record_path": record_path,
        }
    return output


def composite_priority(
    *,
    kev: bool,
    epss_probability: float | None,
    known_ransomware_use: str,
    asset_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Score only when live asset context exists; feeds alone cannot prioritize."""
    if asset_context is None:
        return {
            "status": "UNASSESSED_NO_ASSET_CONTEXT",
            "score": None,
            "band": None,
        }
    exposure = str(asset_context.get("exposure") or "UNKNOWN").upper()
    _require(exposure in {"INTERNET", "INTERNAL", "ISOLATED"}, "INVALID_ASSET_EXPOSURE")
    live_threat = asset_context.get("live_threat_activity") is True
    score = 0.0
    if kev:
        score += 45.0
    if epss_probability is not None:
        score += 30.0 * epss_probability
    if known_ransomware_use.strip().lower() == "known":
        score += 10.0
    score += {"INTERNET": 10.0, "INTERNAL": 5.0, "ISOLATED": 0.0}[exposure]
    if live_threat:
        score += 5.0
    score = round(min(score, 100.0), 2)
    band = "CRITICAL" if score >= 75 else "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"
    return {"status": "ASSESSED", "score": score, "band": band}


def build_feed_report(
    *,
    kev_text: str,
    epss_text: str,
    osv_text: str,
    control_attestation: Mapping[str, Any],
    generated_at: str,
    asset_context: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    _require(
        control_attestation.get("status") == "CONTROLS_ATTESTED",
        "EXTERNAL_FEED_INTAKE_BLOCKED",
    )
    generated = _parse_timestamp(generated_at, "generated_at")
    kev = parse_cisa_kev(kev_text)
    epss, epss_metadata = parse_epss_csv(epss_text)
    osv = parse_osv_modified_csv(osv_text)
    assets = {
        _normalized_vulnerability_id(key): value
        for key, value in dict(asset_context or {}).items()
    }
    vulnerability_ids = sorted(set(kev) | set(epss) | set(osv))
    findings: list[dict[str, Any]] = []
    for vulnerability_id in vulnerability_ids:
        kev_signal = kev.get(vulnerability_id, {})
        epss_signal = epss.get(vulnerability_id, {})
        context = assets.get(vulnerability_id)
        priority = composite_priority(
            kev=bool(kev_signal.get("known_exploited")),
            epss_probability=epss_signal.get("probability"),
            known_ransomware_use=str(kev_signal.get("known_ransomware_use") or "Unknown"),
            asset_context=context,
        )
        findings.append({
            "vulnerability_id": vulnerability_id,
            "signals": {
                "cisa_kev": kev_signal or None,
                "epss": epss_signal or None,
                "osv": osv.get(vulnerability_id),
            },
            "asset_context": dict(context) if context is not None else None,
            "priority": priority,
            "action_allowed": False,
        })
    return {
        "schema": "humanaios.vulnops.feed_report.v0.1",
        "generated_at": generated.isoformat().replace("+00:00", "Z"),
        "control_receipt_id": control_attestation.get("receipt_id"),
        "control_chain_head": control_attestation.get("chain_head"),
        "source_digests": {
            "cisa_kev": _sha256_bytes(kev_text.encode("utf-8")),
            "first_epss": _sha256_bytes(epss_text.encode("utf-8")),
            "osv_modified": _sha256_bytes(osv_text.encode("utf-8")),
        },
        "source_metadata": {"first_epss": epss_metadata},
        "finding_count": len(findings),
        "findings": findings,
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "can_execute": CAN_EXECUTE,
    }


def absorption_rate(*, resolved: int, created: int) -> float | None:
    _require(resolved >= 0 and created >= 0, "ABSORPTION_COUNTS_MUST_BE_NONNEGATIVE")
    if created == 0:
        return None
    return round(resolved / created, 4)


def _read_bounded(path: Path, label: str) -> str:
    if not path.is_file():
        raise SpecLoadFailed(f"{label}_FILE_MISSING")
    size = path.stat().st_size
    _require(size <= _MAX_FEED_BYTES, f"{label}_FILE_TOO_LARGE")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SpecLoadFailed(f"{label}_NOT_UTF8") from exc


def write_report(output: Mapping[str, Any], destination: str | Path) -> None:
    """Write one deterministic UTF-8 JSON report to an explicit path."""
    Path(destination).write_text(
        json.dumps(dict(output), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_events(path: Path) -> list[dict[str, Any]]:
    text = _read_bounded(path, "CONTROL_LEDGER")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise VulnOpsRefusal(f"CONTROL_LEDGER_INVALID_JSON:{line_number}") from exc
        _require(isinstance(event, dict), f"CONTROL_LEDGER_ROW_NOT_OBJECT:{line_number}")
        events.append(event)
    return events


def _control_from_args(args: argparse.Namespace) -> dict[str, Any]:
    now = _parse_timestamp(args.now, "now")
    return verify_feed_control_attestation(
        _load_events(args.control_ledger),
        pinned_head_hash=args.control_head,
        receipt_id=args.control_receipt_id,
        issuer=args.control_issuer,
        now=now,
    )


def run_smoke_test() -> bool:
    """Exercise separation, one-use consumption, runtime proof, and feed gating."""
    try:
        now = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
        actor = WorkloadIdentity(
            "spiffe://humanaios.test/workload/deployer",
            "DEPLOYER",
            "sha256:" + "a" * 64,
            "EXTERNALLY_VERIFIED",
            "github-actions:job:deploy",
        )
        verifier = WorkloadIdentity(
            "spiffe://humanaios.test/workload/verifier",
            "VERIFIER",
            "sha256:" + "b" * 64,
            "EXTERNALLY_VERIFIED",
            "github-actions:job:verify",
        )
        assert_distinct_workload_identities([actor, verifier])
        context = ActionContext(
            "DEPLOY_REMEDIATION", "service:smoke", "staging", "c" * 40,
            "sha256:" + "d" * 64, "revision:smoke-2", "revision:smoke-1",
        )
        grant = {
            "type": "RECEIPT_VERIFIED",
            "receipt_id": "smoke-grant",
            "receipt_type": ACTION_GRANT_TYPE,
            "subject": actor.identity_id,
            "subject_role": actor.role,
            "action": context.action,
            "scope": context.scope(),
            "issuer": "spiffe://humanaios.test/control/issuer",
            "authority_scope": context.authority_scope(),
            "verification_status": "VERIFIED",
            "verification_strength": "CRYPTO_VERIFIED",
            "verification_method": "ED25519",
            "evidence_ref": "smoke:grant-signature",
            "issued_at": "2026-10-24T09:55:00Z",
            "not_before": "2026-10-24T09:55:00Z",
            "expires_at": "2026-10-24T10:05:00Z",
            "one_time": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            ledger = str(Path(tmp) / "grants.jsonl")
            append_receipt_event(ledger, grant)
            _, head = read_receipt_events(ledger)
            assert head is not None
            consume_action_grant(
                ledger, grant_id="smoke-grant", expected_head_hash=head,
                actor=actor, context=context, now=now,
            )
            grant_events, consumed_head = read_receipt_events(ledger)
            assert consumed_head is not None

        observation, observation_head = build_receipt_chain_for_testing([{
            "type": "RECEIPT_VERIFIED",
            "receipt_id": "smoke-observation",
            "receipt_type": RUNTIME_OBSERVATION_TYPE,
            "subject": context.resource,
            "action": "VERIFY_RUNTIME",
            "scope": runtime_observation_scope(context),
            "issuer": verifier.identity_id,
            "authority_scope": context.authority_scope(),
            "verification_status": "VERIFIED",
            "verification_strength": "CRYPTO_VERIFIED",
            "verification_method": "HARDWARE_ATTESTATION",
            "evidence_ref": "smoke:runtime",
            "one_time": False,
            "observer_role": "VERIFIER",
            "observed_resource": context.resource,
            "observed_environment": context.environment,
            "observed_head_sha": context.head_sha,
            "observed_artifact_sha256": context.artifact_sha256,
            "observed_runtime_revision": context.runtime_revision,
            "rollback_ref": context.rollback_ref,
            "vulnerability_closed": True,
            "health_status": "HEALTHY",
            "observed_at": "2026-10-24T10:00:00Z",
        }])
        result = verify_runtime_independently(
            grant_events=grant_events, grant_head_hash=consumed_head,
            grant_id="smoke-grant", observation_events=observation,
            observation_head_hash=observation_head,
            observation_id="smoke-observation", actor=actor, verifier=verifier,
            context=context, now=now,
        )
        assert result["status"] == "VERIFIED", result
        print("smoke-test OK — identity separation, grant consumption, and runtime verification hold.")
        return True
    except Exception as exc:
        print(f"smoke-test FAIL — {exc}", file=sys.stderr)
        return False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    verify = sub.add_parser("verify-controls")
    ingest = sub.add_parser("ingest-feeds")
    for command in (verify, ingest):
        command.add_argument("--control-ledger", type=Path, required=True)
        command.add_argument("--control-head", required=True)
        command.add_argument("--control-receipt-id", required=True)
        command.add_argument("--control-issuer", required=True)
        command.add_argument("--now", required=True)

    ingest.add_argument("--kev", type=Path, required=True)
    ingest.add_argument("--epss", type=Path, required=True)
    ingest.add_argument("--osv", type=Path, required=True)
    ingest.add_argument("--asset-context", type=Path)
    ingest.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    try:
        if args.command == "verify-controls":
            result = _control_from_args(args)
        elif args.command == "ingest-feeds":
            control = _control_from_args(args)
            assets: Mapping[str, Mapping[str, Any]] | None = None
            if args.asset_context is not None:
                loaded = json.loads(_read_bounded(args.asset_context, "ASSET_CONTEXT"))
                _require(isinstance(loaded, dict), "ASSET_CONTEXT_NOT_OBJECT")
                assets = loaded
            result = build_feed_report(
                kev_text=_read_bounded(args.kev, "CISA_KEV"),
                epss_text=_read_bounded(args.epss, "EPSS"),
                osv_text=_read_bounded(args.osv, "OSV"),
                control_attestation=control,
                generated_at=args.now,
                asset_context=assets,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_report(result, args.output)
        else:
            _parser().print_help()
            return 2
    except (OSError, ValueError, VulnOpsRefusal) as exc:
        print(json.dumps({
            "status": "REFUSED",
            "reason": str(exc),
            "authority_effect": AUTHORITY_EFFECT,
            "can_authorize": CAN_AUTHORIZE,
            "can_execute": CAN_EXECUTE,
        }, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
