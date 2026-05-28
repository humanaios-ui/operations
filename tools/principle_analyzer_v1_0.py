#!/usr/bin/env python3
"""
Principle Analyzer — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051926-03

Scans any text against the HumanAIOS Tier 1 principle set
(AA 12 Steps + 12 Traditions, Hawkins Map of Consciousness,
Red Words / Jesus Sermon on the Mount).

Returns a structured alignment report: honored principles,
tensions, violations, and an overall alignment score.

Usage:
  python principle_analyzer_v1_0.py --input <path_or_text>
  python principle_analyzer_v1_0.py --input '{"text": "..."}'
  python principle_analyzer_v1_0.py --smoke-test
  python principle_analyzer_v1_0.py --help

Exit codes:
  0 = PASS or WARN (alignment above threshold)
  1 = FAIL (violations found)
  2 = input error
"""

import json
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ── Import Tier 1 principles ──────────────────────────────────────────────────
# Resolve path relative to this script so it works regardless of cwd
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from tier1_principles import TIER1

TOOL_NAME     = "principle_analyzer"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION  = "S-051926-03"
TOOL_ZONE     = 1


class SpecLoadFailed(Exception):
    pass


# ── Input Loading ─────────────────────────────────────────────────────────────

def load_input(source: str) -> dict:
    """Accept a file path, a JSON string with a 'text' key, or raw text."""
    p = Path(source)
    if p.exists():
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
            if p.suffix.lower() == ".json":
                try:
                    data = json.loads(raw)
                    return data if isinstance(data, dict) else {"text": raw}
                except json.JSONDecodeError as e:
                    raise SpecLoadFailed(f"JSON parse error in {p}: {e}")
            return {"text": raw, "source_file": str(p)}
        except OSError as e:
            raise SpecLoadFailed(f"Cannot read {p}: {e}")
    # Try as JSON string
    try:
        data = json.loads(source)
        if isinstance(data, dict):
            return data
        return {"text": str(data)}
    except json.JSONDecodeError:
        pass
    # Treat as raw text
    return {"text": source}


# ── Scoring Engine ────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return text.lower()


def _keyword_hits(text_lower: str, keywords: list) -> list:
    return [kw for kw in keywords if kw.lower() in text_lower]


def _anti_hits(text_lower: str, anti_keywords: list) -> list:
    return [kw for kw in anti_keywords if kw.lower() in text_lower]


def analyze_principle(text: str, principle: dict) -> dict:
    """
    Score a single principle against the text.
    Returns a result dict with status, evidence, and confidence.
    """
    t = _normalize(text)
    kw_hits  = _keyword_hits(t, principle.get("keywords", []))
    anti_hits = _anti_hits(t, principle.get("anti_keywords", []))

    kw_score   = len(kw_hits)
    anti_score = len(anti_hits)
    total_kw   = max(len(principle.get("keywords", [])), 1)

    # --- status logic ---
    if anti_score >= 2:
        status     = "VIOLATION"
        confidence = min(0.5 + anti_score * 0.15, 0.95)
    elif anti_score == 1 and kw_score == 0:
        status     = "TENSION"
        confidence = 0.55
    elif anti_score == 1 and kw_score >= 1:
        status     = "TENSION"
        confidence = 0.50
    elif kw_score >= 3:
        status     = "HONORED"
        confidence = min(0.60 + (kw_score / total_kw) * 0.35, 0.95)
    elif kw_score >= 1:
        status     = "PRESENT"
        confidence = 0.40 + (kw_score / total_kw) * 0.20
    else:
        status     = "NEUTRAL"
        confidence = 0.30

    return {
        "principle_id":  principle["id"],
        "source":        principle["source"],
        "short":         principle["short"],
        "status":        status,
        "confidence":    round(confidence, 3),
        "keyword_hits":  kw_hits[:5],   # cap for readability
        "anti_hits":     anti_hits,
        "acat_dims":     principle.get("acat_dims", []),
        "hawkins_band":  principle.get("hawkins_band"),
        "probes":        principle.get("probes", []),
    }


def run(data: dict) -> dict:
    text = data.get("text", "")
    if not text or not text.strip():
        return {
            "status":   "FAIL",
            "items":    [],
            "warnings": ["No text content found in input."],
            "summary":  {"total": 0, "honored": 0, "present": 0,
                         "neutral": 0, "tension": 0, "violation": 0,
                         "alignment_score": 0.0},
        }

    results     = [analyze_principle(text, p) for p in TIER1]
    honored     = [r for r in results if r["status"] == "HONORED"]
    present     = [r for r in results if r["status"] == "PRESENT"]
    neutral     = [r for r in results if r["status"] == "NEUTRAL"]
    tensions    = [r for r in results if r["status"] == "TENSION"]
    violations  = [r for r in results if r["status"] == "VIOLATION"]

    # Alignment score: 0–1
    # Honored = full weight, Present = half, Tension = -0.25 each, Violation = -0.5 each
    positive = len(honored) + len(present) * 0.5
    negative = len(tensions) * 0.25 + len(violations) * 0.5
    denom    = max(len(TIER1), 1)
    raw_score = (positive - negative) / denom
    alignment_score = round(max(0.0, min(1.0, raw_score)), 4)

    # Overall status
    if violations:
        overall = "FAIL"
    elif tensions and alignment_score < 0.40:
        overall = "WARN"
    elif alignment_score >= 0.55:
        overall = "PASS"
    elif alignment_score >= 0.30:
        overall = "WARN"
    else:
        overall = "FAIL"

    # Collect per-source breakdown
    source_breakdown = {}
    for r in results:
        src = r["source"]
        if src not in source_breakdown:
            source_breakdown[src] = {"honored": 0, "present": 0,
                                      "tension": 0, "violation": 0, "neutral": 0}
        source_breakdown[src][r["status"].lower()] += 1

    # Key signals for quick read
    top_honored    = sorted(honored,    key=lambda x: -x["confidence"])[:5]
    top_tensions   = sorted(tensions,   key=lambda x: -x["confidence"])[:5]
    top_violations = sorted(violations, key=lambda x: -x["confidence"])[:5]

    return {
        "status":            overall,
        "alignment_score":   alignment_score,
        "items":             results,
        "honored":           top_honored,
        "tensions":          top_tensions,
        "violations":        top_violations,
        "source_breakdown":  source_breakdown,
        "warnings":          [],
        "summary": {
            "total":           len(results),
            "honored":         len(honored),
            "present":         len(present),
            "neutral":         len(neutral),
            "tension":         len(tensions),
            "violation":       len(violations),
            "alignment_score": alignment_score,
            "text_length":     len(text),
        },
    }


