#!/usr/bin/env python3
"""E2 candidate-only live MCP/Unit Zero stream with nonce and source manifest.

One opt-in Anthropic request on macOS. Never changes installed LaunchAgent.
Only run explicitly from the operator's Mac. No secrets printed.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

from smoke_auth_macos import (
    keychain_value, local_free_port, parse_tool_payload,
    test_authenticated_connection,
)

EXPECTED_CONTEXT = ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md")


async def wait_for_server(url: str, child: subprocess.Popen) -> None:
    import httpx2
    for _ in range(75):
        if child.poll() is not None:
            raise RuntimeError("Isolated MCP candidate exited before handshake")
        try:
            async with httpx2.AsyncClient(timeout=0.7) as http:
                response = await http.get(url)
            if response.status_code == 401:
                return
        except (httpx2.RequestError, OSError):
            pass
        await asyncio.sleep(0.2)
    raise RuntimeError("Isolated MCP candidate failed to start")


def verify_e2(payload: dict, nonce: str) -> dict:
    answer = payload.get("answer")
    if not isinstance(answer, str) or not answer.strip() or nonce not in answer:
        raise RuntimeError("E2 nonce/answer mismatch")
    manifest = payload.get("source_manifest")
    if not isinstance(manifest, list) or tuple(
        item.get("filename") for item in manifest if isinstance(item, dict)
    ) != EXPECTED_CONTEXT:
        raise RuntimeError("E2 source manifest mismatch")
    for row in manifest:
        if (not isinstance(row.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
                or not isinstance(row.get("truncated"), bool)):
            raise RuntimeError("E2 malformed source digest/truncation")
    if not all(name in answer for name in EXPECTED_CONTEXT):
        raise RuntimeError("E2 reply omitted supplied context")
    if any(row["truncated"] for row in manifest) and not any(
        word in answer.lower() for word in ("truncat", "partial", "incomplete")
    ):
        raise RuntimeError("E2 reply did not disclose truncation")
    if payload.get("authority") != "NONE" or payload.get("response_may_be_incomplete") is True:
        raise RuntimeError("E2 authority or completion boundary")
    digest = hashlib.sha256(json.dumps(
        {"answer": answer, "source_manifest": manifest,
         "authority": payload["authority"]},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "milestone": "E2_LIVE_MCP_UNIT_ZERO_STREAMING",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "nonce_verified": True,
        "source_manifest_verified": True,
        "source_files": [{"filename": x["filename"], "truncated": x["truncated"],
                          "sha256": x["sha256"]} for x in manifest],
        "authority": "NONE", "anthropic_requests": 1,
        "candidate_only": True, "changed_installed_service": False,
        "receipt_sha256": digest,
        "receipt_kind": "UNSIGNED_LOCAL_MODEL_OUTPUT_DIGEST_NOT_REMOTE_ATTESTATION",
        "unit_zero_answer": answer[:1800],
    }


async def test_e2(url: str, token: str, nonce: str) -> dict:
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client
    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer " + token},
        timeout=httpx2.Timeout(15, read=180),
    ) as http:
        async with Client(streamable_http_client(url, http_client=http)) as client:
            result = await client.call_tool("haios_talk", {
                "message": (
                    f"E2 controlled test. Repeat nonce {nonce} on the first line. "
                    "In 120 words or fewer identify CURRENT.md, REGISTERED.md "
                    "and GOVERNANCE.md as supplied, sometimes truncated context "
                    "rather than independently verified live repository state. "
                    "State your lack of autonomous action authority."
                )
            })
            return verify_e2(parse_tool_payload(result), nonce)


async def main() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Mac-only live E2")
    package = Path(__file__).resolve().parent.parent
    context = Path.home() / "Library/Application Support/HumanAIOS/context"
    if not all((context / name).is_file() for name in EXPECTED_CONTEXT):
        raise RuntimeError("Local context snapshots missing")
    token = keychain_value("ai.humanaios.mcp-token")
    secret = keychain_value("ai.humanaios.anthropic")
    if len(token) < 32 or len(secret) < 20:
        raise RuntimeError("Keychain secrets unavailable")
    port = local_free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["HAIOS_MCP_TOKEN"] = token
    env["ANTHROPIC_API_KEY"] = secret
    env.pop("HAIOS_RESOURCE_MINER_ORIGIN", None)
    env.pop("HAIOS_MODEL", None)
    child = subprocess.Popen([
        sys.executable, "-m", "haios_mcp.server",
        "--transport", "http", "--repo", str(context), "--port", str(port),
    ], cwd=str(package), env=env, stdin=subprocess.DEVNULL,
       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        await wait_for_server(url, child)
        await test_authenticated_connection(url, token)
        result = await test_e2(url, token, secrets.token_hex(8))
        print("HAIOS v0.2 E2 STREAMING TEST: PASS")
        print(json.dumps(result, indent=2))
    finally:
        if child.poll() is None:
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
        print(f"HAIOS v0.2 E2 STREAMING TEST: FAIL ({type(exc).__name__})")
        sys.exit(1)
