#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder v1.7 compliant
nf_ledger_cli_v1_0.py

HumanAIOS / PRS — persistence and command surface for the preregistered
study runner in `prs_run.py`.

WHY THIS EXISTS
---------------
`prs_run.py` implements a complete, tested prediction engine: PIN (a
prediction committed before the outcome is known), RESOLVE (the grounded
outcome), EXPECTED/SURPRISE/VOID verdicts, and a SHA256 hash chain. It has
no `__main__`, no argparse, and no caller outside its own tests, and
`PRSRunner` holds every entry in memory, so nothing it computes survives
the process. This tool supplies the door and the durable store. It changes
no logic in `prs_run.py`.

SCHEMA IS DELIBERATELY NOT DECIDED HERE
---------------------------------------
`NF_LEDGER_SCHEMA_v1.md` requires `molt_id`, `molt_type`, `constant`,
`prior_value`, `proposed_value` and a `prediction` object. `prs_run.py`
emits `entry_type`, `hypothesis_id`, `metric`, `prediction_value` and
`brier_score`. The two are disjoint, and reconciling them is the job of
Q-NF-SCHEMA-01, a READY row in a PRIORITY_QUEUE.md whose ratification_hash
still reads "pending Z2 signature".

So this tool takes `--ledger` as a required argument and commits to no
canonical path. It persists exactly what the engine emits. Creating
`NF_LEDGER.jsonl` itself would settle a pending Z2 decision by side effect,
which is the class of thing Z2HashVerifyGate exists to prevent.

CALIBRATION NOTE (read before trusting `brier_score`)
-----------------------------------------------------
`prs_run._create_resolve_entry` hardcodes `prediction_prob = 1.0`, so its
`brier_score` is (1.0 - 1.0)**2 = 0.0 on EXPECTED and (1.0 - 0.0)**2 = 1.0
on SURPRISE, and nothing else. That is a correct/incorrect flag carrying
the name of a scoring rule; it holds no calibration information, because
every predictor scores identically regardless of how well calibrated it is.

This tool does not alter that value, because it is covered by the engine's
hash. Instead, when `--confidence` is supplied at pin time, a genuine Brier
score is computed at resolve time and recorded in an unhashed `calibration`
block beside the entry. Routed to Z2 as a finding rather than patched here.

Usage:
  python3 tools/nf_ledger_cli_v1_0.py pin --ledger L.jsonl \\
      --id H-001 --metric startup_minutes --threshold 8 --direction lt \\
      --window-days 14 --registered-sha <sha> --confidence 0.7 \\
      --title "Startup under 8 min" --prediction "startup will be < 8 min"
  python3 tools/nf_ledger_cli_v1_0.py resolve --ledger L.jsonl \\
      --id H-001 --actual 6.5
  python3 tools/nf_ledger_cli_v1_0.py verify --ledger L.jsonl
  python3 tools/nf_ledger_cli_v1_0.py export --ledger L.jsonl
  python3 tools/nf_ledger_cli_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prs_run import PRSRunner, PreregisteredHypothesis  # noqa: E402

TOOL_NAME = "nf_ledger_cli"
TOOL_VERSION = "1.0.0"

PIN_HASHED_FIELDS = (
    "entry_type",
    "hypothesis_id",
    "metric",
    "timestamp",
    "registered_sha",
    "prediction_value",
    "prediction_window_days",
    "prior_hash",
)

RESOLVE_HASHED_FIELDS = (
    "entry_type",
    "hypothesis_id",
    "metric",
    "timestamp",
    "outcome",
    "brier_score",
    "metric_actual",
    "metric_predicted",
    "prior_hash",
)

RESOLVE_OPTIONAL_HASHED = ("ratification_hash", "z2_ratified_at")


class LedgerError(RuntimeError):
    """Raised when a ledger cannot be read, or its chain does not validate."""


def compute_entry_hash(entry_data: Dict[str, Any]) -> str:
    """Mirror PRSRunner._compute_entry_hash exactly, so hashes reconcile."""
    return hashlib.sha256(
        json.dumps(entry_data, sort_keys=True).encode()
    ).hexdigest()


