#!/usr/bin/env python3
“””
Registry Issue Compiler — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · S-071026-01

Automates the manual step demonstrated this session: turning a set of
Zone-2-ratified candidates into a GitHub-issue-ready markdown body,
grouped by class, with numbering left to whoever executes (Copilot),
per standing discipline that Claude never self-assigns registry IDs.

STRUCTURAL ENFORCEMENT, not just documentation (lesson from
IC-CAND-BLOCKER-GATE-NOT-ENFORCED, found this session: a check that
only prints a warning and proceeds anyway is not a check): any
candidate missing a `zone2_ratification` field is HARD EXCLUDED from
the compiled issue and reported separately, never silently dropped.
This tool cannot be used to sneak an unratified item into a submission
– the gate is in the code path, not a comment above it.

Usage:
python registry_issue_compiler_v1_0.py –input candidates.json
python registry_issue_compiler_v1_0.py –input candidates.json –output-dir outputs/
python registry_issue_compiler_v1_0.py –smoke-test
“””
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = “registry_issue_compiler”
TOOL_VERSION = “1.0.0”
TOOL_CATEGORY = “pipeline_tool”
TOOL_ZONE = 1  # drafts only – never submits, never self-numbers

REQUIRED_FIELDS = [“id_slug”, “class”, “status”, “synopsis”, “zone2_ratification”]
VALID_CLASSES = {“F”, “IC”, “H”, “IC-correction”}

class SpecLoadFailed(Exception):
pass

def load_input(source: str) -> dict:
p = Path(source)
if p.exists():
try:
return json.loads(p.read_text(encoding=“utf-8”))
except json.JSONDecodeError as e:
raise SpecLoadFailed(f”Cannot parse {p}: {e}”)
try:
return json.loads(source)
except json.JSONDecodeError as e:
raise SpecLoadFailed(f”Input is neither a valid path nor valid JSON: {e}”)

def validate_and_split(candidates: list) -> tuple:
“””
HARD GATE: separates ratified-and-includable from excluded.
Nothing missing zone2_ratification (or with it explicitly null/empty)
reaches the includable list, regardless of any other field’s content.
This is the enforcement IC-CAND-BLOCKER-GATE-NOT-ENFORCED found
missing elsewhere – applied here from the start, not bolted on.
“””
includable, excluded = [], []
for c in candidates:
missing = [f for f in REQUIRED_FIELDS if not c.get(f)]
if c.get(“class”) not in VALID_CLASSES:
missing.append(“class (invalid value)”)
if missing:
excluded.append({“candidate”: c.get(“id_slug”, “UNKNOWN”), “missing”: missing})
continue
includable.append(c)
return includable, excluded

def compile_issue_body(candidates: list, session_id: str, ratified_by: str, ratified_date: str) -> str:
grouped = {“F”: [], “IC”: [], “H”: [], “IC-correction”: []}
for c in candidates:
grouped[c[“class”]].append(c)

```
lines = [
    f"# Session {session_id} — Ratified Registry Updates (Zone 2 complete, Zone 3 pending)",
    "",
    f"**Ratified by:** {ratified_by}, {ratified_date}, session {session_id}",
    "**Prepared by:** Claude (Zone 1 — proposing only, no self-numbering per G-4/IC-030)",
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
    "F": "## Section A — F-candidates to register",
    "IC": "## Section B — IC-candidates to register",
    "H": "## Section C — H-candidates to register (slug-named)",
    "IC-correction": "## Section D — Append-only corrections to existing entries",
}

for cls in ["F", "IC", "H", "IC-correction"]:
    if not grouped[cls]:
        continue
    lines.append(section_titles[cls])
    lines.append("")
    for c in grouped[cls]:
        lines.append(f"### {c['id_slug']}")
        lines.append("")
        lines.append("```")
        lines.append(f"id: \"{c['class']}-[ASSIGN NEXT]\"" if cls != "H" else f"id: \"{c['id_slug']}\"")
        lines.append(f"status: {c['status']}")
        lines.append(f"class: {c['class']}")
        lines.append(f"zone2_ratification: \"{c['zone2_ratification']}\"")
        if c.get("related_finding"):
            lines.append(f"related_finding: {json.dumps(c['related_finding'])}")
        if c.get("principles_triggered"):
            lines.append(f"principles_triggered: {json.dumps(c['principles_triggered'])}")
        lines.append("```")
        lines.append(f"- **Synopsis:** {c['synopsis']}")
        if c.get("evidence"):
            lines.append(f"- **Evidence:** {c['evidence']}")
        if c.get("fix_principle"):
            lines.append(f"- **Fix → Principle {c['fix_principle']}**")
        lines.append("")
    lines.append("---")
    lines.append("")

