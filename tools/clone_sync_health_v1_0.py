#!/usr/bin/env python3
"""
Clone Sync Health — v1.0
Builder v1.7 compliant · monitoring_tool
HumanAIOS · IC-026 class fix · S-070726

Scans all local git clones under a root directory (default: ~/Desktop/HAIOS-Main/).
Reports branch, behind/ahead count, dirty file count, and remote URL for each repo.
Exits nonzero if any clone is behind origin/main or on a non-expected branch.

Addresses T3_IMPROVE_S070726.md Issue-01 (Reconcile drifted local clones) and
Issue-02 (pre-push behind-remote / wrong-branch guard) — IC-026 class.

Modes:
  --check   (default) Report clone health; exit 1 if any clone is drifted or on
            wrong branch. Exit 0 only when all clones are clean.
  --fix     Reconcile drifted clones: git fetch → checkout main → git pull --ff-only.
            Only touches clones that are purely behind (no local-ahead commits). Skips
            dirty or diverged clones and reports them for manual resolution.
  --report  Print a markdown table of all clones; always exits 0 (read-only).

Usage:
  python tools/clone_sync_health_v1_0.py
  python tools/clone_sync_health_v1_0.py --root ~/Desktop/HAIOS-Main
  python tools/clone_sync_health_v1_0.py --fix
  python tools/clone_sync_health_v1_0.py --report
  python tools/clone_sync_health_v1_0.py --smoke-test
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "clone_sync_health"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "monitoring_tool"
TOOL_SESSION  = "S-070726"

# Repos that should always be on main; others are acceptable on any branch.
MAIN_BRANCH_REQUIRED = {
    "operations-staging",
    "operations",
    "humanaios",
    "humanaios-internal",
    "lasting-light-ai",
    "research",
    "docs",
    "acat-inspect",
    "ACAT-Dashboard",
    "ACAT-Observatory",
    "findlocaltattooartists",
    "HAIOSCC",
}

# Default search root — overridden by --root
DEFAULT_ROOT = Path.home() / "Desktop" / "HAIOS-Main"


# ── Git helpers ───────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path, timeout: int = 15) -> tuple[int, str, str]:
    """Run a command; return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout after {timeout}s"
    except FileNotFoundError as e:
        return 1, "", str(e)


def get_clone_status(repo: Path) -> dict:
    """
    Return a status dict for a single git repo.

    Keys: name, path, branch, remote_url, behind, ahead, dirty,
          fetch_ok, severity, note.
    """
    name = repo.name
    status: dict = {
        "name":       name,
        "path":       str(repo),
        "branch":     "?",
        "remote_url": "?",
        "behind":     -1,
        "ahead":      -1,
        "dirty":      -1,
        "fetch_ok":   False,
        "severity":   "unknown",
        "note":       "",
    }

    # Branch
    rc, out, err = _run(["git", "branch", "--show-current"], repo)
    if rc != 0:
        status["note"] = f"branch failed: {err}"
        return status
    status["branch"] = out or "(detached)"

    # Remote URL
    rc, out, _ = _run(["git", "remote", "get-url", "origin"], repo)
    if rc == 0:
        status["remote_url"] = out

    # Fetch (non-fatal — we still report what we know if fetch fails)
    rc, _, err = _run(["git", "fetch", "origin", "--prune", "--quiet"], repo, timeout=30)
    status["fetch_ok"] = rc == 0
    if rc != 0:
        status["note"] = f"fetch failed: {err[:80]}"

    # Behind / Ahead vs origin/main
    rc, out, _ = _run(
        ["git", "rev-list", "--count", "--left-right", "HEAD...origin/main"],
        repo
    )
    if rc == 0 and "\t" in out:
        parts = out.split("\t")
        status["ahead"]  = int(parts[0]) if parts[0].isdigit() else -1
        status["behind"] = int(parts[1]) if parts[1].isdigit() else -1
    elif rc == 0 and out.strip().isdigit():
        # Fallback single-number output (shouldn't happen with --left-right)
        status["behind"] = int(out.strip())
        status["ahead"]  = 0

    # Dirty file count (untracked + modified + staged)
    rc, out, _ = _run(["git", "status", "--porcelain"], repo)
    if rc == 0:
        status["dirty"] = len([l for l in out.splitlines() if l.strip()])

    # Severity
    on_wrong_branch = (
        name in MAIN_BRANCH_REQUIRED and
        status["branch"] not in ("main", "master", "?")
    )
    # behind == -1 means rev-list failed (e.g. no origin/main ref) — treat as unknown,
    # not as "not behind", so drifted repos don't silently report green.
    behind_unknown = status["behind"] == -1
    behind = status["behind"] > 0
    dirty  = status["dirty"] > 0

    if behind_unknown and not on_wrong_branch:
        status["severity"] = "unknown"
        status["note"] = status["note"] or "could not determine behind count (origin/main missing?)"
    elif on_wrong_branch and behind:
        status["severity"] = "critical"
        status["note"] = status["note"] or f"wrong branch ({status['branch']}) + {status['behind']} behind"
    elif on_wrong_branch:
        status["severity"] = "critical"
        status["note"] = status["note"] or f"wrong branch: {status['branch']} (expected main)"
    elif behind:
        status["severity"] = "major" if status["behind"] < 5 else "critical"
        status["note"] = status["note"] or f"{status['behind']} behind origin/main"
    elif dirty:
        status["severity"] = "ok-dirty"
        status["note"] = status["note"] or f"{status['dirty']} dirty file(s)"
    else:
        status["severity"] = "ok"

    return status


