#!/usr/bin/env python3
"""Q-NF-SCHEMA-01: specimen-intake forecasts land on the real NF_LEDGER.

This is the literal falsifier from PRIORITY_QUEUE.md's Q-NF-SCHEMA-01 row: "if
after the adapter `molt_cycle --read-only --nf ledgers/NF_LEDGER.jsonl` still
reports `nf_resolved: 0` against a ledger with >=1 RESOLVE row, the adapter did
not close the edge." These tests build a real, disk-backed, hash-chained ledger
via SpecimenIntakeEvaluator(nf_ledger_path=...), then check `tools/nf_ledger_v0_1.py`
and `molt_cycle.py` both see the same resolved forecast the evaluator itself does.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specimen_intake_evaluator import (
    BehavioralObservations, ImprovementTrajectory, NFLedgerCorrupt, SpecimenIntakeEvaluator,
    SpecimenInput, utcnow,
)

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "tools"))
import nf_ledger_v0_1 as nf  # noqa: E402

# NOTE: a second, unrelated tools/molt_cycle.py exists (a stranded duplicate, see
# ledgers/NF_EVENT_SCHEMA.md). `import molt_cycle` after inserting tools/ onto
# sys.path would silently resolve to that file instead of the root one this test
# targets, since tools/ now sits ahead of the repo root — load the root module by
# explicit path instead of by bare name to avoid that collision.
_molt_cycle_spec = importlib.util.spec_from_file_location(
    "molt_cycle_root", os.path.join(_ROOT, "molt_cycle.py"))
molt_cycle = importlib.util.module_from_spec(_molt_cycle_spec)
_molt_cycle_spec.loader.exec_module(molt_cycle)


def mk_evaluator(nf_ledger_path):
    signer = Ed25519PrivateKey.generate()
    return SpecimenIntakeEvaluator("SPC-NF", ratifier_public_key=signer.public_key(),
                                   nf_ledger_path=nf_ledger_path), signer


def mk_and_publish(ev, signer, cycle=1, q=87.0, acc=0.96,
                   traj=ImprovementTrajectory.IMPROVING, verification_sources=None):
    si = SpecimenInput(datetime(2026, 9, 13, tzinfo=timezone.utc), datetime(2026, 9, 19, tzinfo=timezone.utc),
                       "micro1", 25, 24, 3, ["a"], verification_sources=verification_sources or [])
    obs = BehavioralObservations(acc, 0.25, 12.5, q, 0.94, 0.08, 0.06, 0.67, traj, "increasing")
    r = ev.create_intake_record(cycle, si, obs)
    ev.generate_molt_predictions(r)
    ev.generate_credpolicy_recommendation(r)
    ev.compute_receipt(r)
    t = utcnow()
    sig = signer.sign(ev.ratification_payload(r.receipt_hash, "Z2", t)).hex()
    ev.ratify(r, "Z2", t, sig)
    assert ev.publish_record(r)
    return r


def _canonical_brier_per_predictor(events):
    """Mirrors tools/nf_ledger_v0_1.py's own cmd_score loop exactly, via its own
    project()/pin_outcome() — the canonical result this PR's Brier must match."""
    tokens, pins = nf.project(events)
    acc = {}
    for p in pins.values():
        if p["p"] is None:
            continue
        o = nf.pin_outcome(p, tokens)
        if o in (None, "VOID"):
            continue
        acc.setdefault(p["predictor"], []).append((p["p"] - o) ** 2)
    return {k: sum(v) / len(v) for k, v in acc.items()}


