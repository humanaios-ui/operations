"""
research_graph_view.py
HumanAIOS research-graph living view, Phase 1 (tracking issue #874, hub #799).
Builder v1.7 compliant.

Read-only generator. It reads GitHub state through GET requests, builds a
descriptive view of open and recently closed PRs, and writes exactly two files
under research-graph/: graph.json and GRAPH.md.

Authority: none. Every output carries authority_effect NONE, can_admit false,
can_merge false. The view names missing conditions; it issues no commands,
approvals, or admission state. PR titles are not copied into any output.

Independence: this module does NOT import or reuse the admission gate's trusted
code (tools/repository_coordinator_*.py). Reason codes are re-implemented here.
The policy file is read as data only, for the list of authorized actors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "research_graph_view"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "reporting_tool"
TOOL_SESSION = "research-graph-phase1"
TOOL_ZONE = 1

SCHEMA = "humanaios.research_graph.view.v0.1"
OUT_DIR_NAME = "research-graph"
PR_CAP = 200
ISSUE_CAP = 100
CLOSED_PR_SAMPLE = 30
FILES_CAP = 3000
REVIEWS_CAP = 1000
RUNS_CAP = 1000

# Required workflow runs, by workflow `name:` as GitHub reports it.
# Path filters are NOT hard-coded here: they are read from the workflow file.
REQUIRED_RUN_NAMES = (
    "security-gates",
    "temporal-dissolution-gate",
    "repository-coordinator",
    "ci-predict-pin",
    "quality-baseline",
    "tool-manifest",
)

# Quantifiers are bounded: owner and repository name limits from GitHub, and a
# short cap on whitespace between keyword, colon and reference.
_REPO_QUALIFIER = r"(?:(?P<repo>[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}))?"
CLOSING_RE = re.compile(
    r"\b(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)"
    r"\s{0,8}:?\s{0,8}" + _REPO_QUALIFIER + r"#(?P<num>\d{1,6})\b",
    re.IGNORECASE,
)
# The lookbehind keeps a reference from starting inside a word or path segment.
REF_RE = re.compile(r"(?<![A-Za-z0-9_/.-])" + _REPO_QUALIFIER + r"#(?P<num>\d{1,6})\b")
# Accepts the plain form ("state: ADMISSION_REQUESTED") and the Markdown form
# ("**state:** `ADMISSION_REQUESTED`") used in issue bodies.
ADMISSION_RE = re.compile(r"\bstate\W{0,8}?`?ADMISSION_REQUESTED`?", re.IGNORECASE)
RELEVANT_REVIEW_STATES = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")

REASON_DRAFT = "DRAFT"
REASON_INCOMPLETE = "SNAPSHOT_INCOMPLETE_FOR_PR"
REASON_NO_ADMISSION_LINK = "NO_ADMISSION_LINK"
REASON_LATEST_REVIEW_NOT_APPROVED = "LATEST_REVIEW_NOT_APPROVED"
REASON_HEAD_CHANGED = "HEAD_CHANGED_SINCE_EVALUATION"
REASON_RUN_MISSING = "REQUIRED_RUN_MISSING:"
REASON_RUN_NOT_GREEN = "REQUIRED_RUN_NOT_GREEN:"
REASON_RUN_UNDEFINED = "REQUIRED_WORKFLOW_UNDEFINED:"
CONDITIONAL = "CONDITIONAL:"

# Every reason code this module can emit. Tests pin this list.
REASON_CODES = (
    REASON_DRAFT,
    REASON_INCOMPLETE,
    REASON_NO_ADMISSION_LINK,
    REASON_LATEST_REVIEW_NOT_APPROVED,
    REASON_HEAD_CHANGED,
    REASON_RUN_MISSING,
    REASON_RUN_NOT_GREEN,
    REASON_RUN_UNDEFINED,
    CONDITIONAL,
)

AUTHORITY = {
    "authority_effect": "NONE",
    "can_admit": False,
    "can_merge": False,
    "merge_authority": False,
    "execution_authorized": False,
}


# ---------------------------------------------------------------- workflow data

def parse_workflow(text: str) -> tuple[str | None, list[str] | None]:
    """Return (workflow name, pull_request path filter or None) from YAML text.

    Line-based on purpose: no YAML dependency, and the shape read here is the
    one used in this repository's workflows. Blank lines and comment lines are
    skipped without ending a list.
    """
    name = None
    m = re.search(r"^name:\s*(.+?)\s*$", text, re.M)
    if m:
        name = m.group(1).strip("'\"")

    paths: list[str] | None = None
    in_pr = in_paths = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^  pull_request:\s*$", line):
            in_pr, in_paths = True, False
            continue
        if in_pr and re.match(r"^  \S", line):
            in_pr = in_paths = False
        if in_pr and re.match(r"^    paths:\s*$", line):
            in_paths, paths = True, []
            continue
        if in_paths:
            item = re.match(r"^      - ['\"]?([^'\"]+?)['\"]?\s*$", line)
            if item:
                paths.append(item.group(1))
                continue
            in_paths = False
    return name, paths


def workflow_index(texts: list[str]) -> dict[str, list[str] | None]:
    index: dict[str, list[str] | None] = {}
    for text in texts:
        name, paths = parse_workflow(text)
        if name:
            index[name] = paths
    return index


def glob_matches(pattern: str, path: str) -> bool:
    """Match a GitHub-style path filter: ** spans directories, * does not."""
    regex = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            i += 2
            if i < len(pattern) and pattern[i] == "/":
                # "a/**/b" matches "a/b" as well as "a/x/y/b".
                regex += "(?:.*/)?"
                i += 1
            else:
                regex += ".*"
            continue
        ch = pattern[i]
        regex += "[^/]*" if ch == "*" else re.escape(ch)
        i += 1
    return re.fullmatch(regex, path) is not None


# ------------------------------------------------------------------ the view

def _local_numbers(regex: re.Pattern, body: str, repository: str) -> list[int]:
    """Issue numbers referenced in this repository. Other repositories are ignored."""
    found = set()
    for m in regex.finditer(body or ""):
        qualifier = m.group("repo")
        if qualifier and qualifier.lower() != (repository or "").lower():
            continue
        found.add(int(m.group("num")))
    return sorted(found)


def _closing_targets(body: str, repository: str) -> list[int]:
    return _local_numbers(CLOSING_RE, body, repository)


def _references(body: str, repository: str, closes: list[int]) -> list[int]:
    return sorted(set(_local_numbers(REF_RE, body, repository)) - set(closes))


def _approval_standing(reviews, actors):
    """Return the approval that stands, or None.

    For each authorized actor, the latest relevant review decides. An approval
    that the same actor later superseded with CHANGES_REQUESTED or DISMISSED
    does not count.
    """
    latest: dict[str, dict] = {}
    for r in reviews:
        login = r.get("login")
        if login not in actors or r.get("state") not in RELEVANT_REVIEW_STATES:
            continue
        prev = latest.get(login)
        if prev is None or (r.get("submitted_at") or "") >= (prev.get("submitted_at") or ""):
            latest[login] = r
    approvals = [r for r in latest.values() if r["state"] == "APPROVED"]
    if not approvals:
        return None
    return max(approvals, key=lambda r: r.get("submitted_at") or "")


def _required_run_conditions(pr, index, required_names):
    conditions: list[str] = []
    changed = pr.get("changed_files") or []
    head = pr.get("head_sha")
    runs = [r for r in pr.get("runs", []) if r.get("event") == "pull_request"
            and r.get("head_sha") == head]
    for name in required_names:
        if name not in index:
            conditions.append(REASON_RUN_UNDEFINED + name)
            continue
        paths = index[name]
        if paths is not None and not any(
            glob_matches(p, f) for p in paths for f in changed
        ):
            conditions.append(CONDITIONAL + name)
            continue
        matching = [r for r in runs if r.get("workflow_name") == name]
        if not matching:
            conditions.append(REASON_RUN_MISSING + name)
            continue
        latest = max(matching, key=lambda r: r.get("id") or 0)
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            conditions.append(REASON_RUN_NOT_GREEN + name)
    return conditions


def _admission_issue(issue: dict | None) -> bool:
    # The issues API also returns pull requests. A PR body is never an admission request.
    if not issue or issue.get("is_pull_request"):
        return False
    return bool(ADMISSION_RE.search(issue.get("body") or ""))


def _evaluate_pr(pr, snapshot, actors, index, required_names):
    """Return (lane, missing_conditions, edges) for one PR."""
    repository = snapshot.get("repository") or ""
    body = pr.get("body") or ""
    closes = _closing_targets(body, repository)
    refs = _references(body, repository, closes)
    edges = [{"from": f"PR#{pr['number']}", "to": f"ISSUE#{n}", "kind": "CLOSES"}
             for n in closes]
    edges += [{"from": f"PR#{pr['number']}", "to": f"ISSUE#{n}", "kind": "REFERENCES"}
              for n in refs]

    if pr.get("merged") or pr.get("state") == "closed":
        return "TERMINAL", [], edges

    if pr.get("draft"):
        return "DRAFT", [REASON_DRAFT], edges

    if pr.get("incomplete"):
        # Partial reviews or runs cannot support a definitive condition.
        return "INCOMPLETE", [REASON_INCOMPLETE], edges

    conditions: list[str] = []
    admission_issues = [
        n for n in closes
        if _admission_issue(snapshot["issues"].get(str(n)))
        and snapshot["issues"][str(n)].get("state") == "open"
    ]
    if not admission_issues:
        conditions.append(REASON_NO_ADMISSION_LINK)

    approval = _approval_standing(pr.get("reviews", []), actors)
    if approval is None:
        conditions.append(REASON_LATEST_REVIEW_NOT_APPROVED)
    elif approval.get("commit_id") != pr.get("head_sha"):
        conditions.append(REASON_HEAD_CHANGED)

    conditions += _required_run_conditions(pr, index, required_names)
    lane = "EVALUATION_REVIEW" if conditions else "EVALUATION_READY"
    return lane, conditions, edges


def build_view(snapshot: dict, *, actors, generated_at: str,
               policy_sha: str | None = None,
               required_names=REQUIRED_RUN_NAMES) -> dict:
    """Pure function: snapshot in, view out. No network, no file writes."""
    index = workflow_index(snapshot.get("workflow_texts", []))
    nodes, edges = [], []
    seen_issue_numbers = set()

    for pr in sorted(snapshot.get("pulls", []), key=lambda p: p["number"]):
        lane, conditions, pr_edges = _evaluate_pr(
            pr, snapshot, set(actors), index, required_names)
        edges += pr_edges
        seen_issue_numbers |= {int(e["to"].split("#")[1]) for e in pr_edges}
        nodes.append({
            "id": f"PR#{pr['number']}",
            "kind": "PULL_REQUEST",
            "number": pr["number"],
            "state": "merged" if pr.get("merged") else pr.get("state"),
            "draft": bool(pr.get("draft")),
            "head_sha": pr.get("head_sha"),
            "lane": lane,
            "missing_conditions": conditions,
        })

    for number in sorted(seen_issue_numbers):
        issue = snapshot["issues"].get(str(number))
        if issue is None:
            state, admission = "UNRESOLVED", False
        else:
            state = issue.get("state")
            admission = _admission_issue(issue)
        nodes.append({
            "id": f"ISSUE#{number}",
            "kind": "ISSUE",
            "number": number,
            "state": state,
            "admission_requested": admission,
        })

    status = "INCOMPLETE" if snapshot.get("errors") or snapshot.get("truncated") else "OK"
    return {
        "schema": SCHEMA,
        "repository": snapshot.get("repository"),
        "generated_at": generated_at,
        "policy_sha": policy_sha,
        "default_head_sha": snapshot.get("default_head_sha"),
        "snapshot": {
            "status": status,
            "errors": sorted(snapshot.get("errors", [])),
            "truncated": bool(snapshot.get("truncated")),
            "pr_count": len(snapshot.get("pulls", [])),
        },
        **AUTHORITY,
        "nodes": nodes,
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"], e["kind"])),
    }


# ----------------------------------------------------------------- rendering

def render_markdown(view: dict) -> str:
    def fmt(value):
        return str(value).lower() if isinstance(value, bool) else str(value)

    authority = " · ".join(
        f"{key}: `{fmt(view[key])}`"
        for key in ("authority_effect", "can_admit", "can_merge", "merge_authority",
                    "execution_authorized")
    )
    lines = [
        "# Research graph view (generated, read-only)",
        "",
        f"Schema `{view['schema']}` · generated {view['generated_at']} · "
        f"snapshot **{view['snapshot']['status']}**",
        "",
        f"Authority: {authority}",
        "",
        "This view describes missing conditions; it grants no admission, approval, "
        "or merge authority. Lanes are descriptive.",
        "",
        "## Pull requests",
        "",
        "| PR | Lane | Missing conditions |",
        "|---|---|---|",
    ]
    for node in (n for n in view["nodes"] if n["kind"] == "PULL_REQUEST"):
        conds = ", ".join(f"`{c}`" for c in node["missing_conditions"]) or "—"
        lines.append(f"| #{node['number']} | {node['lane']} | {conds} |")
    if view["snapshot"]["errors"]:
        lines += ["", "## Snapshot errors", ""]
        lines += [f"- {e}" for e in view["snapshot"]["errors"]]
    lines.append("")
    return "\n".join(lines)


def write_report(view: dict, out_dir: Path) -> None:
    """Write exactly graph.json and GRAPH.md into out_dir (must be research-graph/)."""
    if out_dir.name != OUT_DIR_NAME:
        raise ValueError(f"refusing to write outside {OUT_DIR_NAME}/: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "graph.json").write_text(
        json.dumps(view, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "GRAPH.md").write_text(render_markdown(view), encoding="utf-8")


# ------------------------------------------------------------- live fetching

class _ReadOnlyGitHub:
    """GET-only client. There is deliberately no POST/PATCH/PUT/DELETE path."""

    def __init__(self, token: str, repo: str):
        self.token, self.repo = token, repo
        self.errors: list[str] = []

    def get(self, path: str):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}/{path}",
            headers={"Authorization": f"Bearer {self.token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_or_error(self, path: str, label: str, *, not_found_ok: bool = False):
        """Return parsed JSON, or None. Every failure except an allowed 404 is recorded."""
        try:
            return self.get(path)
        except urllib.error.HTTPError as err:
            if err.code == 404 and not_found_ok:
                return None
            self.errors.append(f"{label}: HTTP {err.code}")
        except Exception as err:  # noqa: BLE001 - recorded, snapshot marked INCOMPLETE
            self.errors.append(f"{label}: {type(err).__name__}")
        return None

    def list_all(self, path: str, label: str, *, key: str | None = None, cap: int):
        """Follow pages up to cap. Returns (items, truncated, failed)."""
        items: list = []
        page = 1
        sep = "&" if "?" in path else "?"
        while True:
            data = self.get_or_error(f"{path}{sep}per_page=100&page={page}", label)
            if data is None:
                return items, False, True
            batch = data.get(key, []) if key else data
            items += batch
            if len(batch) < 100:
                return items, False, False
            if len(items) >= cap:
                return items[:cap], True, False
            page += 1


def fetch_snapshot(repo: str, token: str, workflows_dir: Path) -> dict:
    gh = _ReadOnlyGitHub(token, repo)
    truncated = False

    open_prs, cut, _ = gh.list_all("pulls?state=open", "list open PRs", cap=PR_CAP)
    truncated |= cut
    closed_prs = gh.get_or_error(
        f"pulls?state=closed&sort=updated&direction=desc&per_page={CLOSED_PR_SAMPLE}",
        "list closed PRs") or []

    pulls, issue_numbers = [], set()
    for raw in open_prs + closed_prs:
        n = raw["number"]
        files, cut_f, fail_f = gh.list_all(f"pulls/{n}/files", f"files #{n}", cap=FILES_CAP)
        reviews, cut_r, fail_r = gh.list_all(f"pulls/{n}/reviews", f"reviews #{n}", cap=REVIEWS_CAP)
        head = raw["head"]["sha"]
        runs, cut_u, fail_u = gh.list_all(f"actions/runs?head_sha={head}", f"runs #{n}",
                                          key="workflow_runs", cap=RUNS_CAP)
        truncated |= cut_f or cut_r or cut_u
        incomplete = any((cut_f, cut_r, cut_u, fail_f, fail_r, fail_u))
        body = raw.get("body") or ""
        pulls.append({
            "number": n,
            "body": body,
            "state": raw.get("state"),
            "draft": bool(raw.get("draft")),
            "merged": bool(raw.get("merged_at")),
            "incomplete": incomplete,
            "head_sha": head,
            "changed_files": [f["filename"] for f in files],
            "reviews": [{"login": (r.get("user") or {}).get("login"),
                         "state": r.get("state"),
                         "commit_id": r.get("commit_id"),
                         "submitted_at": r.get("submitted_at")} for r in reviews],
            "runs": [{"id": r.get("id"), "workflow_name": r.get("name"),
                      "event": r.get("event"), "head_sha": r.get("head_sha"),
                      "status": r.get("status"), "conclusion": r.get("conclusion")}
                     for r in runs],
        })
        issue_numbers |= set(_closing_targets(body, repo))
        issue_numbers |= set(_references(body, repo, []))

    issues: dict[str, dict] = {}
    unfetched: set[int] = set(sorted(issue_numbers)[ISSUE_CAP:])
    for number in sorted(issue_numbers)[:ISSUE_CAP]:
        errors_before = len(gh.errors)
        # A referenced issue that does not exist is UNRESOLVED, not a fetch failure.
        raw = gh.get_or_error(f"issues/{number}", f"issue #{number}", not_found_ok=True)
        if raw is None:
            if len(gh.errors) > errors_before:
                unfetched.add(number)
            continue
        issues[str(number)] = {"state": raw.get("state"),
                               "body": raw.get("body") or "",
                               "is_pull_request": "pull_request" in raw}
    if len(issue_numbers) > ISSUE_CAP:
        truncated = True
    # A PR whose closing reference could not be read cannot be judged complete.
    for pull in pulls:
        if set(_closing_targets(pull["body"], repo)) & unfetched:
            pull["incomplete"] = True

    default_head = None
    default = gh.get_or_error("branches/main", "default branch")
    if default:
        default_head = default["commit"]["sha"]

    texts = [p.read_text(encoding="utf-8") for p in sorted(workflows_dir.glob("*.yml"))]
    return {
        "repository": repo,
        "default_head_sha": default_head,
        "pulls": pulls,
        "issues": issues,
        "workflow_texts": texts,
        "errors": gh.errors,
        "truncated": truncated,
    }


# ------------------------------------------------------------------ self-check

def run_smoke_test() -> int:
    """Offline check of the pure core: authority fields, one reason code, one pass."""
    snapshot = {
        "repository": "humanaios-ui/operations",
        "default_head_sha": "c" * 40,
        "pulls": [{"number": 1, "body": "Closes #2", "state": "open",
                   "draft": False, "merged": False, "head_sha": "a" * 40,
                   "changed_files": ["docs/x.md"], "reviews": [], "runs": []}],
        "issues": {"2": {"state": "open", "body": "state: ADMISSION_REQUESTED"}},
        "workflow_texts": [],
        "errors": [],
        "truncated": False,
    }
    view = build_view(snapshot, actors=["humanaios-ui"], generated_at="smoke",
                      policy_sha=None)
    checks = {
        "authority_none": view["authority_effect"] == "NONE" and view["can_merge"] is False,
        "reason_emitted": "LATEST_REVIEW_NOT_APPROVED" in view["nodes"][0]["missing_conditions"],
        "admission_link_recognised": "NO_ADMISSION_LINK" not in view["nodes"][0]["missing_conditions"],
    }
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    return 0 if all(checks.values()) else 1


# -------------------------------------------------------------------- CLI

def _load_actors(policy_path: Path) -> tuple[list[str], str]:
    """Read authorized evaluation actors as data. Does not import gate code."""
    raw = policy_path.read_bytes()
    policy = json.loads(raw.decode("utf-8"))
    actors = (policy.get("evaluation_admission") or {}).get("authorized_actors") or []
    return list(actors), hashlib.sha256(raw).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--workflows-dir", type=Path, default=Path(".github/workflows"))
    ap.add_argument("--policy", type=Path, default=Path("REPOSITORY_COORDINATOR_POLICY.json"))
    ap.add_argument("--out-dir", type=Path, default=Path(OUT_DIR_NAME))
    ap.add_argument("--smoke-test", action="store_true",
                    help="run the offline self-check and exit")
    ap.add_argument("--snapshot-json", "--input", dest="snapshot_json", type=Path,
                    help="offline mode: build from a saved snapshot instead of the API")
    args = ap.parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()

    actors, policy_sha = _load_actors(args.policy)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.snapshot_json:
        snapshot = json.loads(args.snapshot_json.read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token or not args.repo:
            print("GITHUB_TOKEN and --repo (or GITHUB_REPOSITORY) are required", file=sys.stderr)
            return 2
        snapshot = fetch_snapshot(args.repo, token, args.workflows_dir)

    view = build_view(snapshot, actors=actors, generated_at=generated_at,
                      policy_sha=policy_sha)
    try:
        write_report(view, args.out_dir)
    except ValueError as err:
        print(err, file=sys.stderr)
        return 2
    print(f"wrote {args.out_dir}/graph.json and GRAPH.md "
          f"(snapshot {view['snapshot']['status']}, {view['snapshot']['pr_count']} PRs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
