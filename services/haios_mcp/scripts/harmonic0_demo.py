#!/usr/bin/env python3
"""HARMONIC-0: only simulated inference and append-only local receipt replay."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile

from haios_mcp.harmonic0 import RouteRequest, CloudGrant, ReceiptJournal, sha256


def sample_requests():
    public = "Public Resource Miner capability classification"
    private = "PRIVATE_OPERATOR_EXAMPLE_NEVER_EXPORTED"
    return [
        RouteRequest("public-local", public, "PUBLIC", "haios_find_resources"),
        RouteRequest("public-cloud", public, "PUBLIC", "haios_talk", local_capable=False,
                     grant=CloudGrant("public-cloud", sha256(public.encode()))),
        RouteRequest("private-unavailable", private, "PRIVATE", "haios_talk",
                     local_healthy=False,
                     grant=CloudGrant("private-unavailable", sha256(private.encode()))),
        RouteRequest("public-no-grant", public, "PUBLIC", "haios_talk", local_healthy=False),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, help="single-writer local JSONL log")
    args = parser.parse_args()
    if args.journal is None:
        with tempfile.TemporaryDirectory(prefix="haios-harmonic0-") as td:
            run(Path(td) / "receipts.jsonl")
    else:
        run(args.journal)


def run(path: Path) -> None:
    journal = ReceiptJournal(path)
    for req in sample_requests():
        receipt = journal.append(req)
        print(json.dumps({"request_id": req.request_id,
                          "route": receipt["decision"]["route"],
                          "reason_code": receipt["decision"]["reason_code"],
                          "receipt_hash": receipt["receipt_hash"]}, sort_keys=True))
    print("REPLAY", json.dumps(journal.verify(), sort_keys=True))
    print("EXECUTION", "SIMULATED_ONLY_NO_PROVIDER_MCP_OR_NETWORK")


if __name__ == "__main__":
    main()
