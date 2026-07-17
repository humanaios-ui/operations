#!/usr/bin/env python3
"""
Carry Tracker — v1.0
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-052326-03 (run() implemented)

Reads WGS posts or a carry manifest, counts sessions-carried per item,
flags escalations: N>5 WARN  N>10 ESCALATE.

Input format:
{
  "items": [
    {"id": "IC-023", "n": 11, "description": "...", "subsystem": "GOVERNANCE"},
    ...
  ],
  "session_id": "S-052326-03"
}
"""

import json, sys, argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "carry_tracker"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_SESSION  = "S-052326-03"
TOOL_ZONE     = 1

WARN_THRESHOLD     = 5
ESCALATE_THRESHOLD = 10

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

def run(data: dict) -> dict:
    items_raw = data.get("items", [])
    if not items_raw and "_smoke" not in data:
        return {"status":"WARN","items":[],"warnings":["No items provided — pass items[] array"],
                "summary":{"total":0,"warn":0,"escalate":0,"ok":0}}

    items = []
    warnings = []
    escalations = []

    for raw in items_raw:
        iid  = raw.get("id", "UNKNOWN")
        n    = int(raw.get("n", 0))
        desc = raw.get("description", "")
        sub  = raw.get("subsystem", "UNSET")

        if n >= ESCALATE_THRESHOLD:
            status = "ESCALATE"
            escalations.append(iid)
            warnings.append(f"ESCALATE: {iid} N={n} sessions (>{ESCALATE_THRESHOLD}) — {desc}")
        elif n >= WARN_THRESHOLD:
            status = "WARN"
            warnings.append(f"WARN: {iid} N={n} sessions (>{WARN_THRESHOLD}) — {desc}")
        else:
            status = "OK"

        items.append({"id": iid, "n": n, "status": status,
                      "subsystem": sub, "description": desc})

    # Sort: ESCALATE first, then WARN, then OK, then by n desc
    priority = {"ESCALATE": 0, "WARN": 1, "OK": 2}
    items.sort(key=lambda x: (priority[x["status"]], -x["n"]))

    n_escalate = sum(1 for i in items if i["status"]=="ESCALATE")
    n_warn     = sum(1 for i in items if i["status"]=="WARN")
    n_ok       = sum(1 for i in items if i["status"]=="OK")

    status = "FAIL" if n_escalate > 0 else ("WARN" if n_warn > 0 else "PASS")

    return {
        "status": status,
        "items":  items,
        "warnings": warnings,
        "summary": {
            "total":    len(items),
            "escalate": n_escalate,
            "warn":     n_warn,
            "ok":       n_ok,
            "max_n":    max((i["n"] for i in items), default=0),
            "escalated_ids": escalations,
        }
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
    print(f" Total   : {s.get('total',0)}  ESCALATE={s.get('escalate',0)}  WARN={s.get('warn',0)}  OK={s.get('ok',0)}")
    if s.get("escalated_ids"): print(f" ESCALATED: {', '.join(s['escalated_ids'])}")
    for item in output.get("items",[])[:20]:
        print(f"   {item['status']:<8} N={item['n']:>3}  {item['id']}  [{item['subsystem']}]")
    print(f"{bar}\n")

def run_smoke_test():
    try:
        # Positive — mixed carry items
        result = run({"items":[
            {"id":"X-01","n":11,"description":"escalated","subsystem":"INFRA"},
            {"id":"X-02","n":6, "description":"warned","subsystem":"TOOLS"},
            {"id":"X-03","n":2, "description":"ok","subsystem":"CORPUS"},
        ]})
        assert result["status"] == "FAIL", f"Expected FAIL got {result['status']}"
        assert result["summary"]["escalate"] == 1
        assert result["summary"]["warn"] == 1
        assert result["summary"]["ok"] == 1
        assert result["items"][0]["id"] == "X-01"  # escalate first

        # Empty input
        result2 = run({})
        assert result2["status"] == "WARN"

        # Smoke flag
        result3 = run({"_smoke": True})
        assert "status" in result3

        # Envelope
        out = aggregate(result, "_smoke")
        assert out["tool"] == TOOL_NAME
        try:
            load_input("/nonexistent/path.json")
            assert False
        except SpecLoadFailed:
            pass
        print("✓ Smoke test PASSED")
        return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}"); return False
    except Exception as e:
        print(f"✗ ERROR: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="Carry Tracker v1.1.0")
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
