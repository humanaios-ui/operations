#!/usr/bin/env python3
"""leak_guard.py — B6: bound the two Empirica session leaks.

Substrate Map build item B6. A janitor for the two leaks proven necessary 2026-10-09:
  - open transactions never POSTFLIGHTed — 93 stale active_transaction_term_*.json across 18 practices
  - pre-compact auto-stashes never pruned — 70 (56 on the evaluator in a single morning)

Design rules, learned the hard way this session:
  - SAFE BY DEFAULT. --scan and the dry-run plans mutate nothing. Destruction needs --apply.
  - ARCHIVE BEFORE DELETE. Transactions are tar'd to ~/ before any removal.
  - NEVER TOUCH GENUINE WIP. Stash pruning only ever selects `empirica: pre-compact` auto-stashes;
    a human's WIP stash is never in the drop set, even with --apply.

The selection logic is pure functions (tested by --smoke-test); git/fs I/O only wraps them.
Intended to run on a SessionEnd hook and/or a periodic cron — see --install-hint.

Commands:
  --scan                                    report open transactions + stash split (read-only)
  --close-transactions [--older-than MIN] [--apply]   archive + remove stale txn files
  --bound-stashes [--keep N] [--apply]      drop pre-compact stashes beyond newest N per repo
  --install-hint                            print the SessionEnd-hook / cron wiring
  --smoke-test
"""
from __future__ import annotations

import argparse
import datetime
import glob
import os
import subprocess
import sys

DEFAULT_ROOT = os.path.expanduser("~/practices")
PRECOMPACT_MARK = "empirica: pre-compact"


# ---------------------------------------------------------------------------
# pure selection logic (the part that must be correct — tested directly)
# ---------------------------------------------------------------------------
def select_stale_transactions(files_with_mtime: list[tuple[str, float]], now: float,
                              older_than_min: int) -> list[str]:
    """Return paths older than the cutoff. A transaction touched recently may be a LIVE
    session's window — never sweep it."""
    cutoff = now - older_than_min * 60
    return [p for p, m in files_with_mtime if m <= cutoff]


