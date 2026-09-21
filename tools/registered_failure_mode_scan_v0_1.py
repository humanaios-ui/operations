#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder v1.7 compliant
registered_failure_mode_scan_v0_1.py

HumanAIOS — REGISTERED.md failure-mode scanner.

Detects the machine-detectable subset of the registry failure-mode taxonomy
(RFM-NN) defined in REGISTERED_FAILURE_MODES.md, and reports an entry-level
first-pass yield / DPMO / sigma baseline using the same methodology as
audits/T1_DEFECT_BASELINE_S070726.md.

Eleven checks, mapped to the taxonomy:

  RFM-06  required_fields        entry missing a field the schema declares
  RFM-07  frontmatter_fence_form `id:` rendered as a markdown heading rather
                                  than sitting inside a `---` fence, making
                                  the entry invisible to fence-based parsers
  RFM-08  quote_hygiene          curly quotes in front-matter values, which
                                  break straight-quote string parsing
  RFM-09  ordering_conformance   entry outside the class block that
                                  REGISTRY_SPEC.md:114 declares for it
  RFM-10  post_terminal_append   entry appended after the `## Changelog`
                                  terminal section (shadow append zone)
  RFM-11  index_desync           body entry absent from the F quick index
  RFM-12  rollup_orphan          IC roll-up table cites an ID with no entry
  RFM-14  cross_artifact_ratification  an artifact's ratification state
                                  contradicts itself or the registry
  RFM-15  ratification_hash_form recorded ratification hash is a git commit
                                  SHA where a decision signature is specified
  RFM-16  class_starvation       a class REGISTRY_SPEC.md ratifies has zero
                                  entries -- a declared channel nothing has
                                  ever flowed through
  RFM-17  header_staleness       `Last updated` older than the newest entry

Entry discovery covers three forms, because an id-only scan silently drops the
malformed entries this tool exists to measure: fenced front matter keyed on
`id:`, correction entries keyed on `correction_to:` (`class: F-correction`),
and legacy `### <ID> — Title` headings carrying bold-prose fields or nothing
at all (REGISTERED.md:2302 H-ELICIT-01, and the H-1 / H-42 / H-LE-02 one-line
entries). Legacy entries count as front-matter loss under RFM-07 and enter the
population, so the denominator reflects the registry rather than the subset
that happens to be parseable.

Each check is split into a collect() step (real file I/O) and an evaluate()
step (a pure function over already-parsed data). That split is what makes
--smoke-test meaningful: the evaluators are exercised against synthetic
known-good and known-bad fixtures before the scanner is trusted against the
live registry.

This matters here more than usual. IC-037 (instrument-scorer-conflation) and
the audits/T2_ANALYZE_S070726.md root-cause analysis -- where a regex bug
(`\w` excluding `-`) manufactured five false ID-collision defects -- are both
measurement-system failures. This scanner is subject to exactly the failure
mode it measures. A checker that has never been run against a known defect is
as unverified as the self-report it replaces.

Known intentional states that are NOT defects (whitelisted, see WHITELIST):
  F-32, F-33  documented honest gaps: present in the quick index with no
              body entry, deliberately never backfilled. Flagging these
              would itself be an IC-037-genus false positive.

Usage:
    # scan the live registry, human-readable report
    python3 tools/registered_failure_mode_scan_v0_1.py scan

    # machine-readable, for a Z3 executor or a future CI gate
    python3 tools/registered_failure_mode_scan_v0_1.py scan --json --out report.json

    # exit non-zero when defects are present (opt-in; see note below)
    python3 tools/registered_failure_mode_scan_v0_1.py scan --enforce

    # validate the scanner against synthetic fixtures before trusting it
    python3 tools/registered_failure_mode_scan_v0_1.py self-test

Advisory by default. `--enforce` is opt-in because the registry carries 98
pre-existing entry-level defects at the time of writing; shipping this
blocking would fail CI on contact, which is how a gate gets disabled rather
than obeyed. That default is itself the IC-050 pattern (a gate that only
warns is a defeated gate) and is routed to Z2 as an explicit decision in
z1-inbox/2026-09-13/Q-RFM-01.md, not settled here.

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

TOOL_NAME = "registered_failure_mode_scan"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "S-091326-01"
TOOL_ZONE = 1


# Builder v1.7 compliant

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return run_self_test(verbose=False)


import argparse
import dataclasses
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from statistics import NormalDist
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_VERSION = "0.1"
SPEC_CITATION = "REGISTERED_FAILURE_MODES.md (RFM taxonomy); REGISTRY_SPEC.md:114 (ordering)"

PASS, FAIL, SKIP, ERROR = "PASS", "FAIL", "SKIP", "ERROR"

# Entries deliberately present in the index with no body. Documented honest
# gaps -- see REGISTERED.md quick index. Not defects.
WHITELIST_INDEX_ONLY = {"F-32", "F-33"}

# Every field the entry-header schema at REGISTERED.md:16-32 declares. The
# schema says entries "must open with" this block, so the whole list is the
# contract -- checking a convenient subset would let the measurement flatter
# the registry. CORE_FIELDS is reported alongside as the actionable subset,
# not as the standard.
REQUIRED_FIELDS = [
    "name", "status", "class", "date_registered", "date_origin",
    "session_registered", "principles_triggered", "substrate", "tags",
    "superseded_by",
]
# Note: REGISTRY_SPEC.md:55-72 also declares `evidence_trail` and `ratification_receipt`,
# but they are not present in the live REGISTERED.md. This scanner checks only the fields
# that are actually adopted in practice. The gap is documented as observable by Z2 as a
# schema-erosion issue (fields declared but not in use) — a measurement-system decision
# point, not a scanner deficiency. See RFM-06 note in REGISTERED_FAILURE_MODES.md.
CORE_FIELDS = ["name", "status", "class", "date_registered", "session_registered"]

# Classes REGISTRY_SPEC.md defines. D/R/GD are ratified but unpopulated.
SPEC_CLASSES = ["F", "IC", "H", "D", "R", "GD"]

# The four entry-level checks that form the FPY denominator. File-level
# checks (index desync, orphan rows, starvation, staleness, cross-artifact)
# are reported separately -- they have no per-entry opportunity count and
# folding them in would inflate the denominator dishonestly.
ENTRY_LEVEL_CHECKS = [
    "ordering_conformance",
    "required_fields",
    "frontmatter_fence_form",
    "quote_hygiene",
]

CURLY = "“”‘’"

