#!/usr/bin/env python3
"""
haios_collab_scanner — v1.0
Builder v1.7 compliant · orchestrator_tool
HumanAIOS · S-052426-collab-automation

Scans multiple sources for collaboration signals and outputs a
structured candidate list for Z2 ratification.

Sources:
  gmail   — aioshuman@gmail.com threads (requires Gmail MCP)
  github  — humanaios-ui/operations issues, forks, stars
  slack   — #wgs-sync collaborator mentions (C0AND66PT7U)
  arxiv   — citations of arXiv:2602.20813 + ACAT keyword matches
  supabase — deployment_surface + bars_observer_id novel values

Output:
  {
    "scan_timestamp": "...",
    "sources_scanned": [...],
    "new_candidates": [{
      "candidate_name": "...",
      "source_type": "gmail|github|slack|arxiv|supabase",
      "source_ref": "...",
      "category": "Research|Platform / Technology|Litigation|Case Study",
      "convergence_signals": [...],
      "raw_signal": "...",
      "match_confidence": 0.0,
      "z2_action": "RATIFY_NEW | UPDATE_EXISTING | SKIP"
    }],
    "updates": [{existing entry updates}],
    "z2_queue_items": [...],
    "status": "PASS|WARN|FAIL"
  }

Usage:
  python haios_collab_scanner_v1_0.py --sources gmail,github,slack --output outputs/
  python haios_collab_scanner_v1_0.py --smoke-test
  python haios_collab_scanner_v1_0.py --serve   # FastMCP stdio mode

Zone: Z1 — scanner runs autonomously. Z2 required for new entry ratification.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "haios_collab_scanner"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "orchestrator_tool"
TOOL_SESSION  = "S-052426-collab-automation"
TOOL_ZONE     = 1

# ── Constants ──────────────────────────────────────────────────────────────
HAIOS_ARXIV_ID   = "2602.20813"
SLACK_WGS_CHANNEL = "C0AND66PT7U"
SLACK_MONITOR_CHANNEL = "C0APHCJ5WUE"
GITHUB_ORG       = "humanaios-ui"
GITHUB_REPO      = "operations"
SUPABASE_PROJECT = "ksinisdzgtnqzsymhfya"
CONTACT_EMAIL    = "aioshuman@gmail.com"

# Known collaborators — skip re-adding
KNOWN_COLLAB_IDS = {
    "COL-001": "EmergenceAI / Agent-E",
    "COL-002": "ShiftSmart",
    "COL-003": "Governing Engines",
    "COL-004": "SYCON-Bench (JiseungHong)",
    "COL-005": "PPT-Bench (Steven Au + Sujit Noronha)",
    "COL-006": "idreesaziz / sycophantic-ai-benchmark",
}

# Category inference rules (keyword → category)
CATEGORY_RULES = [
    (["bench", "benchmark", "arxiv", "paper", "research", "dataset", "psych",
      "measurement", "empirical"], "Research"),
    (["lawsuit", "litigation", "court", "legal", "compliance", "regulation",
      "GDPR", "CCPA", "liability"], "Litigation"),
    (["case study", "unit zero", "pilot", "demo", "gig", "rentahuman",
      "taskrabbit", "client"], "Case Study"),
    (["platform", "API", "SDK", "product", "startup", "enterprise", "tool",
      "agent", "workflow", "orchestrat"], "Platform / Technology"),
]

# Convergence signal patterns (regex → signal label)
CONVERGENCE_PATTERNS = [
    (r"sycophancy|sycophantic|syco", "Sycophancy measurement convergence"),
    (r"calibrat|self.report|self.assess", "Self-report calibration alignment"),
    (r"benchmark|eval|evaluat", "Evaluation framework convergence"),
    (r"harm.aware|safety|alignment", "Harm awareness / safety alignment"),
    (r"agentic|agent.e|emergence|skill", "Agentic behavior observability"),
    (r"workforce|labor|human.orchestrat|worker", "Human orchestration convergence"),
    (r"BARS|behavioral.anchor|observer.score", "BARS methodology alignment"),
    (r"drift|normative.drift|consistency", "Behavioral drift detection alignment"),
    (r"litigation|legal.AI|court|compliance", "Legal/regulatory AI accountability"),
]


class SpecLoadFailed(Exception):
    pass


def load_input(source: str) -> dict:
    p = Path(source) if len(source) < 240 else None
    if p is not None and p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {p}: {e}")
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Not a valid path or JSON string: {e}")


def infer_category(text: str) -> str:
    text_lower = text.lower()
    for keywords, category in CATEGORY_RULES:
        if any(kw.lower() in text_lower for kw in keywords):
            return category
    return "Platform / Technology"  # default


def extract_convergence_signals(text: str) -> list:
    signals = []
    text_lower = text.lower()
    for pattern, label in CONVERGENCE_PATTERNS:
        if re.search(pattern, text_lower):
            signals.append(label)
    return signals


def fuzzy_match_known(candidate_name: str) -> tuple:
    """Returns (col_id, match_confidence) or (None, 0.0)."""
    cand_lower = candidate_name.lower()
    for col_id, known_name in KNOWN_COLLAB_IDS.items():
        known_lower = known_name.lower()
        # Exact match
        if cand_lower == known_lower:
            return col_id, 1.0
        # Token overlap
        cand_tokens = set(re.split(r'\W+', cand_lower))
        known_tokens = set(re.split(r'\W+', known_lower))
        overlap = len(cand_tokens & known_tokens) / max(len(cand_tokens | known_tokens), 1)
        if overlap > 0.5:
            return col_id, overlap
    return None, 0.0


# ── Source-specific scanner stubs (MCP-ready) ─────────────────────────────

def scan_gmail(config: dict) -> list:
    """
    Scan Gmail for collaboration signals.
    In live mode: uses Gmail MCP search_threads.
    Returns list of candidate dicts.
    MCP invocation pattern:
      gmail.search_threads(query='to:aioshuman@gmail.com OR from:aioshuman@gmail.com
                                  (ACAT OR HumanAIOS OR collaboration OR partnership)',
                           max_results=50)
    """
    # Stub: return empty in CLI mode; populated when MCP is available
    return config.get("_gmail_results", [])


def scan_github(config: dict) -> list:
    """
    Scan GitHub for external engagement signals.
    Live mode: fetch https://api.github.com/repos/humanaios-ui/operations/issues
               + /stargazers + /forks
    Returns list of candidate dicts.
    """
    return config.get("_github_results", [])


def scan_slack(config: dict) -> list:
    """
    Scan #wgs-sync for new collaborator mentions.
    Live mode: Slack MCP slack_read_channel(channel_id='C0AND66PT7U', limit=50)
               then scan for names not in KNOWN_COLLAB_IDS values.
    """
    return config.get("_slack_results", [])


def scan_arxiv(config: dict) -> list:
    """
    Scan arXiv for papers citing 2602.20813 or mentioning ACAT.
    Live mode: web_search('arXiv 2602.20813 citing papers') +
               web_search('ACAT behavioral calibration AI arXiv 2026')
    Returns list of candidate dicts.
    """
    return config.get("_arxiv_results", [])


def scan_supabase(config: dict) -> list:
    """
    Scan Supabase for novel deployment_surface or observer_id values.
    Live mode: SELECT DISTINCT deployment_surface, bars_observer_notes
               FROM acat_assessments_v1 WHERE bars_score IS NOT NULL
    Returns list of candidate dicts.
    """
    return config.get("_supabase_results", [])


SOURCE_SCANNERS = {
    "gmail":    scan_gmail,
    "github":   scan_github,
    "slack":    scan_slack,
    "arxiv":    scan_arxiv,
    "supabase": scan_supabase,
}


# ── Core run ───────────────────────────────────────────────────────────────

def run(data: dict) -> dict:
    sources_requested = data.get("sources", list(SOURCE_SCANNERS.keys()))
    if isinstance(sources_requested, str):
        sources_requested = [s.strip() for s in sources_requested.split(",")]

    raw_candidates = []
    sources_scanned = []
    warnings = []

    for source in sources_requested:
        scanner = SOURCE_SCANNERS.get(source)
        if scanner is None:
            warnings.append(f"Unknown source: {source}")
            continue
        try:
            results = scanner(data)
            sources_scanned.append(source)
            raw_candidates.extend(results)
        except Exception as e:
            warnings.append(f"Scanner {source} error: {e}")

    # Process candidates
    new_candidates = []
    updates = []
    z2_items = []
    next_col_num = len(KNOWN_COLLAB_IDS) + 1

    for raw in raw_candidates:
        name   = raw.get("name", "Unknown")
        text   = raw.get("text", "") + " " + name
        source_type = raw.get("source_type", "manual")
        source_ref  = raw.get("source_ref", "")

        col_id, confidence = fuzzy_match_known(name)
        category  = infer_category(text)
        signals   = extract_convergence_signals(text)

        if col_id and confidence >= 0.8:
            # Update existing
            updates.append({
                "col_id": col_id,
                "known_name": KNOWN_COLLAB_IDS[col_id],
                "new_signal": raw.get("signal", ""),
                "source_type": source_type,
                "source_ref": source_ref,
                "match_confidence": round(confidence, 3),
            })
        else:
            # New candidate
            candidate_id = f"COL-{next_col_num:03d}-CAND"
            next_col_num += 1
            z2_id = f"NEW-COLLAB-{name[:20].upper().replace(' ','-')}"

            new_candidates.append({
                "candidate_id": candidate_id,
                "candidate_name": name,
                "source_type": source_type,
                "source_ref": source_ref,
                "category": category,
                "convergence_signals": signals,
                "raw_signal": raw.get("signal", ""),
                "match_confidence": round(confidence, 3),
                "z2_action": "RATIFY_NEW",
                "z2_item_id": z2_id,
            })

            z2_items.append({
                "id": z2_id,
                "description": f"New collaboration candidate: {name} ({source_type})",
                "type": "ratification",
                "sessions_open": 1,
                "first_session": data.get("session_id", "UNKNOWN"),
                "last_session": data.get("session_id", "UNKNOWN"),
                "blocker_if_unresolved": False,
                "notes": f"Source: {source_ref}. Category: {category}. Signals: {', '.join(signals[:2])}",
            })

    # Also surface existing Pending Outreach entries as aged Z2 items
    for col_id, name in KNOWN_COLLAB_IDS.items():
        if col_id in ("COL-004", "COL-005", "COL-006"):  # known pending outreach
            z2_items.append({
                "id": f"OUTREACH-{col_id}",
                "description": f"Z2 ratification pending: outreach to {name}",
                "type": "outreach",
                "sessions_open": 2,
                "first_session": "S-052326",
                "last_session": data.get("session_id", "UNKNOWN"),
                "blocker_if_unresolved": False,
                "notes": "GitHub Issues is confirmed contact method. Night Zone 2 ratification required.",
            })

    status = "PASS" if not warnings else "WARN"
    if not sources_scanned and sources_requested:
        status = "WARN"
        warnings.append("No sources successfully scanned — check MCP connectivity")

    return {
        "status": status,
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": data.get("session_id", "UNKNOWN"),
        "sources_scanned": sources_scanned,
        "sources_requested": sources_requested,
        "new_candidates": new_candidates,
        "updates": updates,
        "z2_queue_items": z2_items,
        "warnings": warnings,
        "summary": {
            "sources_scanned": len(sources_scanned),
            "new_candidates": len(new_candidates),
            "updates": len(updates),
            "z2_items": len(z2_items),
        }
    }


def aggregate(run_result: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME, "version": TOOL_VERSION, "zone": TOOL_ZONE,
        "session": TOOL_SESSION, "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source, "result": run_result.get("status", "FAIL"),
        **run_result
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    bar = "=" * 62
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict : {output.get('result', '?')}")
    s = output.get("summary", {})
    print(f" Sources : {s.get('sources_scanned', 0)} scanned")
    print(f" New     : {s.get('new_candidates', 0)} candidates")
    print(f" Updates : {s.get('updates', 0)} existing entries")
    print(f" Z2 queue: {s.get('z2_items', 0)} items")
    for c in output.get("new_candidates", []):
        print(f"   + CANDIDATE  [{c['category'][:12]}]  {c['candidate_name'][:40]}")
        print(f"     Source: {c['source_type']} · confidence={c['match_confidence']}")
    for u in output.get("updates", []):
        print(f"   ↻ UPDATE     {u['col_id']}  {u['known_name'][:35]}")
    if output.get("warnings"):
        print("\n  Warnings:")
        for w in output["warnings"]:
            print(f"    ⚠ {w}")
    print(f"{bar}\n")


def run_smoke_test() -> bool:
    try:
        # Test with injected mock results
        test_data = {
            "session_id": "S-TEST",
            "sources": ["gmail", "github"],
            "_gmail_results": [
                {
                    "name": "Metaculus Research Team",
                    "source_type": "gmail",
                    "source_ref": "thread:1234",
                    "text": "calibration benchmark forecasting research",
                    "signal": "Inbound inquiry about ACAT calibration methodology"
                }
            ],
            "_github_results": [
                {
                    "name": "SycoAI / sycophancy-guard",
                    "source_type": "github",
                    "source_ref": "github.com/SycoAI/sycophancy-guard",
                    "text": "sycophancy resistance benchmark measurement tool",
                    "signal": "New fork of sycophancy benchmark with ACAT-adjacent methodology"
                }
            ],
        }
        result = run(test_data)
        assert result["status"] in ("PASS", "WARN", "FAIL")
        assert result["summary"]["new_candidates"] == 2
        assert result["summary"]["z2_items"] >= 2 + 3  # 2 new + 3 pending outreach
        assert result["new_candidates"][0]["category"] == "Research"

        # Test empty
        result2 = run({"sources": []})
        assert result2["status"] in ("PASS", "WARN")

        # Test aggregate envelope
        out = aggregate(result, "_smoke")
        assert out["tool"] == TOOL_NAME

        # Test SpecLoadFailed
        try:
            load_input("/nonexistent/path.json")
            assert False
        except SpecLoadFailed:
            pass

        print("✓ Smoke test PASSED")
        return True
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{TOOL_NAME} v{TOOL_VERSION} — Collaboration signal scanner"
    )
    parser.add_argument("--input", "-i", help="JSON config file path or inline JSON")
    parser.add_argument(
        "--sources", "-s",
        default="gmail,github,slack,arxiv,supabase",
        help="Comma-separated source list (default: all)"
    )
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--serve", action="store_true", help="FastMCP stdio mode")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.serve:
        try:
            from fastmcp import FastMCP
            mcp = FastMCP(TOOL_NAME)

            @mcp.tool
            def collab_scanner(config: dict) -> dict:
                """Scan Gmail, GitHub, Slack, arXiv, and Supabase for collaboration signals."""
                return run(config)

            mcp.run()
        except ImportError:
            print("ERROR: fastmcp not installed. Run: pip install fastmcp")
            sys.exit(1)
        return

    # Build config from args
    if args.input:
        try:
            data = load_input(args.input)
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        data = {}

    data["sources"] = [s.strip() for s in args.sources.split(",")]

    run_result = run(data)
    output = aggregate(run_result, args.input or "cli")
    rp = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")
    sys.exit(0 if output["result"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
