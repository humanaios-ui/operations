#!/usr/bin/env python3
"""
repository_coordinator_v0_1.py — evidence-bounded repository coordination index.
Builder v1.7 compliant
HumanAIOS — REPOSITORY-COORDINATOR-02

Builds a read-only coordination view over live pull requests and canonical
repository constraints. It answers "what should the operator inspect next?"
without granting authority, changing queue state, closing PRs, or merging code.

Core invariants:
  OPEN_IS_NOT_RELEVANT
  RELEVANT_IS_NOT_WARRANTED
  MERGEABLE_IS_NOT_CURRENT
  AGE_IS_NOT_STALENESS
  GUIDANCE_REQUIRES_EVIDENCE
  SESSION_ISSUE_PRECEDES_IMPLEMENTATION
  ISSUE_CREATION_IS_NOT_ADMISSION
  ISSUE_IS_SESSION_GRAPH_NOT_EXECUTION
  ASSIGNMENT_IS_NOT_PR_ADMISSION
  DRAFT_IS_NOT_OPERATOR_QUEUE
  PREFLIGHT_IS_NOT_PR_VALIDATION
  AUTONOMOUS_PRODUCTION_CANNOT_OUTRUN_REVIEW_CAPACITY
  ONE_OBJECTIVE_SHOULD_NOT_CREATE_MULTIPLE_ACTIVE_IMPLEMENTATIONS
  ADMISSION_IS_NOT_MERGE_AUTHORITY

Inputs are an offline JSON snapshot collected by the GitHub workflow plus the
checked-out canonical PRIORITY_QUEUE.md. The tool does not call GitHub itself.

Trust boundary: the policy, this tool, and PRIORITY_QUEUE.md must be read from
the trusted base branch, not from a candidate PR checkout. A PR must not be
able to admit itself by editing the policy it is judged against.

Admission evidence is an explicit closing-keyword link ("Fixes #N") to an
admitted issue, or a grandfathered explicit PR number in the policy. An issue
is admitted either by the trusted default-branch policy or by the latest exact
admission command from a policy-authorized actor. Issue body text, labels,
assignment, and unauthorized comments cannot self-admit work. Maintenance
standing comes from the automated author identity, not from a self-assignable
label. Control-plane exemption applies only when every changed file is a
control-plane path.

Usage:
  python3 tools/repository_coordinator_v0_1.py --snapshot snapshot.json
  python3 tools/repository_coordinator_v0_1.py --snapshot snapshot.json \
      --output index.json --markdown index.md --policy REPOSITORY_COORDINATOR_POLICY.json
  python3 tools/repository_coordinator_v0_1.py --snapshot snapshot.json --gate 123
  python3 tools/repository_coordinator_v0_1.py --issue-snapshot issue.json
  python3 tools/repository_coordinator_v0_1.py --preflight-snapshot preflight.json
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
TOOL_VERSION = "0.3.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "REPOSITORY-COORDINATOR-02"
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
# Admission evidence must be an explicit closing-keyword link (GitHub linking
# semantics), not an incidental mention such as "unrelated to #378".
ADMISSION_LINK_RE = re.compile(
    r"\b(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s*:?\s*"
    r"(?:[\w.-]+/[\w.-]+)?#(\d{1,6})\b",
    re.I,
)
ACTIVE_GATE_RE = re.compile(
    r"^###\s+(Q-[A-Z0-9-]+).*?\n(?:.*\n){0,8}?\*\*State:\*\*\s*`?([A-Z_]+)`?",
    re.M,
)

DEFAULT_SESSION_SECTIONS = [
    "session identity",
    "objective",
    "scope",
    "readiness predicates",
    "acceptance criteria",
    "falsifiers",
    "decision log",
]

EMPTY_SECTION_VALUES = {
    "", "n/a", "na", "none", "tbd", "todo", "unknown", "_no response_",
}

ACTION_ORDER = {
    "CLOSE_PRESERVE": 0,
    "REEXAMINE": 1,
    "COMPARE_CONSOLIDATE": 2,
    "REBASE_RETEST": 3,
    "ADVANCE": 4,
}

LANE_ORDER = {
    "CAPACITY_CONTENTION": 0,
    "CONTROL_PLANE": 1,
    "ACTIVE": 2,
    "ADMISSION_REVIEW": 3,
    "WORKBENCH": 4,
    "MAINTENANCE": 5,
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
    if files & {
        "REGISTERED.md", "PRIORITY_QUEUE.md", "MOLT_STATE.md",
        "REPOSITORY_COORDINATOR_POLICY.json",
        ".github/dependabot.yml", ".github/copilot-instructions.md",
        ".github/CODEOWNERS",
    }:
        return "Z2"
    return "Z1"


def _labels(value: Any) -> set[str]:
    labels: set[str] = set()
    for raw in value or []:
        if isinstance(raw, dict):
            name = raw.get("name")
        else:
            name = raw
        if name:
            labels.add(str(name))
    return labels


def _normalized_heading(value: str) -> str:
    """Normalize a Markdown heading without weakening its semantic identity."""
    value = re.sub(r"[`*_]", "", value or "")
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value.rstrip(":")


def _markdown_sections(body: str) -> dict[str, str]:
    """Return issue sections from hand-written H2 or Issue Form H3 headings."""
    lines = (body or "").splitlines()
    level = 2 if any(re.match(r"^##\s+", line) for line in lines) else 3
    heading_re = re.compile(rf"^#{{{level}}}\s+(.+?)\s*$")
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = heading_re.match(line)
        if match:
            current = _normalized_heading(match.group(1))
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def _section_has_content(value: str) -> bool:
    """Reject empty issue-form placeholders while allowing structured Markdown."""
    stripped = re.sub(r"<!--.*?-->", "", value or "", flags=re.S).strip()
    if stripped.lower() in EMPTY_SECTION_VALUES:
        return False
    # Empty checkboxes and headings are structure, not an answer.
    stripped = re.sub(r"(?m)^\s*[-*]\s*\[\s*\]\s*.*$", "", stripped)
    stripped = re.sub(r"(?m)^#{1,6}\s+.*$", "", stripped).strip()
    return bool(stripped)


def _issue_command_decision(
    issue: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Resolve the latest authorized issue command; labels never grant standing."""
    cfg = policy.get("session_admission") or {}
    authorized = {str(x).lower() for x in cfg.get("authorized_actors") or []}
    commands = {
        str(command).strip(): str(state).upper()
        for state, command in (cfg.get("commands") or {}).items()
        if str(command).strip()
    }
    candidates: list[tuple[str, int, str, str, str]] = []
    for comment in issue.get("comments") or []:
        user = comment.get("user") or {}
        actor = str(
            user.get("login") if isinstance(user, dict) else user
            or comment.get("author")
            or ""
        )
        if actor.lower() not in authorized:
            continue
        body = str(comment.get("body") or "").strip()
        first_line = body.splitlines()[0].strip() if body else ""
        state = commands.get(first_line)
        if not state:
            continue
        created = str(comment.get("created_at") or comment.get("updated_at") or "")
        comment_id = int(comment.get("id") or 0)
        candidates.append((created, comment_id, state, actor, first_line))

    if not candidates:
        return {
            "state": "ADMISSION_REVIEW",
            "source": None,
            "actor": None,
            "comment_id": None,
            "evidence": "no authorized admission command is present",
        }

    created, comment_id, state, actor, command = max(candidates)
    return {
        "state": state,
        "source": "AUTHORIZED_ISSUE_COMMAND",
        "actor": actor,
        "comment_id": comment_id,
        "created_at": created,
        "command": command,
        "evidence": f"{actor} issued {command} in issue comment {comment_id}",
    }


