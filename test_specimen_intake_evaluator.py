#!/usr/bin/env python3
"""Red-team regression tests for specimen_intake_evaluator v0.2.
Each test is the probe that broke v0.1 (see specimen-intake_redteam_090826.md)."""
import copy
import unittest
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specimen_intake_evaluator import (
    BehavioralObservations, EvaluationStatus, ImprovementTrajectory, RatificationError,
    ReceiptStatus, SpecimenIntakeEvaluator, SpecimenInput, MoltPrediction, RevertRule, utcnow,
)


def mk_evaluator():
    signer = Ed25519PrivateKey.generate()
    return SpecimenIntakeEvaluator("SPC-T", ratifier_public_key=signer.public_key()), signer


def mk(ev, cycle=1, q=87.0, acc=0.96, traj=ImprovementTrajectory.IMPROVING, sources=None):
    si = SpecimenInput(datetime(2026, 9, 13, tzinfo=timezone.utc), datetime(2026, 9, 19, tzinfo=timezone.utc),
                       "micro1", 25, 24, 3, ["a"], verification_sources=sources or [])
    obs = BehavioralObservations(acc, 0.25, 12.5, q, 0.94, 0.08, 0.06, 0.67, traj, "increasing")
    r = ev.create_intake_record(cycle, si, obs)
    ev.generate_molt_predictions(r)
    ev.generate_credpolicy_recommendation(r)
    ev.compute_receipt(r)
    return r


def ratify(ev, signer, r):
    t = utcnow()
    sig = signer.sign(ev.ratification_payload(r.receipt_hash, "Z2", t)).hex()
    ev.ratify(r, "Z2", t, sig)
    assert ev.publish_record(r)


