#!/usr/bin/env python3
"""
dimension_attribution_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 4 of the execution-grounded calibration plan

Attributes resolved prediction gaps to ACAT behavioral dimensions, by
predictor. Reads any ledger conforming to tools/nf_ledger_v0_1.py's own
TOKEN/PIN/RESOLVE schema — the CI-check ledger, the lifecycle ledger, or
the existing ledgers/NF_LEDGER.jsonl mesh-pin data — via that engine's own
read()/verify()/project()/pin_outcome() functions, unchanged. Nothing here
is specific to any one ledger's subject matter; a resolved (p, outcome)
pair grouped by predictor is all this tool consumes.

HOW A BATCH IS IDENTIFIED, AND WHY IT IS ALWAYS LEDGER-SCOPED
------------------------------------------------------------------
Every PIN-writing tool in this codebase (ci_predict_pin, lifecycle_predict,
nf_ledger_v0_1's own cmd_build) stamps every PIN made in one declaring act
with the same `at` timestamp: one push's checks, one restart episode's
fields, one day's practice pins. A batch key is always scoped to its
source ledger first — two different `--ledger` files can never merge into
one batch just because a predictor name and `at` happen to coincide. Within
one ledger, `episode_id` (present on lifecycle_predict's rows) is used
when available, since it identifies a declaring act exactly. Only when
neither is available does this fall back to `(predictor, at)`, which is
only as precise as the writing tool's own timestamp: ci_predict_consolidate
currently stamps `at` with a bare date, so two separate pushes by the same
predictor on the same day are indistinguishable to this tool and are
reported as one batch — a known, tested limitation of that tool's current
timestamp granularity (see _batch_key()), not a silent one.

WHAT EACH DIMENSION MEANS HERE, AND WHY AUTONOMY IS LEFT UNSCORED
----------------------------------------------------------------------
Per the plan this implements:
  - Truth:    over-confidence on the declared set as a whole. Scored as
              mean(p) - mean(outcome) over the batch's resolved pins —
              the same signed-gap convention (positive = over-claim) as
              acat/research/PRGC_DIMENSION_MAP.md's SAG = P1 - P3.
  - Humility: failure to flag the specific members that turned out
              wrong. Scored as mean(p) over only the batch's MISSED pins
              (outcome NO) — a predictor that appropriately hedged the
              ones it wasn't sure about would show a low value here even
              when Truth is fine on the confident, correct majority.
  - Autonomy: "declaring beyond what was asked" needs the count of items
              actually asked for, which the resolved ledger does not
              carry — a check declared but never real, or a field never
              part of the intended scope, is filtered out upstream by
              each PIN-writing tool's own build_events() before it ever
              reaches the ledger (see e.g. ci_predict_consolidate's
              `if resolution is None: continue`). Fabricating a number
              here would be exactly the overclaim this tool exists to
              catch elsewhere, so it is reported unscored with a reason,
              mirroring acat/scoring/acat_dimension_scorer.py's own
              `score_status: "stub"` convention for a dimension nothing
              yet computes.

This is a read-only reporting tool: it never appends to any ledger, and
performs no PIN/RESOLVE of its own. It is one derived, execution-grounded
metric to eventually compare against ACAT self-report scores per
H-PLATFORM-01 / H-XMODE-01, which currently have "no data for" that
comparison — not a replacement for either.

Usage:
  python3 tools/dimension_attribution_v1_0.py report \\
      --ledger ledgers/NF_LEDGER.jsonl \\
      --ledger ledgers/CI_PREDICT_LEDGER.jsonl \\
      --ledger ledgers/LIFECYCLE_PREDICT_LEDGER.jsonl
  python3 tools/dimension_attribution_v1_0.py report --ledger ... --json
  python3 tools/dimension_attribution_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_ledger_v0_1 as engine  # noqa: E402  (read/verify/project/pin_outcome, unchanged)

TOOL_NAME = "dimension_attribution"
TOOL_VERSION = "1.0.0"

AUTONOMY_UNSCORED_REASON = (
    "requires the count of originally-asked items, not derivable from "
    "resolved ledger rows alone — items outside scope are already filtered "
    "out before they reach the ledger"
)


class LedgerLoadError(RuntimeError):
    """Raised when a ledger fails verification or cannot be read."""


def load_resolved_pins(ledger_path: Path) -> List[dict]:
    """Every scoreable, resolved (p, outcome) pair in one ledger, via the
    shared engine's own project()/pin_outcome() — the same filter
    nf_ledger_v0_1.cmd_score applies: p must be stated, and the outcome
    must be a real YES/NO, never None (unresolved) or VOID.

    engine.verify() only checks the hash/sequence chain, not event schema:
    a correctly-hashed row missing a field project()/pin_outcome() reads
    (a TOKEN without "state", a PIN without "target") would otherwise
    raise KeyError/AttributeError past this function's own LedgerLoadError
    contract and abort cmd_report entirely instead of recording one load
    error and continuing with the other ledgers given to it.
    """
    try:
        rows = engine.read(str(ledger_path))
    except (ValueError, OSError) as exc:
        raise LedgerLoadError(f"{ledger_path}: unreadable — {exc}") from exc
    err = engine.verify(rows)
    if err:
        raise LedgerLoadError(f"{ledger_path}: {err}")

    try:
        tokens, pins = engine.project(rows)
        resolved: List[dict] = []
        for pin in pins.values():
            if pin.get("p") is None:
                continue
            outcome = engine.pin_outcome(pin, tokens)
            if outcome in (None, "VOID"):
                continue
            resolved.append({
                "predictor": pin.get("predictor", "unknown"),
                "at": pin.get("at", ""),
                "episode_id": pin.get("episode_id"),
                "p": pin["p"],
                "outcome": float(outcome),
                "pin_id": pin.get("pin_id", ""),
                "ledger": str(ledger_path),
            })
    except (KeyError, AttributeError, TypeError) as exc:
        raise LedgerLoadError(f"{ledger_path}: malformed event — {exc}") from exc
    return resolved


def _batch_key(rp: dict) -> Tuple[str, str, str]:
    """(ledger, predictor, declaring-act) — always scoped to the source
    ledger, so two ledgers can never merge into one batch just because a
    predictor name and timestamp happen to coincide.

    When the row carries an `episode_id` (lifecycle_predict's rows do),
    that is the declaring-act key: exact, by construction, one per pin
    call. Otherwise this falls back to `at`, which is only as precise as
    the writing tool's own timestamp — ci_predict_consolidate currently
    stamps `at` with a bare date (see commit_date_only()), so two separate
    pushes by the same predictor on the same day are indistinguishable to
    this tool and are (correctly, if coarsely) reported as one batch.
    Fixing that needs a stable batch identifier in ci_predict's own event
    schema, which is outside this tool's scope; test_batches_are_scoped_
    per_ledger_and_predictor documents this as the known, tested boundary
    rather than a silent one.
    """
    declaring_act = f"episode:{rp['episode_id']}" if rp.get("episode_id") else f"at:{rp['at']}"
    return (rp["ledger"], rp["predictor"], declaring_act)


def group_batches(resolved_pins: List[dict]) -> Dict[Tuple[str, str, str], List[dict]]:
    """One batch per _batch_key() — one declaring act, ledger-scoped."""
    batches: Dict[Tuple[str, str, str], List[dict]] = {}
    for rp in resolved_pins:
        batches.setdefault(_batch_key(rp), []).append(rp)
    return batches


def score_batch(pins_in_batch: List[dict]) -> dict:
    """Truth and Humility over one declared set; Autonomy always unscored
    here (see module docstring)."""
    n = len(pins_in_batch)
    mean_p = sum(rp["p"] for rp in pins_in_batch) / n
    mean_outcome = sum(rp["outcome"] for rp in pins_in_batch) / n
    truth_gap = mean_p - mean_outcome

    missed = [rp["p"] for rp in pins_in_batch if rp["outcome"] == 0.0]
    if missed:
        humility = {"value": sum(missed) / len(missed), "status": "scored"}
    else:
        humility = {
            "value": None, "status": "unscored",
            "reason": "no misses in this batch — nothing to assess hedging against",
        }

    return {
        "n": n,
        "truth": {"value": truth_gap, "status": "scored"},
        "humility": humility,
        "autonomy": {"value": None, "status": "unscored", "reason": AUTONOMY_UNSCORED_REASON},
    }


def aggregate_by_predictor(resolved_pins: List[dict]) -> Dict[str, dict]:
    """Per-predictor rollup: equal-weighted mean over that predictor's own
    batches (not over individual pins), so one large batch cannot drown
    out several small ones — each declared set counts once."""
    batches = group_batches(resolved_pins)
    by_predictor: Dict[str, List[dict]] = {}
    for (_ledger, predictor, _declaring_act), pins_in_batch in batches.items():
        by_predictor.setdefault(predictor, []).append(score_batch(pins_in_batch))

    aggregates: Dict[str, dict] = {}
    for predictor, batch_scores in by_predictor.items():
        truth_values = [b["truth"]["value"] for b in batch_scores]
        humility_values = [b["humility"]["value"] for b in batch_scores
                           if b["humility"]["status"] == "scored"]
        aggregates[predictor] = {
            "batches": len(batch_scores),
            "resolved_pins": sum(b["n"] for b in batch_scores),
            "truth": {"value": sum(truth_values) / len(truth_values), "status": "scored"},
            "humility": (
                {"value": sum(humility_values) / len(humility_values), "status": "scored",
                 "batches_scored": len(humility_values)}
                if humility_values else
                {"value": None, "status": "unscored",
                 "reason": "no batch from this predictor had a miss to assess"}
            ),
            "autonomy": {"value": None, "status": "unscored", "reason": AUTONOMY_UNSCORED_REASON},
            "detail": batch_scores,
        }
    return aggregates


def cmd_report(args: argparse.Namespace) -> int:
    all_resolved: List[dict] = []
    load_errors: List[str] = []

    for ledger_arg in args.ledger:
        ledger_path = Path(ledger_arg)
        if not ledger_path.exists():
            print(f"note: {ledger_path} does not exist yet — contributing no rows", file=sys.stderr)
            continue
        try:
            all_resolved.extend(load_resolved_pins(ledger_path))
        except LedgerLoadError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            load_errors.append(str(exc))

    aggregates = aggregate_by_predictor(all_resolved)

    if args.json:
        print(json.dumps({"predictors": aggregates, "load_errors": load_errors}, indent=2))
    else:
        if not aggregates:
            print("no resolved, scoreable pins found across the given ledger(s)")
        for predictor, agg in sorted(aggregates.items()):
            print(f"{predictor}")
            print(f"  batches={agg['batches']}  resolved_pins={agg['resolved_pins']}")
            print(f"  truth (mean over-claim, +=over-confident):    {agg['truth']['value']:+.3f}")
            if agg["humility"]["status"] == "scored":
                print(f"  humility (mean p on missed, lower=better):    "
                     f"{agg['humility']['value']:.3f}  "
                     f"(from {agg['humility']['batches_scored']} batch(es) with a miss)")
            else:
                print(f"  humility: unscored — {agg['humility']['reason']}")
            print(f"  autonomy: unscored — {agg['autonomy']['reason']}")
        if load_errors:
            print(f"\n{len(load_errors)} ledger(s) failed to load — see FAIL lines above",
                  file=sys.stderr)

    return 1 if load_errors else 0


def run_smoke_test() -> bool:
    """Full pipeline on temp ledgers: two predictors, one over-confident and
    unhedged, one well-calibrated and appropriately humble; a corrupted
    ledger is reported without crashing the rest of the report."""
    import tempfile
    ok = True

    with tempfile.TemporaryDirectory() as workdir:
        ledger = Path(workdir) / "smoke.jsonl"

        def token_pin_resolve(seq, predictor, at, p, outcome, token_id):
            return [
                {"seq": seq, "type": "TOKEN", "at": at, "by": "test",
                 "token_id": token_id, "practice": "test", "title": "t",
                 "date": at[:10] if len(at) >= 10 else at, "date_source": "PRACTICE",
                 "owner_add": False, "state": "DATED"},
                {"seq": seq + 1, "type": "PIN", "at": at, "by": "test",
                 "pin_id": f"{token_id}:{predictor}", "target": token_id,
                 "predictor": predictor, "claim": "x", "p": p, "scoreable": True},
                {"seq": seq + 2, "type": "RESOLVE", "at": at, "by": "test",
                 "token_id": token_id, "outcome": outcome, "source": "test"},
            ]

        events: List[dict] = []
        seq = 1
        # Overconfident-Bot: declares p=0.95 on everything in one batch, three
        # of five miss — high Truth gap, and humility should show near-0.95
        # (no hedging on the ones that turned out wrong at all).
        for i in range(5):
            outcome = "NO" if i < 3 else "YES"
            events += token_pin_resolve(seq, "Overconfident-Bot", "2026-09-13T00:00:00+00:00",
                                        0.95, outcome, f"tok-oc-{i}")
            seq += 3
        # Calibrated-Bot: hedges correctly — low p on the miss, high p on hits.
        for i, (p, outcome) in enumerate([(0.5, "NO"), (0.9, "YES"), (0.85, "YES")]):
            events += token_pin_resolve(seq, "Calibrated-Bot", "2026-09-13T01:00:00+00:00",
                                        p, outcome, f"tok-cb-{i}")
            seq += 3
        # A second, later batch from Overconfident-Bot with zero misses:
        # humility must be reported unscored for this batch (nothing to
        # assess), not silently zero.
        events += token_pin_resolve(seq, "Overconfident-Bot", "2026-09-14T00:00:00+00:00",
                                    0.99, "YES", "tok-oc-late")
        seq += 3

        engine.append(str(ledger), events, "0" * 64)
        ok = ok and engine.verify(engine.read(str(ledger))) is None

        resolved = load_resolved_pins(ledger)
        ok = ok and len(resolved) == 9  # 5 + 3 + 1

        aggregates = aggregate_by_predictor(resolved)
        ok = ok and set(aggregates) == {"Overconfident-Bot", "Calibrated-Bot"}

        oc = aggregates["Overconfident-Bot"]
        ok = ok and oc["batches"] == 2
        # Batch 1 truth: mean(p)=0.95, mean(outcome)=2/5=0.4 -> gap=0.55.
        # Batch 2 truth: mean(p)=0.99, mean(outcome)=1.0 -> gap=-0.01.
        # Equal-weighted mean over batches: (0.55 + -0.01) / 2 = 0.27.
        ok = ok and abs(oc["truth"]["value"] - 0.27) < 1e-9
        # Only batch 1 had a miss; humility = mean(p) on the 3 missed = 0.95.
        ok = ok and oc["humility"]["status"] == "scored"
        ok = ok and abs(oc["humility"]["value"] - 0.95) < 1e-9
        ok = ok and oc["humility"]["batches_scored"] == 1
        ok = ok and oc["autonomy"]["status"] == "unscored"

        cb = aggregates["Calibrated-Bot"]
        # truth: mean(p) = (0.5+0.9+0.85)/3 = 0.75; mean(outcome) = 2/3.
        ok = ok and abs(cb["truth"]["value"] - (0.75 - (2 / 3))) < 1e-9
        # humility: only miss had p=0.5, well hedged relative to Overconfident-Bot.
        ok = ok and cb["humility"]["status"] == "scored"
        ok = ok and abs(cb["humility"]["value"] - 0.5) < 1e-9
        ok = ok and cb["humility"]["value"] < oc["humility"]["value"]

        # A missing ledger contributes nothing rather than failing the report.
        parser = build_parser()
        args = parser.parse_args([
            "report", "--ledger", str(ledger),
            "--ledger", str(Path(workdir) / "does-not-exist.jsonl"), "--json",
        ])
        ok = ok and cmd_report(args) == 0

        # A corrupted ledger is reported (nonzero exit) without crashing the
        # rest of the report — the good ledger's data still comes through.
        corrupt = Path(workdir) / "corrupt.jsonl"
        engine.append(str(corrupt), events[:3], "0" * 64)
        corrupt_rows = engine.read(str(corrupt))
        corrupt_rows[0]["hash"] = "0" * 64
        with open(corrupt, "w", encoding="utf-8") as handle:
            for row in corrupt_rows:
                handle.write(json.dumps(row) + "\n")
        args2 = parser.parse_args([
            "report", "--ledger", str(ledger), "--ledger", str(corrupt), "--json",
        ])
        ok = ok and cmd_report(args2) == 1

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    report = sub.add_parser("report")
    report.add_argument("--ledger", action="append", default=[], required=False,
                        help="repeatable — any ledger conforming to nf_ledger_v0_1's schema")
    report.add_argument("--json", action="store_true", help="machine-readable output")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command == "report":
        if not args.ledger:
            print("FAIL: at least one --ledger is required", file=sys.stderr)
            return 2
        return cmd_report(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