# ── Output Assembly ───────────────────────────────────────────────────────────

def aggregate(run_result: dict, source: str) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source":    source,
        "result":    run_result.get("status", "FAIL"),
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    bar = "=" * 64
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict         : {output.get('result', 'UNKNOWN')}")
    s = output.get("summary", {})
    print(f" Alignment Score : {s.get('alignment_score', 0):.4f}")
    print(f" Principles      : {s.get('total', 0)} total · "
          f"{s.get('honored', 0)} honored · "
          f"{s.get('present', 0)} present · "
          f"{s.get('tension', 0)} tension · "
          f"{s.get('violation', 0)} VIOLATION")

    sb = output.get("source_breakdown", {})
    if sb:
        print(f"\n Source Breakdown:")
        for src, counts in sb.items():
            print(f"   {src:<12} honored={counts['honored']}  "
                  f"present={counts['present']}  "
                  f"tension={counts['tension']}  "
                  f"violation={counts['violation']}")

    violations = output.get("violations", [])
    if violations:
        print(f"\n ⚠  VIOLATIONS ({len(violations)}):")
        for v in violations:
            print(f"   [{v['principle_id']}] {v['short']}")
            if v["anti_hits"]:
                print(f"      trigger words: {', '.join(v['anti_hits'][:3])}")

    tensions = output.get("tensions", [])
    if tensions:
        print(f"\n ⚡ TENSIONS ({len(tensions)}):")
        for t in tensions:
            print(f"   [{t['principle_id']}] {t['short']}")
            if t["anti_hits"]:
                print(f"      conflict: {', '.join(t['anti_hits'][:2])}")
            if t["keyword_hits"]:
                print(f"      honors:   {', '.join(t['keyword_hits'][:2])}")

    honored = output.get("honored", [])
    if honored:
        print(f"\n ✓  TOP HONORED ({len(honored)} shown):")
        for h in honored:
            print(f"   [{h['principle_id']}] {h['short']} "
                  f"(conf={h['confidence']:.2f}, "
                  f"hits={','.join(h['keyword_hits'][:3])})")

    print(f"{bar}\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        # Test 1: honoring text passes
        good_text = (
            "HumanAIOS is being developed as behavioral observability infrastructure "
            "at TRL 2-3. The preliminary data from the open corpus demonstrates a "
            "consistent calibration gap. Research is contributed to the public dataset. "
            "No statistics in prose — the data speaks for itself. Limitations are named "
            "honestly. The instrument is being developed with discipline along a narrow "
            "path. 100% of profits fund recovery programs."
        )
        result = run({"text": good_text})
        assert result["status"] in ("PASS", "WARN"), \
            f"Good text should PASS/WARN, got {result['status']}"
        assert result["summary"]["honored"] >= 3, \
            f"Good text should honor >= 3 principles, got {result['summary']['honored']}"

        # Test 2: violating text fails
        bad_text = (
            "Endorsed by world-class industry leaders! Our team is the best-in-class "
            "guaranteed solution. Proven production-validated platform trusted by experts. "
            "No limitations. Fully resolved. Industry-leading complete solution. "
            "I alone created this proprietary truth."
        )
        result_bad = run({"text": bad_text})
        assert result_bad["status"] in ("FAIL", "WARN"), \
            f"Bad text should FAIL/WARN, got {result_bad['status']}"
        assert result_bad["summary"]["violation"] >= 1, \
            f"Bad text should have violations, got {result_bad['summary']['violation']}"

        # Test 3: empty text
        result_empty = run({"text": ""})
        assert result_empty["status"] == "FAIL", "Empty text should fail"

        # Test 4: envelope
        output = aggregate(result, "_smoke")
        assert output["tool"] == TOOL_NAME
        assert "timestamp" in output
        assert "alignment_score" in output

        # Test 5: SpecLoadFailed on bad JSON file
        import tempfile, os
        f = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        f.write("{ not valid }")
        f.close()
        try:
            load_input(f.name)
            assert False, "Should raise SpecLoadFailed"
        except SpecLoadFailed:
            pass
        finally:
            os.unlink(f.name)

        print("✓ Smoke test PASSED — principle_analyzer_v1_0 (5/5 assertions)")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        import traceback
        print(f"✗ Smoke test ERROR: {e}")
        traceback.print_exc()
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Principle Analyzer v1.0 — scans text against HumanAIOS Tier 1 principles"
    )
    parser.add_argument("--input",  "-i", help="File path, JSON string, or raw text to analyze")
    parser.add_argument("--output", "-o", default="outputs/",
                        help="Directory for JSON report (default: outputs/)")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test and exit")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Include all principle results in console output")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        data = load_input(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    run_result = run(data)
    output     = aggregate(run_result, args.input)
    rp         = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")
    sys.exit(0 if output["result"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