class RedTeam(unittest.TestCase):

    def test_rt01_brier_bounded(self):
        ev, signer = mk_evaluator(); r = mk(ev); ratify(ev, signer, r)
        res = ev.resolve_cycle(r, actual_quality=86.2, actual_acceptance=0.94,
                               actual_trajectory=ImprovementTrajectory.IMPROVING, actual_choice="high-complexity-annotation")
        for b in res["brier"]:
            self.assertTrue(0.0 <= b <= 1.0)
        self.assertLess(res["brier"][0], 0.01)   # a 1-point quality miss is near-perfect, not 33.6
        self.assertEqual(r.resolution_hash, r.compute_resolution_hash())

    def test_rt01_out_of_range_resolution_is_rejected(self):
        ev, signer = mk_evaluator(); r = mk(ev); ratify(ev, signer, r)
        with self.assertRaises(ValueError):
            ev.resolve_cycle(r, actual_quality=101.0, actual_acceptance=0.94,
                             actual_trajectory=ImprovementTrajectory.IMPROVING, actual_choice="high-complexity-annotation")

    def test_rt02_chain_link_and_credpolicy_covered_by_hash(self):
        ev, _ = mk_evaluator(); r = mk(ev)
        h = r.receipt_hash
        r.chain_link_prior = "TAMPERED"
        self.assertNotEqual(r.compute_hash(), h)
        r.chain_link_prior = None
        r.credential_policy_output.predicted_choice = "TAMPERED"
        self.assertNotEqual(r.compute_hash(), h)

    def test_rt02_receipt_stable_after_resolution(self):
        ev, signer = mk_evaluator(); r = mk(ev); ratify(ev, signer, r)
        h = r.receipt_hash
        ev.resolve_cycle(r, 80.0, 0.9, ImprovementTrajectory.STABLE, "output-evaluation")
        self.assertEqual(r.compute_hash(), h)
        self.assertNotEqual(r.resolution_hash, h)

    def test_rt03_publish_requires_ratification_signature(self):
        ev, signer = mk_evaluator(); r = mk(ev)
        r.evaluation_status = EvaluationStatus.VERIFIED          # the v0.1 bypass
        self.assertFalse(ev.publish_record(r))
        with self.assertRaises(RatificationError):
            ev.ratify(r, "Z2", utcnow(), "deadbeef")
        # mutate after receipt, then try to ratify with a signature for the old receipt
        t = utcnow()
        good = signer.sign(ev.ratification_payload(r.receipt_hash, "Z2", t)).hex()
        r.behavioral_observations.quality_score = 99.0
        with self.assertRaises(RatificationError):
            ev.ratify(r, "Z2", t, good)

    def test_rt03_publish_revalidates_signature(self):
        ev, signer = mk_evaluator(); r = mk(ev)
        t = utcnow()
        sig = signer.sign(ev.ratification_payload(r.receipt_hash, "Z2", t)).hex()
        ev.ratify(r, "Z2", t, sig)
        r.ratification_signature = "00"
        self.assertFalse(ev.publish_record(r))

    def test_rt04_rq2_falsifier_can_fire(self):
        ev, signer = mk_evaluator()
        for c in (1, 2, 3):
            r = mk(ev, cycle=c); ratify(ev, signer, r)
            ev.resolve_cycle(r, 87.0, 0.95, ImprovementTrajectory.IMPROVING, actual_choice="something-else")
        self.assertTrue(any(f.startswith("RQ2_FALSIFIER") for f in ev.falsifier_check()))

    def test_rt04_disclosure_and_choice_timestamps_are_recorded(self):
        ev, signer = mk_evaluator(); r = mk(ev); ratify(ev, signer, r)
        disclosed_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
        choice_at = datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc)
        ev.record_recommendation_disclosure(r, disclosed_at)
        res = ev.resolve_cycle(r, 87.0, 0.95, ImprovementTrajectory.IMPROVING, actual_choice="a",
                               actual_choice_recorded_at=choice_at)
        self.assertEqual(r.credential_policy_output.disclosed_at, disclosed_at)
        self.assertEqual(r.credential_policy_output.actual_choice_at, choice_at)
        self.assertTrue(res["credpolicy_agreement_pre_disclosure"])

    def test_rt04_predicted_choice_is_not_the_recommendation(self):
        ev, _ = mk_evaluator(); r = mk(ev)
        cp = r.credential_policy_output
        self.assertNotEqual(cp.predicted_choice, cp.recommended_next_tasks[0])

    def test_rt05_forecasts_bounded_and_not_input_relabeled(self):
        ev, _ = mk_evaluator(); r = mk(ev, acc=1.0, q=100.0)
        p = {x.variable: x.prediction_value for x in r.molt_predictions}
        self.assertLessEqual(p["task_acceptance_rate"], 1.0)
        self.assertLess(p["task_quality_score"], 1.0)             # shrunk toward prior, not 105
        with self.assertRaises(ValueError):
            MoltPrediction("x", "v", 1.05, 0.5, 7, utcnow(), RevertRule("abs_below", 0.1))
        self.assertEqual(p["improvement_trajectory"], 1.0)
        self.assertEqual(next(x for x in r.molt_predictions if x.variable == "improvement_trajectory").measurement_window_days, 14)

    def test_rt05_binary_revert_does_not_false_positive_on_non_improving_input(self):
        pred = MoltPrediction("x", "improvement_trajectory", 0.0, 0.6, 14, utcnow(),
                              RevertRule("equals", 0.0), binary=True)
        _, reverted = pred.resolve(0.0)
        self.assertFalse(reverted)

    def test_rt06_mechanical_revert_emits_event_and_fic(self):
        ev, signer = mk_evaluator(); r = mk(ev); ratify(ev, signer, r)
        res = ev.resolve_cycle(r, actual_quality=40.0, actual_acceptance=0.5,
                               actual_trajectory=ImprovementTrajectory.DECLINING, actual_choice="x")
        self.assertEqual(len(res["reverted"]), 3)
        self.assertEqual(r.evaluation_status, EvaluationStatus.REVERTED)
        self.assertTrue(any(e["event_type"] == "REVERT" for e in ev.molt_events))
        self.assertEqual(len(ev.fic_candidates), 3)

    def test_rt06_rq1_revert_rate_and_rq3_falsifiers_exist(self):
        ev, signer = mk_evaluator()
        qs = [87.0, 85.0, 83.0, 81.0]
        accs = [0.96, 0.90, 0.82, 0.70]
        for c, (q, acc) in enumerate(zip(qs, accs), start=1):
            r = mk(ev, cycle=c, q=q, acc=acc); ratify(ev, signer, r)
            ev.resolve_cycle(r, 30.0, 0.3, ImprovementTrajectory.DECLINING, "high-complexity-annotation")
        f = ev.falsifier_check()
        self.assertTrue(any("REVERT rate" in x for x in f))
        self.assertTrue(any(x.startswith("RQ3_FALSIFIER") for x in f))

    def test_rt08_receipt_tier_is_earned(self):
        ev, _ = mk_evaluator()
        self.assertEqual(mk(ev).receipt_status, ReceiptStatus.CLAIM)
        ev2, _ = mk_evaluator()
        self.assertEqual(mk(ev2, sources=["micro1-export:abc"]).receipt_status, ReceiptStatus.CLAIM_WITH_LINK)

    def test_chain_links_across_cycles_and_events(self):
        ev, signer = mk_evaluator()
        r1 = mk(ev, 1); ratify(ev, signer, r1)
        r2 = mk(ev, 2)
        self.assertEqual(r2.chain_link_prior, r1.receipt_hash)
        ratify(ev, signer, r2)
        self.assertEqual(ev.molt_events[1]["prev_event_hash"], ev.molt_events[0]["event_hash"])
        with self.assertRaises(ValueError):
            mk(ev, 2)                                            # duplicate cycle refused

    def test_no_pii_literals_in_module(self):
        import specimen_intake_evaluator, inspect
        src = inspect.getsource(specimen_intake_evaluator).lower()
        for needle in ("carly", "anderson", "m88dj94"):
            self.assertNotIn(needle, src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
