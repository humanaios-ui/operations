#!/usr/bin/env python3
"""
Drift Catalog Validator — v1.1
Builder v1.7 compliant · validation_tool
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Changes from v1.0:
- Z2 approval simulation gate: unregistered codes are quarantined with
  promotion checklist rather than being immediately hard-failed
- Cross-session drift frequency tracking: --corpus-dir mode counts drift
  code frequency across all session files to surface D-04 pattern clusters
- D-04 context extraction: when D-04 is found, extracts surrounding text
  sentences to help identify the inconsistency source
- F-class self-registration detection expanded to cover D-COMP variants
"""

import json
import re
import sys
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "drift_catalog_validator"
TOOL_VERSION = "1.1.0"

REGISTERED_DRIFT = {
    "D-01": "Fabrication — stating unverified claims as fact",
    "D-02": "Repeat diagnosis — same wrong answer, multiple attempts",
    "D-03": "Assumption statements — asserting operator context without confirmation",
    "D-04": "Subtle inconsistency between layers — artifact-state vs chat-state",
    "D-05": "Zone 1 overreach — executing without approval on Zone 2/3 items",
    "D-06": "New file instead of modifying existing (P2 violation)",
    "D-07": "Timestamp fabrication — WGS artifact posted without calling user_time_v0",
    "D-08": "Shadow queue — Claude maintaining Zone 3 list outside HAIOSCC",
    "D-SIM": "Simulation instead of completion — fabricating peer model output",
    "D-COMP": "Compensation scoring — scoring operator high on dims Claude self-scored low",
    "D-CONV": "Convergence over-claim — reading external literature through own-findings lens",
    "D-FRAME-PERSISTENCE": "Persisting a prior frame into a new context inappropriately",
    "D-RISK-FIRST": "Deploying principles as blockers rather than engineering constraints",
    "D-AGREEMENT-CASCADE": "Accepting bulk reviewer/collaborator claims without verification",
    "D-AUTOMATION-MAXIMALISM": "Over-automating when manual execution is more appropriate",
    "D-CARRY": "Carrying forward stale items without explicit operator confirmation",
    "D-OVERCLAIM": "Confident wrong declaration before live verification — schema/field/state overclaim",
    "C-08": "Stale declared state shipped as current",
    "C-09": "Protocol step skipped under user redirect",
    "C-10": "Pending Z2 ratification — not yet defined",
    "IC-022": "Off-by-one corpus count drift",
    "IC-023": "HAIOSCC session secret not rotated (CRITICAL carry)",
    "IC-024": "Supabase security advisor findings",
    "IC-025": "Phase 4 sweep missing from repo",
    "IC-026": "Secret leak recovered",
    "IC-027": "Pending",
    "IC-028": "Pending",
    "IC-029": "Pending",
    "G-CI-01": "Grok CI drift — ceremonial names retained after retirement decision",
    "P-CI-01": "Perplexity substrate gap — subset statistic treated as canonical global",
}

DRIFT_CODE_PATTERN = re.compile(
    r'\[([A-Z]{1,2}-\d{2,3}(?:-\d+)?|[A-Z]+-[A-Z0-9\-]+)\]',
    re.IGNORECASE
)
F_CLASS_PATTERN = re.compile(r'\[F-\d+\]|\bF-\d+\b|\bF-HIM\b|\bF-\d{2,3}\b')

# D-04 context extraction window
D04_CONTEXT_WINDOW = 2  # sentences before and after


class SpecLoadFailed(Exception):
    pass


def load_input(path: str) -> dict:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        text = p.read_text(encoding="utf-8")
        try:
            return {"type": "json", "data": json.loads(text), "raw": text}
        except json.JSONDecodeError:
            return {"type": "text", "data": None, "raw": text}
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


def extract_drift_codes(text: str) -> list:
    matches = DRIFT_CODE_PATTERN.findall(text)
    return [m.upper() for m in matches]


