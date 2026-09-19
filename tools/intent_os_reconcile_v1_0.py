#!/usr/bin/env python3
"""intent_os_reconcile — after a decided candidate merges, record the ratification the merge was.
Builder v1.7 compliant · governance_tool
HumanAIOS · S-091826-01 (under Z2's ruling of 2026-09-18: the merge is the ratification —
z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md)

A tap on the Intent-OS board lands a choice in the ruling's own candidate block, on a branch, in a
pull request that changes that one file (tools/decision_relay.py 0.5.0, `status: DECIDED`). The
relay signs nothing. Z2 reviews and merges the pull request, and that merge IS the Z2 act: whoever
merged it, and the day they did, are the signature's `by` and `at`. What the merge cannot do is write
the three derived files a ratification needs — the day's ruling file, the index entry, the rendered
index — because two branches that both wrote them could not both merge. This tool writes them, on
main, after the fact, from what the tree and GitHub already say:

  for every candidate that is `awaiting_z2` in z1-inbox/INDEX.yaml whose file carries a Ruling
  section with a relay block (status DECIDED, or PENDING from relay 0.4.x):
    1. the block hashes to its `block_hash` and the rest of the file to its `body_hash` — else UNVERIFIED
    2. the last commit that touched the file (git log -1 -- path) belongs to a merged pull request
       into main (GET /repos/{repo}/commits/{sha}/pulls) — else NO-PR (a direct push is d7's
       question, not a ratification)
    3. the person who merged it maps to a declared ratifier (RECONCILE_RATIFIERS, default
       `humanaios-ui=Night`) — else NOT-RATIFIER
    4. sha256(candidate | by=<ratifier> | at=<merge date> | decision=ACCEPT) over the merged bytes —
       the construction `.z1-control/ratify.py --verify` recomputes — is appended to
       z1-inbox/<merge date>/Z2_RULINGS_<merge date>.md (created, and indexed under records:, if
       absent), the candidate is marked `ratified` in INDEX.yaml with that hash, and Z1_INBOX_INDEX.md
       is regenerated with .z1-control/render.py's renderer. The candidate file is NOT touched: the
       bytes Z2 merged are the bytes that are signed.

Idempotent: a second run finds nothing awaiting. A ruling file that already records the candidate
under a different hash is a refusal, never an overwrite. The index shapes are imported from
tools/decision_relay.py so the job writes on main exactly what the relay would have written on a
branch. Reviews are recorded, not required, here: with one member the author merges their own pull
request (d7's bypass, written into the ruling section as such); with more than one, the repository's
required review is the rule and this tool records who approved.

Exit codes: 0 = nothing to reconcile, or everything reconcilable was written · 1 = --check found
candidates to reconcile (nothing written) · 2 = at least one UNVERIFIED / NO-PR / NOT-RATIFIER
(the others are still written under --apply).

Usage:
  python3 tools/intent_os_reconcile_v1_0.py --check            # the plan; exit 1 if something is waiting
  python3 tools/intent_os_reconcile_v1_0.py --apply            # write ruling file, INDEX, rendered index
  python3 tools/intent_os_reconcile_v1_0.py --json ...
  python3 tools/intent_os_reconcile_v1_0.py --self-test

Env: GITHUB_TOKEN (to read the merged pull request; without it every decided candidate is NO-PR)
     GITHUB_REPO=humanaios-ui/operations · RECONCILE_RATIFIERS="humanaios-ui=Night[,login=Name…]"
Deps: PyYAML, git on PATH; tools/decision_relay.py and .z1-control/ beside it. Network only for the
pull-request lookup.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

TOOL_NAME = "intent_os_reconcile"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-091826-01"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night — records a Z2 act already made (the merge); makes none

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELAY = os.path.join("tools", "decision_relay.py")
REPO = os.environ.get("GITHUB_REPO", "humanaios-ui/operations")
ACCEPTED_BLOCK_STATUS = ("DECIDED", "PENDING")  # PENDING: relay 0.4.x, before the merge was the ratification


def load_relay(root: str):
    """The relay's pure text operations (Ruling section, signature, index splices, renderer)."""
    spec = importlib.util.spec_from_file_location("decision_relay", os.path.join(root, RELAY))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = root
    return mod


