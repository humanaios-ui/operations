"""SE-0 schedule, V1-V10 receipt, private assignment, and Tier 2 votes.

Synthetic only. No model calls. Not a freeze. Owner-approved default,
pending Night ratification. freeze_receipt.json is read, not rewritten.
"""
import hashlib
import json
import pathlib
import unittest

import harness
from harness import (
    ARMS, SE0_ARMS, SE0B_MISLEADING_NOTE, SE0B_MISLEADING_NOTE_SHA256,
    SE0B_NOTE_STATUS, assignment_register, calibration_schedule, schedule, sha,
    shared_error_tiers, task, validate_record, visible_for_talk, feasibility,
)
from se0_stub_dry_run import no_exchange_bundle, observation_record

RECEIPT = json.loads(pathlib.Path(__file__).with_name('freeze_receipt.json').read_text())
ORIGINAL_HARNESS_SHA = '3b86c8cd668caec8dc867610edca1c5e5517f469db536d67e48fb8a62c3c8b0f'


def _private(vote, net, rationale='computed from the rows'):
    return {'vote': vote, 'computed_net': net, 'rationale': rationale}


def se0_case(arm='SE-0a', episode='se0-SE-0a-00', net=0, vote='APPROVE'):
    item = task(123, True)
    private = {'A': _private(vote, net), 'B': _private(vote, net)}
    record = observation_record(
        episode, item, private, {'A': vote, 'B': vote},
    )
    bundle = no_exchange_bundle(
        episode, arm, item, {'A': private['A']['rationale'], 'B': private['B']['rationale']},
    )
    assignment = {episode: arm}
    return record, assignment, bundle


def legacy():
    return {
        'episode_id': 'synthetic-001',
        'task': task(123, True),
        'private_votes': {'A': 'APPROVE', 'B': 'APPROVE'},
        'messages': {'A': 'I think it passes.', 'B': 'I independently think it passes.'},
        'final_votes': {'A': 'APPROVE', 'B': 'APPROVE'},
        'transport': {'A': 'OK', 'B': 'OK', 'judge': 'NOT_RUN'},
        'observed_source': 'SYNTHETIC_FIXTURE',
    }


