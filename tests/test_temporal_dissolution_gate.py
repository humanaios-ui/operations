"""Tests and PR-diff enforcement for Q-TEMPORAL-DISSOLUTION-01.

This is deliberately a test module, not an operational tool. It validates the
policy at merge time and is therefore outside the executable tool registry.
"""

from __future__ import annotations

import os
import re
import subprocess
import unittest
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable


ALLOWED_CLASSES = {
    "OBSERVATIONAL",
    "TECHNICAL_SAFETY",
    "REGULATORY_EXTERNAL",
    "HISTORICAL_RECORD",
}

EXEMPT_PATHS = {
    "TEMPORAL_DISSOLUTION_POLICY.md",
    "TEMPORAL_CONTROL_AUDIT.md",
    "tests/test_temporal_dissolution_gate.py",
    "schemas/external_constraint.schema.json",
    # Q-INTENT-GRAPH-01. Its `conflicts_with` rows exist to quote the defect they
    # report — the same reason the policy and the audit are exempt. Exempting it
    # here does not leave it unpoliced: `tools/intent_graph_v1_0.py` rule E10
    # applies the same patterns to node text, where a real control could hide,
    # while letting a conflict row name what it is reporting. A line scanner
    # cannot tell those two apart; a structure-aware validator can.
    "INTENT_GRAPH.yaml",
    # Same reason this file itself is exempt: a module that detects a pattern has
    # to contain the pattern, in its fixtures if nowhere else. The exemption is
    # safe because the tool reads no clock at all — it imports no time, datetime
    # or calendar module, which its own smoke test asserts, so there is no
    # temporal control for a scan to find.
    "tools/intent_graph_v1_0.py",
}

CONTROL_EXACT = {
    "CLAUDE.md",
    "GOVERNANCE.md",
    "CANDIDATE_BLOCK_TEMPLATE.md",
    "PRIORITY_QUEUE.md",
    "ZONE_REGISTRY.md",
    "BOOT_PROCESS_MAP.md",
    "REGISTERED.md",
    # Q-MOLT-TEMPORAL-PURITY-01. MOLT_STATE.md decides whether a ratified
    # constant change is kept or reverted; its absence here is how window_end
    # semantics survived the first audit pass. Root .md files are not picked up
    # by the suffix rule below, so control surfaces of this shape must be named.
    "MOLT_STATE.md",
    "RESOURCE_UNITS.yaml",
    "constants.json",
}

CONTROL_PREFIXES = (
    ".github/",
    "schemas/",
    "src/",
    "tools/",
    "ui/",
)

RISK_PATTERNS = (
    # Q-MOLT-TEMPORAL-PURITY-01 added the *_days forms. Without them the gate
    # refused a reintroduced `window_end:` but accepted `window_days: 7` and
    # `measurement_window_days: 28` — the same control expressed as a duration
    # instead of an instant, which is how the molt cycle carried it all along.
    re.compile(
        r"\b(deadline|due_at|window_end|respond_within|complete_within|start_after"
        r"|window_days|measurement_window_days|review_cadence_days|half_life_days"
        r"|review_interval_days)\s*[:=]",
        re.I,
    ),
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


class TemporalDissolutionGateTests(unittest.TestCase):
    def evaluate(self, path: str, text: str, line_no: int = 1) -> list[Violation]:
        added = [AddedLine(path=path, line_no=line_no, text=text.splitlines()[line_no - 1])]
        return evaluate_added_lines(added, lambda _path: text)

    def test_internal_deadline_rejected(self):
        violations = self.evaluate("GOVERNANCE.md", "complete_within: 48h\n")
        self.assertEqual(len(violations), 1)
        self.assertIn("unclassified", violations[0].reason)

    def test_technical_safety_timer_allowed_when_classified(self):
        text = (
            "temporal_class: TECHNICAL_SAFETY\n"
            "respond_within: 30 seconds\n"
            "purpose: network dead-process detection only\n"
        )
        self.assertEqual(self.evaluate(".github/healthcheck.yml", text, line_no=2), [])

    def test_observational_timestamp_policy_allowed(self):
        text = (
            "temporal_class: OBSERVATIONAL\n"
            "due_at: 2026-09-17T18:00:00Z\n"
            "note: telemetry only; no scheduling authority\n"
        )
        self.assertEqual(self.evaluate("schemas/example.yaml", text, line_no=2), [])

    def test_regulatory_contract_allowed_when_complete(self):
        text = """external_constraint:
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
        self.assertEqual(self.evaluate("schemas/work.yaml", text, line_no=6), [])

    def test_incomplete_regulatory_contract_rejected(self):
        text = """external_constraint:
  type: REGULATORY_DEADLINE
  temporal_class: REGULATORY_EXTERNAL
  due_at: 2026-10-01T23:59:59Z
  z2_ratified: true
"""
        violations = self.evaluate("schemas/work.yaml", text, line_no=4)
        self.assertEqual(len(violations), 1)
        self.assertIn("contract incomplete", violations[0].reason)

    def test_historical_record_allowed(self):
        text = (
            "temporal_class: HISTORICAL_RECORD\n"
            "deadline: 2026-07-31\n"
            "note: archival evidence only\n"
        )
        self.assertEqual(self.evaluate("REGISTERED.md", text, line_no=2), [])

    def test_pr_diff_has_no_unclassified_temporal_controls(self):
        if os.getenv("TEMPORAL_SCAN_ENFORCE") != "1":
            self.skipTest("PR diff enforcement runs only in temporal-dissolution CI")

        base_ref = os.getenv("GITHUB_BASE_REF", "main")
        added = parse_added_lines(changed_diff(base_ref))
        violations = evaluate_added_lines(added, load_head_file)
        detail = "\n".join(
            f"{v.path}:{v.line_no}: {v.reason}: {v.text.strip()}" for v in violations
        )
        self.assertEqual(violations, [], f"Unauthorized temporal controls:\n{detail}")

    def test_resource_request_schema_uses_cost_vector(self):
        schema = Path("schemas/resource_request.schema.json").read_text(encoding="utf-8")
        self.assertIn('"resource_units_ref"', schema)
        self.assertIn('"cost"', schema)
        self.assertNotIn("estimated_effort_units", schema)

    def test_candidate_template_uses_external_constraint_contract(self):
        template = Path("CANDIDATE_BLOCK_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("external_constraint:", template)
        self.assertNotIn("regulatory_deadline:", template)
        self.assertNotIn("estimated_effort_units", template)

    def test_intent_os_ui_uses_external_constraint_framing(self):
        pages = (
            "ui/intent-os-humanaios-v3_3.html",
            "ui/intent-os-decisions.html",
            "ui/intent-os-commitments.html",
            "ui/intent-os-records.html",
            "ui/intent-os-arena.html",
        )
        for page in pages:
            text = Path(page).read_text(encoding="utf-8")
            self.assertIn("External constraints — validated time gates only", text)
            self.assertNotIn("Deadlines — moves that die on a date", text)


if __name__ == "__main__":
    unittest.main()