def hashed_subset(row: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild the exact dict the engine hashed for this row.

    The engine hashes a fixed field subset. Rows on disk carry extra keys
    (the frozen hypothesis, the calibration block), so verification must
    reconstruct the subset rather than hash the whole row.
    """
    entry_type = row.get("entry_type")
    if entry_type == "PIN":
        return {field: row.get(field) for field in PIN_HASHED_FIELDS}
    if entry_type == "RESOLVE":
        data = {field: row.get(field) for field in RESOLVE_HASHED_FIELDS}
        for field in RESOLVE_OPTIONAL_HASHED:
            if row.get(field):
                data[field] = row[field]
        return data
    raise LedgerError(f"unknown entry_type: {entry_type!r}")


def load_rows(path: Path) -> List[Dict[str, Any]]:
    """Read a JSONL ledger. A missing file is an empty ledger, not an error."""
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise LedgerError(f"{path}:{number}: invalid JSON — {exc}") from exc
    return rows


def append_row(path: Path, row: Dict[str, Any]) -> None:
    """Append one row to the ledger, creating the file if absent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def verify_chain(rows: List[Dict[str, Any]]) -> List[str]:
    """Check every row's hash and its link to the previous row.

    Returns a list of human-readable problems; empty means the chain is intact.
    """
    problems: List[str] = []
    previous_hash: Optional[str] = None
    for index, row in enumerate(rows):
        label = f"row {index + 1} ({row.get('entry_type')} {row.get('hypothesis_id')})"
        if row.get("prior_hash") != previous_hash:
            problems.append(
                f"{label}: prior_hash {row.get('prior_hash')!r} does not match "
                f"previous entry hash {previous_hash!r}"
            )
        try:
            expected = compute_entry_hash(hashed_subset(row))
        except LedgerError as exc:
            problems.append(f"{label}: {exc}")
            previous_hash = row.get("hash")
            continue
        if expected != row.get("hash"):
            problems.append(f"{label}: hash mismatch — recomputed {expected}")
        previous_hash = row.get("hash")
    return problems


def rehydrate(runner: PRSRunner, rows: List[Dict[str, Any]]) -> None:
    """Restore runner state from stored rows without re-emitting entries.

    Hypotheses are rebuilt from the frozen `hypothesis` block on PIN rows,
    which is why this tool stores the whole locked hypothesis rather than
    just its threshold: a preregistration that does not record its own
    locked parameters is not a preregistration.
    """
    for row in rows:
        if row.get("entry_type") == "PIN" and row.get("hypothesis"):
            frozen = row["hypothesis"]
            runner.registered_hypotheses[frozen["hypothesis_id"]] = (
                PreregisteredHypothesis(**frozen)
            )
    runner.nf_ledger_entries = [_RehydratedEntry(row["hash"]) for row in rows]


class _RehydratedEntry:
    """Minimal stand-in so the engine can read `[-1].hash` for chain linking.

    The engine only ever reads `.hash` off prior entries; reconstructing full
    NFLedgerEntry objects would add failure modes for no benefit.
    """

    def __init__(self, entry_hash: str) -> None:
        self.hash = entry_hash


def calibrated_brier(confidence: Optional[float], outcome: str) -> Optional[float]:
    """Proper Brier score from a stated confidence, or None when unavailable.

    VOID outcomes are unscored: a run that produced no signal is not a
    passed prediction and must not be recorded as one.
    """
    if confidence is None or outcome == "VOID":
        return None
    realised = 1.0 if outcome == "EXPECTED" else 0.0
    return round((confidence - realised) ** 2, 6)


def cmd_pin(args: argparse.Namespace) -> int:
    """Commit a prediction before its outcome is known."""
    ledger = Path(args.ledger)
    rows = load_rows(ledger)
    problems = verify_chain(rows)
    if problems:
        print("refusing to pin onto a broken chain:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 2

    runner = PRSRunner()
    rehydrate(runner, rows)
    if args.id in runner.registered_hypotheses:
        print(f"hypothesis already pinned: {args.id}", file=sys.stderr)
        return 2

    hypothesis = PreregisteredHypothesis(
        hypothesis_id=args.id,
        title=args.title or args.id,
        prediction=args.prediction or f"{args.metric} {args.direction} {args.threshold}",
        metric=args.metric,
        threshold=args.threshold,
        direction=args.direction,
        experiment_params=json.loads(args.params) if args.params else {},
        registered_at="",
        registered_sha=args.registered_sha or "",
        prediction_window_days=args.window_days,
    )
    result = runner.register_hypothesis(hypothesis)
    entry = runner.nf_ledger_entries[-1]

    row = asdict(entry)
    row["hypothesis"] = asdict(hypothesis)
    row["calibration"] = {"confidence": args.confidence}
    row["tool"] = {"name": TOOL_NAME, "version": TOOL_VERSION}
    append_row(ledger, row)

    print(json.dumps({"pinned": result, "ledger": str(ledger)}, indent=2))
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve a pinned prediction against its measured outcome."""
    ledger = Path(args.ledger)
    rows = load_rows(ledger)
    problems = verify_chain(rows)
    if problems:
        print("refusing to resolve onto a broken chain:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 2

    runner = PRSRunner()
    rehydrate(runner, rows)
    if args.id not in runner.registered_hypotheses:
        print(f"no pinned hypothesis: {args.id}", file=sys.stderr)
        return 2
    if any(r.get("entry_type") == "RESOLVE" and r.get("hypothesis_id") == args.id
           for r in rows):
        print(f"already resolved: {args.id}", file=sys.stderr)
        return 2

    resolution = runner.resolve_prediction(args.id, args.actual)
    outcome = resolution["outcome"]
    entry = runner._create_resolve_entry(args.id, outcome, args.actual)

    confidence = None
    for row in rows:
        if row.get("entry_type") == "PIN" and row.get("hypothesis_id") == args.id:
            confidence = (row.get("calibration") or {}).get("confidence")

    row = asdict(entry)
    row["calibration"] = {
        "confidence": confidence,
        "brier_calibrated": calibrated_brier(confidence, outcome),
        "note": "engine brier_score pins confidence at 1.0; see module docstring",
    }
    row["tool"] = {"name": TOOL_NAME, "version": TOOL_VERSION}
    append_row(ledger, row)

    print(json.dumps({"resolved": resolution, "calibration": row["calibration"]},
                     indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Validate the hash chain end to end."""
    rows = load_rows(Path(args.ledger))
    problems = verify_chain(rows)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print(json.dumps({"rows": len(rows), "chain": "intact"}, indent=2))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Print the ledger as a JSON array."""
    print(json.dumps(load_rows(Path(args.ledger)), indent=2))
    return 0


def smoke_test() -> int:
    """Pin, resolve, verify, and prove a tampered row is rejected."""
    with tempfile.TemporaryDirectory() as workdir:
        ledger = Path(workdir) / "smoke.jsonl"
        parser = build_parser()
        pin_args = parser.parse_args(
            ["pin", "--ledger", str(ledger), "--id", "H-SMOKE-1",
             "--metric", "startup_minutes", "--threshold", "8",
             "--direction", "lt", "--window-days", "14",
             "--confidence", "0.7"])
        if cmd_pin(pin_args) != 0:
            print("smoke: pin failed", file=sys.stderr)
            return 1

        hit = parser.parse_args(["resolve", "--ledger", str(ledger),
                                 "--id", "H-SMOKE-1", "--actual", "6.5"])
        if cmd_resolve(hit) != 0:
            print("smoke: resolve failed", file=sys.stderr)
            return 1

        rows = load_rows(ledger)
        if len(rows) != 2:
            print(f"smoke: expected 2 rows, got {len(rows)}", file=sys.stderr)
            return 1
        if rows[1]["outcome"] != "EXPECTED":
            print(f"smoke: expected EXPECTED, got {rows[1]['outcome']}", file=sys.stderr)
            return 1
        if rows[1]["calibration"]["brier_calibrated"] != 0.09:
            print("smoke: calibrated brier wrong", file=sys.stderr)
            return 1
        if verify_chain(rows):
            print("smoke: clean chain reported problems", file=sys.stderr)
            return 1

        # A ledger that cannot detect tampering is not an anchor.
        rows[1]["metric_actual"] = 99.0
        if not verify_chain(rows):
            print("smoke: tampered row passed verification", file=sys.stderr)
            return 1

        # A missed prediction must record SURPRISE, not silently pass.
        miss_ledger = Path(workdir) / "miss.jsonl"
        cmd_pin(parser.parse_args(
            ["pin", "--ledger", str(miss_ledger), "--id", "H-SMOKE-2",
             "--metric", "startup_minutes", "--threshold", "8",
             "--direction", "lt", "--window-days", "14", "--confidence", "0.9"]))
        cmd_resolve(parser.parse_args(
            ["resolve", "--ledger", str(miss_ledger), "--id", "H-SMOKE-2",
             "--actual", "20.0"]))
        miss_rows = load_rows(miss_ledger)
        if miss_rows[1]["outcome"] != "SURPRISE":
            print(f"smoke: expected SURPRISE, got {miss_rows[1]['outcome']}",
                  file=sys.stderr)
            return 1
        if miss_rows[1]["calibration"]["brier_calibrated"] != 0.81:
            print("smoke: miss calibrated brier wrong", file=sys.stderr)
            return 1

    print(json.dumps({"smoke_test": "PASS", "tool": TOOL_NAME,
                      "version": TOOL_VERSION}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for all subcommands."""
    parser = argparse.ArgumentParser(
        prog="nf_ledger_cli",
        description="Persistence and command surface for the PRS prediction engine.",
    )
    parser.add_argument("--smoke-test", action="store_true",
                        help="run the self-test and exit")
    subparsers = parser.add_subparsers(dest="command")

    pin = subparsers.add_parser("pin", help="commit a prediction before its outcome")
    pin.add_argument("--ledger", required=True)
    pin.add_argument("--id", required=True)
    pin.add_argument("--metric", required=True)
    pin.add_argument("--threshold", type=float, required=True)
    pin.add_argument("--direction", choices=["gt", "lt", "eq"], required=True)
    pin.add_argument("--window-days", type=int, required=True)
    pin.add_argument("--registered-sha", default="")
    pin.add_argument("--title", default="")
    pin.add_argument("--prediction", default="")
    pin.add_argument("--params", default="",
                     help="locked experiment parameters as a JSON object")
    pin.add_argument("--confidence", type=float, default=None,
                     help="stated probability 0..1; enables a real Brier score")

    resolve = subparsers.add_parser("resolve", help="resolve against a measured outcome")
    resolve.add_argument("--ledger", required=True)
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--actual", type=float, required=True)

    verify = subparsers.add_parser("verify", help="validate the hash chain")
    verify.add_argument("--ledger", required=True)

    export = subparsers.add_parser("export", help="print the ledger as JSON")
    export.add_argument("--ledger", required=True)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Dispatch to a subcommand."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return smoke_test()
    handlers = {
        "pin": cmd_pin,
        "resolve": cmd_resolve,
        "verify": cmd_verify,
        "export": cmd_export,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return handler(args)
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
