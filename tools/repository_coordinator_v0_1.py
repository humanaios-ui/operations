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


def _temporal_control_signal(pr: dict[str, Any]) -> bool:
    """Detect time-driven *control* semantics, not examples or domain dates.

    PR prose is useful because authors describe the behavior they intend. Diff
    evidence is restricted to workflow/canonical-control surfaces: scanning
    every Python/test fixture produced a false positive on this coordinator's
    own adversarial string ("30-day rolling window blocks merge").
    """
    body = pr.get("body") or ""
    control_paths = {
        "PRIORITY_QUEUE.md", "MOLT_STATE.md", "constants.json",
        "RESOURCE_UNITS.yaml", "CANDIDATE_BLOCK_TEMPLATE.md",
        "INTENT_GRAPH.yaml", "TEMPORAL_DISSOLUTION_POLICY.md",
    }
    patch_parts = []
    for f in pr.get("file_details") or []:
        path = str(f.get("filename") or f.get("path") or "")
        if path.startswith(".github/workflows/") or path in control_paths:
            patch = str(f.get("patch") or "")
            # Deleted/context lines are evidence of history, not newly proposed
            # control. Keep only added lines (excluding the +++ diff header).
            added = "\n".join(
                line[1:] for line in patch.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            )
            patch_parts.append(added)
    text = body + "\n" + "\n".join(patch_parts)
    return bool(TIME_CONTROL_TERMS.search(text) and CONTROL_TERMS.search(text))


def classify(
    pr: dict[str, Any],
    *,
    competition: dict[int, list[int]],
    main_paths: set[str],
    referenced_prs: dict[str, dict[str, Any]],
    active_gates: list[str],
) -> dict[str, Any]:
    number = int(pr["number"])
    body = pr.get("body") or ""
    files = set(pr.get("files") or [])
    findings: list[Finding] = []

    zero_diff = len(files) == 0
    if zero_diff:
        findings.append(Finding(
            "ZERO_DIFF", "HIGH",
            "GitHub reports no changed files; there is no remaining merge delta."
        ))

    missing = _missing_refs(body, main_paths, files)
    for path in missing[:12]:
        findings.append(Finding(
            "MISSING_REFERENCED_ARTIFACT", "HIGH",
            f"PR body references `{path}`, which is absent from current main and this PR's own changed files."
        ))

    dead_refs = _referenced_pr_failures(pr, referenced_prs)
    for evidence in dead_refs[:12]:
        findings.append(Finding("CLOSED_UNMERGED_REFERENCE", "HIGH", evidence))

    review_states = _latest_review_states(pr.get("reviews") or [])
    blockers = sorted(u for u, state in review_states.items() if state == "CHANGES_REQUESTED")
    if blockers:
        findings.append(Finding(
            "CHANGES_REQUESTED", "HIGH",
            "Latest decisive review state requests changes from: " + ", ".join(blockers)
        ))

    required = _required_authority(pr)
    claimed = _claimed_zones(body)
    if required == "Z2" and "Z2" not in claimed:
        findings.append(Finding(
            "AUTHORITY_CLAIM_MISMATCH", "HIGH",
            "Diff touches a workflow/canonical control surface but the PR body does not claim Z2 review."
        ))

    gate_hits: list[str] = []
    if active_gates and _temporal_control_signal(pr):
        # v0.1 only has a mechanical detector for the global temporal gate.
        temporal = [g for g in active_gates if "TEMPORAL" in g]
        if temporal:
            gate_hits.extend(temporal)
            findings.append(Finding(
                "ACTIVE_GATE_REVIEW_REQUIRED", "HIGH",
                "PR contains time-based control language while the canonical temporal-dissolution gate is active: "
                + ", ".join(temporal)
            ))

    competitors = sorted(competition.get(number) or [])
    if competitors:
        findings.append(Finding(
            "COMPETING_IMPLEMENTATION", "MEDIUM",
            "Substantial file + objective overlap with open PR(s): "
            + ", ".join(f"#{n}" for n in competitors)
        ))

    mergeable_state = str(pr.get("mergeable_state") or "").lower()
    if mergeable_state in {"dirty", "behind"}:
        findings.append(Finding(
            "BASE_OR_CONFLICT_DRIFT", "MEDIUM",
            f"GitHub mergeable_state is `{mergeable_state}`; refresh against current main before merge."
        ))

    high_codes = {f.code for f in findings if f.severity == "HIGH"}
    if zero_diff:
        action = "CLOSE_PRESERVE"
        next_action = "Preserve the PR as evidence/history; do not treat it as an active merge unit."
    elif high_codes:
        action = "REEXAMINE"
        next_action = "Resolve the listed warrant/evidence/authority conflicts before investing in merge repair."
    elif competitors:
        action = "COMPARE_CONSOLIDATE"
        next_action = "Compare the overlapping implementations, preserve unique contributions, and choose or extract one merge unit."
    elif mergeable_state in {"dirty", "behind"}:
        action = "REBASE_RETEST"
        next_action = "Refresh against current main and rerun the relevant test suite."
    else:
        action = "ADVANCE"
        next_action = "Proceed to ordinary review/testing; no coordinator-level blocker was detected."

    if zero_diff:
        objective = "HISTORICAL"
    else:
        objective = "LIVE"

    state_alignment = "CURRENT"
    if high_codes:
        state_alignment = "REVALIDATION_REQUIRED"
    elif mergeable_state in {"dirty", "behind"}:
        state_alignment = "DRIFTED"

    evidence_status = "CURRENT"
    if {"MISSING_REFERENCED_ARTIFACT", "CLOSED_UNMERGED_REFERENCE", "CHANGES_REQUESTED"} & high_codes:
        evidence_status = "STALE_OR_CONTESTED"

    dependency_status = "SATISFIED"
    if dead_refs or missing:
        dependency_status = "INVALIDATED_OR_MISSING"
    elif competitors:
        dependency_status = "COMPETING"

    return {
        "number": number,
        "title": pr.get("title") or "",
        "url": pr.get("html_url") or pr.get("url"),
        "objective": objective,
        "state_alignment": state_alignment,
        "dependency": {
            "status": dependency_status,
            "competing_prs": competitors,
        },
        "authority": {
            "required": required,
            "claimed": sorted(claimed),
            "status": "MISMATCH" if "AUTHORITY_CLAIM_MISMATCH" in high_codes else "ALIGNED_OR_UNCLAIMED",
        },
        "canonical_gates": {
            "status": "REVIEW_REQUIRED" if gate_hits else "CLEAR",
            "blockers": gate_hits,
        },
        "evidence": {"status": evidence_status},
        "merge_surface": {
            "zero_diff": zero_diff,
            "changed_files": len(files),
            "mergeable_state": mergeable_state or "unknown",
        },
        "guidance": {
            "action": action,
            "next_action": next_action,
        },
        "findings": [asdict(f) for f in findings],
    }


