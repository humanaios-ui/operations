"""Offline negative controls for the derived independent-readback/challenge projection."""
import copy
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
try:
    from resource_miner import independent_readback as ib
except ModuleNotFoundError:  # standalone qualification package (offline helper)
    sys.path.insert(0, str(HERE))
    import independent_readback as ib


class IndependentReadbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old = HERE / 'fixtures' / 'internal_readback' if (HERE / 'fixtures' / 'internal_readback').is_dir() else HERE / 'fixtures'
        cls.original_snapshot = json.loads((old / 'snapshot.json').read_text())
        cls.original_projection = json.loads((old / 'initial_broker_projection.json').read_text())
        cls.original_readback = json.loads((old / 'github_readback_pr987.json').read_text())
        cls.original_challenges = json.loads((old / 'challenge_corrections_pr987.json').read_text())

    def setUp(self):
        self.s = copy.deepcopy(self.original_snapshot)
        self.b = copy.deepcopy(self.original_projection)
        self.r = copy.deepcopy(self.original_readback)
        self.c = copy.deepcopy(self.original_challenges)

    def run_qualification(self):
        return ib.qualify(self.s, self.b, self.r, self.c)

    def test_generated_broker_projection_matches_frozen_fixture_when_installed(self):
        try:
            from resource_miner.internal_repository_broker import project
        except ModuleNotFoundError:
            self.skipTest('Requires Resource Miner package checkout; frozen projection still tested')
        generated = project(self.s)
        # Serializer defaults can evolve: preserve source identity/revision,
        # never mistake whole-dict equality for a provenance invariant.
        original = {r['item_ref']: r for r in self.b['resources']}
        current = {r['item_ref']: r for r in generated['resources']}
        self.assertEqual(set(original), set(current))
        for key in original:
            for field in ('resource_id', 'item_ref', 'head_sha', 'source_url',
                          'canonical_url', 'authority_effect', 'source_authentication'):
                self.assertEqual(original[key][field], current[key][field])

    def test_round_trip_readback_challenge_correction_retains_ids_revision(self):
        originals = [copy.deepcopy(x) for x in (self.s, self.b, self.r, self.c)]
        q = self.run_qualification()
        self.assertEqual(q['source_head_sha'], self.r['pr']['head_sha'])
        self.assertEqual(q['source_git_blob_sha'], self.r['blob']['git_blob_sha'])
        self.assertEqual(q['source_url'], self.r['pr']['source_url'])
        self.assertEqual(q['derived_claims']['SOURCE_TITLE_EXACT']['state'], 'CONTRADICTED')
        self.assertEqual(q['original_snapshot_title'], self.s['items'][0]['title'])
        self.assertEqual(q['independently_observed_title'], self.r['pr']['title'])
        self.assertEqual(q['ci_returned_conclusions'], {'success':17})
        self.assertEqual(q['derived_claims']['ALL_REVIEW_THREADS_RESOLVED']['state'], 'CONTRADICTED')
        self.assertEqual(len(q['correction_events']),3)
        self.assertEqual([self.s,self.b,self.r,self.c],originals)

    def test_persistent_immutable_source_and_two_distinct_projections(self):
        first=self.run_qualification()
        raw_before=ib.digest(self.s),ib.digest(self.b),ib.digest(self.r)
        # Challenge overlay can expand independently, without editing GitHub or the broker.
        self.c.append({'event_id':'CHAL-PR987-03','claim_id':'AGENT_BEHAVIOR_INDEPENDENTLY_VALIDATED',
                       'action':'CHALLENGE','reason_code':'NO_AGENT_RUNTIME_WITNESS',
                       'evidence_url':self.r['pr']['source_url'],'observed_at':self.r['observed_at']})
        second=self.run_qualification()
        self.assertNotEqual(first['correction_chain_sha256'], second['correction_chain_sha256'])
        self.assertEqual(raw_before,(ib.digest(self.s),ib.digest(self.b),ib.digest(self.r)))
        self.assertEqual(first['source_head_sha'],second['source_head_sha'])
        self.assertEqual(first['source_git_blob_sha'],second['source_git_blob_sha'])

    def test_stale_forged_head_fails_closed(self):
        self.s['items'][0]['head_sha']='0'*40
        with self.assertRaisesRegex(ValueError,'revision drift'):
            self.run_qualification()

    def test_spoofed_source_identity_fails_closed(self):
        self.r['pr']['source_url']='https://github.com/humanaios-ui/operations/pull/978'
        with self.assertRaisesRegex(ValueError,'identity'):
            self.run_qualification()

    def test_historical_title_alias_does_not_overwrite_source(self):
        orig=self.s['items'][0]['title']
        q=self.run_qualification()
        self.assertEqual(self.s['items'][0]['title'],orig)
        self.assertNotEqual(q['independently_observed_title'],orig)
        self.assertIn('CORRECT',ib.board_html(q))
        self.assertIn('contradicted',ib.systems_report(q).lower())

    def test_untrusted_source_cannot_claim_authority(self):
        self.b['resources'][0]['authority_effect']='ADMIT'
        with self.assertRaisesRegex(ValueError,'promoted'):
            self.run_qualification()

    def test_untrusted_source_cannot_claim_authentication(self):
        self.b['resources'][0]['source_authentication']='VERIFIED'
        with self.assertRaisesRegex(ValueError,'promoted'):
            self.run_qualification()

    def test_mismatched_ci_run_identifier_fails_closed(self):
        self.r['checks'][0]['run_url']=self.r['checks'][1]['run_url']
        with self.assertRaisesRegex(ValueError,'URL/identity'):
            self.run_qualification()

    def test_stale_ci_commit_rejected(self):
        self.r['checks'][0]['head_sha']='0'*40
        with self.assertRaisesRegex(ValueError,'exact head'):
            self.run_qualification()

    def test_review_thread_url_must_bind_to_PR(self):
        self.r['review_threads']['source_url']='https://github.com/humanaios-ui/operations/pull/978/files'
        with self.assertRaisesRegex(ValueError,'review thread'):
            self.run_qualification()

    def test_foreign_challenge_url_rejected(self):
        self.c[0]['evidence_url']='https://attacker.example/challenge'
        with self.assertRaisesRegex(ValueError,'source-linked'):
            self.run_qualification()

    def test_replay_challenge_event_rejected(self):
        self.c[1]['event_id']=self.c[0]['event_id']
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.run_qualification()

    def test_forged_prior_hash_not_allowed_in_input(self):
        self.c[0]['previous_event_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'extra'):
            self.run_qualification()

    def test_malformed_source_title_escaped(self):
        # Title is user data, never inserted as executable markup.
        self.r['pr']['title']='<script>alert(1)</script>'
        q=self.run_qualification()
        page=ib.board_html(q)
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn("default-src 'none'",page)

    def test_no_IO_during_qualification(self):
        from unittest.mock import patch
        with patch('builtins.open',side_effect=AssertionError('file access')):
            q=self.run_qualification()
            ib.board_html(q);ib.systems_report(q)

    def test_no_permission_upgrades(self):
        q=self.run_qualification()
        for k in ('may_admit','may_merge','may_execute','source_mutated'):
            self.assertFalse(q[k])
        self.assertEqual(q['authority_effect'],'NONE')
        self.assertEqual(q['behavioral_validation'],'NOT_ESTABLISHED')
        self.assertEqual(q['authentication'],'NOT_CRYPTOGRAPHICALLY_ATTESTED')


if __name__ == '__main__':
    unittest.main()