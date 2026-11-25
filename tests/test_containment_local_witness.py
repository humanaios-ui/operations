"""Independent local subprocess containment witness contract tests (no network)."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / "research/agent_containment/phase0/independent_local_witness.py"
spec = importlib.util.spec_from_file_location("containment_independent_witness", WITNESS)
witness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(witness)


class LocalWitnessTests(unittest.TestCase):
    def test_independent_local_replay_and_file_preservation(self):
        observed = witness.observe()
        self.assertEqual(observed["evidence_class"], "LOCAL_SUBPROCESS_OBSERVATION_ONLY")
        self.assertEqual(observed["trials"], 12)
        self.assertEqual(observed["events"], 11)
        self.assertEqual(observed["quarantined"], 8)
        self.assertEqual(observed["tamper_negative_control"], "REJECTED")
        self.assertTrue(observed["synthetic_hash_chain_verified_independently"])
        self.assertTrue(observed["inputs_unmodified"])

    def test_witness_does_not_grant_execution_authority(self):
        observed = witness.observe()
        self.assertEqual(observed["external_runtime_isolation"], "UNVERIFIED")
        self.assertEqual(observed["production_effects"], "UNVERIFIED")
        self.assertEqual(observed["operator_authorization"], "NONE")


if __name__ == "__main__":
    unittest.main()
