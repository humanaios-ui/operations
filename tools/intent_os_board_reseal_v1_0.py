#!/usr/bin/env python3
"""intent_os_board_reseal — re-seal the Intent-OS board's *mechanical* seals after a merge; refuse the rest.
Builder v1.7 compliant · governance_tool
HumanAIOS · S-091726-01

Every merge that touches a sealed file makes the board STALE by design (runbook §6). Some of those
files change on every session by construction — the inbox index, the append-only registry and ledgers,
the priority queue — and re-hashing them is a fetch, not a judgement. Others (a tool, a workflow, the
graph, a ruling file) changed because someone changed their meaning, and only a human re-read may say
what the new bytes mean. This tool draws that line in code:

  * MECHANICAL paths (below) that DRIFT are re-hashed; the seal's description gains
    "(re-sealed <date> at <head>; content changed, description not re-read)" so nobody mistakes a hash
    refresh for a read. `read.against` moves to HEAD (the re-hash is a fetch at HEAD) and `rev` advances,
    strictly, so an open browser copy loads the new data on its next restore (taps are kept — the
    board's own rule). `read.date` is never touched: it records the last human read, and this is not one.
    A seal that said ABSENT and now finds a file is an appearance, not a re-hash: NEEDS-HUMAN.
  * anything else that DRIFTs / is MISSING / NOT-IN-HISTORY → REFUSED: exit 2, nothing written, the rows
    listed. That is a re-read for a Z1 session, not a job.

The checker (intent_os_board_check_v1_0.py) still decides HOLDS/STALE; this tool never marks its own work.

Usage:
  python3 tools/intent_os_board_reseal_v1_0.py --check          # what would change; exit 0 nothing / 1 mechanical-only / 2 needs a human
  python3 tools/intent_os_board_reseal_v1_0.py --apply          # write the mechanical re-seals (refuses if anything else drifted)
  python3 tools/intent_os_board_reseal_v1_0.py --json ...
  python3 tools/intent_os_board_reseal_v1_0.py --self-test

No network. Deps: git on PATH; the checker beside it.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

TOOL_NAME = "intent_os_board_reseal"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-091726-01"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join("ui", "intent-os-humanaios-v3_3.html")
CHECKER = os.path.join("tools", "intent_os_board_check_v1_0.py")

# Files whose bytes change by construction on ordinary governance work. A hash refresh here is a fetch.
MECHANICAL = (
    "z1-inbox/INDEX.yaml",
    "REGISTERED.md",
    "PRIORITY_QUEUE.md",
    "ledgers/NF_LEDGER.jsonl",
    "ledgers/RESOURCE_LEDGER.jsonl",
    "Z1_INBOX_INDEX.md",
    "TOOLS_MANIFEST.md",
    "CONTROLLED_DOCUMENTS.md",
)
RESEAL_NOTE_RE = re.compile(r"\s*\((?:re-)?sealed [^)]*\)$")
HUMANAIOS_RE = re.compile(r"(const\s+HUMANAIOS\s*=\s*\{)(.*?)(\n\};)", re.S)


def load_checker(root: str):
    spec = importlib.util.spec_from_file_location("intent_os_board_check", os.path.join(root, CHECKER))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def head_short(root: str) -> str:
    r = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def plan(root: str, board: str) -> dict:
    """Classify the checker's report: which drifted rows are mechanical, which need a human."""
    chk = load_checker(root)
    rep = chk.run(board, root)
    mech, human = [], []
    for r in rep["seals"]:
        if r["status"] in ("DRIFT", "MISSING", "NOT-IN-HISTORY", "UNVERIFIABLE"):
            # a hash-to-hash DRIFT on a mechanical path is a job's; a seal that said ABSENT and now
            # finds a file (DRIFT with no observed hash) is an appearance, and a human's
            mechanical = r.get("path") in MECHANICAL and r["status"] == "DRIFT" and bool(r.get("observed"))
            (mech if mechanical else human).append(r)
    for b in rep.get("bad", []):
        if b.get("artifact") in ("read.against", "HUMANAIOS dataset", "seals"):
            human.append(b)
    ra = rep.get("read_against") or {}
    behind = ra.get("behind_head")
    return {"verdict": rep["verdict"], "mechanical": mech, "human": human, "read_against": ra,
            "behind_head": behind, "head": head_short(root),
            "outcome": "HOLDS" if rep["verdict"] == "HOLDS" else ("MECHANICAL" if not human else "NEEDS-HUMAN")}


