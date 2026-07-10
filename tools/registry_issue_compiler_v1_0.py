#!/usr/bin/env python3
"""
Builder v1.7 compliant
Registry Issue Compiler v1.0.
HumanAIOS pipeline tool for compiling ratified candidates into issue-ready markdown.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_NAME = "registry_issue_compiler"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1

REQUIRED_FIELDS = ["id_slug", "class", "status", "synopsis", "zone2_ratification"]
VALID_CLASSES = {"F", "IC", "H", "IC-correction"}


class SpecLoadFailed(Exception):
    """Raised when input cannot be loaded as JSON."""


def load_input(source: str) -> Any:
    p = Path(source)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SpecLoadFailed(f"Cannot parse {p}: {exc}") from exc
    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Input is neither a valid path nor valid JSON: {exc}") from exc


def validate_and_split(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    includable: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for candidate in candidates:
        missing = [field for field in REQUIRED_FIELDS if not candidate.get(field)]
        if candidate.get("class") not in VALID_CLASSES:
            missing.append("class (invalid value)")
        if missing:
            excluded.append({"candidate": candidate.get("id_slug", "UNKNOWN"), "missing": missing})
            continue
        includable.append(candidate)
    return includable, excluded


def compile_issue_body(
    candidates: list[dict[str, Any]], session_id: str, ratified_by: str, ratified_date: str
) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {"F": [], "IC": [], "H": [], "IC-correction": []}
    for candidate in candidates:
        grouped[candidate["class"]].append(candidate)

    lines = [
        f"# Session {session_id} - Ratified Registry Updates (Zone 2 complete, Zone 3 pending)",
        "",
        f"**Ratified by:** {ratified_by}, {ratified_date}, session {session_id}",
        "**Prepared by:** Claude (Zone 1 - proposing only, no self-numbering per G-4/IC-030)",
        "**Requested action:** Assign correct sequential numbers per series, append per P2 append-only discipline.",
        "",
        "---",
        "",
        "## Numbering instructions",
        "",
        "- Verify current max F-/IC- number live before assigning -- do not trust any number pre-filled here.",
        "- H-series is slug-named, not sequential -- append using the slug given, do not invent a number.",
        "- All entries are append-only. IC-correction entries reference an existing ID, they do not edit it.",
        "",
        "---",
        "",
    ]

    section_titles = {
        "F": "## Section A - F-candidates to register",
        "IC": "## Section B - IC-candidates to register",
        "H": "## Section C - H-candidates to register (slug-named)",
        "IC-correction": "## Section D - Append-only corrections to existing entries",
    }

    for cls in ["F", "IC", "H", "IC-correction"]:
        if not grouped[cls]:
            continue
        lines.append(section_titles[cls])
        lines.append("")
        for candidate in grouped[cls]:
            lines.append(f"### {candidate['id_slug']}")
            lines.append("")
            lines.append("```yaml")
            if cls != "H":
                lines.append(f'id: "{candidate["class"]}-[ASSIGN NEXT]"')
            else:
                lines.append(f'id: "{candidate["id_slug"]}"')
            lines.append(f"status: {candidate['status']}")
            lines.append(f"class: {candidate['class']}")
            lines.append(f'zone2_ratification: "{candidate["zone2_ratification"]}"')
            if candidate.get("related_finding"):
                lines.append(f"related_finding: {json.dumps(candidate['related_finding'])}")
            if candidate.get("principles_triggered"):
                lines.append(f"principles_triggered: {json.dumps(candidate['principles_triggered'])}")
            lines.append("```")
            lines.append(f"- **Synopsis:** {candidate['synopsis']}")
            if candidate.get("evidence"):
                lines.append(f"- **Evidence:** {candidate['evidence']}")
            if candidate.get("fix_principle"):
                lines.append(f"- **Fix -> Principle {candidate['fix_principle']}**")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def aggregate(candidates: list[dict[str, Any]], session_id: str, ratified_by: str, ratified_date: str) -> dict[str, Any]:
    includable, excluded = validate_and_split(candidates)
    body = compile_issue_body(includable, session_id, ratified_by, ratified_date) if includable else None
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "included_count": len(includable),
        "excluded_count": len(excluded),
        "excluded": excluded,
        "issue_body_markdown": body,
    }


def write_report(output: dict[str, Any], output_dir: str) -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_copy = {k: v for k, v in output.items() if k != "issue_body_markdown"}
    json_path = out_dir / f"compiler_report_{output['session_id']}_{ts}.json"
    json_path.write_text(json.dumps(report_copy, indent=2), encoding="utf-8")
    if output["issue_body_markdown"]:
        md_path = out_dir / f"github_issue_{output['session_id']}_{ts}.md"
        md_path.write_text(output["issue_body_markdown"], encoding="utf-8")
        return str(md_path)
    return str(json_path)


def run_smoke_test() -> bool:
    good = {
        "id_slug": "IC-CAND-TEST-GOOD",
        "class": "IC",
        "status": "REGISTERED",
        "synopsis": "test synopsis",
        "zone2_ratification": "Night · 2026-07-10 · S-TEST",
        "fix_principle": "P3",
    }
    bad = {
        "id_slug": "IC-CAND-TEST-BAD",
        "class": "IC",
        "status": "CANDIDATE",
        "synopsis": "unratified",
        "zone2_ratification": "",
    }
    try:
        includable, excluded = validate_and_split([good, bad])
        assert len(includable) == 1
        assert includable[0]["id_slug"] == "IC-CAND-TEST-GOOD"
        assert len(excluded) == 1
        assert excluded[0]["candidate"] == "IC-CAND-TEST-BAD"
        assert "zone2_ratification" in excluded[0]["missing"]

        body = compile_issue_body(includable, "S-TEST", "Night", "2026-07-10")
        assert "IC-CAND-TEST-GOOD" in body
        assert "IC-CAND-TEST-BAD" not in body
        print("Smoke test PASSED")
        return True
    except Exception as exc:  # pragma: no cover
        print(f"Smoke test FAILED: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Registry Issue Compiler v1.0")
    parser.add_argument("--input", "-i")
    parser.add_argument("--output-dir", "-o", default="outputs/")
    parser.add_argument("--session-id", default="S-UNKNOWN")
    parser.add_argument("--ratified-by", default="Night")
    parser.add_argument("--ratified-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        data = load_input(args.input)
    except SpecLoadFailed as exc:
        print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
        sys.exit(2)

    candidates = data if isinstance(data, list) else data.get("candidates", [])
    output = aggregate(candidates, args.session_id, args.ratified_by, args.ratified_date)
    report_path = write_report(output, args.output_dir)
    print(f"Included: {output['included_count']}  Excluded: {output['excluded_count']}")
    if output["excluded"]:
        print("EXCLUDED (missing required fields, never silently dropped):")
        for excluded in output["excluded"]:
            print(f"  {excluded['candidate']}: missing {excluded['missing']}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()