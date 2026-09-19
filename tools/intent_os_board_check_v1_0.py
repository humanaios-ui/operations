#!/usr/bin/env python3
"""intent_os_board_check — verify the Intent-OS board's "verified records" against the tree.
Builder v1.7 compliant · validation_tool
HumanAIOS · S-091426-01

The board (ui/intent-os-humanaios-v3_3.html) renders a `seals` table: each row is a
fingerprint of a real file or commit that the board's green steps rest on. The board's
own rule is "a step only turns green when it's verified, not when someone says it's
done" — but until now nothing re-checked the seals after they were typed in, so a
board re-read was a memory exercise. This makes it a fetch.

What it checks, for every seal in the HUMANAIOS dataset:
  * `path:` given and the file exists  → sha256 prefix must match `sha` → MATCH / DRIFT
  * `path:` given and the file is gone → ABSENT-CONFIRMED if the seal says ABSENT, else MISSING
  * artifact starts with "commit" and `sha` is hex → `git cat-file -e` → PRESENT / NOT-IN-HISTORY
  * anything else (ratification slugs, out-of-tree records) → UNCHECKED, listed, never counted green
It also resolves the commit named in `read.against` ("… at <sha>") the same way.

Exit 0 = every checkable seal holds. Exit 2 = at least one DRIFT / MISSING / NOT-IN-HISTORY:
the board is stale and must be re-read before anything on it is cited.

Usage:
  python3 tools/intent_os_board_check_v1_0.py                      # table
  python3 tools/intent_os_board_check_v1_0.py --json               # machine-readable
  python3 tools/intent_os_board_check_v1_0.py --board ui/other.html
  python3 tools/intent_os_board_check_v1_0.py --self-test

No network. Read-only. Deps: none beyond git on PATH.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile

TOOL_NAME = "intent_os_board_check"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "S-091426-01"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BOARD = os.path.join("ui", "intent-os-humanaios-v3_3.html")

# One seal per line in the board's JS: {artifact:"…", sha:"…"[, path:"…"]}
SEAL_RE = re.compile(r'\{\s*artifact\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*sha\s*:\s*"([^"]*)"(?:\s*,\s*path\s*:\s*"([^"]*)")?\s*\}')
HEX_RE = re.compile(r"^[0-9a-f]{7,64}$")
AGAINST_RE = re.compile(r'against\s*:\s*"[^"]*?\bat\s+([0-9a-f]{7,40})\b')
HUMANAIOS_RE = re.compile(r"const\s+HUMANAIOS\s*=\s*\{(.*?)\n\};", re.S)

BAD = {"DRIFT", "MISSING", "NOT-IN-HISTORY", "UNVERIFIABLE"}


def sha256_prefix(path: str, n: int) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def commit_exists(sha: str, root: str) -> bool:
    """True only if the commit is REACHABLE from HEAD. `git cat-file -e` would also say yes to a
    dangling object left behind by a history reset — which is exactly the case the board must not
    count as verified."""
    r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=root,
                       capture_output=True, text=True)
    return r.returncode == 0


def extract(board_src: str) -> tuple[list[dict], str | None]:
    """Seals + the `read.against` commit from the HUMANAIOS dataset only (not BLANK/EXAMPLE)."""
    m = HUMANAIOS_RE.search(board_src)
    block = m.group(1) if m else board_src
    seals = [{"artifact": a.replace('\\"', '"'), "sha": s, "path": p or None}
             for a, s, p in SEAL_RE.findall(block)]
    ag = AGAINST_RE.search(block)
    return seals, (ag.group(1) if ag else None)


def check_seal(seal: dict, root: str) -> dict:
    art, sha, path = seal["artifact"], seal["sha"], seal.get("path")
    out = dict(seal)
    if path:
        full = os.path.join(root, path)
        if os.path.isfile(full):
            if sha.upper().startswith("ABSENT"):
                out.update(status="DRIFT", detail="seal says ABSENT but the file exists now")
            elif HEX_RE.match(sha):
                got = sha256_prefix(full, len(sha))
                out.update(status="MATCH" if got == sha else "DRIFT", observed=got)
            else:
                # A path-bearing row claims to be checkable. A fingerprint that cannot be compared
                # is a broken seal, not an informational one — it must not let the board HOLD.
                out.update(status="UNVERIFIABLE", detail="sha is not hex; file exists but cannot be compared")
        else:
            out.update(status="ABSENT-CONFIRMED" if sha.upper().startswith("ABSENT") else "MISSING")
        return out
    if art.lower().startswith("commit") and HEX_RE.match(sha):
        out.update(status="PRESENT" if commit_exists(sha, root) else "NOT-IN-HISTORY")
        return out
    out.update(status="UNCHECKED", detail="no path; not a commit — listed, not counted")
    return out


def run(board: str, root: str) -> dict:
    src = open(os.path.join(root, board), encoding="utf-8").read()
    has_dataset = HUMANAIOS_RE.search(src) is not None
    seals, against = extract(src)
    rows = [check_seal(s, root) for s in seals]
    against_row = None
    if against:
        against_row = {"sha": against,
                       "status": "PRESENT" if commit_exists(against, root) else "NOT-IN-HISTORY"}
        if against_row["status"] == "PRESENT":
            # How far the read is behind HEAD. Informational: a board re-sealed after a merge is
            # still a HOLDS board, but a read that is many commits old is a re-read waiting to happen.
            r = subprocess.run(["git", "rev-list", "--count", f"{against}..HEAD"], cwd=root,
                               capture_output=True, text=True)
            against_row["behind_head"] = int(r.stdout.strip() or 0) if r.returncode == 0 else None
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    bad = [r for r in rows if r["status"] in BAD]
    if against_row and against_row["status"] in BAD:
        bad.append({"artifact": "read.against", **against_row})
    # Fail closed. A board with no dataset, no seals, or no `read.against` commit has verified
    # nothing, and "nothing checked" must never read as HOLDS.
    checkable = [r for r in rows if r["status"] not in ("UNCHECKED",)]
    if not has_dataset:
        bad.append({"artifact": "HUMANAIOS dataset", "status": "MISSING", "detail": "no `const HUMANAIOS = {…};` block found"})
    if not checkable:
        bad.append({"artifact": "seals", "status": "MISSING", "detail": "no seal with a path or a commit sha found"})
    if against_row is None:
        bad.append({"artifact": "read.against", "status": "MISSING", "detail": "no `at <sha>` in read.against"})
    return {"board": board, "read_against": against_row, "counts": counts, "seals": rows,
            "verdict": "STALE" if bad else "HOLDS", "bad": bad}


def print_table(rep: dict) -> None:
    print(f"board: {rep['board']}")
    if rep["read_against"]:
        ra = rep["read_against"]; behind = ra.get("behind_head")
        print(f"read.against: {ra['sha']} → {ra['status']}"
              + (f" · {behind} commit(s) behind HEAD" if behind else " · at HEAD" if behind == 0 else ""))
    print(f"{'status':<17} {'sha':<18} {'observed':<18} artifact")
    for r in rep["seals"]:
        print(f"{r['status']:<17} {r['sha'][:16]:<18} {r.get('observed', '')[:16]:<18} {r['artifact']}")
    print("counts:", ", ".join(f"{k}={v}" for k, v in sorted(rep["counts"].items())))
    print("verdict:", rep["verdict"])


def run_smoke_test() -> bool:
    """Plant a board with every classification and check each lands where it should."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-q", "--allow-empty", "-m", "seed"], check=True)
        head = subprocess.run(["git", "-C", td, "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
        # A commit that EXISTS in the object store but is not reachable from HEAD — what a history
        # reset leaves behind. `git cat-file -e` says yes to it; the checker must say NOT-IN-HISTORY.
        tree = subprocess.run(["git", "-C", td, "rev-parse", "HEAD^{tree}"], capture_output=True,
                              text=True, check=True).stdout.strip()
        dangling = subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t",
                                   "commit-tree", tree, "-m", "orphan"], capture_output=True,
                                  text=True, check=True).stdout.strip()
        os.makedirs(os.path.join(td, "ui"))
        open(os.path.join(td, "a.txt"), "w").write("alpha\n")
        open(os.path.join(td, "b.txt"), "w").write("beta\n")
        open(os.path.join(td, "c.txt"), "w").write("gamma\n")
        a_sha = sha256_prefix(os.path.join(td, "a.txt"), 16)
        html = (
            'const EXAMPLE = {\n seals:[{artifact:"decoy", sha:"deadbeefdeadbeef", path:"a.txt"}]\n};\n'
            'const HUMANAIOS = {\n read:{board:"Live", date:"2026-09-14", against:"main at ' + head[:12] + '"},\n'
            ' seals:[\n'
            f'  {{artifact:"a (match)", sha:"{a_sha}", path:"a.txt"}},\n'
            '  {artifact:"b (drift)", sha:"0000000000000000", path:"b.txt"},\n'
            '  {artifact:"c (was absent, now present)", sha:"ABSENT-20260908", path:"c.txt"},\n'
            '  {artifact:"gone (missing)", sha:"1111111111111111", path:"nope.txt"},\n'
            '  {artifact:"still absent", sha:"ABSENT-20260908", path:"never.txt"},\n'
            f'  {{artifact:"commit head", sha:"{head}"}},\n'
            '  {artifact:"commit ghost", sha:"abcdef0123456789abcdef0123456789abcdef01"},\n'
            f'  {{artifact:"commit dangling (exists, unreachable)", sha:"{dangling}"}},\n'
            '  {artifact:"bad fingerprint (path, non-hex)", sha:"not-a-hash", path:"a.txt"},\n'
            '  {artifact:"OI-G1 ratification", sha:"molt-tiers-slug-20260906"}\n'
            ' ]\n};\n'
        )
        open(os.path.join(td, "ui", "board.html"), "w").write(html)
        rep = run(os.path.join("ui", "board.html"), td)
        got = {r["artifact"]: r["status"] for r in rep["seals"]}
        want = {"a (match)": "MATCH", "b (drift)": "DRIFT",
                "c (was absent, now present)": "DRIFT", "gone (missing)": "MISSING",
                "still absent": "ABSENT-CONFIRMED", "commit head": "PRESENT",
                "commit ghost": "NOT-IN-HISTORY",
                "commit dangling (exists, unreachable)": "NOT-IN-HISTORY",
                "bad fingerprint (path, non-hex)": "UNVERIFIABLE",
                "OI-G1 ratification": "UNCHECKED"}
        ok = got == want and "decoy" not in got and rep["verdict"] == "STALE" \
            and rep["read_against"]["status"] == "PRESENT"
        for k in want:
            print(f"  {k:<40} → {got.get(k)}  {'OK' if got.get(k) == want[k] else 'FAIL'}")
        print("  EXAMPLE dataset ignored →", "OK" if "decoy" not in got else "FAIL")
        # a fully-holding board must come back HOLDS
        clean = html.replace('{artifact:"b (drift)", sha:"0000000000000000", path:"b.txt"},\n', "") \
            .replace('{artifact:"c (was absent, now present)", sha:"ABSENT-20260908", path:"c.txt"},\n', "") \
            .replace('{artifact:"gone (missing)", sha:"1111111111111111", path:"nope.txt"},\n', "") \
            .replace('{artifact:"commit ghost", sha:"abcdef0123456789abcdef0123456789abcdef01"},\n', "") \
            .replace(f'{{artifact:"commit dangling (exists, unreachable)", sha:"{dangling}"}},\n', "") \
            .replace('{artifact:"bad fingerprint (path, non-hex)", sha:"not-a-hash", path:"a.txt"},\n', "")
        open(os.path.join(td, "ui", "board.html"), "w").write(clean)
        clean_rep = run(os.path.join("ui", "board.html"), td)
        holds = clean_rep["verdict"] == "HOLDS"
        print("  clean board → HOLDS:", "OK" if holds else "FAIL")
        ok = ok and holds
        # read.against distance: a read at HEAD is 0 behind and the table says "at HEAD"; after one
        # more commit on the branch the same read is 1 behind, still PRESENT, still HOLDS, and the
        # table says so — the visibility must not silently disappear.
        def table_line(rep: dict) -> str:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                print_table(rep)
            return next(l for l in buf.getvalue().splitlines() if l.startswith("read.against:"))
        at_head = clean_rep["read_against"].get("behind_head") == 0 and table_line(clean_rep).endswith("· at HEAD")
        print("  read.against at HEAD → behind_head 0, table 'at HEAD':", "OK" if at_head else "FAIL")
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-q", "--allow-empty", "-m", "one more"], check=True)
        older = run(os.path.join("ui", "board.html"), td)
        ra = older["read_against"]
        behind_ok = (ra["status"] == "PRESENT" and ra.get("behind_head") == 1
                     and older["verdict"] == "HOLDS"
                     and table_line(older).endswith("· 1 commit(s) behind HEAD"))
        print("  read.against 1 commit old → PRESENT, behind_head 1, HOLDS, table says so:",
              "OK" if behind_ok else "FAIL")
        ok = ok and at_head and behind_ok
        # fail closed: no dataset / no seals / no read.against must each be STALE, never HOLDS
        for label, variant in (
            ("no HUMANAIOS block", clean.replace("const HUMANAIOS", "const SOMETHING")),
            ("no checkable seals", clean.replace(f'  {{artifact:"a (match)", sha:"{a_sha}", path:"a.txt"}},\n', "")
                                        .replace('  {artifact:"still absent", sha:"ABSENT-20260908", path:"never.txt"},\n', "")
                                        .replace(f'  {{artifact:"commit head", sha:"{head}"}},\n', "")),
            ("no read.against commit", clean.replace('against:"main at ' + head[:12] + '"', 'against:"memory"')),
        ):
            open(os.path.join(td, "ui", "board.html"), "w").write(variant)
            v = run(os.path.join("ui", "board.html"), td)["verdict"]
            print(f"  fail-closed · {label:<24} → {v}  {'OK' if v == 'STALE' else 'FAIL'}")
            ok = ok and v == "STALE"
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--board", "--input", dest="board", default=DEFAULT_BOARD,
                    help="board HTML, relative to repo root (--input is the tools/README.md alias)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", "--smoke-test", dest="self_test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if run_smoke_test() else 2
    rep = run(a.board, a.root)
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print_table(rep)
    return 0 if rep["verdict"] == "HOLDS" else 2


if __name__ == "__main__":
    sys.exit(main())
