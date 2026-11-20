import asyncio
import os
import sys
import types
import unittest
from unittest.mock import patch

from haios_mcp.server import RequireLocalBearer, create_server, main


class TokenTests(unittest.TestCase):
    @staticmethod
    async def call(gate, headers=()):
        received = []
        async def capture(event):
            received.append(event)
        await gate(
            {"type": "http", "method": "POST", "path": "/mcp", "headers": list(headers)},
            lambda: None,
            capture,
        )
        return received

    def test_missing_token_returns_401_and_never_calls_inner(self):
        calls = []
        async def inner(scope, receive, send):
            calls.append(scope)
        gate = RequireLocalBearer(inner, "T" * 64)
        events = asyncio.run(self.call(gate))
        self.assertEqual(events[0]["status"], 401)
        self.assertFalse(calls)
        self.assertNotIn(b"T", events[-1]["body"])

    def test_valid_token_reaches_inner(self):
        calls = []
        async def inner(scope, receive, send):
            calls.append(scope)
        gate = RequireLocalBearer(inner, "T" * 64)
        asyncio.run(self.call(gate, [(b"authorization", b"Bearer " + b"T" * 64)]))
        self.assertEqual(len(calls), 1)

    def test_token_min_length(self):
        with self.assertRaises(ValueError):
            RequireLocalBearer(lambda *_: None, "short")

    def test_lifespan_scope_passes_through_ungated(self):
        calls = []
        async def inner(scope, receive, send):
            calls.append(scope)
        gate = RequireLocalBearer(inner, "T" * 64)
        asyncio.run(gate({"type": "lifespan"}, lambda: None, lambda _event: None))
        self.assertEqual(len(calls), 1)

    def test_non_http_non_lifespan_scope_is_refused_not_passed_through(self):
        calls = []
        async def inner(scope, receive, send):
            calls.append(scope)
        gate = RequireLocalBearer(inner, "T" * 64)
        asyncio.run(gate({"type": "websocket"}, lambda: None, lambda _event: None))
        self.assertFalse(calls)

    def test_stdio_server_tools_are_five_nonexecuting_functions(self):
        # Fake SDK only; does not pretend to prove real SDK wire compatibility.
        class FakeMCP:
            def __init__(self, name, instructions=""):
                self.names = []
                self.registered = {}
            def tool(self):
                def register(func):
                    self.names.append(func.__name__)
                    self.registered[func.__name__] = func
                    return func
                return register
        sdk = types.ModuleType("mcp")
        server = types.ModuleType("mcp.server")
        server.MCPServer = FakeMCP
        with patch.dict(sys.modules, {"mcp": sdk, "mcp.server": server}):
            result = create_server(types.SimpleNamespace(status=lambda: {}, read_document=lambda *_: {}, talk=lambda *_: {}))
        self.assertEqual(result.names, ["haios_status", "haios_read_document", "haios_self_model", "haios_find_resources", "haios_talk"])
        # Missing or false consent must fail before the model client is called.
        for supplied in ({}, {"consent": False}, {"consent": 1}):
            with self.subTest(supplied=supplied), self.assertRaisesRegex(ValueError, "Explicit consent"):
                result.registered["haios_talk"]("test request", **supplied)
        self.assertEqual(result.registered["haios_talk"]("test request", consent=True), {})


try:
    import mcp.server as _real_mcp_server
    HAVE_REAL_MCP = hasattr(_real_mcp_server, "MCPServer")
except ImportError:  # the offline suite must still run where the SDK is absent
    HAVE_REAL_MCP = False


@unittest.skipUnless(HAVE_REAL_MCP, "needs the real MCP SDK to exercise its argument validation")
class ConsentThroughTheRealSdk(unittest.TestCase):
    """The SDK validates tool arguments BEFORE the function runs. A plain `bool` is coerced leniently, so 1, "true",
    "yes" and "True" would become True and reach the provider. Calling the function directly (test above) skips that."""

    @staticmethod
    def call(**extra):
        reached = []
        bridge = types.SimpleNamespace(status=lambda: {}, read_document=lambda *_: {},
                                       talk=lambda message, session_id="": reached.append(message) or {"ok": True})
        server = create_server(bridge)
        try:
            asyncio.run(server.call_tool("haios_talk", {"message": "test request", **extra}))
        except Exception:
            pass  # a refusal is the expected outcome; what matters is whether the provider call happened
        return bool(reached)

    def test_only_a_literal_json_true_reaches_the_provider(self):
        self.assertTrue(self.call(consent=True))
        for supplied in ({}, {"consent": False}, {"consent": None}, {"consent": 1}, {"consent": 0},
                         {"consent": "true"}, {"consent": "True"}, {"consent": "yes"}, {"consent": "1"}):
            with self.subTest(supplied=supplied):
                self.assertFalse(self.call(**supplied))


if __name__ == "__main__":
    unittest.main()
