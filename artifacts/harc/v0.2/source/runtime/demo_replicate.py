#!/usr/bin/env python3
"""Produce a specimen HARC v0.2 PARTIAL receipt and change proposal.

The caller must supply the SHA-256 of the exact distributed capsule artifact;
the demo refuses to invent one.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from classify_change import classify_detailed
from validate_receipt import validate

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capsule-sha256", required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{64}", args.capsule_sha256):
        raise SystemExit("--capsule-sha256 must be 64 lowercase hex characters")

    receipt = {
        "capsule_id": "humanaios-agent-replication-capsule",
        "capsule_version": "0.2.0",
        "capsule_sha256": args.capsule_sha256,
        "substrate_id": "example-independent-agent",
        "environment": {"runtime": "python3", "network_access": False},
        "prior_review_exposure": "NONE",
        "return_capability": "RETURN_BLOCK_ONLY",
        "replication_status": "PARTIAL",
        "implemented_components": ["zone_classifier", "receipt_validator"],
        "tests": {"passed": 0, "failed": 0, "not_run": 1},
        "test_evidence": [{
            "name": "capsule_conformance_suite",
            "status": "NOT_RUN",
            "evidence_ref": "demo_only:run_tests_separately"
        }],
        "divergences": [{"component": "conformance", "reason": "demo script does not execute the suite"}],
        "limitations": ["This is a specimen receipt, not a replication claim."],
        "warrant": "Specimen only. Run the conformance suite and replace this receipt with observed evidence."
    }
    errors = validate(receipt)
    if errors:
        raise SystemExit("demo receipt failed validation: " + ", ".join(errors))

    proposal_text = "Resolve redirected URLs before local canonical hashing."
    c = classify_detailed(proposal_text)
    proposal = {
        "proposal_id": "ECP-DEMO-001",
        "component": "resource_identity",
        "observation": "Redirect aliases may produce duplicate resource identities.",
        "evidence": ["planted-example"],
        "proposed_change": proposal_text,
        "zone": c.zone,
        "agent_action": c.agent_action,
        "falsifier": "If bounded redirect resolution does not reduce duplicate identities in a planted case, reject the change.",
        "tests_added": 0
    }

    print(json.dumps({"receipt": receipt, "proposal": proposal}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
