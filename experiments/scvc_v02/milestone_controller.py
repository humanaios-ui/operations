"""HumanAIOS SCVC v0.2 milestone pilot — passive, non-authoritative assessment.

This instrument intentionally DOES NOT verify attestation, accept claimed
authorization, execute jobs, mutate governance, or independently achieve work.
No network, credentials, process spawning, repository writes or native scheduler.
Synthetic case testing is distinct from protected-source verification.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "humanaios.milestone_pilot.v0.1"
RESULT_SCHEMA = "humanaios.milestone_pilot_report.v0.1"
MANDATORY = {"schema", "objective_issue", "predecessor_pr", "mode", "authority_effect", "milestones"}
ALLOWED_INPUT = {"observations"}
ALLOWED_STATE = {"UNVERIFIED", "OBSERVED", "CLAIMED_VERIFIED"}


def _valid_id(value):
    return isinstance(value, str) and value.startswith("SCVC-M") and value[6:].isdigit()


def validate(definition):
    """Validate DAG shape and unique acceptance predicates before assessment."""
    if not isinstance(definition, dict) or set(definition) != MANDATORY:
        raise ValueError("unknown milestone contract fields")
    if (definition["schema"] != SCHEMA or definition["mode"] != "PASSIVE_SYNTHETIC"
            or definition["authority_effect"] != "NONE"
            or type(definition["objective_issue"]) is not int
            or definition["objective_issue"] <= 0
            or definition["predecessor_pr"] != 788):
        raise ValueError("incorrect pinned pilot identity")
    nodes = definition["milestones"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 12:
        raise ValueError("invalid bounded milestone set")
    ids = []
    for n in nodes:
        if not isinstance(n, dict) or set(n) != {
                "id", "title", "dependencies", "acceptance", "human_approval_required"}:
            raise ValueError("invalid milestone shape")
        if (not _valid_id(n["id"]) or not isinstance(n["title"], str)
                or not 3 <= len(n["title"]) <= 110
                or not isinstance(n["dependencies"], list)
                or not isinstance(n["acceptance"], list)
                or not 1 <= len(n["acceptance"]) <= 20
                or not isinstance(n["human_approval_required"], bool)
                or any(not isinstance(d, str) for d in n["dependencies"])
                or any(not isinstance(p, str) or not p.isupper()
                       or len(p) > 80 for p in n["acceptance"])
                or len(n["dependencies"]) != len(set(n["dependencies"]))
                or len(n["acceptance"]) != len(set(n["acceptance"]))):
            raise ValueError("invalid milestone data")
        ids.append(n["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate milestone id")
    index = {v: k for k, v in enumerate(ids)}
    for node in nodes:
        if any(d not in index or index[d] >= index[node["id"]] for d in node["dependencies"]):
            raise ValueError("dependency missing, circular, or out of order")
    return nodes


def assess(definition, signals=None):
    """Inspect claimed observations; do not accept evidence as authenticated.

    'OBSERVED' means present in supplied metadata, not trusted observation.
    Promotion requires a separate independently authorized verifier.
    """
    nodes = validate(definition)
    if signals is None:
        signals = {"observations": []}
    if not isinstance(signals, dict) or set(signals) != ALLOWED_INPUT:
        raise ValueError("invalid signal envelope")
    observations = signals["observations"]
    if not isinstance(observations, list) or len(observations) > 200:
        raise ValueError("invalid bounded observations")
    seen = set()
    supplied = {}
    known = {(n["id"], p) for n in nodes for p in n["acceptance"]}
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"milestone_id", "predicate", "state", "ref"}:
            raise ValueError("invalid observation shape")
        key = (row["milestone_id"], row["predicate"])
        ref = row["ref"]
        if (key not in known or key in seen or row["state"] not in ALLOWED_STATE
                or not isinstance(ref, str) or not 1 <= len(ref) <= 128
                or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-" for c in ref)):
            raise ValueError("invalid/duplicate/unbounded observation")
        seen.add(key)
        supplied[key] = row

    result = []
    for n in nodes:
        present = sorted(p for p in n["acceptance"]
                         if (n["id"], p) in supplied and
                         supplied[(n["id"], p)]["state"] != "UNVERIFIED")
        missing = sorted(set(n["acceptance"]) - set(present))
        depends = list(n["dependencies"])
        # No milestone is independently attested or accepted by this process.
        # Later milestones remain blocked even when earlier inputs claim VERIFIED.
        if depends:
            status = "BLOCKED_DEPENDENCY_UNATTESTED"
        elif missing:
            status = "CANDIDATE_EVIDENCE_INCOMPLETE"
        else:
            status = "AWAITING_INDEPENDENT_VERIFICATION"
        result.append({
            "milestone_id": n["id"], "candidate_status": status,
            "untrusted_predicates_present": present,
            "missing_predicates": missing, "unattested_dependencies": depends,
            "human_approval_required": n["human_approval_required"],
            "achieved": False, "can_authorize": False, "authority_effect": "NONE"
        })
    return {
        "schema": RESULT_SCHEMA, "objective_issue": definition["objective_issue"],
        "predecessor_pr": definition["predecessor_pr"], "mode": "PASSIVE_SYNTHETIC",
        "milestones": result, "authority_effect": "NONE",
        "can_authorize": False, "merge_authority": False,
        "authenticated": False, "has_live_witness": False,
        "explanation": "Candidate assessment only; independent current authority is required."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--definition", type=Path, required=True)
    parser.add_argument("--signals", type=Path)
    args = parser.parse_args()
    definition = json.loads(args.definition.read_text(encoding="utf-8"))
    signals = (json.loads(args.signals.read_text(encoding="utf-8"))
               if args.signals else None)
    print(json.dumps(assess(definition, signals), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
