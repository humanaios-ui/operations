"""Bounded, read-only Privacy Footprint Mine analysis kernel.

The kernel inspects caller-supplied text in memory. It makes no network calls,
writes no files, emits no raw detected values, and exposes no action executor.
An OAG-style grant authorizes exactly one RQY-style query; the result carries a
privacy-minimized QRC-style receipt with authority effect ``NONE``.

This first slice detects explicit email addresses, phone numbers, and IP
addresses. It can report an exact-identifier linkage candidate across supplied
sources. It does not perform attribute inference, claim that a provider knows a
fact, or establish common ownership or identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import hmac
import ipaddress
import json
import re
from typing import Any, Callable, Iterable

__all__ = [
    "AuditDenied",
    "EvidenceLocator",
    "PrivacyAuditGrant",
    "PrivacyAuditQuery",
    "PrivacyAuditReceipt",
    "PrivacyAuditResult",
    "PrivacyFinding",
    "PrivacySource",
    "build_privacy_requirements",
    "review_privacy_finding",
    "run_privacy_footprint_audit",
]


class AuditDenied(ValueError):
    """The requested audit cannot cross the consent or privacy boundary."""


SUPPORTED_OPERATIONS = {"EXPLICIT_PII_SCAN", "EXACT_IDENTIFIER_LINKAGE"}
SOURCE_KINDS = {
    "AI_CHAT_EXPORT",
    "PUBLIC_PROFILE_SNAPSHOT",
    "USER_SUPPLIED_ACTIVITY_LOG",
}
USER_DISPOSITIONS = {"UNSET", "ACCEPT_RISK", "SEEK_REPAIR"}

MAX_SOURCES = 20
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024

_IDENTIFIER = re.compile(r"^(?:OAG|RQY|SRC|SUBJ)-[A-F0-9]{16}$")
_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/-]{2,199}$")
_PROVIDER = re.compile(r"^[A-Z][A-Z0-9_-]{1,63}$")
_EMAIL = re.compile(
    r"(?<![A-Z0-9.!#$%&'*+/=?^_`{|}~-])"
    r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
    r"(?![\w-])",
    re.IGNORECASE,
)
_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}(?!\d)"
)
_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?!\w)")

_REQUIREMENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "EMAIL_ADDRESS": {
        "requirement_id": "RR-PRIVACY-EMAIL-CONTROL-001",
        "label": "Email exposure control",
        "objective": (
            "Find privacy tools or account controls that can minimize, redact, "
            "or compartmentalize an exposed email identifier."
        ),
        "affordances": ["data_minimization", "redaction", "identifier_compartmentalization"],
        "signals": ["privacy", "email", "redaction", "alias", "compartmentalization"],
    },
    "PHONE_NUMBER": {
        "requirement_id": "RR-PRIVACY-PHONE-CONTROL-001",
        "label": "Phone exposure control",
        "objective": (
            "Find privacy tools or account controls that can minimize, redact, "
            "or compartmentalize an exposed phone identifier."
        ),
        "affordances": ["data_minimization", "redaction", "profile_visibility_control"],
        "signals": ["privacy", "phone", "redaction", "visibility", "compartmentalization"],
    },
    "IP_ADDRESS": {
        "requirement_id": "RR-PRIVACY-NETWORK-CONTROL-001",
        "label": "Network identifier exposure control",
        "objective": (
            "Find privacy tools or local controls that can minimize disclosure "
            "of an observed network identifier."
        ),
        "affordances": ["data_minimization", "redaction", "local_processing"],
        "signals": ["privacy", "network", "ip address", "redaction", "local processing"],
    },
    "CROSS_SOURCE_LINKAGE": {
        "requirement_id": "RR-PRIVACY-LINKAGE-CONTROL-001",
        "label": "Cross-source linkage control",
        "objective": (
            "Find privacy tools or account controls that can reduce exact-identifier "
            "linkage across user-selected sources."
        ),
        "affordances": ["identifier_compartmentalization", "data_minimization"],
        "signals": ["privacy", "linkage", "alias", "account separation", "compartmentalization"],
    },
}


@dataclass(frozen=True)
class PrivacyAuditGrant:
    grant_id: str
    query_id: str
    subject_ref: str
    purpose: str
    allowed_source_ids: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    issued_at: str
    expires_at: str
    human_authorization_ref: str
    revoked_at: str | None = None
    authority_effect: str = "NONE"


@dataclass(frozen=True)
class PrivacyAuditQuery:
    query_id: str
    grant_id: str
    source_ids: tuple[str, ...]
    operations: tuple[str, ...]
    requested_at: str


@dataclass(frozen=True)
class PrivacySource:
    source_id: str
    source_kind: str
    provider_id: str
    observed_at: str
    content: str = field(repr=False)


@dataclass(frozen=True)
class EvidenceLocator:
    source_id: str
    line: int
    column: int
    span_length: int
    content_commitment: str


@dataclass(frozen=True)
class PrivacyFinding:
    finding_id: str
    finding_type: str
    state: str
    basis_type: str
    value_commitment: str
    evidence: tuple[EvidenceLocator, ...]
    source_ids: tuple[str, ...]
    occurrence_count: int
    source_count: int
    confidence: float | None
    confidence_state: str
    confidence_meaning: str
    claim_text: str
    user_validation: str = "UNREVIEWED"
    user_disposition: str = "UNSET"
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = list(data["evidence"])
        data["source_ids"] = list(data["source_ids"])
        return data


@dataclass(frozen=True)
class PrivacyAuditReceipt:
    schema: str
    receipt_id: str
    grant_id: str
    query_id: str
    state: str
    observed_at: str
    source_commitments: dict[str, str]
    finding_count: int
    requirement_count: int
    output_sha256: str
    receipt_kind: str = "UNSIGNED_LOCAL_COMMITMENT_NOT_AN_ATTESTATION"
    authorization_ref_state: str = "CALLER_SUPPLIED_NOT_CRYPTOGRAPHICALLY_VERIFIED"
    raw_content_retained: bool = False
    raw_values_emitted: bool = False
    network_access: str = "NONE"
    authority_effect: str = "NONE"
    execution: str = "DISABLED"
    limits: tuple[str, ...] = (
        "Explicit pattern detection only; attribute inference is not implemented.",
        "A match does not establish provider knowledge, ownership, or identity.",
        "ZERO_MATCHES_OBSERVED does not establish that no exposure exists.",
        "No spent-grant ledger is present; replay prevention is not established.",
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["limits"] = list(data["limits"])
        return data


@dataclass(frozen=True)
class PrivacyAuditResult:
    schema: str
    query_id: str
    state: str
    findings: tuple[PrivacyFinding, ...]
    resource_requirements: tuple[dict[str, Any], ...]
    receipt: PrivacyAuditReceipt
    authority_effect: str = "NONE"
    execution: str = "DISABLED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "query_id": self.query_id,
            "state": self.state,
            "findings": [finding.to_dict() for finding in self.findings],
            "resource_requirements": list(self.resource_requirements),
            "receipt": self.receipt.to_dict(),
            "authority_effect": self.authority_effect,
            "execution": self.execution,
        }


@dataclass(frozen=True)
class _DetectedValue:
    finding_type: str
    normalized_value: str = field(repr=False)
    locator: EvidenceLocator


def _parse_instant(value: str, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AuditDenied(f"{label} must be a timezone-aware RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuditDenied(f"{label} must be a timezone-aware RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise AuditDenied(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _require_identifier(value: str, prefix: str, label: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value) or not value.startswith(prefix + "-"):
        raise AuditDenied(f"{label} must be a privacy-safe {prefix} identifier")


def _require_unique(values: Iterable[str], label: str) -> tuple[str, ...]:
    rows = tuple(values)
    if not rows or len(rows) != len(set(rows)):
        raise AuditDenied(f"{label} must be non-empty and unique")
    return rows


def _key_bytes(value: bytes | bytearray) -> bytes:
    if not isinstance(value, (bytes, bytearray)) or len(value) < 32:
        raise AuditDenied("pseudonymization_key must contain at least 32 bytes")
    return bytes(value)


def _commit(key: bytes, *parts: str) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def _line_and_column(content: str, offset: int) -> tuple[int, int]:
    line = content.count("\n", 0, offset) + 1
    previous_break = content.rfind("\n", 0, offset)
    return line, offset - previous_break


def _locator(source: PrivacySource, match: re.Match[str], content_commitment: str) -> EvidenceLocator:
    line, column = _line_and_column(source.content, match.start())
    return EvidenceLocator(
        source_id=source.source_id,
        line=line,
        column=column,
        span_length=match.end() - match.start(),
        content_commitment=content_commitment,
    )


def _normalized_phone(value: str) -> str | None:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else None


def _detect(source: PrivacySource, content_commitment: str) -> list[_DetectedValue]:
    out: list[_DetectedValue] = []
    for match in _EMAIL.finditer(source.content):
        out.append(
            _DetectedValue(
                "EMAIL_ADDRESS",
                match.group(0).casefold(),
                _locator(source, match, content_commitment),
            )
        )
    for match in _PHONE.finditer(source.content):
        normalized = _normalized_phone(match.group(0))
        if normalized:
            out.append(
                _DetectedValue(
                    "PHONE_NUMBER",
                    normalized,
                    _locator(source, match, content_commitment),
                )
            )
    for match in _IPV4.finditer(source.content):
        try:
            normalized = str(ipaddress.ip_address(match.group(0)))
        except ValueError:
            continue
        out.append(
            _DetectedValue(
                "IP_ADDRESS",
                normalized,
                _locator(source, match, content_commitment),
            )
        )
    return out


def _finding_id(state: str, basis_type: str, commitment: str) -> str:
    payload = "\0".join((state, basis_type, commitment))
    return "PFF-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def _execution_instant(clock: Callable[[], datetime] | None) -> datetime:
    executed_at = datetime.now(timezone.utc) if clock is None else clock()
    if not isinstance(executed_at, datetime) or executed_at.tzinfo is None:
        raise AuditDenied("trusted execution clock must return a timezone-aware datetime")
    return executed_at.astimezone(timezone.utc)


def _validate_boundary(
    grant: PrivacyAuditGrant,
    query: PrivacyAuditQuery,
    executed_at: datetime,
) -> None:
    _require_identifier(grant.grant_id, "OAG", "grant_id")
    _require_identifier(grant.query_id, "RQY", "grant query_id")
    _require_identifier(grant.subject_ref, "SUBJ", "subject_ref")
    _require_identifier(query.query_id, "RQY", "query_id")
    if query.grant_id != grant.grant_id:
        raise AuditDenied("query is not bound to the supplied grant")
    if query.query_id != grant.query_id:
        raise AuditDenied("grant is bound to a different query_id")
    if grant.purpose != "PERSONAL_PRIVACY_AUDIT":
        raise AuditDenied("grant purpose is outside the personal privacy audit boundary")
    if grant.authority_effect != "NONE":
        raise AuditDenied("privacy audit grants cannot create authority")
    if not _REFERENCE.fullmatch(grant.human_authorization_ref or ""):
        raise AuditDenied("human authorization receipt reference is required")

    allowed_sources = _require_unique(grant.allowed_source_ids, "allowed_source_ids")
    requested_sources = _require_unique(query.source_ids, "query source_ids")
    for source_id in (*allowed_sources, *requested_sources):
        _require_identifier(source_id, "SRC", "source_id")
    if not set(requested_sources).issubset(allowed_sources):
        raise AuditDenied("query includes a source outside the grant")

    allowed_operations = _require_unique(grant.allowed_operations, "allowed_operations")
    requested_operations = _require_unique(query.operations, "query operations")
    if not set(allowed_operations).issubset(SUPPORTED_OPERATIONS):
        raise AuditDenied("grant includes an unsupported operation")
    if not set(requested_operations).issubset(allowed_operations):
        raise AuditDenied("query includes an operation outside the grant")
    if not set(requested_operations).issubset(SUPPORTED_OPERATIONS):
        raise AuditDenied("query includes an unsupported operation")
    if "EXACT_IDENTIFIER_LINKAGE" in requested_operations and "EXPLICIT_PII_SCAN" not in requested_operations:
        raise AuditDenied("exact linkage requires the bounded explicit PII scan")

    issued = _parse_instant(grant.issued_at, "issued_at")
    expires = _parse_instant(grant.expires_at, "expires_at")
    requested = _parse_instant(query.requested_at, "requested_at")
    if expires <= issued:
        raise AuditDenied("grant expiration must follow issuance")
    if requested < issued or requested >= expires:
        raise AuditDenied("query falls outside the grant time window")
    if executed_at < issued or executed_at >= expires:
        raise AuditDenied("grant is not active at trusted execution time")
    if requested > executed_at:
        raise AuditDenied("query request time cannot postdate trusted execution time")
    if grant.revoked_at is not None:
        revoked = _parse_instant(grant.revoked_at, "revoked_at")
        if revoked < issued:
            raise AuditDenied("grant revocation cannot predate issuance")
        if revoked <= requested or revoked <= executed_at:
            raise AuditDenied("grant was revoked before query execution")


def _validate_sources(query: PrivacyAuditQuery, sources: Iterable[PrivacySource]) -> tuple[PrivacySource, ...]:
    rows = tuple(sources)
    if not rows or len(rows) > MAX_SOURCES:
        raise AuditDenied(f"audit requires 1 to {MAX_SOURCES} supplied sources")
    ids = tuple(source.source_id for source in rows)
    if len(ids) != len(set(ids)) or set(ids) != set(query.source_ids):
        raise AuditDenied("supplied sources must exactly match unique query source_ids")

    requested = _parse_instant(query.requested_at, "requested_at")
    total_bytes = 0
    for source in rows:
        _require_identifier(source.source_id, "SRC", "source_id")
        if source.source_kind not in SOURCE_KINDS:
            raise AuditDenied("unsupported source kind")
        if not _PROVIDER.fullmatch(source.provider_id or ""):
            raise AuditDenied("provider_id must be a bounded non-personal label")
        if not isinstance(source.content, str):
            raise AuditDenied("source content must be text")
        observed = _parse_instant(source.observed_at, "source observed_at")
        if observed > requested:
            raise AuditDenied("source observation cannot postdate the query")
        source_bytes = len(source.content.encode("utf-8"))
        if source_bytes > MAX_SOURCE_BYTES:
            raise AuditDenied("source exceeds the bounded in-memory size limit")
        total_bytes += source_bytes
    if total_bytes > MAX_TOTAL_BYTES:
        raise AuditDenied("combined sources exceed the bounded in-memory size limit")
    return rows


def review_privacy_finding(
    finding: PrivacyFinding,
    *,
    validation: str,
    disposition: str = "UNSET",
) -> PrivacyFinding:
    """Apply a user review without authorizing or executing a repair."""
    validation = validation.upper()
    disposition = disposition.upper()
    if validation not in {"CONFIRMED", "DENIED"}:
        raise ValueError("validation must be CONFIRMED or DENIED")
    if disposition not in USER_DISPOSITIONS:
        raise ValueError("unsupported user disposition")
    if validation == "DENIED" and disposition != "UNSET":
        raise ValueError("a denied finding cannot request or accept a repair")
    return replace(
        finding,
        state="USER_CONFIRMED" if validation == "CONFIRMED" else "USER_DENIED",
        user_validation=validation,
        user_disposition=disposition,
    )


def build_privacy_requirements(findings: Iterable[PrivacyFinding]) -> list[dict[str, Any]]:
    """Project findings into Resource Miner requirements without creating work."""
    grouped: dict[str, list[PrivacyFinding]] = {}
    for finding in findings:
        if finding.user_validation == "DENIED" or finding.state in {
            "USER_DENIED",
            "CONTRADICTED",
            "REVOKED",
        }:
            continue
        key = "CROSS_SOURCE_LINKAGE" if finding.finding_type == "CROSS_SOURCE_LINKAGE" else finding.finding_type
        if key in _REQUIREMENT_TEMPLATES:
            grouped.setdefault(key, []).append(finding)

    requirements: list[dict[str, Any]] = []
    for key in sorted(grouped):
        related = grouped[key]
        template = _REQUIREMENT_TEMPLATES[key]
        if any(
            item.user_validation == "CONFIRMED" and item.user_disposition == "SEEK_REPAIR"
            for item in related
        ):
            gap_status = "CONFIRMED"
        elif related and all(item.user_disposition == "ACCEPT_RISK" for item in related):
            gap_status = "INACTIVE"
        else:
            gap_status = "CONDITIONAL"
        requirements.append(
            {
                "requirement_id": template["requirement_id"],
                "gap_status": gap_status,
                "label": template["label"],
                "objective": template["objective"],
                "resource_types": ["privacy_tool"],
                "affordances": list(template["affordances"]),
                "signals": list(template["signals"]),
                "activation_condition": (
                    "The user confirms the observation and explicitly chooses SEEK_REPAIR."
                ),
                "satisfied_when": (
                    "A user-selected control is applied through a separate authorized path "
                    "and a later bounded audit observes the intended change."
                ),
                "source_finding_ids": sorted(item.finding_id for item in related),
                "authority_effect": "NONE",
            }
        )
    return requirements


def run_privacy_footprint_audit(
    grant: PrivacyAuditGrant,
    query: PrivacyAuditQuery,
    sources: Iterable[PrivacySource],
    *,
    pseudonymization_key: bytes | bytearray,
    clock: Callable[[], datetime] | None = None,
) -> PrivacyAuditResult:
    """Run one consent-bound, in-memory, non-executing privacy audit.

    ``clock`` is an injectable trusted-host clock for deterministic tests. The
    CLI does not expose it to request payloads.
    """
    executed_at = _execution_instant(clock)
    _validate_boundary(grant, query, executed_at)
    source_rows = _validate_sources(query, sources)
    key = _key_bytes(pseudonymization_key)

    source_commitments: dict[str, str] = {}
    detected: list[_DetectedValue] = []
    for source in source_rows:
        content_commitment = "hmac-sha256:" + _commit(
            key, "source", source.source_id, source.content
        )
        source_commitments[source.source_id] = content_commitment
        detected.extend(_detect(source, content_commitment))

    linkage_enabled = "EXACT_IDENTIFIER_LINKAGE" in query.operations
    grouped: dict[tuple[str, str], list[_DetectedValue]] = {}
    for item in detected:
        commitment_parts = ["value", item.finding_type, item.normalized_value]
        if not linkage_enabled:
            # Explicit scanning alone must not create a cross-source join key.
            commitment_parts.append(item.locator.source_id)
        value_commitment = "hmac-sha256:" + _commit(
            key, *commitment_parts
        )
        grouped.setdefault((item.finding_type, value_commitment), []).append(item)

    findings: list[PrivacyFinding] = []
    for (finding_type, value_commitment), occurrences in sorted(grouped.items()):
        evidence = tuple(
            sorted(
                (item.locator for item in occurrences),
                key=lambda row: (row.source_id, row.line, row.column, row.span_length),
            )
        )
        source_ids = tuple(sorted({row.source_id for row in evidence}))
        findings.append(
            PrivacyFinding(
                finding_id=_finding_id("OBSERVED", finding_type, value_commitment),
                finding_type=finding_type,
                state="OBSERVED",
                basis_type=finding_type,
                value_commitment=value_commitment,
                evidence=evidence,
                source_ids=source_ids,
                occurrence_count=len(occurrences),
                source_count=len(source_ids),
                confidence=None,
                confidence_state="NOT_CALIBRATED",
                confidence_meaning=(
                    "No calibrated probability is assigned. The record reports only a "
                    "bounded pattern match, not identity, harm, provider knowledge, or ownership."
                ),
                claim_text=(
                    f"The bounded detector observed a value matching {finding_type} "
                    "in user-supplied data. Provider knowledge and ownership are not established."
                ),
            )
        )
        if linkage_enabled and len(source_ids) >= 2:
            findings.append(
                PrivacyFinding(
                    finding_id=_finding_id("LINKAGE_CANDIDATE", finding_type, value_commitment),
                    finding_type="CROSS_SOURCE_LINKAGE",
                    state="LINKAGE_CANDIDATE",
                    basis_type=finding_type,
                    value_commitment=value_commitment,
                    evidence=evidence,
                    source_ids=source_ids,
                    occurrence_count=len(occurrences),
                    source_count=len(source_ids),
                    confidence=None,
                    confidence_state="NOT_CALIBRATED",
                    confidence_meaning=(
                        "No calibrated probability is assigned. Exact normalized-token "
                        "recurrence is bounded to this run and does not establish identity."
                    ),
                    claim_text=(
                        f"The same normalized {finding_type} token was observed in two or "
                        "more user-supplied sources. Common ownership and identity are not established."
                    ),
                )
            )

    findings.sort(key=lambda row: (row.finding_type, row.finding_id))
    requirements = build_privacy_requirements(findings)
    state = "FINDINGS_FOR_HUMAN_REVIEW" if findings else "ZERO_MATCHES_OBSERVED"
    payload_for_digest = {
        "schema": "humanaios.privacy-footprint-audit.v0.1",
        "query_id": query.query_id,
        "observed_at": executed_at.isoformat(),
        "state": state,
        "findings": [finding.to_dict() for finding in findings],
        "resource_requirements": requirements,
        "source_commitments": source_commitments,
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }
    output_sha256 = hashlib.sha256(
        json.dumps(payload_for_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt_id = "QRC-" + hashlib.sha256(
        (query.query_id + "\0" + output_sha256).encode("utf-8")
    ).hexdigest()[:16].upper()
    receipt = PrivacyAuditReceipt(
        schema="humanaios.privacy-footprint-query-receipt.v0.1",
        receipt_id=receipt_id,
        grant_id=grant.grant_id,
        query_id=query.query_id,
        state=state,
        observed_at=executed_at.isoformat(),
        source_commitments=source_commitments,
        finding_count=len(findings),
        requirement_count=len(requirements),
        output_sha256=output_sha256,
    )
    return PrivacyAuditResult(
        schema="humanaios.privacy-footprint-audit.v0.1",
        query_id=query.query_id,
        state=state,
        findings=tuple(findings),
        resource_requirements=tuple(requirements),
        receipt=receipt,
    )
