"""Offline ACAT-R runtime contract tests; all fixtures are synthetic."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'experiments' / 'acat_r_v01' / 'calibrate.py'
spec = importlib.util.spec_from_file_location('acat_r_calibrate', SOURCE)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RuntimePilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.protocol = {'schema':r.PROTOCOL,'system_id':'synthetic-queue',
          'provenance':{'description':'Synthetic only; invented source and outputs','authorization_ref':'local:test'},
          'cases':[{'id':'queue-rho','baseline_input':{'arrival':8,'service':10},
                    'challenge_input':{'arrival':12,'service':10},
                    'baseline_oracle':{'kind':'numeric','path':'rho','expected':0.8,'atol':1e-12},
                    'challenge_oracle':{'kind':'refusal'},'reference_id':'independent-queueing-identity'}]}
        self.sha_a = 'a' * 64
        self.sha_b = 'b' * 64
        self.obs = lambda kind, response: {'case_id':'queue-rho',
            'input_sha256':r.digest(r.canonical(self.protocol['cases'][0][kind+'_input'])),
            'response':response,'evidence_ref':'synthetic:queue'}
        self.p1 = self.phase('P1',self.sha_a,self.obs('baseline',{'ok':True,'rho':0.8}))
        self.p2 = self.phase('P2',self.sha_a,self.obs('challenge',{'ok':True,'rho':1.2}))
        self.p3 = self.phase('P3',self.sha_b,self.obs('challenge',{'ok':False,'reason':'unstable'}))
        self.files = {}
        self.save_all()

    def phase(self,phase,sha,obs):
        return {'schema':r.PHASE,'phase':phase,'system_id':'synthetic-queue',
                'artifact_sha256':sha,'capture_class':'SYNTHETIC','observations':[obs]}

    def write(self,name,obj):
        path = self.root / (name+'.json')
        path.write_text(json.dumps(obj),encoding='utf8')
        self.files[name] = str(path)
        return str(path)

    def save_all(self):
        for n,obj in [('protocol',self.protocol),('p1',self.p1),('p2',self.p2),('p3',self.p3)]:
            self.write(n,obj)
        self.write('commit',r.commit_p1(self.files['protocol'],self.files['p1']))

    def run_eval(self):
        return r.evaluate(*[self.files[x] for x in ('protocol','p1','p2','p3','commit')])

    def test_expected_recovery_but_no_admission(self):
        out = self.run_eval()
        self.assertEqual(out['passes'],{'P1':1,'P2':0,'P3':1})
        self.assertEqual(out['recovered_cases'],1)
        self.assertEqual(out['regressed_cases'],0)
        self.assertEqual(out['challenge_replay_gain'],1.0)
        self.assertEqual(out['evidence_state'],'SYNTHETIC_ONLY')
        self.assertEqual(out['admission'],'HOLD_FOR_INDEPENDENT_REVIEW')
        self.assertFalse(out['can_authorize'])

    def test_repeatable_report(self):
        self.assertEqual(r.canonical(self.run_eval()),r.canonical(self.run_eval()))

    def test_p1_tampering_detected(self):
        self.p1['observations'][0]['response']['rho'] = .9
        self.write('p1',self.p1)
        with self.assertRaisesRegex(r.InvalidEvidence,'commitment mismatch'):
            self.run_eval()

    def test_protocol_tampering_detected(self):
        self.protocol['cases'][0]['baseline_oracle']['expected'] = .9
        self.write('protocol',self.protocol)
        with self.assertRaises(r.InvalidEvidence):self.run_eval()

    def test_bad_challenge_input_hash_rejected(self):
        self.p2['observations'][0]['input_sha256'] = '0'*64
        self.write('p2',self.p2)
        with self.assertRaisesRegex(r.InvalidEvidence,'input mismatch'):self.run_eval()

    def test_p1_p2_artifact_mismatch_rejected(self):
        self.p2['artifact_sha256'] = self.sha_b
        self.write('p2',self.p2)
        with self.assertRaisesRegex(r.InvalidEvidence,'same artifact'):self.run_eval()

    def test_missing_case_rejected(self):
        self.p2['observations'] = []
        self.write('p2',self.p2)
        with self.assertRaisesRegex(r.InvalidEvidence,'one result per case'):self.run_eval()

    def test_p3_wrong_phase_rejected(self):
        self.p3['phase'] = 'P2'
        self.write('p3',self.p3)
        with self.assertRaisesRegex(r.InvalidEvidence,'wrong phase'):self.run_eval()

    def test_self_report_not_authenticated(self):
        for d in (self.p1,self.p2,self.p3): d['capture_class'] = 'SELF_REPORTED'
        self.save_all()
        self.assertEqual(self.run_eval()['evidence_state'],'UNVERIFIED_RUNTIME_OBSERVATIONS')

    def test_bogus_refusal_without_reason_fails(self):
        v,msg = r.check_response({'ok':False},{'kind':'refusal'})
        self.assertFalse(v)
        self.assertIn('reason',msg)

    def test_crash_not_refusal(self):
        self.assertFalse(r.check_response({'status':'ERROR','reason':'crash'},{'kind':'refusal'})[0])

    def test_numeric_string_no_coercion(self):
        v,_ = r.check_response({'ok':True,'rho':'0.8'},self.protocol['cases'][0]['baseline_oracle'])
        self.assertFalse(v)

    def test_nonfinite_string_fail(self):
        v,_ = r.check_response({'ok':True,'rho':0.8,'other':'NaN'},self.protocol['cases'][0]['baseline_oracle'])
        self.assertFalse(v)

    def test_contradictory_ok_and_status(self):
        self.assertFalse(r.check_response({'ok':True,'status':'REFUSED','rho':0.8},self.protocol['cases'][0]['baseline_oracle'])[0])

    def test_bool_cannot_be_numeric(self):
        self.assertFalse(r.check_response({'ok':True,'rho':True},self.protocol['cases'][0]['baseline_oracle'])[0])

    def test_exact_requires_same_type(self):
        self.assertFalse(r.check_response({'ok':True,'out':1},{'kind':'exact','path':'out','expected':True})[0])

    def test_replay_regression(self):
        self.p2['observations'][0]['response'] = {'ok':False,'reason':'unstable'}
        self.p3['observations'][0]['response'] = {'ok':True,'rho':1.2}
        self.write('p2',self.p2); self.write('p3',self.p3)
        z = self.run_eval()
        self.assertEqual(z['regressed_cases'],1)
        self.assertEqual(z['challenge_replay_gain'],-1.0)

    def test_duplicates_json_keys_refused(self):
        path = self.root/'dup.json'
        path.write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(r.InvalidEvidence,'duplicate'):r.load(path)

    def test_nonfinite_json_token_refused(self):
        path = self.root/'nonfinite.json'
        path.write_text('{"a":NaN}')
        with self.assertRaisesRegex(r.InvalidEvidence,'nonfinite'):r.load(path)

    def test_unknown_case_field_refused(self):
        self.protocol['cases'][0]['can_authorize'] = True
        self.write('protocol',self.protocol)
        with self.assertRaisesRegex(r.InvalidEvidence,'unknown fields'):r.validate_protocol(r.load(self.files['protocol'])[0])

    def test_missing_p1_commit_refused(self):
        self.files['commit'] = str(self.root/'missing-commit.json')
        with self.assertRaises(FileNotFoundError):self.run_eval()

    def test_signed_nonfinite_numeric_strings_refused(self):
        oracle=self.protocol['cases'][0]['baseline_oracle']
        for v in ['+NaN','-NaN',' +nan ', '-INF','+infinity']:
            self.assertFalse(r.check_response({'ok':True,'rho':0.8,'aux':v},oracle)[0])

    def test_large_integer_no_uncaught_exception(self):
        oracle=self.protocol['cases'][0]['baseline_oracle']
        ok, _=r.check_response({'ok':True,'rho':10**400},oracle)
        self.assertFalse(ok)
        bad=copy.deepcopy(self.protocol)
        bad['cases'][0]['baseline_oracle']['expected']=10**400
        with self.assertRaisesRegex(r.InvalidEvidence,'finite'):
            r.validate_protocol(bad)

    def test_numeric_comparison_exact_large_int_distinction(self):
        oracle={'kind':'numeric','path':'amount','expected':9007199254740993,'atol':0,'rtol':0}
        self.assertFalse(r.check_response({'ok':True,'amount':9007199254740992.0},oracle)[0])

    def test_numeric_comparison_no_overflow(self):
        oracle={'kind':'numeric','path':'amount','expected':1e308,'atol':0,'rtol':1.9}
        self.assertFalse(r.check_response({'ok':True,'amount':-1e308},oracle)[0])

    def test_cli_existing_output_preserved(self):
        out=self.root/'claimed.json'
        out.write_bytes(b'no overwrites')
        rc=r.main(['commit','--protocol',self.files['protocol'],'--p1',self.files['p1'],
                   '--output',str(out)])
        self.assertEqual(rc,2)
        self.assertEqual(out.read_bytes(),b'no overwrites')

    def test_cli_malformed_evidence_is_code_2(self):
        out=self.root/'new.json'
        bad=self.root/'malformed.json'
        bad.write_text('{"a":NaN}')
        self.assertEqual(r.main(['commit','--protocol',str(bad),'--p1',self.files['p1'],
                                 '--output',str(out)]),2)
        self.assertFalse(out.exists())

    def test_bounded_loader_rejects_large_file(self):
        p=self.root/'oversize.json'
        p.write_bytes(b' '*(r.MAX_BYTES+2))
        with self.assertRaisesRegex(r.InvalidEvidence,'1 MB'):
            r.load(p)

    def test_dangling_symlink_not_followed(self):
        out=self.root/'link'
        victim=self.root/'target'
        out.symlink_to(victim)
        self.assertEqual(r.main(['commit','--protocol',self.files['protocol'],
           '--p1',self.files['p1'],'--output',str(out)]),2)
        self.assertFalse(victim.exists())

    def test_no_shell_runtime_invocation_in_module(self):
        code = SOURCE.read_text()
        for forbidden in ['subprocess.', 'os.system(', 'eval(', 'exec(']:
            self.assertNotIn(forbidden,code)


if __name__ == '__main__':unittest.main()
