#!/usr/bin/env python3
"""coordinator_admission_sweep_dryrun.py — preview coordinator-admission-sweep.yml.
Builder v1.7 compliant - governance_tool

Reproduces, outside of Actions, exactly what `.github/workflows/coordinator-
admission-sweep.yml` would select — so an operator can see which PRs the sweep
would auto-admit *before* enabling it (COORDINATOR_AUTOSWEEP_ENABLED). It
dispatches nothing and writes nothing; it only selects.

The selection is kept identical to the workflow's step
"Select ADVANCE PRs within capacity and (optionally) admit":

    eligible = items where
        lane == ADMISSION_REVIEW
        and guidance.action == ADVANCE
        and no finding has severity == HIGH
    headroom = max(0, capacity.active_operator_queue_limit
                      - capacity.admitted_ready_count)
    budget   = min(headroom, hard_cap)
    selected = first `budget` eligible PRs sorted by number, excluding objectives
               claimed by ACTIVE PRs or an earlier selection in this batch
    Unknown mergeability is ineligible; incomplete live connections fail closed.

Classification is NOT re-implemented here: it comes from the coordinator's own
`repository_coordinator_v0_1.analyze()`, so a disposition drift cannot hide in a
second copy of the rules. Snapshot fidelity matches the workflow (real
`main_paths`; per-PR `mergeable_state`; bot authors canonicalized to the
`<slug>[bot]` form the policy matches).

Usage:
    coordinator_admission_sweep_dryrun.py                 # live: gh + git, prints the plan
    coordinator_admission_sweep_dryrun.py --snapshot S    # offline: analyze a snapshot file
    coordinator_admission_sweep_dryrun.py --max-admits N  # hard cap (default 10)
    coordinator_admission_sweep_dryrun.py --smoke-test    # offline self-test, no network
"""
from __future__ import annotations

TOOL_NAME = "coordinator_admission_sweep_dryrun"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import time
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from repository_coordinator_v0_1 import analyze  # noqa: E402  (coordinator's own classifier)
from repository_coordinator_state_v1 import verify_projection  # noqa: E402

MAINT_BOT_SUFFIX = "[bot]"
DEFAULT_HARD_CAP = 10


# ---------------------------------------------------------------------------
# selection — identical semantics to the workflow's dispatch step
# ---------------------------------------------------------------------------
def plan(index: dict, hard_cap: int = DEFAULT_HARD_CAP) -> dict:
    cap = index.get("capacity") or {}
    limit = int(cap.get("active_operator_queue_limit") or 0)
    admitted_ready = int(cap.get("admitted_ready_count") or 0)
    headroom = max(0, limit - admitted_ready)
    items = index.get("items") or []

    def objectives(it):
        admission = it.get("admission") or {}
        return set(admission.get("objectives") or []) | set(admission.get("declared_objectives") or [])

    claimed = set().union(*(objectives(it) for it in items
                            if it.get("lane") in {"ACTIVE", "CAPACITY_CONTENTION"}))
    eligible = sorted(
        (it for it in items
         if it.get("lane") == "ADMISSION_REVIEW"
         and (it.get("guidance") or {}).get("action") == "ADVANCE"
         and ((it.get("merge_surface") or {}).get("mergeable_state") or "unknown") != "unknown"
         and not objectives(it) & claimed
         and not any(f.get("severity") == "HIGH" for f in (it.get("findings") or []))),
        key=lambda it: it["number"],
    )
    budget = min(headroom, max(0, hard_cap))
    selected, deferred, conflicting = [], [], []
    for it in eligible:
        if objectives(it) & claimed:
            conflicting.append(it)
        elif len(selected) < budget:
            selected.append(it)
            claimed.update(objectives(it))
        else:
            deferred.append(it)
    return {
        "limit": limit,
        "admitted_ready": admitted_ready,
        "headroom": headroom,
        "hard_cap": hard_cap,
        "budget": budget,
        "eligible": eligible,
        "selected": selected,
        "deferred": deferred,
        "conflicting": conflicting,
        "lanes": dict(Counter(it.get("lane") for it in items)),
        "actions": dict(Counter((it.get("guidance") or {}).get("action") for it in items)),
        "open_prs": len(items),
    }


