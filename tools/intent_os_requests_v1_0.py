#!/usr/bin/env python3
"""intent_os_requests — read the agent bus: every REQ- record in z1-inbox, its hash, its stage.
Builder v1.7 compliant · governance_tool
HumanAIOS · S-091726-01

The relay's `/task` (decision_relay.py v0.4) lands a request as a RECORD: `z1-inbox/<day>/REQ-<yyyymmdd>-<nn>.md`
with the ask, a hashed request block and an empty `## Fulfilment`. A worker takes it by filling that section in
its own PR. Nothing else tracks the request — no board, no ticket — so this tool is the read: it walks the inbox,
recomputes each record's hashes, and derives where each request stands from the Fulfilment fields alone:

  requested   Fulfilment empty
  taken       taken_by filled
  pr          pr filled (taken_by too)
  merged      merged filled (pr and taken_by too)
  inconsistent  a later field filled with an earlier one empty — e.g. `merged` with no `pr`

No stage is time-based. A request is not "late"; it is where its Fulfilment says it is (resource-based: work is
done when the resources to do it exist). `--check` is red only on facts a reader can verify: a hash that does not
recompute, an ask that does not match its `ask_sha256`, an id that does not match its filename, an inconsistent
Fulfilment, or a record the inbox index does not carry (the coverage rule's own failure mode).

The dashboard (ui/intent-os-test-dashboard-v1_0.html § Agent requests) shows the `--json` output the harness embeds,
and can re-fetch the same records from `main` on click — recomputing the same hashes in the browser, so a live row
is never green on this tool's word alone.

Usage:
  python3 tools/intent_os_requests_v1_0.py              # table
  python3 tools/intent_os_requests_v1_0.py --json       # the snapshot the harness embeds (schema intentos/requests_v1)
  python3 tools/intent_os_requests_v1_0.py --check      # exit 0 all records verify · 2 any error
  python3 tools/intent_os_requests_v1_0.py --self-test  # fixtures written by the relay's own writer; every classification fires

No network. Deps: none beyond the standard library (the self-test imports tools/decision_relay.py, DRY_RUN).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

TOOL_NAME = "intent_os_requests"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-091726-01"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join("z1-inbox", "INDEX.yaml")
SCHEMA = "intentos/requests_v1"
STAGES = ("requested", "taken", "pr", "merged")
FIELDS = ("taken_by", "pr", "merged", "at")
REQ_ID_RE = re.compile(r"REQ-\d{8}-\d{2,}")
SOURCE = {"repo": "humanaios-ui/operations", "ref": "main"}  # what the dashboard's live fetch reads


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon_ask(ask: str) -> str:
    """Byte-identical to decision_relay.canon_ask: lines right-stripped, outer whitespace stripped."""
    return "\n".join(ln.rstrip() for ln in str(ask).strip().splitlines())


def between(text: str, start: str, end: str | None = None) -> str | None:
    """The record's section under `## <start>`, up to its known next delimiter `## <end>` (or the end of the file).
    Known delimiters only: an ask is verbatim user text, so a `## Something` inside it must not end the section."""
    m = re.search(rf"(?m)^## {re.escape(start)}\n", text)
    if not m:
        return None
    s = m.end()
    if end is None:
        return text[s:]
    e = re.search(rf"(?m)^## {re.escape(end)}\n", text[s:])
    return text[s:s + e.start()] if e else text[s:]


BLOCK_FIELDS = ("title", "lane", "wants", "tagline", "at")


def block_fields(block: str) -> dict:
    """The one-line metadata inside the hashed block, as the relay writes it (`tagline` carries its '(as sent; unverified)' tail)."""
    out = {}
    for k in BLOCK_FIELDS:
        m = re.search(rf"^  {k}: (.*)$", block, re.M)
        v = m.group(1) if m else None
        if k == "tagline" and v is not None:
            v = re.sub(r" \(as sent; unverified\)$", "", v)
        out[k] = v
    return out


def parse_record(text: str, path: str) -> dict:
    """One REQ record → fields, hashes recomputed, stage derived. `errors` lists what a reader could not verify."""
    rec: dict = {"path": path, "id": None, "title": None, "at": None, "lane": None, "wants": None, "tagline": None,
                 "header_status": None, "hash": None, "hash_ok": False, "ask_ok": False, "id_ok": False, "meta_ok": False,
                 "taken_by": "", "pr": "", "merged": "", "fulfilled_at": "", "stage": None, "errors": [], "warnings": []}
    fname = re.search(r"(REQ-\d{8}-\d+)\.md$", path)
    file_id = fname.group(1) if fname else None
    h1 = re.match(r"# Agent request (REQ-\d{8}-\d+) — (.*)", text)
    if h1:
        rec["id"], rec["title"] = h1.group(1), h1.group(2).strip()
    else:
        rec["errors"].append("no '# Agent request <id> — <title>' heading")
    for key, name in (("at", "At"), ("lane", "Lane"), ("wants", "Wants"), ("header_status", "Status")):
        m = re.search(rf"^\*\*{name}:\*\* (.*)$", text, re.M)
        rec[key] = m.group(1).strip() if m else None
    m = re.search(r"tagline as sent: `([^`]*)`", text)
    rec["tagline"] = m.group(1) if m else None
    # hashes: the block's sha256 is the record's `hash:`; ask_sha256 inside the block is sha256 of ## Ask, canonicalised
    blk_sec = between(text, "Request block", "Fulfilment") or ""
    b = re.search(r"```\n(REQUEST .*?)```", blk_sec, re.S)
    hl = re.search(r"^hash: `([0-9a-f]{64})`", blk_sec, re.M)
    ask = between(text, "Ask", "Request block")
    if not b:
        rec["errors"].append("no REQUEST block")
    if not hl:
        rec["errors"].append("no hash line")
    if ask is None:
        rec["errors"].append("no ## Ask section")
    if b and hl:
        rec["hash"] = hl.group(1)
        rec["hash_ok"] = sha(b.group(1).encode()) == rec["hash"]
        if not rec["hash_ok"]:
            rec["errors"].append("request block does not hash to the recorded hash")
        bid = re.match(r"REQUEST (REQ-\d{8}-\d+)", b.group(1))
        block_id = bid.group(1) if bid is not None else None
        rec["id_ok"] = block_id is not None and block_id == rec["id"] == file_id
        if not rec["id_ok"]:
            rec["errors"].append(f"id disagrees: file {file_id} · heading {rec['id']} · block {block_id}")
        am = re.search(r"^  ask_sha256: ([0-9a-f]{64})$", b.group(1), re.M)
        if ask is not None and am:
            rec["ask_ok"] = sha(canon_ask(ask).encode()) == am.group(1)
            if not rec["ask_ok"]:
                rec["errors"].append("## Ask does not hash to the block's ask_sha256 (the ask was edited)")
        elif not am:
            rec["errors"].append("block carries no ask_sha256")
        # the header is what a reader sees; the block is what was hashed — they must agree, or the shown metadata is unverified
        bf = block_fields(b.group(1))
        shown = {"title": rec["title"], "lane": rec["lane"], "wants": rec["wants"], "tagline": rec["tagline"], "at": rec["at"]}
        diff = [f"{k} (header {shown[k]!r}, block {bf[k]!r})" for k in BLOCK_FIELDS if shown[k] != bf[k]]
        rec["meta_ok"] = not diff
        if diff:
            rec["errors"].append("header disagrees with the hashed block: " + "; ".join(diff))
    ful = between(text, "Fulfilment")
    if ful is None:
        rec["errors"].append("no ## Fulfilment section")
    else:
        for f in FIELDS:
            m = re.search(rf"^{f}:[ \t]*(.*)$", ful, re.M)
            rec["fulfilled_at" if f == "at" else f] = (m.group(1).strip() if m else "")
    filled = [bool(rec["taken_by"]), bool(rec["pr"]), bool(rec["merged"])]
    n = sum(filled)
    if filled != [True] * n + [False] * (3 - n):
        rec["stage"] = "inconsistent"
        rec["errors"].append("Fulfilment out of order: " + ", ".join(f"{k}={'set' if v else 'empty'}" for k, v in zip(("taken_by", "pr", "merged"), filled)))
    else:
        rec["stage"] = STAGES[n]
    if rec["stage"] == "merged" and (rec["header_status"] or "").upper() == "OPEN":
        rec["warnings"].append("merged, but the header still says **Status:** OPEN")
    if rec["stage"] in ("taken", "pr") and not rec["fulfilled_at"]:
        rec["warnings"].append("taken with no `at:` (who took it is recorded; when is not — fine, noted)")
    return rec


def indexed_paths(root: str) -> set[str] | None:
    """Record paths under the index's `records:` section only (quoted or bare scalars, any indentation) — a REQ path
    listed under `candidates:` or `excluded:` is not coverage. None when the index is missing or has no records: key."""
    try:
        with open(os.path.join(root, INDEX), encoding="utf-8") as fh:
            idx = fh.read()
    except OSError:
        return None
    # the section ends at the next top-level KEY (a letter at column 0); column-0 list items ("- path: …") belong to it
    m = re.search(r"(?ms)^records:[ \t]*\n?(.*?)(?=^[A-Za-z_]|\Z)", idx)
    if not m:
        return None
    return {x.group(1) for x in re.finditer(r'(?m)^\s*-\s+path:\s*"?([^"\n]+?)"?\s*$', m.group(1))}


def snapshot(root: str) -> dict:
    paths = sorted(p for p in glob.glob(os.path.join(root, "z1-inbox", "*", "REQ-*.md")))
    idx = indexed_paths(root)
    index_error = None
    if idx is None:
        if os.path.isdir(os.path.join(root, "z1-inbox")):
            index_error = f"{INDEX} missing or has no records: section — coverage cannot be read"
        idx = set()
    reqs = []
    for p in paths:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        with open(p, encoding="utf-8") as fh:
            rec = parse_record(fh.read(), rel)
        rec["indexed"] = rel in idx
        if not rec["indexed"]:
            rec["errors"].append(f"not under records: in {INDEX} (the coverage rule will refuse this tree)")
        reqs.append(rec)
    counts = {s: sum(1 for r in reqs if r["stage"] == s) for s in (*STAGES, "inconsistent")}
    errors = ([index_error] if index_error else []) + [f"{r['path']}: {e}" for r in reqs for e in r["errors"]]
    warnings = [f"{r['path']}: {w}" for r in reqs for w in r["warnings"]]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False).stdout.strip()
    return {"tool": TOOL_NAME, "version": TOOL_VERSION, "schema": SCHEMA,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "head": head or None, "source": SOURCE, "index": INDEX, "total": len(reqs), "counts": counts,
            "verified": sum(1 for r in reqs if not r["errors"]), "errors": errors, "warnings": warnings,
            "verdict": "OK" if not errors else "ERROR", "requests": reqs}


def print_table(s: dict) -> None:
    print(f"{TOOL_NAME} v{TOOL_VERSION} · {s['generated_at']} · {(s['head'] or '')[:7]} · {s['total']} request(s) · "
          + " · ".join(f"{k} {v}" for k, v in s["counts"].items()))
    if s["requests"]:
        print(f"{'stage':<13} {'id':<18} {'wants':<7} {'hash':<5} {'idx':<4} title")
        for r in s["requests"]:
            print(f"{r['stage']:<13} {r['id'] or '?':<18} {r['wants'] or '—':<7} {'ok' if r['hash_ok'] and r['ask_ok'] else 'BAD':<5} "
                  f"{'yes' if r['indexed'] else 'NO':<4} {(r['title'] or '')[:60]}"
                  + (f"  ← {r['taken_by']}" if r["taken_by"] else "") + (f" · {r['pr']}" if r["pr"] else ""))
    for e in s["errors"]:
        print("ERROR", e)
    for w in s["warnings"]:
        print("warn ", w)
    print("verdict:", s["verdict"], f"({s['verified']}/{s['total']} verify)")


# ---------------------------------------------------------------------------------------------------
# self-test — fixtures come from the relay's own writer, so the parser is proved against the real format
# ---------------------------------------------------------------------------------------------------
def _relay():
    os.environ["DRY_RUN"] = "1"
    spec = importlib.util.spec_from_file_location("decision_relay", os.path.join(ROOT, "tools", "decision_relay.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run_self_test() -> bool:
    ok = True
    relay = _relay()

    def rec(rid: str, title: str, ask: str, wants: str = "pr") -> str:
        d = {"id": rid, "title": title, "ask": relay.canon_ask(ask), "wants": wants, "ts": "2026-09-17T12:00:00Z", "tagline": "Night", "lane": "acat"}
        blk = relay.req_block(d)
        return relay.req_record(d, blk, sha(blk.encode()))

    def fill(text: str, **kv: str) -> str:
        for k, v in kv.items():
            text = re.sub(rf"(?m)^{k}:.*$", f"{k}: {v}", text, count=1)
        return text

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        day = os.path.join(td, "z1-inbox", "2026-09-17")
        os.makedirs(day)
        fresh = rec("REQ-20260917-01", 'Re-read the "ACAT" map: rows 1–12', "Compare the 12 rows.  \n\nSecond paragraph.")
        taken = fill(rec("REQ-20260917-02", "Second", "x"), taken_by="claude-code session_abc", at="2026-09-17T13:00:00Z")
        withpr = fill(rec("REQ-20260917-03", "Third", "x", "answer"), taken_by="Night", pr="https://github.com/humanaios-ui/operations/pull/400", at="2026-09-17T13:10:00Z")
        merged = fill(rec("REQ-20260917-04", "Fourth", "x"), taken_by="local-model", pr="https://github.com/humanaios-ui/operations/pull/401", merged="yes 2026-09-17", at="2026-09-17T14:00:00Z")
        merged_open = merged  # header still says OPEN → a warning, not an error
        bad_order = fill(rec("REQ-20260917-05", "Fifth", "x"), merged="yes")  # merged with no pr / taken_by
        edited_ask = rec("REQ-20260917-06", "Sixth", "the ask").replace("## Ask\n\nthe ask", "## Ask\n\nthe ask, edited")
        edited_block = rec("REQ-20260917-07", "Seventh", "x").replace("  wants: pr", "  wants: ruling")
        wrong_id = rec("REQ-20260917-09", "Ninth", "x")  # written to the -08 filename
        edited_header = rec("REQ-20260917-10", "Tenth", "x").replace("**Wants:** pr", "**Wants:** ruling")  # block still says pr
        heading_ask = rec("REQ-20260917-11", "Eleventh", "first line\n\n## Details\n\nmore")  # written by the writer directly; the ask carries a ## line
        files = {"REQ-20260917-01.md": fresh, "REQ-20260917-02.md": taken, "REQ-20260917-03.md": withpr, "REQ-20260917-04.md": merged_open,
                 "REQ-20260917-05.md": bad_order, "REQ-20260917-06.md": edited_ask, "REQ-20260917-07.md": edited_block, "REQ-20260917-08.md": wrong_id,
                 "REQ-20260917-10.md": edited_header, "REQ-20260917-11.md": heading_ask}
        for name, txt in files.items():
            with open(os.path.join(day, name), "w", encoding="utf-8") as fh:
                fh.write(txt)
        # index: -01..-07, -10, -11 carried under records: (quoted and bare, column 0 and 2-space); -08 listed only under candidates: (not coverage)
        idx = 'version: 1\ncounts: {candidates: 1, records: 9}\ncandidates:\n- q_id: Q-X\n  path: "z1-inbox/2026-09-17/REQ-20260917-08.md"\n  status: awaiting_z2\nrecords:\n'
        idx += ''.join(f'- path: "z1-inbox/2026-09-17/REQ-20260917-0{i}.md"\n  title: "t"\n  note: "n"\n' for i in (1, 2, 3))
        idx += ''.join(f'  - path: z1-inbox/2026-09-17/REQ-20260917-0{i}.md\n    title: t\n    note: n\n' for i in (4, 5, 6, 7))
        idx += ''.join(f'  - path: z1-inbox/2026-09-17/REQ-20260917-{i}.md\n    title: t\n    note: n\n' for i in (10, 11))
        idx += 'excluded: []\n'
        with open(os.path.join(td, INDEX), "w", encoding="utf-8") as fh:
            fh.write(idx)
        s = snapshot(td)
        by = {r["id"] or r["path"]: r for r in s["requests"]}

        def check(label: str, cond: object) -> None:
            nonlocal ok
            cond = bool(cond)
            ok &= cond
            print(f"  {label:<78} {'OK' if cond else 'FAIL'}")

        check("10 records read; stages requested/taken/pr/merged derived from Fulfilment alone",
              s["total"] == 10 and [by[f"REQ-20260917-0{i}"]["stage"] for i in (1, 2, 3, 4)] == list(STAGES))
        check("fresh record: block hash, ask_sha256 (canonicalised, quotes in title), id and header↔block metadata all verify; indexed",
              by["REQ-20260917-01"]["hash_ok"] and by["REQ-20260917-01"]["ask_ok"] and by["REQ-20260917-01"]["id_ok"] and by["REQ-20260917-01"]["meta_ok"]
              and by["REQ-20260917-01"]["indexed"] and not by["REQ-20260917-01"]["errors"] and by["REQ-20260917-01"]["tagline"] == "Night")
        check("edited header (**Wants:** ≠ block's wants) → error; hashes alone would have passed",
              not by["REQ-20260917-10"]["meta_ok"] and by["REQ-20260917-10"]["hash_ok"] and any("header disagrees" in e for e in by["REQ-20260917-10"]["errors"]))
        check("an ask carrying a '## Details' line still verifies (sections end at known delimiters only)",
              by["REQ-20260917-11"]["ask_ok"] and not by["REQ-20260917-11"]["errors"] and "## Details" in (between(files["REQ-20260917-11.md"], "Ask", "Request block") or ""))
        check("filling Fulfilment does not break the hash (the block is above it)",
              all(by[f"REQ-20260917-0{i}"]["hash_ok"] and not by[f"REQ-20260917-0{i}"]["errors"] for i in (2, 3, 4)))
        check("fields read: taken_by / pr / merged / at", by["REQ-20260917-03"]["taken_by"] == "Night" and by["REQ-20260917-03"]["pr"].endswith("/400")
              and by["REQ-20260917-04"]["merged"] == "yes 2026-09-17" and by["REQ-20260917-02"]["fulfilled_at"] == "2026-09-17T13:00:00Z")
        check("merged with header still OPEN → warning, not error", by["REQ-20260917-04"]["warnings"] and not by["REQ-20260917-04"]["errors"])
        check("merged with no pr/taken_by → inconsistent (error)", by["REQ-20260917-05"]["stage"] == "inconsistent" and by["REQ-20260917-05"]["errors"])
        check("edited ask → ask_sha256 mismatch (error); block hash still fine", not by["REQ-20260917-06"]["ask_ok"] and by["REQ-20260917-06"]["hash_ok"] and by["REQ-20260917-06"]["errors"])
        check("edited block → hash mismatch (error)", not by["REQ-20260917-07"]["hash_ok"] and by["REQ-20260917-07"]["errors"])
        r8 = by["REQ-20260917-09"]
        check("id in heading/block ≠ filename → error; listed under candidates: only → not indexed (error)", not r8["id_ok"] and not r8["indexed"] and len(r8["errors"]) >= 2)
        check("index paths read quoted and bare, column 0 and indented, records: section only", all(by[f"REQ-20260917-0{i}"]["indexed"] for i in range(1, 8)))
        check("counts + verdict: stage counts from Fulfilment (a broken hash is still 'requested'), ERROR overall, 5 verify",
              s["counts"] == {"requested": 6, "taken": 1, "pr": 1, "merged": 1, "inconsistent": 1} and s["verdict"] == "ERROR" and s["verified"] == 5)
        # missing index with an inbox present → error (coverage cannot be read); empty inbox → OK, nothing to show
        os.rename(os.path.join(td, INDEX), os.path.join(td, INDEX + ".bak"))
        e = snapshot(td)
        check("index missing while z1-inbox/ exists → ERROR naming the index", e["verdict"] == "ERROR" and any("missing" in x for x in e["errors"]))
        os.rename(os.path.join(td, INDEX + ".bak"), os.path.join(td, INDEX))
        for n in files:
            os.remove(os.path.join(day, n))
        e = snapshot(td)
        check("no records → total 0, verdict OK", e["total"] == 0 and e["verdict"] == "OK")
        check("snapshot is JSON-serialisable with the schema the dashboard checks", json.loads(json.dumps(s))["schema"] == SCHEMA)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", "--input", dest="root", default=ROOT, help="repository root (--input is the tools/README.md alias)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 2 if any record fails to verify")
    ap.add_argument("--self-test", "--smoke-test", dest="self_test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if run_self_test() else 2
    s = snapshot(a.root)
    if a.json:
        print(json.dumps(s, indent=1, ensure_ascii=False))
    else:
        print_table(s)
    return 2 if (a.check and s["verdict"] != "OK") else 0


if __name__ == "__main__":
    sys.exit(main())
