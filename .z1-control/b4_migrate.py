#!/usr/bin/env python3
"""b4_migrate.py (v2) — gated per-seat content migration into a survivor's OWN store.

Builder v1.7 compliant · governance_tool

v1 trusted `--project-id` to route and trusted the exit code — so all 12 seats' artifacts
landed in ONE store (opportunity-aggregator) and the tool reported success. A probe
established empirica's model: PER-FILE. The CLI reads/writes ONE sessions.db resolved from
context (EMPIRICA_SESSION_DB / CWD); `--project-id` only tags. v2 fixes all of that:

  - ROUTE BY CONTEXT: import with EMPIRICA_SESSION_DB set to the SURVIVOR's own sessions.db.
  - POST-WRITE VERIFY: after import, count the folded-from rows IN THE SURVIVOR'S OWN FILE;
    fail + don't stamp if they're not there. (The guard v1 lacked — it would have caught v1.)
  - EMBED: run project-embed so migrated artifacts are retrievable (project-search returned
    empty on un-embedded rows).
  - ROLLBACK: --rollback restores opportunity-aggregator's store from the pre-migration
    snapshot (clean + certain; the no-provenance tables make surgical SQL deletion unsafe)
    and resets the markers, so the whole migration can be redone correctly.

Gated: both the signed RATIFY row (fold.ratified) and the seat's FOLDED_INTO marker.
Non-destructive to sources; idempotent; dry-run by default.

Commands:
  --rollback [--apply]      restore opportunity's store from snapshot + reset markers
  --seat <name> [--apply]   migrate one folded seat into its survivor's OWN store
  --all [--apply]           every folded, not-yet-migrated seat
  --smoke-test
"""
from __future__ import annotations

TOOL_NAME = "b4_migrate"
TOOL_VERSION = "2.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

import argparse
import datetime
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b4_fold_execute as fold

PRACTICES_ROOT = fold.PRACTICES_ROOT
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b4_migration_bundles")
SNAPSHOT = os.path.expanduser("~/practices-snapshot-2026-10-09-sweep.tgz")
MIS_STORE = "opportunity-aggregator"   # where v1 mis-routed everything
MARKER_MIGRATE_KEYS = ("migrated:", "migrated_nodes:", "migrated_into_file:",
                       "verified_findings:", "migrated_at:", "embed:")

EXPORTERS = {
    "project_findings":  ("finding",   {"finding": "finding", "impact": "impact"},            "is_resolved = 0"),
    "decisions":         ("decision",  {"choice": "choice", "rationale": "rationale",
                                        "reversibility": "reversibility"},                     "1=1"),
    "assumptions":       ("assumption",{"assumption": "assumption", "confidence": "confidence"},"resolution_finding_id IS NULL"),
    "project_unknowns":  ("unknown",   {"unknown": "unknown"},                                  "is_resolved = 0"),
    "mistakes_made":     ("mistake",   {"mistake": "mistake", "why_wrong": "why_wrong",
                                        "prevention": "prevention"},                            "is_invalidated = 0"),
    "project_dead_ends": ("dead_end",  {"approach": "approach", "why_failed": "why_failed"},    "is_invalidated = 0"),
}


def survivor_db(survivor: str) -> str:
    return os.path.join(PRACTICES_ROOT, survivor, ".empirica", "sessions", "sessions.db")


def marker_path(seat: str) -> str:
    return os.path.join(PRACTICES_ROOT, seat, ".empirica", "FOLDED_INTO.yaml")


def read_marker(seat: str) -> dict:
    p = marker_path(seat)
    out = {}
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            if ":" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition(":")
                out[k.strip()] = v.strip()
    return out


def _cols(cur, table: str) -> set:
    try:
        return {r[1] for r in cur.execute(f"PRAGMA table_info({table})")}
    except sqlite3.Error:
        return set()


def _filter_cols(clause: str) -> list:
    return [t for t in ("is_resolved", "is_invalidated", "resolution_finding_id") if t in clause]