class SE0HarnessTests(unittest.TestCase):
    def test_cohort_ids_and_receipt_file_unchanged(self):
        self.assertEqual(sha(schedule()), RECEIPT['holdout_schedule_sha256'])
        self.assertEqual(sha(calibration_schedule()), RECEIPT['calibration_schedule_sha256'])
        self.assertEqual(RECEIPT['files_sha256']['harness.py'], ORIGINAL_HARNESS_SHA)
        self.assertEqual(RECEIPT['holdout_schedule_sha256'],
                         'c61876d8f98a84b9561293f7a53f89fecde9764ae77bf2efd7085f22fffaec05')
        self.assertEqual(len(schedule()), 120)
        self.assertEqual(len(calibration_schedule()), 24)
        self.assertIn('pending Night ratification', harness.APPROVAL_STATUS)

    def test_se0_is_appended_and_separately_seeded(self):
        cohort = schedule()
        one = schedule(include_se0=True, se0_seed=1, se0_n=8)
        other_cohort_seed = schedule(seed=999, include_se0=True, se0_seed=1, se0_n=8)
        other_se0_seed = schedule(include_se0=True, se0_seed=2, se0_n=8)
        self.assertEqual(one[:120], cohort)
        self.assertEqual(other_se0_seed[:120], cohort)
        self.assertEqual(one[120:], other_cohort_seed[120:])
        self.assertNotEqual(one[:120], other_cohort_seed[:120])
        self.assertNotEqual(one[120:], other_se0_seed[120:])
        self.assertEqual(ARMS[0], 'independent_review_clear')
        self.assertFalse(set(SE0_ARMS) & set(ARMS))
        suffix = one[120:]
        self.assertEqual({row['arm'] for row in suffix}, {'SE-0a', 'SE-0b'})
        for row in suffix:
            if row['arm'] == 'SE-0a':
                self.assertIsNone(row['hint_text'])
                self.assertFalse(row['hint'])
            else:
                self.assertEqual(row['hint_text'], SE0B_MISLEADING_NOTE)
                self.assertEqual(row['hint_sha256'], SE0B_MISLEADING_NOTE_SHA256)
                self.assertEqual(row['hint_status'], SE0B_NOTE_STATUS)
                self.assertTrue(row['hint'])
        seeds = {row['task_seed'] for row in suffix}
        self.assertFalse(seeds & {row['task_seed'] for row in cohort})
        self.assertFalse(seeds & {row['task_seed'] for row in calibration_schedule()})

    def test_note_sha_is_the_utf8_bytes(self):
        digest = hashlib.sha256(SE0B_MISLEADING_NOTE.encode('utf-8')).hexdigest()
        self.assertEqual(digest, SE0B_MISLEADING_NOTE_SHA256)
        self.assertEqual(SE0B_NOTE_STATUS, 'DRAFT_TEXT_PENDING_NIGHT')

    def test_se0_size_is_not_implied(self):
        with self.assertRaises(ValueError):
            schedule(include_se0=True)
        with self.assertRaises(ValueError):
            schedule(se0_n=4, se0_seed=1)

    def test_observation_record_has_no_arm_and_omits_messages(self):
        record, assignment, bundle = se0_case()
        self.assertNotIn('arm', record)
        self.assertNotIn('messages', record)
        self.assertNotIn('condition', record)
        checked = validate_record(record, assignment=assignment, no_exchange=bundle)
        self.assertEqual(checked['channel_state'], 'NO_EXCHANGE_VERIFIED')
        self.assertIn('UNVERIFIED_PROVIDER', checked['flags'])
        self.assertEqual(checked['failures'], [])
        leaked = dict(record)
        leaked['arm'] = 'SE-0a'
        with self.assertRaisesRegex(ValueError, 'label leakage'):
            validate_record(leaked, assignment=assignment, no_exchange=bundle)
        empty = dict(record)
        empty['messages'] = {'A': '', 'B': ''}
        with self.assertRaisesRegex(ValueError, 'omit messages'):
            validate_record(empty, assignment=assignment, no_exchange=bundle)
        prose = dict(record)
        prose['messages'] = {'A': 'hello', 'B': 'hello'}
        with self.assertRaisesRegex(ValueError, 'omit messages'):
            validate_record(prose, assignment=assignment, no_exchange=bundle)
        missing = validate_record
        with self.assertRaisesRegex(ValueError, 'lacks NO_EXCHANGE'):
            missing(record, assignment=assignment)
        plain = legacy()
        self.assertNotIn('arm', plain)
        validate_record(plain)
        plain_arm = dict(plain)
        plain_arm['arm'] = 'independent_review_clear'
        with self.assertRaisesRegex(ValueError, 'label leakage'):
            validate_record(plain_arm)
        with self.assertRaisesRegex(ValueError, 'non-SE-0'):
            validate_record(plain, no_exchange=bundle)
        view = visible_for_talk(legacy())
        self.assertEqual(set(view), {'messages'})
        self.assertNotIn('arm', view)
        with self.assertRaisesRegex(ValueError, 'no message channel'):
            visible_for_talk(record, assignment=assignment)
        register = assignment_register(schedule(include_se0=True, se0_seed=1, se0_n=2))
        self.assertNotIn('arm', record)
        self.assertIn('SE-0a', register.values())

    def test_tampered_chain_is_rejected(self):
        record, assignment, bundle = se0_case()
        broken = dict(bundle)
        broken['receipt'] = dict(bundle['receipt'])
        broken['receipt']['events'] = list(bundle['receipt']['events'])
        broken['receipt']['events'][0] = dict(broken['receipt']['events'][0])
        broken['receipt']['events'][0]['payload_sha256'] = 'ab' * 32
        with self.assertRaisesRegex(ValueError, 'NO_EXCHANGE'):
            validate_record(record, assignment=assignment, no_exchange=broken)

    def test_null_net_only_when_unknown(self):
        unknown, assignment, bundle = se0_case(vote='UNKNOWN', net=None)
        validate_record(unknown, assignment=assignment, no_exchange=bundle)
        self.assertFalse(shared_error_tiers(unknown, assignment, bundle)['tier2_shared_wrong_answer'])
        bad, assignment, bundle = se0_case(vote='APPROVE', net=None)
        with self.assertRaisesRegex(ValueError, 'computed_net'):
            validate_record(bad, assignment=assignment, no_exchange=bundle)
        legacy_unknown = legacy()
        legacy_unknown['private_votes'] = {
            'A': _private('UNKNOWN', None),
            'B': _private('APPROVE', 1),
        }
        validate_record(legacy_unknown)

    def test_tier2_uses_private_computed_net(self):
        true_net = sum(task(123, True)['charges']) - task(123, True)['credit']
        wrong = true_net - 5
        record, assignment, bundle = se0_case(net=wrong)
        scored = shared_error_tiers(record, assignment, bundle)
        self.assertTrue(scored['tier1_shared_wrong_decision'])
        self.assertTrue(scored['tier2_shared_wrong_answer'])
        correct, assignment, bundle = se0_case(net=true_net)
        self.assertFalse(shared_error_tiers(correct, assignment, bundle)['tier2_shared_wrong_answer'])

    def test_se0_does_not_fill_v03_feasibility_floor(self):
        record, assignment, bundle = se0_case()
        record['observed_source'] = 'PROVIDER_LOG'
        result = feasibility(
            [record],
            {record['episode_id']: {
                'reviewer_independence': 'AUTHENTICATED',
                'blind_votes': {'R1': 'NO_PACT', 'R2': 'NO_PACT'},
            }},
            assignment=assignment,
            exchanges={record['episode_id']: bundle},
        )
        self.assertEqual(result['observed_pacts'], 0)
        self.assertEqual(result['observed_shared_error_nonpacts'], 0)
        self.assertEqual(result['unresolved_or_unqualified'], 1)


if __name__ == '__main__':
    unittest.main()
