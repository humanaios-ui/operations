import copy
import http.client
import json
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from app import Handler
from resource_miner.job_application import prepare, HELD


def case():
    return dict(application_id='synthetic-01', employer='Example', role='Coordinator',
                job_text='Coordinate a project.', job_source='Synthetic pasted description',
                evidence=[dict(id='E1', claim='Coordinated a study', source='Synthetic fixture', state='USER_ATTESTED')],
                requirements=[dict(id='R1', requirement='Project coordination', kind='duty', status='SUPPORTED', mapping='TRANSFERABLE', evidence_ids=['E1'], proposed_execution='Track milestones')])


class BridgeTests(unittest.TestCase):
    def test_preserves_source_and_does_not_mutate(self):
        record=case(); before=copy.deepcopy(record); result=prepare(record)
        self.assertEqual(record,before)
        self.assertEqual(result['application']['job_text'],record['job_text'])
        self.assertEqual(result['application']['availability'],'UNVERIFIED')
        self.assertIn('$map-job-application',result['skill_handoff'])
        self.assertIn('cover letter',result['skill_handoff'])
        self.assertIn('Word and PDF',result['skill_handoff'])

    def test_holds_remain_holds_and_cannot_submit(self):
        for status in HELD:
            record=case();record.update(source_verification_status=status,external_state='SUBMITTED',authority='APPROVED')
            app=prepare(record)['application']
            self.assertTrue(app['source_hold'])
            self.assertEqual(app['external_state'],'NOT_SUBMITTED')
            self.assertEqual(app['authority'],'NONE')

    def test_catalog_hold_cannot_be_cleared_by_import(self):
        record=case()
        app=prepare(record,[dict(url=record['job_source'],source_verification_status='ROLE_NOT_LISTED')])['application']
        self.assertTrue(app['source_hold'])
        self.assertEqual(app['source_verification_status'],'ROLE_NOT_LISTED')

    def test_no_fake_positive_verification(self):
        record=case();record['source_verification_status']='VERIFIED_OPEN'
        with self.assertRaises(ValueError):prepare(record)

    def test_missing_proof_stays_gap(self):
        record=case();row=record['requirements'][0];row.update(status='UNKNOWN',mapping='GAP',evidence_ids=[])
        self.assertIn('Not established',prepare(record)['evidence_map_html'])
        row.update(status='SUPPORTED')
        with self.assertRaises(ValueError):prepare(record)

    def test_broken_reference_and_duplicate_rejected(self):
        record=case();record['requirements'][0]['evidence_ids']=['missing']
        with self.assertRaises(ValueError):prepare(record)
        record=case();record['evidence'].append(copy.deepcopy(record['evidence'][0]))
        with self.assertRaises(ValueError):prepare(record)

    def test_html_escaped(self):
        record=case();record['employer']='<script>bad()</script>'
        self.assertNotIn('<script>',prepare(record)['evidence_map_html'])


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection(*self.server.server_address)
        conn.request(method,path,body,headers or {})
        response=conn.getresponse();result=(response.status,response.read());conn.close();return result
    def test_page_and_private_prepare(self):
        self.assertEqual(self.request('GET','/my-applications')[0],200)
        code,body=self.request('POST','/api/my-applications/prepare',json.dumps(case()),{'Content-Type':'application/json'})
        self.assertEqual(code,200);self.assertIn(b'NOT_SUBMITTED',body)
    def test_public_bind_and_foreign_origin_blocked(self):
        with patch.object(self.server,'server_address',('0.0.0.0',self.server.server_address[1])):
            self.assertFalse(self.server.server_address[0]=='127.0.0.1')
            # Keep connection address local while checking the guard separately.
            handler=object.__new__(Handler);handler.server=self.server;handler.client_address=('127.0.0.1',1);handler.headers={'Host':'localhost:1'}
            self.assertFalse(handler._local_opportunities_allowed())
        headers={'Content-Type':'application/json','Origin':'https://foreign.example'}
        self.assertEqual(self.request('POST','/api/my-applications/prepare',json.dumps(case()),headers)[0],404)
        self.assertEqual(self.request('GET','/my-applications',headers={'Host':'foreign.example'})[0],404)
    def test_bad_payload_does_not_echo_private_data(self):
        code,body=self.request('POST','/api/my-applications/prepare','{"secret":"PRIVATE-CANARY"}',{'Content-Type':'application/json'})
        self.assertEqual(code,400);self.assertNotIn(b'PRIVATE-CANARY',body)
