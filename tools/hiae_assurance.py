#!/usr/bin/env python3
"""
HIAE-001 assurance transaction core — v0.1 (proposal stage)
Builder v1.7 compliant · validation_tool
HumanAIOS · Q-HIAE-001 · Z1 proposal, NOT ratified (awaiting Z2)

Three pieces, stdlib only:
  1. select_reviewer(): neutral, rotation-based reviewer assignment with
     conflict-of-interest exclusion. The customer cannot name a reviewer.
  2. check_assignment(): recomputes an assignment from a rotation seed that
     the caller supplies from a trusted record, and reports any divergence
     (substituted reviewer, conflicted reviewer, substituted seed).
  3. issue_receipt() / verify_receipt(): versioned assessment receipt that
     pins protocol, ACAT, model and commit versions; carries a signature from
     the assigned reviewer; binds each observer-signed evidence item to its
     request, subject, protocol and observation time; and rejects overclaiming
     wording and unsupported receipt versions.

Limitations (stated, not hidden):
  - Signatures are HMAC-SHA256 with shared keys. This is a stand-in for an
    asymmetric scheme (e.g. Ed25519 or a W3C VC proof). A verifier here must
    hold each signer's key, so this is not public verifiability.
  - Hash chaining is not used as proof of authorship; authorship rests on the
    observer, reviewer and issuer signatures only.
  - Nothing here establishes that a receipt's measurements are true.

Usage:
  python3 tools/hiae_assurance.py --smoke-test [--report-dir DIR]
  python3 tools/hiae_assurance.py --help
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import argparse
import hashlib
import hmac
import json
import re
import sys


TOOL_NAME = "hiae_assurance"
TOOL_VERSION = "0.1.0"
RECEIPT_VERSION = "1.0.0"

# A customer may not name a reviewer by any of these request fields.
CUSTOMER_REVIEWER_KEYS = frozenset({
    "reviewer",
    "reviewer_id",
    "preferred_reviewer",
    "reviewer_preference",
    "select_reviewer",
})

# Overclaiming vocabulary (seed-constitution principle 5). Receipts must not
# say the subject is certified, safe, compliant or accredited.
FORBIDDEN_CLAIM_RE = re.compile(
    r"\b(certified|certification|safe|compliant|compliance|accredited|accreditation)\b",
    re.IGNORECASE,
)

REQUIRED_RECEIPT_FIELDS = frozenset({
    "receipt_version",
    "request_id",
    "reviewer_id",
    "subject_id",
    "protocol_id",
    "protocol_version",
    "acat_version",
    "model_id",
    "model_version",
    "commit_sha",
    "measured",
    "not_measured",
    "findings",
    "evidence",
    "issued_at",
    "issuer_id",
})

# Fields the evidence context must agree with on the receipt.
EVIDENCE_CONTEXT_FIELDS = ("request_id", "subject_id", "protocol_id", "protocol_version")


class AssignmentError(ValueError):
    """Raised when no valid assignment exists or the request is malformed."""


class ReceiptError(ValueError):
    """Raised when a receipt body cannot be issued."""


class SpecLoadFailed(RuntimeError):
    """Raised when a report output location cannot be used."""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def canonical_bytes(obj: Any) -> bytes:
    """Deterministic JSON encoding used for every signed payload."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_payload(key: bytes, payload: Any) -> str:
    return hmac.new(key, canonical_bytes(payload), hashlib.sha256).hexdigest()


def _signature_ok(key: Optional[bytes], payload: Any, value: Any) -> bool:
    if key is None:
        return False
    return hmac.compare_digest(sign_payload(key, payload), str(value or ""))


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings(v)


def overclaim_hits(value: Any) -> List[str]:
    """Return every forbidden claim word found in any string under value."""
    hits: List[str] = []
    for text in _strings(value):
        hits.extend(m.group(0).lower() for m in FORBIDDEN_CLAIM_RE.finditer(text))
    return sorted(set(hits))


# ---------------------------------------------------------------------------
# 1. Neutral reviewer assignment
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Reviewer:
    reviewer_id: str
    org: str
    risk_classes: frozenset
    declared_conflicts: frozenset = frozenset()
    active: bool = True
    credential_valid: bool = True