def _seal_line_re(path: str) -> re.Pattern:
    return re.compile(r'(\{\s*artifact\s*:\s*")((?:[^"\\]|\\.)*)("\s*,\s*sha\s*:\s*")([^"]*)("\s*,\s*path\s*:\s*"' + re.escape(path) + r'"\s*\})')


def apply(root: str, board: str, p: dict, today: str | None = None) -> dict:
    """Rewrite only the mechanical rows, read.against and rev inside the HUMANAIOS block. Refuses otherwise."""
    if p["outcome"] != "MECHANICAL":
        return {"applied": False, "why": p["outcome"], "changed": []}
    today = today or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    head = p["head"]
    src = open(os.path.join(root, board), encoding="utf-8").read()
    m = HUMANAIOS_RE.search(src)
    if not m:
        return {"applied": False, "why": "no HUMANAIOS block", "changed": []}
    blk = m.group(2)
    changed = []
    for r in p["mechanical"]:
        rx = _seal_line_re(r["path"])
        mm = rx.search(blk)
        if not mm:
            return {"applied": False, "why": f"seal row for {r['path']} not found in a rewritable form", "changed": []}
        desc = RESEAL_NOTE_RE.sub("", mm.group(2).replace('\\"', '"'))
        desc = f"{desc} (re-sealed {today} at {head}; content changed, description not re-read)".replace('"', '\\"')
        blk = blk[:mm.start()] + mm.group(1) + desc + mm.group(3) + r["observed"] + mm.group(5) + blk[mm.end():]
        changed.append({"path": r["path"], "from": r["sha"], "to": r["observed"]})
    # read.against: "… at <old> (…" → "… at <head> (…"; the old sha joins the prior-reads list if one exists
    old = (p.get("read_against") or {}).get("sha")
    if old and old != head:
        blk, n = re.subn(r'(against\s*:\s*"[^"]*?\bat\s+)' + re.escape(old) + r'\b', r'\g<1>' + head, blk, count=1)
        if n:
            blk = re.sub(r'(prior reads at [^;"]*?)(;|\))', lambda mm: f"{mm.group(1)}, {old}{mm.group(2)}" if old not in mm.group(1) else mm.group(0), blk, count=1)
            changed.append({"read.against": old, "to": head})
    # rev must strictly increase so a saved older copy in a browser is superseded on restore(): the
    # board compares rev strings lexically. ISO stamps sort; two applies inside one second, or a clock
    # that went backwards, get a zero-padded ordinal suffix instead of a stale rev. read.date is NOT
    # touched: it records the last human read, and this is not one.
    new_rev = {"v": stamp}

    def bump(mm):
        old = mm.group(2)
        if old < stamp:
            new_rev["v"] = stamp
        else:
            base, _, n = old.partition("+")
            new_rev["v"] = f"{base}+{int(n or 0) + 1:03d}"
        return f'{mm.group(1)}{new_rev["v"]}{mm.group(3)}'
    blk = re.sub(r'(\brev\s*:\s*")([^"]*)(")', bump, blk, count=1)
    out = src[:m.start()] + m.group(1) + blk + m.group(3) + src[m.end():]
    open(os.path.join(root, board), "w", encoding="utf-8").write(out)
    after = load_checker(root).run(board, root)
    return {"applied": True, "changed": changed, "rev": new_rev["v"], "verdict_after": after["verdict"]}


def print_plan(p: dict) -> None:
    ra = p.get("read_against") or {}
    print(f"board verdict: {p['verdict']} · read.against {ra.get('sha')} → {ra.get('status')} · {p.get('behind_head')} behind HEAD {p['head']}")
    for r in p["mechanical"]:
        print(f"  MECHANICAL  {r['path']:<32} {r['sha'][:16]} → {r.get('observed', '')[:16]}")
    for r in p["human"]:
        print(f"  NEEDS-HUMAN {str(r.get('path') or r.get('artifact')):<32} {r['status']}")
    print("outcome:", p["outcome"])


