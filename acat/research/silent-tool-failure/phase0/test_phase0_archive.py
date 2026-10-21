"""Archive checks for the ACAT Phase 0 import. Standard library only; no model calls, no network.

Run from this directory: python3 -I -m unittest discover -s . -p 'test_phase0_archive.py' -v
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = json.loads((HERE / 'PHASE0_LOCK.json').read_text())
RECEIPT = json.loads((HERE / 'run_001' / 'PHASE0_RECEIPT.json').read_text())


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RunnerChecksumTest(unittest.TestCase):
    def test_runner_matches_lock(self):
        self.assertEqual(sha256_file(HERE / 'phase0_trial.py'), LOCK['runner_sha256'])

    def test_runner_matches_receipt(self):
        self.assertEqual(RECEIPT['runner_sha256'], LOCK['runner_sha256'])

    def test_changed_runner_bytes_change_digest(self):
        # A one-byte edit must move the digest, or the lock cannot detect drift.
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / 'phase0_trial.py'
            copy.write_bytes((HERE / 'phase0_trial.py').read_bytes() + b'\n')
            self.assertNotEqual(sha256_file(copy), LOCK['runner_sha256'])


class LedgerRehydrateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name) / 'ledger.jsonl'

    def tearDown(self):
        self._tmp.cleanup()

    def _rehydrate(self):
        return subprocess.run(
            [sys.executable, '-I', str(HERE / 'rehydrate_ledger.py'),
             '--lock', str(HERE / 'PHASE0_LOCK.json'),
             '--payload', str(HERE / 'run_001' / 'raw_ledger_times.json'),
             '--receipt', str(HERE / 'run_001' / 'PHASE0_RECEIPT.json'),
             '--output', str(self.out)],
            capture_output=True, text=True)

    def test_reconstruction_matches_receipt_sha(self):
        result = self._rehydrate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sha256_file(self.out), RECEIPT['raw_ledger_sha256'])
        self.assertEqual(self.out.stat().st_size, 1169800)

    def test_refuses_to_overwrite_existing_output(self):
        self.assertEqual(self._rehydrate().returncode, 0)
        original = self.out.read_bytes()
        second = self._rehydrate()
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(self.out.read_bytes(), original)

    def test_replay_matches_receipt_chain(self):
        self.assertEqual(self._rehydrate().returncode, 0)
        sys.path.insert(0, str(HERE))
        try:
            from phase0_trial import verify_ledger
        finally:
            sys.path.pop(0)
        count, last, groups = verify_ledger(self.out)
        self.assertEqual(count, RECEIPT['total_trials'])
        self.assertEqual(last, RECEIPT['last_chain_sha256'])
        self.assertTrue(all(groups[k]['total'] == 400 for k in groups))


if __name__ == '__main__':
    unittest.main()
