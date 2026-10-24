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

    def test_stdio_server_tools_are_three_read_only_functions(self):
        # Fake SDK only; does not pretend to prove real SDK wire compatibility.
        class FakeMCP:
            def __init__(self, name, instructions=""):
                self.names = []
            def tool(self):
                def register(func):
                    self.names.append(func.__name__)
                    return func
                return register
        sdk = types.ModuleType("mcp")
        server = types.ModuleType("mcp.server")
        server.MCPServer = FakeMCP
        with patch.dict(sys.modules, {"mcp": sdk, "mcp.server": server}):
            result = create_server(types.SimpleNamespace(status=lambda: {}, read_document=lambda *_: {}, talk=lambda *_: {}))
        self.assertEqual(result.names, ["haios_status", "haios_read_document", "haios_talk"])


if __name__ == "__main__":
    unittest.main()
