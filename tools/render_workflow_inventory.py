#!/usr/bin/env python3
"""Regenerate the workflow inventory inside .github/WORKFLOWS.md.

Builder v1.7 compliant
HumanAIOS — reporting tool, Zone 1. Reads files; writes only the marked
region of .github/WORKFLOWS.md, and only with --write.

Stdlib only. Scans .github/workflows for *.yml and *.yaml and records, per
file: the workflow name, trigger keys, cron lines, duplicate top-level keys
(GitHub rejects those and then reports a zero-job failure) and a status read
from the file itself (timer, events, manual only, or paused/retired/frozen by
a Q-AGENT-WORKFLOWS-01 marker comment).

    python3 tools/render_workflow_inventory.py            # print the table
    python3 tools/render_workflow_inventory.py --write    # replace the marked region
    python3 tools/render_workflow_inventory.py --check    # exit 1 if the region is stale
    python3 tools/render_workflow_inventory.py --runs 10  # live pass/fail of recent runs (needs gh; prints only)
    python3 tools/render_workflow_inventory.py --smoke-test

The marked region is everything between these HTML comments:

    <!-- workflow-inventory:start -->
    <!-- workflow-inventory:end -->

The committed table holds only what the files say, so --check stays stable.
Run results change by the hour, so --runs prints them and does not write them.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

TOOL_NAME = "render_workflow_inventory"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "reporting_tool"
TOOL_SESSION = "S-112826-01"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
DOC = ROOT / ".github" / "WORKFLOWS.md"
START = "<!-- workflow-inventory:start -->"
END = "<!-- workflow-inventory:end -->"
REPO = "humanaios-ui/operations"

TRIGGER_LINE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*(.*)$")
CRON_LINE = re.compile(r"""cron:\s*['"]([^'"]+)['"]""")
# `on:`, `"on":` and `'on':` at column 0, with an optional value after the colon.
ON_KEY = re.compile(r"""^(?:on|"on"|'on'):(.*)$""")
NAME_LINE = re.compile(r"^name:\s*(.+?)\s*$")
FILTER_KEYS = {"types", "branches", "branches-ignore", "paths", "paths-ignore", "tags", "tags-ignore"}

# Marker comments that Q-AGENT-WORKFLOWS-01 changes leave in a workflow file.
PAUSE_MARKERS = (
    ("Schedule paused by Q-AGENT-WORKFLOWS-01", "paused"),
    ("Retired from the schedule by Q-AGENT-WORKFLOWS-01", "retired"),
    ("Frozen by Q-AGENT-WORKFLOWS-01", "frozen"),
)


def top_level_keys(text: str) -> list[str]:
    keys = []
    for line in text.splitlines():
        if not line or line[0] in " \t#" or line.startswith("---"):
            continue
        if ":" not in line:
            continue
        keys.append(line.split(":", 1)[0].strip().strip("'\""))
    return keys


def _scalar_triggers(value: str) -> list[str]:
    """Triggers written on the `on:` line itself: `on: push` or `on: [push, pull_request]`."""
    value = value.split("#", 1)[0].strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [part.strip().strip("'\"") for part in value.split(",") if part.strip()]


def status_for(text: str, triggers: list[str], crons: list[str]) -> str:
    for marker, label in PAUSE_MARKERS:
        if marker in text:
            return label
    if crons:
        return "timer"
    events = [t for t in triggers if t != "workflow_dispatch"]
    if events:
        return "events"
    if triggers:
        return "manual only"
    return "no trigger"


def parse_text(text: str, filename: str) -> dict:
    keys = top_level_keys(text)
    name = ""
    triggers: list[str] = []
    crons: list[str] = []
    in_on = False
    has_on = False
    for line in text.splitlines():
        if name == "" and not line.startswith((" ", "\t", "#")):
            match = NAME_LINE.match(line)
            if match:
                name = match.group(1).strip().strip("'\"")
        on_match = ON_KEY.match(line)
        if on_match:
            has_on = True
            inline = _scalar_triggers(on_match.group(1))
            if inline:
                triggers.extend(inline)
                in_on = False
            else:
                in_on = True
            continue
        if in_on:
            if line and not line.startswith((" ", "\t", "#")):
                in_on = False
            else:
                trig = TRIGGER_LINE.match(line)
                if trig and trig.group(1) not in FILTER_KEYS:
                    triggers.append(trig.group(1))
                cron = CRON_LINE.search(line)
                if cron:
                    crons.append(cron.group(1))
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    return {
        "file": filename,
        "name": name or "(no name)",
        "triggers": triggers,
        "crons": crons,
        "duplicates": duplicates,
        "has_on": has_on,
        "status": status_for(text, triggers, crons),
    }


def parse_workflow(path: Path) -> dict:
    return parse_text(path.read_text(encoding="utf-8", errors="replace"), path.name)


def load(workflow_dir: Path = WORKFLOW_DIR) -> list[dict]:
    paths = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    return [parse_workflow(path) for path in paths]


def render(rows: list[dict]) -> str:
    defective = [row for row in rows if row["duplicates"] or not row["has_on"]]
    by_trigger: Counter = Counter()
    by_status: Counter = Counter()
    for row in rows:
        by_status[row["status"]] += 1
        for trigger in row["triggers"]:
            by_trigger[trigger] += 1
        if not row["triggers"] and row["has_on"]:
            by_trigger["(unparsed on:)"] += 1
    lines = [
        "Generated by `python3 tools/render_workflow_inventory.py --write`. The date is not embedded here, so `--check` stays green until a workflow file changes.",
        f"Workflow files: **{len(rows)}**. Files with a duplicate top-level key or no `on:` trigger: **{len(defective)}**.",
        "",
        "Status is read from each file: `timer` runs on a schedule, `events` runs on repository events, `manual only` runs only when started by hand, and `paused`, `retired` or `frozen` carry a Q-AGENT-WORKFLOWS-01 marker comment that says why and how to turn it back on.",
        "",
        "| Status | Files |",
        "| --- | ---: |",
    ]
    for status, count in sorted(by_status.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {status} | {count} |")
    lines += [
        "",
        "Trigger counts are file counts, not mutually exclusive.",
        "",
        "| Trigger | Files |",
        "| --- | ---: |",
    ]
    for trigger, count in sorted(by_trigger.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{trigger}` | {count} |")
    lines += [
        "",
        "| File | Name | Status | Triggers | Schedule |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        triggers = ", ".join(f"`{item}`" for item in row["triggers"]) or "—"
        schedule = "<br>".join(f"`{cron}`" for cron in row["crons"]) or "—"
        note = ""
        if row["duplicates"]:
            note = " **duplicate keys:** " + ", ".join(f"`{key}`" for key in row["duplicates"])
        if not row["has_on"]:
            note += " **no on:**"
        name = row["name"].replace("|", "\\|")
        lines.append(f"| `{row['file']}` | {name}{note} | {row['status']} | {triggers} | {schedule} |")
    lines.append("")
    return "\n".join(lines)


def replace_region(document: str, inventory: str) -> str:
    if START not in document or END not in document:
        raise SystemExit(f"{DOC.relative_to(ROOT)} is missing {START} / {END} markers")
    pre, rest = document.split(START, 1)
    _, post = rest.split(END, 1)
    return f"{pre}{START}\n{inventory}{END}{post}"


def fetch_runs(workflow_file: str, count: int) -> list[str]:
    """Conclusions of the last `count` completed runs, newest first. Needs an authenticated gh."""
    out = subprocess.run(
        ["gh", "api", f"repos/{REPO}/actions/workflows/{workflow_file}/runs?status=completed&per_page={count}"],
        capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        return ["(unreadable)"]
    runs = json.loads(out.stdout).get("workflow_runs", [])
    return [run.get("conclusion") or "none" for run in runs]


def render_runs(rows: list[dict], count: int, fetch=fetch_runs) -> str:
    lines = [
        f"Last {count} completed runs per workflow (live; not written to the doc).",
        "A green job can still check nothing; read its log before trusting it.",
        "",
        "| File | Status | Runs | Success | Failure | Other |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        conclusions = fetch(row["file"], count)
        tally = Counter(conclusions)
        other = len(conclusions) - tally["success"] - tally["failure"]
        lines.append(
            f"| `{row['file']}` | {row['status']} | {len(conclusions)} | {tally['success']} | {tally['failure']} | {other} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_smoke_test() -> int:
    """Parse sample workflows in a temp dir and round-trip a marked region. No network, no repo writes."""
    samples = {
        "block.yml": "name: block\non:\n  pull_request:\n    types: [opened]\n  schedule:\n    - cron: '0 1 * * *'\njobs: {}\n",
        "scalar.yml": "name: scalar\non: push\njobs: {}\n",
        "quoted.yml": 'name: quoted\n"on":\n  workflow_dispatch: {}\njobs: {}\n',
        "paused.yml": "name: paused\n# Schedule paused by Q-AGENT-WORKFLOWS-01 W2 (2026-11-26): test.\non:\n  workflow_dispatch: {}\njobs: {}\n",
    }
    expected = {
        "block.yml": (["pull_request", "schedule"], "timer"),
        "scalar.yml": (["push"], "events"),
        "quoted.yml": (["workflow_dispatch"], "manual only"),
        "paused.yml": (["workflow_dispatch"], "paused"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for filename, body in samples.items():
            (folder / filename).write_text(body, encoding="utf-8")
        rows = {row["file"]: row for row in load(folder)}
    for filename, (triggers, status) in expected.items():
        row = rows[filename]
        if row["triggers"] != triggers or row["status"] != status or not row["has_on"]:
            print(f"SMOKE FAIL {filename}: {row}", file=sys.stderr)
            return 1
    doc = f"head\n{START}\nold\n{END}\ntail\n"
    if "old" in replace_region(doc, render(list(rows.values()))):
        print("SMOKE FAIL: marked region not replaced", file=sys.stderr)
        return 1
    print(f"{TOOL_NAME} {TOOL_VERSION} smoke test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the workflow inventory inside .github/WORKFLOWS.md.")
    parser.add_argument("--input", type=Path, default=WORKFLOW_DIR, help="workflow directory to scan (default: .github/workflows)")
    parser.add_argument("--write", action="store_true", help="replace the marked region in .github/WORKFLOWS.md")
    parser.add_argument("--check", action="store_true", help="exit 1 when the marked region is stale")
    parser.add_argument("--runs", type=int, metavar="N", help="print live results of the last N runs per workflow (needs gh)")
    parser.add_argument("--smoke-test", action="store_true", help="run the built-in self-test and exit")
    args = parser.parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()
    rows = load(args.input)
    if args.runs:
        sys.stdout.write(render_runs(rows, args.runs))
        return 0
    inventory = render(rows)
    if args.write or args.check:
        current = DOC.read_text(encoding="utf-8")
        updated = replace_region(current, inventory)
        if args.check and updated != current:
            print("workflow inventory is stale; run python3 tools/render_workflow_inventory.py --write", file=sys.stderr)
            return 1
        if args.write and updated != current:
            DOC.write_text(updated, encoding="utf-8")
            print(f"updated {DOC.relative_to(ROOT)} ({len(rows)} workflows)")
        elif args.write:
            print(f"{DOC.relative_to(ROOT)} already current ({len(rows)} workflows)")
        else:
            print(f"inventory matches ({len(rows)} workflows)")
        return 0
    sys.stdout.write(inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
