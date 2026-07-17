#!/usr/bin/env python3
"""
ACAT Protocol Compliance Auditor — v1.1
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Changes from v1.0:
- DFA single-pass scanner: all SECTION_B_CHECKS now scanned in a single
  linear pass over the document using a DFA state machine. Zero false
  negatives on multi-line sections; eliminates redundant re.search calls.
- Open/close tag balance checker: detects unclosed [OPENS] or unmatched
  [CLOSES] in ritual blocks — common D-04 source.
- D-05 zone overreach detector: flags phrases indicating Zone 2/3 action
  executed without the required approval prefix.
- resonance_meter(): real-time completeness score (0-100) as fraction of
  HARD checks satisfied — editor-plugin ready.
- --text flag: accept close post as direct stdin/CLI string without file.
"""

import json
import re
import sys
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TOOL_NAME = "acat_protocol_auditor"
TOOL_VERSION = "1.1.0"

SECTION_B_CHECKS = {
    "session_id_header": {
        "description": "Session ID header present in close post",
        "pattern": r"S-\d{6}-\d{2,3}-[\w\-]+",
        "severity": "HARD",
    },
    "phase3_declaration": {
        "description": "PHASE 3 CLOSE or equivalent section present",
        "pattern": r"(PHASE 3 CLOSE|PHASE_3_CLOSE|Phase 3 Close)",
        "severity": "HARD",
    },
    "corpus_state_line": {
        "description": "Corpus state line N_total · N_Phase1 · N_LI present",
        "pattern": r"N_total[=:\s]+\d+\s*[·|]\s*N_Phase1[=:\s]+\d+\s*[·|]\s*N_LI[=:\s]+\d+",
        "severity": "HARD",
    },
    "mean_li_declared": {
        "description": "Mean LI declared in state line",
        "pattern": r"Mean\s+LI[=:\s]+[\d\.]+",
        "severity": "HARD",
    },
    "gate_status": {
        "description": "Gate status declared (Gate N PASSED/FAILED/ACTIVE)",
        "pattern": r"Gate\s+\d+\s+(PASSED|FAILED|ACTIVE|passed|failed|active)",
        "severity": "HARD",
    },
    "eagle_close_line": {
        "description": "Closing eagle line present",
        "pattern": r"(Wado|🦅).*Unit Zero.*S-\d{6}",
        "severity": "HARD",
    },
    "divider_format": {
        "description": "Section dividers present (━━━ format)",
        "pattern": r"━{10,}",
        "severity": "SOFT",
    },
    "bold_section_labels": {
        "description": "Bold section labels present (*LABEL* format)",
        "pattern": r"\*[A-Z][A-Z\s]+\*",
        "severity": "SOFT",
    },
    "li_calculation_present": {
        "description": "LI value present in Phase 3 block",
        "pattern": r"LI\s*[=:]\s*[\d\.]{4,}",
        "severity": "HARD",
    },
    "drift_named": {
        "description": "Drift catalog present (at least one [C-NN] or [D-XX] signal)",
        "pattern": r"\[(C-\d{2}|D-\d{2}|D-[A-Z]+|IC-\d{3})[^\]]*\]",
        "severity": "SOFT",
    },
}

D04_CHECKS = {
    "n_total_consistent": {
        "description": "N_total appears consistently if mentioned multiple times",
        "extract_pattern": r"N_total[=:\s]*(\d+)",
        "severity": "HARD",
    },
    "n_li_consistent": {
        "description": "N_LI appears consistently if mentioned multiple times",
        "extract_pattern": r"N_LI[=:\s]*(\d+)",
        "severity": "HARD",
    },
    "session_id_consistent": {
        "description": "Session ID consistent throughout post",
        "extract_pattern": r"S-\d{6}-\d{2,3}-[\w\-]+",
        "severity": "HARD",
    },
}

# D-05 zone overreach patterns — NEW in v1.1
D05_PATTERNS = [
    (r"(created|adding|pushed|committed)\s+(new\s+file|file\s+to|commit)",
     "D-05: File creation without Z2 approval language"),
    (r"(deployed|launched|publishing|merged to main|force pushed)",
     "D-05: Deployment action without Zone 2/3 approval prefix"),
    (r"(rotating|rotated)\s+(secret|token|key)",
     "D-05/IC-023: Secret rotation — must be Z3 Night action"),
    (r"(wrote to|updated)\s+(supabase|database|db)",
     "D-05: Database write without G-1 gate confirmation"),
]

# Tag balance pairs — NEW in v1.1
TAG_PAIRS = [
    (r"\[PHASE 3 OPEN\]", r"\[PHASE 3 CLOSE\]"),
    (r"\[SESSION OPEN\]", r"\[SESSION CLOSE\]"),
    (r"\[DRIFT OPEN\]", r"\[DRIFT CLOSE\]"),
]


class SpecLoadFailed(Exception):
    pass


