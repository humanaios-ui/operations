"""Read-only capability routing and evidence-gap projection for INTENT-OS.

No network, execution, permission granting, or source promotion.
"""
from __future__ import annotations
import json
from pathlib import Path

CAPABILITIES = {
    "resource_discovery": {"module": "resource_miner.intent_os", "needs": ("objective", "candidates")},
    "source_correction": {"module": "resource_miner.controlled_correction", "needs": ("source_ref", "source_revision")},
    "graph_lookup": {"module": "tools.graph_lookup_v0_1", "needs": ("graph",)},
    "independent_evaluation": {"module": "inspect_ai", "needs": ("frozen_cases",)},
}
VALID_STATES = {"OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED", "UNVERIFIED", "CONTRADICTED"}
GRAPH_NAMES = {"intent", "evidence", "system", "temporal"}

def route(objective, available=()):
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("objective required")
    available = set(available)
    return {"objective": objective[:500], "authority_effect": "NONE",
            "execution": "DISABLED",
            "capabilities": [
                {"name": name, "module": spec["module"],
                 "status": "AVAILABLE" if name in available else "NOT_VERIFIED",
                 "required_inputs": list(spec["needs"])}
                for name, spec in CAPABILITIES.items()]}

def project(graphs, claims):
    """Accept only explicitly supplied read-only observations; never infer verified status."""
    if not isinstance(graphs, dict) or not isinstance(claims, list):
        raise ValueError("invalid inputs")
    observations = []
    for name, record in sorted(graphs.items()):
        if name not in GRAPH_NAMES or not isinstance(record, dict):
            raise ValueError("unknown graph")
        source = record.get("source_ref")
        revision = record.get("revision")
        if not isinstance(source, str) or not source or not isinstance(revision, str) or not revision:
            raise ValueError("graph requires source_ref and revision")
        observations.append({"graph": name, "source_ref": source, "revision": revision,
                             "state": "UNVERIFIED", "authority_effect": "NONE"})
    gaps = []
    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise ValueError("invalid claim")
        state = claim.get("state", "UNVERIFIED")
        if state not in VALID_STATES:
            raise ValueError("invalid evidence state")
        ref = claim.get("source_ref")
        revision = claim.get("revision")
        independent = claim.get("independent_receipt")
        if not ref or not revision:
            gaps.append({"claim_index": i, "gap": "MISSING_SOURCE_OR_REVISION"})
        if state in {"OBSERVED", "SUPPORTED"} and not independent:
            gaps.append({"claim_index": i, "gap": "INDEPENDENT_RECEIPT_MISSING"})
        if state in {"UNVERIFIED", "HYPOTHESIZED", "INFERRED"}:
            gaps.append({"claim_index": i, "gap": "NOT_INDEPENDENTLY_VERIFIED"})
    return {"schema": "humanaios.capability_reflex.e0.v1",
            "authority_effect": "NONE", "execution": "DISABLED",
            "graph_observations": observations, "witness_evidence_gaps": gaps,
            "human_outcomes_verified": 0, "human_outcomes_status": "NOT_MEASURED"}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps({"routing": route(data["objective"], data.get("available", [])),
                      "projection": project(data.get("graphs", {}), data.get("claims", []))},
                     indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
