#!/usr/bin/env python3
"""
scheduled_audit_runner_v1_0 — Measure+Issue automated audit loop orchestrator
TYPE: tool
Builder v1.7 compliant · audit_loop_orchestrator
HumanAIOS · S-070726

Runs the audit instruments, applies RESEARCH-FINDING GATES, and emits a summary +
a `gate_tripped` flag for the scheduled-audit workflow to open an issue.

Autonomy level: **MEASURE + ISSUE**. This orchestrator NEVER dispatches work to a
substrate and NEVER merges. It measures and reports; a human triages the issue and
decides dispatch/merge. Widen autonomy only once smag_pilot data earns it.

The gates are the project's own research instruments (not arbitrary thresholds):
  - findings-registry integrity   (registered_findings_validator_v1_0.py, non-strict)
  - behavioral compliance          (behavioral_compliance_gate_v1_0.py, --min-pass-rate)
Additional instruments can be appended to GATES as they become repo-portable.

Usage:
  python3 scheduled_audit_runner_v1_0.py --repo-root . --output outputs/
  python3 scheduled_audit_runner_v1_0.py --smoke-test
Exit code is ALWAYS 0 (measure step must not redden the scheduled run); the
`gate_tripped` flag drives issue creation in the workflow.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "scheduled_audit_runner"
TOOL_VERSION = "1.0.0"

# Each gate: (name, argv builder given repo_root, report-glob, extractor)
# extractor(exit_code, report_dict|None) -> (tripped: bool, detail: str)


def _findings_extract(exit_code, report):
    hard = len(report.get("hard_failures", [])) if report else None
    if hard is None:
        return (exit_code != 0, f"exit {exit_code}, report unreadable")
    return (hard > 0, f"{hard} hard failures")


def _behavioral_extract(exit_code, report):
    rate = report.get("pass_rate") if report else None
    if rate is None:
        return (exit_code != 0, f"exit {exit_code}, report unreadable")
    return (exit_code != 0, f"pass_rate={rate}")


GATES = [
    {
        "name": "findings-registry-integrity",
        "argv": lambda root: [
            sys.executable, f"{root}/tools/registered_findings_validator_v1_0.py",
            "--input", f"{root}/REGISTERED.md", "--output", "{out}",
        ],
        "glob": "registered_findings_*.json",
        "extract": _findings_extract,
    },
    {
        # Regression floor, not an absolute bar: trips only if the full-suite
        # behavioral pass-rate drops BELOW the recorded baseline. This is the
        # "gate based on a research finding" — the baseline IS the finding.
        # RATCHET: raise BEHAVIORAL_FLOOR as the legacy backlog is remediated.
        "name": "behavioral-compliance",
        "argv": lambda root: [
            sys.executable, f"{root}/tools/behavioral_compliance_gate_v1_0.py",
            "--path", f"{root}/tools", "--min-pass-rate", BEHAVIORAL_FLOOR,
            "--output", "{out}",
        ],
        "glob": "behavioral_compliance_*.json",
        "extract": _behavioral_extract,
    },
]

# Regression floor for the full-tool-suite behavioral pass-rate. Current measured
# baseline (S-070726) ≈ 0.73 (legacy backlog); floor set just below so the loop
# catches regressions, not the standing debt. Ratchet up as tools are fixed.
BEHAVIORAL_FLOOR = "0.70"


def _latest_report(out_dir: str, pattern: str):
    matches = sorted(glob.glob(os.path.join(out_dir, pattern)))
    if not matches:
        return None
    try:
        with open(matches[-1], encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def run_gate(gate: dict, repo_root: str, out_dir: str) -> dict:
    """Run one instrument; return its gate result. Never raises."""
    argv = [a.replace("{out}", out_dir) for a in gate["argv"](repo_root)]
    result = {"name": gate["name"], "status": "ERROR", "detail": "", "exit_code": None}
    if len(argv) > 1 and not os.path.exists(argv[1]):
        result["detail"] = "instrument not present (skipped)"
        result["status"] = "SKIP"
        return result
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=300)
        result["exit_code"] = proc.returncode
        report = _latest_report(out_dir, gate["glob"])
        tripped, detail = gate["extract"](proc.returncode, report)
        result["status"] = "TRIP" if tripped else "PASS"
        result["detail"] = detail
    except FileNotFoundError:
        result["detail"] = "instrument not present (skipped)"
        result["status"] = "SKIP"
    except subprocess.TimeoutExpired:
        result["detail"] = "timed out"
        result["status"] = "ERROR"
    return result


def build_summary(results: list, when: str) -> str:
    tripped = [r for r in results if r["status"] == "TRIP"]
    lines = [
        f"# Automated audit — {when}",
        "",
        f"**Autonomy:** measure + issue (no dispatch, no merge). "
        f"**Gates tripped:** {len(tripped)}/{len(results)}.",
        "",
        "| Gate | Status | Detail |",
        "|---|---|---|",
    ]
    for r in results:
        mark = {"PASS": "✅", "TRIP": "⛔", "SKIP": "➖", "ERROR": "⚠️"}.get(r["status"], "?")
        lines.append(f"| {r['name']} | {mark} {r['status']} | {r['detail']} |")
    if tripped:
        lines += ["", "## Action", "A research-finding gate tripped. Human triage: "
                  "confirm, then dispatch a fix (issue → substrate) — this loop does NOT "
                  "dispatch or merge on its own."]
    return "\n".join(lines) + "\n"


def emit_github_output(gate_tripped: bool, summary_path: str) -> None:
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if not gh_out:
        return
    with open(gh_out, "a", encoding="utf-8") as fh:
        fh.write(f"gate_tripped={'true' if gate_tripped else 'false'}\n")
        fh.write(f"summary_path={summary_path}\n")


def run(repo_root: str, out_dir: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = [run_gate(g, repo_root, out_dir) for g in GATES]
    gate_tripped = any(r["status"] == "TRIP" for r in results)
    summary = build_summary(results, when)
    summary_path = os.path.join(out_dir, "scheduled_audit_summary.md")
    Path(summary_path).write_text(summary, encoding="utf-8")
    Path(os.path.join(out_dir, "scheduled_audit_result.json")).write_text(
        json.dumps({"when": when, "gate_tripped": gate_tripped, "gates": results}, indent=2),
        encoding="utf-8",
    )
    print(summary)
    emit_github_output(gate_tripped, summary_path)
    return 0


def run_smoke_test() -> bool:
    """Smoke test: summary builder + extractors behave on synthetic input."""
    ok = True
    t, _ = _findings_extract(1, {"hard_failures": [1, 2]})
    ok = ok and t is True
    t2, _ = _findings_extract(0, {"hard_failures": []})
    ok = ok and t2 is False
    s = build_summary([{"name": "x", "status": "PASS", "detail": "ok", "exit_code": 0}], "now")
    ok = ok and "Automated audit" in s and "measure + issue" in s
    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output", default="outputs")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    return run(args.repo_root, args.output)


if __name__ == "__main__":
    sys.exit(main())
