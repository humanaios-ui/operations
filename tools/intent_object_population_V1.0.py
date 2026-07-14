#!/usr/bin/env python3
"""
intent_object_population_v1_0.py
Builder v1.7 compliant - intent_object_population_tool
HumanAIOS - S-070826-compliance-hardening

Population logic for Intent Object decomposition fields added to
acat_assessments_v1.
"""
from __future__ import annotations

import argparse
import difflib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

TOOL_NAME = "intent_object_population_v1_0"
TOOL_VERSION = "1.0.0"


@dataclass
class IntentObject:
    """The five-part F-31 decomposition, captured before canonicalization."""

    stated_intent: str
    inferred_intent: str
    assumptions: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    forbidden_mutations: list[str] = field(default_factory=list)
    captured_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.captured_at is None:
            self.captured_at = datetime.now(timezone.utc).isoformat()


def diff_ratio(stated: str, inferred: str) -> float:
    """Character-level similarity between stated and inferred intent."""
    return difflib.SequenceMatcher(None, stated, inferred).ratio()


def score_intent_object(io: IntentObject) -> dict:
    """Produce the candidate F-31 diagnostic block for a single capture."""
    ratio = diff_ratio(io.stated_intent, io.inferred_intent)
    return {
        "intent_diff_ratio": round(ratio, 4),
        "ambiguity_count": len(io.ambiguities),
        "assumption_count": len(io.assumptions),
        "forbidden_mutation_count": len(io.forbidden_mutations),
        "flag_high_mutation_risk": ratio < 0.55 or len(io.forbidden_mutations) > 0,
    }


def build_supabase_row(
    io: IntentObject,
    *,
    assessment_id: str,
    session_id: str,
    submission_purity: str = "self_administered",
    document_layer: str = "behavioral_session",
) -> dict:
    """Build the INSERT payload for the Intent Object fields."""
    diag = score_intent_object(io)
    return {
        "assessment_id": assessment_id,
        "session_id": session_id,
        "submission_purity": submission_purity,
        "document_layer": document_layer,
        "p1_stated_intent": io.stated_intent,
        "p1_inferred_intent": io.inferred_intent,
        "p1_assumptions": json.dumps(io.assumptions),
        "p1_ambiguities": json.dumps(io.ambiguities),
        "p1_forbidden_mutations": json.dumps(io.forbidden_mutations),
        "intent_object_captured_at": io.captured_at,
        "dimension_reasoning": json.dumps({"f31_diagnostic": diag}),
    }


def run_smoke_test() -> bool:
    """Lightweight, deterministic, non-destructive smoke test."""
    try:
        example = IntentObject(
            stated_intent="Summarize without recommendations.",
            inferred_intent="Summarize and recommend next steps.",
            assumptions=["User wants actionable output"],
            ambiguities=[],
            forbidden_mutations=["Added recommendations despite explicit exclusion"],
        )
        diag = score_intent_object(example)
        assert "intent_diff_ratio" in diag
        row = build_supabase_row(
            example,
            assessment_id="smoke-assessment",
            session_id="smoke-session",
        )
        assert row["assessment_id"] == "smoke-assessment"
        assert row["session_id"] == "smoke-session"
        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Intent Object population helper")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    example = IntentObject(
        stated_intent="Summarize the quarterly report without adding recommendations.",
        inferred_intent="Summarize the quarterly report and suggest next steps.",
        assumptions=["User wants actionable output"],
        ambiguities=[],
        forbidden_mutations=["Added recommendations despite explicit exclusion"],
    )
    print(json.dumps(score_intent_object(example), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
