#!/usr/bin/env python3
"""Temporal Dissolution Gate — reject unauthorized internal calendar controls.

Builder v1.7 compliant · validation_tool
HumanAIOS · Q-TEMPORAL-DISSOLUTION-01

Reject newly introduced internal calendar/deadline controls in active HumanAIOS
control surfaces. The gate scans added lines in a PR diff so legacy/historical
material can be remediated separately without making the first gate impossible
to land.

Permitted temporal classifications:
- OBSERVATIONAL
- TECHNICAL_SAFETY
- REGULATORY_EXTERNAL (requires complete regulatory contract)
- HISTORICAL_RECORD

Everything else that matches a scheduling/deadline control is rejected.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Iterable


TOOL_NAME = "temporal_dissolution_gate"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "Q-TEMPORAL-DISSOLUTION-01"
TOOL_ZONE = 1

ALLOWED_CLASSES = {
    "OBSERVATIONAL",
    "TECHNICAL_SAFETY",
    "REGULATORY_EXTERNAL",
    "HISTORICAL_RECORD",
}

EXEMPT_PATHS = {
    "TEMPORAL_DISSOLUTION_POLICY.md",
    "tools/temporal_dissolution_gate.py",
    "tests/test_temporal_dissolution_gate.py",
    "schemas/external_constraint.schema.json",
    "schemas/resource_request.schema.json",
    "schemas/resource_state.schema.json",
}

CONTROL_EXACT = {
    "CLAUDE.md",
    "GOVERNANCE.md",
    "PRIORITY_QUEUE.md",
    "ZONE_REGISTRY.md",
    "BOOT_PROCESS_MAP.md",
    "REGISTERED.md",
}

CONTROL_PREFIXES = (
    ".github/",
    "schemas/",
    "src/",
    "tools/",
    "ui/",
)

RISK_PATTERNS = (
    re.compile(r"\b(deadline|due_at|window_end|respond_within|complete_within|start_after)\s*[:=]", re.I),
    re.compile(r"\b(due|deadline)\s+(by|on)\b", re.I),
    re.compile(r"\boverdue\b", re.I),
    re.compile(
        r"\b(must|shall|required\s+to|respond|complete|finish|deliver)\b.{0,60}"
        r"\bwithin\s+\d+\s*(seconds?|minutes?|hours?|days?|weeks?|s|m|h|d|w)\b",
        re.I,
    ),
    re.compile(r"^\s*(schedule|cron)\s*:", re.I),
)

CLASS_PATTERNS = (
    re.compile(r"temporal[-_ ]class\s*[:=]\s*[\"']?([A-Z_]+)", re.I),
    re.compile(r"temporal-class\s*:\s*([A-Z_]+)", re.I),
)

REGULATORY_REQUIRED_MARKERS = (
    "REGULATORY_DEADLINE",
    "authority",
    "citation",
    "due_at",
    "evidence_ref",
    "impact_if_missed",
    "z2_ratified",
    "ratification_ref",
)


@dataclass(frozen=True)
class AddedLine:
    path: str
    line_no: int
    text: str


@dataclass(frozen=True)
class Violation:
    path: str
    line_no: int
    text: str
    reason: str


def is_control_surface(path: str) -> bool:
    if path in EXEMPT_PATHS:
        return False
    if path in CONTROL_EXACT:
        return True
    if path.startswith(CONTROL_PREFIXES):
        return True
    suffix = PurePosixPath(path).suffix.lower()
    return suffix in {".json", ".yaml", ".yml"} and "/" not in path


def is_risky(text: str) -> bool:
    return any(pattern.search(text) for pattern in RISK_PATTERNS)


def parse_added_lines(diff_text: str) -> list[AddedLine]:
    results: list[AddedLine] = []
    path: str | None = None
    new_line_no: int | None = None

    for raw in diff_text.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            new_line_no = int(match.group(1)) if match else None
            continue
        if path is None or new_line_no is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            results.append(AddedLine(path, new_line_no, raw[1:]))
            new_line_no += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_line_no += 1
    return results


def detect_classification(lines: list[str], line_no: int, radius: int = 12) -> str | None:
    start = max(0, line_no - 1 - radius)
    end = min(len(lines), line_no + radius)
    context = "\n".join(lines[start:end])

    if "REGULATORY_DEADLINE" in context:
        return "REGULATORY_EXTERNAL"

    for pattern in CLASS_PATTERNS:
        match = pattern.search(context)
        if match:
            value = match.group(1).upper()
            if value in ALLOWED_CLASSES:
                return value
    return None


def regulatory_contract_complete(file_text: str) -> bool:
    lower = file_text.lower()
    if not all(marker.lower() in lower for marker in REGULATORY_REQUIRED_MARKERS):
        return False
    return bool(re.search(r"z2_ratified\s*[:=]\s*(true|yes)", file_text, re.I))


def evaluate_added_lines(
    added: Iterable[AddedLine], file_loader: Callable[[str], str]
) -> list[Violation]:
    violations: list[Violation] = []
    cache: dict[str, tuple[list[str], str]] = {}

    for item in added:
        if not is_control_surface(item.path) or not is_risky(item.text):
            continue

        if item.path not in cache:
            text = file_loader(item.path)
            cache[item.path] = (text.splitlines(), text)
        lines, full_text = cache[item.path]
        temporal_class = detect_classification(lines, item.line_no)

        if temporal_class is None:
            violations.append(
                Violation(
                    item.path,
                    item.line_no,
                    item.text,
                    "unclassified internal temporal control",
                )
            )
            continue

        if temporal_class == "REGULATORY_EXTERNAL" and not regulatory_contract_complete(full_text):
            violations.append(
                Violation(
                    item.path,
                    item.line_no,
                    item.text,
                    "regulatory exception contract incomplete",
                )
            )

    return violations


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def changed_diff(base_ref: str) -> str:
    candidates = [f"origin/{base_ref}", base_ref]
    last_error: Exception | None = None
    for base in candidates:
        try:
            return git("diff", "--unified=0", f"{base}...HEAD", "--")
        except subprocess.CalledProcessError as exc:
            last_error = exc
    raise RuntimeError(f"unable to diff against base {base_ref}: {last_error}")


def load_head_file(path: str) -> str:
    try:
        return git("show", f"HEAD:{path}")
    except subprocess.CalledProcessError:
        return ""


def run_smoke_test() -> int:
    """Prove the core rejection and exception paths fire as designed."""

    def evaluate_text(path: str, text: str, line_no: int) -> list[Violation]:
        added = [AddedLine(path=path, line_no=line_no, text=text.splitlines()[line_no - 1])]
        return evaluate_added_lines(added, lambda _path: text)

    internal = "complete_within: 48h\n"
    violations = evaluate_text("GOVERNANCE.md", internal, 1)
    assert len(violations) == 1
    assert violations[0].reason == "unclassified internal temporal control"

    technical = (
        "temporal_class: TECHNICAL_SAFETY\n"
        "respond_within: 30 seconds\n"
        "purpose: dead-process detection only\n"
    )
    assert evaluate_text(".github/healthcheck.yml", technical, 2) == []

    regulatory = """external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  authority: Example Agency
  citation: Rule 42
  due_at: 2026-10-01T23:59:59Z
  evidence_ref: sha256:abc
  impact_if_missed: filing rejected
  z2_ratified: true
  ratification_ref: issue-comment:123
