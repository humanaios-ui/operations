#!/usr/bin/env python3
"""E3 cross-branch integration: corrected Resource Miner and Witness MCP, CI only.

Test-only loopback servers, no credentials, live scans, publishing or writes to
repositories. Requires two prechecked local checkouts supplied by the workflow.
"""
from __future__ import annotations

import argparse
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
import urllib.error
import urllib.request

DISPUTED_URL = (
    "https://jobs.lever.co/convergentresearch/"
    "7b0506c1-caf2-4e92-9a44-d062c7a9b988"
)


def port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    candidate = sock.getsockname()[1]
    sock.close()
    return candidate


def invoke_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("Unexpected status from read-only Miner")
        return json.loads(response.read(128001))


def check_ready(url: str, *, unauthorized: bool = False) -> None:
    if unauthorized:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                raise RuntimeError("MCP endpoint unexpectedly allowed anonymous access")
        except urllib.error.HTTPError as error:
            if error.code != 401:
                raise RuntimeError("MCP anonymous denial was not HTTP 401") from None
    else:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            if response.status != 200:
                raise RuntimeError("Miner health probe failed")


def wait_for(url: str, child: subprocess.Popen, unauthorized: bool) -> None:
    for _ in range(100):
        if child.poll() is not None:
            raise RuntimeError("Isolated test service exited")
        try:
            check_ready(url, unauthorized=unauthorized)
            return
        except (OSError, TimeoutError, urllib.error.URLError):
            time.sleep(0.1)
    raise RuntimeError("Isolated test service did not initialize")


def stop(child: subprocess.Popen | None) -> None:
    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=8)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=8)


async def verify_witness(url: str, bearer: str, expected: dict) -> dict:
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer " + bearer},
        timeout=httpx2.Timeout(10.0, read=30.0),
    ) as http:
        async with Client(streamable_http_client(url, http_client=http)) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            if "haios_find_resources" not in tools:
                raise RuntimeError("Witness discovery tool missing")
            result = await client.call_tool(
                "haios_find_resources",
                {"objective": "compute credits for AI research"},
            )
            if result.is_error:
                raise RuntimeError("Witness real snapshot tool failed")
            payload = result.structured_content
            if not isinstance(payload, dict):
                payload = json.loads(result.content[0].text)
            if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
                payload = payload["result"]

    if payload.get("authority") != "NONE" or payload.get("execution") != "DISABLED":
        raise RuntimeError("Witness authority or execution boundary expanded")
    if payload.get("eligibility") != "NOT_ASSESSED":
        raise RuntimeError("Witness asserted eligibility")
    if payload.get("source_mode") != "snapshot" or "withheld" not in payload.get("source_warning", ""):
        raise RuntimeError("Witness failed to carry held-source disclosure")
    if len(payload.get("candidates", [])) > 10 or len(payload.get("candidates", [])) < 1:
        raise RuntimeError("Witness visible candidate bound failed")
    if (payload.get("matched_count") != expected["matched_count"]
            or payload.get("upstream_shown_count") != expected["shown_count"]
            or payload.get("shown_count") != len(payload["candidates"])
            or payload.get("unshown_match_count") !=
                payload["matched_count"] - len(payload["candidates"])):
        raise RuntimeError("Witness displayed vs upstream counts inconsistent")
    if any(c.get("source_url") == DISPUTED_URL for c in payload["candidates"]):
        raise RuntimeError("Disputed listing surfaced in Witness")
    return {
        "upstream_matches": payload["matched_count"],
        "visible_matches": payload["shown_count"],
        "unshown_matches": payload["unshown_match_count"],
        "authority": payload["authority"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--miner-root", type=Path, required=True)
    parser.add_argument("--witness-root", type=Path, required=True)
    args = parser.parse_args()
    miner = args.miner_root.resolve()
    witness = args.witness_root.resolve()
    snapshot = miner / "data/resources.snapshot.jsonl"
    catalog = miner.parent / "data/sources.json"
    if not all(p.is_file() for p in (snapshot, catalog, miner / "app.py",
                                    witness / "CURRENT.md", witness / "REGISTERED.md")):
        raise RuntimeError("Required pinned source inputs missing")
    before = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    catalog_before = hashlib.sha256(catalog.read_bytes()).hexdigest()
    secret = secrets.token_urlsafe(48)
    miner_port, witness_port = port(), port()
    while witness_port == miner_port:
        witness_port = port()

    # Disable all cloud/provider secrets in child process environments.
    env = {k: v for k, v in os.environ.items() if
           not any(tag in k.upper() for tag in
                   ("ANTHROPIC", "HACKERONE", "GITHUB_TOKEN", "OPENAI_API_KEY",
                    "RESOURCE_MINER_ADMIN_TOKEN"))}
    env["PYTHONPATH"] = str(miner)
    server = None
    assistant = None
    try:
        server = subprocess.Popen(
            [sys.executable, str(miner / "app.py"), "--host", "127.0.0.1",
             "--port", str(miner_port)],
            cwd=str(miner), env=env, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        miner_url = "http://127.0.0.1:%d" % miner_port
        wait_for(miner_url + "/api/health", server, unauthorized=False)
        hold = invoke_json(miner_url + "/api/intent", {
            "objective": "Convergent Research Program Launch Manager",
            "source_mode": "snapshot",
        })
        if (DISPUTED_URL in json.dumps(hold)
                or hold.get("authority") != "NONE"
                or "withheld" not in hold.get("source_warning", "")):
            raise RuntimeError("Held listing still surfaced, or no hold disclosure")
        results = invoke_json(miner_url + "/api/intent", {
            "objective": "compute credits for AI research",
            "source_mode": "snapshot",
        })
        if (DISPUTED_URL in json.dumps(results)
                or results.get("eligibility") != "NOT_ASSESSED"
                or results.get("execution") != "DISABLED"):
            raise RuntimeError("Real backend returned held listing or escalated")
        env2 = dict(env)
        env2["PYTHONPATH"] = str(witness / "services/haios_mcp/src")
        env2["HAIOS_RESOURCE_MINER_ORIGIN"] = miner_url
        env2["HAIOS_MCP_TOKEN"] = secret
        assistant = subprocess.Popen(
            [sys.executable, "-m", "haios_mcp.server", "--transport", "http",
             "--repo", str(witness), "--port", str(witness_port)],
            cwd=str(witness), env=env2, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        endpoint = "http://127.0.0.1:%d/mcp" % witness_port
        wait_for(endpoint, assistant, unauthorized=True)
        witness_summary = asyncio.run(verify_witness(endpoint, secret, results))
    finally:
        stop(assistant)
        stop(server)
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != before:
        raise RuntimeError("Historical snapshot mutated")
    if hashlib.sha256(catalog.read_bytes()).hexdigest() != catalog_before:
        raise RuntimeError("Curated catalog mutated")
    report = {
        "milestone": "E3_CORRECTED_BRANCH_INTEGRATION",
        "outcome": "PASS",
        "held_convergent_url_absent_from_full_search": True,
        "historical_snapshot_unchanged": True,
        "curated_catalog_unchanged": True,
        "source_mode": "snapshot",
        "anthropic_requests": 0,
        "miner_live_scan_requests": 0,
        "witness": witness_summary,
        "authority": "NONE",
    }
    report["receipt_kind"] = "UNSIGNED_CI_EXECUTION_DIGEST_NOT_INDEPENDENT_ATTESTATION"
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
