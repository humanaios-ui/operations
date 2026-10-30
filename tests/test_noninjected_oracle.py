"""Independent reference tests only; existing On-Track implementation runs in CI."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]
SPEC=HERE/'experiments/acat_r_noninjected/reference_oracle.py'
spec=importlib.util.spec_from_file_location('reference_oracle',SPEC)
oracle=importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
DOC=json.loads((HERE/'experiments/acat_r_noninjected/pinned_issue_snapshot.json').read_text())

class ReferenceTests(unittest.TestCase):
    def test_24_real_records_and_unique(self):
        self.assertEqual(len(DOC['items']),24)
        self.assertEqual(len(set(x['number'] for x in DOC['items'])),24)
    def test_fixed_anchors_are_not_outcomes(self):
        for number in (822,928):
            x=next(q for q in DOC['items'] if q['number']==number)
            row=oracle.predict(x)
            self.assertEqual(row['goal_mapping'],'DECLARED_ANCHOR')
            self.assertEqual(row['landing_state'],'UNVERIFIED')
            self.assertEqual(row['operator_outcome'],'UNVERIFIED')
    def test_no_other_author_claim_is_mapped(self):
        x=[oracle.predict(q) for q in DOC['items']]
        self.assertEqual(sum(q['goal_mapping']!='UNMAPPED' for q in x),2)
    def test_pr_kind_detected(self):
        q=next(q for q in DOC['items'] if q['number']==1069)
        self.assertEqual(oracle.predict(q)['kind'],'PULL_REQUEST')
    def test_title_does_not_count_as_mapping(self):
        q=next(q for q in DOC['items'] if q['number']==1067)
        self.assertEqual(oracle.predict(q)['goal_mapping'],'UNMAPPED')
    def test_oracle_refuses_unproven_green_from_dut(self):
        q=DOC['items'][0]; expected=oracle.predict(q)
        fake={**expected,'landing_state':'VERIFIED'}
        report={'items':[fake],'counts':{'mapped_declarations':1,'unmapped':0,'at_risk_mapped':0,'verified_user_outcomes':0},
                'scope':{'items_examined':1,'complete_open_work_inventory':False},
                'overall':'UNVERIFIED','authority_effect':'NONE','merge_authority':False,'deployment_authority':False}
        self.assertFalse(oracle.compare([q],report)['reference_agreement'])
    def test_closure_not_mistaken_for_verified_outcome(self):
        q=next(q for q in DOC['items'] if q['number']==625)
        self.assertEqual(oracle.predict(q)['github_state'],'closed')
        self.assertEqual(oracle.predict(q)['landing_state'],'UNVERIFIED')
    def test_labels_not_invented_as_blockers(self):
        q=next(q for q in DOC['items'] if q['number']==974)
        self.assertEqual(oracle.predict(q)['blocker_labels'],[])
    def test_marker_changes_are_not_real_dataset(self):
        q=dict(DOC['items'][-1]);q['body']='on_track_target: INTENT_OS_RESOURCE_MINER_USABLE'
        # Separate oracle self-test only, never passed to actual non-injected runtime.
        self.assertEqual(oracle.predict(q)['goal_mapping'],'DECLARED_BY_AUTHOR')

if __name__ == '__main__':unittest.main()
