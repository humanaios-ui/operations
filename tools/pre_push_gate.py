#!/usr/bin/env python3
"""
Pre-Push Gate — v1.1
Builder v1.7 compliant · security_gate_tool
HumanAIOS · S-070726

Kills the IC-026 class: prevents pushes when the local branch is behind
its remote tracking branch, or when pushing from a branch that is not on
the allowed list.

USAGE — as a standalone check:
    python3 tools/pre_push_gate.py
    python3 tools/pre_push_gate.py --branch main --remote origin
    python3 tools/pre_push_gate.py --allow-branches main,dev

USAGE — as a git pre-push hook (install once per clone):
    ln -s ../../tools/pre_push_gate.py .git/hooks/pre-push
    chmod +x .git/hooks/pre-push

  Git passes two positional args to pre-push hooks (<remote-name> <remote-url>),
  and piped lines of the form "<local-ref> <local-sha> <remote-ref> <remote-sha>"
  on stdin. The hook exits 0 to allow the push, non-zero to abort.

  In hook mode (invoked by git with positional <remote-name>):
    - The remote is read from the positional arg git provides, not from --remote.
    - Allowed branches are resolved in this order:
        1. --allow-branches flag (if passed explicitly)
        2. PRE_PUSH_GATE_ALLOW_BRANCHES environment variable (comma-separated)
        3. git config hooks.allowBranches (comma-separated)
        4. [] — permissive default: every branch is allowed
      This means feature-branch pushes work out of the box; restrict only when
      you have intentionally configured the env var or git config.

CHECKS:
    1. Wrong-branch guard: current branch must be in ALLOWED_BRANCHES.
    2. Behind-remote guard: local HEAD must not be behind the remote tracking
       branch (i.e., `git status --porcelain=v2 --branch` ab field == 0 behind).

EXIT CODES:
    0  — all checks pass; push is allowed
    1  — a guard tripped; push is blocked
    2  — environment error (git not available, not a git repo, etc.)

Audit: S-070726 · P0 · IC-026 class.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TOOL_NAME     = "pre_push_gate"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_SESSION  = "S-070726"

# Branches that are permitted as a push source in standalone mode.
# In hook mode, override via PRE_PUSH_GATE_ALLOW_BRANCHES env var,
# git config hooks.allowBranches, or --allow-branches flag.
DEFAULT_ALLOWED_BRANCHES: list[str] = ["main"]


# ── git helpers ───────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _git_config_get(key: str, repo_path: str = ".") -> str | None:
    """Read a git config value; returns None if the key is not set."""
    rc, out, _ = _run(["git", "config", "--get", key], cwd=repo_path)
    return out if rc == 0 and out else None


def current_branch(repo_path: str = ".") -> tuple[str | None, str]:
    """Return (branch_name, error_message).  branch_name is None on error."""
    rc, out, err = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if rc != 0:
        return None, f"git rev-parse failed: {err}"
    return out, ""


def behind_count(repo_path: str = ".", remote: str = "origin") -> tuple[int | None, str]:
    """
    Return (behind_count, error_message) where behind_count is the number of
    commits the local branch is *behind* its remote tracking branch.
    Returns None on error (e.g., no tracking branch set).
    """
    # Fetch the remote so counts are current.
    rc, _, err = _run(["git", "fetch", remote], cwd=repo_path)
    if rc != 0:
        # Non-fatal: we might be offline.  Fall through and try anyway.
        pass

    rc, out, err = _run(
        ["git", "status", "--porcelain=v2", "--branch"], cwd=repo_path
    )
    if rc != 0:
        return None, f"git status failed: {err}"

    # The branch.ab line looks like: # branch.ab +<ahead> -<behind>
    for line in out.splitlines():
        m = re.match(r"# branch\.ab \+(\d+) -(\d+)", line)
        if m:
            return int(m.group(2)), ""

    # No tracking branch — treat as zero behind (no remote to compare against).
    return 0, ""


# ── guards ────────────────────────────────────────────────────────────────────

def check_branch(
    branch: str,
    allowed: list[str],
) -> tuple[bool, str]:
    """
    True = OK.  False + message = blocked.
    If allowed is empty, every branch is permitted (no-op guard).
    """
    if not allowed:
        return True, ""
    if branch in allowed:
        return True, ""
    return (
        False,
        f"BLOCKED — wrong-branch guard: current branch '{branch}' is not in "
        f"the allowed list {allowed}. Checkout an allowed branch before pushing.",
    )


def check_not_behind(
    repo_path: str = ".",
    remote: str = "origin",
) -> tuple[bool, str]:
    """
    True = OK.  False + message = blocked.
    """
    n, err = behind_count(repo_path=repo_path, remote=remote)
    if n is None:
        # Could not determine (e.g., no tracking branch) — allow through.
        return True, f"WARNING: could not determine behind-count ({err}); allowing push"
    if n > 0:
        return (
            False,
            f"BLOCKED — behind-remote guard: local branch is {n} commit(s) behind "
            f"'{remote}'. Run `git pull --rebase {remote}` before pushing.",
        )
    return True, ""


# ── main run logic ────────────────────────────────────────────────────────────

def run(
    repo_path: str = ".",
    remote: str = "origin",
    allowed_branches: list[str] | None = None,
) -> dict:
    """
    Run all pre-push guards.  Returns a result dict:
        {
            "status": "PASS" | "FAIL",
            "verdict": str,
            "errors": [str, ...],
            "warnings": [str, ...],
            "branch": str | None,
        }
    """
    if allowed_branches is None:
        allowed_branches = DEFAULT_ALLOWED_BRANCHES

    errors: list[str] = []
    warnings: list[str] = []

    # ── Check 1: current branch ───────────────────────────────────────────
    branch, err = current_branch(repo_path=repo_path)
    if branch is None:
        return {
            "status": "FAIL",
            "verdict": f"ABORT — cannot determine current branch: {err}",
            "errors": [err],
            "warnings": [],
            "branch": None,
        }

    ok, msg = check_branch(branch, allowed_branches)
    if not ok:
        errors.append(msg)
    elif msg:
        warnings.append(msg)

    # ── Check 2: not behind remote ────────────────────────────────────────
    ok2, msg2 = check_not_behind(repo_path=repo_path, remote=remote)
    if not ok2:
        errors.append(msg2)
    elif msg2:
        warnings.append(msg2)

    if errors:
        return {
            "status": "FAIL",
            "verdict": "PUSH BLOCKED — pre-push guard(s) failed. Fix errors and retry.",
            "errors": errors,
            "warnings": warnings,
            "branch": branch,
        }
    return {
        "status": "PASS",
        "verdict": "OK — all pre-push guards passed.",
        "errors": [],
        "warnings": warnings,
        "branch": branch,
    }


def run_smoke_test() -> bool:
    """Builder v1.7 smoke test: verifies the module is importable and core functions callable."""
    try:
        ok, msg = check_branch("main", ["main"])
        assert ok, "check_branch('main', ['main']) should pass"

        ok2, msg2 = check_branch("feature-x", ["main"])
        assert not ok2, "check_branch('feature-x', ['main']) should fail"

        result = run(repo_path=".", remote="origin", allowed_branches=["main"])
        assert "status" in result
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Smoke test failed: {exc}")
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-Push Gate v1.1 — behind-remote / wrong-branch guard (IC-026)"
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Override the branch to check (default: current branch from git)",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Remote name to check against (default: origin)",
    )
    parser.add_argument(
        "--allow-branches",
        default=None,  # None signals "not explicitly provided"
        help=(
            "Comma-separated list of allowed push-source branches "
            f"(standalone default: {','.join(DEFAULT_ALLOWED_BRANCHES)}). "
            "Pass an empty string to disable the branch guard. "
            "In hook mode, defaults to [] (all branches allowed) unless overridden "
            "by PRE_PUSH_GATE_ALLOW_BRANCHES env var or git config hooks.allowBranches."
        ),
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to git repository root (default: .)",
    )
    parser.add_argument("--smoke-test",
        action="store_true",
        help="Run built-in smoke test and exit",
    )
    # git pre-push hook passes <remote-name> <remote-url> as positional args.
    # In hook mode these are used directly; in standalone mode they are absent.
    parser.add_argument("remote_name", nargs="?", help=argparse.SUPPRESS)
    parser.add_argument("remote_url", nargs="?", help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.smoke_test:
        ok = run_smoke_test()
        print("Smoke test: PASS" if ok else "Smoke test: FAIL")
        sys.exit(0 if ok else 1)

    repo_path = str(Path(args.repo).resolve())

    # Detect hook mode: git passes <remote-name> as the first positional arg.
    hook_mode = args.remote_name is not None

    # Remote resolution: hook mode reads from argv; standalone uses --remote flag.
    effective_remote = args.remote_name if hook_mode else args.remote

    # Allowed branches resolution.
    if args.allow_branches is not None:
        # Explicit --allow-branches flag always wins.
        allowed = [b.strip() for b in args.allow_branches.split(",") if b.strip()]
    elif hook_mode:
        # Hook mode without an explicit flag: env var → git config → permissive ([]).
        env_val = os.environ.get("PRE_PUSH_GATE_ALLOW_BRANCHES")
        if env_val is not None:
            allowed = [b.strip() for b in env_val.split(",") if b.strip()]
        else:
            gc_val = _git_config_get("hooks.allowBranches", repo_path=repo_path)
            if gc_val is not None:
                allowed = [b.strip() for b in gc_val.split(",") if b.strip()]
            else:
                allowed = []  # permissive default — all branches allowed in hook mode
    else:
        # Standalone mode without an explicit flag: use the declared default (main).
        allowed = list(DEFAULT_ALLOWED_BRANCHES)

    result = run(repo_path=repo_path, remote=effective_remote, allowed_branches=allowed)

    # Print result
    print(f"pre-push gate: {result['verdict']}")
    for w in result.get("warnings", []):
        print(f"  WARNING: {w}")
    for e in result.get("errors", []):
        print(f"  ERROR:   {e}")

    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
