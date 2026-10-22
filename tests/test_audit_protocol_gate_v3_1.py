"""Adversarial contract tests; fixtures do NOT create verified witnesses."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "audit_protocol_gate_v3_1.py"
spec = importlib.util.spec_from_file_location("audit_protocol_gate_v3_1", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sample():
    def receipt():
        return {"score": 3, "tier": "E1", "state": "OBSERVED_PASS", "receipt": "synthetic:untrusted"}
    return {"scope": {"target": "synthetic-only", "commit": "a" * 40,
                      "environment": "sandbox", "auditor": "different-witness",
                      "operator": "sandbox-owner", "authorization_receipt": "synthetic:not-authorized"},
            "claims": {
                "C1": {"applicability": "CLAIMED",
                       "controls": {k: receipt() for k in gate.CONTROLS["C1"]},
                       "risk_sample": {"eligible": 30, "selected": 30, "unauthorized_bypasses": 0}},
                "C2": {"applicability": "CLAIMED",
                       "controls": {k: receipt() for k in gate.CONTROLS["C2"]},
                       "training": {"teacher_version": "synthetic:T1", "student_version": "synthetic:S1",
                                    "baseline": "synthetic:base", "sealed_holdout": "synthetic:holdout",
                                    "witness": "synthetic:untrusted",
                                    "holdout_cycles": [0.80, 0.79, 0.79], "gain": 0.02}},
            }}


class AuditGateTests(unittest.TestCase):
    def test_full_synthetic_record_never_certifies_actual_claim(self):
        d = gate.evaluate(sample())
        self.assertEqual(d["claims"]["C1"]["contract"], "ELIGIBLE_FOR_REVIEW")
        self.assertEqual(d["claims"]["C2"]["contract"], "ELIGIBLE_FOR_REVIEW")
        self.assertTrue(d["claims"]["C1"]["claim"].startswith("INCONCLUSIVE"))
        self.assertFalse(d["merge_authority"])
    def test_five_partial_cannot_pass(self):
        d = sample()
        for control in d["claims"]["C1"]["controls"].values():
            control["score"] = 1
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_b82_or_b83_failure_blocks(self):
        for k in ("B8.2", "B8.3"):
            d = sample()
            d["claims"]["C2"]["controls"][k]["score"] = 0
            d["claims"]["C2"]["controls"][k]["state"] = "OBSERVED_FAIL"
            self.assertEqual(gate.evaluate(d)["claims"]["C2"]["contract"], "BLOCKED")
    def test_missing_subcontrols_block(self):
        d = sample()
        del d["claims"]["C2"]["controls"]["B5"]
        self.assertEqual(gate.evaluate(d)["claims"]["C2"]["contract"], "BLOCKED")
    def test_e3_is_not_e2(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A3"]["tier"] = "E3"
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_not_tested_and_na_not_pass(self):
        for state in ("N_A", "NOT_TESTED", "BLOCKED"):
            d = sample()
            d["claims"]["C1"]["controls"]["A5"]["state"] = state
            self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_empty_risk_frame_cannot_pass(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"] = {"eligible": 0, "selected": 0, "unauthorized_bypasses": 0}
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_risk_sampling(self):
        self.assertEqual([gate.sample_size(n) for n in (0, 1, 4, 5, 30, 50, 400)],
                         [0, 1, 4, 5, 30, 50, 40])
        self.assertGreater(gate.upper95_zero_failures(5), .4)
    def test_vendor_cannot_make_five_samples_sufficient(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"]["selected"] = 5
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_cumulative_collapse_blocks(self):
        d = sample()
        d["claims"]["C2"]["training"]["holdout_cycles"] = [.8, .785, .77, .755]
        self.assertIn("B3:CUMULATIVE_DROP", gate.evaluate(d)["claims"]["C2"]["gaps"])
    def test_zero_or_negative_gain_blocks(self):
        for gain in (0, -0.01):
            d = sample()
            d["claims"]["C2"]["training"]["gain"] = gain
            self.assertEqual(gate.evaluate(d)["claims"]["C2"]["contract"], "BLOCKED")
    def test_same_actor_cannot_claim_independence(self):
        d = sample()
        d["scope"]["auditor"] = d["scope"]["operator"]
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_unpinned_sha_blocks(self):
        d = sample()
        d["scope"]["commit"] = "main"
        self.assertEqual(gate.evaluate(d)["claims"]["C1"]["contract"], "BLOCKED")
    def test_explicitly_unclaimed_is_not_failure(self):
        d = sample()
        d["claims"]["C2"] = {"applicability": "NOT_CLAIMED"}
        self.assertEqual(gate.evaluate(d)["claims"]["C2"]["claim"], "NOT_CLAIMED")

if __name__ == "__main__":
    unittest.main()
