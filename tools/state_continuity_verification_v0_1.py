"""HumanAIOS SCVC v0.1: read-only, non-authoritative continuity assessment.

Finite checks are exhaustive ONLY over caller-supplied synthetic sets. The HLKS /
Session Graph adapter checks structural lineage and scope; it NEVER authenticates
source/issuer claims, reconstructs private payloads, or grants execution rights.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Callable, Iterable

SCHEMA = "humanaios.state_continuity_verification.v0.1"
STATUS = frozenset({"EXACTLY_RECOVERABLE", "SEMANTICALLY_RECOVERABLE",
                    "NOT_ESTABLISHED", "RECONSTRUCTION_DENIED"})
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
DOMAINS = frozenset({"human", "operations", "lasting-light-ai"})
PURPOSES = frozenset({"learning", "research", "operations"})
OPAQUE_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\Z")


def _safe_ref(value: Any) -> bool:
    return isinstance(value, str) and OPAQUE_REF.fullmatch(value) is not None


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("offset-aware timestamp required")
    return stamp.astimezone(timezone.utc)


def _report(scope: str, status: str, reasons: Iterable[str],
            *, sources: Iterable[str] = (), observations: Iterable[str] = (),
            subject: str = "synthetic") -> dict[str, Any]:
    if status not in STATUS:
        raise ValueError("invalid disposition")
    body = {
        "schema": SCHEMA, "scope": scope, "subject_ref": subject,
        "status": status, "reason_codes": sorted(set(reasons)),
        "source_refs": sorted(set(sources)),
        "observation_refs": sorted(set(observations)),
        "advisory_only": True, "can_authorize": False,
        "authority_effect": "NONE", "authenticated": False,
    }
    body["report_id"] = "SCVC-" + sha256(_json(body).encode()).hexdigest()[:20]
    return body


def assess_finite(states: Iterable[Any], project: Callable[[Any], Any],
                  retain: Callable[[Any], Any],
                  meaning: Callable[[Any], Any] | None = None,
                  *, max_states: int = 4096) -> dict[str, Any]:
    """Exhaustively test an enumerated finite state set, NOT an unbounded domain.

    Exact iff (project, retain) is injective. Semantic iff the requested
    meaning is constant on each fiber, but original state is not recoverable.
    Synthetic/caller-supplied observations cannot authenticate outside facts.
    """
    fibers: dict[str, tuple[str, str | None]] = {}
    n = 0
    exact = True
    semantic = True
    for state in states:
        n += 1
        if n > max_states:
            return _report("FINITE_SYNTHETIC", "NOT_ESTABLISHED", ["ENUMERATION_LIMIT"])
        key = _json([project(state), retain(state)])
        orig = _json(state)
        sem = _json(meaning(state)) if meaning is not None else None
        prior = fibers.setdefault(key, (orig, sem))
        if prior[0] != orig:
            exact = False
            if meaning is None or prior[1] != sem:
                semantic = False
    if n == 0:
        return _report("FINITE_SYNTHETIC", "NOT_ESTABLISHED", ["EMPTY_STATE_SET"])
    if exact:
        return _report("FINITE_SYNTHETIC", "EXACTLY_RECOVERABLE",
                       ["FINITE_INJECTIVITY_ESTABLISHED", "SYNTHETIC_ONLY"])
    if meaning is not None and semantic:
        return _report("FINITE_SYNTHETIC", "SEMANTICALLY_RECOVERABLE",
                       ["FINITE_SEMANTIC_FIBERS_ESTABLISHED", "EXACT_NOT_RECOVERABLE", "SYNTHETIC_ONLY"])
    return _report("FINITE_SYNTHETIC", "NOT_ESTABLISHED",
                   ["FINITE_COLLISION_COUNTEREXAMPLE", "SYNTHETIC_ONLY"])


def assess_hlks_session(vlr: dict[str, Any], graph: dict[str, Any],
                        entity_id: str, request: dict[str, Any]) -> dict[str, Any]:
    """Read-only HLKS VLR v1 <-> Session Graph v0.2 structural adapter.

    Intentionally cannot return EXACTLY/SEMANTICALLY_RECOVERABLE. Those require
    independent, scoped reconstruction evidence from an authenticated verifier;
    references, hashes, and self-reported VERIFIED receipts are insufficient.
    No raw payloads or private locators are returned.
    """
    scope = "HLKS_SESSION_BINDING"
    subject = entity_id if _safe_ref(entity_id) else "unknown"

    def result(status: str, *reasons: str, sources=(), observations=()):
        return _report(scope, status, reasons, subject=subject,
                       sources=sources, observations=observations)

    if not isinstance(vlr, dict) or not isinstance(graph, dict) or not isinstance(request, dict):
        return result("NOT_ESTABLISHED", "MALFORMED_INPUT")
    if not _safe_ref(entity_id):
        return result("NOT_ESTABLISHED", "INVALID_OPAQUE_ENTITY_REF")
    if (vlr.get("schema_version") != "humanaios.validated_learning_record.v1"
            or graph.get("status") != "DERIVED_NON_CANONICAL"
            or graph.get("graph_id") != "humanaios-cross-chat-longitudinal-evidence-graph"):
        return result("NOT_ESTABLISHED", "INTERFACE_VERSION_MISMATCH")
    if (vlr.get("authority_effect") != "NONE"
            or vlr.get("can_authorize", False) is not False):
        return result("RECONSTRUCTION_DENIED", "AUTHORITY_LAUNDERING")
    try:
        as_of = _timestamp(request["at"])
        domain, purpose = request["domain"], request["purpose"]
        pin, contract_pin = request["source_commit"], request["contract_commit"]
        if (domain not in DOMAINS or purpose not in PURPOSES
                or not isinstance(pin, str) or not COMMIT.fullmatch(pin)
                or not isinstance(contract_pin, str) or not COMMIT.fullmatch(contract_pin)):
            raise ValueError("invalid context")
        privacy = vlr["privacy_scope"]
        revocation = vlr["revocation"]
        validity = vlr["validity_window"]
        applicability = vlr["applicability"]
        sources = vlr["source_refs"]
        observations = vlr["observation_refs"]
        if not isinstance(sources, list) or not sources or not isinstance(observations, list) or not observations:
            raise ValueError("missing references")
        source_ids = {s["source_id"] for s in sources}
        if any(not _safe_ref(i) for i in source_ids):
            raise ValueError("bad source refs")
        if any(not _safe_ref(o.get("observation_id")) or o["source_id"] not in source_ids
               for o in observations):
            raise ValueError("observation/source mismatch")
        if any(c["source_id"] not in source_ids or
               c["corrects_observation_id"] not in {o["observation_id"] for o in observations}
               for c in vlr.get("correction_refs", [])):
            raise ValueError("correction lineage mismatch")
    except (KeyError, ValueError, TypeError, AttributeError):
        return result("NOT_ESTABLISHED", "MALFORMED_OR_UNBOUND_RECORD")

    # Scope decisions precede all cross-source inspection. No private metadata escapes.
    try:
        if revocation["state"] != "ACTIVE":
            return result("RECONSTRUCTION_DENIED", "REVOKED_OR_DELETED")
        if (domain != privacy["owner_domain"] or domain not in privacy["allowed_domains"]
                or purpose != privacy["purpose"]):
            return result("RECONSTRUCTION_DENIED", "DOMAIN_OR_PURPOSE_DENIED")
        if any(c != "PUBLIC" for c in privacy["data_classes"]):
            return result("RECONSTRUCTION_DENIED", "PRIVATE_SOURCE_UNVERIFIED_CONSENT")
        if as_of > _timestamp(privacy["retention_until"]):
            return result("RECONSTRUCTION_DENIED", "RETENTION_EXPIRED")
        if as_of < _timestamp(validity["valid_from"]) or as_of > _timestamp(validity["expires_at"]):
            return result("NOT_ESTABLISHED", "VALIDITY_WINDOW_MISMATCH")
        if vlr["source_commit"] != pin:
            return result("NOT_ESTABLISHED", "SOURCE_COMMIT_MISMATCH")
        if not any(r["commit"] == contract_pin for r in applicability["contract_refs"]):
            return result("NOT_ESTABLISHED", "CONTRACT_COMMIT_MISMATCH")
        # Source pins are mandatory for this continuity bridge, even where VLR v1
        # permits null source_commit for generic external references.
        if any(s["source_commit"] != pin for s in sources):
            return result("NOT_ESTABLISHED", "UNPINNED_OR_CHANGED_SOURCE")
    except (ValueError, KeyError, TypeError, AttributeError):
        return result("NOT_ESTABLISHED", "MALFORMED_OR_UNBOUND_RECORD")

    if (vlr.get("retrieval", {}).get("state") != "ELIGIBLE"
            or domain not in vlr.get("retrieval", {}).get("eligible_domains", [])):
        return result("NOT_ESTABLISHED", "RETRIEVAL_STATE_NOT_CURRENT")

    entities = [e for e in graph.get("entities", []) if e.get("id") == entity_id]
    if len(entities) != 1:
        return result("NOT_ESTABLISHED", "ENTITY_MISSING_OR_DUPLICATED")
    entity = entities[0]
    graph_sources = {s.get("id"): s for s in graph.get("sources", [])}
    if len(graph_sources) != len(graph.get("sources", [])):
        return result("NOT_ESTABLISHED", "DUPLICATE_GRAPH_SOURCES")
    binding = sorted(set(entity.get("source_refs", [])) & source_ids & set(graph_sources))
    if not binding:
        return result("NOT_ESTABLISHED", "NO_SHARED_SOURCE_BINDING")
    if any(graph_sources[s].get("authority_effect") != "NONE" for s in binding):
        return result("RECONSTRUCTION_DENIED", "GRAPH_AUTHORITY_LAUNDERING")
    linked_assertions = [a for a in graph.get("assertions", []) if a.get("subject") == entity_id]
    linked_events = [e for e in graph.get("events", []) if e.get("entity_ref") == entity_id]
    if any(a.get("authority_effect") != "NONE" for a in linked_assertions) or any(
            e.get("authority_effect") != "NONE" for e in linked_events):
        return result("RECONSTRUCTION_DENIED", "GRAPH_AUTHORITY_LAUNDERING")
    if (entity.get("hydration_state") in ("CONTESTED", "CHAT_DERIVED") or
            any(a.get("epistemic_state") == "CONTESTED" for a in linked_assertions)):
        return result("NOT_ESTABLISHED", "UNRESOLVED_OR_CHAT_DERIVED_CLAIMS",
                      sources=binding)
    if any(e.get("type") == "correction" for e in linked_events):
        return result("NOT_ESTABLISHED", "CORRECTION_REPLAY_REQUIRED", sources=binding)
    bound_events = {e.get("id") for e in linked_events if e.get("source_ref") in binding}
    if not any(o.get("source_id") in binding and o.get("observation_id") in bound_events
               for o in observations):
        return result("NOT_ESTABLISHED", "OBSERVATION_EVENT_NOT_BOUND", sources=binding)
    return result("NOT_ESTABLISHED", "SOURCE_BINDING_NOT_PROOF",
                  "INDEPENDENT_RECONSTRUCTION_NOT_EXECUTED", sources=binding,
                  observations=[o["observation_id"] for o in observations if o["source_id"] in binding])
