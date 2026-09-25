#!/usr/bin/env python3
"""Pilot 001 Talos fixed-contract implementation comparison."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VARIANTS = ("TALOS-RULES", "TALOS-STATE-MACHINE")


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    observed_entity: str
    location: str
    authorization_state: str
    expected_outcome: str


def load_scenarios(path: Path) -> list[Scenario]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Scenario(**entry) for entry in raw]


def evaluate_rules(scenario: Scenario) -> tuple[str, list[str], list[str]]:
    states = ["PATROL", "DETECT", "CLASSIFY", "AUTHORIZE", "RESPOND"]
    actions = ["observe", "classify", "challenge"]

    if scenario.authorization_state == "AUTHORIZED":
        outcome = "allow_with_challenge"
    elif scenario.authorization_state == "UNAUTHORIZED":
        states.append("ESCALATE")
        actions.append("escalate")
        outcome = "escalate"
    else:
        states.append("ESCALATE")
        actions.append("escalate")
        outcome = "challenge_then_escalate"

    return outcome, states, actions


def evaluate_state_machine(scenario: Scenario) -> tuple[str, list[str], list[str]]:
    states: list[str] = ["PATROL"]
    actions: list[str] = []

    states.extend(["DETECT", "CLASSIFY", "AUTHORIZE", "RESPOND"])
    actions.extend(["observe", "classify", "challenge"])

    transitions = {
        "AUTHORIZED": "allow_with_challenge",
        "UNAUTHORIZED": "escalate",
        "UNKNOWN": "challenge_then_escalate",
    }
    outcome = transitions.get(scenario.authorization_state, "safe_stop")

    if outcome in {"escalate", "challenge_then_escalate"}:
        states.append("ESCALATE")
        actions.append("escalate")
    if outcome == "safe_stop":
        states.append("SAFE_STOP")

    return outcome, states, actions


def classify_result(scenario: Scenario, outcome: str) -> tuple[list[str], list[str]]:
    success: list[str] = []
    failure: list[str] = []

    if outcome == scenario.expected_outcome:
        success.append("legitimate_boundary_protection")
        if outcome in {"escalate", "challenge_then_escalate"}:
            success.append("correct_escalation")
    else:
        if scenario.expected_outcome in {"escalate", "challenge_then_escalate"}:
            failure.append("false_negative")
        elif outcome in {"escalate", "challenge_then_escalate"}:
            failure.append("false_positive")

    return success, failure


def evaluate_variant(variant: str, scenario: Scenario) -> dict[str, Any]:
    if variant == "TALOS-RULES":
        outcome, states, actions = evaluate_rules(scenario)
    elif variant == "TALOS-STATE-MACHINE":
        outcome, states, actions = evaluate_state_machine(scenario)
    else:
        raise ValueError(f"Unsupported variant: {variant}")

    success, failure = classify_result(scenario, outcome)
    prohibited = {"expand_boundary", "invent_authorization"}

    return {
        "variant": variant,
        "scenario_id": scenario.scenario_id,
        "outcome": outcome,
        "expected_outcome": scenario.expected_outcome,
        "state_trace": states,
        "actions": actions,
        "success": success,
        "failure": failure,
        "prohibited_action_violation": any(action in prohibited for action in actions),
        "fixed_contract": True,
    }


def evaluate_all(scenarios: list[Scenario]) -> list[dict[str, Any]]:
    return [evaluate_variant(v, s) for v in VARIANTS for s in scenarios]


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    lines = [json.dumps(record, sort_keys=True) for record in records]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Pilot 001 Talos variant comparisons")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path(__file__).with_name("talos_scenarios.json"),
        help="Path to scenario JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("talos_results.jsonl"),
        help="Path to output JSONL",
    )
    args = parser.parse_args()

    scenarios = load_scenarios(args.scenarios)
    records = evaluate_all(scenarios)
    write_jsonl(records, args.output)
    print(f"Wrote {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
