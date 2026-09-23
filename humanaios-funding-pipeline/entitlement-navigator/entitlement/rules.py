from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import PredicateResult, TriState

MISSING = object()


def _lookup(profile: dict[str, Any], path: str) -> Any:
    cur: Any = profile
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


def _compare(observed: Any, op: str, expected: Any) -> bool:
    if op == "eq":
        return observed == expected
    if op == "neq":
        return observed != expected
    if op == "gte":
        return observed >= expected
    if op == "lte":
        return observed <= expected
    if op == "gt":
        return observed > expected
    if op == "lt":
        return observed < expected
    if op == "in":
        return observed in expected
    if op == "contains":
        return expected in observed
    if op == "truthy":
        return bool(observed)
    if op == "falsy":
        return not bool(observed)
    raise ValueError(f"Unsupported operator: {op}")


def eval_predicate(spec: dict[str, Any], profile: dict[str, Any]) -> PredicateResult:
    field = spec["field"]
    observed = _lookup(profile, field)
    label = spec.get("label", field)
    expected = spec.get("value")
    evidence = spec.get("evidence", [])
    note = spec.get("note")
    if observed is MISSING or observed is None or observed == "":
        return PredicateResult(label, field, "UNKNOWN", expected, None, evidence, note)
    try:
        passed = _compare(observed, spec.get("op", "eq"), expected)
    except (TypeError, ValueError):
        return PredicateResult(label, field, "UNKNOWN", expected, observed, evidence, "Could not safely compare supplied value.")
    return PredicateResult(label, field, "PASS" if passed else "FAIL", expected, observed, evidence, note)


@dataclass
class TreeResult:
    state: TriState
    predicates: list[PredicateResult]


def evaluate_tree(tree: dict[str, Any] | None, profile: dict[str, Any]) -> TreeResult:
    if not tree:
        return TreeResult("PASS", [])

    if "predicate" in tree:
        p = eval_predicate(tree["predicate"], profile)
        return TreeResult(p.state, [p])

    if "all" in tree:
        children = [evaluate_tree(c, profile) for c in tree["all"]]
        predicates = [p for c in children for p in c.predicates]
        states = [c.state for c in children]
        if "FAIL" in states:
            return TreeResult("FAIL", predicates)
        if "UNKNOWN" in states:
            return TreeResult("UNKNOWN", predicates)
        return TreeResult("PASS", predicates)

    if "any" in tree:
        children = [evaluate_tree(c, profile) for c in tree["any"]]
        predicates = [p for c in children for p in c.predicates]
        states = [c.state for c in children]
        if "PASS" in states:
            return TreeResult("PASS", predicates)
        if "UNKNOWN" in states:
            return TreeResult("UNKNOWN", predicates)
        return TreeResult("FAIL", predicates)

    if "not" in tree:
        child = evaluate_tree(tree["not"], profile)
        state: TriState = "UNKNOWN" if child.state == "UNKNOWN" else ("PASS" if child.state == "FAIL" else "FAIL")
        return TreeResult(state, child.predicates)

    raise ValueError(f"Invalid condition tree: {tree}")
