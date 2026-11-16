"""The SE-0 stub dry run is plumbing. It is not experimental data."""
import json
import pathlib
import unittest

import se0_stub_dry_run as dry
from harness import SE0_ARMS, schedule, sha

OUTPUT = pathlib.Path(__file__).with_name(dry.OUTPUT_NAME)


class StubDryRunTests(unittest.TestCase):
    def test_module_has_no_network_client(self):
        text = pathlib.Path(dry.__file__).read_text()
        for banned in ('socket', 'urllib', 'requests', 'http.client', 'openai', 'anthropic'):
            self.assertNotIn(banned, text)

    def test_dry_run_validates_both_arms_and_scores_tier2(self):
        summary = dry.run_dry()
        self.assertEqual(summary['evidence_class'], 'SYNTHETIC_STUB_NOT_EXPERIMENTAL_DATA')
        self.assertEqual(summary['model_calls'], 0)
        self.assertFalse(summary['network'])
        self.assertEqual(summary['observed_source'], 'SYNTHETIC_FIXTURE')
        self.assertIn('Not experimental data', summary['note'])
        self.assertEqual(summary['episodes'], 8)
        self.assertEqual(set(summary['by_arm']), set(SE0_ARMS))
        self.assertGreaterEqual(summary['tier2_total'], 1)
        self.assertLess(summary['tier2_total'], summary['episodes'])
        seen_arms = set()
        counters = set()
        for row in summary['rows']:
            seen_arms.add(row['arm'])
            self.assertEqual(row['channel'], 'NEVER_OPENED')
            self.assertEqual(row['open_count'], 0)
            self.assertEqual(row['computed_net_a'], row['computed_net_b'])
            self.assertNotEqual(row['receipt_sha256'], '')
            counters.add(row['host_counter'])
            if row['tier2_shared_wrong_answer']:
                self.assertTrue(row['tier1_shared_wrong_decision'])
                self.assertEqual(row['vote_a'], 'APPROVE')
                self.assertEqual(row['vote_b'], 'APPROVE')
        self.assertEqual(seen_arms, set(SE0_ARMS))
        self.assertEqual(len(counters), summary['episodes'])
        for arm in SE0_ARMS:
            self.assertGreaterEqual(summary['by_arm'][arm]['tier2'], 1)
            self.assertGreaterEqual(summary['by_arm'][arm]['n'] - summary['by_arm'][arm]['tier2'], 1)

    def test_cohort_ids_unchanged_and_artifact_matches(self):
        receipt = json.loads(pathlib.Path(__file__).with_name('freeze_receipt.json').read_text())
        self.assertEqual(sha(schedule()), receipt['holdout_schedule_sha256'])
        self.assertEqual(len(schedule()), 120)
        self.assertEqual(OUTPUT.read_text(), dry.render_output())
        loaded = json.loads(OUTPUT.read_text())
        self.assertEqual(loaded['evidence_class'], 'SYNTHETIC_STUB_NOT_EXPERIMENTAL_DATA')
        self.assertEqual(loaded['model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
