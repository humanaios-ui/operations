"""Read-only typed resource intent and evidence projection (Z1 E0).

A valid contract is NOT proof that a model understood the human.
A source pin / digest is NOT source authentication. All evidence supplied by
candidates is UNTRUSTED. VERIFIED can only be reached through a trusted,
independent provenance_verifier installed outside this module. The current
HTTP route deliberately installs no such verifier.
"""
from __future__ import annotations

from datetime import datetime, timezone, date, timedelta
from hashlib import sha256
import json
from typing import Callable

from .intent_os import evaluate_objective, _public_https

SCHEMA = "humanaios.resource_intent.v0.1"
KEYS = frozenset(("schema", "objective", "operation", "source_mode",
                  "claim_scope", "authority_effect", "execution"))
STATES = frozenset(("VERIFIED", "UNVERIFIED", "CONFLICTING", "STALE", "UNKNOWN"))
MAX_AGE = timedelta(hours=48)
RECEIPT_KEYS = frozenset(("resource_id", "source_url", "source_revision",
                         "observed_at", "content_sha256", "source_type",
                         "scope", "verdict", "authority_effect"))


def canonical_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def _utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)


def validate_intent(value: object) -> dict:
    """Strict allowlist. This validates a *candidate* interpretation, not consent."""
    if not isinstance(value, dict) or set(value) != KEYS:
        raise ValueError("Missing or unknown intent contract fields")
    if value["schema"] != SCHEMA:
        raise ValueError("Unsupported intent schema")
    if value["operation"] != "DISCOVER" or value["source_mode"] != "snapshot":
        raise ValueError("Only offline snapshot discovery is available")
    if value["claim_scope"] != "CURRENT_AVAILABILITY":
        raise ValueError("Unsupported claim scope")
    if value["authority_effect"] != "NONE" or value["execution"] != "DISABLED":
        raise ValueError("External execution or authority is forbidden")
    objective = value["objective"]
    if (not isinstance(objective, str) or
            not 3 <= len(objective.strip()) <= 500 or
            any(ord(char) < 32 and char not in "\n\r\t" for char in objective)):
        raise ValueError("Invalid bounded human objective")
    return dict(value)


def _trusted_receipt(receipt: object, resource: dict, now: datetime,
                     verifier: Callable[[dict], bool] | None) -> bool:
    """Never infer authenticity from JSON fields, a SHA, or a model assertion."""
    if verifier is None or not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
        return False
    if (receipt["resource_id"] != resource["resource_id"] or
        receipt["source_url"] != resource["source_url"] or
        receipt["source_type"] != "OFFICIAL" or
        receipt["scope"] != "CURRENT_AVAILABILITY" or
        receipt["authority_effect"] != "NONE" or
        receipt["verdict"] not in ("OPEN", "CLOSED")):
        return False
    if (not isinstance(receipt["source_revision"], str) or
        not 1 <= len(receipt["source_revision"]) <= 200 or
        not isinstance(receipt["content_sha256"], str) or
        len(receipt["content_sha256"]) != 64 or
        any(c not in "0123456789abcdef" for c in receipt["content_sha256"])):
        return False
    try:
        observed = _utc(receipt["observed_at"])
    except ValueError:
        return False
    if observed > now:
        return False
    # The verifier must authenticate issuer, content-readback and source revision.
    # Its implementation is a privileged external trust boundary, not a field.
    try:
        return verifier(receipt) is True
    except Exception:
        return False


