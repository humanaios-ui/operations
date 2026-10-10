"""GPCS-001 advisory-only cross-session translation, v0.1. No persistence or authorization."""
import hashlib
import json
import re
from datetime import datetime, timezone

SCHEMA = "gpcs.observation.v0.1"
STATES = {"OBSERVED_UNVERIFIED", "EVIDENCE_LINKED", "CONTRADICTED", "SUPERSEDED", "RETRACTED"}
OPERATIONS = {"ADD", "SUPERSEDE", "RETRACT", "CONTRADICT"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN = {"authorization", "authorized", "can_execute", "action_ready", "warrant",
             "credentials", "access_token", "api_key", "private_key", "password",
             "instructions", "system_prompt", "tool_call", "command"}

class ContractError(ValueError):
    pass

def _timestamp(s):
    if not isinstance(s, str):
        raise ContractError("timestamp required")
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("invalid timestamp") from exc
    if d.tzinfo is None or d.utcoffset() is None:
        raise ContractError("timezone required")
    return d.astimezone(timezone.utc)

def _identifier(s):
    if not isinstance(s, str) or not ID.fullmatch(s):
        raise ContractError("invalid identifier")
    return s

def translate(record):
    """Return a deterministic, non-authoritative projection; reject unknown input."""
    if not isinstance(record, dict):
        raise ContractError("object required")
    required = {"schema", "observation_id", "agent_id", "session_id", "source_substrate",
                "source_locator", "source_sha256", "statement", "as_of", "recorded_at",
                "epistemic_state", "operation", "related_observation_ids"}
    extra = set(record) - required
    if extra or set(record) != required or extra & FORBIDDEN:
        raise ContractError("unknown or missing fields")
    if record["schema"] != SCHEMA:
        raise ContractError("schema mismatch")
    for field in ("observation_id", "agent_id", "session_id", "source_substrate"):
        _identifier(record[field])
    if not isinstance(record["source_locator"], str) or not record["source_locator"].strip() or len(record["source_locator"]) > 512:
        raise ContractError("invalid locator")
    if not SHA.fullmatch(str(record["source_sha256"])):
        raise ContractError("source digest must be sha256")
    stmt = record["statement"]
    if not isinstance(stmt, str) or not stmt.strip() or len(stmt) > 1024:
        raise ContractError("invalid statement")
    if record["epistemic_state"] not in STATES or record["operation"] not in OPERATIONS:
        raise ContractError("invalid state/operation")
    links = record["related_observation_ids"]
    if not isinstance(links, list) or len(links) > 32 or len(set(map(str, links))) != len(links):
        raise ContractError("invalid related observations")
    for link in links:
        _identifier(link)
    if record["observation_id"] in links:
        raise ContractError("self-reference")
    if record["operation"] != "ADD" and not links:
        raise ContractError("lineage required for correction/contradiction")
    if record["operation"] == "ADD" and record["epistemic_state"] in {"SUPERSEDED", "RETRACTED"}:
        raise ContractError("terminal state without lineage")
    _timestamp(record["as_of"])
    _timestamp(record["recorded_at"])
    # Time ordering is intentionally not used to confer validity or authorization.
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    identity = record["observation_id"]
    invariants = {"advisory_only": True, "can_authorize": False, "authority_effect": "NONE"}
    return {
        "translation_version": SCHEMA,
        "observation_ledger_entry": {"id": identity, "digest": digest, "record": dict(record), **invariants},
        "session_graph_delta": {"session_id": record["session_id"], "observation_ref": identity,
                                "relation": "RECORDED_OBSERVATION", **invariants},
        "evidence_graph_delta": {"observation_ref": identity, "source_sha256": record["source_sha256"],
                                 "source_locator": record["source_locator"], "operation": record["operation"],
                                 "related_observation_ids": list(links), "epistemic_state": record["epistemic_state"],
                                 "proof_status": "NOT_ESTABLISHED", **invariants},
        "coordinator_candidate": {"candidate_type": "GPCS_ADVISORY_OBSERVATION", "observation_ref": identity,
                                  "admission_state": "NOT_REQUESTED",
                                  "overall_stance": "NOT_STARTED", **invariants}
    }

def replay(records):
    """Deterministic ledger replay; reject identity collisions and unresolved lineage."""
    by_id, outputs = {}, []
    for rec in records:
        projected = translate(rec)
        key = rec["observation_id"]
        if key in by_id:
            raise ContractError("duplicate observation id")
        if any(ref not in by_id for ref in rec["related_observation_ids"]):
            raise ContractError("missing prior lineage")
        by_id[key] = projected["observation_ledger_entry"]["digest"]
        outputs.append(projected)
    return outputs
