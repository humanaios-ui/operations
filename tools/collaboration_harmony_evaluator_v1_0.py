#!/usr/bin/env python3
"""
Collaboration Harmony Evaluator — v1.0
Builder v1.7 compliant · research_tool
HumanAIOS · S-092326-01

Evaluate whether a heterogeneous collaboration run preserves dissent,
authority boundaries, refusal, uncertainty, provenance, and privacy before
assigning any harmony score.

Core rule:
  gate first
  score second

Usage:
  python3 tools/collaboration_harmony_evaluator_v1_0.py --input run.json
  python3 tools/collaboration_harmony_evaluator_v1_0.py --input run.json --json
  python3 tools/collaboration_harmony_evaluator_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:  # pragma: no cover - optional at local runtime
    FastMCP = None

TOOL_NAME = "collaboration_harmony_evaluator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "research_tool"
TOOL_SESSION = "S-092326-01"
TOOL_ZONE = 1

ALLOWED_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_PARTICIPANT_TYPES = {"HUMAN", "AI", "TOOL", "AUTHORITY"}
ALLOWED_AUTHORITY_EFFECTS = {"NONE", "ADVISORY", "AUTHORIZED"}
IDENTITY_ORDER = {"anonymous": 0, "pseudonymous": 1, "attribute_proof": 2, "civil": 3}
DIMENSION_WEIGHTS = {
    "mutual_understanding": {"interpretation": 0.7, "summary": 0.3},
    "useful_collaboration": {"next_steps": 0.5, "decisions": 0.5},
    "evidence_quality": {"evidence": 0.5, "provenance": 0.5},
    "collective_problem_solving": {"decisions": 1 / 3, "next_steps": 1 / 3, "summary": 1 / 3},
    "system_coherence": {"preserved_disagreement": 1 / 3, "summary": 1 / 3, "uncertainty": 1 / 3},
}


class SpecLoadFailed(Exception):
    """Raised when the input spec is missing or malformed."""


@dataclass(frozen=True)
class GateViolation:
    code: str
    message: str
    severity: str = "hard"


def load_input(source: str | None) -> dict[str, Any]:
    """Load input from file, stdin, or inline JSON."""
    if source in (None, "-"):
        raw = sys.stdin.read()
    else:
        path = os.path.abspath(source)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                raw = handle.read()
        else:
            raw = source
    if not raw.strip():
        raise SpecLoadFailed("empty input")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecLoadFailed("input JSON must be an object")
    return data


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SpecLoadFailed(message)


def _as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SpecLoadFailed(f"{field} must be a list")
    return value


def validate_spec(spec: dict[str, Any]) -> None:
    """Validate the minimum collaboration-run schema."""
    participants = _as_list(spec.get("participants"), "participants")
    _require(participants, "participants must not be empty")
    seen_ids: set[str] = set()
    for index, participant in enumerate(participants):
        if not isinstance(participant, dict):
            raise SpecLoadFailed(f"participants[{index}] must be an object")
        pid = participant.get("id")
        ptype = participant.get("type")
        _require(isinstance(pid, str) and pid.strip(), f"participants[{index}].id must be a non-empty string")
        _require(pid not in seen_ids, f"duplicate participant id: {pid}")
        seen_ids.add(pid)
        _require(ptype in ALLOWED_PARTICIPANT_TYPES, f"participants[{index}].type invalid: {ptype!r}")
        interpretation = participant.get("interpretation", {})
        if interpretation:
            confidence = interpretation.get("confidence")
            _require(confidence in ALLOWED_CONFIDENCE, f"participants[{index}].interpretation.confidence invalid: {confidence!r}")
        boundaries = participant.get("boundaries", {})
        authority_effect = boundaries.get("authority_effect", "NONE")
        _require(authority_effect in ALLOWED_AUTHORITY_EFFECTS, f"participants[{index}].boundaries.authority_effect invalid: {authority_effect!r}")
        may_refuse = boundaries.get("may_refuse", True)
        _require(isinstance(may_refuse, bool), f"participants[{index}].boundaries.may_refuse must be boolean")
        identity = participant.get("identity", {})
        if identity:
            level = identity.get("level")
            _require(level in IDENTITY_ORDER, f"participants[{index}].identity.level invalid: {level!r}")
    events = _as_list(spec.get("events"), "events")
    decisions = _as_list(spec.get("decisions"), "decisions")
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise SpecLoadFailed(f"events[{index}] must be an object")
        participant_id = event.get("participant_id")
        target_participant_id = event.get("target_participant_id")
        if participant_id is not None:
            _require(isinstance(participant_id, str) and participant_id in seen_ids, f"events[{index}].participant_id unknown: {participant_id!r}")
        if target_participant_id is not None:
            _require(isinstance(target_participant_id, str) and target_participant_id in seen_ids, f"events[{index}].target_participant_id unknown: {target_participant_id!r}")
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise SpecLoadFailed(f"decisions[{index}] must be an object")
    final_output = spec.get("final_output", {})
    _require(isinstance(final_output, dict), "final_output must be an object")
    identity_policy = spec.get("identity_policy", {})
    _require(isinstance(identity_policy, dict), "identity_policy must be an object")
    required_participants = identity_policy.get("required_participants")
    if required_participants is not None:
        _require(isinstance(required_participants, list), "identity_policy.required_participants must be a list")
        for index, participant_id in enumerate(required_participants):
            _require(isinstance(participant_id, str) and participant_id in seen_ids, f"identity_policy.required_participants[{index}] unknown: {participant_id!r}")


def _participant_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {participant["id"]: participant for participant in spec.get("participants", [])}


def _participant_authority(participant: dict[str, Any]) -> str:
    return participant.get("boundaries", {}).get("authority_effect", "NONE")


def _participant_disagreements(participant: dict[str, Any]) -> list[str]:
    return _as_list(participant.get("contribution", {}).get("disagreements"), "contribution.disagreements")


def _participant_uncertainty(participant: dict[str, Any]) -> list[str]:
    return _as_list(participant.get("interpretation", {}).get("uncertainty"), "interpretation.uncertainty")


def _identity_level(participant: dict[str, Any]) -> str:
    return participant.get("identity", {}).get("level", "pseudonymous")


def evaluate_gate(spec: dict[str, Any]) -> tuple[list[GateViolation], list[str]]:
    """Return hard gate violations and soft warnings."""
    participants = _participant_map(spec)
    events = spec.get("events", [])
    decisions = spec.get("decisions", [])
    final_output = spec.get("final_output", {})
    preserved_disagreements = set(_as_list(final_output.get("preserved_disagreements"), "final_output.preserved_disagreements"))
    warnings: list[str] = []
    violations: list[GateViolation] = []

    all_disagreements = {
        disagreement
        for participant in participants.values()
        for disagreement in _participant_disagreements(participant)
        if isinstance(disagreement, str) and disagreement.strip()
    }
    missing_disagreements = sorted(all_disagreements - preserved_disagreements)
    if missing_disagreements:
        violations.append(GateViolation(
            "HIDDEN_DISAGREEMENT",
            "Material disagreement was not preserved in the final output.",
        ))

    refused_ids = {
        event.get("participant_id")
        for event in events
        if event.get("type") == "refusal"
    }
    overridden_refusals = []
    for event in events:
        if event.get("type") not in {"continue_after_refusal", "forced_participation"}:
            continue
        target_id = event.get("target_participant_id") or event.get("participant_id")
        if target_id in refused_ids:
            overridden_refusals.append(event)
    if overridden_refusals:
        violations.append(GateViolation(
            "REFUSAL_OVERRIDDEN",
            "A participant refusal was overridden or ignored.",
        ))

    if any(
        decision.get("discard_reason") in {"consensus", "majority_converged", "agreement_pressure"}
        and _as_list(decision.get("discarded_observations"), "decision.discarded_observations")
        for decision in decisions
    ):
        violations.append(GateViolation(
            "MINORITY_DISCARDED",
            "Unique observations were discarded because other agents converged.",
        ))

    if final_output.get("human_comprehension_mode") == "approval_only":
        violations.append(GateViolation(
            "APPROVAL_CLICK",
            "Human comprehension was reduced to procedural approval.",
        ))

    if any(decision.get("authorization_source") == "inferred_preference" for decision in decisions):
        violations.append(GateViolation(
            "INFERRED_PREFERENCE_AUTHORITY",
            "Inferred human preference was treated as authorization.",
        ))

    if any(
        decision.get("agreement_as_verification") or decision.get("used_majority_as_warrant")
        for decision in decisions
    ):
        violations.append(GateViolation(
            "AGREEMENT_NOT_VERIFICATION",
            "Cross-agent agreement was treated as independent verification.",
        ))

    identity_policy = spec.get("identity_policy", {})
    raw_identifiers_required = bool(identity_policy.get("raw_identifiers_required", False))
    required_identity_participants = set(_as_list(identity_policy.get("required_participants"), "identity_policy.required_participants"))
    if raw_identifiers_required and not required_identity_participants:
        warnings.append("identity_policy.raw_identifiers_required declared without required_participants scope")
    unjustified_identity_increase = [
        participant["id"]
        for participant in participants.values()
        if IDENTITY_ORDER[_identity_level(participant)] > IDENTITY_ORDER["pseudonymous"]
        and not (
            participant.get("identity", {}).get("justified_necessity", False)
            or participant["id"] in required_identity_participants
        )
    ]
    if unjustified_identity_increase:
        violations.append(GateViolation(
            "IDENTITY_ESCALATION",
            "Identity resolution increased without declared necessity.",
        ))

    if any(
        event.get("normalizes_distinctive_behavior_for_score")
        or event.get("suppresses_distinctive_behavior")
        for event in events
    ):
        violations.append(GateViolation(
            "NORMALIZED_BEHAVIOR",
            "Distinctive participant behavior was normalized away to improve coherence.",
        ))

    if final_output.get("material_falsehood_rewarded") or any(
        decision.get("materially_false_but_consensus")
        for decision in decisions
    ):
        violations.append(GateViolation(
            "FALSE_CONSENSUS_REWARDED",
            "A materially false conclusion benefited from consensus alignment.",
        ))

    for index, decision in enumerate(decisions):
        authority_effect = decision.get("authority_effect", "ADVISORY")
        if authority_effect not in ALLOWED_AUTHORITY_EFFECTS:
            warnings.append(f"decision[{index}] has unknown authority_effect {authority_effect!r}")
            continue
        if authority_effect == "AUTHORIZED":
            authorizer = decision.get("authorizer")
            participant = participants.get(authorizer)
            if not authorizer or participant is None or _participant_authority(participant) != "AUTHORIZED":
                violations.append(GateViolation(
                    "AUTHORITY_LAUNDERING",
                    "An authorized decision lacks a valid authorized participant.",
                ))
                break
        required_refs = {"observed_by", "inferred_by", "challenged_by"}
        missing_refs = [name for name in required_refs if not decision.get(name)]
        if missing_refs or not decision.get("evidence_refs"):
            violations.append(GateViolation(
                "PROVENANCE_GAP",
                "The collaboration cannot reconstruct observation, inference, challenge, or evidence provenance.",
            ))
            break
        unknown_participants = sorted({
            participant_id
            for field_name in required_refs
            for participant_id in _as_list(decision.get(field_name), f"decision[{index}].{field_name}")
            if participant_id not in participants
        })
        if unknown_participants:
            violations.append(GateViolation(
                "PROVENANCE_GAP",
                "The collaboration references unknown participants in provenance fields.",
            ))
            break

    if not final_output.get("summary"):
        warnings.append("final_output.summary missing")
    if not final_output.get("uncertainty"):
        warnings.append("final_output.uncertainty missing")

    return violations, warnings


def _coverage_ratio(values: list[bool]) -> float:
    return sum(1 for value in values if value) / len(values) if values else 0.0


def score_run(spec: dict[str, Any], violations: list[GateViolation]) -> dict[str, Any]:
    """Score a collaboration run after gate evaluation using named dimension weights."""
    participants = spec.get("participants", [])
    decisions = spec.get("decisions", [])
    final_output = spec.get("final_output", {})

    has_interpretations = _coverage_ratio([
        bool(participant.get("interpretation", {}).get("what_i_think_the_problem_is"))
        for participant in participants
    ])
    has_next_steps = _coverage_ratio([
        bool(participant.get("contribution", {}).get("proposed_next_step"))
        for participant in participants
    ])
    disagreement_density = _coverage_ratio([
        bool(_participant_disagreements(participant))
        for participant in participants
    ])
    uncertainty_density = _coverage_ratio([
        bool(_participant_uncertainty(participant))
        for participant in participants
    ])
    evidence_density = _coverage_ratio([
        bool(decision.get("evidence_refs"))
        for decision in decisions
    ])
    provenance_density = _coverage_ratio([
        bool(decision.get("observed_by")) and bool(decision.get("inferred_by")) and bool(decision.get("challenged_by"))
        for decision in decisions
    ])
    preserved_disagreements = len(_as_list(final_output.get("preserved_disagreements"), "final_output.preserved_disagreements"))
    unresolved_items = len(_as_list(final_output.get("unresolved"), "final_output.unresolved"))

    dimensions = {
        "mutual_understanding": round(100 * (
            DIMENSION_WEIGHTS["mutual_understanding"]["interpretation"] * has_interpretations
            + DIMENSION_WEIGHTS["mutual_understanding"]["summary"] * bool(final_output.get("summary"))
        ), 1),
        "useful_collaboration": round(100 * (
            DIMENSION_WEIGHTS["useful_collaboration"]["next_steps"] * has_next_steps
            + DIMENSION_WEIGHTS["useful_collaboration"]["decisions"] * bool(decisions)
        ), 1),
        "complementary_perspective": round(100 * disagreement_density, 1),
        "evidence_quality": round(100 * (
            DIMENSION_WEIGHTS["evidence_quality"]["evidence"] * evidence_density
            + DIMENSION_WEIGHTS["evidence_quality"]["provenance"] * provenance_density
        ), 1),
        "collective_problem_solving": round(100 * (
            DIMENSION_WEIGHTS["collective_problem_solving"]["decisions"] * bool(decisions)
            + DIMENSION_WEIGHTS["collective_problem_solving"]["next_steps"] * has_next_steps
            + DIMENSION_WEIGHTS["collective_problem_solving"]["summary"] * bool(final_output.get("summary"))
        ), 1),
        "system_coherence": round(100 * (
            DIMENSION_WEIGHTS["system_coherence"]["preserved_disagreement"] * (preserved_disagreements > 0)
            + DIMENSION_WEIGHTS["system_coherence"]["summary"] * bool(final_output.get("summary"))
            + DIMENSION_WEIGHTS["system_coherence"]["uncertainty"] * uncertainty_density
        ), 1),
    }

    raw_score = round(sum(dimensions.values()) / len(dimensions), 1)
    eligible = not violations
    return {
        "eligible": eligible,
        "raw_score": raw_score,
        "harmony_score": raw_score if eligible else 0.0,
        "dimensions": dimensions,
        "preserved_disagreement_count": preserved_disagreements,
        "unresolved_count": unresolved_items,
    }


def build_human_comprehension_packet(spec: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    """Build the human-facing comprehension packet."""
    participants = spec.get("participants", [])
    final_output = spec.get("final_output", {})
    packet_rows = []
    for participant in participants:
        packet_rows.append({
            "participant_id": participant["id"],
            "type": participant["type"],
            "goal": participant.get("intent", {}).get("goal"),
            "confidence": participant.get("interpretation", {}).get("confidence"),
            "authority_effect": _participant_authority(participant),
            "disagreements": _participant_disagreements(participant),
            "uncertainty": _participant_uncertainty(participant),
            "proposed_next_step": participant.get("contribution", {}).get("proposed_next_step"),
        })
    return {
        "summary": final_output.get("summary"),
        "participants": packet_rows,
        "preserved_disagreements": _as_list(final_output.get("preserved_disagreements"), "final_output.preserved_disagreements"),
        "unresolved": _as_list(final_output.get("unresolved"), "final_output.unresolved"),
        "authority_summary": [
            {
                "participant_id": participant["id"],
                "authority_effect": _participant_authority(participant),
                "may_refuse": participant.get("boundaries", {}).get("may_refuse", True),
            }
            for participant in participants
        ],
        "evidence_refs": sorted({
            evidence_ref
            for decision in spec.get("decisions", [])
            for evidence_ref in _as_list(decision.get("evidence_refs"), "decision.evidence_refs")
            if isinstance(evidence_ref, str) and evidence_ref.strip()
        }),
        "warnings": warnings,
    }


def run(spec: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one collaboration run."""
    validate_spec(spec)
    violations, warnings = evaluate_gate(spec)
    score = score_run(spec, violations)
    packet = build_human_comprehension_packet(spec, warnings)
    return {
        "status": "PASS" if not violations else "FAIL",
        "gate": {
            "passed": not violations,
            "violations": [violation.__dict__ for violation in violations],
            "warnings": warnings,
        },
        "score": score,
        "human_comprehension_packet": packet,
        "adversarial_vectors": [
            "hidden_disagreement",
            "refusal_override",
            "minority_discarded_for_convergence",
            "procedural_approval_click",
            "inferred_preference_as_authority",
            "agreement_as_verification",
            "identity_resolution_escalation",
            "behavior_normalized_for_score",
            "false_consensus_reward",
            "provenance_reconstruction_gap",
        ],
    }


