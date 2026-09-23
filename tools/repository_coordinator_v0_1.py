#!/usr/bin/env python3
"""
repository_coordinator_v0_1.py — evidence-bounded repository coordination index.
Builder v1.7 compliant
HumanAIOS — PR-RELEVANCE-01

Builds a read-only coordination view over live pull requests and canonical
repository constraints. It answers "what should the operator inspect next?"
without granting authority, changing queue state, closing PRs, or merging code.

Core invariants:
  OPEN_IS_NOT_RELEVANT
  RELEVANT_IS_NOT_WARRANTED
  MERGEABLE_IS_NOT_CURRENT
  AGE_IS_NOT_STALENESS
  GUIDANCE_REQUIRES_EVIDENCE

Inputs are an offline JSON snapshot collected by the GitHub workflow plus the
checked-out canonical PRIORITY_QUEUE.md. The tool does not call GitHub itself.

Usage:
  python3 tools/repository_coordinator_v0_1.py --snapshot snapshot.json
  python3 tools/repository_coordinator_v0_1.py --snapshot snapshot.json \
      --output index.json --markdown index.md
  python3 tools/repository_coordinator_v0_1.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

TOOL_NAME = "repository_coordinator"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parent.parent

STOPWORDS = {
    "add", "all", "and", "build", "chore", "complete", "deps", "fix", "fixes",
    "for", "from", "implementation", "implement", "in", "of", "on", "pull",
    "request", "requirement", "the", "to", "update", "with", "workflow", "yml",
    "yaml", "v0", "v1", "v2", "phase", "ci",
}
CONTROL_TERMS = re.compile(
    r"\b(gate|enforce|enforcer|block|pause|merge|priority|schedule|ratif|authoriz|"
    r"workflow|ship|release|activate)\w*\b",
    re.I,
)
TIME_CONTROL_TERMS = re.compile(
    r"\b(?:\d+\s*[- ]?(?:day|week|month)s?|daily|weekly|monthly|"
    r"rolling\s+window|window_end|deadline|calendar[- ](?:driven|based))\b",
    re.I,
)
PATH_REF_RE = re.compile(
    r"(?<![\w./-])("
    r"(?:\.github|z1-inbox|tools|scripts|docs|ui|ledgers|outputs|tests)"
    r"/[A-Za-z0-9_.\-/]+"
    r")"
)
PR_REF_RE = re.compile(r"(?<![\w])#(\d{1,6})\b")
ACTIVE_GATE_RE = re.compile(
    r"^###\s+(Q-[A-Z0-9-]+).*?\n(?:.*\n){0,8}?\*\*State:\*\*\s*`?([A-Z_]+)`?",
    re.M,
)

ACTION_ORDER = {
    "CLOSE_PRESERVE": 0,
    "REEXAMINE": 1,
    "COMPARE_CONSOLIDATE": 2,
    "REBASE_RETEST": 3,
    "ADVANCE": 4,
}


@dataclass
class Finding:
    code: str
    severity: str
    evidence: str


def _tokens(title: str) -> set[str]:
    raw = re.findall(r"[a-z][a-z0-9_-]{1,}", title.lower())
    return {
        t for t in raw
        if t not in STOPWORDS
        and not re.fullmatch(r"\d+(?:[._-]\d+)*", t)
        and len(t) > 1
    }


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _active_gates(priority_queue_text: str) -> list[str]:
    gates = []
    for gate, state in ACTIVE_GATE_RE.findall(priority_queue_text or ""):
        if state.upper() in {"GATING", "BLOCKING", "ACTIVE"}:
            gates.append(gate)
    return gates


def _latest_review_states(reviews: list[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, tuple[str, str]] = {}
    for review in reviews or []:
        user = str((review.get("user") or {}).get("login") or review.get("user") or "unknown")
        state = str(review.get("state") or "").upper()
        if state not in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            continue
        ts = str(review.get("submitted_at") or review.get("created_at") or "")
        prior = latest.get(user)
        if prior is None or ts >= prior[0]:
            latest[user] = (ts, state)
    return {u: state for u, (_, state) in latest.items()}


def _claimed_zones(body: str) -> set[str]:
    body = body or ""
    claimed = set()
    for z in ("Z1", "Z2", "Z3"):
        if re.search(rf"-\s*\[[xX]\]\s*\*\*{z}\*\*", body):
            claimed.add(z)
    return claimed


def _required_authority(pr: dict[str, Any]) -> str:
    files = set(pr.get("files") or [])
    if any(path.startswith(".github/workflows/") for path in files):
        return "Z2"
    if files & {"REGISTERED.md", "PRIORITY_QUEUE.md", "MOLT_STATE.md"}:
        return "Z2"
    return "Z1"


def _missing_refs(body: str, main_paths: set[str], own_files: set[str]) -> list[str]:
    refs = set(PATH_REF_RE.findall(body or ""))
    return sorted(p for p in refs if p not in main_paths and p not in own_files)


def _referenced_pr_failures(
    pr: dict[str, Any],
    referenced: dict[str, dict[str, Any]],
) -> list[str]:
    out = []
    own = int(pr.get("number") or 0)
    for raw in PR_REF_RE.findall(pr.get("body") or ""):
        n = int(raw)
        if n == own:
            continue
        state = referenced.get(str(n)) or referenced.get(n)
        if not state:
            continue
        if state.get("state") == "closed" and not state.get("merged"):
            out.append(
                f"#{n} is referenced but closed without merge"
            )
    return sorted(set(out))


def _competition(prs: list[dict[str, Any]]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {int(p["number"]): [] for p in prs}
    for i, a in enumerate(prs):
        af = set(a.get("files") or [])
        at = _tokens(a.get("title") or "")
        for b in prs[i + 1:]:
            bf = set(b.get("files") or [])
            bt = _tokens(b.get("title") or "")
            file_overlap = _jaccard(af, bf)
            title_overlap = _jaccard(at, bt)
            # Same files alone are not enough: dependency bumps often share one
            # requirements file but pursue distinct objectives.
            if file_overlap >= 0.50 and title_overlap >= 0.28:
                an, bn = int(a["number"]), int(b["number"])
                result[an].append(bn)
                result[bn].append(an)
    return result


def _temporal_control_signa