_ID_RE = re.compile(
    r'^\s*(?:#+\s*)?id\s*:\s*["“”\']?([A-Za-z0-9\-\_]+)["“”\']?\s*$'
)
# Quote hygiene must cover every declared field, not a convenient four:
# a curly quote in `date_registered` breaks parsing exactly as one in `id` does.
_FM_FIELD_RE = re.compile(
    r'^\s*(?:#+\s*)?(id|' + "|".join(REQUIRED_FIELDS) + r')\s*:'
)
# Correction entries (`class: F-correction` / `IC-correction`) are properly
# fenced but key on `correction_to:` rather than `id:`. An alternate declared
# key is not a missing one, so they must not count as front-matter loss.
_CORRECTION_KEY_RE = re.compile(r'^\s*correction_to\s*:')

# A heading-style entry header, e.g. "### H-ELICIT-01 — Elicitation Surface...".
# The id must carry a hyphen so the F quick-index table header does not match.
_HEADING_ENTRY_RE = re.compile(
    r'^#{3}\s+((?:F|IC|H|NM|D|R|GD|Z2)-[A-Za-z0-9_\-]+)\s*[\u2014\u2013-]'
)
_SECTION_RE = re.compile(
    r'^#{2,3}\s.*(F-class|IC-class|H-class|NM-class|P-IMPROVE|Changelog|Governance Ratifications)'
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    check_id: str
    rfm: str
    title: str
    status: str
    severity: str  # "critical" | "warning" | "info"
    defects: int = 0
    opportunities: Optional[int] = None
    evidence: List[Any] = field(default_factory=list)
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Entry:
    entry_id: str
    line: int
    id_line_raw: str
    block: str
    section: str
    # True when the entry was found only by its `###` heading because it
    # carries no machine-readable front matter at all. Such an entry is
    # invisible to any fence-based parser -- including this one, until it
    # looked for them -- which is the same failure RFM-07 names. Counting it
    # in the population is the point: an instrument that silently drops the
    # malformed entries it exists to measure under-reports by construction.
    legacy: bool = False


# ---------------------------------------------------------------------------
# collect() -- real I/O
# ---------------------------------------------------------------------------

def collect_registry(path: Path) -> Dict[str, Any]:
    """Read REGISTERED.md and return the raw material every evaluator needs."""
    text = path.read_text(encoding="utf-8")
    return parse_registry(text)


def collect_priority_queue(path: Path) -> Optional[str]:
    """Return the file's text, or None when it is absent.

    None and "" must stay distinguishable: an absent input is an ERROR the
    gate has to fail on, not a check that quietly passes. Collapsing both to
    "" is how a gate reports success without having run -- the IC-041
    audit-false-pass genus this scanner exists to detect.
    """
    return path.read_text(encoding="utf-8") if path.exists() else None


def parse_registry(text: str) -> Dict[str, Any]:
    """Pure: turn registry text into entries, sections and table contents.

    Kept separate from collect_registry so fixtures can be parsed without
    touching the filesystem.
    """
    lines = text.split("\n")

    sections: List[Tuple[int, str]] = [
        (i, l.strip()) for i, l in enumerate(lines, 1) if _SECTION_RE.match(l)
    ]

    def section_of(ln: int) -> str:
        cur = "(front matter)"
        for i, label in sections:
            if i <= ln:
                cur = label
        return cur

    starts: List[Tuple[str, int]] = []
    for i, l in enumerate(lines, 1):
        m = _ID_RE.match(l)
        if m:
            starts.append((m.group(1), i))
        # Correction entries keyed on `correction_to:` not `id:`
        m = _CORRECTION_KEY_RE.match(l)
        if m:
            # Extract ID from the value: `correction_to: "F-31"`
            val_match = re.search(r'["""\']?([A-Za-z0-9\-\_]+)["""\']?', l)
            if val_match:
                starts.append((val_match.group(1), i))

    entries: List[Entry] = []
    for n, (eid, ln) in enumerate(starts):
        end = starts[n + 1][1] - 1 if n + 1 < len(starts) else len(lines)
        block = "\n".join(lines[ln - 1:min(ln + 25, end)])
        entries.append(Entry(eid, ln, lines[ln - 1], block, section_of(ln)))

    # Legacy entries: a `### <ID> — Title` heading with no `id:` line anywhere
    # before the next heading. These carry bold-prose fields (`**Class:** H`)
    # instead of front matter, so an id-based scan never sees them.
    id_line_nums = {ln for _, ln in starts}
    id_line_nums |= {i for i, l in enumerate(lines, 1)
                     if _CORRECTION_KEY_RE.match(l)}
    # A malformed `## id: "F-52"` line is itself a heading. Treating it as a
    # boundary would stop the lookahead before the id it contains and flag the
    # entry as legacy on top of the fence-form defect it already has -- double
    # counting the same defect. Exclude id-bearing headings from the boundary.
    heading_lines = [i for i, l in enumerate(lines, 1)
                     if re.match(r'^#{2,3}\s', l) and not _ID_RE.match(l)]
    for i, l in enumerate(lines, 1):
        m = _HEADING_ENTRY_RE.match(l)
        if not m:
            continue
        # Look ahead only as far as the next heading. A fixed line window would
        # see the *following* entry's `id:` and wrongly clear this one -- which
        # is how the first version of this check missed its own fixture.
        nxt = next((h for h in heading_lines if h > i), len(lines) + 1)
        if any(i < j <= nxt for j in id_line_nums):
            continue
        # The documented honest gaps are headings by design, with no entry
        # behind them deliberately. Counting them as malformed entries is the
        # IC-037-genus false positive this scanner is supposed to avoid.
        if m.group(1) in WHITELIST_INDEX_ONLY:
            continue
        end = min(nxt - 1, len(lines))
        entries.append(Entry(m.group(1), i, l, "\n".join(lines[i - 1:end]),
                             section_of(i), legacy=True))
    entries.sort(key=lambda e: e.line)

    # F quick index rows (the table above the first class section)
    # Handles variants like "F-24 / 24b / 24c / 24d" which appear in the same cell
    index_end = sections[0][0] if sections else len(lines)
    index_f = set()
    for l in lines[:index_end]:
        # Match table row: | ... F-ID ... | (may have variants after /)
        m = re.match(r'^\s*\|\s*\**(F-[0-9A-Za-z\-]+)(?:\s*[/|]|(?=\*?\s*\|))', l)
        if m:
            index_f.add(m.group(1))

    # IC roll-up table: IC ids cited between the index and the first class block
    rollup_ic = set()
    for l in lines[:index_end]:
        for m in re.finditer(r'(IC-\d{3})', l):
            rollup_ic.add(m.group(1))

    header = "\n".join(lines[:12])

    return {
        "lines": lines,
        "entries": entries,
        "sections": sections,
        "index_f": index_f,
        "rollup_ic": rollup_ic,
        "header": header,
        "text": text,
    }


# ---------------------------------------------------------------------------
# evaluate() -- pure functions over parsed data
# ---------------------------------------------------------------------------

def evaluate_frontmatter_fence_form(entries: List[Entry]) -> CheckResult:
    """RFM-07: `id:` rendered as a heading escapes fence-based parsers."""
    bad = [(e.entry_id, e.line) for e in entries
           if e.legacy or e.id_line_raw.lstrip().startswith("#")]
    return CheckResult(
        check_id="frontmatter_fence_form",
        rfm="RFM-07",
        title="Front-matter fence loss",
        status=FAIL if bad else PASS,
        severity="critical",
        defects=len(bad),
        opportunities=len(entries),
        evidence=[f"{eid} (L{ln})" for eid, ln in bad],
        reason="`id:` is a markdown heading, not a fenced front-matter field" if bad else None,
    )


def evaluate_quote_hygiene(entries: List[Entry]) -> CheckResult:
    """RFM-08: curly quotes in front-matter values break string parsing."""
    bad = []
    for e in entries:
        for line in e.block.split("\n"):
            if _FM_FIELD_RE.match(line) and any(c in line for c in CURLY):
                bad.append((e.entry_id, e.line))
                break
    return CheckResult(
        check_id="quote_hygiene",
        rfm="RFM-08",
        title="Quote contamination in front matter",
        status=FAIL if bad else PASS,
        severity="critical",
        defects=len(bad),
        opportunities=len(entries),
        evidence=[f"{eid} (L{ln})" for eid, ln in bad],
        reason="curly quotes where straight quotes are required" if bad else None,
    )


def evaluate_required_fields(entries: List[Entry]) -> CheckResult:
    """RFM-06: schema erosion -- a declared field is absent."""
    bad = []
    for e in entries:
        missing = [f for f in REQUIRED_FIELDS
                   if not re.search(rf'^\s*{f}\s*:', e.block, re.M)]
        if missing:
            bad.append((e.entry_id, e.line, missing))
    return CheckResult(
        check_id="required_fields",
        rfm="RFM-06",
        title="Schema erosion (missing required fields)",
        status=FAIL if bad else PASS,
        severity="warning",
        defects=len(bad),
        opportunities=len(entries),
        evidence=[f"{eid} (L{ln}): missing {m}" for eid, ln, m in bad],
        reason="fields declared at REGISTERED.md:16-32 absent from entry" if bad else None,
    )


def _expected_section(entry_id: str) -> Optional[str]:
    if entry_id.startswith("F-"):
        return "F-class"
    if entry_id.startswith("IC-"):
        return "IC-class"
    if entry_id.startswith("H-"):
        return "H-class"
    return None


CLASS_SECTIONS = ("F-class", "IC-class", "H-class")


def evaluate_ordering_conformance(
        entries: List[Entry],
        sections: Optional[List[Tuple[int, str]]] = None) -> CheckResult:
    """RFM-09: REGISTRY_SPEC.md:114 declares F -> IC -> H -> *then other classes*.

    Checks two aspects:
    1. Per-entry placement: F/IC/H entries must sit in their own class block.
       Other classes must sit *after* the three class blocks.
    2. Section-order: The F-class, IC-class, and H-class blocks must appear
       in F -> IC -> H order. Within-block ordering (F numbers strictly
       increasing, IC entries sequential) is out of scope.

    Note: REGISTRY_SPEC.md:36-40 specifies additional within-block ordering
    requirements not covered by this check.
    """
    bad = []
    for e in entries:
        exp = _expected_section(e.entry_id)
        if exp is None:
            # "other classes" belong after H-class, never inside a class block
            if any(c in e.section for c in CLASS_SECTIONS):
                bad.append((e.entry_id, e.line, e.section))
            continue
        if exp not in e.section:
            bad.append((e.entry_id, e.line, e.section))

    # Per-entry placement is only half the rule. The class blocks themselves
    # must appear in F -> IC -> H order; a registry whose H block preceded its
    # F block would put every entry "in its own section" and still violate
    # REGISTRY_SPEC.md:114.
    order_violation = None
    order_violation_defects = 0
    if sections:
        seen = [c for c in (next((c for c in CLASS_SECTIONS if c in label), None)
                            for _, label in sections) if c]
        first = []
        for c in seen:
            if c not in first:
                first.append(c)
        expected = [c for c in CLASS_SECTIONS if c in first]
        if first != expected:
            order_violation = f"class blocks appear as {first}, expected {expected}"
            order_violation_defects = 1  # Section-order violations count as 1 defect
    return CheckResult(
        check_id="ordering_conformance",
        rfm="RFM-09",
        title="Append-ordering decay",
        status=FAIL if (bad or order_violation) else PASS,
        severity="warning",
        defects=len(bad) + order_violation_defects,
        opportunities=len(entries),
        evidence=([f"{eid} (L{ln}) sits under {sec[:50]}" for eid, ln, sec in bad]
                  + ([order_violation] if order_violation else [])),
        reason=("entry/section outside the order REGISTRY_SPEC.md:114 declares"
                if (bad or order_violation) else None),
    )


def evaluate_post_terminal_append(
        entries: List[Entry],
        sections: Optional[List[Tuple[int, str]]] = None) -> CheckResult:
    """RFM-10: entries appended after the Changelog form a shadow zone.

    Compares line positions against the Changelog boundary rather than the
    current section label. Matching on the label alone would miss an entry
    appended under a *later* terminal section (REGISTERED.md ends with
    `## Governance Ratifications`), which is after the Changelog and so
    equally in the shadow zone.
    """
    changelog_line = None
    for ln, label in (sections or []):
        if "Changelog" in label:
            changelog_line = ln
            break
    if changelog_line is None:
        bad = [(e.entry_id, e.line) for e in entries if "Changelog" in e.section]
    else:
        bad = [(e.entry_id, e.line) for e in entries if e.line > changelog_line]
    return CheckResult(
        check_id="post_terminal_append",
        rfm="RFM-10",
        title="Post-terminal append (shadow zone)",
        status=FAIL if bad else PASS,
        severity="warning",
        defects=len(bad),
        opportunities=None,
        evidence=[f"{eid} (L{ln})" for eid, ln in bad],
        reason="entry appended after the `## Changelog` terminal section" if bad else None,
    )


def evaluate_index_desync(entries: List[Entry], index_f: set) -> CheckResult:
    """RFM-11: the hand-maintained quick index stops tracking the body."""
    body_f = {e.entry_id for e in entries if e.entry_id.startswith("F-")}
    missing = sorted(body_f - index_f)
    phantom = sorted((index_f - body_f) - WHITELIST_INDEX_ONLY)
    bad = missing + phantom
    coverage = (len(body_f & index_f) / len(body_f) * 100) if body_f else 100.0
    return CheckResult(
        check_id="index_desync",
        rfm="RFM-11",
        title="F quick-index desync",
        status=FAIL if bad else PASS,
        severity="warning",
        defects=len(bad),
        opportunities=len(body_f),
        evidence=([f"in body, absent from index: {m}" for m in missing]
                  + [f"in index, no body entry: {p}" for p in phantom]
                  + [f"index coverage {coverage:.1f}%"]),
        reason=f"whitelisted honest gaps not counted: {sorted(WHITELIST_INDEX_ONLY)}",
    )


def evaluate_rollup_orphan(entries: List[Entry], rollup_ic: set) -> CheckResult:
    """RFM-12: a Pareto row that points at nothing still reports healthy."""
    body_ic = {e.entry_id for e in entries if re.match(r'^IC-\d{3}$', e.entry_id)}
    orphans = sorted(rollup_ic - body_ic)
    return CheckResult(
        check_id="rollup_orphan",
        rfm="RFM-12",
        title="Orphan IC roll-up row",
        status=FAIL if orphans else PASS,
        severity="critical",
        defects=len(orphans),
        opportunities=len(rollup_ic),
        evidence=[f"{o} cited in roll-up, no body entry" for o in orphans],
        reason="same genus as IC-041 audit-false-pass" if orphans else None,
    )


def evaluate_class_starvation(entries: List[Entry]) -> CheckResult:
    """RFM-16: a ratified class with zero entries is a dormant channel."""
    present = set()
    for e in entries:
        head = e.entry_id.split("-")[0]
        if head in SPEC_CLASSES:
            present.add(head)
    empty = [c for c in SPEC_CLASSES if c not in present]
    return CheckResult(
        check_id="class_starvation",
        rfm="RFM-16",
        title="Ratified-class starvation",
        status=FAIL if empty else PASS,
        severity="warning",
        defects=len(empty),
        opportunities=len(SPEC_CLASSES),
        evidence=[f"class {c}: 0 entries" for c in empty],
        reason="declared in REGISTRY_SPEC.md, never populated; dormant until proof-tested",
    )


def evaluate_header_staleness(header: str, entries: List[Entry], text: str) -> CheckResult:
    """RFM-17: `Last updated` drifts behind the newest dated content."""
    dates = sorted(set(re.findall(r'date_registered:\s*["“]?(\d{4}-\d{2}-\d{2})', text)))
    newest_entry = dates[-1] if dates else None
    gov = sorted(set(re.findall(r'^###\s+(\d{4}-\d{2}-\d{2})\s+—', text, re.M)))
    newest_gov = gov[-1] if gov else None
    newest = max([d for d in (newest_entry, newest_gov) if d], default=None)

    m = re.search(r'\*\*Last updated:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})', header)
    declared = m.group(1) if m else None
    months = {mn: i + 1 for i, mn in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"])}
    declared_iso = None
    if declared:
        dm = re.match(r'([A-Za-z]+) (\d{1,2}), (\d{4})', declared)
        if dm and dm.group(1) in months:
            declared_iso = f"{dm.group(3)}-{months[dm.group(1)]:02d}-{int(dm.group(2)):02d}"

    stale = bool(declared_iso and newest and newest > declared_iso)
    return CheckResult(
        check_id="header_staleness",
        rfm="RFM-17",
        title="Header staleness",
        status=FAIL if stale else PASS,
        severity="info",
        defects=1 if stale else 0,
        opportunities=1,
        evidence=[f"declared Last updated: {declared_iso or declared or 'unparsed'}",
                  f"newest dated content: {newest or 'none found'}"],
        reason="header describes an older file than the one it heads" if stale else None,
    )


def evaluate_ratification_hash_form(text: str) -> CheckResult:
    """RFM-15: a commit SHA where a decision signature is specified.

    CLAUDE.md Decision Routing step 6 and NF_LEDGER_SCHEMA_v1.md both specify
    sha256(candidate | by=Night | at=timestamp | decision=ACCEPT) -- 64 hex
    chars. A 7-8 char git SHA proves when code landed, not what was approved.
    """
    bad = []
    # Capture the whole token, not just its hex prefix, so a non-hex or
    # over-long value is judged rather than silently passing.
    for m in re.finditer(r'\*\*Ratification Hash:\*\*\s*(\S+)', text):
        h = m.group(1)
        if not re.fullmatch(r'[0-9a-fA-F]{64}', h):
            bad.append(h)
    return CheckResult(
        check_id="ratification_hash_form",
        rfm="RFM-15",
        title="Ratification-hash substitution",
        status=FAIL if bad else PASS,
        severity="critical",
        defects=len(bad),
        opportunities=None,
        evidence=[f"'{h}' is {len(h)} chars; a decision signature is exactly 64 hex"
                  for h in bad],
        reason="git commit SHA recorded where sha256(candidate|by|at|decision) is specified"
        if bad else None,
    )


def evaluate_cross_artifact_ratification(
        pq_text: Optional[str], registry_text: str) -> CheckResult:
    """RFM-14: an artifact's ratification state contradicts itself or the registry."""
    ev = []
    if pq_text is None:
        return CheckResult(
            check_id="cross_artifact_ratification", rfm="RFM-14",
            title="Cross-artifact ratification desync", status=ERROR,
            severity="critical",
            reason="PRIORITY_QUEUE.md absent — required input, check could not run",
        )
    pending = bool(re.search(r'ratification_hash.*\|\s*—?\s*\(?pending', pq_text, re.I))
    self_ratified = bool(re.search(r'PRIORITY_QUEUE\.md\s*v?1[._]1\s+ratified', pq_text, re.I))
    registry_ratified = bool(re.search(r'`PRIORITY_QUEUE\.md`\s*v1\.1', registry_text))

    if pending and self_ratified:
        ev.append("PRIORITY_QUEUE.md: metadata says 'pending Z2 signature' while its own "
                  "Appended Events records 'PRIORITY_QUEUE.md v1_1 ratified'")
    if pending and registry_ratified:
        ev.append("PRIORITY_QUEUE.md says pending; REGISTERED.md Governance Ratifications "
                  "lists PRIORITY_QUEUE.md v1.1 as ratified")
    return CheckResult(
        check_id="cross_artifact_ratification",
        rfm="RFM-14",
        title="Cross-artifact ratification desync",
        status=FAIL if ev else PASS,
        severity="critical",
        defects=len(ev),
        opportunities=None,
        evidence=ev,
        reason="an artifact cannot be both pending and ratified" if ev else None,
    )


# ---------------------------------------------------------------------------
# Yield / DPMO
# ---------------------------------------------------------------------------

def compute_baseline(results: List[CheckResult], n_entries: int) -> Dict[str, Any]:
    """Entry-level FPY / DPMO / sigma, matching T1_DEFECT_BASELINE_S070726.md.

    Only the four entry-level checks enter the denominator. File-level checks
    have no per-entry opportunity count; folding them in would inflate the
    denominator and flatter the score.
    """
    entry_results = [r for r in results if r.check_id in ENTRY_LEVEL_CHECKS]
    defects = sum(r.defects for r in entry_results)
    opportunities = n_entries * len(ENTRY_LEVEL_CHECKS)
    if opportunities == 0:
        return {"defects": 0, "opportunities": 0, "fpy": 1.0, "dpmo": 0.0, "sigma": None}
    y = 1 - defects / opportunities
    dpmo = defects / opportunities * 1e6
    sigma = NormalDist().inv_cdf(y) + 1.5 if 0 < y < 1 else None
    return {
        "defects": defects,
        "opportunities": opportunities,
        "fpy": y,
        "dpmo": dpmo,
        "sigma": sigma,
        "methodology": "T1_DEFECT_BASELINE_S070726.md; 1.5-sigma shift convention",
    }


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def run_scan(registry_path: Path, pq_path: Path) -> Dict[str, Any]:
    parsed = collect_registry(registry_path)
    pq_text = collect_priority_queue(pq_path)
    entries = parsed["entries"]

    results = [
        evaluate_ordering_conformance(entries, parsed["sections"]),
        evaluate_required_fields(entries),
        evaluate_frontmatter_fence_form(entries),
        evaluate_quote_hygiene(entries),
        evaluate_post_terminal_append(entries, parsed["sections"]),
        evaluate_index_desync(entries, parsed["index_f"]),
        evaluate_rollup_orphan(entries, parsed["rollup_ic"]),
        evaluate_class_starvation(entries),
        evaluate_header_staleness(parsed["header"], entries, parsed["text"]),
        evaluate_ratification_hash_form(parsed["text"]),
        evaluate_cross_artifact_ratification(pq_text, parsed["text"]),
    ]
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "registry": str(registry_path),
        "entries_parsed": len(entries),
        "results": [r.to_dict() for r in results],
        "baseline": compute_baseline(results, len(entries)),
        "citation": SPEC_CITATION,
    }


def verify_doc(report: Dict[str, Any], doc_path: Path) -> Tuple[bool, List[str]]:
    """Check that the published map's headline numbers match this scan.

    RFM-11 is "a hand-maintained table stops tracking the body". A document
    asserting that failure mode while carrying hand-copied counts would be an
    instance of it. This makes the claim falsifiable: if the registry changes
    and the map is not regenerated, `--verify-doc` fails.

    Anchors assertions to the "Measured Baseline" section to prevent stale values
    in appendices or outdated examples from passing verification.
    """
    if not doc_path.exists():
        return False, [f"{doc_path} not found"]
    text = doc_path.read_text(encoding="utf-8")

    # Extract only the "Measured Baseline" section to prevent stale values
    # in appendices or examples from passing verification
    baseline_match = re.search(r'## Measured Baseline\s*\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
    if not baseline_match:
        return False, ["'Measured Baseline' section not found in document"]
    baseline_text = baseline_match.group(1)

    b = report["baseline"]
    expect = {
        "entry count": str(report["entries_parsed"]),
        "defect count": str(b["defects"]),
        "opportunity count": str(b["opportunities"]),
        "first-pass yield": f"{b['fpy']*100:.1f}%",
        "DPMO": f"{b['dpmo']:,.0f}",
    }
    problems = [f"{label} {val!r} not found in Measured Baseline section"
                for label, val in expect.items() if val not in baseline_text]

    # The Executive Summary restates the headline yield and DPMO in prose and was
    # left outside verification, so it went on asserting 81.2% / 188,380 while the
    # section below it said 80.7% / 193,182 — the same document disagreeing with
    # itself, which is the condition this whole check exists to detect. Scoped to
    # that section on purpose: the Changelog legitimately preserves superseded
    # figures as dated historical entries, and must keep them.
    summary_match = re.search(r'## Executive Summary\s*\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
    if summary_match:
        summary_text = summary_match.group(1)
        for label in ("first-pass yield", "DPMO"):
            if expect[label] not in summary_text:
                problems.append(
                    f"{label} {expect[label]!r} not found in Executive Summary "
                    f"(it restates the headline; regenerate or mark historical)"
                )

    problems.extend(_verify_taxonomy_rows(report, text))
    return (not problems), problems


def _verify_taxonomy_rows(report: Dict[str, Any], text: str) -> List[str]:
    """Check each RFM's occurrence cell in the taxonomy tables against the scan.

    Anchoring only to "Measured Baseline" left the rest of the document
    unguarded: the detail tables carry their own per-RFM occurrence counts, and
    on 2026-09-21 the headline numbers were refreshed while RFM-10 still read
    25 (actual 43), RFM-11 10/45 (actual 9/48), RFM-12 1 (actual 0), RFM-14 2
    (actual 0) and RFM-15 1 (actual 8). The gate passed and the document
    contradicted the scan on the same page — RFM-11 committed by the table that
    defines RFM-11.

    A row is `| **RFM-NN** | name | evidence | **count...** | detection |`. The
    occurrence cell is compared on its first integer, so the surrounding prose
    ("9 / 48 F", "3 / 6 classes", "1 known") stays free-form. Rows for RFMs the
    scanner does not produce are skipped rather than failed, so hand-authored
    entries like RFM-13 and RFM-18 remain valid.

    A second, plain-text row shape is checked too: `| RFM-NN | UNSCORED |
    occurrence | detection | RPN |`, the FMEA summary table. It was invisible
    to the pattern above — no `**` — and on 2026-09-21 that let ten of its
    Occurrence cells sit stale (58/137, 25, 2, 1, ...) through every prior
    round of this fix, including the round that had just regenerated the same
    numbers three headings above it. Anchored on the literal `UNSCORED` token
    in the Severity column, which is this table's own stated invariant (its
    text: "even [RFM-05] is UNSCORED" — no ratified severity mapping exists
    for any row yet); if that ever changes, the anchor should move with it
    rather than silently stop matching.
    """
    problems: List[str] = []
    for r in report["results"]:
        rfm = r["rfm"]
        for pattern, width in (
            (rf"^\|\s*\*\*{re.escape(rfm)}\*\*\s*\|.*$", 6),
            (rf"^\|\s*{re.escape(rfm)}\s*\|\s*UNSCORED[^|]*\|.*$", 5),
        ):
            row = re.search(pattern, text, re.M)
            if not row:
                continue  # not tabulated in this shape
            cells = row.group(0).split("|")
            if len(cells) < width:
                problems.append(f"{rfm} row is malformed — expected {width - 1} cells")
                continue
            occ_cell = cells[4] if width == 6 else cells[3]
            problems.extend(_check_occurrence_cell(rfm, occ_cell, r))
    return problems


def _check_occurrence_cell(rfm: str, cell: str, r: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    found = re.search(r"\d+", cell)
    if not found:
        problems.append(f"{rfm} occurrence cell has no number: {cell.strip()!r}")
        return problems
    if int(found.group(0)) != r["defects"]:
        problems.append(
            f"{rfm} occurrence cell says {found.group(0)}, scan says "
            f"{r['defects']} — regenerate the row"
        )
    # Checking the numerator alone leaves the denominator free to rot: the
    # RFM-07 row read "8 / 137" against a 154-entry registry and passed,
    # because its numerator was right. A stale denominator understates the
    # corpus the defect was measured over, which is the number a reader
    # divides by.
    ratio = re.search(r"(\d+)\s*/\s*(\d+)", cell)
    if ratio and r["opportunities"] is not None:
        if int(ratio.group(2)) != r["opportunities"]:
            problems.append(
                f"{rfm} occurrence denominator says {ratio.group(2)}, scan "
                f"measured over {r['opportunities']} — regenerate the row"
            )
    return problems


def render_report(report: Dict[str, Any]) -> str:
    out = []
    out.append(f"REGISTERED.md failure-mode scan — {report['registry']}")
    out.append(f"entries parsed: {report['entries_parsed']}")
    out.append("")
    out.append(f"{'check':<32} {'RFM':<8} {'status':<6} defects")
    out.append("-" * 62)
    for r in report["results"]:
        opp = f"/{r['opportunities']}" if r["opportunities"] is not None else ""
        out.append(f"{r['check_id']:<32} {r['rfm']:<8} {r['status']:<6} {r['defects']}{opp}")
    b = report["baseline"]
    out.append("")
    out.append("Entry-level baseline (4 checks x N entries):")
    out.append(f"  {b['defects']} defects / {b['opportunities']} opportunities")
    out.append(f"  first-pass yield {b['fpy']*100:.1f}%   DPMO {b['dpmo']:,.0f}"
               + (f"   ~{b['sigma']:.1f} sigma" if b["sigma"] else ""))
    out.append("  (T1 mesh baseline: 42.9% FPY, ~571,000 DPMO, ~1.3 sigma)")
    out.append("")
    out.append("Detail:")
    for r in report["results"]:
        if r["status"] in (PASS, SKIP) and not r["evidence"]:
            continue
        out.append(f"  [{r['rfm']}] {r['title']} — {r['status']}")
        if r["reason"]:
            out.append(f"      note: {r['reason']}")
        for e in r["evidence"][:40]:
            out.append(f"      - {e}")
        if len(r["evidence"]) > 40:
            out.append(f"      ... and {len(r['evidence']) - 40} more")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Self-test — the measurement-system control
# ---------------------------------------------------------------------------

_GOOD_FIXTURE = '''# Fixture
**Last updated:** August 15, 2026

| ID | Slug |
|:---|:---|
| F-01 | alpha |

> IC roll-up: IC-001 pattern

## F-class findings (research)

```
---
id: "F-01"
name: "alpha"
status: REGISTERED
class: F
date_registered: "2026-08-15"
date_origin: "2026-08-01"
session_registered: "S-081526-01"
principles_triggered: ["P-1"]
substrate: "test"
tags: ["test"]
superseded_by: null
---
```

## IC-class corrections (process errors registered)

```
---
id: "IC-001"
name: "beta"
status: REGISTERED
class: IC
date_registered: "2026-08-15"
date_origin: "2026-08-01"
session_registered: "S-081526-01"
principles_triggered: ["P-1"]
substrate: "test"
tags: ["test"]
superseded_by: null
---
```
'''

_BAD_FIXTURE = '''# Fixture
**Last updated:** August 15, 2026

| ID | Slug |
|:---|:---|
| F-01 | alpha |

> IC roll-up: IC-001 pattern, IC-999 orphan

## F-class findings (research)

```
---
id: "F-01"
name: "alpha"
status: REGISTERED
class: F
date_registered: "2026-08-15"
date_origin: "2026-08-01"
session_registered: "S-081526-01"
principles_triggered: ["P-1"]
substrate: "test"
tags: ["test"]
superseded_by: null
---
```

## id: “F-02”
name: “broken-fence-and-curly”
status: REGISTERED
class: F
date_registered: "2026-09-01"
session_registered: "S-090126-01"

### H-LEGACY-01 — bold-prose entry with no front matter at all

**Class:** H (Hypothesis)
**Status:** CANDIDATE
**Registered:** June 14, 2026

## IC-class corrections (process errors registered)

```
---
id: "IC-001"
name: "beta"
status: REGISTERED
class: IC
date_registered: "2026-08-15"
date_origin: "2026-08-01"
session_registered: "S-081526-01"
principles_triggered: ["P-1"]
substrate: "test"
tags: ["test"]
superseded_by: null
---
```

## Changelog

```
---
id: "IC-002"
name: "post-terminal"
class: IC
---
```
'''


def _fix(text: str) -> Dict[str, Any]:
    return parse_registry(text)


def run_self_test(verbose: bool = True) -> bool:
    """Exercise every evaluator against known-good and known-bad fixtures.

    A checker that has never been run against a known defect is as unverified
    as the self-report it replaces. This is the gauge R&R step.
    """
    failures: List[str] = []

    def check(label: str, cond: bool, detail: str = ""):
        if not cond:
            failures.append(f"{label}: {detail}")
        elif verbose:
            print(f"  ok   {label}")

    good = _fix(_GOOD_FIXTURE)
    bad = _fix(_BAD_FIXTURE)

    # --- known-good must be clean on every entry-level check ---
    for fn, name in [
        (evaluate_frontmatter_fence_form, "frontmatter_fence_form"),
        (evaluate_quote_hygiene, "quote_hygiene"),
        (evaluate_required_fields, "required_fields"),
        (evaluate_ordering_conformance, "ordering_conformance"),
    ]:
        r = fn(good["entries"])
        check(f"known-good clean: {name}", r.defects == 0, f"got {r.defects} ({r.evidence})")

    r = evaluate_post_terminal_append(good["entries"])
    check("known-good clean: post_terminal_append", r.defects == 0, f"got {r.defects}")
    r = evaluate_rollup_orphan(good["entries"], good["rollup_ic"])
    check("known-good clean: rollup_orphan", r.defects == 0, f"got {r.evidence}")

    # --- known-bad must be caught, with the exact expected count ---
    r = evaluate_frontmatter_fence_form(bad["entries"])
    # Two distinct fence failures: F-02's `id:` rendered as a heading, and
    # H-LEGACY-01 carrying no front matter at all.
    check("known-bad caught: frontmatter_fence_form", r.defects == 2,
          f"expected 2, got {r.defects}: {r.evidence}")
    r = evaluate_quote_hygiene(bad["entries"])
    check("known-bad caught: quote_hygiene", r.defects == 1, f"expected 1, got {r.defects}")
    r = evaluate_required_fields(bad["entries"])
    check("known-bad caught: required_fields", r.defects >= 1, f"got {r.defects}")
    r = evaluate_post_terminal_append(bad["entries"])
    check("known-bad caught: post_terminal_append", r.defects == 1,
          f"expected 1, got {r.defects}")
    r = evaluate_rollup_orphan(bad["entries"], bad["rollup_ic"])
    check("known-bad caught: rollup_orphan", "IC-999" in " ".join(r.evidence),
          f"got {r.evidence}")
    r = evaluate_ordering_conformance(bad["entries"])
    check("known-bad caught: ordering_conformance", r.defects >= 1, f"got {r.defects}")

    # --- the whitelist must suppress the documented honest gaps ---
    idx = evaluate_index_desync(
        [Entry("F-01", 1, "", "", "F-class")], {"F-01", "F-32", "F-33"})
    check("whitelist suppresses F-32/F-33 false positive", idx.defects == 0,
          f"got {idx.defects}: {idx.evidence}")
    idx2 = evaluate_index_desync(
        [Entry("F-01", 1, "", "", "F-class")], {"F-01", "F-99"})
    check("non-whitelisted phantom still caught", idx2.defects == 1,
          f"got {idx2.defects}")

    # --- ratification hash form ---
    r = evaluate_ratification_hash_form("**Ratification Hash:** e8a501f")
    check("known-bad caught: short hash is not a signature", r.defects == 1,
          f"got {r.defects}")
    r = evaluate_ratification_hash_form("**Ratification Hash:** " + "a" * 64)
    check("known-good clean: 64-hex signature accepted", r.defects == 0, f"got {r.defects}")

    # --- cross-artifact contradiction ---
    r = evaluate_cross_artifact_ratification(
        "| **ratification_hash** | — (pending Z2 signature) |\n"
        "2026-09-09 — PRIORITY_QUEUE.md v1_1 ratified\n", "")
    check("known-bad caught: pending vs ratified contradiction", r.defects >= 1,
          f"got {r.evidence}")
    r = evaluate_cross_artifact_ratification("| **ratification_hash** | abc |\n", "")
    check("known-good clean: no contradiction", r.defects == 0, f"got {r.evidence}")

    # --- staleness ---
    r = evaluate_header_staleness(
        "**Last updated:** August 15, 2026", [],
        'date_registered: "2026-09-01"')
    check("known-bad caught: header staleness", r.defects == 1, f"got {r.defects}")
    r = evaluate_header_staleness(
        "**Last updated:** September 13, 2026", [],
        'date_registered: "2026-09-01"')
    check("known-good clean: header current", r.defects == 0, f"got {r.defects}")

    # --- class starvation (previously untested: a regression here would have
    #     left the documented 3/6 result green) ---
    r = evaluate_class_starvation([Entry("F-01", 1, "", "", "F-class"),
                                   Entry("IC-001", 2, "", "", "IC-class"),
                                   Entry("H-01", 3, "", "", "H-class")])
    check("known-bad caught: class starvation (D/R/GD empty)", r.defects == 3,
          f"expected 3, got {r.defects}: {r.evidence}")
    full = [Entry(f"{c}-01", i, "", "", "") for i, c in enumerate(SPEC_CLASSES)]
    r = evaluate_class_starvation(full)
    check("known-good clean: every class populated", r.defects == 0,
          f"got {r.defects}: {r.evidence}")

    # --- legacy entries must be discovered, not silently dropped ---
    legacy_fix = _fix(_BAD_FIXTURE)
    legacy = [e for e in legacy_fix["entries"] if e.legacy]
    check("legacy heading-style entry discovered", any(
        e.entry_id == "H-LEGACY-01" for e in legacy),
        f"legacy entries found: {[e.entry_id for e in legacy]}")
    check("index table header is not mistaken for an entry",
          not any(e.entry_id == "F" for e in legacy_fix["entries"]),
          "bare 'F' from the quick-index header was parsed as an entry")
    r = evaluate_frontmatter_fence_form(legacy_fix["entries"])
    check("legacy entry counts as fence loss", any(
        "H-LEGACY-01" in e for e in r.evidence), f"got {r.evidence}")

    # --- section order, not just per-entry placement ---
    ordered = [(10, "## F-class findings"), (20, "## IC-class corrections"),
               (30, "### H-class hypotheses")]
    r = evaluate_ordering_conformance([], ordered)
    check("known-good clean: class blocks in F->IC->H order", r.defects == 0
          and not r.evidence, f"got {r.evidence}")
    swapped = [(10, "### H-class hypotheses"), (20, "## F-class findings"),
               (30, "## IC-class corrections")]
    r = evaluate_ordering_conformance([], swapped)
    check("known-bad caught: class blocks out of order",
          any("expected" in e for e in r.evidence), f"got {r.evidence}")

    # --- terminal boundary by position, not by label ---
    secs = [(10, "## F-class findings"), (50, "## Changelog"),
            (90, "## Governance Ratifications")]
    r = evaluate_post_terminal_append(
        [Entry("F-01", 20, "", "", "F-class"),
         Entry("IC-9", 60, "", "", "Changelog"),
         Entry("H-9", 95, "", "", "Governance Ratifications")], secs)
    check("known-bad caught: entry past a LATER terminal section", r.defects == 2,
          f"expected 2 (L60 and L95), got {r.defects}: {r.evidence}")

    # --- quote hygiene beyond the first four fields ---
    r = evaluate_quote_hygiene([Entry(
        "F-9", 1, "", 'id: "F-9"\ndate_registered: \u201c2026-01-01\u201d', "F-class")])
    check("known-bad caught: curly quotes in a non-core field", r.defects == 1,
          f"got {r.defects}")

    # --- hash must be exactly 64 hex ---
    for bad_hash, label in ((("a" * 65), "65 hex"), ("not-a-hash", "non-hex")):
        r = evaluate_ratification_hash_form(f"**Ratification Hash:** {bad_hash}")
        check(f"known-bad caught: {label} rejected", r.defects == 1, f"got {r.defects}")

    # --- absent required input must ERROR, never pass quietly ---
    r = evaluate_cross_artifact_ratification(None, "")
    check("absent PRIORITY_QUEUE.md errors rather than skipping", r.status == ERROR,
          f"got {r.status}")

    # --- baseline arithmetic ---
    fake = [
        CheckResult("ordering_conformance", "RFM-09", "", FAIL, "warning", 29, 131),
        CheckResult("required_fields", "RFM-06", "", FAIL, "warning", 8, 131),
        CheckResult("frontmatter_fence_form", "RFM-07", "", FAIL, "critical", 4, 131),
        CheckResult("quote_hygiene", "RFM-08", "", FAIL, "critical", 3, 131),
        CheckResult("post_terminal_append", "RFM-10", "", FAIL, "warning", 25, None),
    ]
    b = compute_baseline(fake, 131)
    check("baseline excludes file-level checks from denominator",
          b["defects"] == 44 and b["opportunities"] == 524,
          f"got {b['defects']}/{b['opportunities']}")
    check("baseline DPMO arithmetic", abs(b["dpmo"] - 83969) < 2, f"got {b['dpmo']:.0f}")

    # --- verify_doc itself, which gates a published document and had no fixture.
    #     A parser regression here would make the blocking step pass silently on
    #     a stale map, which is the failure it was added to catch.
    vd_report = {
        "entries_parsed": 154,
        "baseline": {"defects": 119, "opportunities": 616,
                     "fpy": 0.807, "dpmo": 193182.0, "sigma": 2.4},
        # dict form, as run_scan serializes it — verify_doc consumes the report
        # after serialization, so the fixture must match that shape, not the
        # dataclass.
        "results": [
            dataclasses.asdict(
                CheckResult("frontmatter_fence_form", "RFM-07", "", FAIL, "critical", 8, 154)),
            dataclasses.asdict(
                CheckResult("index_desync", "RFM-11", "", FAIL, "warning", 9, 48)),
        ],
    }
    good_doc = (
        "## Executive Summary\n\nscores 80.7% first-pass yield / 193,182 DPMO.\n\n"
        "## Measured Baseline\n\n154 entries, 119 defects / 616 opportunities "
        "-> 80.7% first-pass yield -> 193,182 DPMO\n\n"
        "## Taxonomy\n\n"
        "| **RFM-07** | name | evidence | **8 / 154** | 10 |\n"
        "| **RFM-11** | name | evidence | **9 / 48 F** | 10 |\n"
    )
    with tempfile.TemporaryDirectory() as td:
        gp = Path(td) / "good.md"
        gp.write_text(good_doc, encoding="utf-8")
        ok, probs = verify_doc(vd_report, gp)
        check("verify-doc clean on a current document", ok, f"got {probs}")

        # numerator stale
        p2 = Path(td) / "num.md"
        p2.write_text(good_doc.replace("**8 / 154**", "**5 / 154**"), encoding="utf-8")
        ok, probs = verify_doc(vd_report, p2)
        check("verify-doc catches a stale occurrence numerator",
              not ok and any("says 5" in p for p in probs), f"got {probs}")

        # denominator stale while numerator is right — the RFM-07 "8 / 137" case
        p3 = Path(td) / "den.md"
        p3.write_text(good_doc.replace("**8 / 154**", "**8 / 137**"), encoding="utf-8")
        ok, probs = verify_doc(vd_report, p3)
        check("verify-doc catches a stale denominator behind a correct numerator",
              not ok and any("denominator" in p for p in probs), f"got {probs}")

        # Executive Summary contradicting the baseline it summarizes
        p4 = Path(td) / "sum.md"
        p4.write_text(good_doc.replace(
            "scores 80.7% first-pass yield / 193,182 DPMO.",
            "scores 81.2% first-pass yield / 188,380 DPMO."), encoding="utf-8")
        ok, probs = verify_doc(vd_report, p4)
        check("verify-doc catches a stale Executive Summary",
              not ok and any("Executive Summary" in p for p in probs), f"got {probs}")

        # a taxonomy row for an RFM the scanner does not produce must not fail
        p5 = Path(td) / "extra.md"
        p5.write_text(good_doc + "| **RFM-18** | hand-authored | ev | 1 of 43 | 10 |\n",
                      encoding="utf-8")
        ok, probs = verify_doc(vd_report, p5)
        check("verify-doc ignores rows the scanner does not produce", ok, f"got {probs}")

    if verbose:
        print()
        if failures:
            print(f"SELF-TEST FAILED — {len(failures)} assertion(s):")
            for f in failures:
                print(f"  FAIL {f}")
        else:
            print("SELF-TEST PASSED — all evaluators detect their known-bad fixtures")
    return not failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Scan REGISTERED.md for registry failure modes (RFM taxonomy).")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("scan", help="scan the registry")
    sp.add_argument("--input", default="REGISTERED.md")
    sp.add_argument("--priority-queue", default="PRIORITY_QUEUE.md")
    sp.add_argument("--json", action="store_true", help="emit JSON")
    sp.add_argument("--out", help="write report to a file")
    sp.add_argument("--verify-doc", metavar="PATH",
                    help="assert the published map's headline numbers match "
                         "this scan; exits non-zero when the doc has gone stale")
    sp.add_argument("--enforce", action="store_true",
                    help="exit non-zero when defects are present (opt-in; "
                         "advisory by default pending Z2 ruling)")

    sub.add_parser("self-test", help="validate the scanner against fixtures")
    p.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)

    args = p.parse_args(argv)

    if args.smoke_test:
        ok = run_smoke_test()
        print("smoke-test: " + ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    if args.cmd == "self-test":
        return 0 if run_self_test(verbose=True) else 1

    if args.cmd == "scan":
        registry = Path(args.input)
        if not registry.exists():
            print(f"ERROR: {registry} not found", file=sys.stderr)
            return 2
        report = run_scan(registry, Path(args.priority_queue))
        text = json.dumps(report, indent=2) if args.json else render_report(report)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(f"report written to {args.out}")
        else:
            print(text)
        if args.verify_doc:
            ok, problems = verify_doc(report, Path(args.verify_doc))
            print(f"\nverify-doc: {'PASS' if ok else 'FAIL'} — {args.verify_doc}")
            for pr in problems:
                print(f"  - {pr}")
            if not ok:
                return 1

        # Always check for missing inputs (errors/skips); don't gate on --enforce.
        # A missing input means the tool did not fully run; exit nonzero to signal
        # that the result is incomplete, not just warnings.
        total = sum(r["defects"] for r in report["results"])
        unrun = [r["check_id"] for r in report["results"]
                 if r["status"] in (ERROR, SKIP)]
        if unrun:
            print(f"\nWARNING: {len(unrun)} check(s) did not run: "
                  f"{', '.join(unrun)}", file=sys.stderr)
            if not args.json:
                return 1

        if args.enforce:
            if total or unrun:
                print(f"\nENFORCE: failing on {total} defects" +
                      (f" and {len(unrun)} unrun checks" if unrun else ""),
                      file=sys.stderr)
                return 1
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