return "\n".join(lines)
```

def aggregate(candidates: list, session_id: str, ratified_by: str, ratified_date: str) -> dict:
includable, excluded = validate_and_split(candidates)
body = compile_issue_body(includable, session_id, ratified_by, ratified_date) if includable else None
return {
“tool”: TOOL_NAME,
“version”: TOOL_VERSION,
“timestamp”: datetime.now(timezone.utc).isoformat(),
“session_id”: session_id,
“included_count”: len(includable),
“excluded_count”: len(excluded),
“excluded”: excluded,
“issue_body_markdown”: body,
}

def write_report(output: dict, output_dir: str) -> str:
p = Path(output_dir)
p.mkdir(parents=True, exist_ok=True)
ts = datetime.now(timezone.utc).strftime(”%Y%m%dT%H%M%SZ”)
if output[“issue_body_markdown”]:
md_path = p / f”github_issue_{output[‘session_id’]}*{ts}.md”
md_path.write_text(output[“issue_body_markdown”], encoding=“utf-8”)
json_path = p / f”compiler_report*{output[‘session_id’]}_{ts}.json”
report_copy = {k: v for k, v in output.items() if k != “issue_body_markdown”}
json_path.write_text(json.dumps(report_copy, indent=2), encoding=“utf-8”)
return str(md_path) if output[“issue_body_markdown”] else str(json_path)

def run_smoke_test() -> bool:
try:
# Positive: a fully-ratified candidate is included
good = {
“id_slug”: “IC-CAND-TEST-GOOD”, “class”: “IC”, “status”: “REGISTERED”,
“synopsis”: “test synopsis”, “zone2_ratification”: “Night · 2026-07-10 · S-TEST”,
“fix_principle”: “P3”,
}
# Negative: missing zone2_ratification must be excluded, not included
bad = {
“id_slug”: “IC-CAND-TEST-BAD”, “class”: “IC”, “status”: “CANDIDATE”,
“synopsis”: “unratified”, “zone2_ratification”: “”,
}
includable, excluded = validate_and_split([good, bad])
assert len(includable) == 1, “exactly one candidate should pass the gate”
assert includable[0][“id_slug”] == “IC-CAND-TEST-GOOD”
assert len(excluded) == 1, “exactly one candidate should be excluded”
assert excluded[0][“candidate”] == “IC-CAND-TEST-BAD”
assert “zone2_ratification” in excluded[0][“missing”]

```
    body = compile_issue_body(includable, "S-TEST", "Night", "2026-07-10")
    assert "IC-CAND-TEST-GOOD" in body
    assert "IC-CAND-TEST-BAD" not in body, "unratified item must never reach the output body"

    print("✓ Smoke test PASSED")
    return True
except Exception as e:
    print(f"✗ Smoke test FAILED: {e}")
    return False
```

def main():
parser = argparse.ArgumentParser(description=“Registry Issue Compiler v1.0”)
parser.add_argument(”–input”, “-i”)
parser.add_argument(”–output-dir”, “-o”, default=“outputs/”)
parser.add_argument(”–session-id”, default=“S-UNKNOWN”)
parser.add_argument(”–ratified-by”, default=“Night”)
parser.add_argument(”–ratified-date”, default=datetime.now(timezone.utc).strftime(”%Y-%m-%d”))
parser.add_argument(”–smoke-test”, action=“store_true”)
args = parser.parse_args()

```
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

candidates = data if isinstance(data, list) else data.get("candidates", [])
output = aggregate(candidates, args.session_id, args.ratified_by, args.ratified_date)
report_path = write_report(output, args.output_dir)
print(f"Included: {output['included_count']}  Excluded: {output['excluded_count']}")
if output["excluded"]:
    print("EXCLUDED (missing required fields, never silently dropped):")
    for e in output["excluded"]:
        print(f"  {e['candidate']}: missing {e['missing']}")
print(f"Report: {report_path}")
```

if **name** == “**main**”:
main()