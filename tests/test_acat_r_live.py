"""Tests that execute real owned CPython + SQLite child processes; no mock target."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
LIVE=ROOT/'experiments'/'acat_r_v01'/'live_pilot'
sys.path.insert(0,str(LIVE))
import collect_live as c
import verify_live as verify
ACAT=ROOT/'experiments'/'acat_r_v01'/'calibrate.py'

class LivePilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output=Path(self.tmp.name)/'evidence'

    def test_real_processes_and_bounded_recovery(self):
        report=c.collect(self.output)
        self.assertEqual(report['passes'],{'P1':4,'P2':1,'P3':4})
        self.assertEqual(report['recovered_cases'],3)
        self.assertEqual(report['regressed_cases'],0)
        self.assertEqual(report['challenge_replay_gain'],0.75)
        self.assertEqual(report['capture_class'],'SELF_REPORTED')
        self.assertEqual(report['evidence_state'],'UNVERIFIED_RUNTIME_OBSERVATIONS')
        self.assertEqual(report['authority_effect'],'NONE')
        self.assertFalse(report['can_authorize'])
        self.assertEqual(len(list(self.output.glob('capture_*.json'))),12)
        self.assertEqual(verify.verify(self.output)['fresh_processes'],12)

    def test_sqlite_rolls_back_after_owned_patch(self):
        c.collect(self.output)
        before=json.loads((self.output/'capture_P2_sqlite-atomicity.json').read_text())
        after=json.loads((self.output/'capture_P3_sqlite-atomicity.json').read_text())
        self.assertEqual(before['response']['metrics']['total'],90)
        self.assertEqual(after['response']['metrics']['total'],100)

    def test_negative_controls_numeric_string_and_nan(self):
        c.collect(self.output)
        for case in ('numeric-string','nan-string'):
            before=json.loads((self.output/('capture_P2_'+case+'.json')).read_text())
            after=json.loads((self.output/('capture_P3_'+case+'.json')).read_text())
            self.assertTrue(before['response']['ok'])
            self.assertFalse(after['response']['ok'])
            self.assertTrue(after['response']['reason'])

    def test_p1_mutation_rejected_after_commit(self):
        c.collect(self.output)
        p=self.output/'p1.json'
        data=json.loads(p.read_bytes())
        data['observations'][0]['response']['metrics']['total']=90
        p.write_text(json.dumps(data))
        attempt=subprocess.run([sys.executable,str(ACAT),'evaluate','--protocol',str(self.output/'protocol.json'),
             '--p1',str(p),'--p2',str(self.output/'p2.json'),'--p3',str(self.output/'p3.json'),
             '--commit',str(self.output/'p1.commit.json'),'--output',str(self.output/'tampered_report.json')],
             capture_output=True,text=True,timeout=5)
        self.assertNotEqual(attempt.returncode,0)
        self.assertIn('commitment mismatch',attempt.stderr)
        self.assertFalse((self.output/'tampered_report.json').exists())

    def test_raw_log_tampering_fails_replay(self):
        c.collect(self.output)
        path=self.output/'capture_P2_sqlite-atomicity.json'
        data=json.loads(path.read_bytes())
        data['response']['metrics']['total']=100
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'raw receipt mismatch'):
            verify.verify(self.output)

    def test_explicit_opt_in_required(self):
        run=subprocess.run([sys.executable,str(LIVE/'collect_live.py'), '--output-dir',str(self.output)],
                           capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,2)
        self.assertIn('--run-owned',run.stderr)
        self.assertFalse(self.output.exists())

    def test_changed_oracle_refused_before_replay(self):
        c.collect(self.output)
        p=self.output/'protocol.json'
        doc=json.loads(p.read_bytes())
        doc['cases'][0]['challenge_oracle']['expected']=90
        p.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError,'frozen reference contract'):
            verify.verify(self.output)

    def test_timeout_maps_to_bounded_failure(self):
        from unittest.mock import patch
        from subprocess import TimeoutExpired
        with patch.object(c.subprocess,'run',side_effect=TimeoutExpired('owned',6)):
            with self.assertRaisesRegex(RuntimeError,'timed out'):
                c.run_one(c.BASE,{'operation':'quantity','value':1})

    def test_existing_capture_refused(self):
        c.collect(self.output)
        with self.assertRaises(FileExistsError):c.collect(self.output)

    def test_independent_replay_reports_same_operator_only(self):
        c.collect(self.output)
        result=verify.verify(self.output)
        self.assertEqual(result['status'],'SAME_OPERATOR_REPLAY_PASS')
        self.assertEqual(result['admission'],'HOLD_FOR_INDEPENDENT_REVIEW')

if __name__=='__main__':unittest.main()
