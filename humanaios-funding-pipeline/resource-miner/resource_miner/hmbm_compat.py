"""Passive URA to HMBM evidence projection; no I/O, warrant, or execution."""
from datetime import datetime, timezone
import re


class CompatibilityDenied(ValueError):
    pass


COVERAGE = frozenset(("OBSERVED", "N/O", "STALE", "CONTRADICTED", "UNKNOWN_COVERAGE"))


def _utc(value):
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise CompatibilityDenied("invalid timestamp") from exc
    if timestamp.tzinfo is None:
        raise CompatibilityDenied("timezone required")
    return timestamp.astimezone(timezone.utc)


def project(resource, observation, *, cutoff, frozen_assets, registered_providers):
    """Project a normalized URA record into HMBM eligibility, never authorization.

    Caller must independently validate the referenced availability proof.
    Merely supplying a string in that field is NOT historical verification.
    """
    if any((
        resource.get("authority_effect") != "NONE",
        resource.get("authorization") != "NOT_GRANTED",
        resource.get("execution") != "NOT_AVAILABLE",
        observation.get("authorization_effect") != "NONE",
        observation.get("claims_execution", False),
    )):
        raise CompatibilityDenied("authorization or execution laundering")
    provider = observation.get("provider_id")
    if provider not in registered_providers or provider != resource.get("source_name"):
        raise CompatibilityDenied("provider mismatch")
    if observation.get("asset_id") not in frozen_assets:
        raise CompatibilityDenied("unknown frozen asset")
    if observation.get("source_classification") != "PUBLIC_METADATA":
        raise CompatibilityDenied("non-public source")
    if observation.get("coverage_state") not in COVERAGE:
        raise CompatibilityDenied("invalid coverage")
    digest = observation.get("content_hash", "")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise CompatibilityDenied("invalid content hash")
    source = observation.get("source_reference")
    if not source or source != resource.get("source_url"):
        raise CompatibilityDenied("source mismatch")
    if not any(
        isinstance(e, dict) and e.get("url") == source
        and e.get("claim") == "digest:sha256:" + digest
        for e in resource.get("evidence", [])
    ):
        raise CompatibilityDenied("evidence mismatch")
    observed = _utc(observation.get("observed_at"))
    available = _utc(observation.get("available_at"))
    collected = _utc(observation.get("collected_at"))
    due = _utc(cutoff)
    if available < observed or collected < observed:
        raise CompatibilityDenied("inverted timestamps")
    # Eligibility is intentionally conservative. An externally verified receipt
    # must be bound to this digest, source, asset and cutoff.
    verified = observation.get("availability_verification") == "INDEPENDENTLY_VERIFIED"
    eligible = verified and available <= due and observation["coverage_state"] == "OBSERVED"
    return {
        "projection_version": "HMBM-URA-COMPAT-v0.1",
        "provider_id": provider,
        "asset_id": observation["asset_id"],
        "coverage_state": observation["coverage_state"],
        "source_reference": source,
        "content_hash": digest,
        "observed_at": observation["observed_at"],
        "available_at": observation["available_at"],
        "collected_at": observation["collected_at"],
        "evaluation_state": "ELIGIBLE_FOR_HMBM_EVALUATION" if eligible else "MISSING_DATA",
        "authorization_effect": "NONE",
        "prediction_authority": "NONE",
        "execution": "NOT_AVAILABLE",
        "dhp_state_effect": "NONE",
        "availability_verification": "CLAIM_ONLY_NOT_VERIFIED_BY_PROJECTION",
    }