@dataclass(frozen=True)
class AssessmentRequest:
    request_id: str
    customer_id: str
    customer_org: str
    risk_class: str
    subject_id: str
    fields: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HistoryEntry:
    """One prior assignment. History drives load-balancing and prior-involvement checks."""
    request_id: str
    reviewer_id: str
    subject_id: str


@dataclass(frozen=True)
class Assignment:
    request_id: str
    subject_id: str
    reviewer_id: str
    rotation_seed: str
    eligible_ids: Tuple[str, ...]
    pool_ids: Tuple[str, ...]
    selection_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def ineligibility_reasons(
    reviewer: Reviewer, request: AssessmentRequest, history: Iterable[HistoryEntry]
) -> List[str]:
    """Return why a reviewer cannot take this request. Empty list means eligible."""
    reasons: List[str] = []
    if not reviewer.active:
        reasons.append("inactive")
    if not reviewer.credential_valid:
        reasons.append("credential_invalid")
    if request.risk_class not in reviewer.risk_classes:
        reasons.append("not_qualified_for_risk_class")
    if reviewer.org == request.customer_org:
        reasons.append("same_org_as_customer")
    if request.customer_id in reviewer.declared_conflicts or request.customer_org in reviewer.declared_conflicts:
        reasons.append("declared_conflict")
    if any(h.reviewer_id == reviewer.reviewer_id and h.subject_id == request.subject_id for h in history):
        reasons.append("prior_involvement_with_subject")
    return reasons


def select_reviewer(
    request: AssessmentRequest,
    reviewers: Iterable[Reviewer],
    history: Iterable[HistoryEntry],
    rotation_seed: str,
) -> Assignment:
    """
    Choose a reviewer by rotation, with no customer influence.

    Rule: among eligible reviewers, take those with the fewest prior
    assignments (rotation), then break ties with sha256(seed | request_id).
    The result is reproducible from (request, reviewers, history, seed).
    The seed must come from a trusted rotation record, not from the customer.
    """
    supplied = CUSTOMER_REVIEWER_KEYS.intersection(request.fields)
    if supplied:
        raise AssignmentError(f"customer-supplied reviewer fields rejected: {sorted(supplied)}")
    if not rotation_seed:
        raise AssignmentError("rotation_seed is required")

    history = list(history)
    eligible = [
        r for r in sorted(reviewers, key=lambda r: r.reviewer_id)
        if not ineligibility_reasons(r, request, history)
    ]
    if not eligible:
        raise AssignmentError("no eligible conflict-free reviewer")

    load = Counter(h.reviewer_id for h in history)
    min_load = min(load[r.reviewer_id] for r in eligible)
    pool = [r for r in eligible if load[r.reviewer_id] == min_load]

    digest = hashlib.sha256(f"{rotation_seed}|{request.request_id}".encode("utf-8")).hexdigest()
    chosen = pool[int(digest, 16) % len(pool)]

    return Assignment(
        request_id=request.request_id,
        subject_id=request.subject_id,
        reviewer_id=chosen.reviewer_id,
        rotation_seed=rotation_seed,
        eligible_ids=tuple(r.reviewer_id for r in eligible),
        pool_ids=tuple(r.reviewer_id for r in pool),
        selection_digest=digest,
    )


def check_assignment(
    assignment: Assignment,
    request: AssessmentRequest,
    reviewers: Iterable[Reviewer],
    history: Iterable[HistoryEntry],
    trusted_seed: str,
) -> List[str]:
    """
    Recompute the assignment from trusted_seed and return every divergence.

    trusted_seed is supplied by the caller from a trusted rotation record. The
    seed recorded on the assignment is compared against it and is not used as
    the basis for recomputation, so an assignment cannot vouch for its own seed.
    Empty list means valid.
    """
    if assignment.request_id != request.request_id or assignment.subject_id != request.subject_id:
        return ["assignment does not match request"]
    problems: List[str] = []
    if assignment.rotation_seed != trusted_seed:
        problems.append("recorded rotation seed does not match the trusted rotation record")
    try:
        expected = select_reviewer(request, reviewers, history, trusted_seed)
    except AssignmentError as exc:
        return problems + [f"recomputation failed: {exc}"]

    if assignment.reviewer_id != expected.reviewer_id:
        problems.append(
            f"reviewer {assignment.reviewer_id!r} is not the assigned reviewer {expected.reviewer_id!r}"
        )
    if assignment.reviewer_id not in expected.eligible_ids:
        problems.append(f"reviewer {assignment.reviewer_id!r} is not eligible (conflict or qualification)")
    if assignment.eligible_ids != expected.eligible_ids or assignment.pool_ids != expected.pool_ids:
        problems.append("recorded eligibility set does not match recomputation")
    return problems


