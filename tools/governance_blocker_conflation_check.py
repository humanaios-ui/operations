#!/usr/bin/env python3
"""
governance_blocker_conflation_check.py — detects bundled-gate conflation and
checks candidate-block completeness against scattered source requirements.
Builder v1.7 compliant
HumanAIOS — audit tool, read-only

Named after REGISTERED.md's own pattern-roll-up entry IC-033
("Governance-blocker-conflation", instance Z2-CORPUS-TRUST-01): one gate
line bundling several structurally independent decisions, which blocks every
downstream item behind the slowest one even though they don't depend on each
other. This tool mechanizes the two manual steps that fix used by hand:

  1. detect_bundled_gates  — flag a source line that *looks* like a bundled
     gate (one decision verb, 2+ comma/and-separated asks, no existing
     sub-decomposition directly beneath it) so a human/Z1 can decide whether
     to split it. It does not decide HOW to split it.
  2. check_completeness    — given a set of named sources (issue bodies, PR
     review threads, protocol-doc sections) and a consolidated candidate
     document, report which requirement-shaped lines in the sources are not
     reflected anywhere in the candidate. This is the "did the consolidation
     actually capture everything" check that was otherwise done by hand.

Trust boundary: this tool reads an offline JSON snapshot and local files only.
It does not call GitHub itself and holds no credentials — the same boundary
tools/repository_coordinator_v0_1.py uses, for the same reason: a candidate
should not be able to under-represent its own sources by controlling what a
live fetch returns.

Authority: Zone 1 (advisory/read-only). This tool grants no admission, ratifies
nothing, and does not itself decide whether a flagged conflation is real or a
flagged gap matters — that judgment stays with Z1/Z2, per CLAUDE.md's Decision
Routing.

Usage:
  python3 tools/governance_blocker_conflation_check.py --snapshot snapshot.json
  python3 tools/governance_blocker_conflation_check.py --snapshot snapshot.json --output report.json --markdown report.md
  python3 tools/governance_blocker_conflation_check.py --smoke-test

snapshot.json shape:
  {
    "sources": {"<source_id>": "<raw text>", ...},
    "candidate": "<raw text of the consolidated candidate document, or null>"
  }
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TOOL_NAME = "governance_blocker_conflation_check"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "audit_tool"
TOOL_ZONE = 1  # 1=execute/advisory, 2=ratify, 3=night

ROOT = Path(__file__).resolve().parents[1]

_STOPWORDS = frozenset({
    "a", "an", "the", "of", "to", "for", "and", "or", "is", "are", "in",
    "on", "at", "be", "by", "this", "that", "with", "as", "not", "it",
    "its", "has", "have", "if", "no", "any", "per", "-", "--",
})

_CHECKLIST_RE = re.compile(r"^\s*[-*]\s*\[\s?\]\s*(.+?)\s*$", re.MULTILINE)
_DECISION_NEEDED_RE = re.compile(r"(?mi)\*{0,2}decision needed\*{0,2}:?\s*(.+?)\s*$")

# A "bundled gate" candidate line: a decision verb (admit/ratify/approve/
# decide/accept/sign off), with 2+ comma/semicolon/"and"-separated asks
# after it on the same line. Deliberately loose -- false positives are
# expected and are why this is advisory, not a block.
_BUNDLED_GATE_VERB_RE = re.compile(r"(?i)\b(admit|ratify|approve|decide on|sign off on)\b")
_SEPARATOR_RE = re.compile(r"[,;]|\band\b", re.I)
_SUBLIST_RE = re.compile(r"^\s*(?:\d+[.)]|[-*]\s*\[)", re.MULTILINE)


@dataclass
class RequirementLine:
    source_id: str
    kind: str  # "checklist" | "decision_needed"
    text: str


@dataclass
class BundledGateCandidate:
    source_id: str
    line: str
    verb: str


def normalize_tokens(text: str) -> set[str]:
    """Lowercase word tokens, markdown/punctuation stripped, stopwords
    dropped. Used only for the fuzzy overlap check -- not a semantic model,
    just enough to survive rewording between a source and its candidate."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def extract_requirement_lines(text: str, source_id: str) -> list[RequirementLine]:
    """Pull checklist items (`- [ ] ...`) and "Decision needed:" lines out of
    a source document. These are the two requirement shapes this repo's own
    candidate blocks and issue threads already use (see z1-inbox/*/Q-*.md,
    #1200's acceptance criteria)."""
    lines: list[RequirementLine] = []
    for m in _CHECKLIST_RE.finditer(text):
        lines.append(RequirementLine(source_id, "checklist", m.group(1).strip()))
    for m in _DECISION_NEEDED_RE.finditer(text):
        lines.append(RequirementLine(source_id, "decision_needed", m.group(1).strip()))
    return lines