class NFLedgerIntegration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ledger_path = os.path.join(self.tmpdir, "NF_LEDGER.jsonl")

    def test_publish_writes_token_and_pin_events(self):
        ev, signer = mk_evaluator(self.ledger_path)
        r = mk_and_publish(ev, signer)

        events = nf.read(self.ledger_path)
        types = [e["type"] for e in events]
        self.assertEqual(types.count("TOKEN"), len(r.molt_predictions))
        self.assertEqual(types.count("PIN"), len(r.molt_predictions))
        self.assertIsNone(nf.verify(events))

        pin_ids = {e["target"] for e in events if e["type"] == "PIN"}
        self.assertEqual(pin_ids, {p.prediction_id for p in r.molt_predictions})

    def test_resolved_forecast_visible_to_nf_ledger_score_and_molt_cycle(self):
        ev, signer = mk_evaluator(self.ledger_path)
        r = mk_and_publish(ev, signer)

        ev.resolve_cycle(r, actual_quality=86.2, actual_acceptance=0.94,
                         actual_trajectory=ImprovementTrajectory.IMPROVING,
                         actual_choice="high-complexity-annotation")

        # The ledger file itself: chain intact, RESOLVE rows present.
        events = nf.read(self.ledger_path)
        self.assertIsNone(nf.verify(events))
        self.assertGreaterEqual(sum(1 for e in events if e["type"] == "RESOLVE"), 1)

        # tools/nf_ledger_v0_1.py's own projection sees a resolved, scoreable pin.
        tokens, pins = nf.project(events)
        outcomes = [nf.pin_outcome(p, tokens) for p in pins.values()]
        self.assertTrue(any(o in (1.0, 0.0) for o in outcomes))

        # molt_cycle.py's rewritten reader — the actual falsifier this row names.
        mc = molt_cycle.MoltCycle(nf_ledger_path=self.ledger_path)
        read_result = mc.read_nf_ledger()
        self.assertEqual(read_result["status"], "READ_COMPLETE")
        resolved = mc.count_resolved()
        self.assertGreaterEqual(resolved, 1, "molt_cycle must see >=1 resolved pin "
                                              "once the ledger has a RESOLVE row")

        pairs = mc.join_pin_resolve_pairs()
        brier = mc.calculate_brier_scores(pairs)
        self.assertIsNotNone(brier["brier_overall"])
        self.assertIn("Z1", brier["brier_per_predictor"])

        # Exact agreement with the canonical scorer, not just "some number came
        # back" — this is acceptance criterion 4's actual claim (Copilot review).
        canonical = _canonical_brier_per_predictor(events)
        self.assertAlmostEqual(brier["brier_per_predictor"]["Z1"]["brier"], canonical["Z1"])

    def test_reverted_forecast_resolves_no(self):
        # A quality miss well outside the revert band trips REVERT -> outcome NO.
        ev, signer = mk_evaluator(self.ledger_path)
        r = mk_and_publish(ev, signer, q=90.0)
        ev.resolve_cycle(r, actual_quality=10.0, actual_acceptance=0.94,
                         actual_trajectory=ImprovementTrajectory.IMPROVING,
                         actual_choice="high-complexity-annotation")

        events = nf.read(self.ledger_path)
        tokens, pins = nf.project(events)
        quality_pred = next(p for p in r.molt_predictions if p.variable == "task_quality_score")
        self.assertTrue(quality_pred.reverted)
        pin = pins[f"{quality_pred.prediction_id}:Z1"]
        self.assertEqual(nf.pin_outcome(pin, tokens), 0.0)

    def test_default_constructor_does_not_touch_disk(self):
        # No nf_ledger_path -> pure in-memory behavior, unchanged from before.
        signer = Ed25519PrivateKey.generate()
        ev = SpecimenIntakeEvaluator("SPC-NOFILE", ratifier_public_key=signer.public_key())
        mk_and_publish(ev, signer)
        self.assertIsNone(ev.nf_ledger_path)
        self.assertTrue(len(ev.nf_ledger) > 0)  # in-memory sink still populated

    def test_binary_prediction_pin_uses_confidence_weighted_probability(self):
        # Copilot review, PR #313: PIN.p for a binary variable must match the
        # confidence-weighted probability MoltPrediction.resolve() actually
        # scores against, not the raw (0.0/1.0) prediction_value.
        ev, signer = mk_evaluator(self.ledger_path)
        r = mk_and_publish(ev, signer, traj=ImprovementTrajectory.IMPROVING)
        binary_pred = next(p for p in r.molt_predictions if p.variable == "improvement_trajectory")
        self.assertTrue(binary_pred.binary)

        events = nf.read(self.ledger_path)
        pin = next(e for e in events if e["type"] == "PIN" and e["target"] == binary_pred.prediction_id)
        expected_p = (binary_pred.prediction_value * binary_pred.confidence
                      + (1 - binary_pred.prediction_value) * (1 - binary_pred.confidence))
        self.assertAlmostEqual(pin["p"], expected_p)
        # The bug this fixes: raw prediction_value (1.0) is not the calibrated
        # probability (0.6, at confidence 0.6) — they must differ here.
        self.assertNotAlmostEqual(pin["p"], binary_pred.prediction_value)

    def test_verification_source_used_as_resolve_source_when_present(self):
        # RESOLVE.source should be real tree-read-style provenance when the
        # specimen disclosed one, not the synthetic intake-id fallback.
        ev, signer = mk_evaluator(self.ledger_path)
        source = "micro1-platform-export:deadbeef"
        r = mk_and_publish(ev, signer, verification_sources=[source])
        ev.resolve_cycle(r, actual_quality=86.2, actual_acceptance=0.94,
                         actual_trajectory=ImprovementTrajectory.IMPROVING,
                         actual_choice="high-complexity-annotation")
        events = nf.read(self.ledger_path)
        resolves = [e for e in events if e["type"] == "RESOLVE"]
        self.assertTrue(resolves)
        for e in resolves:
            self.assertEqual(e["source"], source)

    def test_corrupt_ledger_refuses_append(self):
        # A tampered existing ledger must refuse further writes rather than
        # extend an already-broken hash chain (Copilot review, PR #313).
        ev, signer = mk_evaluator(self.ledger_path)
        r = mk_and_publish(ev, signer)

        with open(self.ledger_path) as f:
            lines = f.readlines()
        tampered = json.loads(lines[0])
        tampered["by"] = "TAMPERED"
        lines[0] = json.dumps(tampered) + "\n"
        with open(self.ledger_path, "w") as f:
            f.writelines(lines)

        with self.assertRaises(NFLedgerCorrupt):
            ev.resolve_cycle(r, actual_quality=86.2, actual_acceptance=0.94,
                             actual_trajectory=ImprovementTrajectory.IMPROVING,
                             actual_choice="high-complexity-annotation")


if __name__ == "__main__":
    unittest.main()
