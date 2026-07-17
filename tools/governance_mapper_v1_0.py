#!/usr/bin/env python3
"""
Governance Mapper — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-052326-03 (run() implemented)

Takes a governance document (text or fetched markdown), classifies it
against the HumanAIOS governance lane taxonomy, and produces a
GROW/KILL verdict with reasoning.

Input format:
{
  "documents": [
    {"id": "GOVERNANCE.md", "content": "...", "source": "github_raw"},
    ...
  ],
  "session_id": "S-052326-03"
}

Lane taxonomy:
  CANONICAL    — GOVERNANCE.md, SESSION_RITUALS.md, CURRENT.md, REGISTERED.md
  OPERATIONAL  — OPERATOR_RUNBOOK.md, CARRY_BLOCK.md, zone-tracking files
  RESEARCH     — arXiv .md, dataset docs, psychometric reports
  ARCHIVE      — frozen / deprecated files
  EXTERNAL     — third-party governance docs being assessed for compatibility
  UNKNOWN      — cannot classify

Verdict logic:
  GROW  — canonical or operational doc, current version, no contradictions
  WATCH — has potential drift, stale timestamp, or missing required sections
  KILL  — contradicts canonical, deprecated, or duplicate
"""

import json, sys, argparse, re
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "governance_mapper"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION  = "S-052326-03"
TOOL_ZONE     = 1

# Required sections per lane
REQUIRED_SECTIONS = {
    "CANONICAL":   ["version", "principle", "zone"],
    "OPERATIONAL": ["zone", "operator"],
    "RESEARCH":    ["n=", "mean", "findings"],
    "ARCHIVE":     [],
    "EXTERNAL":    [],
    "UNKNOWN":     [],
}

# Canonical filenames
CANONICAL_NAMES = {
    "governance.md", "session_rituals.md", "current.md", "registered.md"
}
OPERATIONAL_NAMES = {
    "operator_runbook.md", "carry_block.md", "current.md"
}
RESEARCH_NAMES = {
    "acat", "arxiv", "dataset", "psychometric", "findings"
}

class SpecLoadFailed(Exception):
    pass

def load_input(source: str) -> dict:
    # Inline JSON strings can be very long — guard before Path() call
    # (Linux filename limit is 255 bytes; longer strings are definitely JSON)
    p = Path(source) if len(source) < 240 else None
    if p is not None and p.exists():
        try:
            with open(p, encoding="utf-8") as f: return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {p}: {e}")
    try: return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Not a valid path or JSON: {e}")

def classify_lane(doc_id: str, content: str) -> str:
    name = doc_id.lower()
    if any(c in name for c in CANONICAL_NAMES): return "CANONICAL"
    if any(o in name for o in OPERATIONAL_NAMES): return "OPERATIONAL"
    if any(r in name for r in RESEARCH_NAMES): return "RESEARCH"
    if "archive" in name or "deprecated" in name or "old_" in name: return "ARCHIVE"
    # Content-based fallback
    content_lower = content.lower()
    if "principle" in content_lower and "zone" in content_lower: return "CANONICAL"
    if "operator" in content_lower and "zone 3" in content_lower: return "OPERATIONAL"
    if re.search(r'n\s*=\s*\d+', content_lower): return "RESEARCH"
    return "EXTERNAL"

def check_required_sections(lane: str, content: str) -> list:
    """Returns list of missing required section keywords."""
    content_lower = content.lower()
    required = REQUIRED_SECTIONS.get(lane, [])
    return [r for r in required if r not in content_lower]

def extract_version(content: str) -> str:
    """Try to extract version string from document."""
    m = re.search(r'v(\d+\.\d+(?:\.\d+)?)', content[:500])
    return f"v{m.group(1)}" if m else "UNKNOWN"

def assess_verdict(lane: str, missing: list, doc_id: str, content: str) -> tuple:
    """Returns (verdict, reasons)."""
    reasons = []
    if lane == "ARCHIVE":
        return "KILL", ["Document is archived/deprecated"]
    if lane == "UNKNOWN":
        return "WATCH", ["Cannot classify lane — manual review needed"]
    if missing:
        reasons.append(f"Missing required sections for {lane}: {', '.join(missing)}")
        return "WATCH", reasons
    if "contradiction" in content.lower() or "deprecated" in content.lower():
        reasons.append("Contains deprecation or contradiction markers")
        return "WATCH", reasons
    reasons.append(f"Lane={lane}, required sections present")
    return "GROW", reasons

