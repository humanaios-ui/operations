"""Fail-closed macOS staging and installer regression fixtures.

All paths are temporary. No LaunchAgent, Keychain, installed pilot, network or
provider is touched. The pinned-doc fixture replaces only EXPECTED test hashes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
SPEC = importlib.util.spec_from_file_location("pilot_stage_guard", SCRIPTS / "pilot_stage_guard.py")
# The implementation imports the rollback helper by name when run as a script.
sys.path.insert(0, str(SCRIPTS))
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class StageGuardNegativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # Physical path matters on macOS (/var -> /private/var).
        root = Path(self.tmp.name).resolve()
        self.home = root / "home"
        self.base = self.home / "Library" / "Application Support" / "HumanAIOS"
        self.base.mkdir(parents=True)
        self.src = root / "public"
        self.src.mkdir()
        self.contents = {k: ("synthetic "+k+"\n").encode() for k in stage.EXPECTED}
        self.expected = {k: hashlib.sha256(v).hexdigest() for k,v in self.contents.items()}
        self.patch = patch.dict(stage.EXPECTED, self.expected, clear=True)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        for name, value in self.contents.items():
            (self.src / name).write_bytes(value)
        self.pilot = self.base / "witness-pilot-e03-z1"
        self.context = self.base / "witness-pilot-e03-context"

    @staticmethod
    def lsof_ok(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, "", "")

    def marked_pilot(self):
        self.pilot.mkdir()
        self.context.mkdir()
        (self.pilot / stage.verify_ownership.__globals__["MARKER"]).write_bytes(
            stage.verify_ownership.__globals__["PILOT_TEXT"])
        (self.context / stage.verify_ownership.__globals__["MARKER"]).write_bytes(
            stage.verify_ownership.__globals__["CONTEXT_TEXT"])

    def test_clean_preflight(self):
        stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.assertFalse(self.pilot.exists())
        self.assertFalse(self.context.exists())

    def test_copy_uses_pinned_source_bytes(self):
        stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.marked_pilot()
        stage.copy_public(self.src, self.base, self.home, self.lsof_ok)
        for name, value in self.contents.items():
            self.assertEqual((self.context/name).read_bytes(), value)
            self.assertEqual((self.context/name).stat().st_mode & 0o777, 0o600)

    def test_swap_source_after_preflight_fails_before_any_doc_copy(self):
        stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.marked_pilot()
        (self.src/"REGISTERED.md").write_bytes(b"swapped source must not stage")
        with self.assertRaisesRegex(stage.StagingRefused, "digest mismatch"):
            stage.copy_public(self.src, self.base, self.home, self.lsof_ok)
        self.assertFalse((self.context/"CURRENT.md").exists())
        self.assertFalse((self.context/"REGISTERED.md").exists())

    def test_symlink_swap_after_preflight_never_reads_private_file(self):
        stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.marked_pilot()
        secret = self.src.parent/"private-record.txt"
        secret.write_bytes(b"PRIVATE-DENIED")
        (self.src/"GOVERNANCE.md").unlink()
        (self.src/"GOVERNANCE.md").symlink_to(secret)
        with self.assertRaises(stage.StagingRefused):
            stage.copy_public(self.src, self.base, self.home, self.lsof_ok)
        self.assertEqual(list(self.context.iterdir()),
                         [self.context/stage.verify_ownership.__globals__["MARKER"]])

    def test_preflight_rejects_symlinked_source(self):
        (self.src/"CURRENT.md").unlink()
        (self.src/"CURRENT.md").symlink_to(self.src/"REGISTERED.md")
        with self.assertRaises(stage.StagingRefused):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)

    def test_digest_mismatch_preflight_refused(self):
        (self.src/"CURRENT.md").write_text("out of band")
        with self.assertRaises(stage.StagingRefused):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.assertFalse(self.pilot.exists())

    def test_existing_pilot_refused(self):
        self.pilot.mkdir()
        with self.assertRaises(stage.StagingRefused):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)

    def test_symlinked_destination_base_refused(self):
        other = self.home/"external"
        other.mkdir()
        self.base.rmdir()
        self.base.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(stage.StagingRefused, "symlinked ancestor"):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.assertEqual(list(other.iterdir()), [])

    def test_symlinked_destination_ancestor_refused(self):
        original = self.home/"Library"/"Application Support"
        alternative = self.home/"physical"
        original.rename(alternative)
        original.symlink_to(alternative, target_is_directory=True)
        with self.assertRaisesRegex(stage.StagingRefused, "symlinked ancestor"):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)
        self.assertFalse(self.pilot.exists())

    def test_lsof_clean_no_match(self):
        stage.port_idle(self.lsof_ok)

    def test_lsof_listener_refused(self):
        def active(args, **kw):
            return subprocess.CompletedProcess(args,0,"528\n","")
        with self.assertRaisesRegex(stage.StagingRefused, "in use"):
            stage.preflight(self.src, self.base, self.home, active)
        self.assertFalse(self.pilot.exists())

    def test_lsof_nonzero_with_error_refused(self):
        def error(args, **kw):
            return subprocess.CompletedProcess(args, 1, "", "permission denied")
        with self.assertRaisesRegex(stage.StagingRefused, "inspection failed"):
            stage.preflight(self.src, self.base, self.home, error)
        self.assertFalse(self.pilot.exists())

    def test_lsof_exit_two_refused(self):
        def error(args, **kw):
            return subprocess.CompletedProcess(args, 2, "", "failed")
        with self.assertRaises(stage.StagingRefused):
            stage.preflight(self.src, self.base, self.home, error)
        self.assertFalse(self.pilot.exists())

    def test_lsof_zero_with_no_pids_refused(self):
        def ambiguous(args, **kw):
            return subprocess.CompletedProcess(args,0,"","")
        with self.assertRaisesRegex(stage.StagingRefused, "ambiguous"):
            stage.preflight(self.src, self.base, self.home, ambiguous)

    def test_lsof_command_unavailable_refused(self):
        def unavailable(args, **kw):
            raise FileNotFoundError("lsof")
        with self.assertRaisesRegex(stage.StagingRefused, "unavailable"):
            stage.preflight(self.src, self.base, self.home, unavailable)

    def test_lsof_timeout_refused(self):
        def timed_out(args, **kw):
            raise subprocess.TimeoutExpired(args, 15)
        with self.assertRaisesRegex(stage.StagingRefused, "unavailable"):
            stage.preflight(self.src, self.base, self.home, timed_out)

    def test_copy_refuses_preexisting_destination_file(self):
        self.marked_pilot()
        (self.context/"CURRENT.md").write_text("do not overwrite")
        with self.assertRaises(stage.StagingRefused):
            stage.copy_public(self.src, self.base, self.home, self.lsof_ok)
        self.assertEqual((self.context/"CURRENT.md").read_text(),"do not overwrite")

    def test_copy_refuses_unmarked_context(self):
        self.pilot.mkdir()
        self.context.mkdir()
        with self.assertRaises(stage.StagingRefused):
            stage.copy_public(self.src, self.base, self.home, self.lsof_ok)
        self.assertEqual(list(self.context.iterdir()), [])

    def test_oversized_public_source_refused(self):
        (self.src/"CURRENT.md").write_bytes(b"x"*(stage.MAX_FILE_BYTES+1))
        with self.assertRaisesRegex(stage.StagingRefused, "oversized"):
            stage.preflight(self.src, self.base, self.home, self.lsof_ok)

    def test_lsof_failure_during_copy_refused_before_writes(self):
        self.marked_pilot()
        def fail(args, **kw):
            return subprocess.CompletedProcess(args,1,"","bad permissions")
        with self.assertRaises(stage.StagingRefused):
            stage.copy_public(self.src, self.base, self.home, fail)
        self.assertEqual(len(list(self.context.iterdir())),1)


class InstallerExistingVenvTests(unittest.TestCase):
    """Run actual installer shell with fake uname/launchctl/Python preflight."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name).resolve()
        self.home=root/"home"
        self.home.mkdir()
        self.checkout=root/"public"
        self.checkout.mkdir()
        for name in stage.EXPECTED:
            (self.checkout/name).write_text("synthetic")
        self.installer=SCRIPTS/"install_macos.sh"
        fake=root/"fake"
        fake.mkdir()
        for name,text in {
            "uname":"#!/bin/sh\necho Darwin\n",
            "launchctl":"#!/bin/sh\nexit 1\n",
            "python313":"#!/bin/sh\nif [ \"$1\" = \"-c\" ]; then exit 0; fi\nexit 94\n",
        }.items():
            p=fake/name;p.write_text(text);p.chmod(0o755)
        self.env=dict(os.environ,HOME=str(self.home),
                      HAIOS_MCP_PYTHON=str(fake/"python313"),
                      PATH=str(fake)+os.pathsep+os.environ.get("PATH",""))
        self.install=self.home/"Library"/"Application Support"/"HumanAIOS"/"mcp"
        self.venv=self.install/".venv"
        self.venv.mkdir(parents=True)

    def invoke(self):
        return subprocess.run(["/bin/bash",str(self.installer),str(self.checkout)],
                              env=self.env,capture_output=True,text=True,timeout=15)

    def test_incompatible_python_315_venv_refused_before_changes(self):
        (self.venv/"pyvenv.cfg").write_text("version = 3.15.0\n")
        (self.venv/"bin").mkdir()
        python=self.venv/"bin"/"python"
        python.write_text("#!/bin/sh\nexit 0\n")
        python.chmod(0o755)
        r=self.invoke()
        self.assertEqual(r.returncode,3,r.stderr)
        self.assertIn("existing MCP virtualenv",r.stderr)
        self.assertTrue((self.venv/"pyvenv.cfg").exists())
        self.assertFalse((self.install/"src").exists())
        self.assertFalse((self.home/"Library"/"LaunchAgents").exists())

    def test_broken_existing_venv_refused_untouched(self):
        (self.venv/"keep").write_text("do not touch")
        r=self.invoke()
        self.assertEqual(r.returncode,3,r.stderr)
        self.assertEqual((self.venv/"keep").read_text(),"do not touch")
        self.assertFalse((self.install/"scripts").exists())
        self.assertFalse((self.home/"Library"/"LaunchAgents").exists())

    def test_linked_existing_venv_refused(self):
        outside=self.home/"outside"
        outside.mkdir()
        self.venv.rmdir()
        self.venv.symlink_to(outside,target_is_directory=True)
        r=self.invoke()
        self.assertEqual(r.returncode,3,r.stderr)
        self.assertTrue(self.venv.is_symlink())
        self.assertEqual(list(outside.iterdir()),[])


if __name__ == "__main__":
    unittest.main(verbosity=2)