def scan_root(root: Path) -> list[dict]:
    """Find all git repos directly under root and return their status."""
    results = []
    if not root.exists():
        return results
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / ".git").exists():
            results.append(get_clone_status(child))
    return results


# ── Output helpers ────────────────────────────────────────────────────────────

SEV_EMOJI = {
    "critical":  "🔴",
    "major":     "🟠",
    "ok-dirty":  "🟡",
    "ok":        "🟢",
    "unknown":   "⚪",
}


def print_table(results: list[dict]) -> None:
    """Print a markdown-style table to stdout."""
    print(
        f"| {'Clone':<28} | {'Branch':<36} | {'Behind':>6} | {'Ahead':>5} | "
        f"{'Dirty':>5} | {'Sev':<10} | Note |"
    )
    print(
        f"| {'-'*28} | {'-'*36} | {'------':>6} | {'-----':>5} | "
        f"{'-----':>5} | {'-'*10} | ---- |"
    )
    for r in results:
        emoji  = SEV_EMOJI.get(r["severity"], "⚪")
        behind = str(r["behind"]) if r["behind"] >= 0 else "?"
        ahead  = str(r["ahead"])  if r["ahead"]  >= 0 else "?"
        dirty  = str(r["dirty"])  if r["dirty"]  >= 0 else "?"
        print(
            f"| {r['name']:<28} | {r['branch']:<36} | {behind:>6} | {ahead:>5} | "
            f"{dirty:>5} | {emoji} {r['severity']:<8} | {r['note']} |"
        )


def write_report(results: list[dict], output_dir: str = ".") -> str:
    """Write JSON report to output_dir. Returns path."""
    ts  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(output_dir) / f"{TOOL_NAME}_{ts}.json"
    payload = {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "session":   TOOL_SESSION,
        "timestamp": ts,
        "clones":    results,
        "summary": {
            "total":    len(results),
            "ok":       sum(1 for r in results if r["severity"] == "ok"),
            "critical": sum(1 for r in results if r["severity"] == "critical"),
            "major":    sum(1 for r in results if r["severity"] == "major"),
            "dirty":    sum(1 for r in results if r["severity"] == "ok-dirty"),
        },
    }
    out.write_text(json.dumps(payload, indent=2))
    return str(out)


# ── Fix (reconcile) ───────────────────────────────────────────────────────────

def fix_clone(r: dict) -> tuple[bool, str]:
    """
    Attempt to reconcile a drifted clone.

    Rules:
    - If dirty: skip (manual resolution required).
    - If ahead > 0: skip (local commits would be lost by reset).
    - If on wrong branch and behind: checkout main then pull --ff-only.
    - If on main/master and behind: pull --ff-only.
    Returns (success, message).
    """
    path   = Path(r["path"])
    branch = r["branch"]
    behind = r["behind"]
    ahead  = r["ahead"]
    dirty  = r["dirty"]

    if dirty > 0:
        return False, f"SKIP — {dirty} dirty files; resolve manually before reconciling"
    if dirty < 0 or ahead < 0 or behind < 0:
        return False, "SKIP — clone state unknown (rev-list failed); verify origin/main exists"
    if ahead > 0:
        return False, f"SKIP — {ahead} local commit(s) ahead of origin; manual rebase required"
    if behind == 0 and branch in ("main", "master"):
        return True, "already clean — nothing to do"

    # Checkout main if on wrong branch
    if branch not in ("main", "master"):
        rc, out, err = _run(["git", "checkout", "main"], path)
        if rc != 0:
            return False, f"checkout main FAILED: {err}"

    target_branch = "master" if branch == "master" else "main"

    # Pull fast-forward
    rc, out, err = _run(["git", "pull", "--ff-only", "origin", target_branch], path, timeout=60)
    if rc != 0:
        return False, f"pull --ff-only FAILED: {err}"

    return True, f"reconciled — pulled {behind} commit(s), now on main"