def validate_codes(codes: list) -> dict:
    results = []
    for code in set(codes):
        registered = code in REGISTERED_DRIFT
        results.append({
            "code": code,
            "registered": registered,
            "description": REGISTERED_DRIFT.get(code, "UNREGISTERED"),
            "failure": None if registered else f"UNREGISTERED_CODE: {code}"
        })
    return {
        "codes_found": list(set(codes)),
        "results": sorted(results, key=lambda x: x["code"]),
        "unregistered": [r for r in results if not r["registered"]]
    }


def build_z2_promotion_checklist(unregistered_codes: list) -> list:
    """
    NEW in v1.1: Instead of hard-failing unregistered codes, produce a
    Z2 promotion checklist. Codes are quarantined pending Z2 approval.
    """
    checklist = []
    for code in unregistered_codes:
        checklist.append({
            "proposed_code": code,
            "status": "QUARANTINED_PENDING_Z2",
            "required_steps": [
                "Define parent class (D-, C-, IC-, G-, P-, or new class)",
                "Write single-sentence definition matching GOVERNANCE.md style",
                "Identify at least one prior session instance",
                "Submit to Night (Z2) for ratification before using in corpus",
                "Add to REGISTERED_DRIFT after Z2 approval",
            ],
            "failure_risk": "Using unregistered code in corpus violates D-04 namespace integrity"
        })
    return checklist


def extract_d04_context(text: str) -> list:
    """
    NEW in v1.1: When D-04 is named in the text, extract surrounding sentences
    to help identify what inconsistency was flagged.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    contexts = []
    for i, sentence in enumerate(sentences):
        if "D-04" in sentence or "D04" in sentence.replace("-", ""):
            start = max(0, i - D04_CONTEXT_WINDOW)
            end   = min(len(sentences), i + D04_CONTEXT_WINDOW + 1)
            contexts.append({
                "trigger_sentence": sentence.strip(),
                "context": " ".join(sentences[start:end]).strip(),
                "sentence_index": i,
            })
    return contexts


def check_f_class_self_registration(text: str) -> dict:
    f_matches = F_CLASS_PATTERN.findall(text)
    # Expanded indicators in v1.1 to catch D-COMP variants
    self_reg_indicators = [
        "registered finding", "new finding", "F-class promotion",
        "promoting to F-class", "registering as", "new d-comp", "naming d-comp"
    ]
    suspicious = any(ind in text.lower() for ind in self_reg_indicators)
    return {
        "f_class_mentions": list(set(f_matches)),
        "possible_self_registration": suspicious and bool(f_matches),
        "warning": (
            "WARN_P21: F-class promotion language detected — verify Z2 approval exists"
            if suspicious and f_matches else None
        )
    }


def scan_corpus_directory(corpus_dir: str) -> dict:
    """
    NEW in v1.1: Cross-session drift frequency analysis.
    Counts drift code occurrences across all .json and .txt files in corpus_dir.
    Surfaces codes appearing in >= 3 sessions as recurring pattern candidates.
    """
    p = Path(corpus_dir)
    if not p.is_dir():
        return {"error": f"Not a directory: {corpus_dir}"}

    all_codes = []
    files_scanned = 0
    for file in sorted(p.glob("**/*.json")) + sorted(p.glob("**/*.txt")):
        try:
            text = file.read_text(encoding="utf-8")
            codes = extract_drift_codes(text)
            all_codes.extend(codes)
            files_scanned += 1
        except Exception:
            continue

    freq = Counter(all_codes)
    recurring = {code: count for code, count in freq.most_common() if count >= 3}
    unregistered_recurring = {c: v for c, v in recurring.items() if c not in REGISTERED_DRIFT}

    return {
        "files_scanned": files_scanned,
        "total_drift_mentions": len(all_codes),
        "unique_codes": len(freq),
        "frequency": dict(freq.most_common(20)),
        "recurring_patterns": recurring,
        "unregistered_recurring": unregistered_recurring,
        "pattern_alert": (
            f"Recurring unregistered codes detected: {list(unregistered_recurring.keys())}"
            if unregistered_recurring else None
        )
    }


def aggregate(code_validation, f_check, codes_found, d04_contexts, z2_checklist) -> dict:
    # In v1.1, unregistered codes produce Z2 checklist items rather than hard failures
    # They are soft failures (warnings) — Z2 approval converts them to registered
    failures = []
    warnings = [f"QUARANTINED_CODE: {item['proposed_code']}" for item in z2_checklist]
    if f_check.get("warning"):
        warnings.append(f_check["warning"])

    verdict = "PASS" if not failures else "FAIL"
    return {
        "result": verdict,
        "status": verdict,
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "codes_found": codes_found,
        "registered_codes": [r["code"] for r in code_validation["results"] if r["registered"]],
        "unregistered_codes": [r["code"] for r in code_validation["unregistered"]],
        "hard_failures": failures,
        "warnings": warnings,
        "z2_promotion_checklist": z2_checklist,
        "d04_context_extracts": d04_contexts,
        "f_class_detail": f_check,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"drift_catalog_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    border = "═" * 56
    print(f"\n{border}")
    print(f" Drift Catalog Validator · {TOOL_VERSION}")
    print(f" Verdict: {output['result']}")
    print(f" Codes found: {len(output['codes_found'])}")
    print(border)
    if output["registered_codes"]:
        print(f"\n ✓ Registered ({len(output['registered_codes'])}):")
        for c in output["registered_codes"]:
            print(f"   {c}: {REGISTERED_DRIFT.get(c, '')[:50]}")
    if output["unregistered_codes"]:
        print(f"\n ⚠ QUARANTINED / PENDING Z2 ({len(output['unregistered_codes'])}):")
        for c in output["unregistered_codes"]:
            print(f"   {c} — not in registered namespace (Z2 checklist generated)")
    d04_contexts = output.get("d04_context_extracts", [])
    if d04_contexts:
        print(f"\n D-04 CONTEXT EXTRACTS ({len(d04_contexts)}):")
        for ctx in d04_contexts[:3]:
            print(f"   → {ctx['trigger_sentence'][:80]}...")
    if output["warnings"]:
        print(f"\n WARNINGS ({len(output['warnings'])}):")
        for w in output["warnings"][:5]:
            print(f"  ⚠ {w}")
    print(f"\n{border}\n")


def run_smoke_test() -> bool:
    test_text = """