def ratifier_map() -> dict:
    """GitHub login → declared ratifier name. Never taken from a candidate or a request."""
    raw = os.environ.get("RECONCILE_RATIFIERS", "humanaios-ui=Night")
    out = {}
    for part in raw.split(","):
        login, _, name = part.strip().partition("=")
        if login and name:
            out[login.strip().lower()] = name.strip()
    return out


def gh_get(path: str, token: str):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Authorization": f"token {token}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def last_commit(root: str, rel: str) -> str | None:
    r = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=root, capture_output=True, text=True)
    sha = r.stdout.strip()
    return sha if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha) else None


def github_lookup(root: str, rel: str) -> dict:
    """The merged pull request behind the file's last commit on this checkout, or {"error": …}.
    Returns number, html_url, merged_by, merged_at (ISO), author, approvers."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return {"error": "GITHUB_TOKEN not set — the merged pull request cannot be read"}
    sha = last_commit(root, rel)
    if not sha:
        return {"error": "no commit touches this file on the checkout (git log -1)"}
    try:
        prs = gh_get(f"/repos/{REPO}/commits/{sha}/pulls", token)
        merged = [p for p in prs if p.get("merged_at") and (p.get("base") or {}).get("ref") == "main"]
        if not merged:
            return {"error": f"commit {sha[:12]} belongs to no pull request merged into main", "sha": sha}
        pr = gh_get(f"/repos/{REPO}/pulls/{merged[0]['number']}", token)  # the list omits merged_by
        approvers = []
        try:
            for rv in gh_get(f"/repos/{REPO}/pulls/{pr['number']}/reviews", token):
                if rv.get("state") == "APPROVED" and (rv.get("user") or {}).get("login"):
                    approvers.append(rv["user"]["login"])
        except (urllib.error.URLError, KeyError, ValueError):
            pass  # reviews are recorded when readable, never required here
        return {"number": pr["number"], "html_url": pr.get("html_url", ""), "sha": sha,
                "merged_by": ((pr.get("merged_by") or {}).get("login") or ""), "merged_at": pr.get("merged_at") or "",
                "author": ((pr.get("user") or {}).get("login") or ""), "approvers": sorted(set(approvers))}
    except urllib.error.HTTPError as e:
        return {"error": f"GitHub answered HTTP {e.code} reading the pull request for {sha[:12]}", "sha": sha}
    except (urllib.error.URLError, KeyError, ValueError) as e:
        return {"error": f"could not read the pull request for {sha[:12]}: {e}", "sha": sha}


def plan(root: str, lookup=github_lookup) -> dict:
    """Every awaiting candidate that carries a relay block, classified. Reads only."""
    relay = load_relay(root)
    sys.path.insert(0, os.path.join(root, ".z1-control"))
    import yaml  # noqa: E402
    import validate as v  # noqa: E402
    idx_text = open(os.path.join(root, relay.INDEX), encoding="utf-8").read()
    index = yaml.load(idx_text, Loader=v.StrictLoader)
    ratifiers = set(str(r) for r in (index.get("ratifiers") or []))
    logins = ratifier_map()
    rows = []
    for c in index.get("candidates") or []:
        if c.get("status") != "awaiting_z2":
            continue
        qid, rel = str(c.get("q_id")), str(c.get("path"))
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            continue
        text = open(full, encoding="utf-8").read()
        f = relay.ruling_fields(text)
        if not f or not f.get("block") or f.get("status") not in ACCEPTED_BLOCK_STATUS:
            continue  # an open question, or a section the relay did not write
        row = {"q_id": qid, "path": rel, "block_status": f["status"], "choice": f.get("choice"), "block_hash": f.get("block_hash")}
        m = re.search(r"^  question: (.*)$", f["block"], re.M)
        row["question"] = m.group(1) if m else ""
        m = re.search(r"^RULING (\S+)", f["block"])
        row["id"] = m.group(1) if m else ""
        m = re.search(r"^  choice: (.*)$", f["block"], re.M)
        if relay.sha(f["block"].encode()) != f.get("block_hash") or relay.body_hash(text) != f.get("body_hash") \
                or not m or m.group(1) != f.get("choice"):
            row.update(outcome="UNVERIFIED", why="the Ruling section does not hash to what the relay landed — edited after the tap")
            rows.append(row)
            continue
        pr = lookup(root, rel)
        if pr.get("error"):
            row.update(outcome="NO-PR", why=pr["error"])
            rows.append(row)
            continue
        by = logins.get(str(pr.get("merged_by", "")).lower())
        if not by or by not in ratifiers:
            row.update(outcome="NOT-RATIFIER", why=f"merged by '{pr.get('merged_by')}', who is not mapped to a declared ratifier {sorted(ratifiers)}", pr=pr)
            rows.append(row)
            continue
        at = str(pr.get("merged_at", ""))[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", at):
            row.update(outcome="NO-PR", why=f"pull request #{pr.get('number')} carries no merge date", pr=pr)
            rows.append(row)
            continue
        digest = relay.signature(open(full, "rb").read(), by, at)
        row.update(outcome="RECONCILE", by=by, at=at, signature=digest, ruling=f"z1-inbox/{at}/Z2_RULINGS_{at}.md", pr=pr,
                   override=(not pr.get("approvers")) or (pr.get("approvers") == [pr.get("author")]))
        rows.append(row)
    todo = [r for r in rows if r["outcome"] == "RECONCILE"]
    refused = [r for r in rows if r["outcome"] != "RECONCILE"]
    return {"tool": TOOL_NAME, "version": TOOL_VERSION, "rows": rows,
            "outcome": "REFUSED" if refused else ("RECONCILE" if todo else "NOTHING"),
            "counts": {"reconcile": len(todo), "refused": len(refused)}}


def ruling_section(relay, row: dict) -> str:
    pr = row["pr"]
    who = (f"single-member override — the author reviewed and merged their own pull request (d7's bypass, recorded as such)"
           if row["override"] else f"approved by {', '.join(pr['approvers'])}, merged by {pr['merged_by']}")
    return (f"\n## {row['q_id']} — ACCEPT\n\nHash: `{row['signature']}`\n\n"
            f"- **Decision:** ACCEPT (ratified) · board ruling {row['id']}: `{row['choice']}`\n"
            f"- **By:** {row['by']}\n- **At:** {row['at']}\n- **Candidate:** `{row['path']}`\n"
            f"- **Ratified by merge:** pull request #{pr['number']} ({pr['html_url']}) merged by {pr['merged_by']} at {pr['merged_at']}; {who}\n"
            f"- **Landed by:** tools/decision_relay.py (`{row['block_status']}` block, hash `{str(row['block_hash'])[:16]}…`); recorded by {TOOL_NAME} v{TOOL_VERSION} on main at commit {pr.get('sha', '')[:12]}\n"
            f"- **Signature:** `sha256(candidate | by={row['by']} | at={row['at']} | decision=ACCEPT)`, computed over the candidate's bytes as merged — the merge is the ratification (Z2, 2026-09-18).\n")


def apply(root: str, p: dict) -> list:
    """Write the three derived files for every RECONCILE row. Returns the paths written."""
    relay = load_relay(root)
    written = []
    idx = open(os.path.join(root, relay.INDEX), encoding="utf-8").read()
    for row in sorted((r for r in p["rows"] if r["outcome"] == "RECONCILE"), key=lambda r: (r["at"], r["q_id"])):
        rel = row["ruling"]
        full = os.path.join(root, rel)
        ruling = open(full, encoding="utf-8").read() if os.path.exists(full) else (
            f"# Z2 Rulings — {row['at']}\n\nSignatures issued by the Z2 serial gate. Each hash is\n"
            f"`sha256(candidate | by=<ratifier> | at=<date> | decision=<D>)` over the\n"
            f"candidate block's bytes at the moment of decision, so editing a ratified\ncandidate afterwards breaks `ratify.py --verify`.\n")
        if f"## {row['q_id']} — ACCEPT" in ruling:
            if f"`{row['signature']}`" not in ruling:
                row.update(outcome="REFUSED", why=f"{rel} already records {row['q_id']} under a different hash; nothing written for it")
                continue
        else:
            ruling += ruling_section(relay, row)
        if f'path: "{rel}"' not in idx and f"path: {rel}\n" not in idx:
            idx = relay.index_add_record(idx, rel, f"Z2 rulings {row['at']} — signatures issued by .z1-control/ratify.py and tools/{TOOL_NAME}_v1_0.py",
                                         "Z2 output. Cited as z2_ruling by the candidates it signs; the reconcile job records each merge of a decided candidate here.")
        idx = relay.index_mark_ratified(idx, row["q_id"], row["by"], row["at"], rel, row["signature"])
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w", encoding="utf-8").write(ruling)
        written.append(rel)
    if written:
        open(os.path.join(root, relay.INDEX), "w", encoding="utf-8").write(idx)
        written.append(relay.INDEX)
        rendered = relay.rendered_index(idx, lambda rel: open(os.path.join(root, rel), encoding="utf-8").read() if os.path.exists(os.path.join(root, rel)) else "")
        open(os.path.join(root, relay.RENDERED), "w", encoding="utf-8").write(rendered)
        written.append(relay.RENDERED)
    p["written"] = sorted(set(written))
    p["counts"]["refused"] = len([r for r in p["rows"] if r["outcome"] != "RECONCILE"])
    return p["written"]


def table(p: dict) -> str:
    lines = [f"{TOOL_NAME} v{TOOL_VERSION} — {p['outcome']}"]
    for r in p["rows"]:
        tail = (f"→ {r['by']} at {r['at']} · #{r['pr']['number']} · {r['signature'][:16]}…" + (" · single-member override" if r.get("override") else "")
                if r["outcome"] == "RECONCILE" else f"— {r.get('why', '')}")
        lines.append(f"  {r['outcome']:<13} {r['q_id']:<26} {str(r.get('id') or ''):<5} {str(r.get('choice') or ''):<24} {tail}")
    if p.get("written"):
        lines.append("  written: " + ", ".join(p["written"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    ok = True
    td = tempfile.mkdtemp(prefix="reconcile_selftest_")
    try:
        shutil.copytree(os.path.join(ROOT, ".z1-control"), os.path.join(td, ".z1-control"))
        os.makedirs(os.path.join(td, "tools"))
        shutil.copy(os.path.join(ROOT, RELAY), os.path.join(td, RELAY))
        os.makedirs(os.path.join(td, "z1-inbox", "2026-09-14"))
        subprocess.run(["git", "init", "-q"], cwd=td, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "root"], cwd=td, check=True)
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "w").write(
            "version: 1\ngenerated: '2026-09-16'\ndecision_window_days: 2\ncounts:\n  candidates: 3\n  records: 0\nratifiers:\n- Night\ncandidates:\n"
            "- q_id: Q-BOARD-RULING-06\n  title: Board ruling d6\n  path: z1-inbox/2026-09-14/Q-BOARD-RULING-06.md\n  submitted: '2026-09-14'\n  status: awaiting_z2\n  falsifier_waiver: question\n"
            "- q_id: Q-BOARD-RULING-07\n  title: Board ruling d7\n  path: z1-inbox/2026-09-14/Q-BOARD-RULING-07.md\n  submitted: '2026-09-14'\n  status: awaiting_z2\n  falsifier_waiver: question\n"
            "- q_id: Q-BOARD-RULING-08\n  title: Board ruling d8\n  path: z1-inbox/2026-09-14/Q-BOARD-RULING-08.md\n  submitted: '2026-09-14'\n  status: awaiting_z2\n  falsifier_waiver: question\n"
            "records: []\nexcluded: []\n")
        relay = load_relay(td)
        for n, q in ((6, "batch source?"), (7, "direct pushes?"), (8, "open question")):
            open(os.path.join(td, "z1-inbox", "2026-09-14", f"Q-BOARD-RULING-{n:02d}.md"), "w").write(
                f"# Ruling request Q-BOARD-RULING-{n:02d}\n\n## Question\n\n{q}\n\n## Ruling\n\nchoice:\nby:\nat:\nstatus: OPEN\n\n## Z2 Review Checklist\n\n- [ ] {q}\n")
        def decide(n, q, choice, status="DECIDED"):
            rel = f"z1-inbox/2026-09-14/Q-BOARD-RULING-{n:02d}.md"
            text = open(os.path.join(td, rel)).read()
            block = relay.ruling_block({"id": f"d{n}", "tagline": "Night", "project": "HumanAIOS", "q": q, "choice": choice, "ts": "2026-09-18T01:00:00Z"})
            if status != "DECIDED":
                block = block.replace("status: DECIDED", f"status: {status}")
            open(os.path.join(td, rel), "w").write(relay.write_choice(text, choice, "Night", "2026-09-18T01:00:00Z", status, block, relay.sha(block.encode()), relay.body_hash(text)))
            return rel
        c6 = decide(6, "batch source?", "own postings")
        c7 = decide(7, "direct pushes?", "bypass + IC", status="PENDING")  # a 0.4.x block: accepted
        render_ok = subprocess.run([sys.executable, os.path.join(td, ".z1-control", "render.py")], cwd=td, capture_output=True, text=True).returncode == 0
        subprocess.run(["git", "add", "-A"], cwd=td, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "decided"], cwd=td, check=True)
        PR = {"number": 401, "html_url": "https://example.test/pull/401", "sha": "abc", "merged_by": "humanaios-ui", "merged_at": "2026-09-18T02:30:00Z", "author": "humanaios-ui", "approvers": []}
        def lookup(root, rel):
            if rel.endswith("-06.md"):
                return PR
            if rel.endswith("-07.md"):
                return {**PR, "number": 402, "merged_by": "humanaios-ui", "approvers": ["reviewer2"], "author": "someone"}
            return {"error": "no pull request"}
        # --check: two to reconcile (d6 DECIDED, d7 PENDING), the open d8 has no block and is not listed
        p = plan(td, lookup)
        ok &= p["outcome"] == "RECONCILE" and [r["q_id"] for r in p["rows"]] == ["Q-BOARD-RULING-06", "Q-BOARD-RULING-07"] and p["counts"] == {"reconcile": 2, "refused": 0}
        ok &= p["rows"][0]["override"] is True and p["rows"][1]["override"] is False and p["rows"][0]["by"] == "Night" and p["rows"][0]["at"] == "2026-09-18"
        ok &= p["rows"][0]["signature"] == relay.signature(open(os.path.join(td, c6), "rb").read(), "Night", "2026-09-18")
        print("plan: DECIDED and PENDING blocks behind merged PRs → RECONCILE; open question not listed; override flagged when no second reviewer →", ok)
        before = {rel: open(os.path.join(td, rel)).read() for rel in (c6, c7)}
        # --apply: one ruling file for the day, two sections, one records: entry; candidates untouched; the z2 gate's own tools agree
        written = apply(td, p)
        ruling = open(os.path.join(td, "z1-inbox", "2026-09-18", "Z2_RULINGS_2026-09-18.md")).read()
        idx = open(os.path.join(td, "z1-inbox", "INDEX.yaml")).read()
        ok &= sorted(written) == sorted(["z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md", "z1-inbox/INDEX.yaml", "Z1_INBOX_INDEX.md"])
        ok &= ruling.count("— ACCEPT") == 2 and "single-member override" in ruling and "approved by reviewer2" in ruling and "#401" in ruling
        ok &= idx.count("status: ratified") == 2 and idx.count("status: awaiting_z2") == 1 and idx.count("Z2_RULINGS_2026-09-18.md") == 3 and "records: 1" in idx
        ok &= all(open(os.path.join(td, rel)).read() == before[rel] for rel in before)
        print("apply: ruling file + INDEX + rendered index written, candidates untouched, one records entry for two signatures →", ok)
        gate = {}
        for name, args in (("validate", ["validate.py"]), ("render --check", ["render.py", "--check"]), ("ratify --verify", ["ratify.py", "--verify"])):
            r = subprocess.run([sys.executable, os.path.join(td, ".z1-control", args[0])] + args[1:], cwd=td, capture_output=True, text=True)
            gate[name] = r.returncode
            if r.returncode != 0:
                print(f"  {name} said:\n" + (r.stdout + r.stderr)[-800:])
        ok &= all(v == 0 for v in gate.values()) and render_ok
        print("the z2 gate's own tools on the reconciled tree: validate.py, render.py --check, ratify.py --verify →", gate)
        # idempotent: nothing awaiting on a second run, nothing written
        p2 = plan(td, lookup)
        ok &= p2["outcome"] == "NOTHING" and p2["rows"] == [] and apply(td, p2) == []
        print("second run → NOTHING, nothing written →", p2["outcome"])
        # refusals: a tampered block, a merger who is not a ratifier, no pull request — nothing written for any of them
        c8 = decide(8, "open question", "yes")
        t = open(os.path.join(td, c8)).read().replace("  choice: yes", "  choice: no")
        open(os.path.join(td, c8), "w").write(t)
        p3 = plan(td, lookup)
        ok &= p3["outcome"] == "REFUSED" and p3["rows"][0]["outcome"] == "UNVERIFIED"
        open(os.path.join(td, c8), "w").write(t.replace("  choice: no", "  choice: yes"))
        p4 = plan(td, lambda root, rel: {**PR, "merged_by": "stranger"})
        ok &= p4["rows"][0]["outcome"] == "NOT-RATIFIER" and "stranger" in p4["rows"][0]["why"]
        p5 = plan(td, lookup)
        ok &= p5["rows"][0]["outcome"] == "NO-PR"
        snapshot = {rel: open(os.path.join(td, rel)).read() for rel in ("z1-inbox/INDEX.yaml", "Z1_INBOX_INDEX.md", "z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md")}
        for pp in (p3, p4, p5):
            apply(td, pp)
        ok &= all(open(os.path.join(td, rel)).read() == snapshot[rel] for rel in snapshot)
        print("refusals: tampered block → UNVERIFIED · merged by a stranger → NOT-RATIFIER · no pull request → NO-PR; nothing written →", ok)
        # a ruling file that already records the candidate under another hash is refused, never overwritten
        open(os.path.join(td, c8), "w").write(t.replace("  choice: no", "  choice: yes"))
        rf = os.path.join(td, "z1-inbox", "2026-09-18", "Z2_RULINGS_2026-09-18.md")
        open(rf, "a").write("\n## Q-BOARD-RULING-08 — ACCEPT\n\nHash: `0000`\n")
        p6 = plan(td, lambda root, rel: PR)
        ok &= p6["outcome"] == "RECONCILE"
        apply(td, p6)
        ok &= p6["rows"][0]["outcome"] == "REFUSED" and "different hash" in p6["rows"][0]["why"] and "status: awaiting_z2" in open(os.path.join(td, "z1-inbox", "INDEX.yaml")).read()
        print("a ruling file that already carries the candidate under another hash → REFUSED, index untouched →", ok)
        # the ratifier map is env-driven and case-insensitive on the login; a bad entry is ignored
        os.environ["RECONCILE_RATIFIERS"] = "HumanAIOS-UI=Night, broken, x=Y"
        ok &= ratifier_map() == {"humanaios-ui": "Night", "x": "Y"}
        del os.environ["RECONCILE_RATIFIERS"]
        print("ratifier map: login lower-cased, malformed entries dropped →", ok)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="plan only; exit 1 if something is waiting to be reconciled")
    g.add_argument("--apply", action="store_true", help="write the ruling file, INDEX.yaml and Z1_INBOX_INDEX.md")
    g.add_argument("--self-test", "--smoke-test", dest="self_test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    p = plan(a.root)
    if a.apply:
        apply(a.root, p)
    print(json.dumps(p, indent=1) if a.json else table(p))
    if p["counts"]["refused"]:
        return 2
    if a.check and p["counts"]["reconcile"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
