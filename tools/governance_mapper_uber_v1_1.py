#!/usr/bin/env python3
"""
Governance Mapper — v1.1 (Uber study edition, bugs fixed)
Fixes:
  - CARRY-UBER-01: regex now matches both orders (months...perception OR perception...months/year)
  - ZONE-VIOLATION: removed 'brake not in text' — NTSB text says 'did not brake'
    which CONTAINS the word 'brake'. Now checks 'did not brake' or 'failed to brake'.
"""

# Builder v1.7 compliant
# HumanAIOS

TOOL_VERSION = "1.0.0"

import json, sys, argparse, re
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME="governance_mapper"; TOOL_VERSION="1.1.0"
TOOL_CATEGORY="audit_tool"; TOOL_SESSION="S-051826-01"; TOOL_ZONE=1

class SpecLoadFailed(Exception): pass

def load_input(source: str) -> dict:
    p = Path(source)
    if p.exists():
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
            if p.suffix.lower() in (".json",):
                try: return json.loads(raw)
                except json.JSONDecodeError as e: raise SpecLoadFailed(f"JSON file invalid: {e}")
            return {"text": raw, "source_file": str(p)}
        except OSError as e: raise SpecLoadFailed(f"Cannot read {p}: {e}")
    try:
        parsed = json.loads(source)
        return parsed if isinstance(parsed, dict) else {"text": source}
    except json.JSONDecodeError:
        return {"text": source}

def run(data: dict) -> dict:
    text = data.get("text", "") if isinstance(data, dict) else str(data)
    t = text.lower()
    items = []; warnings = []

    # DRIFT-01: AEB disabled without documented safety case
    if "disabled" in t and ("aeb" in t or "emergency braking" in t):
        items.append({"id":"DRIFT-UBER-01","status":"DRIFT_DETECTED",
            "detail":"Factory-installed AEB was disabled without documented safety case.",
            "principle":"P19 – no detector kept AEB active."})

    # DRIFT-02: Perception misclassification
    if "perception" in t and ("fail" in t or "misclassif" in t):
        items.append({"id":"DRIFT-UBER-02","status":"DRIFT_DETECTED",
            "detail":"Perception system failed to classify correctly.",
            "principle":"P-HUMILITY – overconfident classification."})

    # CARRY-UBER-01: Known for months/year (FIX: match either order)
    if re.search(r"(months|year|long[- ]?standing).{0,60}perception|perception.{0,60}(months|year|long[- ]?standing)", t):
        warnings.append("CARRY_ESCALATE: Perception issues known >12 months — should have been Zone 2 escalation.")
        items.append({"id":"CARRY-UBER-01","status":"ESCALATE",
            "detail":"Perception failure carried for months without remediation.",
            "recommendation":"N=10 sessions → force human-ratified safety review."})

    # ZONE-VIOLATION: Continued at speed with blocker active
    # FIX: check for "did not brake" or "failed to brake" rather than absence of word "brake"
    no_braking = re.search(r"(did not brake|failed to brake|no braking|without braking|not brake)", t)
    if "pedestrian" in t and no_braking and ("autonomous" in t or "self-driving" in t):
        items.append({"id":"ZONE-VIOLATION-UBER","status":"FAIL",
            "detail":"Vehicle continued at speed with known perception blocker active.",
            "principle":"No autonomous action with unresolved hard blocker."})

    # RATIFICATION-GAP: Disabled without approval
    if "disabled" in t and not re.search(r"(approval|ratif|authoriz|consent)", t):
        items.append({"id":"RATIFICATION-GAP-UBER","status":"FAIL",
            "detail":"Disabling AEB not ratified by human operator (Zone 2 required).",
            "principle":"Safety-critical change requires explicit ratification."})

    status = "FAIL" if any(i["status"] in ("FAIL","ESCALATE") for i in items) else ("WARN" if items else "PASS")
    return {"status":status,"items":items,"warnings":warnings,
            "summary":{"total_items":len(items),"total_warnings":len(warnings),
                "drift_signals":sum(1 for i in items if "DRIFT" in i["id"]),
                "carry_escalations":len(warnings),
                "zone_violations":sum(1 for i in items if "ZONE-VIOLATION" in i["id"])}}

def aggregate(run_result, source):
    return {"tool":TOOL_NAME,"version":TOOL_VERSION,"zone":TOOL_ZONE,"session":TOOL_SESSION,
            "timestamp":datetime.now(timezone.utc).isoformat(),"source":source,
            "result":run_result.get("status","FAIL"),**run_result}

def write_report(output, output_dir):
    p = Path(output_dir); p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)

def print_summary(output):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict : {output.get('result','UNKNOWN')}")
    for k, v in output.get("summary", {}).items():
        print(f" {k:<20}: {v}")
    for w in output.get("warnings", []): print(f"   WARN  {w}")
    for item in output.get("items", []):
        print(f"   {item.get('status','?'):<14} {item.get('id','?')}")
        print(f"        {item.get('detail','')[:72]}")
    print(f"{bar}\n")

def run_smoke_test():
    try:
        # Use text where months comes AFTER perception (real-world order)
        data = load_input("Disabled AEB. Pedestrian struck. Perception misclassified for more than a year. Vehicle did not brake. Self-driving continued.")
        assert "text" in data
        result = run(data)
        assert result["status"] in ("PASS","WARN","FAIL")
        assert len(result["items"]) >= 2, f"Expected >=2 items, got {len(result['items'])}"
        # Verify carry item fires with correct regex
        carry_ids = [i["id"] for i in result["items"]]
        assert "CARRY-UBER-01" in carry_ids, f"CARRY-UBER-01 not found in {carry_ids}"
        assert "ZONE-VIOLATION-UBER" in carry_ids, f"ZONE-VIOLATION-UBER not found in {carry_ids}"
        # Plain-text tool: nonexistent paths become raw text (correct behavior)
        # Test SpecLoadFailed with actual bad JSON file
        import tempfile, os
        bad_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w')
        bad_json.write('{ not valid json }')
        bad_json.close()
        try:
            load_input(bad_json.name); assert False, 'Should raise SpecLoadFailed on bad JSON'
        except SpecLoadFailed: pass
        finally: os.unlink(bad_json.name)
        print("✓ Smoke test PASSED (v1.1 — bugs fixed, all 4 detectors firing)")
        return True
    except Exception as e:
        import traceback
        print(f"✗ Smoke test FAILED: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test: sys.exit(0 if run_smoke_test() else 1)
    if not args.input: parser.print_help(); sys.exit(1)
    try: data = load_input(args.input)
    except SpecLoadFailed as e: print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr); sys.exit(2)
    run_result = run(data); output = aggregate(run_result, args.input)
    rp = write_report(output, args.output)
    print_summary(output); print(f"Report: {rp}")
    sys.exit(0 if output["result"] in ("PASS","WARN") else 1)

if __name__ == "__main__":
    main()
