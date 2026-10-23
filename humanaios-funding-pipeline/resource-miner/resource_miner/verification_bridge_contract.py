"""Fail-closed bridge; only actual URA registry normalization is accepted."""
from .models import ResourceCandidate, EvidenceRef
from .verification_opportunities import OpportunityObservation, evaluate

class BridgeDenied(ValueError):
    pass

def project(registry, observation, *, need_state="UNKNOWN", claim_summary="Unverified claim"):
    from .universal_adapter import AdapterRegistry, Observation, AdapterDenied
    if not isinstance(registry, AdapterRegistry) or not isinstance(observation, Observation):
        raise BridgeDenied("registered URA observation required")
    try:
        row = registry.normalize(observation)
    except AdapterDenied as exc:
        raise BridgeDenied("URA rejected observation") from exc
    if (row["authority_effect"], row["authorization"], row["execution"]) != (
            "NONE", "NOT_GRANTED", "NOT_AVAILABLE"):
        raise BridgeDenied("authority boundary")
    refs = row["evidence"]
    if len(refs) != 1 or refs[0]["url"] != row["source_url"]:
        raise BridgeDenied("provenance mismatch")
    candidate = ResourceCandidate(
        resource_id=row["resource_id"], title=row["title"],
        source_name=row["source_name"], source_url=row["source_url"],
        canonical_url=row["canonical_url"], discovery_method=row["discovery_method"],
        discovered_at=row["discovered_at"], primary_source_url=row["primary_source_url"],
        resource_types=list(row["resource_types"]), evidence=[EvidenceRef(**refs[0])],
        route="WATCH", status="UNKNOWN", eligibility_assessed=False,
        eligibility_status="UNASSESSED",
        opportunity_kind="INDEPENDENT_VERIFICATION_OPPORTUNITY",
        opportunity_source_kind="PUBLIC_METADATA")
    screen = evaluate(OpportunityObservation(
        identifier=candidate.resource_id, subject=candidate.title,
        source_url=candidate.source_url, source_kind="synthetic",
        need_state=need_state, claim_summary=claim_summary,
        evidence_refs=(candidate.source_url,)), {})
    rid = candidate.resource_id
    graph = {
        "nodes": [{"id": rid, "type": "RESOURCE_CANDIDATE"},
                  {"id": rid + ":claim", "type": "UNVERIFIED_CLAIM"},
                  {"id": rid + ":evidence", "type": "PROVENANCE_REFERENCE",
                   "digest": observation.evidence_digest}],
        "edges": [{"from": rid, "to": rid + ":claim", "type": "ASSERTS"},
                  {"from": rid + ":claim", "to": rid + ":evidence", "type": "CITES"}],
        "authority_effect": "NONE", "can_authorize": False}
    return {"resource": candidate.to_dict(), "verification": screen, "graph": graph,
            "authority_effect": "NONE", "can_authorize": False}
