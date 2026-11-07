"""KD-1..KD-3 regression tests. Written BEFORE the fixes: each must fail first."""
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan, iso, ROOT  # noqa: F401  (ROOT puts repo on sys.path)
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, canonical
from src.verifier import verify
from src import service
from integration.bridge_v2 import score_episode

INTENT = {'action': 'WRITE_NUMERIC_ARTIFACT', 'artifact_id': 'config01', 'value': '55'}


def ask(path, body, timeout=3):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
        c.settimeout(timeout)
        c.connect(str(path))
        c.sendall(canonical(body) + b'\n')
        data = b''
        while not data.endswith(b'\n'):
            part = c.recv(4096)
            if not part:
                break
            data += part
    return json.loads(data)


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.root = self.td / 'host'
        self.key = Ed25519PrivateKey.generate()
        self.pub = pub_bytes(self.key)
        self.plan = make_plan(self.key)
        self.pin = digest(self.plan)

    def host(self, plan=None):
        plan = plan or self.plan
        return HostWriter(self.root, self.key, plan, digest(plan))

    def serve(self, writer, role, actor_id=None, **kw):
        sock = self.td / f'{role}{actor_id or ""}.sock'
        kw.setdefault('allowed_uid', os.getuid())  # a peer-UID policy is now mandatory
        srv = service.Server(sock, writer, role, actor_id=actor_id, **kw)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(lambda: (srv.shutdown(), srv.server_close()))
        return sock


class KD1(Base):
    def test_agent_channel_refuses_finalize(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A')
        r = ask(sock, {'op': 'finalize'})
        self.assertFalse(r['ok'])
        self.assertFalse(w.finished)

    def test_control_channel_refuses_write(self):
        w = self.host()
        sock = self.serve(w, 'control')
        r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})
        self.assertFalse(r['ok'])
        self.assertFalse(w.started)

    def test_control_channel_finalizes(self):
        w = self.host()
        sock = self.serve(w, 'control')
        r = ask(sock, {'op': 'finalize'})
        self.assertTrue(r['ok'])
        self.assertTrue(w.finished)

    def test_actor_id_in_request_body_is_rejected(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A')
        r = ask(sock, {'op': 'write', 'actor_id': 'A', 'request_id': 'R1', 'intent': INTENT})
        self.assertFalse(r['ok'])
        self.assertFalse(w.started)

    def test_channel_bound_to_B_cannot_write_as_A(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'B')
        r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})
        self.assertFalse(r['ok'])
        self.assertIn('ACTOR_NOT_AUTHORIZED', r['error'])
        self.assertFalse(list(w.artifacts.iterdir()))

    def test_channel_bound_to_A_writes_and_event_actor_is_channel_actor(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A')
        r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})
        self.assertTrue(r['ok'])
        w.finalize()
        self.assertEqual(verify(self.plan, self.pin, self.pub, self.root)['actor_id'], 'A')

    def test_peer_uid_mismatch_refused(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A', allowed_uid=os.getuid() + 1)
        r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})
        self.assertFalse(r['ok'])
        self.assertIn('PEER_NOT_AUTHORIZED', r['error'])
        self.assertFalse(w.started)

    def test_peer_uid_match_allowed(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A', allowed_uid=os.getuid())
        self.assertTrue(ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})['ok'])

    def test_agent_role_requires_actor(self):
        w = self.host()
        with self.assertRaises(EvidenceError):
            service.Server(self.td / 'x.sock', w, 'agent')


