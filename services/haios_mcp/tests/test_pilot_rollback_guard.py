"""Independent negative-control suite for the E0.3 pilot rollback guard.

Only disposable temporary HOME folders are ever removed. No macOS runtime,
Keychain, network endpoint, provider call, or installed pilot is touched.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE if (HERE / 'pilot_rollback_guard.py').is_file() else HERE.parent / 'scripts'
SPEC = importlib.util.spec_from_file_location('pilot_rollback_guard', SCRIPTS / 'pilot_rollback_guard.py')
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class RollbackGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # macOS tempfile may return /var/... while /var redirects to /private/var.
        # Use the physical path for tests of unrelated lsof/ps failure cases.
        self.home = pathlib.Path(self.tmp.name).resolve() / 'private-home'
        self.pilot, self.context = guard.pilot_paths(self.home)
        self.pilot.mkdir(parents=True)
        self.context.mkdir()
        (self.pilot / guard.MARKER).write_bytes(guard.PILOT_TEXT)
        (self.context / guard.MARKER).write_bytes(guard.CONTEXT_TEXT)

    def fake_run(self, *, ps=None, files=None, port=None, error=None):
        if ps is None:
            ps = '1 /sbin/launchd\n42 /usr/bin/python harmless.py\n'
        if files is None:
            files = {}
        def run(args):
            if error and error in args:
                return subprocess.CompletedProcess(args, 2, '', 'insufficient permissions')
            if args[0].endswith('/ps'):
                return subprocess.CompletedProcess(args, 0, ps, '')
            if '-iTCP:8768' in args:
                value = port or ''
            elif '+D' in args:
                value = files.get(args[-1], '')
            else:
                raise AssertionError(f'unexpected command: {args}')
            return subprocess.CompletedProcess(args, 0 if value else 1, value, '')
        return run

    def test_valid_ownership_and_idle_accepts(self):
        guard.check(self.home, self.fake_run())

    def test_clean_partial_install_with_both_markers_can_be_recovered(self):
        self.assertFalse((self.pilot / '.venv').exists())
        guard.check(self.home, self.fake_run())

    def test_missing_pilot_marker_refused(self):
        (self.pilot / guard.MARKER).unlink()
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_missing_context_marker_refused(self):
        (self.context / guard.MARKER).unlink()
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_marker_contents_mismatch_refused(self):
        (self.pilot / guard.MARKER).write_text('unrelated owner')
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_marker_symlink_refused(self):
        original = self.pilot / guard.MARKER
        original.unlink()
        original.symlink_to(self.context / guard.MARKER)
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_pilot_symlink_refused(self):
        for file in self.pilot.iterdir(): file.unlink()
        self.pilot.rmdir()
        self.pilot.symlink_to(self.context, target_is_directory=True)
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_context_symlink_refused(self):
        for file in self.context.iterdir(): file.unlink()
        self.context.rmdir()
        self.context.symlink_to(self.pilot, target_is_directory=True)
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_parent_directory_symlink_refused(self):
        alternate = self.home / 'alternate'
        alternate.mkdir()
        (self.home / 'Library').rename(alternate / 'Library')
        (self.home / 'Library').symlink_to(alternate / 'Library', target_is_directory=True)
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_same_name_directory_but_missing_marker_refused(self):
        (self.context / guard.MARKER).rename(self.context / 'not_a_marker')
        with self.assertRaises(guard.RollbackRefused): guard.check(self.home, self.fake_run())

    def test_any_port_pilot_process_in_ps_refused(self):
        text = f'1 /sbin/launchd\n401 {self.pilot}/.venv/bin/python -m haios_mcp.server --port 49155\n'
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(ps=text))

    def test_witness_process_without_pilot_path_refused(self):
        text = '1 /sbin/launchd\n402 python -m haios_mcp.server --port 59221\n'
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(ps=text))

    def test_context_process_reference_refused(self):
        text = f'1 /sbin/launchd\n403 some-process --repo {self.context}\n'
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(ps=text))

    def test_pilot_fd_or_cwd_on_any_port_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(files={str(self.pilot): '404\n'}))

    def test_context_fd_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(files={str(self.context): '405\n'}))

    def test_port_8768_still_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'active'):
            guard.check(self.home, self.fake_run(port='406\n'))

    def test_lsof_unknown_error_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'lsof'):
            guard.check(self.home, self.fake_run(error='+D'))

    def test_ps_unavailable_refused(self):
        def bad(args):
            if args[0].endswith('/ps'):
                return subprocess.CompletedProcess(args, 2, '', 'denied')
            return subprocess.CompletedProcess(args, 1, '', '')
        with self.assertRaisesRegex(guard.RollbackRefused, 'Process listing'):
            guard.check(self.home, bad)

    def test_malformed_ps_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'Malformed'):
            guard.check(self.home, self.fake_run(ps='???\n'))

    def test_empty_ps_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'Empty'):
            guard.check(self.home, self.fake_run(ps=''))

    def test_malformed_lsof_refused(self):
        with self.assertRaisesRegex(guard.RollbackRefused, 'Unexpected lsof'):
            guard.check(self.home, self.fake_run(port='not-a-pid\n'))

    def test_guard_own_pid_is_excluded_in_scanner(self):
        text = f'{os.getpid()} python services/haios_mcp/scripts/pilot_rollback_guard.py\n1 /sbin/launchd\n'
        self.assertEqual(guard._ps_hits(text, self.pilot, self.context, {os.getpid()}), set())

    def test_other_process_with_source_only_is_conservatively_refused(self):
        text = '1 /sbin/launchd\n409 python services/haios_mcp/scripts/smoke_e3.py\n'
        self.assertEqual(guard._ps_hits(text, self.pilot, self.context), {409})


class ShellRollbackDisposableFixtures(unittest.TestCase):
    """Real shell rollback effects, but stubbed Darwin/guard in temporary HOME."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.home = root / 'home'
        self.pilot, self.context = guard.pilot_paths(self.home)
        self.pilot.mkdir(parents=True)
        self.context.mkdir()
        (self.pilot / guard.MARKER).write_bytes(guard.PILOT_TEXT)
        (self.context / guard.MARKER).write_bytes(guard.CONTEXT_TEXT)
        self.neighbor = self.pilot.parent / 'existing-production-mcp'
        self.neighbor.mkdir()
        (self.neighbor / 'keep').write_text('protected')
        self.src = root / 'reviewed-copy'
        scripts = self.src / 'scripts'
        scripts.mkdir(parents=True)
        (scripts / 'stage_e03_pilot_macos.sh').write_text(
            (SCRIPTS / 'stage_e03_pilot_macos.sh').read_text())
        (scripts / 'pilot_rollback_guard.py').write_text('''\
import os, sys
from pathlib import Path
log = os.environ.get('GUARD_LOG')
if log:
    with open(log, 'a') as f: f.write('called\\n')
if os.environ.get('GUARD_REFUSE') == '1':
    print('ROLLBACK REFUSED: synthetic process active', file=sys.stderr)
    sys.exit(3)
print('ROLLBACK CHECK PASS: mock')
''')
        fake = root / 'fake-bin'
        fake.mkdir()
        (fake / 'uname').write_text('#!/bin/sh\necho Darwin\n')
        (fake / 'uname').chmod(0o755)
        # Test-only interpreter shim: guard mocked on Linux; no real Mac touched.
        self.pyshim = fake / 'python313'
        self.pyshim.write_text(f'''#!/bin/sh
if [ "$1" = "-c" ]; then exit 0; fi
exec "{sys.executable}" "$@"
''')
        self.pyshim.chmod(0o755)
        self.log = root / 'check-log'
        self.env = dict(os.environ, HOME=str(self.home),
                        HAIOS_PILOT_PYTHON=str(self.pyshim),
                        GUARD_LOG=str(self.log), PATH=str(fake)+os.pathsep+os.environ.get('PATH',''))
        self.script = scripts / 'stage_e03_pilot_macos.sh'

    def run_mode(self, mode, refuse=False):
        env = dict(self.env)
        if refuse: env['GUARD_REFUSE'] = '1'
        return subprocess.run(['/bin/bash', str(self.script), mode], env=env,
                              capture_output=True, text=True, timeout=15)

    def test_check_only_never_deletes(self):
        r = self.run_mode('--rollback-check')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.pilot.exists())
        self.assertTrue(self.context.exists())
        self.assertIn('NO FILES CHANGED', r.stdout)

    def test_denied_check_never_deletes(self):
        r = self.run_mode('--rollback', refuse=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(self.pilot.exists())
        self.assertTrue(self.context.exists())
        self.assertTrue(self.neighbor.exists())

    def test_success_deletes_two_marked_fixtures_only(self):
        r = self.run_mode('--rollback')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.pilot.exists())
        self.assertFalse(self.context.exists())
        self.assertEqual((self.neighbor / 'keep').read_text(), 'protected')
        self.assertEqual(self.log.read_text().count('called'), 2)

    def test_unmarked_partial_stage_is_not_deleted(self):
        (self.pilot / guard.MARKER).unlink()
        # This mock only checks the process guard, not marker ownership.
        # Actual production marker checks are independently unit-tested above.
        # Ensure refusal from the guard stops shell deletion.
        r = self.run_mode('--rollback', refuse=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(self.pilot.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