# ---------------------------------------------------------------------------
# 2. Evidence authentication and versioned receipts
# ---------------------------------------------------------------------------

def make_evidence(
    evidence_id: str,
    observer_id: str,
    observer_key: bytes,
    content: bytes,
    context: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Create an observer-signed evidence item.

    The content is hashed, not embedded. The context (request, subject,
    protocol and observation time) is inside the signed payload, so the item
    cannot be replayed into a receipt for a different request or protocol.
    """
    missing = {"request_id", "subject_id", "protocol_id", "protocol_version", "observed_at"}.difference(context)
    if missing:
        raise ReceiptError(f"evidence context missing: {sorted(missing)}")
    item = {
        "evidence_id": evidence_id,
        "observer_id": observer_id,
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "context": dict(context),
    }
    item["observer_signature"] = sign_payload(observer_key, item)
    return item


def issue_receipt(
    body: Mapping[str, Any],
    issuer_id: str,
    issuer_key: bytes,
    reviewer_key: bytes,
) -> Dict[str, Any]:
    """
    Sign a receipt body.

    The reviewer signs first, over the body. The issuer then signs the body
    including the reviewer signature. Refuses overclaiming wording and missing
    fields. Any signature fields already present in body are discarded.
    """
    clean = {k: v for k, v in body.items() if k not in ("signature", "reviewer_signature")}
    receipt = {**clean, "receipt_version": RECEIPT_VERSION}
    missing = REQUIRED_RECEIPT_FIELDS.difference(receipt)
    if missing:
        raise ReceiptError(f"missing receipt fields: {sorted(missing)}")
    if receipt["issuer_id"] != issuer_id:
        raise ReceiptError("issuer_id does not match signing issuer")
    hits = overclaim_hits({k: receipt[k] for k in ("measured", "not_measured", "findings")})
    if hits:
        raise ReceiptError(f"overclaiming wording rejected: {hits}")

    receipt["reviewer_signature"] = {
        "reviewer_id": receipt["reviewer_id"],
        "alg": "HMAC-SHA256",
        "value": sign_payload(reviewer_key, receipt),
    }
    receipt["signature"] = {
        "issuer_id": issuer_id,
        "alg": "HMAC-SHA256",
        "value": sign_payload(issuer_key, receipt),
    }
    return receipt


def verify_receipt(
    receipt: Mapping[str, Any],
    assignment: Assignment,
    issuer_keys: Mapping[str, bytes],
    observer_keys: Mapping[str, bytes],
    reviewer_keys: Mapping[str, bytes],
) -> List[str]:
    """Return every problem with a receipt. Empty list means it verifies."""
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        return [f"unsupported receipt_version {receipt.get('receipt_version')!r}; this verifier implements {RECEIPT_VERSION}"]

    missing = REQUIRED_RECEIPT_FIELDS.difference(receipt)
    if missing:
        return [f"missing receipt fields: {sorted(missing)}"]

    problems: List[str] = []

    # Issuer signature covers everything except the issuer signature itself.
    sig = receipt.get("signature") or {}
    issuer_body = {k: v for k, v in receipt.items() if k != "signature"}
    if sig.get("issuer_id") not in issuer_keys:
        problems.append("unknown issuer")
    elif not _signature_ok(issuer_keys[sig["issuer_id"]], issuer_body, sig.get("value")):
        problems.append("issuer signature does not verify (receipt altered or wrong key)")

    if receipt["request_id"] != assignment.request_id:
        problems.append("receipt is for a different request")
    if receipt["reviewer_id"] != assignment.reviewer_id:
        problems.append(
            f"receipt reviewer {receipt['reviewer_id']!r} is not the assigned reviewer {assignment.reviewer_id!r}"
        )
    if receipt["subject_id"] != assignment.subject_id:
        problems.append("receipt subject does not match assignment")

    # The assigned reviewer must have signed this exact body.
    rsig = receipt.get("reviewer_signature") or {}
    reviewer_body = {k: v for k, v in receipt.items() if k not in ("signature", "reviewer_signature")}
    if rsig.get("reviewer_id") != assignment.reviewer_id:
        problems.append("reviewer signature is not from the assigned reviewer")
    elif not _signature_ok(reviewer_keys.get(assignment.reviewer_id), reviewer_body, rsig.get("value")):
        problems.append("reviewer signature does not verify for the assigned reviewer")

    hits = overclaim_hits({k: receipt[k] for k in ("measured", "not_measured", "findings")})
    if hits:
        problems.append(f"overclaiming wording: {hits}")

    expected_context = {k: receipt[k] for k in EVIDENCE_CONTEXT_FIELDS}
    for item in receipt["evidence"]:
        label = item.get("evidence_id")
        item_body = {k: v for k, v in item.items() if k != "observer_signature"}
        obs_key = observer_keys.get(item.get("observer_id", ""))
        if obs_key is None:
            problems.append(f"evidence {label!r}: unknown observer")
        elif not _signature_ok(obs_key, item_body, item.get("observer_signature")):
            problems.append(f"evidence {label!r}: observer signature invalid")
        context = item.get("context") or {}
        if any(context.get(k) != v for k, v in expected_context.items()):
            problems.append(f"evidence {label!r} is bound to a different request, subject or protocol")

    return problems


# ---------------------------------------------------------------------------
# Synthetic end-to-end transaction (test fixture, not production keys)
# ---------------------------------------------------------------------------

# Fixture keys are derived from public labels, so no key material is stored in
# source. They are not secrets and must not be used to sign a real receipt.
DEMO_KEYS = {
    name: hashlib.sha256(f"hiae-demo-fixture|{name}".encode("utf-8")).digest()
    for name in (
        "issuer:humanaios-operations",
        "observer:rater-a",
        "observer:rater-b",
        "reviewer:rev-1",
        "reviewer:rev-2",
        "reviewer:rev-3",
        "reviewer:rev-4",
    )
}

DEMO_PROTOCOL = {
    "protocol_id": "HIAE-SYN-PROTO",
    "protocol_version": "0.1.0",
    "acat_version": "v5.5",
    "model_id": "synthetic-model",
    "model_version": "2026-10-10",
    "commit_sha": "0" * 40,
}

DEMO_SEED = "seed-2026-10-10"
DEMO_OBSERVED_AT = "2026-10-10T00:00:00Z"
DEMO_ISSUER = "issuer:humanaios-operations"


def demo_reviewers() -> List[Reviewer]:
    return [
        Reviewer("rev-1", "org-alpha", frozenset({"low", "medium"})),
        Reviewer("rev-2", "org-beta", frozenset({"low", "medium"})),
        Reviewer("rev-3", "org-gamma", frozenset({"low", "medium"}), declared_conflicts=frozenset({"cust-1"})),
        Reviewer("rev-4", "cust-org", frozenset({"low", "medium"})),
    ]


def _observer_keys() -> Dict[str, bytes]:
    """Observer keys keyed by full observer id, as evidence items reference them."""
    return {k: v for k, v in DEMO_KEYS.items() if k.startswith("observer:")}


def _reviewer_keys() -> Dict[str, bytes]:
    """Reviewer keys keyed by reviewer id, as the assignment references them."""
    return {k[len("reviewer:"):]: v for k, v in DEMO_KEYS.items() if k.startswith("reviewer:")}


def _demo_request(request_id: str = "req-0001", subject_id: str = "subject-A") -> AssessmentRequest:
    return AssessmentRequest(
        request_id=request_id,
        customer_id="cust-1",
        customer_org="cust-org-1",
        risk_class="low",
        subject_id=subject_id,
    )


def _demo_evidence(request: AssessmentRequest) -> List[Dict[str, Any]]:
    context = {
        "request_id": request.request_id,
        "subject_id": request.subject_id,
        "protocol_id": DEMO_PROTOCOL["protocol_id"],
        "protocol_version": DEMO_PROTOCOL["protocol_version"],
        "observed_at": DEMO_OBSERVED_AT,
    }
    return [
        make_evidence("ev-1", "observer:rater-a", DEMO_KEYS["observer:rater-a"], b"transcript-1-bytes", context),
        make_evidence("ev-2", "observer:rater-b", DEMO_KEYS["observer:rater-b"], b"transcript-2-bytes", context),
    ]


def _receipt_body(request: AssessmentRequest, assignment: Assignment, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        **DEMO_PROTOCOL,
        "request_id": request.request_id,
        "reviewer_id": assignment.reviewer_id,
        "subject_id": request.subject_id,
        "measured": ["Protocol HIAE-SYN-PROTO v0.1.0 run on two synthetic transcripts"],
        "not_measured": ["No real customer data", "No claim about the subject beyond these transcripts"],
        "findings": ["Two observer-signed evidence items were captured for this synthetic run"],
        "evidence": evidence,
        "issued_at": "2026-10-10T00:00:00Z",
        "issuer_id": DEMO_ISSUER,
    }


def run_synthetic_transaction(
    request: Optional[AssessmentRequest] = None,
    rotation_seed: str = DEMO_SEED,
    history: Iterable[HistoryEntry] = (),
) -> Tuple[Assignment, Dict[str, Any], List[str]]:
    """Run the lifecycle once: assign, evidence, receipt, verify. Returns (assignment, receipt, problems)."""
    request = request or _demo_request()
    history = list(history)
    reviewers = demo_reviewers()
    assignment = select_reviewer(request, reviewers, history, rotation_seed)

    receipt = issue_receipt(
        _receipt_body(request, assignment, _demo_evidence(request)),
        DEMO_ISSUER,
        DEMO_KEYS[DEMO_ISSUER],
        DEMO_KEYS[f"reviewer:{assignment.reviewer_id}"],
    )

    problems = check_assignment(assignment, request, reviewers, history, trusted_seed=rotation_seed)
    problems += verify_receipt(
        receipt,
        assignment,
        issuer_keys={DEMO_ISSUER: DEMO_KEYS[DEMO_ISSUER]},
        observer_keys=_observer_keys(),
        reviewer_keys=_reviewer_keys(),
    )
    return assignment, receipt, problems


def negative_cases() -> Dict[str, bool]:
    """Each case must be rejected. Returns name -> True when rejected as required."""
    results: Dict[str, bool] = {}
    issuer_keys = {DEMO_ISSUER: DEMO_KEYS[DEMO_ISSUER]}
    observer_keys = _observer_keys()
    reviewer_keys = _reviewer_keys()
    reviewers = demo_reviewers()

    def verify(receipt: Mapping[str, Any], assignment: Assignment) -> List[str]:
        return verify_receipt(receipt, assignment, issuer_keys, observer_keys, reviewer_keys)

    # customer names a reviewer
    try:
        select_reviewer(
            AssessmentRequest("req-neg", "cust-1", "cust-org-1", "low", "subject-N", {"preferred_reviewer": "rev-2"}),
            reviewers, [], DEMO_SEED,
        )
        results["customer_selected_reviewer"] = False
    except AssignmentError:
        results["customer_selected_reviewer"] = True

    request, assignment, receipt = _valid_transaction()

    # falsified receipt: finding changed after signing
    tampered = dict(receipt)
    tampered["findings"] = ["Subject passed independent assessment"]
    results["falsified_receipt"] = bool(verify(tampered, assignment))

    # forged evidence: content hash changed after the observer signed
    forged = json.loads(json.dumps(receipt))
    forged["evidence"][0]["content_sha256"] = hashlib.sha256(b"fabricated").hexdigest()
    results["forged_evidence"] = bool(verify(forged, assignment))

    # evidence replayed from another request, re-issued so both signatures are valid
    other_request = _demo_request("req-0002", "subject-A")
    replayed = issue_receipt(
        _receipt_body(request, assignment, _demo_evidence(other_request)),
        DEMO_ISSUER,
        DEMO_KEYS[DEMO_ISSUER],
        DEMO_KEYS[f"reviewer:{assignment.reviewer_id}"],
    )
    results["evidence_replayed_to_other_request"] = bool(verify(replayed, assignment))

    # unauthorized reviewer: receipt names the assigned reviewer but is signed with another key
    forged_reviewer = issue_receipt(
        _receipt_body(request, assignment, _demo_evidence(request)),
        DEMO_ISSUER,
        DEMO_KEYS[DEMO_ISSUER],
        b"attacker-key-not-a-reviewer",
    )
    results["unauthorized_reviewer"] = bool(verify(forged_reviewer, assignment))

    # wrong reviewer named: a valid receipt for a different reviewer than the one assigned
    wrong_name_id = "rev-2" if assignment.reviewer_id != "rev-2" else "rev-1"
    wrong_named = issue_receipt(
        _receipt_body(request, assignment, _demo_evidence(request)) | {"reviewer_id": wrong_name_id},
        DEMO_ISSUER,
        DEMO_KEYS[DEMO_ISSUER],
        DEMO_KEYS[f"reviewer:{wrong_name_id}"],
    )
    results["wrong_reviewer_named"] = bool(verify(wrong_named, assignment))

    # conflicted assignment: forced onto the declared-conflict reviewer
    forced = Assignment(
        request_id=request.request_id,
        subject_id=request.subject_id,
        reviewer_id="rev-3",
        rotation_seed=DEMO_SEED,
        eligible_ids=(),
        pool_ids=(),
        selection_digest="",
    )
    results["conflicted_assignment"] = bool(
        check_assignment(forced, _demo_request("req-neg", "subject-N"), reviewers, [], trusted_seed=DEMO_SEED)
    )

    # substituted rotation seed: assignment records a different seed than the trusted one
    substituted = Assignment(**{**assignment.to_dict(), "rotation_seed": "seed-attacker"})
    results["substituted_rotation_seed"] = bool(check_assignment(substituted, request, reviewers, [], trusted_seed=DEMO_SEED))

    # unsupported receipt version
    future = dict(receipt)
    future["receipt_version"] = "9.0.0"
    results["unsupported_receipt_version"] = bool(verify(future, assignment))

    # overclaim at issue time
    try:
        issue_receipt(
            {**DEMO_PROTOCOL, "request_id": "r", "reviewer_id": "rev-1", "subject_id": "s",
             "measured": ["x"], "not_measured": ["y"], "findings": ["Subject is certified safe"],
             "evidence": [], "issued_at": "t", "issuer_id": DEMO_ISSUER},
            DEMO_ISSUER,
            DEMO_KEYS[DEMO_ISSUER],
            DEMO_KEYS["reviewer:rev-1"],
        )
        results["overclaim_rejected"] = False
    except ReceiptError:
        results["overclaim_rejected"] = True

    return results


def _valid_transaction() -> Tuple[AssessmentRequest, Assignment, Dict[str, Any]]:
    request = _demo_request()
    assignment = select_reviewer(request, demo_reviewers(), [], DEMO_SEED)
    receipt = issue_receipt(
        _receipt_body(request, assignment, _demo_evidence(request)),
        DEMO_ISSUER,
        DEMO_KEYS[DEMO_ISSUER],
        DEMO_KEYS[f"reviewer:{assignment.reviewer_id}"],
    )
    return request, assignment, receipt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def write_report(results: Mapping[str, Any], out_dir: str) -> str:
    """Write the smoke-test results as JSON evidence for CI. Returns the report path."""
    directory = Path(out_dir)
    if not directory.is_dir():
        raise SpecLoadFailed(f"report directory does not exist: {out_dir}")
    path = directory / f"{TOOL_NAME}_report.json"
    path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def smoke_test(report_dir: Optional[str] = None) -> int:
    assignment, receipt, problems = run_synthetic_transaction()
    negatives = negative_cases()
    failures = []
    if problems:
        failures.append(f"happy path produced problems: {problems}")
    for name, rejected in negatives.items():
        if not rejected:
            failures.append(f"negative case not rejected: {name}")
    results = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "happy_path_problems": problems,
        "negative_cases": negatives,
        "passed": not failures,
    }
    if report_dir:
        print(f"report: {write_report(results, report_dir)}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print(f"{TOOL_NAME} smoke test OK: assigned {assignment.reviewer_id}, receipt verified, negatives rejected")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="HIAE-001 assurance transaction core (proposal stage)")
    parser.add_argument("--smoke-test", action="store_true", help="run synthetic transaction and negative cases")
    parser.add_argument("--report-dir", help="directory to write the smoke-test JSON report into")
    args = parser.parse_args(argv)
    if args.smoke_test:
        try:
            return smoke_test(args.report_dir)
        except SpecLoadFailed as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
