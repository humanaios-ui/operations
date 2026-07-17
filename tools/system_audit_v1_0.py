#!/usr/bin/env python3
"""
System Audit — v1.0
Builder v1.7 compliant · orchestrator_tool
HumanAIOS · S-052326-03 (run() implemented)

Single-command pre-flight: checks GitHub raw URL reachability,
Supabase row count, Cloudflare zone alias, CURRENT.md age.
PASS/WARN/FAIL in under 30 seconds.

Input format:
{
  "checks": {
    "github_raw_url":     "https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md",
    "supabase_row_count": 629,
    "supabase_deadline_days": 7,
    "current_md_age_days": 2,
    "cf_zones": ["humanaios.ai","ops.humanaios.ai"],
    "cf_zones_healthy": ["humanaios.ai","ops.humanaios.ai"],
    "carry_count": 8,
    "gate_active": 2,
    "gate_passed": [1]
  }
}

NOTE: This tool operates in analysis mode (no live network calls) —
it validates the pre-fetched state snapshot passed by the operator.
For live fetches, the governance_fetcher tool is the correct tool.
"""

import json, sys, argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "system_audit"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "orchestrator_tool"
TOOL_SESSION  = "S-052326-03"
TOOL_ZONE     = 1

# Thresholds
SUPABASE_DEADLINE_WARN     = 14   # days
SUPABASE_DEADLINE_CRITICAL = 7
CURRENT_MD_STALE_DAYS      = 7
CARRY_WARN                 = 5
CARRY_ESCALATE             = 10
CORPUS_MIN_ROWS            = 600  # expected minimum

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
    checks = data.get("checks", {})
    if not checks and "_smoke" not in data:
        return {"status":"WARN","items":[],"warnings":["No checks provided — pass checks{} dict"],
                "summary":{"total":0,"pass":0,"warn":0,"fail":0}}

    items = []
    warnings = []

    def check(name, status, detail, action=None):
        items.append({"check":name,"status":status,"detail":detail,"action":action or ""})
        if status in ("WARN","FAIL"):
            warnings.append(f"{status}: {name} — {detail}")

    # ── GitHub raw URL reachability ─────────────────────────────────────────
    gh_url = checks.get("github_raw_url")
    gh_reachable = checks.get("github_raw_reachable", None)
    if gh_url:
        if gh_reachable is False:
            check("github_raw", "FAIL", f"URL unreachable: {gh_url}",
                  "Verify network, repo visibility, and URL path")
        elif gh_reachable is True:
            check("github_raw", "PASS", f"URL reachable: {gh_url}")
        else:
            check("github_raw", "WARN", f"Reachability not tested for: {gh_url}",
                  "Run governance_fetcher to verify")

    # ── Supabase row count ──────────────────────────────────────────────────
    row_count = checks.get("supabase_row_count")
    if row_count is not None:
        if row_count < CORPUS_MIN_ROWS:
            check("supabase_rows", "WARN",
                  f"Row count {row_count} below expected {CORPUS_MIN_ROWS}",
                  "Verify corpus — may have pending rows not yet ingested")
        else:
            check("supabase_rows", "PASS", f"Row count {row_count} OK")

    # ── Supabase deadline ───────────────────────────────────────────────────
    days_left = checks.get("supabase_deadline_days")
    if days_left is not None:
        if days_left <= SUPABASE_DEADLINE_CRITICAL:
            check("supabase_deadline", "FAIL",
                  f"API change deadline in {days_left} days — CRITICAL",
                  "Execute endorse_event Option B + table GRANTs immediately")
        elif days_left <= SUPABASE_DEADLINE_WARN:
            check("supabase_deadline", "WARN",
                  f"API change deadline in {days_left} days",
                  "Schedule Supabase schema migration this week")
        else:
            check("supabase_deadline", "PASS", f"Supabase deadline in {days_left} days")

    # ── CURRENT.md age ──────────────────────────────────────────────────────
    current_md_age = checks.get("current_md_age_days")
    if current_md_age is not None:
        if current_md_age > CURRENT_MD_STALE_DAYS:
            check("current_md_age", "WARN",
                  f"CURRENT.md is {current_md_age} days old",
                  "Update CURRENT.md to reflect active session state")
        else:
            check("current_md_age", "PASS", f"CURRENT.md age: {current_md_age} days")

    # ── Cloudflare zones ────────────────────────────────────────────────────
    cf_zones         = checks.get("cf_zones", [])
    cf_zones_healthy = set(checks.get("cf_zones_healthy", []))
    for zone in cf_zones:
        if zone in cf_zones_healthy:
            check(f"cf_zone_{zone}", "PASS", f"CF zone {zone} LIVE")
        else:
            check(f"cf_zone_{zone}", "WARN", f"CF zone {zone} not confirmed healthy",
                  f"Check CF dashboard for {zone}")

    # ── Carry count ─────────────────────────────────────────────────────────
    carry = checks.get("carry_count")
    if carry is not None:
        if carry >= CARRY_ESCALATE:
            check("carry_count", "FAIL", f"System carry count N={carry} — ESCALATE",
                  "Dedicated session needed to clear carry backlog")
        elif carry >= CARRY_WARN:
            check("carry_count", "WARN", f"System carry count N={carry}",
                  "Include carry-reduction in next session agenda")
        else:
            check("carry_count", "PASS", f"System carry count N={carry}")

    # ── Gate status ─────────────────────────────────────────────────────────
    gate_active = checks.get("gate_active")
    gate_passed = checks.get("gate_passed", [])
    if gate_active is not None:
        check("gate_status", "PASS",
              f"Gate {gate_active} active, gates {gate_passed} passed")

    # ── Smoke fallback ───────────────────────────────────────────────────────
    if not items:
        items.append({"check":"_smoke","status":"PASS","detail":"Smoke run — no checks provided","action":""})

    n_pass = sum(1 for i in items if i["status"]=="PASS")
    n_warn = sum(1 for i in items if i["status"]=="WARN")
    n_fail = sum(1 for i in items if i["status"]=="FAIL")
    status = "FAIL" if n_fail>0 else ("WARN" if n_warn>0 else "PASS")

    return {
        "status": status,
        "items":  items,
        "warnings": warnings,
        "summary": {"total":len(items),"pass":n_pass,"warn":n_warn,"fail":n_fail},
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
    print(f" Checks  : {s.get('total',0)}  PASS={s.get('pass',0)}  WARN={s.get('warn',0)}  FAIL={s.get('fail',0)}")
    for item in output.get("items",[]):
        sym = "✓" if item["status"]=="PASS" else ("⚠" if item["status"]=="WARN" else "✗")
        print(f"   {sym} {item['status']:<4}  {item['check']:<30}  {item['detail'][:40]}")
    print(f"{bar}\n")

def run_smoke_test():
    try:
        result = run({"checks":{
            "supabase_row_count": 629,
            "supabase_deadline_days": 7,
            "current_md_age_days": 2,
            "carry_count": 8,
            "gate_active": 2, "gate_passed": [1],
            "cf_zones": ["humanaios.ai"], "cf_zones_healthy": ["humanaios.ai"],
        }})
        assert result["status"] in ("PASS","WARN","FAIL")
        assert result["summary"]["fail"] >= 1  # supabase deadline <= 7 = FAIL
        assert any(i["check"]=="supabase_deadline" for i in result["items"])

        # Empty
        result2 = run({})
        assert result2["status"]=="WARN"

        out = aggregate(result, "_smoke")
        assert out["tool"]==TOOL_NAME
        try: load_input("/nonexistent.json"); assert False
        except SpecLoadFailed: pass
        print("✓ Smoke test PASSED"); return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}"); return False
    except Exception as e:
        print(f"✗ ERROR: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="System Audit v1.1.0")
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
