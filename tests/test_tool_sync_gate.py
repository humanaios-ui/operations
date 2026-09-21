"""Smoke tests for tool manifest sync gate."""

import os
import subprocess
import yaml
import tempfile
import shutil
import sys
from pathlib import Path


class TestToolSyncGate:
    """Test tool manifest synchronization between YAML and Markdown."""

    @classmethod
    def setup_class(cls):
        """Save original files for restoration after tests."""
        cls.repo_root = Path(__file__).parent.parent
        cls.manifest_path = cls.repo_root / "tools-manifest.yaml"
        cls.markdown_path = cls.repo_root / "TOOLS_MANIFEST.md"

        # Backup originals
        cls.manifest_backup = cls.manifest_path.read_text()
        cls.markdown_backup = cls.markdown_path.read_text()

    @classmethod
    def teardown_class(cls):
        """Restore original files."""
        cls.manifest_path.write_text(cls.manifest_backup)
        cls.markdown_path.write_text(cls.markdown_backup)

    def restore_files(self):
        """Helper to restore files between tests."""
        self.manifest_path.write_text(self.manifest_backup)
        self.markdown_path.write_text(self.markdown_backup)

    def run_gate_check(self):
        """Run the gate validation: scan.py --check, then render.py --check."""
        try:
            # Run scan.py --check
            result_scan = subprocess.run(
                [sys.executable, ".tool-control/scan.py", "--check"],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            if result_scan.returncode != 0:
                return False, f"scan.py --check failed: {result_scan.stderr}"

            # Run render.py --check
            result_render = subprocess.run(
                [sys.executable, ".tool-control/render.py", "--check"],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            if result_render.returncode != 0:
                return False, f"render.py --check failed: {result_render.stderr}"

            return True, "✓ Tool manifest is in sync"
        except Exception as e:
            return False, str(e)

    def test_detect_stale_render(self):
        """Test 1: Detect Stale Markdown - modify manifest without render.py."""
        self.restore_files()

        # Modify manifest: add a test entry
        with open(self.manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        # Add a test tool entry
        manifest['tools'].append({
            'name': 'test-sync-tool',
            'path': 'tools/test-sync.py',
            'category': 'diagnostic_tool'
        })

        with open(self.manifest_path, 'w') as f:
            yaml.dump(manifest, f)

        # Run gate WITHOUT running render.py
        # Gate should FAIL because markdown is stale
        passed, msg = self.run_gate_check()

        self.restore_files()

        # Should detect drift (manifest changed but markdown not regenerated)
        assert not passed, f"Gate should fail when markdown is stale. Got: {msg}"

    def test_both_synced(self):
        """Test 2: Pass When Both Synced - run both scan.py and render.py."""
        self.restore_files()

        # Run scan.py to regenerate/validate manifest
        result_scan = subprocess.run(
            [sys.executable, ".tool-control/scan.py"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        assert result_scan.returncode == 0, f"scan.py failed: {result_scan.stderr}"

        # Run render.py to regenerate markdown
        result_render = subprocess.run(
            [sys.executable, ".tool-control/render.py"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        assert result_render.returncode == 0, f"render.py failed: {result_render.stderr}"

        # Run gate — should PASS
        passed, msg = self.run_gate_check()

        self.restore_files()

        # Should pass when both files are in sync
        assert passed, f"Gate should pass when both files synced. Got: {msg}"

    def test_manual_edit_overwritten(self):
        """Test 3: Manual Edits Overwritten - verify render.py regeneration is deterministic."""
        self.restore_files()

        # Save original markdown
        original_markdown = self.markdown_path.read_text()

        # Manually edit TOOLS_MANIFEST.md (simulating accidental edit)
        modified = original_markdown.replace(
            "## Registered Tools",
            "## Registered Tools (MANUAL EDIT)"
        )

        # Only proceed if replacement was found
        if "## Registered Tools" in original_markdown:
            self.markdown_path.write_text(modified)

            # Run render.py to regenerate markdown (overwrites manual edit)
            result_render = subprocess.run(
                [sys.executable, ".tool-control/render.py"],
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            assert result_render.returncode == 0, f"render.py failed: {result_render.stderr}"

            # Verify manual edit was overwritten
            regenerated_markdown = self.markdown_path.read_text()

            # Manual edit should not survive regeneration
            assert regenerated_markdown != modified, "Manual edit should be overwritten by render.py"
            # Regenerated should match original (render.py is deterministic)
            assert regenerated_markdown == original_markdown, "Regenerated markdown should match original"

        self.restore_files()


if __name__ == "__main__":
    # Run tests with pytest
    pytest_args = ["-xvs", __file__]
    exit_code = subprocess.run([sys.executable, "-m", "pytest"] + pytest_args).returncode
    sys.exit(exit_code)