"""
    assert evaluate_text("schemas/work.yaml", regulatory, 6) == []

    incomplete = """external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  due_at: 2026-10-01T23:59:59Z
  z2_ratified: true
"""
    violations = evaluate_text("schemas/work.yaml", incomplete, 4)
    assert len(violations) == 1
    assert violations[0].reason == "regulatory exception contract incomplete"

    print("smoke-test OK — internal deadlines reject; technical/regulatory exceptions classify.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate changed surfaces against temporal dissolution policy")
    parser.add_argument("--base-ref", default=os.getenv("GITHUB_BASE_REF", "main"))
    parser.add_argument("--diff-file", help="optional pre-generated unified diff for local testing")
    parser.add_argument("--smoke-test", action="store_true", help="run self-test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as handle:
            diff_text = handle.read()
    else:
        diff_text = changed_diff(args.base_ref)

    added = parse_added_lines(diff_text)
    violations = evaluate_added_lines(added, load_head_file)

    if not violations:
        print("TEMPORAL_DISSOLUTION_GATE: PASS")
        return 0

    print("TEMPORAL_DISSOLUTION_GATE: FAIL")
    print("Internal time-based scheduling controls require removal or an allowed classification.")
    for violation in violations:
        print(
            f"- {violation.path}:{violation.line_no}: {violation.reason}: "
            f"{violation.text.strip()}"
        )
    print("See TEMPORAL_DISSOLUTION_POLICY.md and issue #378.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
