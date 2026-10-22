"""Build a thin Oracle state artifact for the Oracle + Actualizer MVP."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

STATUS_PRIORITY = {
    "DEFEATED": 0,
    "UNKNOWN": 1,
    "DISPUTED": 2,
    "INFERRED": 3,
    "PARTIALLY_SUPPORTED": 4,
    "OBSERVED": 5,
    "VERIFIED": 6,
}

STATUS_COLOR = {
    "VERIFIED": "green",
    "PARTIALLY_SUPPORTED": "yellow",
    "OBSERVED": "blue",
    "INFERRED": "blue",
    "DISPUTED": "black",
    "UNKNOWN": "gray",
    "DEFEATED": "red",
}


def _now_from_arg(now_arg: str | None) -> datetime:
    if not now_arg:
        return datetime.now(UTC)
    if now_arg.endswith("Z"):
        now_arg = now_arg[:-1] + "+00:00"
    return datetime.fromisoformat(now_arg).astimezone(UTC)


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_value(args: list[str], default: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True).strip() or default
    except (subprocess.CalledProcessError, FileNotFoundError):
        return default


def _minimum_status(statuses: list[str]) -> str:
    return min(statuses, key=lambda status: STATUS_PRIORITY.get(status, -1))


def _action_from_claims(
    action_id: str,
    proposed_action: str,
    goal: str,
    claim_ids: list[str],
    claim_statuses: dict[str, str],
    authority_basis: str,
    required_preconditions: list[str],
    affected_artifacts: list[str],
    execution_plan: list[str],
    expected_observation: str,
    success_condition: str,
    falsifier: str,
    reversible: bool = True,
) -> dict:
    statuses = [claim_statuses[claim_id] for claim_id in claim_ids]
    lowest = _minimum_status(statuses)
    blocked = lowest in {"UNKNOWN", "DISPUTED", "DEFEATED"}

    if blocked:
        status = "BLOCKED_PENDING_OVERRIDE"
    else:
        status = "READY_FOR_HUMAN_AUTHORIZATION"

    return {
        "action_id": action_id,
        "proposed_action": proposed_action,
        "goal": goal,
        "authority_basis": authority_basis,
        "warrant": claim_ids,
        "warrant_premise_statuses": statuses,
        "lowest_warrant_status": lowest,
        "ui_color": STATUS_COLOR[lowest],
        "required_preconditions": required_preconditions,
        "affected_artifacts": affected_artifacts,
        "execution_plan": execution_plan,
        "reversible": reversible,
        "expected_observation": expected_observation,
        "success_condition": success_condition,
        "falsifier": falsifier,
        "human_approval_required": True,
        "status": status,
        "execution_receipt": None,
    }


def build_oracle_state(now: datetime) -> dict:
    generated_at = _iso(now)
    executed_at = now - timedelta(hours=2)
    quarantine_until = executed_at + timedelta(hours=48)

    claims = [
        {
            "claim_id": "CR-117",
            "statement": "Three active SMAG work items overlap in scope and expected outputs.",
            "epistemic_status": "VERIFIED",
            "provenance_refs": ["issue:#497", "issue:#507", "audit:scope-overlap-v1"],
        },
        {
            "claim_id": "CR-121",
            "statement": "Consolidation can reduce operator queue load without dropping evidence history.",
            "epistemic_status": "INFERRED",
            "provenance_refs": ["analysis:queue-comparison-v2"],
        },
        {
            "claim_id": "CR-130",
            "statement": "Consolidation has no hidden dependency on external registries.",
            "epistemic_status": "UNKNOWN",
            "provenance_refs": ["challenge:topology-gap-01"],
        },
    ]
    claim_statuses = {claim["claim_id"]: claim["epistemic_status"] for claim in claims}

    ready_action = _action_from_claims(
        action_id="ACT-0042",
        proposed_action="Consolidate three overlapping SMAG work items with preserved lineage.",
        goal="Reduce duplicate operational work while preserving challenge/evidence links.",
        claim_ids=["CR-117", "CR-121"],
        claim_statuses=claim_statuses,
        authority_basis="human-approved repository coordination",
        required_preconditions=[
            "all candidate issues are independently classified as overlapping",
            "no unresolved blocker evidence is open",
        ],
        affected_artifacts=["PRIORITY_QUEUE.md", "REGISTERED.md"],
        execution_plan=[
            "create one consolidated work item",
            "cross-link predecessor issues",
            "preserve prior evidence references",
            "close predecessors only after verification",
        ],
        expected_observation="One active item replaces three redundant active items with preserved provenance.",
        success_condition="Queue shows one active consolidated item and all predecessor evidence remains traceable.",
        falsifier="New evidence shows materially independent scope across any predecessor item.",
    )

    blocked_action = _action_from_claims(
        action_id="ACT-0043",
        proposed_action="Close redundant issues immediately.",
        goal="Reduce open issue count rapidly.",
        claim_ids=["CR-130"],
        claim_statuses=claim_statuses,
        authority_basis="none",
        required_preconditions=["independent topology review confirms no hidden dependency"],
        affected_artifacts=["issues"],
        execution_plan=["bulk-close candidate issues"],
        expected_observation="Issue count drops with no regressions.",
        success_condition="No impacted dependency is observed post-close.",
        falsifier="Dependency breakage or missing authority appears in post-action observation.",
    )

    receipt = {
        "receipt_id": "RCPT-0001",
        "action_id": "ACT-0042",
        "executed_at": _iso(executed_at),
        "consequence_status": "EXECUTION_CONSEQUENCE_UNVERIFIED",
        "quarantine_until": _iso(quarantine_until),
        "independent_verification": {
            "status": "PENDING",
            "evidence_refs": [],
        },
    }

    return {
        "policy": {
            "epistemic_status_required": True,
            "badge_visibility_rule": "every_rendered_claim",
            "actualizer_action_color": "minimum_warrant_status",
            "execution_consequence_quarantine_hours": 48,
            "living_constitution_status": "EXPERIMENTAL_FALSIFIABLE",
        },
        "system_state": {
            "repository": "humanaios-ui/operations",
            "branch": _git_value(["branch", "--show-current"], "unknown"),
            "commit": _git_value(["rev-parse", "--short", "HEAD"], "unknown"),
            "generated_at": generated_at,
            "posture": "evidence-bound, contestable, human-authority-retained",
        },
        "constitutional_state": {
            "foundational_principles": [
                "Oracle is not ground truth",
                "Agreement is not verification",
                "Actualizer cannot self-authorize",
                "Unknowns remain first-class",
            ],
            "authorization_grants": [
                {
                    "authorization_id": "AUTH-001",
                    "grantor": "asset-owner",
                    "grantee_role": "SECURITY-EVALUATOR",
                    "assets": ["sandbox-A"],
                    "permitted_actions": ["security_testing"],
                    "prohibited_actions": ["third_party_access"],
                    "valid_from": None,
                    "valid_until": None,
                    "delegation_allowed": False,
                    "evidence_ref": "scope-document-v1",
                }
            ],
            "trust_boundaries": [{"boundary_id": "TB-001", "description": "No third-party asset crossing without explicit grant."}],
            "delegation_grants": [{"delegation_id": "DG-001", "delegation_allowed": False, "evidence_ref": "scope-document-v1"}],
            "safe_stop_policies": [{"policy_id": "SSP-001", "stop_condition": "authority unresolved", "required_action": "halt_and_escalate"}],
        },
        "agents": [
            {"agent_id": "witness-1", "role": "WITNESS", "authority_scope": "verification only"},
            {"agent_id": "jester-1", "role": "JESTER", "authority_scope": "challenge only"},
            {"agent_id": "oracle-1", "role": "ORACLE", "authority_scope": "state synthesis only"},
            {"agent_id": "actualizer-1", "role": "ACTUALIZER", "authority_scope": "proposal only"},
            {
                "agent_id": "topology-1",
                "role": "PROVENANCE_TOPOLOGY_AGENT",
                "authority_scope": "hidden-dependency and provenance-path detection",
            },
            {"agent_id": "human-1", "role": "HUMAN_OPERATOR", "authority_scope": "consequential authorization"},
        ],
        "claims": claims,
        "evidence": [
            {"evidence_id": "EV-001", "type": "issue", "source": "#497", "observed_at": generated_at},
            {"evidence_id": "EV-002", "type": "audit", "source": "scope-overlap-v1", "observed_at": generated_at},
        ],
        "warrants": [
            {"warrant_id": "WR-001", "claim_ids": ["CR-117", "CR-121"], "status": "ACTIVE"},
            {"warrant_id": "WR-002", "claim_ids": ["CR-130"], "status": "BLOCKED_UNKNOWN"},
        ],
        "challenges": [
            {"challenge_id": "CH-001", "target_claim_id": "CR-130", "status": "UNRESOLVED", "reason": "missing topology proof"}
        ],
        "unknowns": [
            {
                "unknown_id": "UK-001",
                "question": "Do any hidden dependencies make immediate closure unsafe?",
                "current_evidence": ["challenge:topology-gap-01"],
                "needed_observation": "provenance topology scan",
                "candidate_experiment": "compare dependency graph before/after dry-run",
            }
        ],
        "experiments": [
            {
                "experiment_id": "PILOT-001",
                "status": "BASELINE_PRESERVED",
                "note": "No substrate optimization applied in baseline stage.",
            }
        ],
        "precedents": [{"precedent_id": "PR-001", "note": "Precedent informs but does not override contradictory current evidence."}],
        "amendments": [{"amendment_id": "AM-001", "status": "PROPOSED", "note": "Epistemic badge enforcement under active test."}],
        "actions": [ready_action, blocked_action],
        "execution_receipts": [receipt],
        "human_attention": [
            {
                "attention_id": "HA-001",
                "type": "AUTHORITY_DECISION",
                "summary": "Authorize ACT-0042 after reviewing unresolved challenges.",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Oracle state artifact")
    parser.add_argument("--output", default="oracle_state.json", help="Path for generated oracle state")
    parser.add_argument("--now", default=None, help="ISO timestamp override for reproducible output")
    args = parser.parse_args()

    now = _now_from_arg(args.now)
    state = build_oracle_state(now)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
