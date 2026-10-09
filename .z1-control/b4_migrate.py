#!/usr/bin/env python3
"""b4_migrate.py — B4: migrate a folded seat's artifacts into its survivor. One gated command per seat.

Completes the second layer of the fold: b4_fold_execute wrote the FOLDED_INTO markers (topology);
this moves the epistemic CONTENT. Reads a folded seat's live artifacts from its sessions.db and
emits (or applies) an `empirica log-artifacts --project-id <survivor>` import, tagged with
provenance back to the folded seat.

Gated and safe:
  - Requires BOTH the signed RATIFY row (via b4_fold_execute.ratified) AND the seat's FOLDED_INTO
    marker. Refuses otherwise.
  - LIVE artifacts only — resolved findings/unknowns and invalidated mistakes/dead-ends stay in the
    read-only source store (their closure is history, not live knowledge to re-home).
  - Non-destructive: the source store is never modified. Idempotent — records `migrated: true`
    in the marker and skips a second run.
  - Safe-by-default: writes the bundle + prints the import command. --apply runs the import.

Commands:
  --seat <name> [--apply]   migrate one folded seat (dry-run default)
  --all [--apply]           every folded, not-yet-migrated seat
  --smoke-test
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b4_fold_execute as fold  # reuse the ratification gate + PRACTICES_ROOT

PRACTICES_ROOT = fold.PRACTICES_ROOT
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b4_migration_bundles")

# table → (node type, {node_data_field: db_column}, live-filter SQL). Defensive: columns checked at read.
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


def marker_path(seat: str) -> str:
    return os.path.join(PRACTICES_ROOT, seat, ".empirica", "FOLDED_INTO.yaml")


def read_marker(seat: str) -> dict:
    p = marker_path(seat)
    if not os.path.isfile(p):
        return {}
    out = {}
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


def export_seat(seat: str) -> tuple[list, dict]:
    """Return (nodes, counts). Live artifacts only, tagged with provenance to the seat."""
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
            # require the primary text field
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


def _filter_cols(clause: str) -> list:
    return [tok for tok in ("is_resolved", "is_invalidated", "resolution_finding_id") if tok in clause]


# ---------------------------------------------------------------------------
def migrate(seat: str, apply: bool) -> int:
    ok, msg = fold.ratified()
    if not ok:
        print(f"::error::REFUSING {seat} — not ratified: {msg}")
        return 1
    marker = read_marker(seat)
    if not marker or marker.get("folded_into") in (None, ""):
        print(f"::error::REFUSING {seat} — no FOLDED_INTO marker (run b4_fold_execute first)")
        return 1
    if marker.get("migrated") == "true":
        print(f"  {seat}: already migrated (marker says migrated:true) — skipping (idempotent)")
        return 0
    survivor = marker["folded_into"]

    nodes, counts = export_seat(seat)
    if not nodes:
        print(f"  {seat}: no live artifacts to migrate → {survivor} (resolved/invalidated stay in source)")
        return 0
    bundle = {"nodes": nodes}
    os.makedirs(OUT_DIR, exist_ok=True)
    bpath = os.path.join(OUT_DIR, f"{seat}.json")
    with open(bpath, "w", encoding="utf-8") as fh:
        json.dump(bundle, fh, indent=2, default=str)
    summary = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()) if v)
    print(f"  {seat} → {survivor}: {len(nodes)} live nodes ({summary})")
    print(f"    bundle: {bpath}")

    cmd = f"empirica log-artifacts --project-id {survivor} - < {bpath}"
    if not apply:
        print(f"    [dry-run] import with:  {cmd}")
        print("    (re-run with --apply to import + mark the seat migrated)")
        return 0

    r = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"::error::{seat}: import failed — {r.stderr.strip()[:300]}")
        print(f"    (bundle preserved at {bpath}; source store untouched; marker NOT updated)")
        return 1
    # idempotency stamp on the marker (append-only addition; store still not deleted)
    with open(marker_path(seat), "a", encoding="utf-8") as fh:
        fh.write(f"migrated: true\nmigrated_nodes: {len(nodes)}\n"
                 f"migrated_at: {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}\n")
    print(f"  ✓ {seat}: {len(nodes)} artifacts imported into {survivor}; marker stamped migrated:true")
    return 0


def cmd_all(apply: bool) -> int:
    rc = 0
    for seat in sorted(fold.FOLDS):
        rc |= migrate(seat, apply)
    return rc


# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        seat = "demo-seat"
        emp = os.path.join(tmp, seat, ".empirica", "sessions")
        os.makedirs(emp)
        db = os.path.join(emp, "sessions.db")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE project_findings (id INT, finding TEXT, impact REAL, is_resolved INT)")
        con.execute("INSERT INTO project_findings VALUES (1,'live finding',0.7,0),(2,'closed',0.3,1)")
        con.execute("CREATE TABLE decisions (id INT, choice TEXT, rationale TEXT, reversibility TEXT)")
        con.execute("INSERT INTO decisions VALUES (1,'a choice','because','committal')")
        con.commit(); con.close()

        orig_root = fold.PRACTICES_ROOT
        global PRACTICES_ROOT
        fold.PRACTICES_ROOT = tmp
        PRACTICES_ROOT = tmp
        try:
            nodes, counts = export_seat(seat)
            # the resolved finding is excluded; the live one + the decision are kept
            assert counts.get("finding") == 1, f"live-only filter: {counts}"
            assert counts.get("decision") == 1, counts
            types = {n["type"] for n in nodes}
            assert types == {"finding", "decision"}, types
            assert all(n["data"].get("subject") == f"folded-from:{seat}" for n in nodes), "provenance tag missing"
            assert all(n["type"] in {"finding", "unknown", "dead_end", "mistake", "assumption", "decision", "source"}
                       for n in nodes), "invalid node type for log-artifacts"
            # gate: unratified → refuse (temp empty ledger)
            import ratify_eco
            orig_led = ratify_eco.LEDGER
            ratify_eco.LEDGER = os.path.join(tmp, "empty.jsonl")
            try:
                assert migrate(seat, apply=False) == 1, "must refuse when not ratified"
            finally:
                ratify_eco.LEDGER = orig_led
        finally:
            fold.PRACTICES_ROOT = orig_root
            PRACTICES_ROOT = orig_root
    print("✓ smoke-test passed: live-only export (resolved excluded), provenance tag, valid node "
          "types, refuses when unratified")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="b4_migrate.py", description="B4 — migrate a folded seat's artifacts into its survivor (gated).")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--seat", help="one folded seat to migrate")
    g.add_argument("--all", action="store_true", help="every folded, not-yet-migrated seat")
    g.add_argument("--smoke-test", action="store_true")
    p.add_argument("--apply", action="store_true", help="actually run the import (default: dry-run)")
    args = p.parse_args(argv)
    if args.smoke_test:
        return cmd_smoke()
    if args.all:
        return cmd_all(args.apply)
    if args.seat:
        return migrate(args.seat, args.apply)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
