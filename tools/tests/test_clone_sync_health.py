"""
test_clone_sync_health.py
Integration tests for tools/clone_sync_health_v1_0.py.
Builder v1.7 compliant — test_clone_sync_health_tool
HumanAIOS — S-070726-test-clone-sync-health

Covers:
  1. get_clone_status  — clean, behind, dirty, no-origin/main (unknown guard)
  2. fix_clone         — skip when unknown state, skip when dirty, reconcile when behind
  3. run_smoke_test    — built-in smoke test

Run:
    pytest tools/tests/test_clone_sync_health.py -v
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from clone_sync_health_v1_0 import (
    fix_clone,
    get_clone_status,
    run_smoke_test,
)

TOOL_NAME = "test_clone_sync_health"
TOOL_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _git(cmd: list[str], cwd: str | Path) -> None:
    """Run a git command, raising on failure."""
    subprocess.run(["git"] + cmd, cwd=str(cwd), check=True,
                   capture_output=True, text=True)


def _make_repo_pair(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create a bare 'remote' and a local clone of it with one commit on main.
    Returns (local_path, remote_path).
    """
    remote = tmp_path / "remote.git"
    local  = tmp_path / "local"
    remote.mkdir()
    local.mkdir()

    _git(["init", "--bare", str(remote)], cwd=str(tmp_path))
    # Ensure the bare repo HEAD points to main (portable across git versions).
    (remote / "HEAD").write_text("ref: refs/heads/main\n")

    _git(["init", str(local)], cwd=str(tmp_path))
    subprocess.run(
        ["git", "checkout", "-b", "main"],
        cwd=str(local), capture_output=True,
    )
    _git(["config", "user.email", "test@example.com"], cwd=str(local))
    _git(["config", "user.name", "Test"], cwd=str(local))
    _git(["remote", "add", "origin", str(remote)], cwd=str(local))

    (local / "README.md").write_text("init\n")
    _git(["add", "README.md"], cwd=str(local))
    _git(["commit", "-m", "init"], cwd=str(local))
    _git(["push", "-u", "origin", "main"], cwd=str(local))

    return local, remote


def _advance_remote(remote: Path, local: Path) -> None:
    """
    Add one commit to the remote so local is behind by 1.
    Simulates a collaborator push while the local clone is stale.
    """
    import tempfile as _tmp
    with _tmp.TemporaryDirectory() as other_dir:
        other = Path(other_dir) / "other"
        subprocess.run(
            ["git", "clone", str(remote), str(other)],
            check=True, capture_output=True, text=True,
        )
        _git(["config", "user.email", "other@example.com"], cwd=other)
        _git(["config", "user.name", "Other"], cwd=other)
        (other / "OTHER.md").write_text("remote commit\n")
        _git(["add", "OTHER.md"], cwd=other)
        _git(["commit", "-m", "remote advance"], cwd=other)
        _git(["push", "origin", "main"], cwd=other)


# ─────────────────────────────────────────────────────────────────────────────
# get_clone_status
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCloneStatus:

    def test_clean_repo_is_ok(self, tmp_path):
        """A repo in sync with origin/main reports severity 'ok'."""
        local, _ = _make_repo_pair(tmp_path)
        status = get_clone_status(local)
        assert status["severity"] == "ok", f"Expected ok, got: {status}"
        assert status["behind"] == 0
        assert status["branch"] == "main"

    def test_behind_repo_is_drifted(self, tmp_path):
        """A repo behind origin/main reports severity 'major' or 'critical'."""
        local, remote = _make_repo_pair(tmp_path)
        _advance_remote(remote, local)
        status = get_clone_status(local)
        assert status["severity"] in ("major", "critical"), (
            f"Expected major/critical for behind repo, got: {status['severity']}"
        )
        assert status["behind"] > 0

    def test_dirty_repo_is_ok_dirty(self, tmp_path):
        """A repo with uncommitted changes reports severity 'ok-dirty'."""
        local, _ = _make_repo_pair(tmp_path)
        (local / "dirty.txt").write_text("unstaged\n")
        status = get_clone_status(local)
        assert status["severity"] == "ok-dirty"
        assert status["dirty"] > 0

    def test_no_origin_main_reports_unknown_not_ok(self, tmp_path):
        """
        Core false-negative guard: when origin/main does not exist (e.g. a repo
        whose default branch is not 'main'), rev-list fails → behind stays -1.
        The severity must be 'unknown', NOT 'ok', so drifted repos don't report green.
        """
        # Create a repo whose only remote branch is 'master', not 'main'.
        remote = tmp_path / "remote-master.git"
        local  = tmp_path / "local-master"
        remote.mkdir()
        local.mkdir()

        _git(["init", "--bare", str(remote)], cwd=str(tmp_path))
        (remote / "HEAD").write_text("ref: refs/heads/master\n")

        _git(["init", str(local)], cwd=str(tmp_path))
        subprocess.run(
            ["git", "checkout", "-b", "master"],
            cwd=str(local), capture_output=True,
        )
        _git(["config", "user.email", "t@t.com"], cwd=str(local))
        _git(["config", "user.name", "T"], cwd=str(local))
        _git(["remote", "add", "origin", str(remote)], cwd=str(local))
        (local / "f.txt").write_text("x\n")
        _git(["add", "f.txt"], cwd=str(local))
        _git(["commit", "-m", "init"], cwd=str(local))
        _git(["push", "-u", "origin", "master"], cwd=str(local))

        status = get_clone_status(local)
        # origin/main does not exist → rev-list fails → behind == -1
        assert status["behind"] == -1, (
            f"Expected behind=-1 when origin/main missing, got {status['behind']}"
        )
        assert status["severity"] == "unknown", (
            f"False-negative: expected 'unknown' when origin/main missing, got '{status['severity']}'"
        )


