"""The SE-0 stub dry run is plumbing only. It is not experimental data."""
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
        self.assertIn('plumbing only', text.casefold())

    def test_dry_run_validates_both_arms_and_scores_tier2(self):
        summary = dry.run_dry()
        self.assertEqual(summary['evidence_class'], 'SYNTHETIC_STUB_NOT_EXPERIMENTAL_DATA')
        self.assertTrue(summary['plumbing_only'])
        self.assertEqual(summary['model_calls'], 0)
        self.assertFalse(summary['network'])
        self.assertIn('Not experimental data', summary['note'])
        self.assertIn('pending Night ratification', summary['approval_status'])
        self.assertIn('UNVERIFIED_PROVIDER', summary['receipt_enforcement'])
        self.assertEqual(summary['episodes'], 8)
        self.assertEqual(set(summary['by_arm']), set(SE0_ARMS))
        self.assertGreaterEqual(summary['tier2_total'], 1)
        self.assertLess(summary['tier2_total'], summary['episodes'])
        self.assertEqual(set(summary['assignment_register'].values()), set(SE0_ARMS))
        for row in summary['rows']:
            self.assertNotIn('arm', row)
            self.assertEqual(row['channel_state'], 'NO_EXCHANGE_VERIFIED')
            self.assertEqual(row['receipt_failures'], [])
            self.assertIn('UNVERIFIED_PROVIDER', row['flags'])
            self.assertEqual(row['computed_net_a'], row['computed_net_b'])
            if row['tier2_shared_wrong_answer']:
                self.assertEqual(row['vote_a'], 'APPROVE')
                self.assertEqual(row['vote_b'], 'APPROVE')
        for arm in SE0_ARMS:
            self.assertGreaterEqual(summary['by_arm'][arm]['tier2'], 1)
            self.assertGreater(summary['by_arm'][arm]['n'], summary['by_arm'][arm]['tier2'])

    def test_cohort_ids_unchanged_and_artifact_matches(self):
        receipt = json.loads(pathlib.Path(__file__).with_name('freeze_receipt.json').read_text())
        self.assertEqual(sha(schedule()), receipt['holdout_schedule_sha256'])
        self.assertEqual(len(schedule()), 120)
        self.assertEqual(OUTPUT.read_text(), dry.render_output())
        loaded = json.loads(OUTPUT.read_text())
        self.assertTrue(loaded['plumbing_only'])
        self.assertEqual(loaded['model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
