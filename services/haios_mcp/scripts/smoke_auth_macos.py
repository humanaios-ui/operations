#!/usr/bin/env python3
"""Isolated, non-mutating v0.2 MCP HTTP authentication smoke test on macOS.

Run with the existing v0.1.1 virtualenv's Python. This starts the candidate
package on a random loopback port in a child process, then shuts it down.
It does not touch the installed launchd service or invoke Anthropic.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone


EXPECTED_TOOLS = {
    "haios_status",
    "haios_read_document",
    "haios_self_model",
    "haios_find_resources",
    "haios_talk",
}


def keychain_value(service: str) -> str:
    account = subprocess.check_output(["/usr/bin/id", "-un"], text=True).strip()
    return subprocess.check_output(
        ["/usr/bin/security", "find-generic-password", "-a", account, "-s", service, "-w"],
        text=True, stderr=subprocess.DEVNULL,
    ).rstrip("\r\n")


def local_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def parse_tool_payload(result):
    if result.is_error:
        raise RuntimeError("MCP tool returned is_error=True")
    raw = result.structured_content
    if raw is None:
        import json as _json
        for item in result.content:
            if getattr(item, "type", None) == "text":
                raw = _json.loads(item.text)
                break
    if not isinstance(raw, dict):
        raise RuntimeError("Unexpected MCP payload shape")
    return raw.get("result", raw) if isinstance(raw.get("result"), dict) else raw


async def test_authenticated_connection(url: str, token: str):
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    async with httpx2.AsyncClient(timeout=2.5) as anon:
        no_auth = await anon.get(url)
        wrong = await anon.get(url, headers={"Authorization": "Bearer " + "invalid-test-token-" + secrets.token_hex(20)})
        if no_auth.status_code != 401 or wrong.status_code != 401:
            raise RuntimeError("Bearer gate failed: expected HTTP 401 for absent and wrong tokens")

    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer " + token},
        timeout=httpx2.Timeout(10.0, read=20.0),
    ) as http:
        async with Client(streamable_http_client(url, http_client=http)) as client:
            result = await client.list_tools()
            actual = {tool.name for tool in result.tools}
            if actual != EXPECTED_TOOLS:
                raise RuntimeError("v0.2 tools mismatch; got " + repr(sorted(actual)))
            status = parse_tool_payload(await client.call_tool("haios_status", {}))
            if status.get("version") != "0.2.0-z1" or status.get("authority") != "NONE":
                raise RuntimeError("v0.2 status or authority mismatch")
            if status.get("filesystem_write") is not False:
                raise RuntimeError("Writable authority unexpectedly exposed")
            model = parse_tool_payload(await client.call_tool("haios_self_model", {}))
            if model.get("authority") != "NONE":
                raise RuntimeError("Witness self-model authority mismatch")
            normalized = json.dumps({"tools": sorted(actual), "status": status, "self_model": model}, sort_keys=True, default=str)
            return {
                "service_version": status["version"],
                "tools": sorted(actual),
                "tool_count": len(actual),
                "no_token_http": no_auth.status_code,
                "invalid_token_http": wrong.status_code,
                "authority": status["authority"],
                "receipt_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "receipt_kind": "UNSIGNED_LOCAL_TOOL_RESULT_DIGEST_NOT_REMOTE_ATTESTATION",
            }


async def main():
    if sys.platform != "darwin":
        raise RuntimeError("This smoke test is intended for macOS")
    package_dir = Path(__file__).resolve().parent.parent
    source = package_dir / "src"
    context = Path.home() / "Library/Application Support/HumanAIOS/context"
    if not (context / "CURRENT.md").is_file() or not (context / "REGISTERED.md").is_file():
        raise RuntimeError("Expected HumanAIOS public context snapshot not found")
    if not (source / "haios_mcp/server.py").is_file():
        raise RuntimeError("v0.2 package is incomplete")

    token = keychain_value("ai.humanaios.mcp-token")
    if len(token) < 32:
        raise RuntimeError("Keychain MCP token is missing or too short")

    port = local_free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source) + os.pathsep + env.get("PYTHONPATH", "")
    env["HAIOS_MCP_TOKEN"] = token
    # Do not read Anthropic credentials: this tests MCP authentication only.
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("HAIOS_RESOURCE_MINER_ORIGIN", None)
    child = subprocess.Popen(
        [sys.executable, "-m", "haios_mcp.server", "--transport", "http",
         "--repo", str(context), "--port", str(port)],
        cwd=str(package_dir), env=env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        import httpx2
        for _ in range(70):
            if child.poll() is not None:
                raise RuntimeError(f"candidate process exited before handshake (status {child.returncode})")
            try:
                async with httpx2.AsyncClient(timeout=0.5) as http:
                    r = await http.get(url)
                    if r.status_code == 401:
                        break
            except (httpx2.RequestError, OSError):
                pass
            await asyncio.sleep(0.2)
        else:
            raise RuntimeError("candidate did not bind a loopback listener")
        result = await test_authenticated_connection(url, token)
        print("HAIOS v0.2 CONTROLLED AUTH TEST: PASS")
        print(json.dumps({
            "observed_utc": datetime.now(timezone.utc).isoformat(),
            "transport": "isolated loopback HTTP / MCP",
            "candidate_only": True,
            "changed_installed_service": False,
            "anthropic_requests": 0,
            **result,
        }, indent=2))
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        # Error details exclude local secrets and raw remote responses.
        print(f"HAIOS v0.2 CONTROLLED AUTH TEST: FAIL ({type(exc).__name__}: {exc})")
        sys.exit(1)
