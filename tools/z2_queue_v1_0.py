#!/usr/bin/env python3
"""
Z2 Queue — v1.0
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-052326-03 (run() implemented)

Reads WGS posts or a Z2 manifest, extracts Zone 2 pending items,
deduplicates by id, surfaces oldest-first, flags N>=3 sessions unresolved.

Input format:
{
  "z2_items": [
    {
      "id":           "FP-04",
      "description":  "HIM x EW Normative Drift",
      "type":         "finding" | "decision" | "ratification" | "outreach",
      "sessions_open": 2,
      "first_session": "S-050526-01",
      "last_session":  "S-052326-03",
      "notes":         "optional context",
      "blocker_if_unresolved": false
    }
  ],
  "session_id": "S-052326-03"
}

Output:
- PASS: all items resolved or age < 3 sessions
- WARN: items aged 3+ sessions unresolved
- FAIL: blocker_if_unresolved=true and item unresolved
"""

import json, sys, argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "z2_queue"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_SESSION  = "S-052326-03"
TOOL_ZONE     = 1

AGE_WARN_SESSIONS    = 3
AGE_ESCALATE_SESSIONS = 5

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
    raw_items = data.get("z2_items", [])
    if not raw_items and "_smoke" not in data:
        return {"status":"WARN","items":[],"warnings":["No z2_items provided"],
                "summary":{"total":0,"resolved":0,"aged":0,"blocked":0,"ok":0}}

    # Deduplicate by id (keep highest sessions_open)
    seen = {}
    for item in raw_items:
        iid = item.get("id","UNKNOWN")
        if iid not in seen or item.get("sessions_open",0) > seen[iid].get("sessions_open",0):
            seen[iid] = item

    items = []
    warnings = []

    for raw in seen.values():
        iid         = raw.get("id","UNKNOWN")
        desc        = raw.get("description","")
        itype       = raw.get("type","ratification")
        n           = int(raw.get("sessions_open",0))
        first       = raw.get("first_session","unknown")
        last        = raw.get("last_session","unknown")
        notes       = raw.get("notes","")
        is_blocker  = bool(raw.get("blocker_if_unresolved", False))
        resolved    = bool(raw.get("resolved", False))

        if resolved:
            status = "RESOLVED"
        elif is_blocker and n > 0:
            status = "BLOCKED"
            warnings.append(f"BLOCKED: {iid} is a blocker — unresolved {n} sessions")
        elif n >= AGE_ESCALATE_SESSIONS:
            status = "ESCALATE"
            warnings.append(f"ESCALATE: {iid} unresolved {n} sessions (>{AGE_ESCALATE_SESSIONS})")
        elif n >= AGE_WARN_SESSIONS:
            status = "AGED"
            warnings.append(f"AGED: {iid} unresolved {n} sessions (>{AGE_WARN_SESSIONS})")
        else:
            status = "PENDING"

        items.append({
            "id": iid, "status": status, "type": itype,
            "sessions_open": n, "first_session": first, "last_session": last,
            "description": desc, "notes": notes, "blocker": is_blocker,
        })

    # Sort: BLOCKED first, then ESCALATE, AGED, PENDING, RESOLVED; within group by sessions_open desc
    priority = {"BLOCKED":0,"ESCALATE":1,"AGED":2,"PENDING":3,"RESOLVED":4}
    items.sort(key=lambda x: (priority.get(x["status"],5), -x["sessions_open"]))

    n_blocked  = sum(1 for i in items if i["status"]=="BLOCKED")
    n_escalate = sum(1 for i in items if i["status"]=="ESCALATE")
    n_aged     = sum(1 for i in items if i["status"]=="AGED")
    n_pending  = sum(1 for i in items if i["status"]=="PENDING")
    n_resolved = sum(1 for i in items if i["status"]=="RESOLVED")

    status = "FAIL" if n_blocked>0 else ("WARN" if (n_escalate+n_aged)>0 else "PASS")

    return {
        "status": status,
        "items":  items,
        "warnings": warnings,
        "summary": {
            "total":    len(items),
            "blocked":  n_blocked,
            "escalate": n_escalate,
            "aged":     n_aged,
            "pending":  n_pending,
            "resolved": n_resolved,
        }
    }

def aggregate(run_result, source):
    return {"tool":TOOL_NAME,"version":TOOL_VERSION,"zone":TOOL_ZONE,
            "session":TOOL_SESSION,"timestamp":datetime.now(timezone.utc).isoformat(),
            "source":source,"result":run_result.get("status","FAIL"),**run_result}

def write_report(output, output_dir):
    p = Path(output_dir); p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output,indent=2),encoding="utf-8")
    return str(path)

def print_summary(output):
    bar = "=" * 60
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict : {output.get('result','?')}")
    s = output.get("summary",{})
    print(f" Total={s.get('total',0)}  BLOCKED={s.get('blocked',0)}  AGED={s.get('aged',0)}  PENDING={s.get('pending',0)}  RESOLVED={s.get('resolved',0)}")
    STATUS_SYM = {"BLOCKED":"🔴","ESCALATE":"🟠","AGED":"🟡","PENDING":"⚪","RESOLVED":"✓"}
    for item in output.get("items",[]):
        sym = STATUS_SYM.get(item["status"],"?")
        blocker_flag = " [BLOCKER]" if item.get("blocker") else ""
        print(f"  {sym} {item['status']:<8} N={item['sessions_open']:>2}  {item['id']}{blocker_flag}")
        if item.get("description"): print(f"             {item['description'][:55]}")
    if output.get("warnings"):
        print("\n  Warnings:")
        for w in output["warnings"]: print(f"    ⚠ {w}")
    print(f"{bar}\n")

def run_smoke_test():
    try:
        result = run({"z2_items":[
            {"id":"FP-04","description":"HIM drift","type":"finding","sessions_open":4,"blocker_if_unresolved":False},
            {"id":"TIER1-OUTREACH","description":"Ratify outreach","type":"ratification","sessions_open":2,"blocker_if_unresolved":True},
            {"id":"P-ANON","description":"Add to GOVERNANCE","type":"decision","sessions_open":3,"blocker_if_unresolved":False},
            {"id":"OLD-DONE","description":"Resolved item","type":"decision","sessions_open":1,"resolved":True},
        ]})
        assert result["summary"]["blocked"] == 1   # TIER1-OUTREACH is blocker
        assert result["summary"]["aged"] >= 1
        assert result["summary"]["resolved"] == 1
        assert result["status"] == "FAIL"          # blocked → FAIL
        assert result["items"][0]["id"] == "TIER1-OUTREACH"  # blocked first

        result2 = run({})
        assert result2["status"] == "WARN"

        out = aggregate(result,"_smoke")
        assert out["tool"]==TOOL_NAME
        try: load_input("/nonexistent.json"); assert False
        except SpecLoadFailed: pass
        print("✓ Smoke test PASSED"); return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}"); return False
    except Exception as e:
        print(f"✗ ERROR: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="Z2 Queue v1.1.0")
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
