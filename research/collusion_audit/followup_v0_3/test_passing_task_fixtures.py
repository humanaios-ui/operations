"""Offline-only matched-task controls: NO model calls, spend or execution."""
import copy
import unittest

import harness
from passing_task_fixtures import actor_task, control_tasks, fixture_audit


class PassingTaskFixtureTests(unittest.TestCase):
    def test_balanced_reproducible_and_disjoint(self):
        calibration = control_tasks(12, 40000, 113)
        holdout = control_tasks(20, 50000, 731)
        self.assertEqual(calibration, control_tasks(12, 40000, 113))
        self.assertNotEqual(holdout, control_tasks(20, 50000, 732))
        used = {x['task_seed'] for x in harness.calibration_schedule()}
        used.update(x['task_seed'] for x in harness.schedule())
        self.assertTrue({x['task_seed'] for x in calibration}.isdisjoint(used))
        self.assertTrue({x['task_seed'] for x in holdout}.isdisjoint(used))
        self.assertTrue({x['task_seed'] for x in calibration}.isdisjoint(
            x['task_seed'] for x in holdout))
        self.assertEqual(fixture_audit(calibration, used)['valid'], 12)
        self.assertEqual(fixture_audit(holdout, used), {
            'families': 20, 'tasks': 40, 'valid': 20, 'invalid': 20,
            'behavioral_observations': 0, 'status': 'SYNTHETIC_FIXTURE_ONLY',
        })

    def test_true_passing_and_failing_boundary(self):
        rows = control_tasks(20, 50000, 731)
        good = [x for x in rows if x['class'] == 'VALID']
        bad = [x for x in rows if x['class'] == 'INVALID']
        self.assertEqual(len(good), len(bad))
        self.assertEqual({x['margin'] for x in good}, {0, 1, 8})
        self.assertEqual({x['margin'] for x in bad}, {-1, -8})
        self.assertTrue(any(x['margin'] == 0 and not harness.violates(x['task']) for x in good))
        self.assertTrue(all(not harness.violates(x['task']) for x in good))
        self.assertTrue(all(harness.violates(x['task']) for x in bad))

    def test_reported_net_not_an_oracle_and_crossed_in_both_classes(self):
        rows = control_tasks(20, 50000, 731)
        for c in ('VALID', 'INVALID'):
            offsets = {x['task']['reported_net'] - x['true_net']
                       for x in rows if x['class'] == c}
            self.assertEqual(offsets, {-3, 0, 3})
        for r in rows:
            d = actor_task(r)
            d['reported_net'] = 1000000
            self.assertEqual(harness.violates(d), r['class'] == 'INVALID')

    def test_actor_payload_strips_all_labels(self):
        for x in control_tasks(3, 50000, 731):
            shown = actor_task(x)
            self.assertEqual(set(shown), {
                'charges', 'credit', 'net_limit', 'reported_net', 'policy'})
            self.assertFalse(any(k in shown for k in (
                'class', 'margin', 'true_net', 'family_id', 'task_seed', 'id')))
            self.assertEqual(shown['policy'], harness.task(1)['policy'])

    def test_duplicate_seed_and_invalid_pair_fail_closed(self):
        rows = control_tasks(2, 50000, 1)
        with self.assertRaises(ValueError):
            fixture_audit(rows, existing_seeds={50000})
        with self.assertRaises(ValueError):
            fixture_audit(rows + (rows[0],))
        with self.assertRaises(ValueError):
            fixture_audit(rows[:3])
        tampered = list(copy.deepcopy(rows))
        tampered[0]['task']['net_limit'] = 9999999
        with self.assertRaises(ValueError):
            fixture_audit(tampered)

    def test_no_live_runner_and_parameter_bounds(self):
        for bad in (0, -1, 1.2, True, '4'):
            with self.assertRaises(ValueError):
                control_tasks(bad, 50000, 10)
        with self.assertRaises(ValueError):
            control_tasks(20, 20000, 10)
        with self.assertRaises(ValueError):
            control_tasks(20, 50000, True)


if __name__ == '__main__':
    unittest.main()
