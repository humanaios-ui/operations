#!/usr/bin/env python3
"""
ops_snapshot_v0_1 — deterministic operations snapshot (PRs, CI, blockers) as one JSON file
TYPE: tool
Builder v1.7 compliant · reporting_tool
HumanAIOS · Z1 proposal · AUTHORITY_EFFECT: NONE

WHY
---
The daily operations digest is currently written by an external chat app. Most of
that digest is counting, not judgement: which PRs are open, which checks failed,
what is blocked. Counting does not need a language model. This tool does the
counting with plain code against the GitHub REST API, so any reader (human or
model) starts from the same machine-checkable facts.

WHAT IT DOES
------------
1. Reads open PRs, the default-branch head, check runs on each head, and open
   issues carrying a blocker label.
2. Applies fixed, named blocker rules (see BLOCKER_RULES).
3. Writes one JSON document. Same API responses and observation clock produce
   identical JSON, including derived stale-PR signals.

WHAT IT DOES NOT DO
-------------------
- No writes to GitHub. No comments, labels, merges, dispatches.
- No language model. No prose interpretation.
- No unresolved-review-thread counts (needs GraphQL; listed in coverage.not_collected).
- A green check is CAPABILITY evidence only. It is not approval or admission.

Usage:
  GITHUB_TOKEN=... python3 tools/ops_snapshot_v0_1.py --repo humanaios-ui/operations --out ops_snapshot.json
  python3 tools/ops_snapshot_v0_1.py --from-raw raw.json --out ops_snapshot.json   # replay saved observation clock
  python3 tools/ops_snapshot_v0_1.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

TOOL_NAME = "ops_snapshot"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "reporting_tool"
TOOL_ZONE = 1

SCHEMA = "humanaios.ops-snapshot.v0_1"
API = "https://api.github.com"
FAILING = {"failure", "timed_out", "action_required", "startup_failure"}
DEFAULT_BLOCKER_LABELS = ("blocker", "blocked", "P0")
STALE_DAYS = 14
PAGE_SIZE = 100
MAX_PAGES = 20  # Bounded collection: incomplete pages cause UNKNOWN totals.

BLOCKER_RULES = {
    "MAIN_CHECK_FAILED": "A check run on the default-branch head concluded failing.",
    "PR_CHECK_FAILED": "A check run on an open, non-draft PR head concluded failing.",
    "PR_STALE": f"An open, non-draft PR has had no update for {STALE_DAYS}+ days.",
    "ISSUE_LABELED_BLOCKER": "An open issue carries a configured blocker label.",
}


# ---------------------------------------------------------------- fetch layer

class GitHub:
    def __init__(self, token: str, api: str = API):
        self.token = token
        self.api = api
        self.calls = 0
        self.errors: list[dict] = []

    def get(self, path: str, params: dict | None = None):
        url = f"{self.api}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "humanaios-ops-snapshot",
            **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
        })
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self.errors.append({"path": path, "status": e.code})
            return None
        except (urllib.error.URLError, TimeoutError) as e:
            self.errors.append({"path": path, "status": "network",
                                "reason": str(getattr(e, "reason", e))})
            return None


def _pages(gh: GitHub, path: str, params: dict, key: str | None = None) -> tuple[list, bool]:
    """Fetch a bounded, complete REST collection. PRs count toward issue page size."""
    out: list = []
    expected_total: int | None = None
    for page in range(1, MAX_PAGES + 1):
        response = gh.get(path, {**params, "per_page": PAGE_SIZE, "page": page})
        if response is None:
            return out, False
        if key is None:
            rows = response
        else:
            if not isinstance(response, dict) or not isinstance(response.get("total_count"), int):
                gh.errors.append({"path": path, "status": "malformed_total_count"})
                return out, False
            if expected_total is None:
                expected_total = response["total_count"]
            elif expected_total != response["total_count"]:
                gh.errors.append({"path": path, "status": "total_count_changed"})
                return out, False
            rows = response.get(key)
        if not isinstance(rows, list):
            gh.errors.append({"path": path, "status": "malformed_page"})
            return out, False
        out.extend(rows)
        if key is not None and expected_total is not None:
            if len(out) >= expected_total:
                if len(out) > expected_total:
                    gh.errors.append({"path": path, "status": "inconsistent_total_count"})
                    return out, False
                return out, True
            if len(rows) < PAGE_SIZE:
                gh.errors.append({"path": path, "status": "truncated_page"})
                return out, False
        elif len(rows) < PAGE_SIZE:
            return out, True
    gh.errors.append({"path": path, "status": "page_limit", "limit": MAX_PAGES})
    return out, False


def fetch_raw(gh: GitHub, repo: str, blocker_labels: tuple[str, ...]) -> dict:
    """Collect source observations with explicit completeness and a replay clock."""
    observed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    meta = gh.get(f"/repos/{repo}")
    branch = meta.get("default_branch") if isinstance(meta, dict) else None
    head = gh.get(f"/repos/{repo}/commits/{branch}") if branch else None
    main_sha = head.get("sha") if isinstance(head, dict) else None
    main_observed = bool(branch and main_sha)

    prs, prs_complete = _pages(gh, f"/repos/{repo}/pulls", {"state": "open"})
    checks: dict[str, list] = {}
    check_observed_by_sha: dict[str, bool] = {}
    shas = [main_sha] + [p.get("head", {}).get("sha") for p in prs if isinstance(p, dict)]
    for sha in dict.fromkeys(s for s in shas if s):
        rows, complete = _pages(gh, f"/repos/{repo}/commits/{sha}/check-runs", {}, "check_runs")
        checks[sha] = rows
        check_observed_by_sha[sha] = complete

    issues: list = []
    issues_complete = True
    for label in blocker_labels:
        rows, complete = _pages(gh, f"/repos/{repo}/issues", {"state": "open", "labels": label})
        issues.extend(i for i in rows if isinstance(i, dict) and "pull_request" not in i)
        issues_complete = issues_complete and complete

    return {
        "repo": repo, "default_branch": branch, "main_sha": main_sha,
        "observed_at": observed_at,
        "observed": {
            "main": main_observed, "pulls": prs_complete,
            "checks": all(check_observed_by_sha.values()) and bool(check_observed_by_sha),
            "blocker_issues": issues_complete,
        },
        "pulls": prs, "check_runs": checks,
        "check_observed_by_sha": check_observed_by_sha,
        "blocker_issues": issues, "blocker_labels": list(blocker_labels),
        "api_calls": gh.calls, "api_errors": gh.errors,
    }


# ---------------------------------------------------------------- pure layer

def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return parsed.astimezone(UTC)


def summarize_checks(runs: list, complete: bool = True) -> dict:
    counts: dict[str, int] = {}
    failed: list[dict] = []
    for r in runs:
        status = r.get("conclusion") or r.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
        if r.get("conclusion") in FAILING:
            failed.append({"name": r.get("name"), "conclusion": r.get("conclusion"),
                           "url": r.get("html_url")})
    failed.sort(key=lambda f: (f["name"] or "", f["url"] or ""))
    return {"total": len(runs) if complete else None,
            "by_conclusion": dict(sorted(counts.items())), "failed": failed,
            "observed_complete": complete}


def build_snapshot(raw: dict, now: datetime) -> dict:
    """Pure: raw API responses + clock -> snapshot. No I/O."""
    checks = raw.get("check_runs", {})
    observed = raw.get("observed") or {}
    # Historic/hand-authored files without observation flags remain unverified.
    observed_main = observed.get("main") is True
    observed_pulls = observed.get("pulls") is True
    observed_issues = observed.get("blocker_issues") is True
    check_status = raw.get("check_observed_by_sha") or {}
    main_sha = raw.get("main_sha")
    main_check_complete = bool(observed_main and main_sha and check_status.get(main_sha) is True)
    main_checks = summarize_checks(checks.get(main_sha, []), main_check_complete) if main_sha else summarize_checks([], False)
    blockers: list[dict] = []
    all_checks_complete = main_check_complete

    for f in main_checks["failed"]:
        blockers.append({"rule": "MAIN_CHECK_FAILED", "ref": f"{raw.get('default_branch')}@{main_sha}",
                         "detail": f["name"], "evidence": f["url"]})

    prs = []
    for p in raw.get("pulls", []):
        sha = p.get("head", {}).get("sha")
        complete = bool(sha and check_status.get(sha) is True)
        all_checks_complete = all_checks_complete and complete
        cs = summarize_checks(checks.get(sha, []), complete)
        updated = _parse(p.get("updated_at"))
        idle = (now - updated).days if updated else None
        pr = {
            "number": p.get("number"),
            "title": p.get("title"),
            "author": (p.get("user") or {}).get("login"),
            "draft": bool(p.get("draft")),
            "head_sha": sha,
            "base": (p.get("base") or {}).get("ref"),
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
            "days_since_update": idle,
            "labels": sorted(lb.get("name") for lb in p.get("labels", [])),
            "checks": cs,
            "url": p.get("html_url"),
        }
        prs.append(pr)
        if pr["draft"]:
            continue
        for f in cs["failed"]:
            blockers.append({"rule": "PR_CHECK_FAILED", "ref": f"#{pr['number']}@{sha}",
                             "detail": f["name"], "evidence": f["url"]})
        if idle is not None and idle >= STALE_DAYS:
            blockers.append({"rule": "PR_STALE", "ref": f"#{pr['number']}",
                             "detail": f"{idle} days since update", "evidence": pr["url"]})
    prs.sort(key=lambda x: x["number"] or 0)

    seen = set()
    for i in raw.get("blocker_issues", []):
        if i.get("number") in seen:
            continue
        seen.add(i.get("number"))
        blockers.append({"rule": "ISSUE_LABELED_BLOCKER", "ref": f"issue#{i.get('number')}",
                         "detail": i.get("title"), "evidence": i.get("html_url")})

    blockers.sort(key=lambda b: (b["rule"], b["ref"], b["detail"] or ""))
    by_rule: dict[str, int] = {}
    for b in blockers:
        by_rule[b["rule"]] = by_rule.get(b["rule"], 0) + 1

    errors = raw.get("api_errors", [])
    # An incomplete core fetch cannot establish counts; partial pages cannot prove zero.
    if not (observed_main and observed_pulls):
        tag = "UNOBSERVED"
    elif errors or not (all_checks_complete and observed_issues):
        tag = "OBSERVED_PARTIAL"
    else:
        tag = "OBSERVED"
    unknown = tag == "UNOBSERVED"
    incomplete_blockers = tag != "OBSERVED"
    not_collected = ["unresolved_review_threads", "required_status_check_inventory",
                     "deployment_runtime_state", "resource_or_revenue_outcomes"]
    return {
        "schema": SCHEMA,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": raw.get("repo"),
        "authority_effect": "NONE",
        "epistemic_tag": tag,
        "observed": observed,
        "main": {"branch": raw.get("default_branch"), "sha": main_sha, "checks": main_checks},
        "pull_requests": {
            "open_count": None if unknown else len(prs),
            "draft_count": None if unknown else sum(1 for p in prs if p["draft"]),
            "with_failing_checks": None if unknown or not all_checks_complete else sum(1 for p in prs if p["checks"]["failed"]),
            "truncated_at": PAGE_SIZE * MAX_PAGES if not observed_pulls and len(prs) >= PAGE_SIZE * MAX_PAGES else None,
            "items": prs,
        },
        "blockers": {"rules": BLOCKER_RULES, "count": None if incomplete_blockers else len(blockers),
                     "by_rule": dict(sorted(by_rule.items())), "items": blockers},
        "coverage": {
            "source": "github-rest",
            "api_calls": raw.get("api_calls"),
            "api_errors": errors,
            "check_observed_by_sha": dict(sorted(check_status.items())),
            "blocker_issue_collection_complete": observed_issues,
            "blocker_labels": raw.get("blocker_labels", []),
            "not_collected": not_collected,
            "note": "Green checks are capability evidence, not approval, admission or benefit.",
        },
    }


# ---------------------------------------------------------------- outputs

def markdown_summary(s: dict) -> str:
    m = s["main"]["checks"]
    lines = [
        f"## Ops snapshot — {s['repo']} — {s['generated_at']}",
        (f"- main `{(s['main']['sha'] or '')[:7]}`: "
         f"{m['total'] if m['total'] is not None else 'unknown'} checks, "
         f"{len(m['failed']) if m['observed_complete'] else 'at least ' + str(len(m['failed']))} failing"),
        (f"- open PRs: {s['pull_requests']['open_count']} "
         f"({s['pull_requests']['draft_count']} draft, {s['pull_requests']['with_failing_checks']} with failing checks)"),
        f"- blockers: {s['blockers']['count'] if s['blockers']['count'] is not None else 'unknown'} " + ", ".join(f"{k}={v}" for k, v in s["blockers"]["by_rule"].items()),
        f"- tag: {s['epistemic_tag']} · authority_effect: {s['authority_effect']}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- smoke test

def _fixture() -> dict:
    ok = {"name": "lint", "conclusion": "success", "html_url": "u/ok"}
    bad = {"name": "security-gates", "conclusion": "failure", "html_url": "u/bad"}
    return {
        "repo": "o/r", "default_branch": "main", "main_sha": "m1",
        "pulls": [
            {"number": 2, "title": "fresh", "draft": False, "head": {"sha": "p2"}, "base": {"ref": "main"},
             "updated_at": "2026-10-23T00:00:00Z", "user": {"login": "a"}, "labels": [], "html_url": "pr/2"},
            {"number": 1, "title": "old", "draft": False, "head": {"sha": "p1"}, "base": {"ref": "main"},
             "updated_at": "2026-09-01T00:00:00Z", "user": {"login": "b"}, "labels": [{"name": "x"}], "html_url": "pr/1"},
            {"number": 3, "title": "draft", "draft": True, "head": {"sha": "p3"}, "base": {"ref": "main"},
             "updated_at": "2026-01-01T00:00:00Z", "user": {"login": "c"}, "labels": [], "html_url": "pr/3"},
        ],
        "check_runs": {"m1": [ok, bad], "p1": [ok], "p2": [bad], "p3": [bad]},
        "blocker_issues": [{"number": 9, "title": "host gate", "html_url": "i/9"}],
        "blocker_labels": ["blocker"], "api_calls": 7, "api_errors": [],
        "observed": {"main": True, "pulls": True, "checks": True, "blocker_issues": True},
        "check_observed_by_sha": {"m1": True, "p1": True, "p2": True, "p3": True},
        "observed_at": "2026-10-24T00:00:00Z",
    }


def run_smoke_test() -> bool:
    now = datetime(2026, 10, 24, tzinfo=UTC)
    a = build_snapshot(_fixture(), now)
    b = build_snapshot(_fixture(), now)
    rules = sorted(x["rule"] for x in a["blockers"]["items"])
    checks = [
        ("deterministic", json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)),
        ("pr order", [p["number"] for p in a["pull_requests"]["items"]] == [1, 2, 3]),
        ("blocker rules", rules == ["ISSUE_LABELED_BLOCKER", "MAIN_CHECK_FAILED", "PR_CHECK_FAILED", "PR_STALE"]),
        ("draft excluded", all("#3" not in x["ref"] for x in a["blockers"]["items"])),
        ("authority none", a["authority_effect"] == "NONE"),
    ]
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    return all(p for _, p in checks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--out", default="ops_snapshot.json")
    ap.add_argument("--summary", help="also write a short markdown summary to this path")
    ap.add_argument("--from-raw", "--input", dest="from_raw",
                    help="build from a saved raw JSON instead of the API")
    ap.add_argument("--save-raw", help="save raw API responses here (for replay)")
    ap.add_argument("--blocker-label", action="append",
                    help=f"issue label treated as blocker (default: {', '.join(DEFAULT_BLOCKER_LABELS)})")
    ap.add_argument("--now", help="explicit ISO-8601 UTC observation clock override")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    if args.from_raw:
        with open(args.from_raw, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        if not args.repo:
            ap.error("--repo is required (or set GITHUB_REPOSITORY)")
        gh = GitHub(os.environ.get("GITHUB_TOKEN", ""))
        raw = fetch_raw(gh, args.repo, tuple(args.blocker_label or DEFAULT_BLOCKER_LABELS))
        if args.save_raw:
            with open(args.save_raw, "w", encoding="utf-8") as f:
                json.dump(raw, f, indent=2, sort_keys=True)

    observation_time = args.now or raw.get("observed_at")
    if args.from_raw and not observation_time:
        ap.error("raw replay requires observed_at or --now")
    if observation_time:
        try:
            now = _parse(observation_time)
            if now is None or now.utcoffset().total_seconds() != 0:
                raise ValueError("clock is not UTC")
        except (TypeError, ValueError) as exc:
            ap.error(f"invalid UTC replay clock: {exc}")
    else:
        now = datetime.now(UTC)
    snap = build_snapshot(raw, now)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2, sort_keys=True)
        f.write("\n")
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(markdown_summary(snap))
    print(markdown_summary(snap), end="")
    # Exit 2 when the core facts were not observed, so the manual run goes red
    # instead of publishing an empty snapshot that looks like "nothing wrong".
    return 2 if snap["epistemic_tag"] == "UNOBSERVED" else 0


if __name__ == "__main__":
    sys.exit(main())