def analyze(snapshot: dict[str, Any], priority_queue_text: str) -> dict[str, Any]:
    prs = list(snapshot.get("pull_requests") or [])
    competitions = _competition(prs)
    main_paths = set(snapshot.get("main_paths") or [])
    referenced = snapshot.get("referenced_pull_requests") or {}
    gates = _active_gates(priority_queue_text)

    items = [
        classify(
            pr,
            competition=competitions,
            main_paths=main_paths,
            referenced_prs=referenced,
            active_gates=gates,
        )
        for pr in prs
    ]
    items.sort(key=lambda x: (ACTION_ORDER[x["guidance"]["action"]], x["number"]))

    counts: dict[str, int] = {}
    for item in items:
        action = item["guidance"]["action"]
        counts[action] = counts.get(action, 0) + 1

    return {
        "schema_version": "0.1",
        "advisory_only": True,
        "repository": snapshot.get("repository"),
        "main_sha": snapshot.get("main_sha"),
        "active_canonical_gates": gates,
        "invariants": [
            "OPEN_IS_NOT_RELEVANT",
            "RELEVANT_IS_NOT_WARRANTED",
            "MERGEABLE_IS_NOT_CURRENT",
            "AGE_IS_NOT_STALENESS",
            "GUIDANCE_REQUIRES_EVIDENCE",
        ],
        "counts": counts,
        "items": items,
    }


