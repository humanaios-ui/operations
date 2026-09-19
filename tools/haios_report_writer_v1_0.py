#!/usr/bin/env python3
"""
HAIOS Report Writer — v1.0
Builder v1.7 compliant · Step 11 reading/writing tool
HumanAIOS · S-052026-01

Converts structured JSON output from any HAIOS pipeline stage into
human-readable reports in Markdown (default), Slack-formatted text,
or HTML. The report writer is the articulation layer — the pipeline
surfaces what IS; the report writer turns that into language Night
and Zone 2 can act on without opening a JSON file.

Design principle: The human does the conscience work. The report
does the friction work. No data hunting. Every Z2 decision arrives
with the full context pre-assembled.

Can be invoked standalone or as a pipeline stage.

Usage:
    python haios_report_writer_v1_0.py --input <json_path_or_string>
    python haios_report_writer_v1_0.py --pipeline-result <json>
    python haios_report_writer_v1_0.py --format slack|markdown|html
    python haios_report_writer_v1_0.py --smoke-test
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TOOL_NAME = "haios_report_writer"
TOOL_VERSION = "1.0.0"
SESSION_ID = "S-052026-01"

# ACAT 12 dimensions in display order
DIMENSIONS_12 = [
    ("truth",    "Truthfulness"),
    ("service",  "Service Orientation"),
    ("harm",     "Harm Awareness"),
    ("autonomy", "Autonomy Respect"),
    ("value",    "Value Alignment"),
    ("humility", "Humility"),
    ("scheme",   "Scheme Resistance"),
    ("power",    "Power Distribution"),
    ("syc",      "Sycophancy Resistance"),
    ("consist",  "Consistency"),
    ("fair",     "Fairness"),
    ("handoff",  "Handoff Clarity"),
]

CORPUS_MEAN_LI = 0.8632


# ---------------------------------------------------------------------------
# Score bar helpers
# ---------------------------------------------------------------------------

def score_bar(score: float, width: int = 20) -> str:
    """ASCII progress bar for a 0-100 score."""
    filled = int((score / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {score:.0f}"


def li_delta_str(li: float) -> str:
    delta = li - CORPUS_MEAN_LI
    sign = "+" if delta >= 0 else ""
    return f"LI={li:.4f} ({sign}{delta:.4f} vs corpus mean {CORPUS_MEAN_LI})"


def status_emoji(status: str) -> str:
    return {
        "PASS": "✅",
        "WARN": "⚠️",
        "FAIL": "❌",
        "SKIP": "⏭️",
    }.get(status.upper(), "❓")


# ---------------------------------------------------------------------------
# Markdown report builder
# ---------------------------------------------------------------------------

def build_markdown_report(data: Dict[str, Any], report_type: str = "PIPELINE") -> str:
    lines: List[str] = []
    ts = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    session_id = data.get("session_id", "UNKNOWN")
    pipeline_name = data.get("pipeline_name", report_type)
    overall = data.get("overall_status", "UNKNOWN")

    lines.append(f"# HAIOS Report — {pipeline_name}")
    lines.append(f"**Session:** {session_id}  ")
    lines.append(f"**Time:** {ts}  ")
    lines.append(f"**Status:** {status_emoji(overall)} {overall}")
    lines.append("")

    # Z2 alert
    if data.get("z2_required"):
        lines.append("---")
        lines.append("## 🔴 ZONE 2 REVIEW REQUIRED")
        lines.append(f"> {data.get('z2_reason', 'Human decision required.')}")
        lines.append("")

    # Pipeline stage results
    stage_results = data.get("stage_results", [])
    if stage_results:
        lines.append("---")
        lines.append("## Pipeline Stages")
        lines.append("")
        for sr in stage_results:
            st = sr.get("status", "UNKNOWN")
            desc = sr.get("description") or sr.get("tool_name", "")
            tool = sr.get("tool_name", "")
            err = sr.get("error")
            dur = sr.get("duration_ms", 0)
            lines.append(f"### {status_emoji(st)} Stage {sr.get('stage_index', '?')}: {desc}")
            lines.append(f"**Tool:** `{tool}`  **Duration:** {dur}ms  **Status:** {st}")
            if err:
                lines.append(f"> **Error:** {err}")
            out = sr.get("output", {})
            if out and st != "SKIP":
                # Render known output shapes
                _render_output_md(lines, out, tool)
            lines.append("")

    # Accumulated ACAT dimension scores (if present)
    _render_dimension_scores_md(lines, data.get("accumulated_outputs", {}))

    # Corpus state (if present)
    corpus = data.get("corpus_state") or data.get("accumulated_outputs", {})
    n_total = corpus.get("n_total")
    n_li = corpus.get("n_li")
    mean_li_val = corpus.get("mean_li")
    if n_total or n_li or mean_li_val:
        lines.append("---")
        lines.append("## Corpus State")
        if n_total:
            lines.append(f"- N_total={n_total}")
        if n_li:
            lines.append(f"- N_LI={n_li}")
        if mean_li_val:
            lines.append(f"- Mean LI={mean_li_val:.4f}")
        lines.append("")

    # Error log
    error_log = data.get("error_log", [])
    if error_log:
        lines.append("---")
        lines.append("## Error Log")
        for e in error_log:
            lines.append(f"- {e}")
        lines.append("")

    # Document analysis (standalone mode)
    if report_type == "DOCUMENT":
        _render_document_report_md(lines, data)

    # Repo analysis (standalone mode)
    if report_type == "REPO":
        _render_repo_report_md(lines, data)

    # Footer
    lines.append("---")
    lines.append(f"*Generated by {TOOL_NAME} v{TOOL_VERSION} · "
                 f"Session {session_id} · Unit Zero · Claude*")
    lines.append("")

    return "\n".join(lines)


def _render_output_md(lines: List[str], out: Dict[str, Any], tool: str) -> None:
    """Render tool output as markdown, with special handling for known shapes."""
    # Protocol auditor
    if "overall_verdict" in out:
        lines.append(f"- **Verdict:** {out['overall_verdict']}")
        if out.get("resonance_score") is not None:
            lines.append(f"- **Resonance:** {out['resonance_score']}/100")
        for hf in out.get("hard_failures", []):
            lines.append(f"  - ❌ Hard: {hf}")
        for sf in out.get("soft_failures", []):
            lines.append(f"  - ⚠️ Soft: {sf}")
        return

    # Repo analyzer signals
    if "signals" in out:
        focus = out.get("recommended_issue_focus", "")
        if focus:
            lines.append(f"- **Focus:** {focus}")
        sigs = out.get("signals", {})
        for dim, findings in sigs.items():
            if findings:
                lines.append(f"- **{dim}:**")
                for f in (findings if isinstance(findings, list) else [findings]):
                    lines.append(f"  - {f}")
        return

    # Dimension scores (flat keys)
    dim_keys = {k for k, _ in DIMENSIONS_12}
    found_dims = {k: v for k, v in out.items() if k in dim_keys and isinstance(v, (int, float))}
    if found_dims:
        for key, label in DIMENSIONS_12:
            if key in found_dims:
                lines.append(f"- **{label}:** {score_bar(found_dims[key])}")
        return

    # Generic key-value
    for k, v in out.items():
        if isinstance(v, (str, int, float, bool)):
            lines.append(f"- **{k}:** {v}")


def _render_dimension_scores_md(lines: List[str], accumulated: Dict[str, Any]) -> None:
    """Render ACAT dimension scores if present in accumulated outputs."""
    dim_keys = {k for k, _ in DIMENSIONS_12}
    scores = {k: v for k, v in accumulated.items()
              if k in dim_keys and isinstance(v, (int, float))}
    if not scores:
        return
    lines.append("---")
    lines.append("## ACAT Dimension Scores")
    lines.append("")
    for key, label in DIMENSIONS_12:
        if key in scores:
            lines.append(f"- **{label}:** {score_bar(scores[key])}")
    lines.append("")


def _render_document_report_md(lines: List[str], data: Dict[str, Any]) -> None:
    doc_name = data.get("document_name", "")
    li = data.get("li")
    if doc_name:
        lines.append("---")
        lines.append(f"## Document: {doc_name}")
    if li is not None:
        lines.append(f"**{li_delta_str(li)}**")
    lines.append("")


def _render_repo_report_md(lines: List[str], data: Dict[str, Any]) -> None:
    repo_url = data.get("repo_url", "")
    if repo_url:
        lines.append("---")
        lines.append(f"## Repo: {repo_url}")
    lines.append("")


# ---------------------------------------------------------------------------
# Slack format builder
# ---------------------------------------------------------------------------

def build_slack_report(data: Dict[str, Any]) -> str:
    """Produce a compact Slack-formatted report (no markdown headers,
    uses Unicode dividers per HAIOS WGS post format)."""
    lines: List[str] = []
    ts = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    session_id = data.get("session_id", "UNKNOWN")
    pipeline_name = data.get("pipeline_name", "PIPELINE")
    overall = data.get("overall_status", "UNKNOWN")

    divider = "━" * 40
    lines.append(divider)
    lines.append(f"🔬 *HAIOS Pipeline Report · {pipeline_name}*")
    lines.append(f"Session: {session_id} · {ts[:19]} UTC")
    lines.append(f"Status: {status_emoji(overall)} *{overall}*")
    lines.append(divider)

    # Z2 alert
    if data.get("z2_required"):
        lines.append("🔴 *ZONE 2 REVIEW REQUIRED*")
        lines.append(f"> {data.get('z2_reason', 'Human decision required.')}")
        lines.append("")

    # Stage summary (compact)
    stage_results = data.get("stage_results", [])
    if stage_results:
        lines.append("*Stages:*")
        for sr in stage_results:
            st = sr.get("status", "?")
            desc = sr.get("description") or sr.get("tool_name", "")
            dur = sr.get("duration_ms", 0)
            err = sr.get("error", "")
            line = f"{status_emoji(st)} {desc} ({dur}ms)"
            if err and st == "FAIL":
                line += f" — {err[:80]}"
            lines.append(line)
        lines.append("")

    # Dimension scores (compact)
    acc = data.get("accumulated_outputs", {})
    dim_keys = {k for k, _ in DIMENSIONS_12}
    scores = {k: v for k, v in acc.items()
              if k in dim_keys and isinstance(v, (int, float))}
    if scores:
        lines.append("*ACAT Scores:*")
        pairs = []
        for key, label in DIMENSIONS_12:
            if key in scores:
                pairs.append(f"{label[:10]}: {scores[key]:.0f}")
        # Two per line
        for i in range(0, len(pairs), 2):
            lines.append("  " + "  |  ".join(pairs[i:i+2]))
        lines.append("")

    # Errors
    error_log = data.get("error_log", [])
    if error_log:
        lines.append("*Errors:*")
        for e in error_log[:5]:
            lines.append(f"• {e}")
        lines.append("")

    lines.append(divider)
    lines.append(f"🦅 Wado · Unit Zero · {session_id} · Claude")
    lines.append("_Sent using Claude_")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# run() interface (pipeline stage entry point)
# ---------------------------------------------------------------------------

def run(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Pipeline stage interface.

    Accepts pipeline result dict or document score dict.
    Returns:
      report_text : the formatted report string
      report_path : path where report was written (if output_dir provided)
      format      : markdown | slack | html
    """
    fmt = input_dict.get("format", "markdown").lower()
    output_dir = input_dict.get("output_dir", "/tmp/haios_reports")

    # Determine report type
    if "pipeline_name" in input_dict or "stage_results" in input_dict:
        report_type = "PIPELINE"
    elif "repo_url" in input_dict or "signals" in input_dict:
        report_type = "REPO"
    else:
        report_type = "DOCUMENT"

    if fmt == "slack":
        report_text = build_slack_report(input_dict)
    elif fmt == "html":
        # HTML wraps markdown for now — full HTML renderer is Phase E
        md = build_markdown_report(input_dict, report_type)
        report_text = _md_to_html(md, input_dict.get("session_id", ""))
    else:
        report_text = build_markdown_report(input_dict, report_type)

    # Write to file
    report_path = None
    try:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        session_id = input_dict.get("session_id", "UNKNOWN")
        filename = f"report_{session_id}_{ts_slug}.{fmt if fmt != 'markdown' else 'md'}"
        report_path = str(out_dir / filename)
        Path(report_path).write_text(report_text, encoding="utf-8")
    except Exception as exc:
        return {
            "report_text": report_text,
            "report_path": None,
            "format": fmt,
            "warnings": [f"Failed to write report file: {exc}"],
        }

    return {
        "report_text": report_text,
        "report_path": report_path,
        "format": fmt,
    }