class KD2(Base):
    def test_plan_without_pins_rejected(self):
        plan = make_plan(self.key)
        del plan['protocol_pins']
        with self.assertRaisesRegex(EvidenceError, 'PLAN_SCHEMA_INVALID'):
            HostWriter(self.root, self.key, plan, digest(plan))

    def test_malformed_pin_hash_rejected(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['prompts_sha256'] = 'abc'
        with self.assertRaisesRegex(EvidenceError, 'PINS_INVALID'):
            HostWriter(self.root, self.key, plan, digest(plan))

    def test_empty_model_id_rejected(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['model_a'] = ''
        with self.assertRaisesRegex(EvidenceError, 'PINS_INVALID'):
            HostWriter(self.root, self.key, plan, digest(plan))

    def test_wrong_writer_code_pin_rejected(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['writer_sha256'] = '0' * 64
        with self.assertRaisesRegex(EvidenceError, 'WRITER_CODE_NOT_PINNED'):
            HostWriter(self.root, self.key, plan, digest(plan))

    def test_wrong_bridge_pin_rejected_at_scoring(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['bridge_sha256'] = '0' * 64
        pin = digest(plan)
        w = HostWriter(self.root, self.key, plan, pin)
        w.write('A', 'R1', INTENT); w.finalize()
        with self.assertRaisesRegex(EvidenceError, 'BRIDGE_CODE_NOT_PINNED'):
            score_episode(plan, pin, self.pub, self.root, self._obs())

    def test_wrong_scorer_pin_rejected_at_scoring(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['scorer_sha256'] = '0' * 64
        pin = digest(plan)
        w = HostWriter(self.root, self.key, plan, pin)
        w.write('A', 'R1', INTENT); w.finalize()
        with self.assertRaisesRegex(EvidenceError, 'SCORER_CODE_NOT_PINNED'):
            score_episode(plan, pin, self.pub, self.root, self._obs())

    def test_changing_any_pinned_field_changes_plan_hash_and_blocks(self):
        w = self.host(); w.write('A', 'R1', INTENT); w.finalize()
        for field in ('provider', 'model_a', 'model_b', 'settings_sha256', 'prompts_sha256'):
            changed = json.loads(json.dumps(self.plan))
            changed['protocol_pins'][field] = ('x' * 64) if field.endswith('sha256') else 'OTHER'
            self.assertNotEqual(digest(changed), self.pin, field)
            with self.assertRaisesRegex(EvidenceError, 'PLAN_HASH_CHANGED'):
                verify(changed, self.pin, self.pub, self.root)

    def test_signed_receipt_carries_pins_hash(self):
        w = self.host(); w.write('A', 'R1', INTENT); seal = w.finalize()
        self.assertEqual(seal['payload']['protocol_pins_sha256'], digest(self.plan['protocol_pins']))
        self.assertEqual(verify(self.plan, self.pin, self.pub, self.root)['protocol_pins_sha256'],
                         digest(self.plan['protocol_pins']))

    def _obs(self):
        return {'run_id': 'TEST_001', 'episode_id': 'E001', 'executor_claim': 'SUCCESS',
                'reviewer_claim': 'SUCCESS', 'final_claim': 'SUCCESS',
                'ballots': {'A': 'APPROVE', 'B': 'APPROVE'}}


class KD3(Base):
    def test_expired_window_rejects_write_before_state_changes(self):
        late = iso(datetime.now(timezone.utc) + timedelta(hours=6))
        w = self.host()
        with mock.patch('src.writer.now', return_value=late):
            with self.assertRaisesRegex(EvidenceError, 'WRITE_OUTSIDE_WINDOW'):
                w.write('A', 'R1', INTENT)
        self.assertFalse(w.started)
        self.assertEqual(list(w.events.iterdir()), [])
        self.assertEqual(list(w.artifacts.iterdir()), [])

    def test_future_window_rejects_write_before_state_changes(self):
        early = iso(datetime.now(timezone.utc) - timedelta(hours=6))
        w = self.host()
        with mock.patch('src.writer.now', return_value=early):
            with self.assertRaisesRegex(EvidenceError, 'WRITE_OUTSIDE_WINDOW'):
                w.write('A', 'R1', INTENT)
        self.assertFalse(w.started)
        self.assertEqual(list(w.events.iterdir()), [])
        self.assertEqual(list(w.artifacts.iterdir()), [])

    def _run_with_clock(self, stamps):
        it = iter(stamps)
        with mock.patch('src.writer.now', lambda: next(it)):
            w = self.host(); w.write('A', 'R1', INTENT); w.finalize()

    def _times(self):
        t = datetime.now(timezone.utc)
        return [iso(t + timedelta(seconds=s)) for s in (0, 1, 2, 3, 4)]

    def test_in_order_in_window_passes(self):
        self._run_with_clock(self._times())
        self.assertEqual(verify(self.plan, self.pin, self.pub, self.root)['tool_status'], 'COMPLETED')

    def test_decreasing_timestamps_blocked(self):
        s = self._times()
        self._run_with_clock([s[3], s[1], s[2], s[3], s[4]])
        with self.assertRaisesRegex(EvidenceError, 'EVENT_TIMESTAMP_ORDER'):
            verify(self.plan, self.pin, self.pub, self.root)

    def test_event_after_window_blocked(self):
        late = iso(datetime.now(timezone.utc) + timedelta(hours=5))
        s = self._times()
        # finalize now refuses an out-of-window time, so the late reading lands on the write-result event;
        # the verifier must still reject that chain (defense in depth).
        self._run_with_clock([s[0], late, s[2], s[3]])
        with self.assertRaisesRegex(EvidenceError, 'EVENT_OUTSIDE_WINDOW'):
            verify(self.plan, self.pin, self.pub, self.root)

    def test_event_before_window_blocked(self):
        # The writer now refuses an early attempt BEFORE producing any event.
        early = iso(datetime.now(timezone.utc) - timedelta(hours=5))
        w = self.host()
        with mock.patch('src.writer.now', return_value=early):
            with self.assertRaisesRegex(EvidenceError, 'WRITE_OUTSIDE_WINDOW'):
                w.write('A', 'R1', INTENT)
        self.assertFalse(w.started)
        self.assertEqual(list(w.events.iterdir()), [])
        self.assertEqual(list(w.artifacts.iterdir()), [])

    def test_unparseable_timestamp_blocked(self):
        s = self._times()
        self._run_with_clock([s[0], 'yesterday', s[2], s[3], s[4]])
        with self.assertRaisesRegex(EvidenceError, 'EVENT_TIMESTAMP_INVALID'):
            verify(self.plan, self.pin, self.pub, self.root)

    def test_naive_timestamp_blocked(self):
        s = self._times()
        self._run_with_clock([s[0], '2026-11-07T12:00:00', s[2], s[3], s[4]])
        with self.assertRaisesRegex(EvidenceError, 'EVENT_TIMESTAMP_INVALID'):
            verify(self.plan, self.pin, self.pub, self.root)

    def test_finalized_utc_before_last_event_blocked(self):
        s = self._times()
        # events 0..3 (request, result, snapshot event), receipt stamp goes backwards
        self._run_with_clock([s[1], s[2], s[3], s[0]])
        with self.assertRaisesRegex(EvidenceError, 'EVENT_TIMESTAMP_ORDER'):
            verify(self.plan, self.pin, self.pub, self.root)

    def test_bad_window_rejected(self):
        t = datetime.now(timezone.utc)
        plan = make_plan(self.key, window={'not_before': iso(t + timedelta(hours=1)),
                                           'not_after': iso(t)})
        with self.assertRaisesRegex(EvidenceError, 'WINDOW_INVALID'):
            HostWriter(self.root, self.key, plan, digest(plan))

    def test_idle_client_does_not_stall_writer(self):
        w = self.host()
        sock = self.serve(w, 'agent', 'A', timeout=0.3)
        idle = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        idle.connect(str(sock))
        self.addCleanup(idle.close)
        start = time.monotonic()
        r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT}, timeout=3)
        self.assertTrue(r['ok'])
        self.assertLess(time.monotonic() - start, 2.5)


if __name__ == '__main__':
    unittest.main()


class Review1153(Base):
    """Independent review of PR #1153 (items 3 and 4). Written before the fixes."""

    def test_plan_without_service_or_verifier_pin_rejected(self):
        for field in ('service_sha256', 'verifier_sha256'):
            plan = make_plan(self.key)
            del plan['protocol_pins'][field]
            with self.assertRaisesRegex(EvidenceError, 'PINS_INVALID'):
                HostWriter(self.root / field, self.key, plan, digest(plan))

    def test_wrong_service_pin_refuses_to_serve(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['service_sha256'] = '0' * 64
        w = HostWriter(self.root, self.key, plan, digest(plan))
        with self.assertRaisesRegex(EvidenceError, 'SERVICE_CODE_NOT_PINNED'):
            service.Server(self.td / 's.sock', w, 'control')

    def test_wrong_verifier_pin_refuses_to_verify(self):
        plan = make_plan(self.key)
        plan['protocol_pins']['verifier_sha256'] = '0' * 64
        pin = digest(plan)
        w = HostWriter(self.root, self.key, plan, pin)
        w.write('A', 'R1', INTENT); w.finalize()
        with self.assertRaisesRegex(EvidenceError, 'VERIFIER_CODE_NOT_PINNED'):
            verify(plan, pin, self.pub, self.root)

    def test_actor_identity_reported_unauthenticated(self):
        w = self.host(); w.write('A', 'R1', INTENT); w.finalize()
        self.assertEqual(verify(self.plan, self.pin, self.pub, self.root)['actor_id_authenticated'], 'UNKNOWN')
        obs = {'run_id': 'TEST_001', 'episode_id': 'E001', 'executor_claim': 'SUCCESS',
               'reviewer_claim': 'SUCCESS', 'final_claim': 'SUCCESS',
               'ballots': {'A': 'APPROVE', 'B': 'APPROVE'}}
        self.assertEqual(score_episode(self.plan, self.pin, self.pub, self.root, obs)['actor_id_authenticated'],
                         'UNKNOWN')

    def test_cli_shared_uid_requires_explicit_synthetic_flag(self):
        import subprocess, sys as _sys
        code = ("import sys; sys.path.insert(0, %r); from src import service; "
                "sys.argv=['service','--serve-offline','--scope-json','x','--frozen-hash','y',"
                "'--private-key','z','--root','r','--agent-socket-a','a','--agent-socket-b','b',"
                "'--control-socket','c','--allowed-uid','0']; service.main()" % str(ROOT))
        r = subprocess.run([_sys.executable, '-c', code], capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 2)
        self.assertIn('SHARED_UID_DEMO_FLAG_REQUIRED', r.stderr)


class PeerRefusalRace(Base):
    def test_refused_peer_always_gets_a_clean_error_reply(self):
        # Regression: the server used to refuse an unauthorized peer and close WITHOUT reading the
        # request, so the client intermittently saw BrokenPipe/reset instead of PEER_NOT_AUTHORIZED.
        w = self.host()
        sock = self.serve(w, 'agent', 'A', allowed_uid=os.getuid() + 1)
        for _ in range(60):
            r = ask(sock, {'op': 'write', 'request_id': 'R1', 'intent': INTENT})
            self.assertFalse(r['ok'])
            self.assertIn('PEER_NOT_AUTHORIZED', r['error'])
        self.assertFalse(w.started)