def _count_in_db(db: str, seat: str) -> int:
    """folded-from:<seat> findings present in THIS db file (the post-write verify)."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = con.execute("SELECT count(*) FROM project_findings WHERE subject = ?",
                        (f"folded-from:{seat}",)).fetchone()[0]
        con.close()
        return n
    except sqlite3.Error:
        return 0


def _folded_from_total(db: str) -> int:
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = con.execute("SELECT count(*) FROM project_findings WHERE subject LIKE 'folded-from:%'").fetchone()[0]
        con.close()
        return n
    except sqlite3.Error:
        return 0


def _survivor_session(sdb: str) -> tuple[str, str]:
    """A real (session_id, project_id) from the survivor's OWN sessions table. log-artifacts
    needs these to resolve context; EMPIRICA_SESSION_DB only sets which file it writes to."""
    try:
        con = sqlite3.connect(f"file:{sdb}?mode=ro", uri=True)
        row = con.execute("SELECT session_id, project_id FROM sessions WHERE project_id IS NOT NULL "
                          "ORDER BY created_at DESC LIMIT 1").fetchone()
        con.close()
        return (row[0], row[1]) if row and row[0] and row[1] else ("", "")
    except sqlite3.Error:
        return ("", "")


def export_seat(seat: str) -> tuple[list, dict]:
    db = os.path.join(PRACTICES_ROOT, seat, ".empirica", "sessions", "sessions.db")
    nodes, counts = [], {}
    if not os.path.isfile(db):
        return nodes, counts
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    for table, (ntype, fieldmap, live) in EXPORTERS.items():
        have = _cols(cur, table)
        if not have:
            continue
        usable = {dst: src for dst, src in fieldmap.items() if src in have}
        if not usable:
            continue
        live_clause = live if all(c in have for c in _filter_cols(live)) else "1=1"
        try:
            rows = cur.execute(f"SELECT * FROM {table} WHERE {live_clause}").fetchall()
        except sqlite3.Error:
            continue
        kept = 0
        for i, r in enumerate(rows):
            data = {}
            for dst, src in usable.items():
                v = r[src]
                if v is None:
                    continue
                if dst in ("impact", "confidence"):
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                data[dst] = v
            primary = next(iter(fieldmap))
            if primary not in data or not str(data[primary]).strip():
                continue
            data["subject"] = f"folded-from:{seat}"
            data["visibility"] = "shared"
            nodes.append({"ref": f"{seat.replace('.', '_')}_{ntype}_{i}", "type": ntype, "data": data})
            kept += 1
        counts[ntype] = kept
    con.close()
    return nodes, counts


# ---------------------------------------------------------------------------
def migrate(seat: str, apply: bool) -> int:
    ok, msg = fold.ratified()
    if not ok:
        print(f"::error::REFUSING {seat} — not ratified: {msg}")
        return 1
    marker = read_marker(seat)
    if not marker.get("folded_into"):
        print(f"::error::REFUSING {seat} — no FOLDED_INTO marker (run b4_fold_execute first)")
        return 1
    if marker.get("migrated") == "true":
        print(f"  {seat}: already migrated — skipping (idempotent)")
        return 0
    survivor = marker["folded_into"]
    sdb = survivor_db(survivor)
    if not os.path.isfile(sdb):
        print(f"::error::{seat}: survivor store not found: {sdb}")
        return 1

    nodes, counts = export_seat(seat)
    if not nodes:
        print(f"  {seat}: no live artifacts → {survivor}")
        return 0
    os.makedirs(OUT_DIR, exist_ok=True)
    bpath = os.path.join(OUT_DIR, f"{seat}.json")
    json.dump({"nodes": nodes}, open(bpath, "w", encoding="utf-8"), indent=2, default=str)
    want_findings = sum(1 for n in nodes if n["type"] == "finding")
    summary = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()) if v)
    print(f"  {seat} → {survivor}: {len(nodes)} live nodes ({summary})")

    sid, pid = _survivor_session(sdb)
    if not sid or not pid:
        print(f"::error::{seat}: no resolvable session in {survivor}'s store — cannot import")
        return 1
    if not apply:
        print(f"    [dry-run] import into {survivor}'s OWN store:")
        print(f"      EMPIRICA_SESSION_DB={sdb} empirica log-artifacts --session-id {sid} --project-id {pid} - < {bpath}")
        print(f"      → then verify {want_findings} findings in that file + embed")
        return 0

    env = {**os.environ, "EMPIRICA_SESSION_DB": sdb}
    with open(bpath, encoding="utf-8") as fh:
        r = subprocess.run(["empirica", "log-artifacts", "--session-id", sid, "--project-id", pid, "-"],
                           stdin=fh, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"::error::{seat}: import failed — {r.stderr.strip()[:300]}")
        print(f"    (bundle at {bpath}; source untouched; marker NOT updated)")
        return 1
    # POST-WRITE VERIFY — in the SURVIVOR'S OWN file (the guard v1 lacked)
    got = _count_in_db(sdb, seat)
    if got < want_findings:
        print(f"::error::{seat}: POST-WRITE VERIFY FAILED — {got}/{want_findings} folded-from "
              f"findings in {survivor}'s file. NOT stamping; investigate before retry.")
        return 1
    emb = subprocess.run(["empirica", "project-embed"], env=env, capture_output=True, text=True)
    emb_note = "embedded" if emb.returncode == 0 else f"embed-deferred({emb.stderr.strip()[:50]})"
    with open(marker_path(seat), "a", encoding="utf-8") as fh:
        fh.write(f"migrated: true\nmigrated_nodes: {len(nodes)}\nmigrated_into_file: {sdb}\n"
                 f"verified_findings: {got}\nembed: {emb_note}\n"
                 f"migrated_at: {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}\n")
    print(f"  ✓ {seat}: {len(nodes)} into {survivor}'s OWN file; verified {got}/{want_findings} findings; {emb_note}")
    return 0


def cmd_all(apply: bool) -> int:
    rc = 0
    for seat in sorted(fold.FOLDS):
        rc |= migrate(seat, apply)
    return rc


# ---------------------------------------------------------------------------
def cmd_rollback(apply: bool) -> int:
    """Restore the mis-routed store (opportunity-aggregator) from the pre-migration snapshot
    and reset the 12 markers. Clean + certain — the no-provenance tables (decisions/assumptions/
    mistakes) make surgical SQL deletion unsafe, so we revert the whole file to its floor."""
    oppdb = survivor_db(MIS_STORE)
    member = f"practices/{MIS_STORE}/.empirica/sessions/sessions.db"
    before = _folded_from_total(oppdb)
    if not os.path.isfile(SNAPSHOT):
        print(f"::error::snapshot not found: {SNAPSHOT}")
        return 1
    with tarfile.open(SNAPSHOT) as tf:
        has = member in tf.getnames()
    print(f"rollback: restore {MIS_STORE} store from snapshot + reset {len(fold.FOLDS)} markers")
    print(f"  snapshot contains the store file: {has}")
    print(f"  folded-from findings currently in {MIS_STORE}: {before}")
    if not apply:
        print("  [dry-run] --apply to: back up current db → restore snapshot copy → reset markers")
        return 0
    if not has:
        print("::error::snapshot lacks the store file — aborting (no safe restore)")
        return 1
    bak = oppdb + f".bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(oppdb, bak)
    tmp = os.path.join("/tmp", "b4rollback")
    with tarfile.open(SNAPSHOT) as tf:
        try:
            tf.extract(member, path=tmp, filter="data")   # py3.12+ safe extraction
        except TypeError:
            tf.extract(member, path=tmp)
    shutil.copy2(os.path.join(tmp, member), oppdb)
    reset = 0
    for seat in fold.FOLDS:
        mp = marker_path(seat)
        if os.path.isfile(mp):
            lines = [l for l in open(mp, encoding="utf-8")
                     if not l.startswith(MARKER_MIGRATE_KEYS)]
            open(mp, "w", encoding="utf-8").writelines(lines)
            reset += 1
    after = _folded_from_total(oppdb)
    print(f"  ✓ restored {MIS_STORE} (backup: {bak})")
    print(f"    folded-from findings: {before} → {after}   markers reset: {reset}/{len(fold.FOLDS)}")
    print("    now re-run:  b4_migrate.py --all --apply   (routes each seat to its own survivor file)")
    return 0


# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        seat = "demo-seat"
        emp = os.path.join(tmp, seat, ".empirica", "sessions")
        os.makedirs(emp)
        db = os.path.join(emp, "sessions.db")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE project_findings (id INT, finding TEXT, impact REAL, is_resolved INT, subject TEXT)")
        con.execute("INSERT INTO project_findings VALUES (1,'live',0.7,0,NULL),(2,'closed',0.3,1,NULL)")
        con.execute("CREATE TABLE decisions (id INT, choice TEXT, rationale TEXT, reversibility TEXT)")
        con.execute("INSERT INTO decisions VALUES (1,'a choice','because','committal')")
        con.commit(); con.close()
        orig = fold.PRACTICES_ROOT
        global PRACTICES_ROOT
        fold.PRACTICES_ROOT = tmp; PRACTICES_ROOT = tmp
        try:
            nodes, counts = export_seat(seat)
            assert counts.get("finding") == 1 and counts.get("decision") == 1, counts
            assert all(n["data"]["subject"] == f"folded-from:{seat}" for n in nodes)
            assert all(n["type"] in {"finding","unknown","dead_end","mistake","assumption","decision","source"}
                       for n in nodes)
            # post-write verify counts folded-from in a given db
            con = sqlite3.connect(db)
            con.execute("INSERT INTO project_findings VALUES (3,'x',0.1,0,'folded-from:demo-seat')")
            con.commit(); con.close()
            assert _count_in_db(db, seat) == 1, "verify helper must count folded-from"
            import ratify_eco
            ol = ratify_eco.LEDGER; ratify_eco.LEDGER = os.path.join(tmp, "empty.jsonl")
            try:
                assert migrate(seat, apply=False) == 1, "must refuse when not ratified"
            finally:
                ratify_eco.LEDGER = ol
        finally:
            fold.PRACTICES_ROOT = orig; PRACTICES_ROOT = orig
    print("✓ smoke-test passed: live-only export, provenance, valid types, post-write-verify helper, "
          "refuses unratified")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="b4_migrate.py", description="B4 v2 — per-seat migration into the survivor's own store (gated, verified).")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--rollback", action="store_true", help="restore opportunity's store from snapshot + reset markers")
    g.add_argument("--seat", help="one folded seat")
    g.add_argument("--all", action="store_true")
    g.add_argument("--smoke-test", action="store_true")
    p.add_argument("--apply", action="store_true", help="act (default: dry-run)")
    args = p.parse_args(argv)
    if args.smoke_test:
        return cmd_smoke()
    if args.rollback:
        return cmd_rollback(args.apply)
    if args.all:
        return cmd_all(args.apply)
    if args.seat:
        return migrate(args.seat, args.apply)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