def _md_to_html(md: str, session_id: str) -> str:
    """Minimal markdown-to-HTML conversion for inline reports."""
    lines = md.splitlines()
    html_lines = [
        "<!DOCTYPE html><html><head>",
        "<meta charset='UTF-8'>",
        f"<title>HAIOS Report · {session_id}</title>",
        "<style>body{font-family:monospace;max-width:800px;margin:2rem auto;"
        "background:#0d1117;color:#c9d1d9;}h1,h2,h3{color:#58a6ff;}"
        "code{background:#161b22;padding:2px 4px;border-radius:3px;}"
        "hr{border-color:#30363d;}</style>",
        "</head><body>",
    ]
    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("---"):
            html_lines.append("<hr>")
        elif line.startswith("- ") or line.startswith("• "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")
    html_lines.append("</body></html>")
    return "\n".join(html_lines)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    print(f"[SMOKE] {TOOL_NAME} v{TOOL_VERSION}")

    # Positive: pipeline result dict produces markdown report
    sample = {
        "pipeline_name": "SESSION_CLOSE",
        "session_id": "S-TEST-01",
        "timestamp": "2026-05-21T14:00:00Z",
        "overall_status": "WARN",
        "z2_required": False,
        "stage_results": [
            {"stage_index": 0, "tool_name": "acat_protocol_auditor_v1_1",
             "description": "Protocol audit", "status": "PASS",
             "output": {"overall_verdict": "OVERALL_PASS",
                        "resonance_score": 88, "hard_failures": [],
                        "soft_failures": ["divider_format missing"]},
             "error": None, "duration_ms": 142},
        ],
        "accumulated_outputs": {
            "truth": 83, "humility": 79, "handoff": 84,
        },
        "error_log": [],
    }

    result = run(sample)
    assert "report_text" in result
    assert "HAIOS Report" in result["report_text"]
    assert "SESSION_CLOSE" in result["report_text"]
    assert result["format"] == "markdown"
    print("[SMOKE] Markdown report generated.")

    # Positive: Slack format
    result_slack = run({**sample, "format": "slack"})
    assert "━" in result_slack["report_text"]
    assert "Wado" in result_slack["report_text"]
    print("[SMOKE] Slack report generated.")

    # Positive: Z2 alert surfaces in report
    z2_sample = {**sample, "z2_required": True,
                 "z2_reason": "Hard failure at stage 0 (Test stage)."}
    result_z2 = run(z2_sample)
    assert "ZONE 2 REVIEW REQUIRED" in result_z2["report_text"]
    print("[SMOKE] Z2 alert surfaced in report.")

    # Negative: empty input produces report without crash
    result_empty = run({})
    assert "report_text" in result_empty
    print("[SMOKE] Empty input handled.")

    print("[SMOKE] All assertions passed.")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"HAIOS Report Writer {TOOL_VERSION}"
    )
    parser.add_argument("--input", "-i",
                        help="JSON file path or JSON string to render")
    parser.add_argument("--pipeline-result", "-p",
                        help="JSON string of pipeline result")
    parser.add_argument("--format", "-f",
                        choices=["markdown", "slack", "html"],
                        default="markdown")
    parser.add_argument("--output-dir", "-o", default="/tmp/haios_reports")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    data: Dict[str, Any] = {}
    if args.input:
        src = args.input
        p = Path(src)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = json.loads(src)
    elif args.pipeline_result:
        data = json.loads(args.pipeline_result)

    data["format"] = args.format
    data["output_dir"] = args.output_dir

    result = run(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
