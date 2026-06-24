#!/usr/bin/env python3
"""
Corpus Integrity Validator — v1.1
Builder v1.7 compliant · validation_tool
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Validates ACAT corpus CSV export against schema requirements.
Checks every row for missing fields, out-of-range scores,
LI calculation correctness, mode field validity, Phase pairing,
and cross-row D-04 monotonicity (LI must not regress within agent arc).

Usage:
python corpus_integrity_validator.py --input acat_corpus.csv
python corpus_integrity_validator.py --input acat_corpus.csv --strict
python corpus_integrity_validator.py --smoke-test
"""

import csv
import json
import sys
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "corpus_integrity_validator"
TOOL_VERSION = "1.1.0"

REQUIRED_COLUMNS = [
    "agent_name", "layer", "truth", "service", "harm", "autonomy",
    "value", "humility", "total", "phase", "pre_total", "post_total",
    "learning_index", "mode", "timestamp"
]
SCORE_COLUMNS = ["truth", "service", "harm", "autonomy", "value", "humility"]
VALID_PHASES = {"Phase 1", "Phase 3", "phase1", "phase3", "P1", "P3"}
VALID_MODES = {
    "EMPIRICAL", "RETROSPECTIVE_ANALYTICAL", "CROSS_SUBSTRATE", "SELF_REPORT",
    "empirical", "retrospective_analytical", "cross_substrate", "self_report"
}
CORPUS_MEAN_LI = 0.8632
LI_RECALC_TOLERANCE = 0.005  # allow small floating-point rounding


class SpecLoadFailed(Exception):
    pass


