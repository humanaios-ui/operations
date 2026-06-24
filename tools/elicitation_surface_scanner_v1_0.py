#!/usr/bin/env python3
"""
Elicitation Surface Scanner — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-062326 · drafted in response to a real, found instance of
the failure class it scans for (see KNOWN_FINDINGS below).

PURPOSE
Every place the project collects ACAT data — assess.html, the FastAPI
routes, the MCP wrapper, any homepage prompt, any future surface — is
an "elicitation surface." If two surfaces disagree on dimension count,
field names, or instrument_variant tagging, the corpus silently
accumulates non-equivalent rows (H-ELICIT-01 / F-52 territory) without
anyone deciding that should happen.

This tool does not fix surfaces. It reports where they disagree with
the canonical schema and with each other, so a human (or the next
Claude session) makes that call explicitly instead of by accident.

CANONICAL SCHEMA SOURCE
The canonical 12-dimension list below was read directly from
information_schema.columns on the live acat_assessments_v1 table
(Supabase project ksinisdzgtnqzsymhfya) on 2026-06-23. This is a
*frozen snapshot*, not a live connection — re-verify against the
live schema before trusting this file's CANONICAL_DIMENSIONS blindly
six months from now. fetch_live_schema() below shows how to re-pull it
when SUPABASE_URL / SUPABASE_KEY are available; it is not called by
default so this tool has no network dependency to run.

KNOWN_FINDINGS (as of 2026-06-23, this session)
- supabase_corpus_connector_v1_0_2.py and corpus_integrity_validator_v1_1.py
  both hardcode a 6-dimension flat-column schema (truth, service, harm,
  autonomy, value, humility, total, phase, pre_total, post_total).
  corpus_integrity_validator targets the legacy CSV/frozen-archive
  corpus — that schema is correct for ITS job. supabase_corpus_connector
  targets the LIVE Supabase table, which has moved to a 12-dimension,
  p1_/p3_-prefixed schema. That connector's CANONICAL_COLUMNS constant
  is stale relative to what it actually connects to.
- assess.html (project-knowledge copy, header says "v1.0 · 11
  dimensions") has no Handoff dimension. The live table has p1_handoff
  / p3_handoff columns, and ACAT_V5_4_TIER2_PROMPT marks Handoff
  required from S-052726 forward. Unresolved as of this scan: is
  assess.html stale, or is Handoff intentionally optional outside the
  Tier 2 arm? This tool flags it; it does not resolve it.

Usage:
  python elicitation_surface_scanner_v1_0.py --scan FILE [FILE ...]
  python elicitation_surface_scanner_v1_0.py --scan FILE --json
  python elicitation_surface_scanner_v1_0.py --smoke-test
"""

import argparse
import json
import re
import sys
from pathlib import Path

TOOL_NAME = "elicitation_surface_scanner"
TOOL_VERSION = "1.0.0"

# Canonical 12-dimension schema, frozen snapshot per header above.
CANONICAL_DIMENSIONS = [
    "truth", "service", "harm", "autonomy", "value", "humility",
    "scheme", "power", "syc", "consist", "fair", "handoff",
]
CANONICAL_P1_FIELDS = {f"p1_{d}" for d in CANONICAL_DIMENSIONS}
CANONICAL_P3_FIELDS = {f"p3_{d}" for d in CANONICAL_DIMENSIONS}
LEGACY_FLAT_FIELDS = {
    "truth", "service", "harm", "autonomy", "value", "humility",
    "total", "phase", "pre_total", "post_total",
}