def detect_bundled_gates(text: str, source_id: str) -> list[BundledGateCandidate]:
    """Flag lines shaped like IC-033's Z2-CORPUS-TRUST-01: one decision verb
    governing 2+ distinct asks on one line, with no sub-decomposition
    (numbered or checkbox list) in the following few lines. Advisory only --
    this does not claim the asks are actually independent, only that the
    shape matches the pattern REGISTERED.md already names."""
    candidates: list[BundledGateCandidate] = []
    text_lines = text.splitlines()
    for i, line in enumerate(text_lines):
        verb_match = _BUNDLED_GATE_VERB_RE.search(line)
        if not verb_match:
            continue
        remainder = line[verb_match.end():]
        if len(_SEPARATOR_RE.findall(remainder)) < 2:
            continue
        lookahead = "\n".join(text_lines[i + 1 : i + 4])
        if _SUBLIST_RE.search(lookahead):
            continue  # already decomposed directly beneath it
        candidates.append(
            BundledGateCandidate(source_id, line.strip(), verb_match.group(1).lower())
        )
    return candidates


def check_completeness(
    sources: dict[str, str], candidate_text: str, threshold: float = 0.6
) -> dict:
    """For every requirement-shaped line found across `sources`, check
    whether its significant tokens are substantially present somewhere in
    `candidate_text`. A line below `threshold` overlap is reported as
    unrepresented -- a candidate completeness gap, not proof the candidate
    is wrong (a source line can legitimately be out of scope)."""
    candidate_tokens = normalize_tokens(candidate_text)
    represented: list[dict] = []
    unrepresented: list[dict] = []
    for source_id, text in sources.items():
        for req in extract_requirement_lines(text, source_id):
            req_tokens = normalize_tokens(req.text)
            if not req_tokens:
                continue
            overlap = len(req_tokens & candidate_tokens) / len(req_tokens)
            row = {
                "source_id": req.source_id,
                "kind": req.kind,
                "text": req.text,
                "overlap": round(overlap, 3),
            }
            (represented if overlap >= threshold else unrepresented).append(row)
    return {
        "threshold": threshold,
        "total_requirements": len(represented) + len(unrepresented),
        "represented": represented,
        "unrepresented": unrepresented,
    }


def analyze(snapshot: dict) -> dict:
    sources: dict[str, str] = snapshot.get("sources", {})
    candidate_text: str = snapshot.get("candidate") or ""

    bundled: list[dict] = []
    for source_id, text in sources.items():
        for c in detect_bundled_gates(text, source_id):
            bundled.append({"source_id": c.source_id, "line": c.line, "verb": c.verb})
    if candidate_text:
        for c in detect_bundled_gates(candidate_text, "candidate"):
            bundled.append({"source_id": c.source_id, "line": c.line, "verb": c.verb})

    report: dict = {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "bundled_gate_candidates": bundled,
    }
    if candidate_text:
        report["completeness"] = check_completeness(sources, candidate_text)
    return report