def run(data: dict) -> dict:
    docs = data.get("documents", [])
    if not docs and "_smoke" not in data:
        return {"status":"WARN","items":[],"warnings":["No documents provided"],
                "summary":{"total":0,"grow":0,"watch":0,"kill":0}}

    items = []
    warnings = []

    for doc in docs:
        doc_id  = doc.get("id", "unknown")
        content = doc.get("content", "")
        source  = doc.get("source", "unknown")

        lane    = classify_lane(doc_id, content)
        missing = check_required_sections(lane, content)
        version = extract_version(content)
        verdict, reasons = assess_verdict(lane, missing, doc_id, content)

        if verdict in ("WATCH","KILL"):
            warnings.append(f"{verdict}: {doc_id} — {reasons[0]}")

        items.append({
            "id":      doc_id,
            "lane":    lane,
            "verdict": verdict,
            "version": version,
            "source":  source,
            "missing_sections": missing,
            "reasons": reasons,
            "status":  verdict,
        })

    n_grow  = sum(1 for i in items if i["verdict"]=="GROW")
    n_watch = sum(1 for i in items if i["verdict"]=="WATCH")
    n_kill  = sum(1 for i in items if i["verdict"]=="KILL")

    status = "FAIL" if n_kill > 0 else ("WARN" if n_watch > 0 else "PASS")

    return {
        "status":   status,
        "items":    items,
        "warnings": warnings,
        "summary":  {"total": len(items), "grow": n_grow, "watch": n_watch, "kill": n_kill},
    }

def aggregate(run_result, source):
    return {"tool": TOOL_NAME, "version": TOOL_VERSION, "zone": TOOL_ZONE,
            "session": TOOL_SESSION, "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source, "result": run_result.get("status","FAIL"), **run_result}

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
    print(f" Verdict : {output.get('result','?')}")
    s = output.get("summary",{})
    print(f" Total={s.get('total',0)}  GROW={s.get('grow',0)}  WATCH={s.get('watch',0)}  KILL={s.get('kill',0)}")
    for item in output.get("items",[]):
        print(f"   {item['verdict']:<5}  [{item['lane']:<11}]  {item['id']}  {item['version']}")
    print(f"{bar}\n")

def run_smoke_test():
    try:
        result = run({"documents":[
            {"id":"GOVERNANCE.md","content":"principle zone version v6.4","source":"github_raw"},
            {"id":"old_notes_deprecated.md","content":"deprecated content","source":"local"},
            {"id":"acat_findings.md","content":"n=629 mean li=0.8632 findings registered","source":"local"},
        ]})
        assert result["summary"]["grow"] >= 1
        assert result["summary"]["kill"] >= 1

        # Empty
        result2 = run({})
        assert result2["status"] == "WARN"

        out = aggregate(result, "_smoke")
        assert out["tool"] == TOOL_NAME
        try: load_input("/nonexistent.json"); assert False
        except SpecLoadFailed: pass
        print("✓ Smoke test PASSED"); return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}"); return False
    except Exception as e:
        print(f"✗ ERROR: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="Governance Mapper v1.1.0")
    parser.add_argument("--input","-i")
    parser.add_argument("--output","-o",default="outputs/")
    parser.add_argument("--smoke-test",action="store_true")
    args = parser.parse_args()
    if args.smoke_test: sys.exit(0 if run_smoke_test() else 1)
    if not args.input: parser.print_help(); sys.exit(1)
    try: data = load_input(args.input)
    except SpecLoadFailed as e: print(f"SPEC_LOAD_FAILED: {e}",file=sys.stderr); sys.exit(2)
    run_result = run(data)
    output = aggregate(run_result, args.input)
    rp = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")
    sys.exit(0 if output["result"] in ("PASS","WARN") else 1)

if __name__ == "__main__": main()
