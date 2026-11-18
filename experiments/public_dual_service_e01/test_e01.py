"""Fault-injection tests designed to make E0.1 guards fail; self-authored.

Does not prove independence of gold labels, model-based prompt-injection safety,
privacy protection in live systems, or actual backend integration.
"""
from __future__ import annotations
import copy
import unittest
import run_e01 as e

class E01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c['id']: c for c in e.all_cases()}
        cls.frozen = e.load('frozen_sources.json')
        cls.oracle, cls.sidecar, cls.blob = e.validators()

    def output(self, case_id='S01'):
        return e.build_output(self.cases[case_id], self.frozen)

    def errors(self, output, case_id='S01'):
        return e.audit_output(self.cases[case_id], output, self.frozen, self.oracle, self.sidecar)

    def test_baseline_all_28(self):
        self.assertEqual(len(self.cases), 28)
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                out = self.output(case_id)
                self.assertEqual(out['sidecar']['decision'], case['expected'])
                self.assertEqual(self.errors(out,case_id), [])
                self.assertEqual(e.build_output(case,self.frozen),out)

    def test_original_frozen_input_hashes(self):
        import hashlib
        from pathlib import Path
        p=Path(e.__file__).resolve().parent
        self.assertEqual(hashlib.sha256((p/'frozen_cases.json').read_bytes()).hexdigest(), 'b8579e64088af24b2cae1375653ca0aa17052bcf544be440be6b332b2d199cf1')
        self.assertEqual(hashlib.sha256((p/'frozen_sources.json').read_bytes()).hexdigest(), 'd9986e8ca70823fb15ded7d21e6452bebcd368777ea05ce895a98b74f9c63268')

    def test_invalid_time_is_hold(self):
        self.assertEqual(self.output('S09')['sidecar']['decision'], 'INVALID_SOURCE_TIME')
        self.assertEqual(self.output('R12')['sidecar']['decision'], 'INVALID_SOURCE_TIME')
        self.assertEqual(self.output('S09')['sidecar']['evidence_count'], 0)

    def test_future_time_is_hold(self):
        self.assertEqual(self.output('S10')['sidecar']['decision'], 'FUTURE_SOURCE_TIME')
        self.assertEqual(self.output('R13')['sidecar']['decision'], 'FUTURE_SOURCE_TIME')

    def test_naive_and_impossible_timestamps_rejected(self):
        for raw in ['2026-11-18T12:00:00','2026-02-30T12:00:00Z','garbage','2026-11-18T12:00:00+25:00', None, True]:
            with self.subTest(raw=raw):
                self.assertEqual(e.validate_clock(raw)[0], 'INVALID_SOURCE_TIME')

    def test_utc_offset_parsed(self):
        self.assertEqual(e.validate_clock('2026-11-18T06:00:00-06:00')[0], 'CURRENT')

    def test_boundary_future_rejected(self):
        self.assertEqual(e.validate_clock('2026-11-18T12:00:01Z')[0], 'FUTURE_SOURCE_TIME')

    def test_bad_actual_source_timestamp_prevents_observation(self):
        changed=copy.deepcopy(self.frozen)
        changed['sources']['security']['observed_at']='garbage'
        with self.assertRaises(ValueError): e.build_output(self.cases['S01'],changed)

    def test_real_future_source_timestamp_prevents_observation(self):
        changed=copy.deepcopy(self.frozen)
        changed['sources']['resource']['observed_at']='2030-01-01T00:00:00Z'
        with self.assertRaises(ValueError): e.build_output(self.cases['R01'],changed)

    def test_budget_bool_rejected(self):
        self.assertEqual(self.output('R11')['sidecar']['decision'],'NEEDS_PROOF')

    def test_budget_nan_rejected(self):
        c=copy.deepcopy(self.cases['R01']);c['input']['budget_usd']=float('nan')
        self.assertEqual(e.build_output(c,self.frozen)['sidecar']['decision'],'NEEDS_PROOF')

    def test_budget_negative_rejected(self):
        c=copy.deepcopy(self.cases['R01']);c['input']['budget_usd']=-1
        self.assertEqual(e.build_output(c,self.frozen)['sidecar']['decision'],'NEEDS_PROOF')

    def test_alternate_goal_relevance(self):
        self.assertEqual(self.output('R10')['sidecar']['decision'],'RELEVANT_NOT_ELIGIBILITY_ASSESSED')

    def test_unsupported_goal_not_relevant(self):
        self.assertFalse(e.relevant_learning_goal('advanced offensive security live lab'))

    def test_duplicate_evidence_one_record(self):
        self.assertEqual(self.output('S06')['sidecar']['evidence_count'],1)
        self.assertEqual(self.output('R06')['sidecar']['evidence_count'],1)

    def test_conflicting_evidence_retained(self):
        self.assertEqual(self.output('S05')['sidecar']['evidence_count'],2)
        self.assertEqual(self.output('R05')['sidecar']['evidence_count'],2)

    def test_source_note_injection_no_output_change(self):
        for injected, clean in [('S07','S01'),('S14','S01'),('R07','R01'),('R14','R01')]:
            with self.subTest(injected=injected):
                a=self.output(injected);b=self.output(clean)
                self.assertEqual(a['sidecar']['decision'],b['sidecar']['decision'])
                self.assertEqual(a['sidecar']['rationale'],b['sidecar']['rationale'])
                self.assertNotIn(e.PRIVATE_SENTINEL,e.canonical(a).decode())

    def test_mutation_unauthorized_oracle_write_is_caught(self):
        out=self.output();out['observation']['authority_effect']='WRITE'
        self.assertIn('authority:authority_effect',self.errors(out))

    def test_mutation_oracle_authorizer_is_caught(self):
        out=self.output();out['observation']['can_authorize']=True
        self.assertIn('authority:can_authorize',self.errors(out))

    def test_mutation_wrong_action_is_caught(self):
        out=self.output();out['sidecar']['action_class']='EXECUTE'
        self.assertIn('sidecar_action',self.errors(out))

    def test_mutation_global_safety_claim_is_caught(self):
        out=self.output('S02');out['sidecar']['rationale']='All systems are safe.'
        self.assertIn('false_or_unauthorized_claim',self.errors(out,'S02'))

    def test_mutation_false_eligibility_claim_is_caught(self):
        out=self.output('R01');out['sidecar']['rationale']='You are eligible.'
        self.assertIn('false_or_unauthorized_claim',self.errors(out,'R01'))

    def test_mutation_private_marker_is_caught(self):
        out=self.output();out['sidecar']['rationale']+=' '+e.PRIVATE_SENTINEL
        self.assertIn('synthetic_private_marker_echo',self.errors(out))

    def test_mutation_source_note_echo_is_caught(self):
        out=self.output('S07');out['sidecar']['rationale']+=self.cases['S07']['input']['source_note']
        self.assertIn('untrusted_source_note_echo',self.errors(out,'S07'))

    def test_mutation_false_evidence_link_is_caught(self):
        out=self.output();out['sidecar']['evidence_links']=['https://attacker.example/claim']
        self.assertIn('bad_evidence_link',self.errors(out))

    def test_mutation_false_source_digest_is_caught(self):
        out=self.output();out['observation']['source']['content_sha256']='a'*64
        self.assertIn('oracle_source_mismatch',self.errors(out))

    def test_mutation_evidence_count_is_caught(self):
        out=self.output();out['sidecar']['evidence_count']=0
        self.assertIn('evidence_mismatch',self.errors(out))

    def test_mutation_sidecar_decision_is_caught(self):
        out=self.output();out['sidecar']['decision']='NOT_AFFECTED_BY_THIS_ADVISORY'
        self.assertIn('frozen_expected_mismatch',self.errors(out))

    def test_mutation_invalid_observation_time_is_caught(self):
        out=self.output();out['observation']['recorded_at']='garbage'
        self.assertIn('bad_recorded_at',self.errors(out))

    def test_mutation_future_observation_time_is_caught(self):
        out=self.output();out['observation']['as_of']='2030-01-01T12:00:00Z'
        self.assertIn('bad_as_of',self.errors(out))

    def test_mutation_mismatched_observation_claim_is_caught(self):
        out=self.output();out['observation']['observation']='Everything safe.'
        self.assertIn('observation_sidecar_mismatch',self.errors(out))

    def test_mutation_missing_scope_is_caught(self):
        out=self.output('S02');out['sidecar']['rationale']='No match for this advisory.'
        self.assertIn('missing_advisory_scope',self.errors(out,'S02'))

    def test_mutation_missing_eligibility_scope_is_caught(self):
        out=self.output('R01');out['sidecar']['rationale']='A relevant free beginner resource.'
        self.assertIn('missing_eligibility_scope',self.errors(out,'R01'))

    def test_mutation_extra_sidecar_field_rejected(self):
        out=self.output();out['sidecar']['approve_for_user']=True
        self.assertTrue(any(x.startswith('sidecar_schema:') for x in self.errors(out)))

    def test_source_url_invalid_rejected(self):
        bad=copy.deepcopy(self.frozen)
        bad['sources']['security']['source_url']='http://localhost/admin'
        with self.assertRaises(ValueError):e.build_output(self.cases['S01'],bad)

    def test_schema_does_not_use_any_new_authority(self):
        out=self.output()
        self.assertEqual(out['observation']['authority_effect'],'NONE')
        self.assertFalse(out['observation']['can_authorize'])
        self.assertTrue(out['observation']['advisory_only'])

if __name__=='__main__':
    unittest.main(verbosity=2)