def render_markdown(report: dict) -> str:
    lines = [f"# Governance blocker/conflation check ({report['tool']} v{report['version']})", ""]

    bundled = report.get("bundled_gate_candidates", [])
    lines.append(f"## Possible bundled gates ({len(bundled)})")
    lines.append("")
    if not bundled:
        lines.append("None detected. Advisory only -- absence here is not proof none exist.")
    for b in bundled:
        lines.append(f"- `{b['source_id']}` (verb: {b['verb']}): {b['line']}")
    lines.append("")

    completeness = report.get("completeness")
    if completeness is not None:
        unrep = completeness["unrepresented"]
        lines.append(
            f"## Candidate completeness: {len(completeness['represented'])}/"
            f"{completeness['total_requirements']} requirement lines represented "
            f"(threshold {completeness['threshold']})"
        )
        lines.append("")
        if unrep:
            lines.append("**Unrepresented in the candidate:**")
            for r in unrep:
                lines.append(f"- `{r['source_id']}` ({r['kind']}, overlap {r['overlap']}): {r['text']}")
        else:
            lines.append("No requirement line fell below the overlap threshold.")
        lines.append("")

    return "\n".join(lines)


def run_smoke_test() -> bool:
    # Fixture 1: IC-033's own documented shape (Z2-CORPUS-TRUST-01) -- must
    # be flagged as a bundled gate.
    bundled_text = (
        "- [ ] Z2: admit bounded protocol, budget, reviewer/ethics controls; "
        "no unapproved live model calls.\n"
    )
    candidates = detect_bundled_gates(bundled_text, "fixture-1114")
    assert len(candidates) == 1, candidates
    assert candidates[0].verb == "admit"

    # Fixture 2: the same line, but already decomposed into a checklist
    # directly beneath it -- must NOT be flagged.
    decomposed_text = (
        "Z2: admit bounded protocol, budget, reviewer/ethics controls.\n"
        "1. Budget decision\n"
        "2. Reviewer decision\n"
        "3. Ethics decision\n"
    )
    assert detect_bundled_gates(decomposed_text, "fixture-decomposed") == []

    # Fixture 3: completeness check -- a candidate that covers budget and
    # reviewer but drops ethics must report the ethics line as unrepresented.
    sources = {
        "1200": (
            "- [ ] Confirm sprint signup and submission UI state with provider.\n"
            "- [ ] Freeze exact phrases, contexts, prompts, rating rubric.\n"
        ),
        "1114": (
            "- [ ] Z2: admit bounded protocol, budget, reviewer/ethics controls; "
            "no unapproved live model calls.\n"
        ),
    }
    candidate_covers_budget_and_reviewer_only = (
        "Decision needed: name the provider/model and a dollar ceiling for the budget.\n"
        "Decision needed: name or approve the two blinded raters and the kappa threshold.\n"
    )
    result = check_completeness(sources, candidate_covers_budget_and_reviewer_only, threshold=0.5)
    assert result["total_requirements"] == 3, result
    unrep_texts = [r["text"] for r in result["unrepresented"]]
    assert any("admit bounded protocol" in t for t in unrep_texts), result

    # Fixture 4: a candidate that explicitly cites the ethics line should
    # mark it represented, not just budget/reviewer.
    candidate_covers_all_three = candidate_covers_budget_and_reviewer_only + (
        "Decision needed: accept the ethics scaffolding or specify required text first "
        "-- this candidate admits bounded protocol, budget, reviewer and ethics controls.\n"
    )
    result2 = check_completeness(sources, candidate_covers_all_three, threshold=0.5)
    assert len(result2["unrepresented"]) < len(result["unrepresented"]), (result, result2)

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)

    if args.smoke_test:
        print("PASS" if run_smoke_test() else "FAIL")
        return 0

    if not args.snapshot:
        parser.error("--snapshot is required unless --smoke-test is used")

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    report = analyze(snapshot)
    if "completeness" in report:
        report["completeness"] = check_completeness(
            snapshot.get("sources", {}), snapshot.get("candidate") or "", args.threshold
        )

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