def fetch_live_schema(supabase_url, supabase_key):
    """Re-pull the live column list. Not called by default — no network
    dependency for normal runs. Mirrors supabase_corpus_connector's auth
    pattern (anon key, REST API, no service_role needed)."""
    from urllib.request import Request, urlopen
    url = f"{supabase_url}/rest/v1/acat_assessments_v1?limit=1"
    req = Request(url, headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"})
    with urlopen(req, timeout=10) as resp:
        rows = json.loads(resp.read().decode("utf-8"))
    return sorted(rows[0].keys()) if rows else []


def extract_assess_html_dims(text):
    """assess.html declares dims as JS array literals: {id:'truth', ...}
    inside CORE_DIMS = [...] and EXT_DIMS = [...]."""
    found = set()
    for block_name in ("CORE_DIMS", "EXT_DIMS"):
        m = re.search(rf"{block_name}\s*=\s*\[(.*?)\];", text, re.DOTALL)
        if m:
            found.update(re.findall(r"id\s*:\s*'(\w+)'", m.group(1)))
    return found


def extract_prefixed_fields(text):
    """Any surface (homepage prompt JSON, API payload examples) that
    uses p1_xxx / p3_xxx field names in quoted-key position. Only counts
    a match if the suffix is a known dimension name -- p1_timestamp,
    p3_committed_at, etc. are legitimate metadata fields, not missing
    dimension scores, and must not trigger a false flag. (Found as a
    real false positive against phase1_intake.schema.json /
    phase3_submission.schema.json, S-062326 — fixed same session.)"""
    candidates = re.findall(r'"(p[13]_\w+)"\s*:', text)
    return {f for f in candidates if f.split("_", 1)[1] in CANONICAL_DIMENSIONS}


def extract_json_schema_scores(text):
    """JSON Schema contracts (acat/contracts/*.schema.json) declare the
    accepted score keys under a nested "scores" -> "required": [...] list,
    UNPREFIXED (truth, service, ... not p1_truth). This is a distinct
    failure mode from the p1_/p3_ check above: it catches payload-shape
    drift (e.g. a client sending p1_truth at the top level when the
    contract requires {"scores": {"truth": ...}}), which the live-table
    column check cannot see. Found via this exact bug on the homepage
    Copy & Paste / REST API panels, S-062326."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return set()
    scores_block = data.get("properties", {}).get("scores", {})
    return set(scores_block.get("required", []))



def extract_python_const_list(text, varnames):
    """Python list-literal constants like CANONICAL_COLUMNS = [...]."""
    found = set()
    for var in varnames:
        m = re.search(rf"{var}\s*=\s*\[(.*?)\]", text, re.DOTALL)
        if m:
            found.update(re.findall(r'"(\w+)"', m.group(1)))
    return found


def classify_and_compare(surface_name, found):
    """Returns a result dict. Distinguishes 'targets legacy flat schema'
    from 'targets live p1_/p3_ schema' before diffing, so a legacy-schema
    surface doesn't get flagged as missing 12 dimensions it never claimed
    to have."""
    result = {"surface": surface_name, "found_fields": sorted(found)}

    looks_prefixed = any(f.startswith(("p1_", "p3_")) for f in found)
    core_six = {"truth", "service", "harm", "autonomy", "value", "humility"}
    non_dim_aux = found - set(CANONICAL_DIMENSIONS)
    looks_bare_dims = bool(found) and (not looks_prefixed) and not non_dim_aux
    looks_legacy_flat = (not looks_prefixed) and (not looks_bare_dims) and core_six.issubset(found)

    if looks_prefixed:
        result["schema_type"] = "live_prefixed_p1_p3"
        missing = (CANONICAL_P1_FIELDS | CANONICAL_P3_FIELDS) - found
        extra = found - (CANONICAL_P1_FIELDS | CANONICAL_P3_FIELDS)
        result["missing"] = sorted(missing)
        result["unexpected"] = sorted(extra)
        result["status"] = "OK" if not missing else "INCOMPLETE"
    elif looks_legacy_flat:
        result["schema_type"] = "legacy_flat_csv"
        result["status"] = "OK_BUT_VERIFY_INTENTIONAL"
        result["auxiliary_fields"] = sorted(found - core_six)
        result["note"] = (
            "Matches the legacy flat CSV schema (core six unprefixed), not the "
            "live 12-dim p1_/p3_ Supabase schema. Correct if this surface targets "
            "the frozen archive; stale if it targets the live table."
        )
    elif looks_bare_dims:
        result["schema_type"] = "bare_dimension_ids"
        missing = set(CANONICAL_DIMENSIONS) - found
        extra = found - set(CANONICAL_DIMENSIONS)
        result["missing"] = sorted(missing)
        result["unexpected"] = sorted(extra)
        result["status"] = "OK" if not missing else "INCOMPLETE"
    else:
        result["schema_type"] = "unrecognized"
        result["status"] = "UNRECOGNIZED"

    return result


def scan_file(path):
    text = Path(path).read_text(errors="replace")
    name = Path(path).name

    surfaces = []
    dims = extract_assess_html_dims(text)
    if dims:
        surfaces.append(classify_and_compare(f"{name} [JS dim arrays]", dims))

    prefixed = extract_prefixed_fields(text)
    if prefixed:
        surfaces.append(classify_and_compare(f"{name} [p1_/p3_ fields]", prefixed))

    cols = extract_python_const_list(
        text, ["CANONICAL_COLUMNS", "REQUIRED_COLUMNS", "SCORE_COLUMNS"]
    )
    if cols:
        surfaces.append(classify_and_compare(f"{name} [python column const]", cols))

    schema_scores = extract_json_schema_scores(text)
    if schema_scores:
        surfaces.append(classify_and_compare(f"{name} [JSON Schema scores.required]", schema_scores))

    if not surfaces:
        surfaces.append({"surface": name, "status": "NO_SURFACE_DETECTED",
                          "note": "No known extractor pattern matched this file."})
    return surfaces


def run_smoke_test():
    cases_passed = 0
    # Case 1: full 12-dim prefixed surface -> OK
    full = {f"p1_{d}" for d in CANONICAL_DIMENSIONS} | {f"p3_{d}" for d in CANONICAL_DIMENSIONS}
    r = classify_and_compare("smoke:full", full)
    assert r["status"] == "OK", r
    cases_passed += 1
    # Case 2: 6-dim-only prefixed surface -> INCOMPLETE, reports the missing 6
    six = {f"p1_{d}" for d in CANONICAL_DIMENSIONS[:6]} | {f"p3_{d}" for d in CANONICAL_DIMENSIONS[:6]}
    r = classify_and_compare("smoke:six_only", six)
    assert r["status"] == "INCOMPLETE" and len(r["missing"]) == 12, r
    cases_passed += 1
    # Case 3: legacy flat schema -> flagged for human confirmation, not auto-failed
    r = classify_and_compare("smoke:legacy", LEGACY_FLAT_FIELDS)
    assert r["status"] == "OK_BUT_VERIFY_INTENTIONAL", r
    cases_passed += 1
    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test: {cases_passed}/3 cases passed")
    return cases_passed == 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", nargs="+", help="File paths to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        ok = run_smoke_test()
        sys.exit(0 if ok else 1)

    if not args.scan:
        parser.print_help()
        sys.exit(1)

    report = {"tool": TOOL_NAME, "version": TOOL_VERSION, "results": []}
    any_problem = False
    for path in args.scan:
        for r in scan_file(path):
            report["results"].append(r)
            if r.get("status") not in ("OK",):
                any_problem = True

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report["results"]:
            print(f"\n[{r['status']}] {r['surface']}")
            if r.get("schema_type"):
                print(f"  schema_type: {r['schema_type']}")
            if r.get("missing"):
                print(f"  missing: {r['missing']}")
            if r.get("unexpected"):
                print(f"  unexpected: {r['unexpected']}")
            if r.get("note"):
                print(f"  note: {r['note']}")

    sys.exit(1 if any_problem else 0)


if __name__ == "__main__":
    main()