def load_corpus(path: str) -> list:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        rows = []
        with open(p, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        if not rows:
            raise SpecLoadFailed("Corpus file is empty")
        return rows
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


def validate_schema(rows: list) -> dict:
    if not rows:
        return {"passed": False, "failures": ["EMPTY_CORPUS"]}
    headers = set(rows[0].keys())
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        return {"passed": False, "failures": [f"MISSING_COLUMN: {c}" for c in missing]}
    return {"passed": True, "failures": [], "headers": list(headers)}


def _safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def validate_rows(rows: list, strict: bool = False) -> dict:
    failures = []
    warnings = []
    li_values = []

    for i, row in enumerate(rows):
        row_id = f"row_{i+1}_{row.get('agent_name', 'unknown')}"

        # Score range check
        for col in SCORE_COLUMNS:
            val = row.get(col, "")
            score = _safe_float(val)
            if score is None:
                if val:
                    failures.append(f"INVALID_{col.upper()}: {row_id} value='{val}'")
            elif not (0 <= score <= 100):
                failures.append(f"RANGE_{col.upper()}: {row_id} score={score}")

        # LI range check
        li_val = row.get("learning_index", "")
        li = _safe_float(li_val)
        if li is None:
            if li_val:
                failures.append(f"INVALID_LI: {row_id} value='{li_val}'")
        else:
            li_values.append(li)
            if li < 0 or li > 2.0:
                warnings.append(f"LI_OUTLIER: {row_id} LI={li}")

        # LI recalculation verification — NEW in v1.1
        # For Phase 3 rows: verify learning_index = post_total / pre_total
        phase = row.get("phase", "")
        if phase in {"Phase 3", "phase3", "P3"}:
            pre = _safe_float(row.get("pre_total"))
            post = _safe_float(row.get("post_total"))
            declared_li = _safe_float(row.get("learning_index"))
            if pre and pre > 0 and post is not None and declared_li is not None:
                recalc_li = round(post / pre, 4)
                if abs(recalc_li - declared_li) > LI_RECALC_TOLERANCE:
                    failures.append(
                        f"LI_RECALC_MISMATCH: {row_id} declared={declared_li} "
                        f"recalculated={recalc_li} (post={post}/pre={pre})"
                    )

        # Mode field validity
        mode = row.get("mode", "")
        if mode and mode not in VALID_MODES:
            if strict:
                failures.append(f"INVALID_MODE: {row_id} mode='{mode}'")
            else:
                warnings.append(f"WARN_MODE: {row_id} mode='{mode}' not in recognized set")

        # Agent name present
        if not row.get("agent_name", "").strip():
            failures.append(f"MISSING_AGENT_NAME: {row_id}")

    # Cross-row D-04 monotonicity check — NEW in v1.1
    # Within each agent: Phase 3 LI values must not regress session-over-session
    agent_phase3_li = defaultdict(list)
    for row in rows:
        phase = row.get("phase", "")
        if phase not in {"Phase 3", "phase3", "P3"}:
            continue
        agent = row.get("agent_name", "")
        li = _safe_float(row.get("learning_index"))
        if agent and li is not None:
            agent_phase3_li[agent].append(li)

    for agent, lis in agent_phase3_li.items():
        if len(lis) >= 3:
            # Flag if LI regresses by more than 0.10 from a prior local maximum
            local_max = lis[0]
            for j, val in enumerate(lis[1:], 1):
                if val > local_max:
                    local_max = val
                elif local_max - val > 0.10:
                    warnings.append(
                        f"D04_LI_REGRESSION: agent={agent} session_{j} LI={val:.4f} "
                        f"regressed from local_max={local_max:.4f} (>0.10 drop)"
                    )

    # Phase pairing check — NEW in v1.1
    # Every agent should have at least one Phase 1 row if they have Phase 3 rows
    agent_phases = defaultdict(set)
    for row in rows:
        agent = row.get("agent_name", "")
        phase = row.get("phase", "")
        if phase in {"Phase 1", "phase1", "P1"}:
            agent_phases[agent].add("P1")
        elif phase in {"Phase 3", "phase3", "P3"}:
            agent_phases[agent].add("P3")

    for agent, phases in agent_phases.items():
        if "P3" in phases and "P1" not in phases:
            warnings.append(
                f"PHASE_PAIRING_MISSING: agent={agent} has Phase 3 rows but no Phase 1 baseline"
            )

    # Summary stats
    stats = {}
    if li_values:
        stats["n_rows"] = len(rows)
        stats["n_li_valid"] = len(li_values)
        stats["mean_li"] = round(sum(li_values) / len(li_values), 4)
        stats["li_above_mean"] = sum(1 for l in li_values if l > CORPUS_MEAN_LI)
        stats["n_agents"] = len(agent_phases)
        stats["agents_with_phase_pairing_gap"] = sum(
            1 for a, p in agent_phases.items() if "P3" in p and "P1" not in p
        )

    return {
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
        "stats": stats
    }


def aggregate(schema, rows_result) -> dict:
    all_failures = schema.get("failures", []) + rows_result.get("failures", [])
    verdict = "PASS" if not all_failures else "FAIL"
    return {
        "result": verdict,
        "status": verdict,
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hard_failures": all_failures,
        "warnings": rows_result.get("warnings", []),
        "corpus_stats": rows_result.get("stats", {})
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"corpus_integrity_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    border = "═" * 56
    stats = output.get("corpus_stats", {})
    print(f"\n{border}")
    print(f" Corpus Integrity Validator · {TOOL_VERSION}")
    print(f" Verdict: {output['result']}")
    if stats:
        print(f" Rows: {stats.get('n_rows', 'N/A')}")
        print(f" LI valid: {stats.get('n_li_valid', 'N/A')}")
        print(f" Mean LI: {stats.get('mean_li', 'N/A')}")
        print(f" Agents: {stats.get('n_agents', 'N/A')}")
        gap = stats.get("agents_with_phase_pairing_gap", 0)
        if gap:
            print(f" ⚠ Agents missing Phase 1 baseline: {gap}")
    if output["hard_failures"]:
        print(f"\n FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"][:10]:
            print(f"  ✗ {f}")
        if len(output["hard_failures"]) > 10:
            print(f"  ... and {len(output['hard_failures'])-10} more")
    if output["warnings"]:
        print(f"\n WARNINGS: {len(output['warnings'])}")
    print(f"\n{border}\n")


def run_smoke_test() -> bool:
    import tempfile, os
    test_rows = [
        {"agent_name": "TestAgent", "layer": "test", "truth": "85", "service": "86",
         "harm": "84", "autonomy": "87", "value": "85", "humility": "83",
         "total": "510", "phase": "Phase 1", "pre_total": "510", "post_total": "510",
         "learning_index": "0.85", "mode": "EMPIRICAL", "timestamp": "2026-05-12", "metadata": ""},
        {"agent_name": "TestAgent", "layer": "test", "truth": "86", "service": "87",
         "harm": "85", "autonomy": "88", "value": "86", "humility": "84",
         "total": "516", "phase": "Phase 3", "pre_total": "510", "post_total": "516",
         "learning_index": "1.0118", "mode": "EMPIRICAL", "timestamp": "2026-05-12", "metadata": ""},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS + ["metadata"])
        writer.writeheader()
        writer.writerows(test_rows)
        tmp = f.name
    try:
        rows = load_corpus(tmp)
        schema = validate_schema(rows)
        row_results = validate_rows(rows)
        output = aggregate(schema, row_results)
        assert "result" in output
        assert "status" in output
        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    finally:
        os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description="Corpus Integrity Validator v1.1")
    parser.add_argument("--input", "-i", help="Path to corpus CSV")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        rows = load_corpus(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    schema = validate_schema(rows)
    row_results = validate_rows(rows, args.strict)
    output = aggregate(schema, row_results)
    report_path = write_report(output, args.output)
    print_summary(output)
    print(f"Report written: {report_path}")
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
