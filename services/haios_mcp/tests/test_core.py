import os
from pathlib import Path
import tempfile
import types
import copy
import unittest
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from haios_mcp.core import HumanAIOSBridge, load_document, PUBLIC_DOCUMENTS


class FakeStream:
    def __init__(self, owner):
        self.owner = owner
        self.text_stream = self.texts()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def texts(self):
        if self.owner.fail:
            raise Exception("DANGEROUS PROVIDER DETAIL api-key-test")
        yield "I see CURRENT.md "
        yield "only as supplied context."

    def get_final_message(self):
        return types.SimpleNamespace(stop_reason="end_turn")


class FakeMessageAPI:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def stream(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return FakeStream(self)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Valid operations checkout can lack START_HERE.md.
        (self.root / "CURRENT.md").write_text("C" * 6100, encoding="utf-8")
        (self.root / "REGISTERED.md").write_text("PUBLIC REGISTRY", encoding="utf-8")
        (self.root / "GOVERNANCE.md").write_text("no automatic approvals", encoding="utf-8")
        (self.root / "PRIVATE.md").write_text("secret", encoding="utf-8")
        self.api = FakeMessageAPI()
        self.bridge = HumanAIOSBridge(self.root, client_factory=lambda: types.SimpleNamespace(messages=self.api))

    def test_root_identity_requires_both_canonical_files(self):
        self.assertIsNotNone(self.bridge.root)
        (self.root / "REGISTERED.md").unlink()
        with self.assertRaisesRegex(ValueError, "REGISTERED.md"):
            HumanAIOSBridge(self.root)

    def test_start_here_is_optional_context_and_explicit_read_fails_closed(self):
        self.assertFalse((self.root / "START_HERE.md").exists())
        self.assertFalse(next(x for x in self.bridge.status()["documents"] if x["filename"] == "START_HERE.md")["available"])
        with self.assertRaises(ValueError):
            self.bridge.read_document("START_HERE.md")
        self.assertEqual(len(self.bridge.talk("Hello")["source_manifest"]), 3)

    def test_status_no_provider_call_and_allowlisted(self):
        info = self.bridge.status()
        self.assertEqual(info["authority"], "NONE")
        self.assertFalse(info["filesystem_write"])
        self.assertFalse(info["shell_execution"])
        self.assertEqual(self.api.calls, [])
        self.assertEqual(len(info["documents"]), len(PUBLIC_DOCUMENTS))
        self.assertNotIn("PRIVATE.md", str(info))

    def test_file_read_has_full_hash_and_truncation(self):
        result = self.bridge.read_document("CURRENT.md", 20)
        self.assertEqual(result["content"], "C" * 20)
        self.assertEqual(result["total_characters"], 6100)
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["sha256"]), 64)

    def test_reject_private_and_traversal(self):
        for name in ("PRIVATE.md", "../PRIVATE.md", "/etc/passwd", "START_HERE.md/../PRIVATE.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                load_document(self.root, name)

    def test_reject_symlink_even_to_allowlisted_filename(self):
        (self.root / "SEED.md").symlink_to(self.root / "PRIVATE.md")
        with self.assertRaises(ValueError):
            self.bridge.read_document("SEED.md")

    def test_reject_oversized(self):
        (self.root / "SEED.md").write_bytes(b"A" * 2_000_001)
        with self.assertRaises(ValueError):
            self.bridge.read_document("SEED.md")

    def test_new_and_followup_session(self):
        first = self.bridge.talk("Hello")
        second = self.bridge.talk("What did I ask?", first["session_id"])
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertEqual(len(self.api.calls), 2)
        self.assertEqual(len(first["answer_sha256"]), 64)
        self.assertEqual(first["receipt_kind"], "UNSIGNED_MODEL_RESPONSE_DIGEST_NOT_ATTESTATION")
        self.assertEqual(len(self.api.calls[1]["messages"]), 3)
        self.assertEqual(self.api.calls[1]["messages"][0]["content"], "Hello")
        manifest = first["source_manifest"]
        self.assertEqual([v["filename"] for v in manifest], ["CURRENT.md", "REGISTERED.md", "GOVERNANCE.md"])
        self.assertTrue(manifest[0]["truncated"])
        self.assertIn('truncated=true', self.api.calls[0]["system"])
        self.assertNotIn("PRIVATE.md", self.api.calls[0]["system"])

    def test_unauthorized_session_fails_without_provider_call(self):
        with self.assertRaisesRegex(ValueError, "Unknown or expired"):
            self.bridge.talk("Hello", "attacker")
        self.assertFalse(self.api.calls)

    def test_expired_session(self):
        instant = [100]
        bridge = HumanAIOSBridge(self.root, client_factory=lambda: types.SimpleNamespace(messages=self.api), clock=lambda: instant[0])
        sid = bridge.talk("Hello")["session_id"]
        instant[0] += 1801
        with self.assertRaisesRegex(ValueError, "Unknown or expired"):
            bridge.talk("Remember me?", sid)

    def test_sessions_are_bounded_and_opaque(self):
        ids = {self.bridge.talk("hi")["session_id"] for _ in range(12)}
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(self.bridge._sessions), 8)

    def test_failed_new_request_does_not_evict_full_session_pool(self):
        ids = [self.bridge.talk("hi")["session_id"] for _ in range(8)]
        self.api.fail = True
        with self.assertRaises(RuntimeError):
            self.bridge.talk("provider fails")
        self.assertEqual(set(ids), set(self.bridge._sessions))

    def test_provider_failure_does_not_echo_secrets_or_save_turn(self):
        self.api.fail = True
        with self.assertLogs("haios_mcp", level="WARNING") as logged:
            with self.assertRaises(RuntimeError) as e:
                self.bridge.talk("Hello")
        self.assertIn("class=Exception", "\n".join(logged.output))
        self.assertNotIn("DANGEROUS PROVIDER DETAIL", "\n".join(logged.output))
        self.assertNotIn("api-key-test", "\n".join(logged.output))
        self.assertNotIn("api-key-test", str(e.exception))
        self.assertFalse(self.bridge._sessions)

    def test_reject_unsafe_lengths(self):
        for message in ("", " " * 6, "x" * 4001):
            with self.assertRaises(ValueError):
                self.bridge.talk(message)
        self.assertFalse(self.api.calls)

    def test_self_model_uses_metaphor_not_consciousness_or_execution_claims(self):
        model = self.bridge.self_model()
        self.assertEqual(model["subjective_awareness"], "NOT_ESTABLISHED")
        self.assertEqual(model["authority"], "NONE")
        self.assertFalse(model["observations"]["filesystem_write"])
        self.assertIn("haios_find_resources", model["known_tools"])

    def test_stream_overflow_discards_partial_answer(self):
        class Huge(FakeStream):
            def texts(self):
                yield "A" * 12001
        self.api.stream = lambda **kwargs: Huge(self.api)
        with self.assertRaisesRegex(RuntimeError, "streaming request failed"):
            self.bridge.talk("hi")
        self.assertFalse(self.bridge._sessions)

    def test_resource_miner_disabled_without_explicit_operator_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            result = self.bridge.find_resources("compute credits for AI research")
        self.assertEqual(result["status"], "NOT_CONFIGURED")

    def test_resource_miner_disallows_remote_targets_and_invalid_intent(self):
        for origin in ("https://example.com", "http://evil.com:8766", "http://localhost:8766", "http://127.0.0.1:8766/private", "http://127.0.0.1:8766@evil.com", "http://127.0.0.1:80"):
            with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN": origin}):
                with self.subTest(origin=origin), self.assertRaises(ValueError):
                    self.bridge.find_resources("compute credits")
        with self.assertRaises(ValueError):
            self.bridge.find_resources("private\nsecret")

    def test_resource_miner_local_loopback_public_snapshot(self):
        captured = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                content = self.rfile.read(int(self.headers["Content-Length"]))
                captured.append((self.path, json.loads(content)))
                body = json.dumps({
                    "authority": "NONE", "source_mode": "snapshot", "source_status": "STORED_SNAPSHOT",
                    "status": "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW", "source_warning": "Two records unexamined",
                    "execution": "DISABLED", "eligibility": "NOT_ASSESSED",
                    "matched_count": 1, "shown_count": 1, "unexamined_count": 2,
                    "receipt_sha256": "a" * 64,
                    "candidates": [{"resource_id": "id1", "title": "Compute Credits", "source_name": "DEV Community",
                                    "source_url": "https://example.com/resource", "route": "WATCH",
                                    "applicant_private_data": "DO_NOT_LEAK", "eligibility_assessed": False}]
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN": f"http://127.0.0.1:{server.server_port}"}):
            result = self.bridge.find_resources("compute credits")
        self.assertEqual(captured, [("/api/intent", {"objective": "compute credits", "source_mode": "snapshot"})])
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["candidates"][0]["title"], "Compute Credits")
        self.assertNotIn("DO_NOT_LEAK", str(result))
        self.assertEqual(result["status"], "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW")
        self.assertEqual(result["unexamined_count"], 2)
        self.assertEqual(result["source_warning"], "Two records unexamined")
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["source_mode"], "snapshot")
        self.assertEqual(result["receipt_sha256"], "a" * 64)

    def test_partial_status_cannot_be_silently_laundered(self):
        from unittest.mock import patch
        # A malformed unqualified status with nonzero unexamined_count
        # must fail rather than misrepresent the search as complete.
        import io
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.dumps({
                    "authority": "NONE", "execution": "DISABLED", "eligibility": "NOT_ASSESSED",
                    "source_mode": "snapshot", "status": "NO_SUPPORTED_MATCH",
                    "source_status": "CURATED_SNAPSHOT_NOT_LIVE", "source_warning": "incomplete",
                    "matched_count": 0, "shown_count": 0, "unexamined_count": 2,
                    "receipt_sha256": "b" * 64, "candidates": [],
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_): pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN": f"http://127.0.0.1:{server.server_port}"}):
                with self.assertRaisesRegex(RuntimeError, "partial-search"):
                    self.bridge.find_resources("compute credits")
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_unassessed_public_candidate_refuses_claimed_eligibility(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.dumps({
                    "authority": "NONE", "execution": "DISABLED", "eligibility": "NOT_ASSESSED",
                    "source_mode": "snapshot", "status": "CANDIDATES_FOR_HUMAN_REVIEW",
                    "source_status": "STORED", "matched_count": 1,
                    "shown_count": 1, "unexamined_count": 0, "receipt_sha256": "c" * 64,
                    "candidates": [{"resource_id":"id", "title":"grant", "source_name":"DEV Community",
                        "source_url":"https://example.com/grant", "route":"WATCH", "eligibility_assessed":True}]
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *_): pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"HAIOS_RESOURCE_MINER_ORIGIN": f"http://127.0.0.1:{server.server_port}"}):
                with self.assertRaisesRegex(RuntimeError, "eligibility"):
                    self.bridge.find_resources("compute credits")
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()