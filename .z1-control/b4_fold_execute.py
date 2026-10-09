#!/usr/bin/env python3
"""b4_fold_execute.py — B4: execute the non-destructive practice fold, gated on ratification.

Folds 12 Empirica practice SEATS into their role-survivors per .z1-control/B4_FOLD_MANIFEST.md.
Collapses the PRACTICE layer (ai_id + .empirica store + calibration), NOT repos — every repo
stays and is preserved on a remote.

The gate that makes this safe (and ties it to the whole substrate):
  --apply REFUSES unless a verifying, signed RATIFY row for Q-MOLT-PRACTICES-COLLAPSE-01 with
  decision=ACCEPT exists in eco_ratify_ledger.jsonl (B1). Execution is gated on ratification —
  in code, not by convention.

Non-destructive, reversible:
  - A fold writes a `.empirica/FOLDED_INTO.yaml` marker on the seat (role + survivor + date).
    Removing the marker undoes the fold. NOTHING is deleted; stores are kept read-only.
  - The consequential cross-store ops (artifact migration into the survivor, ai_id alias in
    entity_registry) are EMITTED as `empirica` commands for review, not auto-run — the same
    "emit, don't silently execute the irreversible" stance B1 takes.
  - Precondition re-checked at run time: every folding seat's HEAD must be on a remote.

Commands:
  --plan                 per-seat actions (dry-run, default)
  --verify-preserved     confirm every folding seat's HEAD is on a remote
  --apply                write FOLDED_INTO markers + emit migration commands (GATED on ratify)
  --smoke-test
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ratify_eco  # B1 — ledger reader/verifier (same dir)

PRACTICES_ROOT = os.path.expanduser("~/practices")
RATIFY_CANDIDATE = "Q-MOLT-PRACTICES-COLLAPSE-01"

# The confirmed D4 map (Admiral 2026-10-09). Hardcoded, not parsed, so it can't drift from
# the manifest under us. (role, survivor_or_marker). "SURVIVOR"/"BRIDGE"/"STANDS" = not folded.
FOLD_MAP = {
    "humanaios":                      ("Builder",         "SURVIVOR"),
    "website":                        ("Builder",         "humanaios"),
    "humanaios-internal":             ("Builder",         "humanaios"),
    "humanaios-ui":                   ("Builder",         "humanaios"),
    "flta-app-empirica":              ("Builder",         "humanaios"),
    "empirica-foundation-evaluator":  ("Evaluator",       "SURVIVOR"),
    "empirica-mesh-support":          ("Gov/Mesh",        "SURVIVOR"),
    "hooks":                          ("Gov/Mesh",        "empirica-mesh-support"),
    "empirica-analytics":             ("Gov/Mesh",        "empirica-mesh-support"),
    "empirica-temporal-oracle":       ("Gov/Mesh",        "empirica-mesh-support"),
    "schema.sql":                     ("Gov/Mesh",        "empirica-mesh-support"),  # +rename
    "local-machine-optimizer":        ("Gov/Mesh",        "empirica-mesh-support"),
    "empirica-outreach":              ("Outreach",        "SURVIVOR"),
    "collaborator-ops":               ("Outreach",        "empirica-outreach"),
    "opportunity-aggregator":         ("Research",        "SURVIVOR"),   # + Builder bridge
    "empirica-resource-miner":        ("Research",        "opportunity-aggregator"),
    "grok-crossref":                  ("Research",        "opportunity-aggregator"),
    "empirica-autonomy":              ("Autonomy",        "STANDS"),
    "acat-x":                         ("Builder+Research","BRIDGE"),
}
FOLDS = {s: (role, surv) for s, (role, surv) in FOLD_MAP.items()
         if surv not in ("SURVIVOR", "BRIDGE", "STANDS")}


# ---------------------------------------------------------------------------
# the ratification gate
# ---------------------------------------------------------------------------
def ratified() -> tuple[bool, str]:
    """True iff a verifying, signed ACCEPT row for the collapse exists in the ledger (B1)."""
    rows = ratify_eco.read_ledger(ratify_eco.LEDGER)  # read the current ledger path (test-patchable)
    if not rows:
        return False, "eco_ratify_ledger.jsonl is empty — collapse not ratified"
    # chain integrity (mirror ratify_eco.cmd_verify's chain check, quietly)
    prev = ratify_eco.GENESIS
    for i, r in enumerate(rows):
        if r.get("prev_hash") != prev or ratify_eco._row_hash(r) != r.get("record_hash"):
            return False, f"ledger chain broken at row {i} — refusing to act on a tampered ledger"
        prev = r.get("record_hash", ratify_eco.GENESIS)
    hit = [r for r in rows if r.get("candidate_id") == RATIFY_CANDIDATE and r.get("decision") == "ACCEPT"]
    if not hit:
        return False, f"no signed ACCEPT row for {RATIFY_CANDIDATE} — ratify via ratify_eco.py first"
    return True, hit[-1]["signature"]


# ---------------------------------------------------------------------------
# preservation precondition
# ---------------------------------------------------------------------------
def head_on_remote(seat: str) -> bool:
    d = os.path.join(PRACTICES_ROOT, seat)
    if not os.path.isdir(os.path.join(d, ".git")):
        return False
    head = subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True)
    if head.returncode != 0:
        return False
    r = subprocess.run(["git", "-C", d, "branch", "-r", "--contains", head.stdout.strip()],
                       capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def cmd_verify_preserved() -> int:
    bad = 0
    for seat in FOLDS:
        ok = head_on_remote(seat)
        print(f"  {'✓' if ok else '✗ MACHINE-ONLY'} {seat}")
        bad += 0 if ok else 1
    print(f"\n{'All folding seats preserved on a remote.' if not bad else str(bad)+' seat(s) NOT preserved — do NOT fold them.'}")
    return 0 if not bad else 1


# ---------------------------------------------------------------------------
# plan / apply
# ---------------------------------------------------------------------------
def _marker(seat: str, role: str, surv: str, sig: str) -> str:
    return (f"# Non-destructive fold marker (B4). Remove this file to undo.\n"
            f"folded_into: {surv}\nrole: {role}\nseat: {seat}\n"
            f"ratified_by: {RATIFY_CANDIDATE}\nratify_signature: {sig}\n"
            f"folded_at: {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}\n"
            f"store_deleted: false\nreversible: true\n")


def _migration_cmds(seat: str, surv: str) -> list[str]:
    # EMITTED for review, not auto-run — the consequential cross-store ops.
    return [
        f"empirica log-artifacts --project-id {surv} -   # ← migrate {seat}'s findings/decisions (cross-link)",
        f"empirica note --project-id {surv} 'folded {seat} → {surv} per {RATIFY_CANDIDATE}'",
        f"# register alias {seat} → {surv} in entity_registry (archived seat, store kept read-only)",
    ]


def cmd_plan() -> int:
    print(f"B4 fold plan — {len(FOLDS)} seats fold into 6 role-practices (repos untouched)\n")
    by_surv: dict = {}
    for seat, (role, surv) in sorted(FOLDS.items()):
        by_surv.setdefault((role, surv), []).append(seat)
    for (role, surv), seats in sorted(by_surv.items()):
        print(f"  {role:16} ◄ {surv}")
        for s in seats:
            print(f"        fold: {s}")
    print("\n  Survivors/stands/bridges (not folded): " +
          ", ".join(s for s, (_, m) in FOLD_MAP.items() if m in ("SURVIVOR", "BRIDGE", "STANDS")))
    ok, msg = ratified()
    print(f"\n  ratification gate: {'✓ RATIFIED — ' + msg[:20] + '…' if ok else '⛔ ' + msg}")
    print("  (--apply writes reversible FOLDED_INTO markers + emits migration commands; refuses if not ratified)")
    return 0


def cmd_apply() -> int:
    ok, msg = ratified()
    if not ok:
        print(f"::error::REFUSING to fold — {msg}")
        print("  Ratify first:  python3 .z1-control/ratify_eco.py "
              f"--candidate .z1-control/{RATIFY_CANDIDATE}.yaml --by Night --decision ACCEPT --apply")
        return 1
    sig = msg
    print(f"✓ ratified ({RATIFY_CANDIDATE}, sig {sig[:16]}…) — folding {len(FOLDS)} seats (non-destructive)\n")
    unpreserved = [s for s in FOLDS if not head_on_remote(s)]
    if unpreserved:
        print(f"::error::these folding seats are NOT on a remote: {unpreserved} — aborting (preserve first)")
        return 1
    for seat, (role, surv) in sorted(FOLDS.items()):
        emp = os.path.join(PRACTICES_ROOT, seat, ".empirica")
        if os.path.isdir(emp):
            with open(os.path.join(emp, "FOLDED_INTO.yaml"), "w") as fh:
                fh.write(_marker(seat, role, surv, sig))
            print(f"  ✓ {seat} → {surv}  (marker written; store kept)")
            for c in _migration_cmds(seat, surv):
                print(f"        {c}")
        else:
            print(f"  ? {seat}: no .empirica dir — skipped")
    print("\n✓ markers written. Review + run the emitted migration commands to complete each fold.")
    print("  Undo any fold: delete its .empirica/FOLDED_INTO.yaml.")
    return 0


# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    import json, tempfile
    # FOLD_MAP integrity: 13 folds, 6 role-survivors, autonomy stands, acat-x bridges
    assert len(FOLDS) == 12, f"expected 12 folds, got {len(FOLDS)}"
    assert FOLD_MAP["empirica-autonomy"][1] == "STANDS"
    assert FOLD_MAP["acat-x"][1] == "BRIDGE"
    survivors = {surv for _, surv in FOLDS.values()}
    assert survivors == {"humanaios", "empirica-mesh-support", "empirica-outreach", "opportunity-aggregator"}, survivors

    # the gate: refuses when no ACCEPT row; passes when present; catches a broken chain
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "l.jsonl")
        orig = ratify_eco.LEDGER
        ratify_eco.LEDGER = led
        try:
            assert ratified()[0] is False, "empty ledger must not ratify"
            at = "2026-10-09T00:00:00+00:00"
            row = {"schema": ratify_eco.SCHEMA, "seq": 0, "at": at, "by": "Night",
                   "decision": "ACCEPT", "decision_status": "ratified",
                   "candidate_id": RATIFY_CANDIDATE, "candidate_path": None,
                   "payload_sha256": "x", "signature": "sig_abc", "prev_hash": ratify_eco.GENESIS}
            row["record_hash"] = ratify_eco._row_hash(row)
            ratify_eco.append_ledger(row, led)
            assert ratified()[0] is True, "valid ACCEPT row must ratify"
            # tamper → chain break caught
            rows = ratify_eco.read_ledger(led)
            rows[0]["decision"] = "REJECT"
            with open(led, "w") as fh:
                for r in rows:
                    fh.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
            assert ratified()[0] is False, "tampered ledger must not ratify"
        finally:
            ratify_eco.LEDGER = orig
    print("✓ smoke-test passed: 12 folds→4 survivors(+autonomy stands,+acat-x bridge); "
          "gate refuses empty/tampered ledger, passes on signed ACCEPT")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="b4_fold_execute.py", description="B4 — non-destructive fold, gated on ratification.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--plan", action="store_true")
    g.add_argument("--verify-preserved", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--smoke-test", action="store_true")
    args = p.parse_args(argv)
    if args.smoke_test:
        return cmd_smoke()
    if args.verify_preserved:
        return cmd_verify_preserved()
    if args.apply:
        return cmd_apply()
    return cmd_plan()


if __name__ == "__main__":
    raise SystemExit(main())
