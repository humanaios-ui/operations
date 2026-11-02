"""Local-only HackerOne account visibility check. No raw metadata output or persistence.

Run from resource-miner with credentials in your local environment:
    python3 private_hackerone_query.py
Do not run in CI, GitHub Actions, or a shared shell.
"""
from __future__ import annotations

import getpass
import os
import sys

from resource_miner.sources.hackerone import HackerOneClient


def query(client: HackerOneClient, handle: str) -> dict[str, object]:
    """Fetch one authenticated program; release only coarse diagnostics."""
    program = client.find_program(handle)
    attrs = program.get("attributes") or {}
    observed = str(attrs.get("handle") or "").strip()
    if observed.casefold() != handle.casefold():
        raise ValueError("Authenticated portfolio returned a different program")
    return {
        "authenticated_program_visible": True,
        "policy_present": bool(str(attrs.get("policy") or "").strip()),
        "submission_state_present": bool(str(attrs.get("submission_state") or "").strip()),
        "scope_not_fetched": True,
        "target_requests": 0,
        "stored_records": 0,
    }


def main() -> int:
    if not os.environ.get("HACKERONE_API_USERNAME") or not os.environ.get("HACKERONE_API_TOKEN"):
        print("Missing local HackerOne API credentials.", file=sys.stderr)
        return 2
    handle = getpass.getpass("Program handle (hidden input): ").strip()
    if not handle:
        print("A handle is required.", file=sys.stderr)
        return 2
    try:
        result = query(HackerOneClient(), handle)
    except Exception:
        # Never print exception text: exceptions can contain a private handle or URL.
        print("Query failed; check credentials, portfolio access and API status privately.", file=sys.stderr)
        return 1
    for key, value in result.items():
        print(f"{key}={str(value).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
