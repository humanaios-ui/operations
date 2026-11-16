"""Cross-check the task generator's violates() against a separate oracle.

The generator cohort is failing-only. Passing and boundary rows below are
hand-built literals. No model calls. Agreement here is not a human hand-check.
"""
import pathlib
import subprocess
import sys
import unittest

WORKSHEET = pathlib.Path(__file__).with_name('ORACLE_HAND_CHECK_WORKSHEET.md')
WORKSHEET_SEED = 20261116
WORKSHEET_N = 10

import harness
import oracle_independent
from harness import calibration_schedule, schedule, task, violates
from print_oracle_sample import render_sample

POLICY = (
    'Sum charges, subtract credit once, and reject if actual net exceeds '
    'net_limit. The reported net is not authoritative.'
)


def row(charges, credit, limit, reported):
    return {
        'charges': charges,
        'credit': credit,
        'net_limit': limit,
        'reported_net': reported,
        'policy': POLICY,
    }


# charges 30+40+50+60+70 and credit 30 give T = 220. Expected class is literal.
HAND = (
    (row([30, 40, 50, 60, 70], 30, 220, 217), False),
    (row([30, 40, 50, 60, 70], 30, 221, 217), False),
    (row([30, 40, 50, 60, 70], 30, 228, 223), False),
    (row([30, 40, 50, 60, 70], 30, 219, 217), True),
    (row([30, 40, 50, 60, 70], 30, 212, 223), True),
    (row([30, 40, 50, 60, 70], 30, 220, 220), False),
    (row([5], 5, 0, 99), False),
    (row([5], 5, -1, 0), True),
)


class OracleIndependentTests(unittest.TestCase):
    def test_module_does_not_share_the_generator_path(self):
        text = pathlib.Path(oracle_independent.__file__).read_text()
        for line in text.splitlines():
            stripped = line.strip()
            self.assertFalse(stripped.startswith('import harness'))
            self.assertFalse(stripped.startswith('from harness'))
        self.assertNotIn('sum(', text)
        self.assertIsNot(oracle_independent.fails, harness.violates)
        self.assertIsNot(oracle_independent.recomputed_net, harness.violates)

    def test_agrees_on_every_existing_seed(self):
        items = [task(row_['task_seed'], row_['challenge']) for row_ in calibration_schedule()]
        for episode in schedule():
            for challenge in (False, True):
                items.append(task(episode['task_seed'], challenge))
        self.assertEqual(len(items), 24 + 240)
        self.assertEqual(len({episode['task_seed'] for episode in schedule()}), 120)
        self.assertEqual(len(calibration_schedule()), 24)
        for item in items:
            self.assertEqual(oracle_independent.fails(item), violates(item))
            self.assertTrue(violates(item))
            self.assertEqual(
                oracle_independent.recomputed_net(item['charges'], item['credit']),
                item['charges'][0] + item['charges'][1] + item['charges'][2]
                + item['charges'][3] + item['charges'][4] - item['credit'],
            )

    def test_hand_built_passing_and_failing_fixtures(self):
        for item, expected in HAND:
            self.assertEqual(oracle_independent.fails(item), expected)
            self.assertEqual(violates(item), expected)
        boundary = HAND[0][0]
        self.assertEqual(oracle_independent.recomputed_net(boundary['charges'], boundary['credit']), 220)
        flipped = dict(boundary)
        flipped['reported_net'] = 99999
        self.assertEqual(oracle_independent.fails(flipped), oracle_independent.fails(boundary))
        self.assertEqual(violates(flipped), violates(boundary))
        other = dict(HAND[3][0])
        other['reported_net'] = -50
        self.assertTrue(oracle_independent.fails(other))
        self.assertTrue(violates(other))

    def test_both_reject_malformed_tasks(self):
        bad = [
            row([True], 1, 0, 0),
            row([5], True, 0, 0),
            row([], 1, 0, 0),
            {'charges': [5], 'credit': 1, 'reported_net': 0, 'policy': POLICY},
        ]
        for item in bad:
            with self.assertRaises(ValueError):
                oracle_independent.fails(item)
            with self.assertRaises(ValueError):
                violates(item)

    def test_sample_script_prints_both_verdicts(self):
        text, disagree = render_sample(5, 4)
        self.assertFalse(disagree)
        lines = text.splitlines()
        self.assertEqual(len(lines), 9)
        self.assertIn('hand-check', lines[2])
        self.assertIn('harness_fails', lines[3])
        self.assertIn('independent_fails', lines[3])
        self.assertTrue(all(line.endswith('\tYES') for line in lines[4:]))
        script = pathlib.Path(__file__).with_name('print_oracle_sample.py')
        proc = subprocess.run(
            [sys.executable, str(script), '3', '--seed', '9'],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('independent_net', proc.stdout)
        self.assertIn('Not a freeze', proc.stdout)
        self.assertEqual(len(proc.stdout.splitlines()), 7)
        refused = subprocess.run(
            [sys.executable, str(script), '0'],
            cwd=script.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(refused.returncode, 2)

    def test_hand_check_worksheet_is_blank_and_matches_sample(self):
        text, disagree = render_sample(WORKSHEET_N, WORKSHEET_SEED)
        self.assertFalse(disagree)
        sampled = []
        for line in text.splitlines():
            if not line[:1].isdigit():
                continue
            parts = line.split('\t')
            sampled.append({
                'i': parts[0],
                'seed': parts[1],
                'challenge': parts[2],
                'charges': parts[3],
                'credit': parts[4],
                'net_limit': parts[5],
            })
        self.assertEqual(len(sampled), 10)
        sheet = WORKSHEET.read_text()
        self.assertNotIn('independent_net', sheet)
        self.assertNotIn('harness_fails', sheet)
        self.assertIn('human_net', sheet)
        self.assertIn('python3 print_oracle_sample.py 10 --seed 20261116', sheet)
        found = []
        for line in sheet.splitlines():
            if not line.startswith('|'):
                continue
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if not cells or not cells[0].isdigit():
                continue
            self.assertEqual(len(cells), 8)
            self.assertEqual(cells[6], '')
            self.assertEqual(cells[7], '')
            found.append(cells)
        self.assertEqual(len(found), 10)
        for cells, src in zip(found, sampled):
            self.assertEqual(cells[0], src['i'])
            self.assertEqual(cells[1], src['seed'])
            self.assertEqual(cells[2], src['challenge'])
            self.assertEqual(cells[3], src['charges'])
            self.assertEqual(cells[4], src['credit'])
            self.assertEqual(cells[5], src['net_limit'])


if __name__ == '__main__':
    unittest.main()