def run_smoke_test() -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        os.makedirs(os.path.join(td, "tools")); os.makedirs(os.path.join(td, "ui")); os.makedirs(os.path.join(td, "z1-inbox"))
        open(os.path.join(td, "tools", "intent_os_board_check_v1_0.py"), "w").write(open(os.path.join(ROOT, CHECKER), encoding="utf-8").read())
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "w").write("a: 1\n")
        open(os.path.join(td, "REGISTERED.md"), "w").write("reg v1\n")
        open(os.path.join(td, "tools", "x.py"), "w").write("print(1)\n")
        subprocess.run(["git", "-C", td, "add", "-A"], check=True)
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "seed"], check=True)
        chk = load_checker(td)
        h = lambda p: chk.sha256_prefix(os.path.join(td, p), 16)  # noqa: E731
        head0 = head_short(td)

        def board(idx, reg, x, against):
            return ('const HUMANAIOS = {\n rev:"2026-09-16",\n read:{board:"Live", date:"2026-09-16", against:"main at ' + against + ' (prior reads at aaaaaaa; d17 ruled)"},\n'
                    ' seals:[\n'
                    f'  {{artifact:"z1-inbox/INDEX.yaml (43 candidates)", sha:"{idx}", path:"z1-inbox/INDEX.yaml"}},\n'
                    f'  {{artifact:"REGISTERED.md (re-sealed 2026-09-16 at 0749022)", sha:"{reg}", path:"REGISTERED.md"}},\n'
                    f'  {{artifact:"x.py — a tool", sha:"{x}", path:"tools/x.py"}},\n'
                    ' ]\n};\n')
        bp = os.path.join(td, "ui", "b.html")
        open(bp, "w").write(board(h("z1-inbox/INDEX.yaml"), h("REGISTERED.md"), h("tools/x.py"), head0))
        p = plan(td, "ui/b.html")
        ok &= p["outcome"] == "HOLDS"; print("  clean board → HOLDS, nothing to do:", p["outcome"])
        # mechanical drift only: inbox + registry change, one more commit
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "a").write("b: 2\n"); open(os.path.join(td, "REGISTERED.md"), "a").write("F-99\n")
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-am", "inbox"], check=True)
        head1 = head_short(td)
        p = plan(td, "ui/b.html")
        ok &= p["outcome"] == "MECHANICAL" and {r["path"] for r in p["mechanical"]} == {"z1-inbox/INDEX.yaml", "REGISTERED.md"} and not p["human"]
        print("  inbox + registry drift → MECHANICAL (2 rows):", p["outcome"])
        a = apply(td, "ui/b.html", p, today="2026-09-17")
        src = open(bp).read()
        ok &= (a["applied"] and a["verdict_after"] == "HOLDS" and len(a["changed"]) == 3
               and src.count("re-sealed 2026-09-17 at " + head1) == 2 and "re-sealed 2026-09-16 at 0749022" not in src
               and f"main at {head1} (prior reads at aaaaaaa, {head0};" in src and 'date:"2026-09-16"' in src
               and re.search(r'rev:"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"', src) is not None and "x.py — a tool" in src)
        rev1 = a["rev"]
        print("  --apply: 2 seals re-hashed, notes replaced not stacked, read.against moved, prior read kept, rev advanced, read.date untouched, HOLDS:", "OK" if ok else "FAIL")
        # a second apply on a holding board is a no-op
        a2 = apply(td, "ui/b.html", plan(td, "ui/b.html"))
        ok &= not a2["applied"] and a2["why"] == "HOLDS"; print("  --apply on HOLDS → nothing written:", not a2["applied"])
        # rev is strictly monotonic even inside one second / with a rev already ahead of the clock
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "a").write("d: 4\n")
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-am", "inbox2"], check=True)
        cur = open(bp).read()
        open(bp, "w").write(re.sub(r'rev:"[^"]*"', 'rev:"2999-01-01T00:00:00Z"', cur, count=1))
        a_m = apply(td, "ui/b.html", plan(td, "ui/b.html"))
        ok &= a_m["applied"] and a_m["rev"] == "2999-01-01T00:00:00Z+001" and a_m["rev"] > "2999-01-01T00:00:00Z"
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "a").write("e: 5\n")
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-am", "inbox3"], check=True)
        a_m2 = apply(td, "ui/b.html", plan(td, "ui/b.html"))
        ok &= a_m2["applied"] and a_m2["rev"] == "2999-01-01T00:00:00Z+002" and a_m2["rev"] > a_m["rev"] and rev1 < a_m["rev"]
        print("  rev already ahead of the clock → +001, then +002, each lexically greater:", "OK" if a_m2["rev"] == "2999-01-01T00:00:00Z+002" else "FAIL")
        # a seal that said ABSENT and now finds a file on a mechanical path is an appearance, not a re-hash
        open(bp, "w").write(board(h("z1-inbox/INDEX.yaml"), h("REGISTERED.md"), h("tools/x.py"), head_short(td)).replace(
            ' ]\n};', '  {artifact:"PRIORITY_QUEUE.md (absent)", sha:"ABSENT-20260901", path:"PRIORITY_QUEUE.md"},\n ]\n};'))
        open(os.path.join(td, "PRIORITY_QUEUE.md"), "w").write("q\n")
        p_abs = plan(td, "ui/b.html")
        a_abs = apply(td, "ui/b.html", p_abs)
        ok &= p_abs["outcome"] == "NEEDS-HUMAN" and [r.get("path") for r in p_abs["human"]] == ["PRIORITY_QUEUE.md"] and not a_abs["applied"]
        print("  ABSENT seal now present on a mechanical path → NEEDS-HUMAN, refused:", p_abs["outcome"])
        os.remove(os.path.join(td, "PRIORITY_QUEUE.md"))
        open(bp, "w").write(board(h("z1-inbox/INDEX.yaml"), h("REGISTERED.md"), h("tools/x.py"), head_short(td)))
        # non-mechanical drift: the tool changes → refused, nothing written even though the inbox also drifted
        open(os.path.join(td, "tools", "x.py"), "w").write("print(2)\n"); open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "a").write("c: 3\n")
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-am", "tool"], check=True)
        before = open(bp).read()
        p = plan(td, "ui/b.html")
        a3 = apply(td, "ui/b.html", p)
        ok &= p["outcome"] == "NEEDS-HUMAN" and [r["path"] for r in p["human"]] == ["tools/x.py"] and len(p["mechanical"]) == 1 and not a3["applied"] and open(bp).read() == before
        print("  tool drift + inbox drift → NEEDS-HUMAN, --apply refused, board untouched:", p["outcome"])
        # a mechanical file that went MISSING is a human matter too
        os.remove(os.path.join(td, "tools", "x.py")); open(os.path.join(td, "tools", "x.py"), "w").write("print(1)\n")
        os.remove(os.path.join(td, "REGISTERED.md"))
        p = plan(td, "ui/b.html")
        ok &= p["outcome"] == "NEEDS-HUMAN" and any(r.get("path") == "REGISTERED.md" and r["status"] == "MISSING" for r in p["human"])
        print("  mechanical path MISSING → NEEDS-HUMAN:", p["outcome"])
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", "--input", dest="root", default=ROOT, help="repository root (--input is the tools/README.md alias)")
    ap.add_argument("--board", default=BOARD)
    ap.add_argument("--check", action="store_true", help="classify only (default)")
    ap.add_argument("--apply", action="store_true", help="write the mechanical re-seals")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", "--smoke-test", dest="self_test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if run_smoke_test() else 2
    p = plan(a.root, a.board)
    result = {"plan": p}
    if a.apply:
        result["apply"] = apply(a.root, a.board, p)
    if a.json:
        print(json.dumps(result, indent=1))
    else:
        print_plan(p)
        if a.apply:
            r = result["apply"]
            print("apply:", "written — " + ", ".join(c.get("path") or "read.against" for c in r["changed"]) + f" · verdict after: {r['verdict_after']}" if r["applied"] else f"refused ({r['why']})")
    if p["outcome"] == "HOLDS":
        return 0
    if p["outcome"] == "MECHANICAL":
        return 0 if (a.apply and result["apply"]["applied"] and result["apply"]["verdict_after"] == "HOLDS") else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