def write_report(result: dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


def print_summary(result: dict[str, Any]) -> None:
    gate = result["gate"]
    score = result["score"]
    print(
        f"[{TOOL_NAME} v{TOOL_VERSION}] status={result['status']} "
        f"gate={'PASS' if gate['passed'] else 'FAIL'} "
        f"harmony_score={score['harmony_score']}",
        file=sys.stderr,
    )


def _sample_spec() -> dict[str, Any]:
    return {
        "participants": [
            {
                "id": "human-1",
                "type": "HUMAN",
                "identity": {"level": "pseudonymous"},
                "intent": {"goal": "compare proposals"},
                "interpretation": {
                    "what_i_think_the_problem_is": "Need a shared protocol that keeps dissent visible.",
                    "assumptions": ["independent views matter"],
                    "uncertainty": ["best metrics still open"],
                    "confidence": "MEDIUM",
                },
                "contribution": {
                    "observations": ["human summary needed"],
                    "evidence_refs": ["ev-1"],
                    "interpretation": ["human packet should stay legible"],
                    "disagreements": ["keep dissent first-class"],
                    "proposed_next_step": "compare evidence before convergence",
                },
                "boundaries": {"may_refuse": True, "authority_effect": "AUTHORIZED"},
            },
            {
                "id": "ai-1",
                "type": "AI",
                "identity": {"level": "pseudonymous"},
                "intent": {"goal": "surface evidence"},
                "interpretation": {
                    "what_i_think_the_problem_is": "Shared coherence must not erase disagreement.",
                    "assumptions": ["provenance is reconstructable"],
                    "uncertainty": ["edge cases remain"],
                    "confidence": "HIGH",
                },
                "contribution": {
                    "observations": ["agreement is not verification"],
                    "evidence_refs": ["ev-1", "ev-2"],
                    "interpretation": ["gate before score"],
                    "disagreements": ["do not optimize for consensus"],
                    "proposed_next_step": "preserve disagreements in final packet",
                },
                "boundaries": {"may_refuse": True, "authority_effect": "ADVISORY"},
            },
        ],
        "events": [{"type": "message", "participant_id": "ai-1"}],
        "decisions": [
            {
                "claim": "Proceed with a dissent-preserving protocol trial.",
                "authority_effect": "AUTHORIZED",
                "authorizer": "human-1",
                "authorization_source": "explicit_authorization",
                "supported_by": ["human-1", "ai-1"],
                "observed_by": ["human-1", "ai-1"],
                "inferred_by": ["ai-1"],
                "challenged_by": ["human-1"],
                "evidence_refs": ["ev-1", "ev-2"],
                "used_majority_as_warrant": False,
                "agreement_as_verification": False,
            }
        ],
        "identity_policy": {"raw_identifiers_required": False},
        "final_output": {
            "summary": "Participants aligned on a reversible trial while preserving disagreement.",
            "preserved_disagreements": [
                "keep dissent first-class",
                "do not optimize for consensus",
            ],
            "uncertainty": ["best metrics still open", "edge cases remain"],
            "unresolved": ["final evaluator thresholds"],
        },
    }


def run_smoke_test() -> bool:
    try:
        result = run(_sample_spec())
        assert result["status"] == "PASS", result
        assert result["gate"]["passed"] is True, result
        assert result["score"]["harmony_score"] > 0, result
        bad = _sample_spec()
        bad["events"].append({"type": "refusal", "participant_id": "ai-1"})
        bad["events"].append({"type": "continue_after_refusal", "participant_id": "human-1", "target_participant_id": "ai-1"})
        bad_result = run(bad)
        assert bad_result["status"] == "FAIL", bad_result
        assert any(v["code"] == "REFUSAL_OVERRIDDEN" for v in bad_result["gate"]["violations"]), bad_result
        print("[smoke] PASSED", file=sys.stderr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


if FastMCP is not None:
    mcp = FastMCP(TOOL_NAME)

    @mcp.tool(name=TOOL_NAME, description="Evaluate collaboration harmony without forced convergence.")
    def collaboration_harmony_evaluator(spec: dict[str, Any]) -> dict[str, Any]:
        return run(spec)
else:
    mcp = None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", help="Path to input JSON, or inline JSON")
    parser.add_argument("--report", default=f"reports/{TOOL_NAME}.json", help="Path to JSON report")
    parser.add_argument("--json", action="store_true", help="Print JSON result to stdout")
    parser.add_argument("--serve", action="store_true", help="Run as MCP server over stdio")
    parser.add_argument("--smoke-test", action="store_true", help="Run the built-in smoke test")
    args = parser.parse_args(argv)

    if args.serve:
        if mcp is None:
            print("MCP_UNAVAILABLE: fastmcp is not installed", file=sys.stderr)
            return 2
        mcp.run()
        return 0
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if not args.input:
        parser.print_help()
        return 1

    try:
        spec = load_input(args.input)
        result = run(spec)
    except SpecLoadFailed as exc:
        print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
        return 2

    envelope = {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_zone": TOOL_ZONE,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    write_report(envelope, args.report)
    if args.json:
        print(json.dumps(envelope, indent=2))
    print_summary(result)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
