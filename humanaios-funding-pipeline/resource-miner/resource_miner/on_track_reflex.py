#!/usr/bin/env python3
"""On-Track Reflex v0.1: read-only observation for INTENT-OS x Resource Miner.

Builder v1.7 compliant. TOOL_ZONE=1. No admission, deployment, or merge authority.
This instrument reports explicit *claims* of connection, not goal attainment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
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
MAX_ITEMS = 500


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
    with urlopen(req, timeout=15) as response:
        return json.load(response), response.headers.get("Link", "")


def github_snapshot(repo: str, token: str, max_pages: int) -> tuple[list[dict], bool]:
    """Collect bounded open items (GitHub issues endpoint includes PRs).

    Always fetch the canonical closed objective as an anchor, but never claim
    the bounded sample represents every repository or historical work item.
    """
    if repo != REPO or not 1 <= max_pages <= 5:
        raise ValueError("Only the operations repository and 1-5 pages are supported")
    items: list[dict] = []
    truncated = False
    for page in range(1, max_pages + 1):
        payload, link = _json_get(repo,
            f"/repos/humanaios-ui/operations/issues?state=open&sort=updated&direction=desc&per_page=100&page={page}",
            token)
        if not isinstance(payload, list):
            raise ValueError("Unexpected GitHub issue list response")
        items.extend(payload)
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
    markers = set(MARKER.findall(body[:8000]))
    if markers == {TARGET}:
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
                 truncated: bool = False, source: str = "OFFLINE_FIXTURE") -> dict:
    if repo != REPO:
        raise ValueError("Only allowlisted repo supported in v0.1")
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError("Invalid or oversized item collection")
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
                  "complete_open_work_inventory": not truncated and source == "GITHUB_API_OPEN_PLUS_ANCHOR",
                  "may_omit_closed_work": True, "sampling_truncated": bool(truncated),
                  "cross_repository_coverage": False},
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
        ],
    }
    report["snapshot_sha256"] = _digest(report)
    return report


def _markdown_cell(text: object) -> str:
    # Untrusted issue titles must never inject tables, links, or job-summary commands.
    s = str(text).replace("|", "/").replace(chr(96), "'")
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", s)
    return s[:130]


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
        f"cross-repository: false.",
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
    lines += ["", f"Showing {min(limit,len(report['items']))} of {len(report['items'])} inspected items.",
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
    assert "## fake success" not in render_markdown(report)
    print("on-track reflex smoke test: PASS")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, help="Offline JSON list or {items, truncated} specimen")
    p.add_argument("--repo", default=REPO, choices=(REPO,))
    p.add_argument("--max-pages", type=int, default=3)
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
        report = build_report(items, args.repo, truncated=truncated, source=source)
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