# ─────────────────────────────────────────────────────────────────────────────
# fix_clone
# ─────────────────────────────────────────────────────────────────────────────

class TestFixClone:

    def test_fix_unknown_state_is_skipped(self):
        """fix_clone must skip when behind == -1 (unknown state), not return success."""
        unknown_state = {
            "name": "mystery-repo", "path": "/tmp/mystery",
            "branch": "main", "remote_url": "https://github.com/x/y",
            "behind": -1, "ahead": -1, "dirty": 0,
            "fetch_ok": False, "severity": "unknown", "note": "rev-list failed",
        }
        ok, msg = fix_clone(unknown_state)
        assert not ok, "fix_clone must not succeed when state is unknown"
        assert "unknown" in msg.lower() or "skip" in msg.lower(), (
            f"Expected skip/unknown message, got: {msg}"
        )

    def test_fix_dirty_is_skipped(self):
        """fix_clone must skip dirty repos."""
        dirty_state = {
            "name": "dirty-repo", "path": "/tmp/dirty",
            "branch": "main", "remote_url": "https://github.com/x/y",
            "behind": 5, "ahead": 0, "dirty": 3,
            "fetch_ok": True, "severity": "critical", "note": "dirty",
        }
        ok, msg = fix_clone(dirty_state)
        assert not ok
        assert "dirty" in msg.lower()

    def test_fix_ahead_is_skipped(self):
        """fix_clone must skip repos that are ahead of origin."""
        ahead_state = {
            "name": "ahead-repo", "path": "/tmp/ahead",
            "branch": "main", "remote_url": "https://github.com/x/y",
            "behind": 0, "ahead": 2, "dirty": 0,
            "fetch_ok": True, "severity": "ok", "note": "",
        }
        ok, msg = fix_clone(ahead_state)
        assert not ok
        assert "ahead" in msg.lower()

    def test_fix_already_clean_returns_success(self):
        """fix_clone must return success when behind == 0 and on main."""
        clean_state = {
            "name": "clean-repo", "path": "/tmp/clean",
            "branch": "main", "remote_url": "https://github.com/x/y",
            "behind": 0, "ahead": 0, "dirty": 0,
            "fetch_ok": True, "severity": "ok", "note": "",
        }
        ok, msg = fix_clone(clean_state)
        assert ok
        assert "already clean" in msg.lower()

    def test_fix_behind_repo_is_reconciled(self, tmp_path):
        """fix_clone successfully reconciles a repo that is behind origin/main."""
        local, remote = _make_repo_pair(tmp_path)
        _advance_remote(remote, local)

        status = get_clone_status(local)
        assert status["behind"] > 0, "Pre-condition: local must be behind for this test"

        ok, msg = fix_clone(status)
        assert ok, f"Expected fix_clone to succeed, got: {msg}"
        assert "reconciled" in msg.lower() or "pulled" in msg.lower()

        # Verify the repo is now clean
        post_status = get_clone_status(local)
        assert post_status["behind"] == 0, (
            f"After fix, expected behind=0, got {post_status['behind']}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# smoke test
# ─────────────────────────────────────────────────────────────────────────────

class TestSmokeTest:

    def test_smoke_test_passes(self):
        assert run_smoke_test() is True


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