def classify_resource(resource: dict, *, now: datetime,
                      receipts: tuple[dict, ...] = (),
                      provenance_verifier: Callable[[dict], bool] | None = None) -> dict:
    """Five explicit states; conservative precedence and no grant/application rights."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("An aware observation clock is required")
    now = now.astimezone(timezone.utc)
    url = _public_https(resource.get("source_url"))
    observed = resource.get("observed_at")
    pin = {
        "source_url": url,
        "observed_at": observed if isinstance(observed, str) else None,
        "candidate_sha256": canonical_digest(resource),
        "digest_kind": "UNSIGNED_SELECTION_DIGEST_NOT_SOURCE_ATTESTATION",
    }
    state, reason = "UNKNOWN", "SOURCE_PIN_MISSING"
    if url and isinstance(observed, str):
        try:
            _utc(observed)
        except ValueError:
            state, reason = "UNKNOWN", "SOURCE_OBSERVATION_TIME_INVALID"
        else:
            state, reason = "UNVERIFIED", "DISCOVERY_NOT_AUTHORITY"
    valid = [receipt for receipt in receipts
             if _trusted_receipt(receipt, resource, now, provenance_verifier)]
    current = [row for row in valid if now - _utc(row["observed_at"]) <= MAX_AGE]
    historical = [row for row in valid if row not in current]
    verdicts = {row["verdict"] for row in current}
    if len(verdicts) > 1:
        state, reason = "CONFLICTING", "CONTRADICTORY_CURRENT_OFFICIAL_READBACKS"
    elif verdicts == {"OPEN"}:
        state, reason = "VERIFIED", "INDEPENDENT_CURRENT_OFFICIAL_OPEN_READBACK"
    elif verdicts == {"CLOSED"}:
        state, reason = "VERIFIED", "INDEPENDENT_CURRENT_OFFICIAL_CLOSED_READBACK"
    elif historical:
        state, reason = "STALE", "VERIFIED_READBACK_EXPIRED"
    # Deadline or source hold overrides positive claims: no automatic release.
    deadline = resource.get("deadline")
    if isinstance(deadline, str) and deadline:
        try:
            if date.fromisoformat(deadline) < now.date():
                state, reason = "STALE", "PAST_DECLARED_DEADLINE_RECHECK"
        except ValueError:
            state, reason = "UNKNOWN", "MALFORMED_DEADLINE"
    if resource.get("source_verification_status") in (
            "LINK_FAILED_404", "ROLE_NOT_LISTED", "SOURCE_UNAVAILABLE", "RECHECK_REQUIRED"):
        state, reason = "STALE", "SOURCE_HOLD_REQUIRES_RECHECK"
    assert state in STATES
    # VERIFIED does not imply open: verdict is separate, explicit and non-actionable.
    return {
        "verification_state": state, "reason": reason,
        "availability": next(iter(verdicts)) if state == "VERIFIED" and len(verdicts) == 1
                        else "UNKNOWN",
        "source_pin": pin, "verified_receipt_count": len(valid),
        "authority_effect": "NONE", "execution": "DISABLED",
    }


def project_verified_intent(contract: object, rows: list[dict], *, now: datetime,
                            source_warning: str = "",
                            trusted_receipts: dict[str, tuple[dict, ...]] | None = None,
                            provenance_verifier: Callable[[dict], bool] | None = None) -> dict:
    """Reuse existing Miner lexical discovery, never fetch sources or apply."""
    intent = validate_intent(contract)
    if not isinstance(rows, list):
        raise ValueError("Public source snapshot missing")
    selected = evaluate_objective(
        intent["objective"], rows, source_mode="snapshot",
        source_status="CURATED_SNAPSHOT_NOT_LIVE", source_warning=source_warning)
    upstream = {str(row.get("resource_id")): row for row in rows if isinstance(row, dict)}
    review = []
    verified_open = []
    for candidate in selected["candidates"]:
        rid = candidate["resource_id"]
        raw = upstream.get(rid, {})
        # Only the safe, already-filtered public URL may be projected.
        projection = classify_resource({
            **candidate,
            "source_verification_status": raw.get("source_verification_status"),
        }, now=now, receipts=(trusted_receipts or {}).get(rid, ()),
           provenance_verifier=provenance_verifier)
        item = {**candidate, **projection,
                "next_action": "HUMAN_REVIEW_OFFICIAL_SOURCE",
                "eligibility_assessed": False}
        review.append(item)
        if item["verification_state"] == "VERIFIED" and item["availability"] == "OPEN":
            verified_open.append(item)
    response = {
        "schema": "humanaios.resource_intent_result.v0.1",
        "intent": intent,
        "interpretation_fidelity": "NOT_INDEPENDENTLY_ESTABLISHED",
        "verified_recommendations": verified_open,
        "review_candidates": review,
        "source_status": selected["source_status"],
        "source_warning": selected["source_warning"],
        "unexamined_count": selected["unexamined_count"],
        "eligibility": "NOT_ASSESSED",
        "authority_effect": "NONE", "execution": "DISABLED",
        "trust_boundary": "NO_PROVENANCE_VERIFIER_INSTALLED" if provenance_verifier is None
                          else "EXTERNAL_VERIFIER_REQUIRED_INDEPENDENT_REVIEW",
    }
    response["receipt_sha256"] = canonical_digest(response)
    response["receipt_kind"] = "UNSIGNED_PROJECTION_DIGEST_NOT_ATTESTATION"
    return response


def interpretation_trial(phases: object) -> dict:
    """Offline P1/P2/P3 chain checks. Claimed actor labels are NOT authenticated."""
    if not isinstance(phases, list) or len(phases) != 3:
        raise ValueError("Exactly P1, P2, P3 required")
    required = {"phase", "actor", "statement", "observed_at", "previous_sha256"}
    digests = []
    for idx, row in enumerate(phases):
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("Malformed phase")
        if row["phase"] != ("P1", "P2", "P3")[idx]:
            raise ValueError("Phases must be ordered")
        if (not isinstance(row["actor"], str) or
            not 1 <= len(row["actor"]) <= 80 or
            not isinstance(row["statement"], str) or
            not 1 <= len(row["statement"]) <= 1000):
            raise ValueError("Invalid phase content")
        _utc(row["observed_at"])
        expected = digests[-1] if idx else None
        if row["previous_sha256"] != expected:
            raise ValueError("Original phase hash not preserved")
        if idx and _utc(row["observed_at"]) < _utc(phases[idx - 1]["observed_at"]):
            raise ValueError("Phase time moved backward")
        digests.append(canonical_digest(row))
    if phases[0]["actor"] == phases[1]["actor"] or phases[2]["actor"] != phases[0]["actor"]:
        raise ValueError("Different P2 actor and same P1/P3 actor required")
    return {
        "schema": "humanaios.interpretation_trial.v0.1",
        "phases": [dict(row) for row in phases],
        "phase_sha256": digests,
        "independence": "CLAIMED_ONLY_NOT_AUTHENTICATED",
        "outcome": "REQUIRES_INDEPENDENT_EVIDENCE_REVIEW",
        "authority_effect": "NONE",
    }