def evaluate_session_issue(
    issue: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Validate the issue as a session graph and report its admission state."""
    cfg = policy.get("session_admission") or {}
    required = [
        _normalized_heading(str(x))
        for x in cfg.get("required_sections") or DEFAULT_SESSION_SECTIONS
    ]
    sections = _markdown_sections(str(issue.get("body") or ""))
    missing = [name for name in required if name not in sections]
    empty = [
        name for name in required
        if name in sections and not _section_has_content(sections[name])
    ]
    structure_gate = "PASS" if not missing and not empty else "FAIL"

    number = int(issue.get("number") or issue.get("issue_number") or 0)
    static_issues = {
        int(x) for x in (policy.get("admission") or {}).get("issue_numbers") or []
    }
    if number and number in static_issues:
        decision = {
            "state": "ADMITTED",
            "source": "DEFAULT_BRANCH_POLICY",
            "actor": "Z2",
            "comment_id": None,
            "evidence": f"default-branch policy explicitly admits issue #{number}",
        }
    else:
        decision = _issue_command_decision(issue, policy)

    preflight_eligible = (
        structure_gate == "PASS"
        and decision["state"] == "ADMITTED"
        and str(issue.get("state") or "open").lower() == "open"
    )
    return {
        "schema_version": "0.1",
        "authority_effect": "ADMISSION_ROUTING_ONLY",
        "issue_number": number,
        "title": str(issue.get("title") or ""),
        "issue_state": str(issue.get("state") or "open").lower(),
        "structure_gate": structure_gate,
        "missing_sections": missing,
        "empty_sections": empty,
        "admission": decision,
        "preflight_eligible": preflight_eligible,
        "invariants": [
            "ISSUE_CREATION_IS_NOT_ADMISSION",
            "ISSUE_IS_SESSION_GRAPH_NOT_EXECUTION",
            "ADMISSION_IS_NOT_MERGE_AUTHORITY",
        ],
    }


def evaluate_preflight(
    snapshot: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed binding check for an exact branch commit before PR creation."""
    issue = snapshot.get("issue") or {}
    branch = snapshot.get("branch") or {}
    issue_result = evaluate_session_issue(issue, policy)
    number = int(issue_result.get("issue_number") or 0)
    cfg = policy.get("session_admission") or {}
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, str] = {}

    def record(name: str, ok: bool, failure: str) -> None:
        checks[name] = "PASS" if ok else "FAIL"
        if not ok:
            errors.append(failure)

    record(
        "session_graph_structure",
        issue_result["structure_gate"] == "PASS",
        "session issue is missing required, substantive sections",
    )
    record(
        "admission_standing",
        issue_result["admission"]["state"] == "ADMITTED",
        "session issue has no current authorized admission decision",
    )
    record(
        "issue_open",
        issue_result["issue_state"] == "open",
        "session issue is not open",
    )

    branch_name = str(branch.get("name") or "")
    branch_pattern = str(
        cfg.get("branch_pattern")
        or r"^(?:[^/]+/)?issue-(?P<issue_number>[0-9]+)(?:[-/].*)?$"
    )
    branch_match = re.fullmatch(branch_pattern, branch_name)
    bound_number = int(branch_match.group("issue_number")) if branch_match else 0
    record(
        "branch_issue_binding",
        bool(branch_match) and bound_number == number,
        f"branch `{branch_name}` is not bound to issue #{number}",
    )

    head_sha = str(branch.get("head_sha") or "")
    base_sha = str(branch.get("base_sha") or "")
    record(
        "head_identity",
        bool(re.fullmatch(r"[0-9a-f]{40}", head_sha)),
        "branch head SHA is missing or malformed",
    )
    record(
        "base_identity",
        bool(re.fullmatch(r"[0-9a-f]{40}", base_sha)),
        "base SHA is missing or malformed",
    )

    first_message = str(branch.get("first_commit_message") or "")
    ref_pattern = str(
        cfg.get("first_commit_reference_pattern")
        or r"(?i)^(?:refs?|relates-to):[ ]*#(?P<issue_number>[0-9]+)$"
    )
    ref_match = re.search(ref_pattern, first_message, flags=re.M)
    ref_number = int(ref_match.group("issue_number")) if ref_match else 0
    record(
        "first_commit_issue_reference",
        bool(ref_match) and ref_number == number,
        f"first implementation commit must contain `Refs: #{number}`",
    )

    files = [str(x) for x in branch.get("changed_files") or []]
    record(
        "implementation_delta",
        bool(files) and bool(branch.get("files_complete", True)),
        "branch comparison has no complete implementation delta",
    )
    open_prs = [int(x) for x in branch.get("open_pull_requests") or []]
    if open_prs:
        warnings.append(
            "branch already has open PR(s) "
            + ", ".join(f"#{x}" for x in open_prs)
            + "; this is a revalidation, not a pre-PR run"
        )

    return {
        "schema_version": "0.1",
        "authority_effect": "PREFLIGHT_EVIDENCE_ONLY",
        "gate": "PASS" if not errors else "FAIL",
        "issue_number": number,
        "branch": branch_name,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "changed_files": files,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "issue": issue_result,
        "invariants": [
            "SESSION_ISSUE_PRECEDES_IMPLEMENTATION",
            "PREFLIGHT_IS_NOT_PR_VALIDATION",
            "ADMISSION_IS_NOT_MERGE_AUTHORITY",
        ],
    }