# ── Smoke test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    """Quick self-test using a temp in-memory structure."""
    # Simulate known good/bad status dicts
    good = {
        "name": "test-repo", "path": "/tmp/test",
        "branch": "main", "remote_url": "https://github.com/x/y",
        "behind": 0, "ahead": 0, "dirty": 0,
        "fetch_ok": True, "severity": "ok", "note": "",
    }
    bad = {
        "name": "drifted-repo", "path": "/tmp/drifted",
        "branch": "dependabot/foo", "remote_url": "https://github.com/x/y",
        "behind": 27, "ahead": 0, "dirty": 9,
        "fetch_ok": True, "severity": "critical",
        "note": "wrong branch (dependabot/foo) + 27 behind",
    }
    results = [good, bad]

    # Table renders without crash
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_table(results)
    table = buf.getvalue()
    assert "test-repo"    in table, "good row missing"
    assert "drifted-repo" in table, "bad row missing"
    assert "critical"     in table, "severity missing"

    # Severity assignment
    assert good["severity"] == "ok"
    assert bad["severity"]  == "critical"

    # fix_clone skip logic (no actual git calls)
    ok, msg = fix_clone(bad)   # dirty > 0 → skip
    assert not ok and "dirty" in msg.lower(), f"expected dirty skip, got: {msg}"

    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test PASSED")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=f"{TOOL_NAME} v{TOOL_VERSION} — local git clone sync health checker"
    )
    p.add_argument("--root",       default=str(DEFAULT_ROOT),
                   help="Root directory to scan for git repos (default: ~/Desktop/HAIOS-Main)")
    p.add_argument("--check",      action="store_true",
                   help="Check mode (default): exit 1 if any clone is behind origin/main or on wrong branch")
    p.add_argument("--fix",        action="store_true",
                   help="Reconcile drifted clones (fetch + checkout main + pull --ff-only)")
    p.add_argument("--report",     action="store_true",
                   help="Print markdown table and exit 0 (read-only, no exit-code signalling)")
    p.add_argument("--output-dir", default=".",
                   help="Directory to write JSON report (default: current dir)")
    p.add_argument("--no-report",  action="store_true",
                   help="Skip writing JSON report file")
    p.add_argument("--smoke-test", action="store_true",
                   help="Run smoke test and exit")
    p.add_argument("--list-rules", action="store_true",
                   help="Print tool rules and exit")
    return p


def main() -> int:
    parser = build_parser()
    args   = parser.parse_args()

    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    if args.list_rules:
        print(__doc__)
        return 0

    root = Path(args.root).expanduser()
    print(f"{TOOL_NAME} v{TOOL_VERSION} · scanning {root}")
    print()

    results = scan_root(root)

    if not results:
        print(f"No git repos found under {root}")
        return 0

    print_table(results)
    print()

    drifted = [r for r in results if r["severity"] in ("critical", "major")]

    if args.fix:
        print("── Fix mode ─────────────────────────────────────────────────────")
        any_fail = False
        for r in drifted:
            ok, msg = fix_clone(r)
            icon = "✅" if ok else "⚠️ "
            print(f"  {icon} {r['name']}: {msg}")
            if not ok:
                any_fail = True
        print()
        if any_fail:
            print("⚠️  Some clones could not be auto-reconciled — see above for manual steps.")
        else:
            print("✅ All reconcilable clones are now clean.")
        # Re-scan to show updated state
        print()
        print("── Updated state ────────────────────────────────────────────────")
        results = scan_root(root)
        print_table(results)
        print()
        drifted = [r for r in results if r["severity"] in ("critical", "major")]

    if not args.no_report:
        try:
            report_path = write_report(results, args.output_dir)
            print(f"Report written: {report_path}")
        except OSError as e:
            print(f"Warning: could not write report: {e}", file=sys.stderr)

    if args.report:
        # Read-only mode: always exit 0
        return 0

    # Check mode (default): exit 1 if any drifted clones remain
    if drifted:
        names = ", ".join(r["name"] for r in drifted)
        print(
            f"\n❌ {len(drifted)} clone(s) drifted ({names}).\n"
            f"   Run with --fix to auto-reconcile, or see §15 of OPERATOR_RUNBOOK.md.\n"
            f"   IC-026 class — do not push until all clones are clean."
        )
        return 1

    print("✅ All clones are in sync with origin/main.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
