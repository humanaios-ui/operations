#!/usr/bin/env python3
"""Explicit HARC v0.2 transition validator.

This validates capsule-local state transitions. It does not grant Z2/Z3
permission and does not mutate any external system.
"""
from __future__ import annotations

REPLICATION_TRANSITIONS = {
    "UNTESTED": {"PARTIAL", "FAILED", "REPLICATED"},
    "PARTIAL": {"PARTIAL", "FAILED", "REPLICATED"},
    "FAILED": {"FAILED", "PARTIAL", "REPLICATED"},
    "REPLICATED": {"REPLICATED"},
}

ENGINEERING_TRANSITIONS = {
    "OBSERVED": {"PROPOSED"},
    "PROPOSED": {"Z1_EXECUTED", "Z2_AWAITING_RATIFICATION", "Z3_BLOCKED"},
    "Z1_EXECUTED": set(),
    "Z2_AWAITING_RATIFICATION": set(),
    "Z3_BLOCKED": set(),
}


def validate_transition(machine: str, old: str, new: str) -> list[str]:
    tables = {"replication": REPLICATION_TRANSITIONS, "engineering": ENGINEERING_TRANSITIONS}
    if machine not in tables:
        return ["invalid:machine"]
    table = tables[machine]
    if old not in table:
        return ["invalid:old_state"]
    if new not in set(table) | {x for allowed in table.values() for x in allowed}:
        return ["invalid:new_state"]
    if new not in table[old]:
        return [f"invalid_transition:{old}->{new}"]
    return []