def _maintenance(pr: dict[str, Any], policy: dict[str, Any]) -> bool:
    """Maintenance standing is granted by the automated author identity only.

    Labels are self-assignable by anyone with triage access, so a label alone
    must not move a PR out of admission review. Labels still refine cohorts.
    """
    cfg = policy.get("maintenance") or {}
    authors = set(cfg.get("authors") or [])
    author = str(pr.get("author") or "")
    return author in authors


def _maintenance_cohort(pr: dict[str, Any]) -> str:
    title = (pr.get("title") or "").lower()
    files = pr.get("files") or []
    if "actions/" in title or any(p.startswith(".github/workflows/") for p in files):
        return "github-actions"
    if "docker" in title or any("docker" in p.lower() for p in files):
        return "docker"
    if "depend" in title or any(
        p.endswith(("requirements.txt", "pyproject.toml", "poetry.lock"))
        for p in files
    ):
        return "python-dependencies"
    return "maintenance-other"


def _control_plane(pr: dict[str, Any], policy: dict[str, Any]) -> bool:
    """A PR is control-plane only when *every* changed file is a control path.

    Touching one control-plane file alongside feature work must not exempt the
    feature work from admission; that would make a whitespace edit to
    CODEOWNERS a universal admission bypass.
    """
    paths = set((policy.get("control_plane") or {}).get("paths") or [])
    files = set(pr.get("files") or [])
    return bool(files) and bool(pr.get("files_complete", True)) and files <= paths


def _zero_diff(pr: dict[str, Any]) -> bool:
    return bool(pr.get("files_complete", True)) and not (pr.get("files") or [])


def _admission_evidence(
    pr: dict[str, Any],
    policy: dict[str, Any],
    referenced_items: dict[str, dict[str, Any]],
) -> tuple[bool, list[str], list[int]]:
    cfg = policy.get("admission") or {}
    admitted_prs = {int(x) for x in cfg.get("pull_request_numbers") or []}
    admitted_issues = {int(x) for x in cfg.get("issue_numbers") or []}
    evidence: list[str] = []
    objectives: list[int] = []

    number = int(pr.get("number") or 0)
    if number in admitted_prs:
        evidence.append(f"policy explicitly admits PR #{number}")
        objectives.append(-number)

    for raw in ADMISSION_LINK_RE.findall(pr.get("body") or ""):
        ref = int(raw)
        item = referenced_items.get(str(ref)) or referenced_items.get(ref)
        if not item or item.get("is_pull_request"):
            continue
        admitted_by_policy = ref in admitted_issues
        session_result = evaluate_session_issue(item, policy)
        admitted_by_command = (
            session_result["structure_gate"] == "PASS"
            and session_result["admission"]["state"] == "ADMITTED"
            and session_result["issue_state"] == "open"
        )
        if (admitted_by_policy or admitted_by_command) and ref not in objectives:
            evidence.append(f"policy admits linked issue #{ref}")
            if admitted_by_command and not admitted_by_policy:
                evidence[-1] = session_result["admission"]["evidence"]
            objectives.append(ref)

    linked_objectives = [x for x in objectives if x > 0]
    if len(linked_objectives) > 1:
        evidence.append(
            "multiple admitted session issues are linked; exactly one objective is required"
        )
        return False, evidence, objectives

    return bool(evidence), evidence, objectives


