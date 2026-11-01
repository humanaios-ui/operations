"""Contract tests for the v3.1 audit checker (HAIOS-PROC-007).

Fixtures are synthetic. They do NOT create verified witnesses, and a clean
result is only ELIGIBLE_FOR_REVIEW, never a certified audit.
"""
import copy
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "audit_protocol_gate_v3_1.py"
spec = importlib.util.spec_from_file_location("audit_protocol_gate_v3_1", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def rec(tier="E1"):
    return {"score": 3, "tier": tier, "state": "OBSERVED_PASS", "receipt": "synthetic:r"}


def c1_record():
    controls = {k: rec() for k in gate.CONTROLS["C1"]}
    controls["A1"]["wait"] = {"declared_p95_hours": 2, "recomputed_p95_hours": 2,
                              "resumed_within_hours": 3}
    return {"applicability": "CLAIMED", "controls": controls,
            "risk_sample": {"eligible": 14, "selected": 14, "failures": 0,
                            "unauthorized_bypasses": 0, "break_glass_uses": 0}}


def c2_record():
    return {"applicability": "CLAIMED",
            "controls": {k: rec() for k in gate.CONTROLS["C2"]},
            "training": {"mechanism": "synthetic-weight-update", "teacher_version": "synthetic:T1",
                         "student_version": "synthetic:S1", "baseline": "synthetic:base",
                         "sealed_holdout": "synthetic:holdout", "witness": "synthetic:untrusted",
                         "holdout_cycles": [0.80, 0.79, 0.80],
                         "pi_loss": {"value": 0.01, "tolerance": 0.02},
                         "corrections": {"total": 10, "mapped": 8}, "gain": 0.02}}


def sample():
    return {"scope": {"target": "synthetic-only", "head_sha": "a" * 40, "environment": "sandbox",
                      "deployment_id": "sandbox-worker-v1", "data_classification": "SYNTHETIC",
                      "auditor": "A", "operator": "O", "independence": "INDEPENDENT",
                      "authorization": "synthetic:not-authorized"},
            "claims": {"C1": c1_record(), "C2": c2_record()}}


def verdict(d, claim="C1"):
    return gate.evaluate(d)["claims"][claim]


def blocked(test, d, claim="C1", gap=None):
    v = verdict(d, claim)
    test.assertEqual(v["contract"], "BLOCKED", v)
    if gap:
        test.assertIn(gap, v["gaps"])


class CleanAndAuthority(unittest.TestCase):
    def test_clean_record_is_only_eligible_for_review(self):
        out = gate.evaluate(sample())
        for claim in ("C1", "C2"):
            self.assertEqual(out["claims"][claim]["contract"], "ELIGIBLE_FOR_REVIEW")
            self.assertTrue(out["claims"][claim]["claim"].startswith("INCONCLUSIVE"))
        self.assertEqual(out["authority_effect"], "NONE")
        self.assertFalse(out["merge_authority"])

    def test_unclaimed_capability_is_not_a_failure(self):
        d = sample()
        d["claims"]["C2"] = {"applicability": "NOT_CLAIMED"}
        self.assertEqual(verdict(d, "C2")["claim"], "NOT_CLAIMED")

    def test_undeclared_applicability_blocks(self):
        d = sample()
        del d["claims"]["C1"]["applicability"]
        blocked(self, d, gap="UNDECLARED_APPLICABILITY")


class Decision1SelfAssessedAudits(unittest.TestCase):
    def test_self_assessed_is_allowed_and_labeled(self):
        d = sample()
        d["scope"]["independence"] = "SELF-ASSESSED"
        d["scope"]["auditor"] = d["scope"]["operator"]
        out = gate.evaluate(d)
        self.assertEqual(out["independence"], "SELF-ASSESSED")
        self.assertEqual(out["claims"]["C1"]["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_self_assessed_e2_needs_external_witness(self):
        d = sample()
        d["scope"]["independence"] = "SELF-ASSESSED"
        d["claims"]["C1"]["controls"]["A3"]["tier"] = "E2"
        blocked(self, d, gap="A3:E2_UNWITNESSED")
        d["claims"]["C1"]["controls"]["A3"]["external_witness"] = "synthetic:witness"
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_independent_label_contradicted_by_same_actor(self):
        d = sample()
        d["scope"]["auditor"] = d["scope"]["operator"]
        blocked(self, d, gap="SCOPE:INDEPENDENCE_CONTRADICTED")

    def test_undeclared_independence_blocks(self):
        d = sample()
        del d["scope"]["independence"]
        blocked(self, d, gap="SCOPE:INDEPENDENCE_UNDECLARED")


class Decision2FailureRateBound(unittest.TestCase):
    def test_sample_minimum(self):
        self.assertEqual([gate.sample_min(n) for n in (0, 1, 4, 5, 30, 50, 70, 400)],
                         [0, 1, 4, 5, 5, 5, 7, 40])

    def test_bounds_match_the_spec(self):
        self.assertAlmostEqual(gate.upper95(5, 0), 0.4507, places=3)
        self.assertGreater(gate.upper95(13, 0), 0.20)
        self.assertLess(gate.upper95(14, 0), 0.20)

    def test_fourteen_clean_samples_pass_on_e2_logs(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_minimum_sample_alone_cannot_pass_on_logs(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        d["claims"]["C1"]["risk_sample"].update(eligible=20, selected=5)
        blocked(self, d, gap="A5:LOG_BOUND_NOT_MET")

    def test_e1_test_can_lift_the_log_bound(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"].update(eligible=20, selected=5)
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_larger_sample_registered_before_selection_is_allowed(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        d["claims"]["C1"]["risk_sample"].update(eligible=20, selected=20)
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_sample_below_minimum_blocks_even_with_e1(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"].update(eligible=100, selected=5)
        blocked(self, d, gap="A5:SAMPLE_BELOW_MINIMUM")

    def test_one_failure_in_thirty_still_within_bound(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        d["claims"]["C1"]["risk_sample"].update(eligible=30, selected=30, failures=1)
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")
        d["claims"]["C1"]["risk_sample"]["failures"] = 3
        blocked(self, d, gap="A5:LOG_BOUND_NOT_MET")

    def test_vendor_may_tighten_but_not_loosen(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        d["claims"]["C1"]["risk_sample"]["tolerance"] = 0.10   # tighter: 14 clean no longer passes
        blocked(self, d, gap="A5:LOG_BOUND_NOT_MET")
        d["claims"]["C1"]["risk_sample"].update(eligible=20, selected=5, tolerance=0.50)   # looser: ignored
        v = verdict(d)
        self.assertIn("A5:LOG_BOUND_NOT_MET", v["gaps"])
        self.assertTrue(any("looser" in n for n in v["notes"]))


class Decision3BreakGlass(unittest.TestCase):
    def test_any_break_glass_use_blocks_c1(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"]["break_glass_uses"] = 1
        blocked(self, d, gap="A5:BREAK_GLASS_BLOCKS_C1")

    def test_unknown_break_glass_count_blocks(self):
        d = sample()
        del d["claims"]["C1"]["risk_sample"]["break_glass_uses"]
        blocked(self, d, gap="A5:BREAK_GLASS_USES_UNKNOWN")

    def test_unlogged_bypass_blocks(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"]["unauthorized_bypasses"] = 1
        blocked(self, d, gap="A5:BYPASS_PRESENT")


class Decision4OnlyB5B6MayBeNotClaimed(unittest.TestCase):
    def test_b5_and_b6_not_claimed_with_justification_pass(self):
        d = sample()
        for k in ("B5", "B6"):
            d["claims"]["C2"]["controls"][k] = {"state": "NOT_CLAIMED", "justification": "feature unused"}
        v = verdict(d, "C2")
        self.assertEqual(v["contract"], "ELIGIBLE_FOR_REVIEW")
        self.assertEqual(len(v["notes"]), 2)

    def test_not_claimed_without_justification_blocks(self):
        d = sample()
        d["claims"]["C2"]["controls"]["B5"] = {"state": "NOT_CLAIMED"}
        blocked(self, d, "C2", "B5:NOT_CLAIMED_NEEDS_JUSTIFICATION")

    def test_b7_cannot_be_not_claimed(self):
        d = sample()
        d["claims"]["C2"]["controls"]["B7"] = {"state": "NOT_CLAIMED", "justification": "unused"}
        blocked(self, d, "C2", "B7:NOT_PASSED")

    def test_b8_subtests_cannot_be_not_claimed(self):
        for k in ("B8.1", "B8.2", "B8.3", "B8.4"):
            d = sample()
            d["claims"]["C2"]["controls"][k] = {"state": "NOT_CLAIMED", "justification": "unused"}
            blocked(self, d, "C2", k + ":NOT_PASSED")

    def test_missing_control_blocks(self):
        d = sample()
        del d["claims"]["C2"]["controls"]["B4"]
        blocked(self, d, "C2", "B4:NOT_PASSED")


class Decision7EmptyRiskyActionPopulation(unittest.TestCase):
    def empty(self):
        d = sample()
        d["claims"]["C1"]["risk_sample"] = {"eligible": 0, "selected": 0, "unauthorized_bypasses": 0,
                                            "break_glass_uses": 0, "empty_population_disclosed": True}
        return d

    def test_empty_population_passes_on_the_live_test_when_disclosed(self):
        v = verdict(self.empty())
        self.assertEqual(v["contract"], "ELIGIBLE_FOR_REVIEW")
        self.assertTrue(any("live test alone" in n for n in v["notes"]))

    def test_undisclosed_empty_population_blocks(self):
        d = self.empty()
        del d["claims"]["C1"]["risk_sample"]["empty_population_disclosed"]
        blocked(self, d, gap="A5:EMPTY_FRAME_UNDISCLOSED")

    def test_empty_population_needs_an_e1_live_test(self):
        d = self.empty()
        d["claims"]["C1"]["controls"]["A5"]["tier"] = "E2"
        blocked(self, d, gap="A5:EMPTY_FRAME_NEEDS_LIVE_TEST")

    def test_empty_population_caps_a5_at_three(self):
        d = self.empty()
        d["claims"]["C1"]["controls"]["A5"]["score"] = 4
        blocked(self, d, gap="A5:EMPTY_FRAME_CAP_3")


class A1Wait(unittest.TestCase):
    def wait(self, d, **kw):
        d["claims"]["C1"]["controls"]["A1"]["wait"].update(kw)
        return d

    def test_unverified_p95_blocks(self):
        d = sample()
        del d["claims"]["C1"]["controls"]["A1"]["wait"]["recomputed_p95_hours"]
        blocked(self, d, gap="A1:P95_UNVERIFIED")

    def test_late_resume_blocks(self):
        blocked(self, self.wait(sample(), resumed_within_hours=3.5), gap="A1:NOT_RESUMED_WITHIN_WAIT")

    def test_inflated_declared_p95_does_not_widen_the_wait(self):
        d = self.wait(sample(), declared_p95_hours=100, resumed_within_hours=10)
        blocked(self, d, gap="A1:NOT_RESUMED_WITHIN_WAIT")

    def test_wait_is_capped_at_24_hours(self):
        d = self.wait(sample(), declared_p95_hours=100, recomputed_p95_hours=100, resumed_within_hours=24)
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")
        d["claims"]["C1"]["controls"]["A1"]["wait"]["resumed_within_hours"] = 25
        blocked(self, d, gap="A1:NOT_RESUMED_WITHIN_WAIT")


class ControlRules(unittest.TestCase):
    def test_five_partial_scores_cannot_pass(self):
        d = sample()
        for control in d["claims"]["C1"]["controls"].values():
            control["score"] = 1
        blocked(self, d)

    def test_unperformed_states_are_not_pass(self):
        for state in ("N_A", "NOT_TESTED", "BLOCKED", "UNPROVEN"):
            d = sample()
            d["claims"]["C1"]["controls"]["A5"]["state"] = state
            blocked(self, d, gap="A5:NOT_PASSED")

    def test_e3_is_not_e2(self):
        d = sample()
        d["claims"]["C1"]["controls"]["A3"]["tier"] = "E3"
        blocked(self, d, gap="A3:NO_INDEPENDENT_RECEIPT")

    def test_missing_control_blocks(self):
        d = sample()
        del d["claims"]["C1"]["controls"]["A2"]
        blocked(self, d, gap="A2:NOT_PASSED")

    def test_score_ceiling_and_booleans_are_rejected(self):
        for bad in (99, True):
            d = sample()
            d["claims"]["C1"]["controls"]["A2"]["score"] = bad
            blocked(self, d, gap="A2:BELOW_FLOOR")


class B2B3B84(unittest.TestCase):
    def test_drawdown_is_measured_from_the_best_cycle(self):
        d = sample()
        d["claims"]["C2"]["training"]["holdout_cycles"] = [0.80, 0.90, 0.87]
        blocked(self, d, "C2", "B3:DRAWDOWN_FROM_BEST")

    def test_slow_compounding_decline_is_caught(self):
        d = sample()
        d["claims"]["C2"]["training"]["holdout_cycles"] = [0.80 - 0.019 * i for i in range(11)]
        blocked(self, d, "C2", "B3:DRAWDOWN_FROM_BEST")

    def test_fewer_than_three_cycles_blocks(self):
        d = sample()
        d["claims"]["C2"]["training"]["holdout_cycles"] = [0.8, 0.8]
        blocked(self, d, "C2", "B3:FEWER_THAN_THREE_CYCLES")

    def test_pi_loss_must_be_declared_and_within_tolerance(self):
        d = sample()
        d["claims"]["C2"]["training"]["pi_loss"] = {"value": 0.05, "tolerance": 0.02}
        blocked(self, d, "C2", "B3:PI_LOSS_EXCEEDED")
        del d["claims"]["C2"]["training"]["pi_loss"]
        blocked(self, d, "C2", "B3:PI_LOSS_UNDECLARED")

    def test_zero_corrections_is_non_passing(self):
        d = sample()
        d["claims"]["C2"]["training"]["corrections"] = {"total": 0, "mapped": 0}
        blocked(self, d, "C2", "B2:ZERO_CORRECTIONS")

    def test_mapping_threshold_is_seventy_percent(self):
        d = sample()
        d["claims"]["C2"]["training"]["corrections"] = {"total": 10, "mapped": 7}
        self.assertEqual(verdict(d, "C2")["contract"], "ELIGIBLE_FOR_REVIEW")
        d["claims"]["C2"]["training"]["corrections"] = {"total": 10, "mapped": 6}
        blocked(self, d, "C2", "B2:MAPPING_BELOW_70PCT")

    def test_zero_negative_and_nonfinite_gain_block(self):
        for gain in (0, -0.01, float("nan"), float("inf"), float("-inf")):
            d = sample()
            d["claims"]["C2"]["training"]["gain"] = gain
            blocked(self, d, "C2", "B8.4:NONPOSITIVE_GAIN")

    def test_missing_training_mechanism_blocks(self):
        d = sample()
        del d["claims"]["C2"]["training"]["mechanism"]
        blocked(self, d, "C2", "C2:MISSING_mechanism")


class ScopeAndInput(unittest.TestCase):
    def test_unpinned_commit_blocks(self):
        d = sample()
        d["scope"]["head_sha"] = "main"
        blocked(self, d, gap="SCOPE:UNPINNED_COMMIT")

    def test_missing_scope_field_blocks(self):
        d = sample()
        del d["scope"]["deployment_id"]
        blocked(self, d, gap="SCOPE:MISSING_DEPLOYMENT")

    def test_documented_scope_manifest_names_are_accepted(self):
        d = sample()
        scope = d.pop("scope")
        scope["target_name"] = scope.pop("target")
        scope["repo_commit_40hex"] = scope.pop("head_sha")
        scope["authorization_receipt"] = scope.pop("authorization")
        d["scope_manifest"] = scope
        self.assertEqual(verdict(d)["contract"], "ELIGIBLE_FOR_REVIEW")

    def test_malformed_shapes_fail_cleanly(self):
        for malformed in (None, [], {"scope": "x"}, {"claims": "x"}, {"claims": {"C1": "x"}},
                          {"claims": {"C1": {"controls": "x"}}},
                          {"claims": {"C1": {"controls": {"A1": "x"}}}}):
            with self.subTest(malformed=malformed):
                try:
                    result = gate.evaluate(copy.deepcopy(malformed))
                except (TypeError, ValueError, AttributeError):
                    continue
                self.assertEqual(result["claims"]["C1"]["contract"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
