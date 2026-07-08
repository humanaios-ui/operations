"""
test_pre_push_gate.py
Builder v1.7 compliant - pre_push_gate_tests
HumanAIOS - S-070826-compliance-hardening
Tests for tools/pre_push_gate.py (IC-026 guard — S-070726).
Builder v1.7 compliant — test_pre_push_gate_tool
HumanAIOS — S-070726-test-pre-push-gate

Covers:
  1. check_branch  — allowed / wrong-branch logic
  2. check_not_behind — behind-remote detection using a real local git setup
  3. run()         — integration: stale push blocked, wrong branch blocked, happy path
  4. hook mode     — remote from argv, permissive default, env var / git config overrides

Run:
    pytest tools/tests/test_pre_push_gate.py -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover - allows local smoke execution without pytest
    pytest = None

TOOL_NAME = "test_pre_push_gate"
TOOL_VERSION = "1.0.0"

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from pre_push_gate import (
    check_branch,
    check_not_behind,
    run,
    run_smoke_test as module_run_smoke_test,
)

TOOL_NAME = "test_pre_push_gate"
TOOL_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _git(cmd: list[str], cwd: str) -> None:
    """Run a git command, raising on failure."""
    subprocess.run(["git"] + cmd, cwd=cwd, check=True,
                   capture_output=True, text=True)


def _make_repo_pair(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create a 'remote' bare repo and a 'local' clone of it with one commit.
    Returns (local_path, remote_path).
    """
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    remote.mkdir()
    local.mkdir()

    _git(["init", "--bare", str(remote)], cwd=str(tmp_path))
    # Ensure the bare repo HEAD points to main (git <2.28 defaults to master;
    # git >=2.45.1 blocks symbolic-ref on implicit bare repos via
    # safe.bareRepository=explicit).  Writing the file is always portable.
    (remote / "HEAD").write_text("ref: refs/heads/main\n")

    _git(["init", str(local)], cwd=str(tmp_path))
    # Set initial branch name to main regardless of system default.
    subprocess.run(
        ["git", "checkout", "-b", "main"],
        cwd=str(local), capture_output=True
    )
    _git(["config", "user.email", "test@example.com"], cwd=str(local))
    _git(["config", "user.name", "Test"], cwd=str(local))
    _git(["remote", "add", "origin", str(remote)], cwd=str(local))

    # Initial commit
    (local / "README.md").write_text("init\n")
    _git(["add", "README.md"], cwd=str(local))
    _git(["commit", "-m", "init"], cwd=str(local))
    _git(["push", "-u", "origin", "main"], cwd=str(local))

    return local, remote


def _advance_remote(remote: Path, local: Path) -> None:
    """
    Make the remote one commit ahead of the local clone so that local is *behind*.
    We do this by cloning the remote into a second local copy, committing there,
    and pushing — simulating another contributor's push.
    """
    import tempfile as _tmp
    with _tmp.TemporaryDirectory() as other_dir:
        other = Path(other_dir) / "other"
        subprocess.run(
            ["git", "clone", str(remote), str(other)],
            check=True, capture_output=True, text=True,
        )
        _git(["config", "user.email", "other@example.com"], cwd=str(other))
        _git(["config", "user.name", "Other"], cwd=str(other))
        (other / "OTHER.md").write_text("new commit from other\n")
        _git(["add", "OTHER.md"], cwd=str(other))
        _git(["commit", "-m", "other contributor commit"], cwd=str(other))
        _git(["push", "origin", "main"], cwd=str(other))


def _advance_remote_branch(remote: Path, branch: str) -> None:
    """Advance a specific branch on the remote so local is behind on that branch."""
    import tempfile as _tmp
    with _tmp.TemporaryDirectory() as other_dir:
        other = Path(other_dir) / "other"
        subprocess.run(
            ["git", "clone", "--branch", branch, str(remote), str(other)],
            check=True, capture_output=True, text=True,
        )
        _git(["config", "user.email", "other@example.com"], cwd=str(other))
        _git(["config", "user.name", "Other"], cwd=str(other))
        (other / f"REMOTE_{branch}.md").write_text(f"remote advance on {branch}\n")
        _git(["add", "."], cwd=str(other))
        _git(["commit", "-m", f"remote advance on {branch}"], cwd=str(other))
        _git(["push", "origin", branch], cwd=str(other))


