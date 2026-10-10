import tempfile
import unittest
from pathlib import Path
from tools.iew.iew_runner import PIN, capture, sha
from tools.iew.witness_gate import classify_evidence

class IEW003Witness(unittest.TestCase):
    def setUp(self):
        self.fixture = Path(__file__).parent / "fixtures" / "witness_fixture.py"
    def test_real_subprocess_result(self):
        observed = capture(self.fixture)
        self.assertEqual(observed["outcome_class"], "EXITED")
        self.assertEqual(observed["stdout_sha256"], sha(b"RESULT=42\n"))
        self.assertEqual(observed["exit_code"], 0)
    def test_read_only_fabrication_rejected(self):
        obs = capture(self.fixture)
        r = classify_evidence({"stdout": "FAKE", "exit_code": 0},
               observed=obs, expected_source_sha256=PIN,
               expected_input_sha256=sha(b"42\n"), trusted_context=True)
        self.assertEqual(r["reason"], "OUTCOME_MISMATCH")
    def test_import_then_print_fabrication_rejected(self):
        obs = capture(self.fixture)
        r = classify_evidence({"stdout": "FORGED", "exit_code": 0},
               observed=obs, expected_source_sha256=PIN,
               expected_input_sha256=sha(b"42\n"), trusted_context=True)
        self.assertEqual(r["result"], "BLOCKED")
    def test_sha_chain_cannot_replace_observation(self):
        r = classify_evidence({"stdout": "RESULT=42\n", "exit_code":0, "hash":"arbitrary"},
               observed=None, expected_source_sha256=PIN,
               expected_input_sha256=sha(b"42\n"), trusted_context=True)
        self.assertEqual(r["reason"], "NO_INDEPENDENT_WITNESS")
    def test_source_mutation_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "changed.py"
            p.write_text(self.fixture.read_text() + "\n# mutation\n")
            with self.assertRaisesRegex(ValueError, "SOURCE_BINDING_MISMATCH"):
                capture(p)
    def test_matching_comparison_not_admission(self):
        obs = capture(self.fixture)
        r = classify_evidence({"stdout": "RESULT=42\n", "exit_code":0},
               observed=obs, expected_source_sha256=PIN,
               expected_input_sha256=sha(b"42\n"), trusted_context=True)
        self.assertEqual(r["result"], "OUTCOME_MATCH")
        self.assertEqual(r["admission_effect"], "NONE")
        self.assertFalse(r["independently_attested"])
