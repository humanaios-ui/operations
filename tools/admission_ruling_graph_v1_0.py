#!/usr/bin/env python3
"""
admission_ruling_graph_v1_0.py — join the admission ledger to Z2 rulings and render one page.
Builder v1.7 compliant
HumanAIOS — Q-ADMISSION-RULING-GRAPH-01 (direction 1 of 4, ratified by merge of PR 1287)

Answers: which pull requests were admitted, what happened to each admission, which
candidate blocks each one carried, and which pull request carried the Z2 ruling.

  render                 write ADMISSION_RULING_GRAPH.md from the live sources
  render --stdout        print the page instead of writing it
  --ledger-ref REF       git ref holding ADMISSION_LEDGER.jsonl
                         (default origin/repository-coordinator-state)
  --ledger PATH          read a ledger file instead of a git ref
  --main-ref REF         git ref for the merge history (default origin/main)
  --smoke-test           self-check on a fixture; no filesystem or git access

SOURCES (all read-only)
  ledger     ADMISSION_LEDGER.jsonl on the repository-coordinator-state branch. The copy
             on main is a stale snapshot and is NOT used. Parsed with
             repository_coordinator_state_v1_1.parse_ledger, which accepts both the v2
             events and the 25 older v1 rows. The older v1 reader (…_state_v1.py) rejects
             the live ledger at its first v2 row and is not used.
  merges     the merge commits on main: "Merge pull request #N" and the z1-inbox
             candidate blocks (z1-inbox/**/Q-*.md) each one changed.
  index      z1-inbox/INDEX.yaml: status and signature of each candidate.
  rulings    z1-inbox/**/Z2_RULINGS_*.md: where it names the pull request whose merge
             was the ratification.

WHAT IT DOES NOT DO
  It decides nothing, admits nothing and writes nothing back to the ledger, the index or
  any ruling. authority_effect is NONE. A row on the page is evidence of what the ledger
  and the history say; it is not an admission and not a ruling.
  A pull request merged by squash or rebase has no merge commit, so it is invisible to
  the merge join and is never flagged as a gap.

TEMPORAL POSITION (Q-TEMPORAL-DISSOLUTION-01)
  This tool reads no clock and prints no timestamp. Rows are ordered by their position
  in the ledger (its append order), and a pull request's events are shown in that
  order. Nothing here ages or comes due.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_NAME = "admission_ruling_graph"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-112026-admission-ruling-graph"
TOOL_ZONE = 1

AUTHORITY_EFFECT = "NONE"
ROOT = Path(__file__).resolve().parents[1]
PAGE = "ADMISSION_RULING_GRAPH.md"
LEDGER_FILE = "ADMISSION_LEDGER.jsonl"
INDEX_FILE = "z1-inbox/INDEX.yaml"
DEFAULT_LEDGER_REF = "origin/repository-coordinator-state"
DEFAULT_MAIN_REF = "origin/main"

MERGE_RE = re.compile(r"^Merge pull request #(\d+) from ")
QFILE_RE = re.compile(r"^z1-inbox/.+/(Q-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2})\.md$")
RULING_SECTION_RE = re.compile(r"(?m)^## (Q-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2}) — (\w+)\s*$")
RULING_PR_RE = re.compile(r"pull request #(\d+)")
TERMINAL = "TERMINATE_MERGED"


# --------------------------------------------------------------------------- pure joins

def pr_events(events: list[dict[str, Any]]) -> dict[int, list[tuple[int, str]]]:
    """pull request number -> [(ledger position, decision)] in ledger order."""
    out: dict[int, list[tuple[int, str]]] = {}
    for position, event in enumerate(events, start=1):
        if event.get("subject_kind") != "PULL_REQUEST":
            continue
        out.setdefault(int(event["subject_number"]), []).append(
            (position, str(event["decision"]))
        )
    return out


def parse_merge_log(text: str) -> tuple[list[int], dict[int, list[str]]]:
    """Read `git log --first-parent -m --name-only` output made with the markers below.

    Each record starts with \\x01<sha>\\t<subject>, followed by file names, one per line.
    Returns (pull requests merged, oldest first as the history lists them reversed,
    {pull request -> candidate block ids it changed}).
    """
    merged: list[int] = []
    carried: dict[int, list[str]] = {}
    for record in text.split("\x01"):
        if not record.strip():
            continue
        head, _, body = record.partition("\n")
        _, _, subject = head.partition("\t")
        match = MERGE_RE.match(subject.strip())
        if not match:
            continue
        pr = int(match.group(1))
        merged.append(pr)
        for line in body.splitlines():
            found = QFILE_RE.match(line.strip())
            if found:
                carried.setdefault(pr, [])
                if found.group(1) not in carried[pr]:
                    carried[pr].append(found.group(1))
    merged.reverse()  # git lists newest first; keep history order, oldest first
    return merged, carried


def ruling_prs(ruling_texts: dict[str, str]) -> dict[str, dict[str, Any]]:
    """candidate id -> {"pr": int | None, "file": path} from the Z2_RULINGS files."""
    out: dict[str, dict[str, Any]] = {}
    for path, text in ruling_texts.items():
        sections = list(RULING_SECTION_RE.finditer(text))
        for i, section in enumerate(sections):
            end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            body = text[section.end():end]
            pr = RULING_PR_RE.search(body)
            out[section.group(1)] = {"pr": int(pr.group(1)) if pr else None, "file": path}
    return out


def build_graph(
    *,
    events: list[dict[str, Any]],
    merged: list[int],
    carried: dict[int, list[str]],
    candidates: dict[str, dict[str, Any]],
    rulings: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    by_pr = pr_events(events)
    merged_set = set(merged)

    rows = []
    for pr, evs in sorted(by_pr.items(), key=lambda kv: kv[1][0][0]):
        last = evs[-1][1]
        rows.append({
            "pr": pr,
            "events": [{"position": p, "decision": d} for p, d in evs],
            "last": last,
            "merged_on_main": pr in merged_set,
            "blocks": [q for q in carried.get(pr, []) if q in candidates],
        })

    # an admitted pull request that merged, whose ledger history does not end in a merged row
    gaps = [
        {"pr": r["pr"], "last": r["last"]}
        for r in rows
        if r["merged_on_main"] and r["last"] != TERMINAL
    ]

    # each candidate block, the pull requests that changed it, and the ruling
    block_prs: dict[str, list[int]] = {}
    for pr in merged:
        for q in carried.get(pr, []):
            if q in candidates:
                block_prs.setdefault(q, []).append(pr)
    blocks = []
    for q, meta in candidates.items():
        prs = block_prs.get(q, [])
        ruling = rulings.get(q)
        ruled_pr = ruling["pr"] if ruling else None
        blocks.append({
            "q_id": q,
            "status": meta.get("status"),
            "prs": prs,
            "ruled_by_pr": ruled_pr,
            "ruling_file": ruling["file"] if ruling else None,
            "signature": meta.get("z2_hash"),
            "ruled_pr_admitted": bool(ruled_pr and ruled_pr in by_pr),
        })
    # keep a block that has any pull request or any ruling file; a ruling signed by ratify.py
    # names no pull request but is still a ruling
    blocks = [b for b in blocks if b["prs"] or b["ruling_file"]]
    return {
        "rows": rows,
        "gaps": gaps,
        "blocks": blocks,
        "event_count": len(events),
        "pr_count": len(by_pr),
        "decisions": _count(str(e["decision"]) for e in events),
    }


def _count(items) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return dict(sorted(out.items()))


# --------------------------------------------------------------------------- rendering

def _esc(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _link(pr: int) -> str:
    return f"[#{pr}](https://github.com/humanaios-ui/operations/pull/{pr})"


def render_markdown(graph: dict[str, Any], *, ledger_ref: str, main_ref: str) -> str:
    lines = [
        "# Admission → ruling graph",
        "",
        "> **Generated** by `tools/admission_ruling_graph_v1_0.py`. Do not hand-edit.",
        f"> `authority_effect: {AUTHORITY_EFFECT}`. This page is evidence of what the admission ledger and the merge",
        "> history say. It is not an admission, not a ruling, and not merge authority.",
        "> It carries no timestamps: rows are in ledger order (its append order).",
        "> Until the refresh workflow (direction 2 of `Q-ADMISSION-RULING-GRAPH-01`) exists, this page is a",
        "> snapshot that is regenerated by hand, so it lags the ledger.",
        "",
        f"Ledger: `{LEDGER_FILE}` on `{ledger_ref}` ({graph['event_count']} events, {graph['pr_count']} pull requests).",
        f"Merge history: `{main_ref}`, merge commits only (a squash or rebase merge is not seen).",
        "Decisions: " + ", ".join(f"{k} {v}" for k, v in graph["decisions"].items()) + ".",
        "",
        "## Merged pull requests whose ledger history does not end in a merged row",
        "",
    ]
    if graph["gaps"]:
        lines += ["| Pull request | Last ledger decision |", "|---|---|"]
        lines += [f"| {_link(g['pr'])} | `{g['last']}` |" for g in graph["gaps"]]
        lines += [
            "",
            "These merged on `main`, but the ledger's last row for them is not `TERMINATE_MERGED`. This page",
            "does not say why; it shows only that the two sources disagree.",
        ]
    else:
        lines.append("None.")
    lines += ["", "## Candidate blocks, the pull requests that changed them, and the ruling", ""]
    lines += [
        "| Candidate | Status | Pull requests (merge order) | Ruling carried by | Ruling PR admitted in ledger |",
        "|---|---|---|---|---|",
    ]
    for b in graph["blocks"]:
        prs = ", ".join(_link(p) for p in b["prs"]) or "—"
        ruled = _link(b["ruled_by_pr"]) if b["ruled_by_pr"] else "—"
        admitted = ("yes" if b["ruled_pr_admitted"] else "no") if b["ruled_by_pr"] else "—"
        lines.append(f"| `{b['q_id']}` | {_esc(b['status'])} | {prs} | {ruled} | {admitted} |")
    lines += ["", "A dash in `Ruling carried by` means the ruling file does not name a pull request",
              "(older rulings were signed by `ratify.py`).", "",
              "## Admission history per pull request (ledger order)", ""]
    lines += ["| Pull request | Events (ledger position: decision) | Merged on main | Candidate blocks |",
              "|---|---|---|---|"]
    for r in graph["rows"]:
        evs = " → ".join(f"{e['position']}:{e['decision']}" for e in r["events"])
        blocks = ", ".join(f"`{q}`" for q in r["blocks"]) or "—"
        lines.append(f"| {_link(r['pr'])} | {evs} | {'yes' if r['merged_on_main'] else 'no'} | {blocks} |")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- sources

def _git(args: list[str]) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def load_sources(ledger_ref: str, main_ref: str, ledger_path: str | None) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    import repository_coordinator_state_v1_1 as state  # the live ledger needs the v1.1 reader
    import yaml

    text = Path(ledger_path).read_text(encoding="utf-8") if ledger_path else _git(
        ["show", f"{ledger_ref}:{LEDGER_FILE}"]
    )
    events = state.parse_ledger(text)
    merged, _ = parse_merge_log(_git(
        ["log", "--first-parent", "--merges", "--format=%x01%H%x09%s", main_ref]))
    _, carried = parse_merge_log(_git(
        ["log", "--first-parent", "-m", "--name-only", "--format=%x01%H%x09%s", main_ref,
         "--", ":(glob)z1-inbox/**/Q-*.md"]))
    index = yaml.safe_load((ROOT / INDEX_FILE).read_text(encoding="utf-8"))
    candidates = {c["q_id"]: c for c in index.get("candidates") or []}
    ruling_texts = {
        str(p.relative_to(ROOT)): p.read_text(encoding="utf-8")
        for p in sorted((ROOT / "z1-inbox").glob("**/Z2_RULINGS_*.md"))
    }
    return {
        "events": events, "merged": merged, "carried": carried,
        "candidates": candidates, "rulings": ruling_prs(ruling_texts),
    }


# --------------------------------------------------------------------------- smoke test

def run_smoke_test() -> bool:
    ev = lambda n, d, kind="PULL_REQUEST": {"subject_kind": kind, "subject_number": n, "decision": d}
    events = [
        ev(10, "ADMIT"), ev(10, "REVOKE"),            # admitted, then voided, never merged-terminal
        ev(11, "ADMIT"), ev(11, "TERMINATE_MERGED"),  # clean
        ev(12, "ADMIT"), ev(12, "REVOKE"),            # merged on main, history ends in REVOKE: a gap
        ev(99, "ADMIT", kind="ISSUE"),                # issues are not pull requests
    ]
    log = (
        "\x01c3\tMerge pull request #12 from x/z\nz1-inbox/2026-11-20/Q-DEMO-02.md\n"
        "\x01c2\tMerge pull request #11 from x/y\nz1-inbox/2026-11-20/Q-DEMO-01.md\n"
        "\x01c1\tMerge pull request #5 from x/w\nREADME.md\n"
    )
    merged, carried = parse_merge_log(log)
    rulings = ruling_prs({
        "z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md":
            "# R\n\n## Q-DEMO-01 — ACCEPT\n\n- **Ratified by merge:** pull request #11 (u) merged\n"
            "\n## Q-OLD-01 — ACCEPT\n\nsigned by ratify.py\n",
    })
    candidates = {
        "Q-DEMO-01": {"status": "ratified", "z2_hash": "abc"},
        "Q-DEMO-02": {"status": "awaiting_z2"},
        "Q-OLD-01": {"status": "ratified", "z2_hash": "def"},
    }
    g = build_graph(events=events, merged=merged, carried=carried,
                    candidates=candidates, rulings=rulings)
    page = render_markdown(g, ledger_ref="fixture", main_ref="fixture")
    checks = [
        ("merge order is oldest first", merged == [5, 11, 12]),
        ("issue events are not pull requests", 99 not in {r["pr"] for r in g["rows"]}),
        ("rows in ledger order", [r["pr"] for r in g["rows"]] == [10, 11, 12]),
        ("gap found for a merged PR ending in REVOKE", g["gaps"] == [{"pr": 12, "last": "REVOKE"}]),
        ("an unmerged voided PR is not a gap", 10 not in {x["pr"] for x in g["gaps"]}),
        ("clean PR is not a gap", 11 not in {x["pr"] for x in g["gaps"]}),
        ("ruling PR parsed", rulings["Q-DEMO-01"]["pr"] == 11 and rulings["Q-OLD-01"]["pr"] is None),
        ("block carries its pull requests in merge order", {b["q_id"]: b["prs"] for b in g["blocks"]}["Q-DEMO-02"] == [12]),
        ("ruled PR is found in the ledger", {b["q_id"]: b["ruled_pr_admitted"] for b in g["blocks"]}["Q-DEMO-01"] is True),
        ("old ruling has no PR", {b["q_id"]: b["ruled_by_pr"] for b in g["blocks"]}["Q-OLD-01"] is None),
        ("page states it has no authority", "authority_effect: NONE" in page),
        ("page prints no clock", not re.search(r"\d{4}-\d{2}-\d{2}T|\bUTC\b", page)),
        ("page does not guess a cause for a gap", "common reading" not in page.lower()),
    ]
    ok = True
    for name, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok &= bool(passed)
    return ok


# --------------------------------------------------------------------------- cli

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("command", nargs="?", default="render", choices=["render"])
    ap.add_argument("--stdout", action="store_true", help="print the page instead of writing it")
    ap.add_argument("--ledger-ref", default=DEFAULT_LEDGER_REF)
    ap.add_argument("--ledger", default=None, metavar="PATH")
    ap.add_argument("--main-ref", default=DEFAULT_MAIN_REF)
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args(argv)
    if args.smoke_test:
        ok = run_smoke_test()
        print("smoke test:", "OK" if ok else "FAILED")
        return 0 if ok else 1
    graph = build_graph(**load_sources(args.ledger_ref, args.main_ref, args.ledger))
    page = render_markdown(
        graph, ledger_ref=args.ledger or args.ledger_ref, main_ref=args.main_ref,
    )
    if args.stdout:
        sys.stdout.write(page)
    else:
        (ROOT / PAGE).write_text(page, encoding="utf-8")
        print(f"wrote {PAGE}: {graph['event_count']} events, {graph['pr_count']} pull requests, "
              f"{len(graph['gaps'])} gap(s), {len(graph['blocks'])} block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