# ─────────────────────────────────────────────────────────────────────────────
# check_branch
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckBranch:

    def test_allowed_branch_passes(self):
        ok, msg = check_branch("main", ["main"])
        assert ok
        assert msg == ""

    def test_allowed_branch_in_list_passes(self):
        ok, msg = check_branch("dev", ["main", "dev"])
        assert ok

    def test_wrong_branch_is_blocked(self):
        ok, msg = check_branch("feature-x", ["main"])
        assert not ok
        assert "BLOCKED" in msg
        assert "feature-x" in msg
        assert "main" in msg

    def test_empty_allowed_list_allows_any_branch(self):
        """An empty allowed list disables the branch guard."""
        ok, msg = check_branch("any-branch", [])
        assert ok

    def test_case_sensitive_mismatch_is_blocked(self):
        ok, _ = check_branch("Main", ["main"])
        assert not ok


# ─────────────────────────────────────────────────────────────────────────────
# check_not_behind  — uses real git repos in temp dirs
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckNotBehind:

    def test_up_to_date_branch_passes(self, tmp_path):
        local, remote = _make_repo_pair(tmp_path)
        ok, msg = check_not_behind(repo_path=str(local), remote="origin")
        assert ok, f"Expected PASS but got: {msg}"

    def test_behind_remote_is_blocked(self, tmp_path):
        """
        Core acceptance criterion: a deliberately-stale push is blocked.

        Steps:
          1. Create local clone and matching remote.
          2. Advance the remote by one commit (another contributor pushed).
          3. check_not_behind() must return False (blocked).
        """
        local, remote = _make_repo_pair(tmp_path)
        _advance_remote(remote, local)
        # local is now behind by 1 commit
        ok, msg = check_not_behind(repo_path=str(local), remote="origin")
        assert not ok, "Expected stale push to be BLOCKED but it passed"
        assert "BLOCKED" in msg
        assert "behind" in msg.lower()

    def test_no_tracking_branch_does_not_block(self, tmp_path):
        """If no upstream is set, the guard must not block (cannot determine)."""
        local = tmp_path / "untracked"
        local.mkdir()
        _git(["init", "-b", "main", str(local)], cwd=str(tmp_path))
        _git(["config", "user.email", "t@t.com"], cwd=str(local))
        _git(["config", "user.name", "T"], cwd=str(local))
        (local / "f.txt").write_text("x")
        _git(["add", "f.txt"], cwd=str(local))
        _git(["commit", "-m", "lone commit"], cwd=str(local))
        # No remote configured → fetch will fail → gate should allow
        ok, msg = check_not_behind(repo_path=str(local), remote="origin")
        assert ok, f"Expected no-tracking to PASS, got blocked: {msg}"


# ─────────────────────────────────────────────────────────────────────────────
# run() — integration
# ─────────────────────────────────────────────────────────────────────────────

class TestRunIntegration:

    def test_up_to_date_main_branch_passes(self, tmp_path):
        local, remote = _make_repo_pair(tmp_path)
        result = run(repo_path=str(local), remote="origin", allowed_branches=["main"])
        assert result["status"] == "PASS"
        assert result["branch"] == "main"

    def test_stale_push_blocked(self, tmp_path):
        """
        Acceptance criterion: `run()` returns FAIL when local is behind remote.
        """
        local, remote = _make_repo_pair(tmp_path)
        _advance_remote(remote, local)
        result = run(repo_path=str(local), remote="origin", allowed_branches=["main"])
        assert result["status"] == "FAIL"
        assert any("behind" in e.lower() for e in result["errors"])

    def test_wrong_branch_blocked(self, tmp_path):
        """run() returns FAIL when pushing from a non-allowed branch."""
        local, remote = _make_repo_pair(tmp_path)
        # Create and checkout a feature branch
        _git(["checkout", "-b", "feature-test"], cwd=str(local))
        result = run(repo_path=str(local), remote="origin", allowed_branches=["main"])
        assert result["status"] == "FAIL"
        assert result["branch"] == "feature-test"
        assert any("feature-test" in e for e in result["errors"])

    def test_both_violations_reported_together(self, tmp_path):
        """Both behind-remote and wrong-branch errors appear in a single FAIL."""
        local, remote = _make_repo_pair(tmp_path)
        # Push a feature branch so it has tracking info.
        _git(["checkout", "-b", "stale-feature"], cwd=str(local))
        (local / "feature.txt").write_text("feature\n")
        _git(["add", "feature.txt"], cwd=str(local))
        _git(["commit", "-m", "feature commit"], cwd=str(local))
        _git(["push", "-u", "origin", "stale-feature"], cwd=str(local))
        # Now advance the remote copy of that branch.
        _advance_remote_branch(remote, "stale-feature")
        result = run(repo_path=str(local), remote="origin", allowed_branches=["main"])
        assert result["status"] == "FAIL"
        assert len(result["errors"]) >= 2

    def test_empty_allowed_branches_skips_branch_guard(self, tmp_path):
        """When allowed_branches is empty, only the behind-remote guard applies."""
        local, remote = _make_repo_pair(tmp_path)
        _git(["checkout", "-b", "any-branch"], cwd=str(local))
        result = run(repo_path=str(local), remote="origin", allowed_branches=[])
        # Branch guard disabled; should PASS (not behind)
        assert result["status"] == "PASS"