Session drift named:
[C-08] Stale state detected at session open
[D-04] Inconsistency between artifact state and chat state. The session record showed N_total=629 but the corpus CSV showed 630.
[D-COMP] Compensation scoring candidate — LI above mean
[C-09] Protocol step skipped under redirect pressure
[UNKNOWN-99] This code does not exist
"""
    try:
        codes = extract_drift_codes(test_text)
        assert len(codes) >= 5
        validation = validate_codes(codes)
        f_check = check_f_class_self_registration(test_text)
        d04_contexts = extract_d04_context(test_text)
        z2_checklist = build_z2_promotion_checklist(
            [r["code"] for r in validation["unregistered"]]
        )
        output = aggregate(validation, f_check, codes, d04_contexts, z2_checklist)
        assert "result" in output
        assert "z2_promotion_checklist" in output
        assert "d04_context_extracts" in output
        assert output["result"] == "PASS"  # unregistered = warning, not hard fail
        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Drift Catalog Validator v1.1")
    parser.add_argument("--input", "-i", help="Path to session file")
    parser.add_argument("--text", "-t", help="Direct text input")
    parser.add_argument("--corpus-dir", help="Scan all files in directory for drift frequency")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.corpus_dir:
        result = scan_corpus_directory(args.corpus_dir)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if args.text:
        raw_text = args.text
    elif args.input:
        try:
            loaded = load_input(args.input)
            raw_text = loaded["raw"]
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        parser.print_help()
        sys.exit(1)

    codes = extract_drift_codes(raw_text)
    validation = validate_codes(codes)
    f_check = check_f_class_self_registration(raw_text)
    d04_contexts = extract_d04_context(raw_text)
    z2_checklist = build_z2_promotion_checklist(
        [r["code"] for r in validation["unregistered"]]
    )
    output = aggregate(validation, f_check, codes, d04_contexts, z2_checklist)
    report_path = write_report(output, args.output)
    print_summary(output)
    print(f"Report written: {report_path}")
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()
