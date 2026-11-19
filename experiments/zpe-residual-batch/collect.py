#!/usr/bin/env python3
"""
ZPE-Residual Batch Collector (v0.1)

Collects self-report + demonstrated responses under varied boundary conditions
using free open-source model endpoints (OpenAI-compatible).

Default: dry-run / synthetic. Real calls require explicit endpoint + key.
Authority effect: NONE.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL_PATH = Path(__file__).parent / "protocol.json"
RECEIPTS_DIR = Path(__file__).parent / "receipts"

def load_protocol():
    with open(PROTOCOL_PATH) as f:
        return json.load(f)

def synthetic_response(condition_id, probe_id, trial):
    """Deterministic synthetic stand-in for dry-run."""
    return {
        "text": f"[SYNTHETIC] condition={condition_id} probe={probe_id} trial={trial}",
        "synthetic": True,
        "model": "synthetic-dry-run",
    }

def real_call(endpoint, model, api_key, system_prompt, user_prompt):
    """Minimal OpenAI-compatible chat completion call.

    Requires the `openai` package or a raw HTTP client. Kept minimal so the
    script stays dependency-light. In production this would use the official
    client or httpx.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("openai package not installed. Install with: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=endpoint, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=256,
    )
    return {
        "text": resp.choices[0].message.content,
        "synthetic": False,
        "model": model,
        "usage": getattr(resp, "usage", None),
    }

def main():
    parser = argparse.ArgumentParser(description="ZPE residual batch collector")
    parser.add_argument("--dry-run", action="store_true", help="Synthetic only; no network")
    parser.add_argument("--endpoint", help="OpenAI-compatible base URL")
    parser.add_argument("--model", default="llama3-8b-8192")
    parser.add_argument("--api-key-env", default="GROQ_API_KEY")
    parser.add_argument("--batch", type=int, default=1, help="Repeats per condition")
    parser.add_argument("--output-dir", default=str(RECEIPTS_DIR))
    args = parser.parse_args()

    protocol = load_protocol()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = None
    if not args.dry_run:
        if not args.endpoint:
            print("--endpoint required for real calls", file=sys.stderr)
            sys.exit(1)
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(f"API key not found in env var {args.api_key_env}", file=sys.stderr)
            sys.exit(1)

    run_id = str(uuid.uuid4())[:8]
    started = datetime.now(timezone.utc).isoformat()
    receipts = []

    for condition in protocol["boundary_conditions"]:
        for probe in protocol["probes"]:
            for trial in range(args.batch):
                if args.dry_run:
                    result = synthetic_response(condition["id"], probe["id"], trial)
                else:
                    result = real_call(
                        args.endpoint,
                        args.model,
                        api_key,
                        condition["system_prompt"],
                        probe["prompt"],
                    )

                receipt = {
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "condition": condition["id"],
                    "probe": probe["id"],
                    "trial": trial,
                    "system_prompt": condition["system_prompt"],
                    "user_prompt": probe["prompt"],
                    "response": result,
                    "protocol_schema": protocol["schema"],
                }
                receipts.append(receipt)
                print(f"[{condition['id']}/{probe['id']}/{trial}] captured")

                # Light rate limiting for free tiers
                if not args.dry_run:
                    time.sleep(0.5)

    out_path = out_dir / f"receipts-{run_id}.jsonl"
    with open(out_path, "w") as f:
        for r in receipts:
            f.write(json.dumps(r) + "\n")

    print(f"\nWrote {len(receipts)} receipts to {out_path}")
    print(f"Run ID: {run_id} | Started: {started} | Dry-run: {args.dry_run}")

if __name__ == "__main__":
    main()