# ─────────────────────────────────────────────────────────────────────────────
# smoke test
# ─────────────────────────────────────────────────────────────────────────────

class TestSmokeTest:

    def test_smoke_test_passes(self):
        assert run_smoke_test() is True


# ─────────────────────────────────────────────────────────────────────────────
# hook mode — remote from argv, permissive default, env/config overrides
# ─────────────────────────────────────────────────────────────────────────────

GATE_SCRIPT = Path(__file__).resolve().parents[1] / "pre_push_gate.py"


def _run_gate_cli(
    local: Path,
    extra_args: list[str] | None = None,
    env: dict | None = None,
) -> tuple[int, str]:
    """Run pre_push_gate.py as a subprocess; return (returncode, combined output)."""
    cmd = [sys.executable, str(GATE_SCRIPT), "--repo", str(local)] + (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout + result.stderr


class TestHookMode:
    """Verify hook-mode behaviors: remote from argv, permissive default, overrides."""

    def test_hook_mode_permissive_by_default(self, tmp_path):
        """Feature-branch push is allowed in hook mode when no env var / git config set."""
        import os as _os
        local, remote = _make_repo_pair(tmp_path)
        _git(["checkout", "-b", "feature-x"], cwd=str(local))
        # Strip any PRE_PUSH_GATE_ALLOW_BRANCHES that might be set in the outer env.
        env = {k: v for k, v in _os.environ.items() if k != "PRE_PUSH_GATE_ALLOW_BRANCHES"}
        rc, out = _run_gate_cli(local, ["origin", str(remote)], env=env)
        assert rc == 0, f"Feature-branch push should be allowed in hook mode:\n{out}"

    def test_hook_mode_uses_remote_from_argv(self, tmp_path):
        """Stale push is still blocked in hook mode using the remote passed on argv."""
        local, remote = _make_repo_pair(tmp_path)
        _advance_remote(remote, local)
        # Simulate: git passes "origin <url>" as positional args.
        rc, out = _run_gate_cli(local, ["origin", str(remote)])
        assert rc == 1, f"Stale push should be BLOCKED in hook mode:\n{out}"
        assert "BLOCKED" in out

    def test_hook_mode_env_var_restricts_branches(self, tmp_path):
        """PRE_PUSH_GATE_ALLOW_BRANCHES restricts allowed branches in hook mode."""
        import os as _os
        local, remote = _make_repo_pair(tmp_path)
        _git(["checkout", "-b", "feature-env"], cwd=str(local))
        env = {**_os.environ, "PRE_PUSH_GATE_ALLOW_BRANCHES": "main"}
        rc, out = _run_gate_cli(local, ["origin", str(remote)], env=env)
        assert rc == 1, f"Feature branch should be blocked by env var:\n{out}"
        assert "BLOCKED" in out
        assert "feature-env" in out

    def test_hook_mode_git_config_restricts_branches(self, tmp_path):
        """hooks.allowBranches git config restricts allowed branches in hook mode."""
        import os as _os
        local, remote = _make_repo_pair(tmp_path)
        _git(["config", "hooks.allowBranches", "main"], cwd=str(local))
        _git(["checkout", "-b", "feature-cfg"], cwd=str(local))
        env = {k: v for k, v in _os.environ.items() if k != "PRE_PUSH_GATE_ALLOW_BRANCHES"}
        rc, out = _run_gate_cli(local, ["origin", str(remote)], env=env)
        assert rc == 1, f"Feature branch should be blocked by git config:\n{out}"
        assert "BLOCKED" in out
        assert "feature-cfg" in out


<<<<<<< HEAD
if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
=======
def run_smoke_test() -> bool:
    """Builder compliance smoke test."""
    try:
        assert TOOL_NAME == "test_pre_push_gate"
        assert TOOL_VERSION
        assert callable(check_branch)
        assert callable(check_not_behind)
        assert callable(run)
        return bool(module_run_smoke_test())
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(0 if run_smoke_test() else 1)
>>>>>>> origin/main
