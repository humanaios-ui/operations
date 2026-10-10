import importlib.util,pathlib,tempfile,hashlib,unittest
P=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver',P/'tools/governance_invariant_evaluator.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class TestEvaluator(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.pins={}
  for name in (*m.REQUIRED,'.gov-control/governance-files.yaml'):
   f=self.root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('- path: REGISTERED.md\n');self.pins[name]=hashlib.sha256(f.read_bytes()).hexdigest()
  self.data=dict(schema='humanaios.governance-evaluation-input.v1',head_sha='a'*40,base_sha='b'*40,diff_head_sha='a'*40,diff_base_sha='b'*40,source='protected_checkout',governance_pins=self.pins,changed_files=['tools/harmless.py'],claimed_authority='Z1',can_authorize=False,authority_effect='NONE')
 def tearDown(self):self.tmp.cleanup()
 def check(self):return m.evaluate(self.data,self.root)
 def test_valid_advisory(self):
  r=self.check();self.assertEqual(r['status'],'PASS');self.assertFalse(r['admitted'])
 def test_missing_evidence(self):
  self.data['governance_pins']={};self.assertEqual(self.check()['status'],'FAIL')
 def test_fake_pin(self):
  self.data['governance_pins']['REGISTRY_SPEC.md']='0'*64;self.assertEqual(self.check()['status'],'FAIL')
 def test_self_ratification(self):
  self.data['claimed_authority']='Z2';self.assertEqual(self.check()['status'],'FAIL')
 def test_alias(self):
  self.data['changed_files']=['./REGISTERED.md'];self.assertEqual(self.check()['status'],'FAIL')
 def test_distinct_events(self):
  ids=[x['id'] for x in self.check()['event_nodes']];self.assertTrue(set(('A1','A3','B6','B6b'))<=set(ids))
 def test_diff_mismatch(self):
  self.data['diff_head_sha']='f'*40;self.assertEqual(self.check()['status'],'FAIL')
 def test_unsafe_path(self):
  self.data['changed_files']=['../REGISTERED.md'];self.assertEqual(self.check()['status'],'FAIL')
if __name__=='__main__':unittest.main()
