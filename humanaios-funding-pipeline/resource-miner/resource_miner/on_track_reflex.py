#!/usr/bin/env python3
"""On-Track Reflex v0.1: read-only observation for INTENT-OS x Resource Miner.

Builder v1.7 compliant. TOOL_ZONE=1. No admission, deployment, or merge authority.
This instrument reports explicit *claims* of connection, not goal attainment.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TOOL_NAME = "on_track_reflex"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "S-101826-on-track-reflex"
TOOL_ZONE = 1

REPO = "humanaios-ui/operations"
TARGET = "INTENT_OS_RESOURCE_MINER_USABLE"
ANCHORS = frozenset((822, 928))  # Issue #822 is a declared product objective; #928 is the observation pilot.
MARKER = re.compile(r"(?m)^[ \t]*on_track_target:[ \t]*([A-Z0-9_]+)[ \t]*$")
BLOCK_LABELS = frozenset(("blocked", "needs-human", "needs_human", "on-hold"))
API = "https://api.github.com"
MAX_ITEMS = 501
# Transient GitHub throttling (secondary rate limits) shows up as 403 or 429.
# Retries are bounded; a persistent refusal still fails closed.
RETRYABLE_STATUS = frozenset((403, 429))
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = (2, 4, 8)
MAX_RETRY_AFTER_SECONDS = 60
THROTTLE_HEADERS = (
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-ratelimit-resource",
    "x-ratelimit-used",
    "x-github-request-id",
)
_sleep = time.sleep


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_get(repo: str, path: str, token: str) -> tuple[object, str]:
    if repo != REPO or not path.startswith("/repos/humanaios-ui/operations/"):
        raise ValueError("Repository or API path not allowlisted")
    req = Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "humanaios-on-track-reflex/0.1",
        **({"Authorization": "Bearer " + token} if token else {}),
    })
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urlopen(req, timeout=15) as response:
                return json.load(response), response.headers.get("Link", "")
        except HTTPError as error:
            if error.code not in RETRYABLE_STATUS:
                raise
            _log_throttle(path, attempt, error)
            # A depleted primary GitHub API allowance cannot recover through
            # short backoff. Stop immediately, preserving the failed-observation
            # gate and avoiding three additional quota-consuming requests.
            remaining = next((value for key, value in error.headers.items()
                              if key.lower() == "x-ratelimit-remaining"), None) if error.headers else None
            if remaining == "0":
                raise
            if attempt == MAX_ATTEMPTS:
                raise
            _sleep(_retry_delay(error, attempt))
    raise AssertionError("unreachable")


def _log_throttle(path: str, attempt: int, error: HTTPError) -> None:
    """Diagnostic only: record why GitHub refused a read.

    Logs rate-limit facts and a short body snippet. Never logs the token or
    request headers.
    """
    headers = {name: error.headers.get(name) for name in THROTTLE_HEADERS} if error.headers else {}
    try:
        body = error.read(200).decode("utf-8", "replace")
    except Exception:  # no body stream (e.g. synthetic error); still log the status
        body = ""
    present = {name: value for name, value in headers.items() if value}
    print(
        f"on-track reflex throttle: HTTP {error.code} path={path} attempt={attempt} "
        f"headers={json.dumps(present, sort_keys=True)} body={json.dumps(body)}",
        file=sys.stderr,
    )


def _retry_delay(error: HTTPError, attempt: int) -> float:
    retry_after = error.headers.get("Retry-After", "") if error.headers else ""
    if retry_after.isdigit():
        return min(int(retry_after), MAX_RETRY_AFTER_SECONDS)
    return BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]


def github_snapshot(repo: str, token: str, max_pages: int) -> tuple[list[dict], bool]:
    """Collect bounded open items (GitHub issues endpoint includes PRs).

    Always fetch the canonical closed objective as an anchor, but never claim
    the bounded sample represents every repository or historical work item.
    """
    if repo != REPO or not 1 <= max_pages <= 5:
        raise ValueError("Only the operations repository and 1-5 pages are supported")
    items: list[dict] = []
    seen: set[int] = set()
    truncated = False
    for page in range(1, max_pages + 1):
        payload, link = _json_get(repo,
            f"/repos/humanaios-ui/operations/issues?state=open&sort=updated&direction=desc&per_page=100&page={page}",
            token)
        if not isinstance(payload, list):
            raise ValueError("Unexpected GitHub issue list response")
        for value in payload:
            number = value.get("number") if isinstance(value, dict) else None
            if number in seen:
                # Offset pagination can repeat or omit rows after concurrent edits.
                # A duplicate is evidence of sampling instability, not an error to hide.
                truncated = True
                continue
            seen.add(number)
            items.append(value)
        next_page = bool(re.search(r'<[^>]+>;\s*rel="next"', link))
        if not next_page:
            break
        if page == max_pages:
            truncated = True
    # The product anchor may be closed and absent from the open-work sampling.
    anchor, _ = _json_get(repo, "/repos/humanaios-ui/operations/issues/822", token)
    if not isinstance(anchor, dict):
        raise ValueError("Unexpected GitHub anchor response")
    items = [item for item in items if item.get("number") != 822]
    items.append(anchor)
    return items, truncated


def _labels(item: dict) -> list[str]:
    labels = item.get("labels") or []
    if not isinstance(labels, list):
        return []
    return sorted({label.get("name", "").lower() for label in labels
                   if isinstance(label, dict) and isinstance(label.get("name"), str)})


def _goal_link(item: dict) -> tuple[str, str]:
    number = item["number"]
    if number in ANCHORS:
        return "DECLARED_ANCHOR", "Pilot objective anchor (not outcome evidence)"
    body = item.get("body") or ""
    if not isinstance(body, str):
        body = ""
    # Markers in issue text are only untrusted declarations, never an authorization.
    # The first nonempty line is the declaration. A fenced example later
    # cannot declare a goal. Scan the entire body to catch conflicting claims.
    normalized = "\n".join(body.splitlines())
    logical = next((line for line in normalized.split("\n") if line.strip()), "")
    markers = set(MARKER.findall(normalized))
    if markers == {TARGET} and MARKER.fullmatch(logical):
        return "DECLARED_BY_AUTHOR", "Explicit goal marker (not independent corroboration)"
    if markers:
        return "UNMAPPED", "Unknown or conflicting marker; requires human mapping"
    return "UNMAPPED", "No explicit goal map"


def _row(item: dict, repo: str) -> dict:
    if not isinstance(item, dict):
        raise ValueError("Issue must be an object")
    number = item.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
        raise ValueError("Invalid issue number")
    title = item.get("title")
    if not isinstance(title, str):
        title = "(title unavailable)"
    title = re.sub(r"[\x00-\x1f\x7f]+", " ", title).strip()[:160]
    kind = "PULL_REQUEST" if isinstance(item.get("pull_request"), dict) else "ISSUE"
    state = item.get("state")
    if state not in ("open", "closed"):
        state = "unknown"
    mapped, basis = _goal_link(item)
    labels = _labels(item)
    blocked = bool(BLOCK_LABELS.intersection(labels))
    # Neither PR existence nor issue closure establishes tests or user outcomes.
    landing = "AT_RISK" if (mapped != "UNMAPPED" and blocked) else "UNVERIFIED"
    if mapped == "UNMAPPED":
        next_action = "Ask owner to declare a supported goal mapping, or leave unrelated."
    elif blocked:
        next_action = "Resolve the named blocker; obtain independent evidence."
    elif number == 822:
        next_action = "Verify deployed /intent-os and a human objective-to-resource outcome."
    elif kind == "PULL_REQUEST":
        next_action = "Verify exact-head tests, then observe user-visible behavior."
    else:
        next_action = "Identify an implemented change and its exact verification receipt."
    return {
        "ref": f"{repo}#{number}",
        "url": f"https://github.com/{repo}/{'pull' if kind == 'PULL_REQUEST' else 'issues'}/{number}",
        "title": title,
        "kind": kind,
        "github_state": state,
        "goal_id": TARGET if mapped != "UNMAPPED" else None,
        "goal_mapping": mapped,
        "mapping_basis": basis,
        "implementation": ("PR_EXISTS_NOT_VERIFIED" if kind == "PULL_REQUEST"
                           else "ISSUE_EXISTS_NOT_VERIFIED"),
        "exact_head_ci": "UNVERIFIED",
        "operator_outcome": "UNVERIFIED",
        "landing_state": landing,
        "blocker_labels": sorted(BLOCK_LABELS.intersection(labels)),
        "next_action": next_action,
        "authority_effect": "NONE",
    }


def build_report(items: list[dict], repo: str = REPO, *,
                 truncated: bool = False, source: str = "OFFLINE_FIXTURE",
                 execution_event: str = "OFFLINE_FIXTURE",
                 execution_sha: str = "UNVERIFIED") -> dict:
    if repo != REPO:
        raise ValueError("Only allowlisted repo supported in v0.1")
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError("Invalid or oversized item collection")
    if execution_event not in {"OFFLINE_FIXTURE", "pull_request", "issues", "workflow_dispatch"}:
        raise ValueError("Unrecognized observation event")
    if execution_sha != "UNVERIFIED" and not re.fullmatch(r"[a-f0-9]{40}", execution_sha):
        raise ValueError("Invalid execution SHA")
    by_number = {}
    for item in items:
        row = _row(item, repo)
        number = int(row["ref"].split("#")[1])
        if number in by_number:
            raise ValueError("Duplicate issue number in source")
        by_number[number] = row
    rows = sorted(by_number.values(),
                  key=lambda x: (x["goal_mapping"] == "UNMAPPED", -int(x["ref"].split("#")[1])))
    mapped = [r for r in rows if r["goal_mapping"] != "UNMAPPED"]
    report = {
        "schema": "humanaios.on_track_reflex/v0.1",
        "goal_id": TARGET,
        "goal_description": "Usable INTENT-OS human objective -> Resource Miner candidates -> independently observed user outcome",
        "scope": {"repository": repo, "source": source, "items_examined": len(rows),
                  "complete_open_work_inventory": False,
                  "may_omit_closed_work": True, "sampling_truncated": bool(truncated),
                  "cross_repository_coverage": False,
                  "execution_event": execution_event, "execution_sha": execution_sha,
                  "candidate_code": execution_event == "pull_request"},
        "counts": {"mapped_declarations": len(mapped), "unmapped": len(rows) - len(mapped),
                   "at_risk_mapped": sum(r["landing_state"] == "AT_RISK" for r in mapped),
                   "verified_user_outcomes": 0},
        "items": rows,
        "overall": "UNVERIFIED",
        "authority_effect": "NONE",
        "merge_authority": False,
        "deployment_authority": False,
        "limitations": [
            "Only explicit issue author goal mappings and fixed pilot anchors are classified.",
            "Mapping assertions, labels and GitHub closure are not independent outcome evidence.",
            "Exact-head CI and deployed human usability have not been checked by this pilot.",
            "A green status is intentionally impossible without an independent outcome verifier.",
            "Intent and evidence graphs may contain PROPOSED mappings; this report does not ratify them.",
            "Offset-paginated GitHub observations are not a point-in-time or complete inventory.",
            "Pull-request events run candidate-controlled code; observations do not independently attest deployment.",
        ],
    }
    report["snapshot_sha256"] = _digest(report)
    return report


def _markdown_cell(text: object) -> str:
    # Untrusted issue titles must never inject tables, links, or job-summary commands.
    s = str(text).replace("|", "/").replace(chr(96), "'")
    s = re.sub(r"[\[\]()]","", s)
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", s)
    return html.escape(s[:130], quote=True)


def render_markdown(report: dict, limit: int = 30) -> str:
    s = report["scope"]
    c = report["counts"]
    lines = [
        "# INTENT-OS On-Track Reflex — observational pilot",
        "",
        "**Core question:** Of everything we are building, what is moving us toward usable INTENT-OS + Resource Miner?",
        "",
        f"**Overall: UNVERIFIED.** No live user outcome has been independently verified by this observer.",
        f"**Scope:** {s['repository']}; {s['items_examined']} items inspected; "
        f"open-work inventory complete: {str(s['complete_open_work_inventory']).lower()}; "
        f"cross-repository: false; sampling truncated: {str(s['sampling_truncated']).lower()}; "
        f"closed history omitted: {str(s['may_omit_closed_work']).lower()}.",
        f"**Observation provenance:** event `{s['execution_event']}`; checkout `{s['execution_sha']}`; "
        f"candidate-controlled code: {str(s['candidate_code']).lower()}.",
        f"**Declared mapping:** {c['mapped_declarations']} mapped / {c['unmapped']} unmapped; "
        f"{c['at_risk_mapped']} mapped with blocker labels. Verified user outcomes: 0.",
        "",
        "Issue and PR descriptions are *claims*, not proof. Merged is not deployed. Deployed is not usable.",
        "",
        "| Work | Mapping | Landing | Next verifiable step |",
        "|---|---|---|---|",
    ]
    for row in report["items"][:limit]:
        label = _markdown_cell(row["ref"] + " " + row["title"])
        lines.append(f"| [{label}]({row['url']}) | {row['goal_mapping']} | "
                     f"{row['landing_state']} | {_markdown_cell(row['next_action'])} |")
    lines += ["", "**Limitations:**", *("- " + str(x) for x in report["limitations"]),
              "", f"Showing {min(limit,len(report['items']))} of {len(report['items'])} inspected items.",
              f"Snapshot SHA-256: {report['snapshot_sha256']}",
              "",
              "Advisory only. No admission, authorization, deploy, write, or merge effects.",
              "Next: compare 30 pilot judgments to independent human reviews; verify production /intent-os separately."]
    return "\n".join(lines) + "\n"


def smoke_test() -> None:
    raw = [
        {"number": 822, "title": "Usable intent service", "state": "closed", "body": ""},
        {"number": 9000, "title": "| injection\n## fake success", "state": "open",
         "pull_request": {"url": "https://api.github.com/"},
         "body": "on_track_target: INTENT_OS_RESOURCE_MINER_USABLE\nTests PASS (self-asserted)"},
        {"number": 9001, "title": "Other work", "state": "open", "body": ""},
    ]
    report = build_report(raw)
    assert report["counts"]["mapped_declarations"] == 2
    assert report["counts"]["verified_user_outcomes"] == 0
    assert all(x["landing_state"] == "UNVERIFIED" for x in report["items"])
    assert report["snapshot_sha256"] == build_report(raw)["snapshot_sha256"]
    assert "\n## fake success" not in render_markdown(report)
    print("on-track reflex smoke test: PASS")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, help="Offline JSON list or {items, truncated} specimen")
    p.add_argument("--repo", default=REPO, choices=(REPO,))
    p.add_argument("--max-pages", type=int, default=3)
    p.add_argument("--execution-event", choices=("OFFLINE_FIXTURE", "pull_request", "issues", "workflow_dispatch"), default="OFFLINE_FIXTURE")
    p.add_argument("--execution-sha", default="UNVERIFIED")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--markdown-out", type=Path)
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args(argv)
    if args.smoke_test:
        smoke_test()
        return 0
    try:
        if args.input:
            raw = json.loads(args.input.read_text(encoding="utf-8"))
            items = raw.get("items") if isinstance(raw, dict) else raw
            truncated = bool(raw.get("truncated", False)) if isinstance(raw, dict) else False
            source = "OFFLINE_FIXTURE"
        else:
            items, truncated = github_snapshot(args.repo, os.getenv("GITHUB_TOKEN", ""), args.max_pages)
            source = "GITHUB_API_OPEN_PLUS_ANCHOR"
        report = build_report(items, args.repo, truncated=truncated, source=source,
                              execution_event=args.execution_event, execution_sha=args.execution_sha)
        rendered = render_markdown(report)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.markdown_out:
            args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_out.write_text(rendered, encoding="utf-8")
        if not args.json_out and not args.markdown_out:
            print(rendered)
        return 0
    except (ValueError, KeyError, TypeError, OSError, HTTPError, URLError) as exc:
        print(f"on-track reflex unavailable (fail closed): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
