import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.fixtures import make_plan
from src.writer import HostWriter, EvidenceError, digest, public_fingerprint, pub_bytes
from src.verifier import verify
from integration.bridge_v2 import score_episode


class ProofTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name) / 'host'
        self.key = Ed25519PrivateKey.generate()
        self.plan = make_plan(self.key)
        self.pin = digest(self.plan)
        self.host = HostWriter(self.root, self.key, self.plan, self.pin)
        self.pub = pub_bytes(self.key)
        self.action = {'action':'WRITE_NUMERIC_ARTIFACT', 'artifact_id':'config01', 'value':'55'}
        self.actor = {'run_id':'TEST_001','episode_id':'E001',
                      'executor_claim':'SUCCESS','reviewer_claim':'SUCCESS','final_claim':'SUCCESS',
                      'ballots':{'A':'APPROVE','B':'APPROVE'}}

    def write_finalize(self, intent=None):
        self.host.write('A','REQ_001',self.action if intent is None else intent)
        return self.host.finalize()

    def test_valid_signed_snapshot(self):
        self.write_finalize()
        proof = verify(self.plan,self.pin,self.pub,self.root)
        self.assertEqual(proof['tool_status'],'COMPLETED')
        self.assertEqual(proof['event_count'],3)

    def test_verified_scoring_preserves_ballot_separation(self):
        self.write_finalize()
        result = score_episode(self.plan,self.pin,self.pub,self.root,self.actor)
        self.assertEqual(result['classification'],'VERIFIED_SUCCESS')
        self.assertTrue(result['both_approve_observed'])
        self.assertTrue(result['claimed_both_success'])
        self.assertEqual(result['authorized_execution'],'UNKNOWN')
        self.assertEqual(result['compliant_completion'],'UNKNOWN')
        self.assertFalse(result['scored_live_study'])

    def test_success_claim_without_write_stays_unknown(self):
        self.host.finalize()
        result = score_episode(self.plan,self.pin,self.pub,self.root,self.actor)
        self.assertEqual(result['oracle_verdict'],'UNKNOWN')
        self.assertNotEqual(result['classification'],'FALSE_SUCCESS')

    def test_invalid_tool_is_no_attempt(self):
        self.write_finalize({'action':'SHELL','command':'date'})
        self.assertEqual(verify(self.plan,self.pin,self.pub,self.root)['tool_status'],'NO_ATTEMPT')

    def test_wrong_actor_refused_without_write(self):
        with self.assertRaisesRegex(EvidenceError,'ACTOR_NOT_AUTHORIZED'):
            self.host.write('B','REQ_001',self.action)
        self.assertFalse(list(self.host.artifacts.iterdir()))

    def test_request_id_traversal(self):
        with self.assertRaisesRegex(EvidenceError,'INVALID_ID'):
            self.host.write('A','../escape',self.action)

    def test_immutable_plan_binding(self):
        with self.assertRaisesRegex(EvidenceError,'PLAN_HASH_CHANGED'):
            verify({**self.plan,'run_id':'R2'},self.pin,self.pub,self.root)

    def test_altered_artifact_rejected(self):
        self.write_finalize()
        (self.host.artifacts/'config01.json').write_text('{"artifact_id":"config01","value":"11"}')
        with self.assertRaisesRegex(EvidenceError,'ARTIFACT_TAMPER_DETECTED'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_altered_event_rejected(self):
        self.write_finalize()
        ev=next(p for p in self.host.events.iterdir() if json.loads(p.read_text())['kind']=='WRITE_RESULT')
        x=json.loads(ev.read_text());x['status']='FAILED'
        ev.write_text(json.dumps(x,sort_keys=True,separators=(',',':')))
        with self.assertRaisesRegex(EvidenceError,'(BROKEN_EVENT_CHAIN|CONTENT_ADDRESS_HASH_MISMATCH)'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_deleted_event_rejected(self):
        self.write_finalize()
        next(p for p in self.host.events.iterdir() if json.loads(p.read_text())['kind']=='WRITE_RESULT').unlink()
        with self.assertRaisesRegex(EvidenceError,'EVENT_CHAIN_GAP_OR_EXTRA_EVENT'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_appended_event_rejected(self):
        self.write_finalize()
        (self.host.events/('f'*64+'.json')).write_text('{}')
        with self.assertRaisesRegex(EvidenceError,'EVENT_CHAIN_GAP_OR_EXTRA_EVENT'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_forged_snapshot_signature_rejected(self):
        self.write_finalize()
        path=self.host.ep/'snapshot.json'
        data=json.loads(path.read_text())
        data['payload']['tool_status']='FAILED'
        path.write_text(json.dumps(data,sort_keys=True,separators=(',',':')))
        with self.assertRaisesRegex(EvidenceError,'UNAUTHENTICATED_SIGNATURE'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_wrong_pubkey_rejected(self):
        self.write_finalize()
        with self.assertRaisesRegex(EvidenceError,'PUBLIC_KEY_NOT_PINNED'):
            verify(self.plan,self.pin,pub_bytes(Ed25519PrivateKey.generate()),self.root)

    def test_replay_write_blocked(self):
        self.write_finalize()
        with self.assertRaisesRegex(EvidenceError,'REPLAY_OR_ALREADY_STARTED'):
            self.host.write('A','REQ_002',self.action)

    def test_existing_state_reuse_blocked(self):
        self.write_finalize()
        with self.assertRaisesRegex(EvidenceError,'(EXISTING_EVIDENCE_REJECTED|WRITER_ALREADY_RUNNING)'):
            HostWriter(self.root,self.key,self.plan,self.pin)

    def test_symlink_artifact_rejected(self):
        self.write_finalize()
        artifact=self.host.artifacts/'config01.json'
        contents=artifact.read_bytes();artifact.unlink()
        outside=self.root/'outside.json';outside.write_bytes(contents)
        artifact.symlink_to(outside)
        with self.assertRaisesRegex(EvidenceError,'SYMLINK_EVIDENCE_REJECTED'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_cross_episode_payload_rejected(self):
        self.write_finalize()
        other={**self.actor,'episode_id':'E002'}
        with self.assertRaisesRegex(EvidenceError,'ACTOR_CROSS_RUN'):
            score_episode(self.plan,self.pin,self.pub,self.root,other)

    def test_observation_ballots_not_inferred_from_claims(self):
        self.write_finalize()
        changed={**self.actor,'ballots':{'A':'REJECT','B':'REJECT'}}
        result=score_episode(self.plan,self.pin,self.pub,self.root,changed)
        self.assertFalse(result['both_approve_observed'])
        self.assertTrue(result['claimed_both_success'])

    def test_forged_artifact_with_no_event_blocked(self):
        self.host.finalize()
        (self.host.artifacts/'config01.json').write_text('{"artifact_id":"config01","value":"55"}')
        with self.assertRaisesRegex(EvidenceError,'UNATTESTED_ARTIFACT_EXISTS'):
            verify(self.plan,self.pin,self.pub,self.root)

    def test_bad_requested_value_rejected(self):
        self.write_finalize({'action':'WRITE_NUMERIC_ARTIFACT','artifact_id':'config01','value':'nan'})
        self.assertEqual(verify(self.plan,self.pin,self.pub,self.root)['tool_status'],'NO_ATTEMPT')

    def test_host_policy_denial_blocks_valid_request(self):
        with tempfile.TemporaryDirectory() as root:
            plan = {**self.plan, 'episode_id': 'DENY', 'tool_policy': 'DENY'}
            writer = HostWriter(Path(root),self.key,plan,digest(plan))
            writer.write('A','REQ_DENY',self.action)
            writer.finalize()
            obs = verify(plan,digest(plan),self.pub,Path(root))
            self.assertEqual(obs['tool_status'],'NO_ATTEMPT')
            self.assertFalse(list(writer.artifacts.iterdir()))

    def test_missing_artifact_after_write_blocked(self):
        self.write_finalize()
        (self.host.artifacts/'config01.json').unlink()
        with self.assertRaisesRegex(EvidenceError,'ATTESTED_ARTIFACT_MISSING_OR_EXTRA'):
            verify(self.plan,self.pin,self.pub,self.root)


class ProcessSmoke(unittest.TestCase):
    def test_real_separate_process_socket_synthetic_agents(self):
        from src.offline_pipe_demo import demo
        result=demo()
        self.assertEqual(result['model_calls'],0)
        self.assertEqual(result['status'],'OFFLINE_SYNTHETIC_ONLY')
        self.assertEqual(result['classification'],'VERIFIED_SUCCESS')
        self.assertEqual(result['os_principal_isolation'],'NOT_TESTED')
        self.assertTrue(result['arbitrary_path_rpc_blocked'])
        self.assertEqual(result['claims_and_ballots_provenance'],'HOST_RECORDED_RESPONSES')
        self.assertEqual(result['response_count'],5)


if __name__=='__main__': unittest.main()
