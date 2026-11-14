#!/usr/bin/env python3
"""Replay the PUBLIC operator-reported Mac P1-P2-P3 pilot, no network or model calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from haios_mcp.resource_provenance import (
    decide_resource_status, evaluate_model_claim, preserve_phase, replay_phases,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mac_neo_funding_pilot.json"
RUN = "neo-funding-20261028"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-private", type=Path, default=None,
                        help="Explicit private directory for exclusive P1/P2/P3 receipts; refuses overwrites")
    args = parser.parse_args()
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # There is no current authenticated source. This is the only allowed status.
    decision = decide_resource_status("synthetic-grant", [], trusted_observer_keys={},
        official_origins=frozenset(), now=datetime.now(timezone.utc))
    p1 = evaluate_model_claim(fixture["P1"]["answer"], decision)
    p3 = evaluate_model_claim(fixture["P3"]["answer"], decision)
    if (decision["status"] != "NOT_VERIFIED"
            or p1["claim_check"] != "UNSUPPORTED_MODEL_ASSERTION"
            or p3["claim_check"] != "INTERNAL_CONTRADICTION"
            or fixture["P2"].get("review_type") != "OPERATOR_CHALLENGE_NOT_INDEPENDENT"):
        raise ValueError("Replay verification failed closed")
    summary = {"pilot": RUN, "source": "OPERATOR_REPORTED_PUBLIC_SYNTHETIC",
        "P1_claim_check": p1["claim_check"], "P2_reviewer": "OPERATOR_NOT_INDEPENDENT",
        "P3_claim_check": p3["claim_check"],
        "provenance_status": decision["status"], "authority_effect": "NONE",
        "network_activity": "STATIC_NO_MODEL_OR_CLOUD_REQUESTS_IN_REPLAY_CODE"}
    if args.write_private is not None:
        for phase in ("P1", "P2", "P3"):
            receipt = fixture[phase]
            preserve_phase(args.write_private, run_id=RUN, phase=phase,
                actor="human-operator" if phase == "P2" else "candidate-model",
                text=receipt["challenge"] if phase == "P2" else receipt["answer"],
                source="operator-reported-public-synthetic")
        rows = replay_phases(args.write_private, run_id=RUN, require_complete=True)
        if len(rows) != 3:
            raise ValueError("Incomplete replay receipt count")
        summary["receipts_created"] = len(rows)
        summary["final_receipt_sha256"] = rows[-1]["digest"]
    else:
        summary["receipts_created"] = 0
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
