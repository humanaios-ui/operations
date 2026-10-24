import os
from pathlib import Path
import tempfile
import types
import copy
import unittest
from unittest.mock import patch

from haios_mcp.core import HumanAIOSBridge, load_document, PUBLIC_DOCUMENTS


class FakeMessageAPI:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        if self.fail:
            raise Exception("DANGEROUS PROVIDER DETAIL api-key-test")
        return types.SimpleNamespace(
            content=[types.SimpleNamespace(type="text", text="I see CURRENT.md only as supplied context.")],
            stop_reason="end_turn",
        )


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

    def test_provider_failure_does_not_echo_secrets_or_save_turn(self):
        self.api.fail = True
        with self.assertRaises(RuntimeError) as e:
            self.bridge.talk("Hello")
        self.assertNotIn("api-key-test", str(e.exception))
        self.assertFalse(self.bridge._sessions)

    def test_reject_unsafe_lengths(self):
        for message in ("", " " * 6, "x" * 4001):
            with self.assertRaises(ValueError):
                self.bridge.talk(message)
        self.assertFalse(self.api.calls)


if __name__ == "__main__":
    unittest.main()
