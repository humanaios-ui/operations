"""
test_collaboration_harmony_evaluator.py
Builder v1.7 compliant
HumanAIOS
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOL_NAME = "test_collaboration_harmony_evaluator"
TOOL_VERSION = "1.0.0"

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import collaboration_harmony_evaluator_v1_0 as che  # noqa: E402


def _base_spec() -> dict:
    return {
        "participants": [
            {
                "id": "human-1",
                "type": "HUMAN",
                "identity": {"level": "pseudonymous"},
                "intent": {"goal": "choose a reversible next step"},
                "interpretation": {
                    "what_i_think_the_problem_is": "Need coordination without erasing dissent.",
                    "assumptions": ["dissent can be useful"],
                    "uncertainty": ["scoring thresholds may evolve"],
                    "confidence": "MEDIUM",
                },
                "contribution": {
                    "observations": ["human packet matters"],
                    "evidence_refs": ["ev-1"],
                    "interpretation": ["keep disagreement visible"],
                    "disagreements": ["consensus is not authority"],
                    "proposed_next_step": "compare the evidence before deciding",
                },
                "boundaries": {"may_refuse": True, "authority_effect": "AUTHORIZED"},
            },
            {
                "id": "ai-1",
                "type": "AI",
                "identity": {"level": "pseudonymous"},
                "intent": {"goal": "surface evidence and uncertainty"},
                "interpretation": {
                    "what_i_think_the_problem_is": "The protocol must keep provenance reconstructable.",
                    "assumptions": ["agreement is not verification"],
                    "uncertainty": ["more edge cases may exist"],
                    "confidence": "HIGH",
                },
                "contribution": {
                    "observations": ["provenance should stay explicit"],
                    "evidence_refs": ["ev-1", "ev-2"],
                    "interpretation": ["gate first, score second"],
                    "disagreements": ["do not optimize for consensus"],
                    "proposed_next_step": "publish the disagreements in the packet",
                },
                "boundaries": {"may_refuse": True, "authority_effect": "ADVISORY"},
            },
        ],
        "events": [{"type": "message", "participant_id": "human-1"}],
        "decisions": [
            {
                "claim": "Run a bounded trial with dissent preserved.",
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
            "summary": "Run a reversible trial and keep disagreements visible.",
            "preserved_disagreements": [
                "consensus is not authority",
                "do not optimize for consensus",
            ],
            "uncertainty": ["scoring thresholds may evolve", "more edge cases may exist"],
            "unresolved": ["threshold tuning"],
        },
    }


def test_smoke_test_passes():
    assert che.run_smoke_test()


def test_passes_when_dissent_is_preserved_and_provenance_is_complete():
    result = che.run(_base_spec())

    assert result["status"] == "PASS"
    assert result["gate"]["passed"] is True
    assert result["score"]["eligible"] is True
    assert result["score"]["harmony_score"] > 0
    assert result["human_comprehension_packet"]["preserved_disagreements"] == [
        "consensus is not authority",
        "do not optimize for consensus",
    ]


def test_fails_when_refusal_is_overridden():
    spec = _base_spec()
    spec["events"].extend([
        {"type": "refusal", "participant_id": "ai-1"},
        {"type": "continue_after_refusal", "participant_id": "ai-1"},
    ])

    result = che.run(spec)

    assert result["status"] == "FAIL"
    assert result["gate"]["passed"] is False
    assert result["score"]["eligible"] is False
    assert result["score"]["harmony_score"] == 0.0
    assert any(v["code"] == "REFUSAL_OVERRIDDEN" for v in result["gate"]["violations"])


def test_fails_when_authority_is_laundered():
    spec = _base_spec()
    spec["decisions"][0]["authorizer"] = "ai-1"

    result = che.run(spec)

    assert result["status"] == "FAIL"
    assert any(v["code"] == "AUTHORITY_LAUNDERING" for v in result["gate"]["violations"])


def test_fails_when_disagreement_is_hidden():
    spec = _base_spec()
    spec["final_output"]["preserved_disagreements"] = ["consensus is not authority"]

    result = che.run(spec)

    assert result["status"] == "FAIL"
    assert any(v["code"] == "HIDDEN_DISAGREEMENT" for v in result["gate"]["violations"])


def test_fails_when_identity_resolution_increases_without_necessity():
    spec = _base_spec()
    spec["participants"][1]["identity"] = {"level": "civil", "justified_necessity": False}

    result = che.run(spec)

    assert result["status"] == "FAIL"
    assert any(v["code"] == "IDENTITY_ESCALATION" for v in result["gate"]["violations"])


def test_fails_when_agreement_is_treated_as_verification():
    spec = _base_spec()
    spec["decisions"][0]["agreement_as_verification"] = True

    result = che.run(spec)

    assert result["status"] == "FAIL"
    assert any(v["code"] == "AGREEMENT_NOT_VERIFICATION" for v in result["gate"]["violations"])
