"""Atlas bridge falsifiers: exact-path lineage and non-authoritative boundaries."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architecture.codebase_atlas_bridges import project, SCHEMA

SESSION_SOURCE='chat_graph/source/humanaios_cross_chat_knowledge_graph.v0.1.json'
SESSION_OVERLAY='chat_graph/evidence/github_hydration_2026-10-02.json'

class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)
        self.git('init','-q')
        self.git('config','user.name','Atlas Test')
        self.git('config','user.email','atlas@example.test')
        self.put('EVIDENCE_GRAPH.json', {'nodes':[{'id':'A1','label':'proof.py'},
                                                    {'id':'A2','label':'same.py'},
                                                    {'id':'C1','label':'claim'}],
                                          'edges':[{'from':'A1','to':'C1','relation':'test'}]})
        self.put('docs/proof.py','VALUE=1')
        self.put('docs/same.py','same')
        self.put('app/same.py','same')
        self.put(SESSION_SOURCE, {'nodes':[{'id':'n1','label':'docs/proof.py'}],
                                  'edges':[], 'generated_date':'2026-10-02'})
        self.put(SESSION_OVERLAY, {'authority_effect':'NONE','observed_on':'2026-10-02',
                                    'repository_snapshot':{'commit_sha':'a'*40}})
        self.put('chat_graph/schema/longitudinal_graph.schema.json',{'type':'object'})
        self.put('tools/state_continuity_verification_v0_1.py','# passive\n')
        self.put('schemas/validated_learning_record_v1.schema.json', {'type':'object'})
        self.put('experiments/scvc_v02/trusted_witness.py','# independently authenticated elsewhere\n')
        self.put('tools/repository_coordinator_state_v1_1.py','# state bridge\n')
        self.put('REPOSITORY_COORDINATOR_POLICY.json', {
            'invariants':['NO_SELF_ADMISSION'],
            'evaluation_admission':{'merge_authority':False},
            'state':{'merge_authority':False},
            'control_plane':{'paths':['tools/repository_coordinator_state_v1_1.py',
                                      'docs/proof.py','../private/key']}})
        self.git('add','.')
        self.git('commit','-qm','source fixtures')
        self.head=self.git('rev-parse','HEAD').strip()
        self.atlas={'head_sha':self.head,'snapshot':'HEAD_WORKTREE', 'worktree_clean':True,
                    'authority_effect':'NONE','merge_authority':False}
        self.tracked=self.git('ls-files').splitlines()
        self.owner=lambda p:p.split('/')[0] if '/' in p else 'root'

    def git(self,*cmd):
        return subprocess.run(['git','-C',str(self.repo),*cmd],capture_output=True,
                              text=True,check=True).stdout

    def put(self,path,value):
        f=self.repo/path
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(json.dumps(value) if isinstance(value,dict) else value,encoding='utf-8')

    def output(self):
        return project(self.repo,self.atlas,self.tracked,self.owner)

    def test_four_views_and_no_promotion(self):
        a=self.output()
        self.assertEqual(a['schema'],SCHEMA)
        self.assertEqual(set(a['views']),{'evidence','session','scvc','coordinator'})
        for v in a['views'].values():
            self.assertEqual(v['verification'],'NOT_ESTABLISHED')
            self.assertEqual(v['state'],'SOURCE_BOUND')
        self.assertEqual(a['views']['evidence']['node_count'], 3)
        self.assertEqual(a['views']['evidence']['edge_count'], 1)
        self.assertEqual(a['views']['session']['node_count'], 1)
        self.assertGreaterEqual(a['views']['session']['bindings'], 3)
        self.assertGreaterEqual(a['views']['evidence']['bindings'], 1)
        self.assertFalse(a['can_authorize'])
        self.assertFalse(a['authenticated'])
        self.assertFalse(a['merge_authority'])
        self.assertEqual(a['authority_effect'],'NONE')
        self.assertEqual(a['views']['scvc']['continuity_status'],'NOT_ESTABLISHED')
        self.assertEqual(a['views']['coordinator']['admission_status'],'STATE_BRANCH_NOT_READ')
        self.assertFalse(a['views']['coordinator']['state_branch_verified'])
        self.assertTrue(all(b['authority_effect']=='NONE' for b in a['bindings']))

    def test_unique_exact_evidence_binding_no_fuzzy_or_ambiguous(self):
        e=[b for b in self.output()['bindings'] if b['graph']=='evidence']
        self.assertEqual(len([b for b in e if b['relation']=='EVIDENCE_NODE_LABEL_MATCH']),1)
        matched=[b for b in e if b['relation']=='EVIDENCE_NODE_LABEL_MATCH']
        self.assertEqual(matched[0]['path'],'docs/proof.py')
        self.assertEqual(matched[0]['epistemic_state'],'DECLARED_NOT_VERIFIED')

    def test_session_cannot_make_historical_snapshot_current(self):
        v=self.output()['views']['session']['historical_observation']
        self.assertEqual(v['overlay_observed_on'],'2026-10-02')
        self.assertNotEqual(v['overlay_commit_sha'],self.head)
        self.assertFalse(v['same_as_atlas_head'])
        session=[b for b in self.output()['bindings'] if b['graph']=='session']
        derived=[b for b in session if b['relation']=='CHAT_SYNTHESIS_EXACT_PATH']
        self.assertEqual([b['epistemic_state'] for b in derived],['CHAT_DERIVED'])
        self.assertEqual(derived[0]['source_time'],'2026-10-02')

    def test_git_head_not_dirty_worktree_source_and_no_secret(self):
        before=self.output()
        self.put(SESSION_SOURCE,{'nodes':[{'id':'attack','label':'/private/token'}], 'edges':[]})
        after=self.output()
        self.assertEqual(before,after)
        self.assertNotIn('private/token',json.dumps(after))

    def test_malicious_policies_cannot_create_authority(self):
        self.atlas['merge_authority']=True
        with self.assertRaisesRegex(ValueError,'authority'):
            self.output()
        self.atlas['merge_authority']=False
        self.put('REPOSITORY_COORDINATOR_POLICY.json',{
            'invariants': [],'state':{'merge_authority':True},
            'evaluation_admission':{'merge_authority':False}, 'control_plane':{'paths':[]}})
        self.git('add','REPOSITORY_COORDINATOR_POLICY.json')
        self.git('commit','-qm','adversarial policy')
        self.atlas['head_sha']=self.git('rev-parse','HEAD').strip()
        with self.assertRaisesRegex(ValueError,'boundary'):
            self.output()

    def test_untracked_inputs_never_included_and_missing_means_incomplete(self):
        self.put('private_roots.json',{'token':'VERY_PRIVATE'})
        a=self.output()
        self.assertNotIn('VERY_PRIVATE',json.dumps(a))
        self.tracked.remove('experiments/scvc_v02/trusted_witness.py')
        a=project(self.repo,self.atlas,self.tracked,self.owner)
        self.assertEqual(a['views']['scvc']['state'],'INCOMPLETE_SOURCE')
        self.assertEqual(a['views']['scvc']['present'],2)

    def test_head_pin_cannot_be_forged(self):
        self.atlas['head_sha']='b'*40
        with self.assertRaisesRegex(ValueError,'head does not match'):
            self.output()

    def test_repeated_projection_is_deterministic(self):
        self.assertEqual(self.output(),self.output())

if __name__=='__main__':
    unittest.main()
