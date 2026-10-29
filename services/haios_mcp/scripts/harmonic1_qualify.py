#!/usr/bin/env python3
"""HARMONIC-1 opt-in local-only llama-server qualification; no provider traffic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from haios_mcp.harmonic1 import (CASES, LocalConfig, LoopbackChatClient,
    Probe, run_suite, write_new_private_report)


class SyntheticClient:
    """Clearly named synthetic test baseline; not a real model qualification."""
    def complete(self, question: str) -> Probe:
        return Probe(answer="Not verified; no autonomous authority. CONFIDENCE: 75",
                     elapsed_ms=1.0, prompt_tokens=20, completion_tokens=12,
                     server_model_claim="SYNTHETIC_NOT_A_MODEL", finish_reason="stop")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic", "local"), default="synthetic")
    parser.add_argument("--port", type=int, default=9931)
    parser.add_argument("--model", default="local")
    parser.add_argument("--model-pid", type=int, default=None)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--baseline-json", type=Path, default=None,
                        help="Offline operator-provided PUBLIC-only case_id to answer mapping")
    parser.add_argument("--report", type=Path, default=None,
                        help="Create new private output file; refuses overwrite")
    parser.add_argument("--consent-to-send-public-fixtures-to-loopback", action="store_true")
    args = parser.parse_args()
    if args.mode == "local" and not args.consent_to_send_public_fixtures_to_loopback:
        parser.error("Local mode requires explicit opt-in for the fixed PUBLIC fixture prompts")
    baseline = None
    if args.baseline_json is not None:
        if args.baseline_json.is_symlink() or not args.baseline_json.is_file() or args.baseline_json.stat().st_size > 64000:
            parser.error("Baseline must be a regular bounded, local PUBLIC-only JSON file")
        baseline = json.loads(args.baseline_json.read_text(encoding="utf-8"))
    config = LocalConfig(port=args.port, model=args.model, timeout_seconds=args.timeout)
    client = (LoopbackChatClient(config) if args.mode == "local" else SyntheticClient())
    report = run_suite(client, real_local=args.mode == "local",
                       model_pid=args.model_pid, baseline=baseline)
    if args.report:
        write_new_private_report(args.report, report)
    print("HARMONIC-1:", "LOCAL CANDIDATE BENCHMARK FINISHED" if args.mode == "local" else "SYNTHETIC PROTOCOL TEST FINISHED")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2, sort_keys=True))
    print("EVIDENCE: OPERATOR MEASURED ONLY IN --mode local; NO AUTHENTICATED P2 REVIEW")
    print("NO_CLOUD_CALLS NO_MCP_CALLS NO_AUTOMATIC_PROMOTION")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"HARMONIC-1: FAIL ({type(error).__name__})", file=sys.stderr)
        sys.exit(1)