def _base_lane(
    pr: dict[str, Any],
    *,
    policy: dict[str, Any],
    referenced_items: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    admitted, evidence, objectives = _admission_evidence(pr, policy, referenced_items)
    maintenance = _maintenance(pr, policy)
    control_plane = _control_plane(pr, policy)
    draft = bool(pr.get("draft"))

    if maintenance:
        lane = "MAINTENANCE"
    elif control_plane:
        lane = "CONTROL_PLANE"
    elif draft:
        lane = "WORKBENCH"
    elif admitted:
        lane = "ACTIVE"
    else:
        lane = "ADMISSION_REVIEW"

    return lane, {
        "admitted": admitted,
        "evidence": evidence,
        "objectives": objectives,
        "maintenance": maintenance,
        "control_plane": control_plane,
        "draft": draft,
        "cohort": _maintenance_cohort(pr) if maintenance else None,
    }


def _missing_refs(body: str, main_paths: set[str], own_files: set[str]) -> list[str]:
    refs = set(PATH_REF_RE.findall(body or ""))
    known = main_paths | own_files

    def exists(ref: str) -> bool:
        if ref in known:
            return True
        prefix = ref.rstrip("/") + "/"
        return any(path.startswith(prefix) for path in known)

    return sorted(p for p in refs if not exists(p))


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
    """Detect local temporal-control coupling, not unrelated terms far apart.

    A prior whole-document boolean cross-match could combine an external
    opportunity date in one section with an unrelated word such as "workflow"
    elsewhere and falsely classify the PR as internal scheduling logic.
    """
    body = pr.get("body") or ""
    control_paths = {
        "PRIORITY_QUEUE.md", "MOLT_STATE.md", "constants.json",
        "RESOURCE_UNITS.yaml", "CANDIDATE_BLOCK_TEMPLATE.md",
        "INTENT_GRAPH.yaml", "TEMPORAL_DISSOLUTION_POLICY.md",
    }

    evidence_parts = [body]
    for f in pr.get("file_details") or []:
        path = str(f.get("filename") or f.get("path") or "")
        if path.startswith(".github/workflows/") or path in control_paths:
            patch = str(f.get("patch") or "")
            added = "\n".join(
                line[1:] for line in patch.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            )
            evidence_parts.append(added)

    for text in evidence_parts:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not TIME_CONTROL_TERMS.search(line):
                continue
            local = "\n".join(lines[max(0, i - 1): min(len(lines), i + 2)])
            if CONTROL_TERMS.search(local):
                return True
    return False


def classify(
    pr: dict[str, Any],
    *,
    competition: dict[int, list[int]],
    main_paths: set[str],
    referenced_prs: dict[str, dict[str, Any]],
    referenced_items: dict[str, dict[str, Any]],
    active_gates: list[str],
    policy: dict[str, Any],
    capacity_contention: bool,
    duplicate_objectives: dict[int, list[int]] | None = None,
) -> dict[str, Any]:
    number = int(pr["number"])
    body = pr.get("body") or ""
    files = set(pr.get("files") or [])
    findings: list[Finding] = []

    base_lane, admission = _base_lane(
        pr,
        policy=policy,
        referenced_items=referenced_items,
    )
    lane = "CAPACITY_CONTENTION" if capacity_contention and base_lane == "ACTIVE" else base_lane

    if lane == "ADMISSION_REVIEW":
        findings.append(Finding(
            "ADMISSION_REQUIRED", "MEDIUM",
            "No repository-coordinator admission record covers this non-maintenance ready PR."
        ))
    elif lane == "CAPACITY_CONTENTION":
        findings.append(Finding(
            "CAPACITY_BACKPRESSURE", "HIGH",
            "Admitted ready work exceeds the active operator-queue capacity; coordinator refuses to select winners."
        ))

    duplicates = sorted(
        n for n in (duplicate_objectives or {}).get(number) or [] if n != number
    )
    if duplicates and base_lane == "ACTIVE":
        findings.append(Finding(
            "DUPLICATE_ACTIVE_IMPLEMENTATION", "HIGH",
            "Another ready PR claims the same admitted objective: "
            + ", ".join(f"#{n}" for n in duplicates)
            + "; coordinator refuses to select a winner."
        ))

    zero_diff = _zero_diff(pr)
    if zero_diff:
        findings.append(Finding(
            "ZERO_DIFF", "HIGH",
            "GitHub reports no changed files; there is no remaining merge delta."
        ))

    missing = _missing_refs(body, main_paths, files)
    for ref_path in missing[:12]:
        findings.append(Finding(
            "MISSING_REFERENCED_ARTIFACT", "HIGH",
            f"PR body references `{ref_path}`, which is absent from current main and this PR's own changed files."
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
    routing_codes = {"CAPACITY_BACKPRESSURE", "DUPLICATE_ACTIVE_IMPLEMENTATION"}
    if zero_diff:
        action = "CLOSE_PRESERVE"
        next_action = "Preserve the PR as evidence/history; do not treat it as an active merge unit."
    elif high_codes - routing_codes:
        action = "REEXAMINE"
        next_action = "Resolve the listed warrant/evidence/authority conflicts before investing in merge repair."
    elif competitors or duplicates:
        action = "COMPARE_CONSOLIDATE"
        next_action = "Compare the overlapping implementations, preserve unique contributions, and choose or extract one merge unit."
    elif mergeable_state in {"dirty", "behind"}:
        action = "REBASE_RETEST"
        next_action = "Refresh against current main and rerun the relevant test suite."
    else:
        action = "ADVANCE"
        next_action = "Proceed to ordinary review/testing; no coordinator-level technical blocker was detected."

    objective = "HISTORICAL" if zero_diff else "LIVE"

    state_alignment = "CURRENT"
    if high_codes - routing_codes:
        state_alignment = "REVALIDATION_REQUIRED"
    elif mergeable_state in {"dirty", "behind"}:
        state_alignment = "DRIFTED"

    evidence_status = "CURRENT"
    if {"MISSING_REFERENCED_ARTIFACT", "CLOSED_UNMERGED_REFERENCE", "CHANGES_REQUESTED"} & high_codes:
        evidence_status = "STALE_OR_CONTESTED"

    dependency_status = "SATISFIED"
    if dead_refs or missing:
        dependency_status = "INVALIDATED_OR_MISSING"
    elif competitors or duplicates:
        dependency_status = "COMPETING"

    admission_gate = "PASS"
    admission_reason = "lane does not require additional admission evidence"
    if lane == "ADMISSION_REVIEW":
        admission_gate = "FAIL"
        admission_reason = "ready non-maintenance work has no explicit admission record"
    elif lane == "CAPACITY_CONTENTION":
        admission_gate = "FAIL"
        admission_reason = "active admitted work exceeds configured operator capacity"
    elif duplicates and lane == "ACTIVE":
        admission_gate = "FAIL"
        admission_reason = "multiple ready implementations claim one admitted objective; operator must consolidate"
    elif lane == "WORKBENCH":
        admission_reason = "draft work is isolated from the operator queue"
    elif lane == "MAINTENANCE":
        admission_reason = "maintenance is routed to a cohort lane"
    elif lane == "CONTROL_PLANE":
        admission_reason = "coordinator control-plane changes use ordinary Z2 review rather than recursive admission"
    elif lane == "ACTIVE":
        admission_reason = "explicit admission evidence found and capacity is available"

    return {
        "number": number,
        "title": pr.get("title") or "",
        "url": pr.get("html_url") or pr.get("url"),
        "author": pr.get("author"),
        "draft": bool(pr.get("draft")),
        "lane": lane,
        "objective": objective,
        "state_alignment": state_alignment,
        "admission": {
            **admission,
            "gate": admission_gate,
            "gate_reason": admission_reason,
        },
        "dependency": {
            "status": dependency_status,
            "competing_prs": competitors,
            "duplicate_objective_prs": duplicates,
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
            "files_complete": bool(pr.get("files_complete", True)),
            "mergeable_state": mergeable_state or "unknown",
        },
        "guidance": {
            "action": action,
            "next_action": next_action,
        },
        "findings": [asdict(f) for f in findings],
    }


def analyze(
    snapshot: dict[str, Any],
    priority_queue_text: str,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or {
        "capacity": {"active_operator_queue": 4},
        "admission": {"issue_numbers": [], "pull_request_numbers": []},
        "maintenance": {"authors": ["dependabot[bot]"], "labels": ["dependencies"]},
        "control_plane": {"paths": []},
    }
    prs = list(snapshot.get("pull_requests") or [])
    competitions = _competition(prs)
    main_paths = set(snapshot.get("main_paths") or [])
    referenced_prs = snapshot.get("referenced_pull_requests") or {}
    referenced_items = snapshot.get("referenced_items") or {}
    gates = _active_gates(priority_queue_text)

    base_lanes = {
        int(pr["number"]): _base_lane(
            pr,
            policy=policy,
            referenced_items=referenced_items,
        )
        for pr in prs
    }
    # Zero-diff PRs are historical, not merge units; they must not consume
    # operator capacity or trigger contention.
    ready_admitted = [
        n for n, (lane, _) in base_lanes.items()
        if lane == "ACTIVE" and not _zero_diff(next(p for p in prs if int(p["number"]) == n))
    ]
    active_limit = int((policy.get("capacity") or {}).get("active_operator_queue") or 0)
    capacity_contention = active_limit >= 0 and len(ready_admitted) > active_limit

    # ONE_OBJECTIVE_SHOULD_NOT_CREATE_MULTIPLE_ACTIVE_IMPLEMENTATIONS:
    # two ready PRs claiming the same admitted objective are both held.
    by_objective: dict[int, list[int]] = {}
    for n in ready_admitted:
        for objective in base_lanes[n][1].get("objectives") or []:
            by_objective.setdefault(int(objective), []).append(n)
    duplicate_objectives: dict[int, list[int]] = {}
    for owners in by_objective.values():
        if len(owners) > 1:
            for n in owners:
                duplicate_objectives.setdefault(n, [])
                duplicate_objectives[n] = sorted(set(duplicate_objectives[n]) | set(owners))

    items = [
        classify(
            pr,
            competition=competitions,
            main_paths=main_paths,
            referenced_prs=referenced_prs,
            referenced_items=referenced_items,
            active_gates=gates,
            policy=policy,
            capacity_contention=capacity_contention,
            duplicate_objectives=duplicate_objectives,
        )
        for pr in prs
    ]
    items.sort(
        key=lambda x: (
            LANE_ORDER.get(x["lane"], 99),
            ACTION_ORDER[x["guidance"]["action"]],
            x["number"],
        )
    )

    action_counts: dict[str, int] = {}
    lane_counts: dict[str, int] = {}
    cohorts: dict[str, list[int]] = {}
    for item in items:
        action = item["guidance"]["action"]
        action_counts[action] = action_counts.get(action, 0) + 1
        lane = item["lane"]
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        cohort = item.get("admission", {}).get("cohort")
        if lane == "MAINTENANCE" and cohort:
            cohorts.setdefault(str(cohort), []).append(item["number"])

    return {
        "schema_version": "0.3",
        "advisory_only": False,
        "authority_effect": "ADMISSION_ROUTING_ONLY",
        "repository": snapshot.get("repository"),
        "main_sha": snapshot.get("main_sha"),
        "active_canonical_gates": gates,
        "capacity": {
            "active_operator_queue_limit": active_limit,
            "admitted_ready_count": len(ready_admitted),
            "contention": capacity_contention,
            "duplicate_objective_prs": sorted(duplicate_objectives),
        },
        "invariants": [
            "OPEN_IS_NOT_RELEVANT",
            "RELEVANT_IS_NOT_WARRANTED",
            "MERGEABLE_IS_NOT_CURRENT",
            "AGE_IS_NOT_STALENESS",
            "GUIDANCE_REQUIRES_EVIDENCE",
            "SESSION_ISSUE_PRECEDES_IMPLEMENTATION",
            "ISSUE_CREATION_IS_NOT_ADMISSION",
            "ISSUE_IS_SESSION_GRAPH_NOT_EXECUTION",
            "ASSIGNMENT_IS_NOT_PR_ADMISSION",
            "DRAFT_IS_NOT_OPERATOR_QUEUE",
            "PREFLIGHT_IS_NOT_PR_VALIDATION",
            "AUTONOMOUS_PRODUCTION_CANNOT_OUTRUN_REVIEW_CAPACITY",
            "ONE_OBJECTIVE_SHOULD_NOT_CREATE_MULTIPLE_ACTIVE_IMPLEMENTATIONS",
            "ADMISSION_IS_NOT_MERGE_AUTHORITY",
        ],
        "counts": {
            "actions": action_counts,
            "lanes": lane_counts,
        },
        "maintenance_cohorts": {
            name: sorted(numbers) for name, numbers in sorted(cohorts.items())
        },
        "items": items,
    }


def _row(item: dict[str, Any]) -> str:
    findings = item.get("findings") or []
    why = "; ".join(f["evidence"] for f in findings[:2]) or item["admission"]["gate_reason"]
    why = why.replace("|", "\\|").replace("\n", " ")
    action = item["guidance"]["action"]
    return (
        f"| [#{item['number']}]({item.get('url') or '#'}) {item['title']} | "
        f"{action} | {why} |"
    )


def render_markdown(index: dict[str, Any]) -> str:
    items = index.get("items") or []
    lanes = (index.get("counts") or {}).get("lanes") or {}
    capacity = index.get("capacity") or {}
    active_limit = capacity.get("active_operator_queue_limit", 0)
    # The capacity numerator is what analyze() actually counts against the
    # limit; control-plane attention is reported separately.
    operator_count = capacity.get("admitted_ready_count", lanes.get("ACTIVE", 0))

    lines = [
        "<!-- repository-coordinator -->",
        "## Repository Coordinator — admission + backpressure index",
        "",
        f"Main: `{str(index.get('main_sha') or 'unknown')[:12]}` · "
        f"Repository PRs: **{len(items)}** · "
        f"Operator queue: **{operator_count}/{active_limit}** · "
        f"Control plane: **{lanes.get('CONTROL_PLANE', 0)}**",
        "",
        "> Repository work may exist without entering the operator queue. "
        "Admission controls working-set standing only; it is not merge or governance authority.",
        "",
        "| Lane | Count | Meaning |",
        "|---|---:|---|",
        f"| ACTIVE | {lanes.get('ACTIVE', 0)} | Explicitly admitted, ready work within capacity |",
        f"| CONTROL_PLANE | {lanes.get('CONTROL_PLANE', 0)} | Coordinator policy/control changes requiring ordinary review |",
        f"| ADMISSION_REVIEW | {lanes.get('ADMISSION_REVIEW', 0)} | Ready work not yet admitted |",
        f"| WORKBENCH | {lanes.get('WORKBENCH', 0)} | Draft/agent work; not operator queue |",
        f"| MAINTENANCE | {lanes.get('MAINTENANCE', 0)} | Routine maintenance routed by cohort |",
        f"| CAPACITY_CONTENTION | {lanes.get('CAPACITY_CONTENTION', 0)} | Admitted work exceeds capacity; no autonomous winner selection |",
        "",
    ]

    gates = index.get("active_canonical_gates") or []
    if gates:
        lines.append("Active canonical gate(s): " + ", ".join(f"`{g}`" for g in gates))
        lines.append("")

    if capacity.get("contention"):
        lines += [
            "### Backpressure engaged",
            "",
            "Admitted ready work exceeds configured capacity. The coordinator refuses to choose which objective should win; operator selection or de-admission is required.",
            "",
        ]

    if capacity.get("duplicate_objective_prs"):
        lines += [
            "### Duplicate implementations",
            "",
            "More than one ready PR claims the same admitted objective: "
            + ", ".join(f"#{n}" for n in capacity["duplicate_objective_prs"])
            + ". All are held pending operator consolidation.",
            "",
        ]

    sections = [
        (["CAPACITY_CONTENTION"], "Capacity contention"),
        (["CONTROL_PLANE", "ACTIVE"], "Active operator queue"),
        (["ADMISSION_REVIEW"], "Admission review"),
        (["WORKBENCH"], "Workbench — visible, not operator queue"),
    ]
    for lane_names, heading in sections:
        rows = [item for item in items if item["lane"] in lane_names]
        if not rows:
            continue
        lines += [f"### {heading}", "", "| PR | Technical guidance | Evidence / routing reason |", "|---|---|---|"]
        lines += [_row(item) for item in rows]
        lines.append("")

    maintenance = [item for item in items if item["lane"] == "MAINTENANCE"]
    if maintenance:
        lines += ["### Maintenance cohorts", "", "| Cohort | Count | PRs |", "|---|---:|---|"]
        by_cohort: dict[str, list[dict[str, Any]]] = {}
        for item in maintenance:
            cohort = str(item["admission"].get("cohort") or "maintenance-other")
            by_cohort.setdefault(cohort, []).append(item)
        for cohort, rows in sorted(by_cohort.items()):
            refs = ", ".join(f"#{x['number']}" for x in rows)
            lines.append(f"| {cohort} | {len(rows)} | {refs} |")
        lines.append("")

    lines += [
        "---",
        "`SESSION_ISSUE_PRECEDES_IMPLEMENTATION · ISSUE_CREATION_IS_NOT_ADMISSION · "
        "PREFLIGHT_IS_NOT_PR_VALIDATION · ADMISSION_IS_NOT_MERGE_AUTHORITY`",
    ]
    return "\n".join(lines) + "\n"


def gate_decision(index: dict[str, Any], number: int) -> dict[str, Any]:
    """Fail-closed admission decision for one PR from a computed index.

    Returns {"gate": "PASS"|"FAIL", "lane": ..., "reason": ...}. A PR that is
    absent from the index is a FAIL: the gate does not pass on missing evidence.
    """
    for item in index.get("items") or []:
        if int(item.get("number") or 0) == int(number):
            admission = item.get("admission") or {}
            gate = "PASS" if admission.get("gate") == "PASS" else "FAIL"
            return {
                "number": int(number),
                "gate": gate,
                "lane": item.get("lane"),
                "reason": admission.get("gate_reason") or "no admission reason recorded",
                "evidence": admission.get("evidence") or [],
                "capacity": index.get("capacity") or {},
            }
    return {
        "number": int(number),
        "gate": "FAIL",
        "lane": None,
        "reason": "target PR is absent from the repository snapshot; refusing to pass on missing evidence",
        "evidence": [],
        "capacity": index.get("capacity") or {},
    }


def run_smoke_test() -> bool:
    snapshot = {
        "repository": "example/repo",
        "main_sha": "abc123",
        "main_paths": ["PRIORITY_QUEUE.md", ".github/workflows/base.yml"],
        "referenced_pull_requests": {"9": {"state": "closed", "merged": False}},
        "referenced_items": {
            "10": {
                "state": "open",
                "is_pull_request": False,
                "labels": [],
                "title": "Admitted objective",
            }
        },
        "pull_requests": [
            {
                "number": 1,
                "title": "SMAG gate wire-up",
                "body": "- [x] **Z1**\nDepends on #9\n30-day rolling window blocks merge",
                "files": [".github/workflows/smag.yml", "tools/smag.py"],
                "file_details": [{"filename": ".github/workflows/smag.yml", "patch": "+ enforce 30-day rolling window before merge"}],
                "reviews": [],
                "mergeable_state": "dirty",
                "author": "builder",
                "draft": False,
                "labels": [],
            },
            {
                "number": 2,
                "title": "Admitted implementation",
                "body": "Fixes #10",
                "files": ["src/work.py"],
                "file_details": [],
                "reviews": [],
                "mergeable_state": "clean",
                "author": "builder",
                "draft": False,
                "labels": [],
            },
        ],
    }
    policy = {
        "capacity": {"active_operator_queue": 4},
        "admission": {"issue_numbers": [10], "pull_request_numbers": [1]},
        "session_admission": {
            "required_sections": DEFAULT_SESSION_SECTIONS,
            "authorized_actors": ["operator"],
            "commands": {
                "ADMITTED": "/admit",
                "DEFERRED": "/defer",
                "REJECTED": "/reject",
            },
            "branch_pattern": r"^(?:[^/]+/)?issue-(?P<issue_number>[0-9]+)(?:[-/].*)?$",
            "first_commit_reference_pattern": r"(?i)^(?:refs?|relates-to):[ ]*#(?P<issue_number>[0-9]+)$",
        },
        "maintenance": {"authors": ["dependabot[bot]"], "labels": ["dependencies"]},
        "control_plane": {"paths": ["REPOSITORY_COORDINATOR_POLICY.json"]},
    }
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource-state scheduling gate\n**State:** `GATING`\n"
    index = analyze(snapshot, pq, policy)
    one = next(x for x in index["items"] if x["number"] == 1)
    two = next(x for x in index["items"] if x["number"] == 2)
    assert one["guidance"]["action"] == "REEXAMINE"
    assert two["lane"] == "ACTIVE"
    assert two["admission"]["gate"] == "PASS"
    assert gate_decision(index, 2)["gate"] == "PASS"
    assert gate_decision(index, 404)["gate"] == "FAIL"
    codes = {f["code"] for f in one["findings"]}
    assert "ACTIVE_GATE_REVIEW_REQUIRED" in codes
    assert "AUTHORITY_CLAIM_MISMATCH" in codes
    assert "CLOSED_UNMERGED_REFERENCE" in codes
    assert "AGE_IS_NOT_STALENESS" in index["invariants"]
    assert "ASSIGNMENT_IS_NOT_PR_ADMISSION" in index["invariants"]

    section_text = "\n\n".join(
        f"## {name.title()}\nSubstantive {name}." for name in DEFAULT_SESSION_SECTIONS
    )
    session_issue = {
        "number": 11,
        "title": "Session objective",
        "body": section_text,
        "state": "open",
        "comments": [{
            "id": 7,
            "body": "/admit\n\nAuthorized for the working set.",
            "created_at": "2026-09-30T00:00:00Z",
            "user": {"login": "operator"},
        }],
    }
    assert evaluate_session_issue(session_issue, policy)["preflight_eligible"] is True
    preflight = evaluate_preflight({
        "issue": session_issue,
        "branch": {
            "name": "codex/issue-11-session-objective",
            "head_sha": "b" * 40,
            "base_sha": "a" * 40,
            "first_commit_message": "Implement objective\n\nRefs: #11",
            "changed_files": ["src/work.py"],
            "files_complete": True,
            "open_pull_requests": [],
        },
    }, policy)
    assert preflight["gate"] == "PASS"
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument(
        "--issue-snapshot", type=Path,
        help="Validate one issue as a session graph and report admission standing.",
    )
    parser.add_argument(
        "--preflight-snapshot", type=Path,
        help="Validate issue/branch/first-commit binding before PR creation.",
    )
    parser.add_argument("--priority-queue", type=Path, default=ROOT / "PRIORITY_QUEUE.md")
    parser.add_argument("--policy", type=Path, default=ROOT / "REPOSITORY_COORDINATOR_POLICY.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument(
        "--gate", type=int, metavar="PR_NUMBER",
        help="Emit the fail-closed admission decision for one PR; exit 1 unless it is PASS.",
    )
    args = parser.parse_args(argv)

    if args.smoke_test:
        print("PASS" if run_smoke_test() else "FAIL")
        return 0

    selected = sum(bool(x) for x in (
        args.snapshot, args.issue_snapshot, args.preflight_snapshot,
    ))
    if selected != 1:
        parser.error(
            "select exactly one of --snapshot, --issue-snapshot, or --preflight-snapshot"
        )

    if not args.policy.exists():
        print(f"gate=FAIL reason=policy file missing: {args.policy}")
        return 1

    policy = json.loads(args.policy.read_text(encoding="utf-8"))

    if args.issue_snapshot:
        raw = json.loads(args.issue_snapshot.read_text(encoding="utf-8"))
        issue = raw.get("issue") or raw
        result = evaluate_session_issue(issue, policy)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        # Admission review is a normal pending state. Only a malformed session
        # graph makes issue-intake validation fail.
        return 0 if result["structure_gate"] == "PASS" else 1

    if args.preflight_snapshot:
        raw = json.loads(args.preflight_snapshot.read_text(encoding="utf-8"))
        result = evaluate_preflight(raw, policy)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0 if result["gate"] == "PASS" else 1

    assert args.snapshot is not None
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    pq = args.priority_queue.read_text(encoding="utf-8", errors="replace") if args.priority_queue.exists() else ""
    index = analyze(snapshot, pq, policy)

    if args.gate is not None:
        decision = gate_decision(index, args.gate)
        print(json.dumps(decision, indent=2, sort_keys=True))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Repository admission/backpressure gate: {decision['gate']} ({decision['lane']}) — {decision['reason']}")
        return 0 if decision["gate"] == "PASS" else 1

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
