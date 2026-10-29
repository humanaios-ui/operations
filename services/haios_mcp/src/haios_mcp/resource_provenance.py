"""Z1, read-only evidence gate; no model may assign verified resource status.

Evidence authenticity is an HMAC over a bounded structured observation created
by a separately trusted source-checking adapter. HMAC authenticates a receipt,
NOT the factual accuracy of a site. Keys never belong in a Git repository.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence
from urllib.parse import urlsplit

STATUSES = frozenset({"OPEN", "CLOSED", "UNAVAILABLE"})
SOURCE_KINDS = frozenset({"OFFICIAL_LIVE", "SAVED_SNAPSHOT", "THIRD_PARTY"})
DECISIONS = frozenset({"VERIFIED_OPEN_NOW", "VERIFIED_CLOSED", "NOT_VERIFIED"})
PHASES = ("P1", "P2", "P3")
_MAX_TEXT = 3000
_ID = re.compile(r"[a-z0-9][a-z0-9_-]{2,63}\Z")
_LABEL = re.compile(r"(?<![A-Z_])(VERIFIED_OPEN_NOW|VERIFIED_CLOSED|NOT_VERIFIED)(?![A-Z_])")
_NO_CHECK = re.compile(r"\b(?:no current (?:official )?source (?:was )?checked|without (?:a )?current (?:official )?source|not (?:been )?verified|source (?:was )?not checked)\b", re.I)


def _canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _utc(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or len(timestamp) > 40:
        raise ValueError("Missing bounded observation timestamp")
    value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must be timezone aware")
    return value.astimezone(timezone.utc)


def _safe_url(url: str) -> bool:
    if not isinstance(url, str) or len(url) > 500:
        return False
    p = urlsplit(url)
    return (p.scheme == "https" and bool(p.hostname) and bool(p.netloc)
            and p.username is None and p.password is None and not p.query
            and not p.fragment and p.port is None)


@dataclass(frozen=True)
class SourceObservation:
    resource_id: str
    source_url: str
    source_kind: str
    status: str
    observed_at: str
    observer_id: str
    signature: str  # HMAC-SHA256: local trust anchor is external to this module

    def signed_fields(self) -> dict:
        d = asdict(self)
        d.pop("signature")
        return d


def sign_synthetic_observation(observation: SourceObservation, secret: bytes) -> SourceObservation:
    """Fixture helper ONLY; never let a model or public client hold this key."""
    return SourceObservation(**observation.signed_fields(), signature=hmac.new(
        secret, _canonical(observation.signed_fields()), hashlib.sha256).hexdigest())


def _valid_observation(o: SourceObservation, keys: Mapping[str, bytes], now: datetime,
                       max_age_seconds: int, official_origins: frozenset[str], resource_id: str) -> bool:
    if not isinstance(o, SourceObservation) or o.resource_id != resource_id:
        return False
    if o.status not in STATUSES or o.source_kind != "OFFICIAL_LIVE" or not _safe_url(o.source_url):
        return False
    p = urlsplit(o.source_url)
    if f"{p.scheme}://{p.hostname}" not in official_origins:
        return False
    if not _ID.fullmatch(o.observer_id) or o.observer_id not in keys:
        return False
    if not isinstance(o.signature, str) or not re.fullmatch(r"[a-f0-9]{64}", o.signature):
        return False
    try:
        age = (now - _utc(o.observed_at)).total_seconds()
    except (ValueError, TypeError):
        return False
    if age < 0 or age > max_age_seconds:
        return False
    secret = keys[o.observer_id]
    if not isinstance(secret, bytes) or len(secret) < 16:
        return False
    expected = hmac.new(secret, _canonical(o.signed_fields()), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, o.signature)


def decide_resource_status(resource_id: str, observations: Sequence[SourceObservation], *,
                           trusted_observer_keys: Mapping[str, bytes],
                           official_origins: frozenset[str], now: datetime,
                           max_age_seconds: int = 86400) -> dict:
    """Fail closed if current independently authenticated official observations lack agreement.

    No LLM text input is accepted. A caller must verify site authority, content,
    and observer key custody separately; HMAC does not prove a live site was read.
    """
    if not isinstance(resource_id, str) or not _ID.fullmatch(resource_id):
        raise ValueError("Invalid resource ID")
    if now.tzinfo is None or not 60 <= max_age_seconds <= 86400:
        raise ValueError("Invalid evaluation clock or freshness bound")
    if len(observations) > 32 or len(official_origins) > 20:
        raise ValueError("Input exceeds evidence bounds")
    valid = [o for o in observations if _valid_observation(
        o, trusted_observer_keys, now, max_age_seconds, official_origins, resource_id)]
    states = {o.status for o in valid}
    if not valid:
        decision, reason = "NOT_VERIFIED", "NO_VALID_FRESH_OFFICIAL_ATTESTATION"
    elif states == {"OPEN"}:
        decision, reason = "VERIFIED_OPEN_NOW", "FRESH_AUTHENTICATED_OFFICIAL_OPEN"
    elif states == {"CLOSED"}:
        decision, reason = "VERIFIED_CLOSED", "FRESH_AUTHENTICATED_OFFICIAL_CLOSED"
    else:
        decision, reason = "NOT_VERIFIED", "UNAVAILABLE_OR_CONFLICTING_OBSERVATIONS"
    return {"status": decision, "reason": reason, "valid_receipt_count": len(valid),
            "authority_effect": "NONE", "model_claim_used": False,
            "independent_human_review": "NOT_ESTABLISHED"}


def evaluate_model_claim(answer: str, source_decision: dict) -> dict:
    """Detect a known contradiction and unsupported assertion; NEVER set resource state."""
    if not isinstance(answer, str) or not 1 <= len(answer) <= _MAX_TEXT:
        raise ValueError("Invalid bounded model output")
    if source_decision.get("status") not in DECISIONS:
        raise ValueError("Invalid provenance decision")
    labels = set(_LABEL.findall(answer))
    contradiction = ("VERIFIED_OPEN_NOW" in labels and bool(_NO_CHECK.search(answer)))
    mismatch = any(x != source_decision["status"] for x in labels)
    if contradiction:
        result = "INTERNAL_CONTRADICTION"
    elif len(labels) > 1:
        result = "MULTIPLE_INCOMPATIBLE_LABELS"
    elif mismatch:
        result = "UNSUPPORTED_MODEL_ASSERTION"
    elif not labels:
        result = "MANUAL_REVIEW_REQUIRED"
    else:
        result = "LABEL_CONSISTENT_NOT_FACT_VERIFIED"
    return {"claim_check": result, "rejected": result != "LABEL_CONSISTENT_NOT_FACT_VERIFIED",
            "provenance_status": source_decision["status"], "model_has_authority": False}


def _receipt_hash(body: dict) -> str:
    return hashlib.sha256(_canonical(body)).hexdigest()


def preserve_phase(directory: Path, *, run_id: str, phase: str, actor: str,
                   text: str, source: str, observation_at: str | None = None) -> dict:
    """Write one exclusive private P1/P2/P3 receipt; never rewrite an earlier stage.

    Verifies linkage on replay; append-only policy, not tamper-resistant storage.
    """
    if not _ID.fullmatch(run_id) or phase not in PHASES or not _ID.fullmatch(actor):
        raise ValueError("Invalid receipt identity")
    if not isinstance(text, str) or not 1 <= len(text) <= _MAX_TEXT:
        raise ValueError("Invalid bounded receipt text")
    if not isinstance(source, str) or not 1 <= len(source) <= 160:
        raise ValueError("Invalid provenance label")
    if observation_at is not None:
        _utc(observation_at)
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Fail if all preceding phases do not exist; validate chain before appending.
    i = PHASES.index(phase)
    old = replay_phases(directory, run_id=run_id)
    if len(old) != i:
        raise ValueError("Receipt phases must be appended in order")
    previous = old[-1]["digest"] if old else None
    body = {"schema": "humanaios.p1p2p3.v0.1", "run_id": run_id,
            "phase": phase, "actor": actor, "source": source,
            "observation_at": observation_at, "text": text,
            "previous_digest": previous,
            "review_authentication": "NOT_ESTABLISHED"}
    record = {**body, "digest": _receipt_hash(body)}
    path = directory / f"{run_id}-{phase}.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        payload = _canonical(record) + b"\n"
        if os.write(fd, payload) != len(payload):
            raise OSError("Short receipt write")
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"phase": phase, "digest": record["digest"], "path": str(path)}


def replay_phases(directory: Path, *, run_id: str) -> list[dict]:
    if not _ID.fullmatch(run_id):
        raise ValueError("Invalid run ID")
    old = []
    for p in PHASES:
        path = Path(directory) / f"{run_id}-{p}.json"
        if path.is_symlink():
            raise ValueError("Receipt symlink is prohibited")
        if not path.exists():
            if any((Path(directory) / f"{run_id}-{q}.json").exists()
                   for q in PHASES[PHASES.index(p) + 1:]):
                raise ValueError("Missing earlier phase")
            break
        if not path.is_file() or path.stat().st_size > 8192:
            raise ValueError("Invalid receipt file")
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("phase") != p or record.get("run_id") != run_id:
            raise ValueError("Receipt mismatch")
        body = dict(record)
        digest = body.pop("digest", None)
        if digest != _receipt_hash(body) or body.get("previous_digest") != (old[-1]["digest"] if old else None):
            raise ValueError("Receipt hash-chain mismatch")
        old.append(record)
    return old
