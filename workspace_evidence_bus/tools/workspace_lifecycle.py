#!/usr/bin/env python3
"""Deterministic lifecycle projection for the Workspace Evidence Bus.

Historical Drive state files are observations, not mutable current state.
Current state is derived only from committed receipts that satisfy the required
checks and preserve authority_effect=NONE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

INITIAL_STATE = "CODE_ONLY_NOT_DEPLOYED"
ROUNDTRIP_VERIFIED = "ROUNDTRIP_VERIFIED"
NEXT_GATE = "BIND_PRIVATE_REFERENCES"

REQUIRED_PASS_FIELDS = (
    "apps_script_post",
    "drive_write_readback_hash",
    "idempotent_replay",
    "secrets_present_check",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_roundtrip_receipt(receipt: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    if receipt.get("artifact_type") != "WORKSPACE_ROUNDTRIP_GATE_RECEIPT":
        errors.append("unexpected artifact_type")
    if receipt.get("authority_effect") != "NONE":
        errors.append("authority_effect must remain NONE")
    if receipt.get("event_type") != "ROUNDTRIP_TEST":
        errors.append("event_type must be ROUNDTRIP_TEST")

    for field in REQUIRED_PASS_FIELDS:
        if receipt.get(field) != "PASS":
            errors.append(f"{field} must equal PASS")

    first = receipt.get("first_attempt")
    replay = receipt.get("replay_attempt")
    if not isinstance(first, dict) or first.get("status") != "PASS" or first.get("replayed") is not False:
        errors.append("first_attempt must be PASS with replayed=false")
    if not isinstance(replay, dict) or replay.get("status") != "PASS" or replay.get("replayed") is not True:
        errors.append("replay_attempt must be PASS with replayed=true")

    hmbm = receipt.get("hmbm_effect")
    if isinstance(hmbm, dict) and hmbm.get("prediction_authorized") is not False:
        errors.append("roundtrip receipt cannot authorize prediction")

    return errors


def project_current_state(
    receipt_path: Path,
    *,
    historical_drive_file_id: str | None = None,
    historical_recorded_at: str | None = None,
    historical_recorded_state: str = INITIAL_STATE,
) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    errors = validate_roundtrip_receipt(receipt)
    if errors:
        raise ValueError("; ".join(errors))

    state: dict[str, Any] = {
        "artifact_type": "WORKSPACE_EVIDENCE_BUS_CURRENT_STATE",
        "schema_version": "1.0",
        "authority_effect": "NONE",
        "state": ROUNDTRIP_VERIFIED,
        "derived_from": [
            {
                "kind": "receipt",
                "path": receipt_path.as_posix(),
                "sha256": sha256_file(receipt_path),
                "event_id": receipt["event_id"],
                "workflow_run_id": receipt["workflow_run_id"],
            }
        ],
        "next_gate": NEXT_GATE,
        "invariants": [
            "DRIVE_ARTIFACT != AUTHORITY",
            "HISTORICAL_SNAPSHOT != CURRENT_STATE",
            "CURRENT_STATE = deterministic_projection(immutable_receipts)",
            "DRIVE_WRITE != REPOSITORY_ADMISSION",
            "REPOSITORY_ADMISSION != AUTHORIZATION",
            "AUTHORIZATION != MERGE",
        ],
    }

    if historical_drive_file_id:
        state["historical_snapshots"] = [
            {
                "store": "GOOGLE_DRIVE",
                "opaque_id": historical_drive_file_id,
                "recorded_at": historical_recorded_at,
                "recorded_state": historical_recorded_state,
                "current_status": "SUPERSEDED_AS_CURRENT_STATE",
                "note": "Historical observation is preserved; only its use as current state is superseded.",
            }
        ]

    return state


def write_projection(state: Mapping[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--historical-drive-file-id")
    parser.add_argument("--historical-recorded-at")
    args = parser.parse_args()

    state = project_current_state(
        args.receipt,
        historical_drive_file_id=args.historical_drive_file_id,
        historical_recorded_at=args.historical_recorded_at,
    )
    write_projection(state, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