def classify_stashes(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split stash entries into (pre_compact, wip). `entries` are newest-first (stash@{0} newest).
    A stash is pre-compact only if its subject carries the empirica pre-compact marker; everything
    else — including anything a human wrote — is WIP and is protected."""
    pre = [e for e in entries if PRECOMPACT_MARK in e["subject"]]
    wip = [e for e in entries if PRECOMPACT_MARK not in e["subject"]]
    return pre, wip


def select_stashes_to_drop(entries: list[dict], keep: int) -> list[dict]:
    """Of the PRE-COMPACT stashes, keep the newest `keep`; return the rest to drop.
    WIP stashes are never returned. Caller drops highest index first (indices shift on drop)."""
    pre, _wip = classify_stashes(entries)
    return pre[keep:]  # entries are newest-first, so [keep:] is everything past the newest N


# ---------------------------------------------------------------------------
# io wrappers
# ---------------------------------------------------------------------------
def find_practices(root: str) -> list[str]:
    return sorted(d for d in glob.glob(os.path.join(root, "*"))
                  if os.path.isdir(os.path.join(d, ".empirica")))


def txn_files(practice: str) -> list[tuple[str, float]]:
    out = []
    for p in glob.glob(os.path.join(practice, ".empirica", "active_transaction_term_*.json")):
        try:
            out.append((p, os.path.getmtime(p)))
        except OSError:
            pass
    return out


def stash_entries(repo: str) -> list[dict]:
    """git stash list → [{ref, subject}], newest-first. [] if not a repo / no stashes."""
    try:
        r = subprocess.run(["git", "-C", repo, "stash", "list", "--format=%gd%x09%gs"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    entries = []
    for line in r.stdout.splitlines():
        if "\t" in line:
            ref, subject = line.split("\t", 1)
            entries.append({"ref": ref.strip(), "subject": subject.strip()})
    return entries


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------
def cmd_scan(root: str) -> int:
    practices = find_practices(root)
    tot_txn = tot_pre = tot_wip = 0
    print(f"leak-guard scan · {len(practices)} practices under {root}\n")
    print(f"  {'practice':32} {'open-txn':>8} {'pre-compact':>12} {'wip-stash':>10}")
    for d in practices:
        n_txn = len(txn_files(d))
        pre, wip = classify_stashes(stash_entries(d))
        tot_txn += n_txn; tot_pre += len(pre); tot_wip += len(wip)
        if n_txn or pre or wip:
            print(f"  {os.path.basename(d):32} {n_txn:>8} {len(pre):>12} {len(wip):>10}")
    print(f"\n  {'TOTAL':32} {tot_txn:>8} {tot_pre:>12} {tot_wip:>10}")
    print(f"\n  open transactions leaking: {tot_txn} · prunable pre-compact stashes: {tot_pre} "
          f"· protected WIP stashes: {tot_wip}")
    if tot_txn or tot_pre:
        print("  → close-transactions / bound-stashes (dry-run first; --apply to act).")
    return 0


def cmd_close_transactions(root: str, older_than_min: int, apply: bool) -> int:
    practices = find_practices(root)
    now = datetime.datetime.now().timestamp()
    stale = []
    for d in practices:
        stale += select_stale_transactions(txn_files(d), now, older_than_min)
    if not stale:
        print(f"No transactions older than {older_than_min} min. Nothing to close.")
        return 0
    stamp = datetime.date.today().isoformat()
    arc = os.path.expanduser(f"~/empirica-txn-archive-{stamp}.tgz")
    if not apply:
        print(f"[dry-run] would archive + remove {len(stale)} stale transaction file(s) "
              f"(older than {older_than_min} min) → {arc}")
        for p in stale[:8]:
            print(f"    {p}")
        if len(stale) > 8:
            print(f"    … and {len(stale) - 8} more")
        print("  re-run with --apply to act.")
        return 0
    # archive first (reversible floor), then remove
    import tarfile
    with tarfile.open(arc, "a:gz" if os.path.exists(arc) else "w:gz") as tf:
        for p in stale:
            tf.add(p, arcname=os.path.relpath(p, os.path.expanduser("~")))
    removed = 0
    for p in stale:
        try:
            os.remove(p); removed += 1
        except OSError as e:
            print(f"  !! could not remove {p}: {e}")
    print(f"✓ archived {len(stale)} → {arc}, removed {removed} stale transaction file(s).")
    return 0


def cmd_bound_stashes(root: str, keep: int, apply: bool) -> int:
    practices = find_practices(root)
    plan = []  # (repo, [refs-to-drop newest-first], wip_count)
    for d in practices:
        entries = stash_entries(d)
        if not entries:
            continue
        drop = select_stashes_to_drop(entries, keep)
        _pre, wip = classify_stashes(entries)
        if drop:
            plan.append((d, [e["ref"] for e in drop], len(wip)))
    if not plan:
        print(f"No pre-compact stashes beyond the newest {keep} per repo. Nothing to prune.")
        return 0
    total = sum(len(refs) for _, refs, _ in plan)
    for d, refs, wip in plan:
        print(f"  {os.path.basename(d):32} drop {len(refs):>3} pre-compact "
              f"(keep {keep}; {wip} WIP protected)")
    if not apply:
        print(f"\n[dry-run] would drop {total} pre-compact auto-stash(es) across "
              f"{len(plan)} repo(s). WIP stashes never touched. Re-run with --apply.")
        return 0
    dropped = 0
    for d, refs, _ in plan:
        # Drop highest index first: stash@{N} indices shift down as earlier ones are removed.
        for ref in sorted(refs, key=lambda r: int(r.strip("stash@{}") or 0), reverse=True):
            r = subprocess.run(["git", "-C", d, "stash", "drop", ref],
                               capture_output=True, text=True)
            if r.returncode == 0:
                dropped += 1
            else:
                print(f"  !! {os.path.basename(d)} {ref}: {r.stderr.strip()}")
    print(f"✓ dropped {dropped} pre-compact auto-stash(es); all WIP stashes left intact.")
    return 0


def cmd_install_hint() -> int:
    print("""Wire leak-guard so the leaks can't re-accumulate:

  # 1. SessionEnd hook (close THIS session's transactions as it exits) — .claude/settings.json:
  #    "hooks": { "SessionEnd": [ { "hooks": [ { "type": "command",
  #      "command": "python3 .z1-control/leak_guard.py --close-transactions --older-than 0 --apply" } ] } ] }
  #
  # 2. Periodic janitor (bound the stash graveyard) — cron or a canonical loop, daily:
  #    python3 .z1-control/leak_guard.py --bound-stashes --keep 3 --apply
  #
  # Both are safe: transactions are archived before removal; only empirica:pre-compact
  # stashes are ever dropped. The deeper fix — capping the stash at CREATION in the
  # empirica pre-compact mechanism — lives in the empirica package, not here; this janitor
  # bounds the symptom until that lands.""")
    return 0


# ---------------------------------------------------------------------------
# smoke-test (pure logic; CI-wired beside ratify.py / candidate_bundle.py)
# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    now = 1_000_000.0
    files = [("a.json", now - 100), ("b.json", now - 60 * 60 * 24), ("c.json", now - 30)]
    stale = select_stale_transactions(files, now, older_than_min=720)  # 12h
    assert stale == ["b.json"], f"only the day-old txn is stale: {stale}"
    assert select_stale_transactions(files, now, 0) == ["a.json", "b.json", "c.json"], \
        "--older-than 0 sweeps all (SessionEnd mode)"

    entries = [  # newest-first, as git returns
        {"ref": "stash@{0}", "subject": "On main: empirica: pre-compact abc - 07:40"},
        {"ref": "stash@{1}", "subject": "WIP on feature: real human work"},     # WIP — protected
        {"ref": "stash@{2}", "subject": "On main: empirica: pre-compact abc - 07:38"},
        {"ref": "stash@{3}", "subject": "On main: empirica: pre-compact abc - 07:36"},
        {"ref": "stash@{4}", "subject": "On governance: Phase 1 authorization"},  # WIP — protected
    ]
    pre, wip = classify_stashes(entries)
    assert len(pre) == 3 and len(wip) == 2, "classify split wrong"
    drop = select_stashes_to_drop(entries, keep=1)
    drop_refs = {e["ref"] for e in drop}
    assert drop_refs == {"stash@{2}", "stash@{3}"}, f"keep newest 1 pre-compact, drop rest: {drop_refs}"
    # the load-bearing invariant: NO wip stash is ever selected for dropping
    assert all(PRECOMPACT_MARK in e["subject"] for e in drop), "WIP leaked into drop set!"
    assert select_stashes_to_drop(entries, keep=10) == [], "keep>count drops nothing"

    print("✓ smoke-test passed: stale-txn cutoff (incl SessionEnd --older-than 0); "
          "stash classify; keep-newest-N; WIP never in drop set")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="leak_guard.py", description="B6 — bound Empirica session leaks.")
    p.add_argument("--root", default=DEFAULT_ROOT, help=f"practices root (default {DEFAULT_ROOT})")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--scan", action="store_true")
    g.add_argument("--close-transactions", action="store_true")
    g.add_argument("--bound-stashes", action="store_true")
    g.add_argument("--install-hint", action="store_true")
    g.add_argument("--smoke-test", action="store_true")
    p.add_argument("--older-than", type=int, default=720, help="transaction age cutoff in minutes (default 720)")
    p.add_argument("--keep", type=int, default=3, help="pre-compact stashes to keep per repo (default 3)")
    p.add_argument("--apply", action="store_true", help="actually act (default: dry-run)")
    args = p.parse_args(argv)

    if args.smoke_test:
        return cmd_smoke()
    if args.install_hint:
        return cmd_install_hint()
    if args.scan:
        return cmd_scan(args.root)
    if args.close_transactions:
        return cmd_close_transactions(args.root, args.older_than, args.apply)
    if args.bound_stashes:
        return cmd_bound_stashes(args.root, args.keep, args.apply)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
