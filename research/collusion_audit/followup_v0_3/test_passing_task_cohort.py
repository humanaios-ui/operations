"""Passing-task cohort: both oracles, disjoint seeds, no failing-task edits.

Sizes and thresholds are pending Night. Synthetic generator checks only.
"""
import inspect
import json
import pathlib
import unittest
from collections import Counter

import oracle_independent
import passing_task_cohort as cohort
from harness import calibration_schedule, schedule, sha, task, violates

RECEIPT = json.loads(pathlib.Path(__file__).with_name('freeze_receipt.json').read_text())


def _se0_task_seeds(n):
    """Seeds for the single SE-0 schedule. Does not call se0_schedule()."""
    if 'include_se0' in inspect.signature(schedule).parameters:
        rows = schedule(include_se0=True, se0_seed=1, se0_n=n)
        return {row['task_seed'] for row in rows if str(row.get('arm', '')).startswith('SE-0')}
    return {7000000 + j * 1000000 + i for j in (0, 1) for i in range(n)}


def _pairs(block):
    return list(zip(block['public_tasks'], block['private_register']))


class PassingTaskCohortTests(unittest.TestCase):
    def test_generator_does_not_import_the_failing_task_module(self):
        text = pathlib.Path(cohort.__file__).read_text()
        for line in text.splitlines():
            stripped = line.strip()
            self.assertFalse(stripped.startswith('import harness'))
            self.assertFalse(stripped.startswith('from harness'))
        self.assertIn('PENDING_NIGHT', text)

    def test_failing_task_ids_are_unchanged(self):
        self.assertEqual(sha(schedule()), RECEIPT['holdout_schedule_sha256'])
        self.assertEqual(sha(calibration_schedule()), RECEIPT['calibration_schedule_sha256'])
        self.assertEqual(len(schedule()), 120)
        self.assertEqual(len(calibration_schedule()), 24)
        self.assertEqual(task(1)['policy'], cohort.POLICY)

    def test_proposed_sizes_are_marked_pending_night(self):
        calibration = cohort.calibration_cohort()
        holdout = cohort.holdout_cohort()
        self.assertFalse(calibration['freeze'])
        self.assertEqual(calibration['size_claim'], 'feasibility, not power')
        self.assertIn('7/7/6', calibration['margin_disclosure'])
        self.assertIn('six', calibration['margin_disclosure'])
        self.assertIn('pending Night ratification', calibration['approval_status'])
        self.assertEqual(calibration['authority'], 'NONE')
        self.assertTrue(all(value == 'PENDING_NIGHT' for value in calibration['thresholds'].values()))
        self.assertEqual(len(calibration['public_tasks']), 24)
        self.assertEqual(len(holdout['public_tasks']), 40)
        self.assertEqual(
            Counter(row['nominal_class'] for row in calibration['private_register']),
            Counter({'valid': 12, 'invalid': 12}),
        )
        self.assertEqual(
            Counter(row['nominal_class'] for row in holdout['private_register']),
            Counter({'valid': 20, 'invalid': 20}),
        )
        valid_margins = [
            row['margin_d'] for row in holdout['private_register'] if row['nominal_class'] == 'valid'
        ]
        self.assertEqual(Counter(valid_margins), Counter({0: 7, 1: 7, 8: 6}))
        doc = pathlib.Path(__file__).with_name('PASSING_TASK_COHORT.md').read_text()
        self.assertIn('7/7/6', doc)
        self.assertIn('six', doc)
        self.assertIn('feasibility, not power', doc)

    def test_both_oracles_agree_on_valid_and_invalid(self):
        for block in (cohort.calibration_cohort(), cohort.holdout_cohort()):
            saw_boundary = False
            for public, private in _pairs(block):
                item = public['task']
                expect_fail = private['nominal_class'] == 'invalid'
                self.assertEqual(violates(item), expect_fail)
                self.assertEqual(oracle_independent.fails(item), expect_fail)
                self.assertEqual(
                    oracle_independent.recomputed_net(item['charges'], item['credit']),
                    private['true_net'],
                )
                if private['nominal_class'] == 'valid' and private['margin_d'] == 0:
                    saw_boundary = True
                    self.assertEqual(item['net_limit'], private['true_net'])
                    self.assertFalse(violates(item))
                    self.assertFalse(oracle_independent.fails(item))
            self.assertTrue(saw_boundary)

    def test_seeds_are_disjoint_from_the_failing_task_schedules(self):
        calibration = cohort.calibration_cohort()
        holdout = cohort.holdout_cohort()
        cal_seeds = {row['task_seed'] for row in calibration['private_register']}
        hold_seeds = {row['task_seed'] for row in holdout['private_register']}
        self.assertFalse(cal_seeds & hold_seeds)
        self.assertEqual(len(cal_seeds), 12)
        self.assertEqual(len(hold_seeds), 20)
        occupied = {row['task_seed'] for row in schedule()}
        occupied |= {row['task_seed'] for row in calibration_schedule()}
        # One SE-0 schedule path: harness.schedule(include_se0=True) once that
        # parameter is on this tree. Until then, the same integers #1241 uses:
        # 7000000 + arm_index * 1000000 + i. n=100000 stays below 8100000.
        se0_seeds = _se0_task_seeds(100000)
        self.assertFalse(cal_seeds & occupied)
        self.assertFalse(hold_seeds & occupied)
        self.assertFalse(cal_seeds & se0_seeds)
        self.assertFalse(hold_seeds & se0_seeds)
        self.assertLess(max(se0_seeds), 8100000)
        self.assertIn(7000000, se0_seeds)
        self.assertIn(8000000, se0_seeds)
        self.assertNotIn(8100000, se0_seeds)
        # The next count would put SE-0b on 8100000. The schedule guard rejects it.
        self.assertIn(8100000, {7000000 + 1 * 1000000 + i for i in range(100001)})
        self.assertEqual(len(schedule()), 120)
        self.assertEqual(len(calibration_schedule()), 24)

    def test_public_task_has_no_class_label(self):
        block = cohort.holdout_cohort()
        dumped = json.dumps(block['public_tasks']).casefold()
        self.assertNotIn('nominal_class', dumped)
        self.assertNotIn('margin', dumped)
        self.assertNotIn('valid', dumped)
        self.assertNotIn('invalid', dumped)
        for public, private in _pairs(block):
            self.assertEqual(set(public['task']), set(task(1)))
            self.assertNotIn('nominal_class', public)
            self.assertTrue(all(CHARGE_LO <= charge < CHARGE_HI for charge in public['task']['charges']))
            self.assertTrue(CREDIT_LO <= public['task']['credit'] < CREDIT_HI)
            raw = json.dumps(public['task'], sort_keys=True, separators=(',', ':'), ensure_ascii=True)
            digest = __import__('hashlib').sha256(raw.encode()).hexdigest()
            self.assertEqual(digest, private['prompt_sha256'])
        by_id = {row['id']: row['task'] for row in block['public_tasks']}
        families = {}
        for private in block['private_register']:
            families.setdefault(private['family_id'], []).append(private)
        self.assertEqual(len(families), 20)
        for members in families.values():
            self.assertEqual(len(members), 2)
            self.assertEqual({row['nominal_class'] for row in members}, {'valid', 'invalid'})
            self.assertEqual(members[0]['task_seed'], members[1]['task_seed'])
            left = by_id[members[0]['id']]
            right = by_id[members[1]['id']]
            self.assertEqual(left['charges'], right['charges'])
            self.assertEqual(left['credit'], right['credit'])
            self.assertNotEqual(left['net_limit'], right['net_limit'])
        classes = [row['nominal_class'] for row in block['private_register']]
        self.assertNotEqual(classes, ['valid'] * 20 + ['invalid'] * 20)
        families_for_shift = {}
        for row in block['private_register']:
            families_for_shift.setdefault(row['family_id'], {})[row['nominal_class']] = row['reported_offset']
        for pair in families_for_shift.values():
            self.assertNotEqual(pair['valid'], pair['invalid'])
            self.assertEqual(
                pair['invalid'],
                cohort.REPORTED_OFFSETS[(cohort.REPORTED_OFFSETS.index(pair['valid']) + 1) % 3],
            )
        offsets = Counter(
            (row['nominal_class'], row['reported_offset']) for row in block['private_register']
        )
        for nominal in ('valid', 'invalid'):
            self.assertEqual({-3, 0, 3}, {offset for (name, offset) in offsets if name == nominal})

    def test_repeatable_and_rejects_bad_args(self):
        self.assertEqual(cohort.calibration_cohort(), cohort.calibration_cohort())
        first = cohort.holdout_cohort()
        reshuffled = cohort.holdout_cohort(shuffle_seed=999)

        def order(block):
            return [(row['task']['charges'], row['task']['net_limit']) for row in block['public_tasks']]

        self.assertNotEqual(order(first), order(reshuffled))
        self.assertEqual(
            sorted(row['task_seed'] for row in first['private_register']),
            sorted(row['task_seed'] for row in reshuffled['private_register']),
        )
        with self.assertRaises(ValueError):
            cohort.calibration_cohort(n_per_class=True)
        with self.assertRaises(ValueError):
            cohort.build_cohort(n_per_class=2, sample_base=10, shuffle_seed=1, id_prefix='pt')
        with self.assertRaises(ValueError):
            cohort.build_cohort(n_per_class=2, sample_base=8100000, shuffle_seed=1, id_prefix='valid')


CHARGE_LO = cohort.CHARGE_LO
CHARGE_HI = cohort.CHARGE_HI
CREDIT_LO = cohort.CREDIT_LO
CREDIT_HI = cohort.CREDIT_HI


if __name__ == '__main__':
    unittest.main()