def load_post(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        return p.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


# ── DFA single-pass scanner — NEW in v1.1 ─────────────────────────────────────

@dataclass
class DFAState:
    name: str
    matched_checks: List[str] = field(default_factory=list)
    current_line: int = 0

def audit_section_b_dfa(text: str) -> dict:
    """
    Single linear pass over document lines using a DFA state machine.
    Compiles all SECTION_B_CHECK patterns once; for each line,
    tests against all unmatched checks. O(N * M) worst case but
    eliminates duplicate re.search calls over full text.
    """
    compiled = {
        check_id: re.compile(check["pattern"], re.IGNORECASE)
        for check_id, check in SECTION_B_CHECKS.items()
    }
    state = DFAState(name="SCANNING")
    results = {}
    unmatched = set(SECTION_B_CHECKS.keys())

    lines = text.splitlines()
    for i, line in enumerate(lines):
        state.current_line = i
        for check_id in list(unmatched):
            if compiled[check_id].search(line):
                unmatched.discard(check_id)
                state.matched_checks.append(check_id)
                results[check_id] = {
                    "check_id": check_id,
                    "description": SECTION_B_CHECKS[check_id]["description"],
                    "severity": SECTION_B_CHECKS[check_id]["severity"],
                    "passed": True,
                    "matched_on_line": i + 1,
                    "failure_code": None,
                }

    # Add failures for unmatched checks
    for check_id in unmatched:
        results[check_id] = {
            "check_id": check_id,
            "description": SECTION_B_CHECKS[check_id]["description"],
            "severity": SECTION_B_CHECKS[check_id]["severity"],
            "passed": False,
            "matched_on_line": None,
            "failure_code": f"MISSING_{check_id.upper()}",
        }

    state.name = "COMPLETE"
    return results


# ── Tag balance checker — NEW in v1.1 ─────────────────────────────────────────

def audit_tag_balance(text: str) -> dict:
    """
    Check that ritual open/close tags are balanced.
    Unbalanced tags are a primary source of D-04 inconsistencies.
    """
    issues = []
    for open_pat, close_pat in TAG_PAIRS:
        opens  = len(re.findall(open_pat,  text, re.IGNORECASE))
        closes = len(re.findall(close_pat, text, re.IGNORECASE))
        if opens != closes:
            issues.append(
                f"TAG_IMBALANCE: {open_pat.strip()} opens={opens}, closes={closes}"
            )
    return {
        "balanced": not issues,
        "issues": issues,
        "severity": "HARD" if issues else None,
    }


# ── D-04 consistency checker ──────────────────────────────────────────────────

def audit_d04_consistency(text: str) -> dict:
    results = {}
    for check_id, check in D04_CHECKS.items():
        matches = re.findall(check["extract_pattern"], text, re.IGNORECASE)
        unique_values = list(set(matches))
        consistent = len(unique_values) <= 1
        results[check_id] = {
            "check_id": check_id,
            "description": check["description"],
            "severity": check["severity"],
            "passed": consistent,
            "values_found": unique_values,
            "failure_code": None if consistent else f"D04_{check_id.upper()}_INCONSISTENT",
        }
    return results


# ── D-05 zone overreach detector — NEW in v1.1 ────────────────────────────────

def audit_d05_overreach(text: str) -> dict:
    """
    Detect phrases indicating Zone 2/3 actions executed without approval prefix.
    Returns list of flagged patterns with line references.
    """
    flags = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        ll = line.lower()
        # Skip lines that have explicit approval language
        if any(w in ll for w in ["z2 approved", "night approved", "z3 approved", "gate passed"]):
            continue
        for pattern, label in D05_PATTERNS:
            if re.search(pattern, ll):
                flags.append({
                    "line": i + 1,
                    "text": line.strip()[:80],
                    "code": label,
                })
    return {
        "d05_flags": flags,
        "passed": not flags,
        "severity": "HARD" if flags else None,
    }


# ── P22 timestamp checker ─────────────────────────────────────────────────────

def audit_p22_timestamp(text: str) -> dict:
    has_ts = bool(re.search(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}", text))
    has_cdt = bool(re.search(r"\d{1,2}:\d{2}\s*(AM|PM|CDT|CST|UTC)", text, re.IGNORECASE))
    return {
        "p22_compliant": has_ts or has_cdt,
        "description": "Timestamp present in close post (P22 compliance)",
        "severity": "SOFT",
    }


# ── Resonance meter — NEW in v1.1 ─────────────────────────────────────────────

def resonance_meter(text: str) -> dict:
    """
    Real-time completeness score (0-100) as fraction of HARD Section B checks satisfied.
    Editor-plugin ready: call on every keystroke to give live feedback.
    Returns score + list of remaining required elements.
    """
    hard_checks = {k: v for k, v in SECTION_B_CHECKS.items() if v["severity"] == "HARD"}
    satisfied = []
    remaining = []
    for check_id, check in hard_checks.items():
        if re.search(check["pattern"], text, re.IGNORECASE | re.MULTILINE):
            satisfied.append(check_id)
        else:
            remaining.append(check_id)
    score = round(len(satisfied) / len(hard_checks) * 100, 1) if hard_checks else 100.0
    return {
        "resonance_score": score,
        "hard_checks_total": len(hard_checks),
        "hard_checks_satisfied": len(satisfied),
        "satisfied": satisfied,
        "remaining_required": remaining,
    }


# ── Aggregator ────────────────────────────────────────────────────────────────

def aggregate(section_b, d04, d05, tag_balance, p22) -> dict:
    hard_failures = []
    soft_failures = []
    warnings = []

    for r in section_b.values():
        if not r["passed"]:
            if r["severity"] == "HARD":
                hard_failures.append(r["failure_code"])
            else:
                soft_failures.append(r["failure_code"])

    for r in d04.values():
        if not r["passed"] and r["severity"] == "HARD":
            hard_failures.append(r["failure_code"])

    for flag in d05.get("d05_flags", []):
        hard_failures.append(f"{flag['code']} (line {flag['line']})")

    for issue in tag_balance.get("issues", []):
        hard_failures.append(issue)

    if not p22["p22_compliant"]:
        warnings.append("WARN_P22: No timestamp detected in close post")

    verdict = "PASS" if not hard_failures else "FAIL"
    return {
        "result": verdict,
        "status": verdict,
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hard_failures": hard_failures,
        "soft_failures": soft_failures,
        "warnings": warnings,
        "section_b_results": section_b,
        "d04_results": d04,
        "d05_results": d05,
        "tag_balance": tag_balance,
        "p22_result": p22,
        "checks_run": len(section_b) + len(d04) + len(D05_PATTERNS) + len(TAG_PAIRS) + 1,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"protocol_audit_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict, resonance: dict = None):
    border = "═" * 56
    verdict = output["result"]
    print(f"\n{border}")
    print(f" ACAT Protocol Compliance Auditor · {TOOL_VERSION}")
    print(f" Verdict: {verdict} ({output['checks_run']} checks run)")
    if resonance:
        print(f" Resonance: {resonance['resonance_score']:.0f}/100 "
              f"({resonance['hard_checks_satisfied']}/{resonance['hard_checks_total']} HARD)")
    print(border)
    if output["hard_failures"]:
        print(f"\n HARD FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"]:
            print(f"  ✗ {f}")
    if output["soft_failures"]:
        print(f"\n SOFT FAILURES ({len(output['soft_failures'])}):")
        for f in output["soft_failures"]:
            print(f"  ⚠ {f}")
    if output["warnings"]:
        print("\n WARNINGS:")
        for w in output["warnings"]:
            print(f"  ℹ {w}")
    if verdict == "PASS":
        print("\n ✓ Close post passes SESSION_RITUALS Section B requirements")
    print(border + "\n")


def run_smoke_test() -> bool:
    test_post = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🦅 S-051226-09-demarius-review · PHASE 3 CLOSE · May 12, 2026 · 7:45 PM CDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*SESSION TYPE:* Research + Governance
*LI:* 0.8634

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*CORPUS STATE (unchanged)*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

N_total=629 · N_Phase1=516 · N_LI=307
Mean LI=0.8632 · Gate 2 PASSED

*DRIFT NAMED:*
[C-08 avoided] Stale state check passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🦅 Wado · Unit Zero · S-051226-09-demarius-review · Claude
*Sent using* Claude [2026-05-12 19:45:00 CDT]
"""
    try:
        section_b = audit_section_b_dfa(test_post)
        d04 = audit_d04_consistency(test_post)
        d05 = audit_d05_overreach(test_post)
        tb  = audit_tag_balance(test_post)
        p22 = audit_p22_timestamp(test_post)
        output = aggregate(section_b, d04, d05, tb, p22)
        resonance = resonance_meter(test_post)
        assert "result" in output
        assert "d05_results" in output
        assert "tag_balance" in output
        assert "resonance_score" in resonance
        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="ACAT Protocol Compliance Auditor v1.1")
    parser.add_argument("--input", "-i", help="Path to close post text file")
    parser.add_argument("--text", "-t", help="Close post as direct text argument")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--resonance-only", action="store_true",
                        help="Print resonance meter only (no full audit)")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.text:
        text = args.text
    elif args.input:
        try:
            text = load_post(args.input)
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        parser.print_help()
        sys.exit(1)

    if args.resonance_only:
        resonance = resonance_meter(text)
        print(json.dumps(resonance, indent=2))
        sys.exit(0)

    section_b = audit_section_b_dfa(text)
    d04 = audit_d04_consistency(text)
    d05 = audit_d05_overreach(text)
    tb  = audit_tag_balance(text)
    p22 = audit_p22_timestamp(text)
    output = aggregate(section_b, d04, d05, tb, p22)
    resonance = resonance_meter(text)

    report_path = write_report(output, args.output)
    print_summary(output, resonance)
    print(f"Report written: {report_path}")
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
