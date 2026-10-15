#!/usr/bin/env python3
"""CI prediction rollup guard: non-authoritative, fail-closed ledger reconciliation.

Only a single writer may append to a verified, append-only ledger. This module
does not authorize, approve, merge, fetch network data, or rewrite history.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import nf_ledger_v0_1 as engine

TOOL_NAME = "ci_predict_rollup"
TOOL_VERSION = "0.1.0"
ROLLING_BRANCH = "ci-predict-consolidate/rolling"
CONSOLIDATE_TITLE = "ci-predict: consolidate resolved CI predictions"


class RollupBlocked(ValueError):
    pass


def validate_rows(path: Path) -> list[dict]:
    if path.is_symlink() or not path.is_file():
        raise RollupBlocked(f"ledger file missing or symlinked: {path.name}")
    try:
        rows = engine.read(str(path))
        error = engine.verify(rows)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise RollupBlocked(f"ledger parse or hash verification failed: {exc}") from exc
    if error:
        raise RollupBlocked(f"ledger hash chain failed: {error}")
    if rows and rows[0].get("seq") != 1:
        raise RollupBlocked("ledger first sequence must be 1")
    token_ids = [r["token_id"] for r in rows if r.get("type") == "TOKEN"]
    if len(set(token_ids)) != len(token_ids):
        raise RollupBlocked("ledger has duplicate TOKEN identities")
    return rows


def require_append_only(base: Path, candidate: Path) -> int:
    """A rolling branch must extend EXACTLY the verified main chain."""
    trusted = validate_rows(base)
    proposal = validate_rows(candidate)
    if len(proposal) < len(trusted) or proposal[: len(trusted)] != trusted:
        raise RollupBlocked(
            "DIVERGED_LEDGER: candidate does not extend main's exact events; "
            "human reconciliation and fresh check evidence required"
        )
    return len(proposal) - len(trusted)


def select_writer(open_prs: list[dict]) -> dict | None:
    """Refuse duplicates, including legacy timestamped consolidation PRs."""
    if not isinstance(open_prs, list) or len(open_prs) >= 200:
        raise RollupBlocked("open PR inventory incomplete or invalid")
    consolidations = [
        item for item in open_prs
        if isinstance(item, dict)
        and (
            item.get("title") == CONSOLIDATE_TITLE
            or str(item.get("headRefName") or "").startswith("ci-predict-consolidate/")
        )
    ]
    legacy = [
        item for item in consolidations
        if item.get("headRefName") != ROLLING_BRANCH
    ]
    if legacy:
        nums = sorted(str(i.get("number") or "?") for i in legacy)
        raise RollupBlocked(
            "LEGACY_BACKLOG: verify and disposition the existing consolidation PRs "
            "before enabling the single rolling writer: " + ", ".join(nums)
        )
    if len(consolidations) > 1:
        raise RollupBlocked("multiple rolling consolidation PRs; refuse to publish")
    if consolidations and consolidations[0].get("headRefName") != ROLLING_BRANCH:
        raise RollupBlocked("unexpected writer branch")
    return consolidations[0] if consolidations else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("select")
    selection.add_argument("--inventory", type=Path, required=True)
    verify = sub.add_parser("verify-prefix")
    verify.add_argument("--base", type=Path, required=True)
    verify.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "select":
            inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
            selected = select_writer(inventory)
            print(json.dumps({"status": "PASS", "pr": selected, "branch": ROLLING_BRANCH}))
        else:
            count = require_append_only(args.base, args.candidate)
            print(json.dumps({"status": "PASS", "pending_events": count}))
        return 0
    except (RollupBlocked, OSError, ValueError) as exc:
        print(f"ROLLUP_BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