def render_markdown(index: dict[str, Any]) -> str:
    lines = [
        "<!-- repository-coordinator -->",
        "## Repository Coordinator — advisory index",
        "",
        f"Main: `{str(index.get('main_sha') or 'unknown')[:12]}` · "
        f"Open PRs indexed: **{len(index.get('items') or [])}** · "
        "**No authority effect**",
        "",
        "> Guidance is evidence-bounded and state-based. PR age is intentionally not a signal.",
        "",
    ]
    gates = index.get("active_canonical_gates") or []
    if gates:
        lines.append("Active canonical gate(s): " + ", ".join(f"`{g}`" for g in gates))
        lines.append("")

    groups = [
        ("REEXAMINE", "Reexamine before repair/merge"),
        ("COMPARE_CONSOLIDATE", "Competing work — compare/consolidate"),
        ("REBASE_RETEST", "Refresh and retest"),
        ("ADVANCE", "Advance through ordinary review"),
        ("CLOSE_PRESERVE", "Preserve/close as non-merge work"),
    ]
    by_action: dict[str, list[dict[str, Any]]] = {}
    for item in index.get("items") or []:
        by_action.setdefault(item["guidance"]["action"], []).append(item)

    for action, heading in groups:
        rows = by_action.get(action) or []
        if not rows:
            continue
        lines += [f"### {heading}", "", "| PR | Why | Next action |", "|---|---|---|"]
        for item in rows:
            findings = item.get("findings") or []
            why = "; ".join(f["evidence"] for f in findings[:3]) or "No coordinator-level blocker detected."
            why = why.replace("|", "\\|").replace("\n", " ")
            nxt = item["guidance"]["next_action"].replace("|", "\\|")
            lines.append(
                f"| [#{item['number']}]({item.get('url') or '#'}) {item['title']} | {why} | {nxt} |"
            )
        lines.append("")

    lines += [
        "---",
        "`OPEN_IS_NOT_RELEVANT · RELEVANT_IS_NOT_WARRANTED · MERGEABLE_IS_NOT_CURRENT`",
    ]
    return "\n".join(lines) + "\n"


def run_smoke_test() -> bool:
    snapshot = {
        "repository": "example/repo",
        "main_sha": "abc123",
        "main_paths": ["PRIORITY_QUEUE.md", ".github/workflows/base.yml"],
        "referenced_pull_requests": {"9": {"state": "closed", "merged": False}},
        "pull_requests": [
            {
                "number": 1,
                "title": "SMAG gate wire-up",
                "body": "- [x] **Z1**\nDepends on #9\n30-day rolling window blocks merge",
                "files": [".github/workflows/smag.yml", "tools/smag.py"],
                "file_details": [{"patch": "+ enforce 30-day rolling window before merge"}],
                "reviews": [],
                "mergeable_state": "dirty",
            },
            {
                "number": 2,
                "title": "SMAG gate enforcement",
                "body": "- [x] **Z2**",
                "files": [".github/workflows/smag.yml", "tools/smag.py"],
                "file_details": [],
                "reviews": [],
                "mergeable_state": "clean",
            },
        ],
    }
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource-state scheduling gate\n**State:** `GATING`\n"
    index = analyze(snapshot, pq)
    one = next(x for x in index["items"] if x["number"] == 1)
    assert one["guidance"]["action"] == "REEXAMINE"
    codes = {f["code"] for f in one["findings"]}
    assert "ACTIVE_GATE_REVIEW_REQUIRED" in codes
    assert "AUTHORITY_CLAIM_MISMATCH" in codes
    assert "CLOSED_UNMERGED_REFERENCE" in codes
    assert "COMPETING_IMPLEMENTATION" in codes
    assert "AGE_IS_NOT_STALENESS" in index["invariants"]
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--priority-queue", type=Path, default=ROOT / "PRIORITY_QUEUE.md")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)

    if args.smoke_test:
        print("PASS" if run_smoke_test() else "FAIL")
        return 0

    if not args.snapshot:
        parser.error("--snapshot is required unless --smoke-test is used")

    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    pq = args.priority_queue.read_text(encoding="utf-8", errors="replace") if args.priority_queue.exists() else ""
    index = analyze(snapshot, pq)
    payload = json.dumps(index, indent=2, sort_keys=True) + "\n"
    markdown = render_markdown(index)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