# ---------------------------------------------------------------------------
# live snapshot (gh + git) — mirrors the workflow's collect step
# ---------------------------------------------------------------------------
_GQL = """
query($owner:String!,$repo:String!,$cursor:String){
  repository(owner:$owner,name:$repo){
    pullRequests(states:OPEN, first:40, after:$cursor, orderBy:{field:CREATED_AT,direction:ASC}){
      pageInfo{hasNextPage endCursor}
      nodes{
        number title body isDraft url headRefOid mergeable mergeStateStatus
        author{__typename login}
        labels(first:20){nodes{name}}
        files(first:100){pageInfo{hasNextPage endCursor} nodes{path}}
        reviews(first:100){pageInfo{hasNextPage endCursor} nodes{author{login} state submittedAt commit{oid}}}
      }
    }
  }
}"""


def _sh(args):
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT)


def _gh_open_prs(owner: str, repo: str) -> list[dict]:
    cursor, nodes = None, []
    while True:
        args = ["gh", "api", "graphql", "-f", f"query={_GQL}",
                "-F", f"owner={owner}", "-F", f"repo={repo}"]
        if cursor:
            args += ["-F", f"cursor={cursor}"]
        for _ in range(6):
            r = _sh(args)
            if r.returncode == 0 and r.stdout.strip():
                break
            if any(s in (r.stderr or "") for s in
                   ("reset by peer", 'Post "https', "recv failure", "timeout")):
                time.sleep(4)
                continue
            raise SystemExit(f"gh graphql failed: {(r.stderr or '')[:400]}")
        page = json.loads(r.stdout)["data"]["repository"]["pullRequests"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return nodes


def _main_paths(ref: str = "origin/main") -> list[str]:
    r = _sh(["git", "ls-tree", "-r", "--name-only", ref])
    if r.returncode != 0:
        raise SystemExit(f"git ls-tree failed for {ref}: {r.stderr.strip()[:400]}")
    return [p for p in r.stdout.splitlines() if p]


def _row(n: dict, maint_authors: set[str]) -> dict:
    a = n.get("author") or {}
    author = a.get("login") or "unknown"
    if a.get("__typename") == "Bot" and not author.endswith(MAINT_BOT_SUFFIX):
        author = f"{author}{MAINT_BOT_SUFFIX}"
    is_draft = bool(n.get("isDraft"))
    need = (not is_draft) and (author not in maint_authors)
    mss = (n.get("mergeStateStatus") or "UNKNOWN").lower()
    if n.get("mergeable") == "UNKNOWN":
        mss = "unknown"
    if need:
        for connection in ("files", "reviews"):
            page_info = (n.get(connection) or {}).get("pageInfo") or {}
            if page_info.get("hasNextPage") is not False:
                raise SystemExit(f"PR #{n['number']} has incomplete {connection}; refusing a partial admission plan")
    return {
        "number": n["number"], "title": n.get("title") or "", "body": n.get("body") or "",
        "author": author, "labels": [x["name"] for x in (n["labels"]["nodes"] or [])],
        "html_url": n.get("url"), "state": "open", "draft": is_draft,
        "head_sha": n.get("headRefOid") or "",
        "mergeable_state": mss if need else "unknown",
        "files_complete": need,
        "files": [f["path"] for f in (n["files"]["nodes"] or [])] if need else [],
        "file_details": [],
        "reviews": ([{"user": {"login": (rv.get("author") or {}).get("login") or "unknown"},
                      "state": rv.get("state"), "submitted_at": rv.get("submittedAt"),
                      "commit_id": (rv.get("commit") or {}).get("oid")}
                     for rv in (n["reviews"]["nodes"] or [])] if need else []),
    }


def _live_state(owner: str, repo: str, policy: dict) -> tuple[dict, dict]:
    cfg = policy.get("state") or {}
    branch, ledger_path, projection_path = (
        cfg.get("branch"), cfg.get("ledger_path"), cfg.get("projection_path")
    )
    if not all((branch, ledger_path, projection_path)):
        raise SystemExit("policy state-branch contract is incomplete; refusing to preview")

    def api(path):
        result = _sh(["gh", "api", path])
        if result.returncode != 0:
            raise SystemExit(f"gh state lookup failed: {result.stderr.strip()[:400]}")
        return json.loads(result.stdout)

    sha = api(f"repos/{owner}/{repo}/branches/{branch}")["commit"]["sha"]

    def fetch_text(path):
        data = api(f"repos/{owner}/{repo}/contents/{path}?ref={sha}")
        if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
            raise SystemExit(f"state path {path} is not a base64-encoded file")
        return base64.b64decode(data["content"]).decode("utf-8")

    ledger_text, projection_text = fetch_text(ledger_path), fetch_text(projection_path)
    with tempfile.TemporaryDirectory(prefix="coordinator-sweep-") as tmp:
        ledger_file, state_file = Path(tmp) / "ledger.jsonl", Path(tmp) / "state.json"
        ledger_file.write_text(ledger_text, encoding="utf-8")
        state_file.write_text(projection_text, encoding="utf-8")
        state = verify_projection(ledger_file, state_file)
    if state.get("merge_authority") is not False:
        raise SystemExit("coordinator state claims merge authority; refusing to preview")
    return state, {
        "state_mode": "v0.3", "state_branch": branch, "state_sha": sha,
        "ledger_sha256": hashlib.sha256(ledger_text.encode("utf-8")).hexdigest(),
        "projection_sha256": hashlib.sha256(projection_text.encode("utf-8")).hexdigest(),
    }


def _live_index(owner: str, repo: str) -> dict:
    policy = json.loads((ROOT / "REPOSITORY_COORDINATOR_POLICY.json").read_text())
    state, state_receipt = _live_state(owner, repo, policy)
    pq = (ROOT / "PRIORITY_QUEUE.md").read_text(encoding="utf-8")
    maint = set((((policy or {}).get("maintenance") or {}).get("authors") or []))
    snapshot = {
        "schema_version": "0.3", "purpose": "admission-sweep-dryrun",
        "repository": f"{owner}/{repo}", "main_sha": "local", "policy_ref": "main",
        "policy_sha": "local", "main_paths": _main_paths(),
        **state_receipt,
        "referenced_items": {}, "referenced_pull_requests": {},
        "pull_requests": [_row(n, maint) for n in _gh_open_prs(owner, repo)],
    }
    return analyze(snapshot, pq, policy=policy, state=state)


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
def render(p: dict) -> str:
    L = ["=" * 64,
         "COORDINATOR ADMISSION SWEEP — DRY RUN (selects only; dispatches nothing)",
         "=" * 64,
         f"open PRs analyzed        : {p['open_prs']}",
         f"capacity limit           : {p['limit']}",
         f"admitted-ready (current) : {p['admitted_ready']}",
         f"headroom                 : {p['headroom']}",
         f"hard cap this run        : {p['hard_cap']}",
         f"budget (min)             : {p['budget']}",
         "",
         f"lane census   : {p['lanes']}",
         f"action census : {p['actions']}",
         "",
         f"ELIGIBLE (ADVANCE / no HIGH / ADMISSION_REVIEW): {len(p['eligible'])}"]
    for it in p["eligible"]:
        L.append(f"   #{it['number']:<5} {it['title'][:66]}")
    L.append("")
    L.append("WOULD ADMIT this run (%d): %s" % (
        len(p["selected"]), ", ".join("#" + str(x["number"]) for x in p["selected"]) or "none"))
    if p["deferred"]:
        L.append("DEFERRED (over budget): "
                 + ", ".join("#" + str(x["number"]) for x in p["deferred"]))
    if p["conflicting"]:
        L.append("SKIPPED (objective selected in this batch): "
                 + ", ".join("#" + str(x["number"]) for x in p["conflicting"]))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# smoke-test — offline, no network; exercises classify + select end to end
# ---------------------------------------------------------------------------
def _smoke() -> int:
    policy = {
        "capacity": {"active_operator_queue": 9},
        "maintenance": {"authors": ["dependabot[bot]"]},
    }
    state = {"merge_authority": False,
             "admitted_pull_request_numbers": [], "admitted_issue_numbers": []}
    main_paths = ["README.md", "docs/guide.md"]

    def pr(number, **kw):
        base = {"number": number, "title": f"pr{number}", "body": "", "author": "someone",
                "labels": [], "html_url": f"http://x/{number}", "state": "open", "draft": False,
                "head_sha": f"sha{number}", "mergeable_state": "clean", "files_complete": True,
                "files": ["README.md"], "file_details": [], "reviews": []}
        base.update(kw)
        return base

    snapshot = {
        "schema_version": "0.3", "purpose": "admission-sweep-dryrun",
        "repository": "o/r", "main_sha": "x", "policy_ref": "main", "policy_sha": "x",
        "main_paths": main_paths, "referenced_items": {}, "referenced_pull_requests": {},
        "pull_requests": [
            pr(101),                                              # clean ADVANCE → eligible
            pr(102, mergeable_state="dirty"),                     # REBASE_RETEST → excluded
            pr(103, reviews=[{"user": {"login": "rev"}, "state": "CHANGES_REQUESTED",
                              "submitted_at": "2026-01-01T00:00:00Z", "commit_id": "sha103"}]),
            # ^ CHANGES_REQUESTED → HIGH finding → REEXAMINE → excluded
            pr(104, draft=True),                                  # WORKBENCH → excluded
            pr(105, author="dependabot[bot]"),                    # MAINTENANCE → excluded
        ],
    }
    index = analyze(snapshot, "", policy=policy, state=state)
    p = plan(index, hard_cap=DEFAULT_HARD_CAP)

    elig = {it["number"] for it in p["eligible"]}
    assert elig == {101}, f"eligible should be exactly {{101}}, got {elig}"
    assert [it["number"] for it in p["selected"]] == [101], "should select #101"
    assert p["headroom"] == 9 and p["budget"] == 9, (p["headroom"], p["budget"])

    # capacity bound: a full queue yields zero headroom → nothing selected
    state_full = dict(state, admitted_pull_request_numbers=list(range(900, 909)))
    # fabricate 9 admitted-ready ACTIVE PRs so admitted_ready_count == limit
    snap_full = dict(snapshot, pull_requests=snapshot["pull_requests"] + [
        pr(900 + i) for i in range(9)
    ])
    idx2 = analyze(snap_full, "", policy=policy, state=state_full)
    p2 = plan(idx2, hard_cap=DEFAULT_HARD_CAP)
    assert idx2["capacity"]["admitted_ready_count"] == 9, idx2["capacity"]
    assert p2["headroom"] == 0 and p2["budget"] == 0, p2
    assert p2["selected"] == [], "full ACTIVE queue must select nothing"

    # hard cap clamps below headroom
    p3 = plan(index, hard_cap=0)
    assert p3["selected"] == [], "hard_cap=0 must select nothing"

    print("✓ smoke-test passed: ADVANCE/no-HIGH/ADMISSION_REVIEW selection; "
          "dirty/changes-requested/draft/maintenance excluded; headroom + hard-cap bounds hold")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="coordinator_admission_sweep_dryrun.py",
                                 description="Preview which PRs coordinator-admission-sweep.yml would admit.")
    ap.add_argument("--snapshot", metavar="FILE",
                    help="analyze a snapshot JSON file offline instead of live gh/git")
    ap.add_argument("--owner", default="humanaios-ui")
    ap.add_argument("--repo", default="operations")
    ap.add_argument("--max-admits", type=int, default=DEFAULT_HARD_CAP, help="hard cap (default 10)")
    ap.add_argument("--json", action="store_true", help="emit the plan as JSON")
    ap.add_argument("--smoke-test", action="store_true", help="offline self-test; no network")
    args = ap.parse_args(argv)

    if args.smoke_test:
        return _smoke()

    if args.snapshot:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "REPOSITORY_COORDINATOR_POLICY.json").read_text())
        state = json.loads((ROOT / "COORDINATOR_STATE.json").read_text())
        pq = (ROOT / "PRIORITY_QUEUE.md").read_text(encoding="utf-8")
        index = analyze(snapshot, pq, policy=policy, state=state)
    else:
        index = _live_index(args.owner, args.repo)

    p = plan(index, hard_cap=args.max_admits)
    if args.json:
        slim = {k: ([it["number"] for it in v] if k in {"eligible", "selected", "deferred", "conflicting"} else v)
                for k, v in p.items()}
        print(json.dumps(slim, indent=2, sort_keys=True))
    else:
        print(render(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
