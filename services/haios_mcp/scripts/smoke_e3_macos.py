#!/usr/bin/env python3
"""E3: isolated Witness MCP -> public snapshot Resource Miner, no scanning.

Runs a synthetic contract/challenge test and, when the operator has a local
readable Resource Miner checkout + snapshot, an independent real implementation
readback. Installs nothing. Changes no existing service. Makes no Claude call.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading

from smoke_auth_macos import keychain_value, local_free_port, parse_tool_payload, test_authenticated_connection
from smoke_e2_macos import wait_for_server

OBJECTIVE = "compute credits for AI research"


def find_miner_checkout() -> tuple[Path | None, str]:
    home = Path.home()
    paths = []
    if os.environ.get("HAIOS_E3_MINER_ROOT"):
        paths.append(Path(os.environ["HAIOS_E3_MINER_ROOT"]).expanduser())
    paths.extend([
        home / "Desktop/HAIOS-Main/operations-staging/humanaios-funding-pipeline/resource-miner",
        home / "Desktop/HAIOS-Main/operations/humanaios-funding-pipeline/resource-miner",
        home / "Desktop/HAIOS-Main/resource-miner",
        home / "resource-miner",
    ])
    found_without_snapshot = False
    for path in paths:
        if (path / "app.py").is_file() and (path / "resource_miner/intent_os.py").is_file():
            if (path / "data/resources.snapshot.jsonl").is_file():
                return path.resolve(), "FOUND_LOCAL_STORED_SNAPSHOT"
            found_without_snapshot = True
    return None, "LOCAL_SNAPSHOT_NOT_FOUND" if found_without_snapshot else "MINER_CHECKOUT_NOT_FOUND"


class SyntheticPublicMiner(BaseHTTPRequestHandler):
    mode = "positive"
    seen = []

    def do_POST(self):
        if self.path != "/api/intent":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length))
        type(self).seen.append(request)
        candidate = {
            "resource_id": "SYNTHETIC-E3-001", "title": "Compute credits for research",
            "description": "Synthetic review-only source", "source_name": "HumanAIOS Funding Pipeline",
            "source_url": "https://example.org/compute", "route": "WATCH",
            "observed_at": "2026-10-01", "last_verified_at": None, "deadline": None,
            "eligibility_assessed": False, "PRIVATE_CANARY": "NEVER_EXPOSE_E3_CANARY",
        }
        if type(self).mode == "private":
            candidate["source_name"] = "HackerOne private program"
        result = {
            "status": "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW",
            "source_mode": "snapshot", "source_status": "CURATED_SNAPSHOT_NOT_LIVE",
            "source_warning": "Synthetic fixture: unexamined public rows remain",
            "matched_count": 3, "shown_count": 1, "unexamined_count": 2,
            "authority": "NONE", "execution": "DISABLED", "eligibility": "NOT_ASSESSED",
            "receipt_sha256": hashlib.sha256(b"SYNTHETIC-E3-RECEIPT").hexdigest(),
            "candidates": [candidate],
        }
        body = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    # No Anthropic, GitHub, or private-source credentials in either subprocess.
    for k in list(env):
        if any(tag in k.upper() for tag in ("ANTHROPIC", "GITHUB_TOKEN", "HACKERONE", "RESOURCE_MINER_ADMIN_TOKEN", "OPENAI_API_KEY")):
            env.pop(k, None)
    return env


async def call_resources(url: str, token: str, *, expected_error: bool = False) -> dict:
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    async with httpx2.AsyncClient(
        headers={"Authorization": "Bearer " + token},
        timeout=httpx2.Timeout(10.0, read=30.0),
    ) as http:
        async with Client(streamable_http_client(url, http_client=http)) as client:
            raw = await client.call_tool("haios_find_resources", {"objective": OBJECTIVE})
            if expected_error:
                if raw.is_error is not True:
                    raise RuntimeError("Private source was not rejected")
                return {"refused_private_source": True}
            return parse_tool_payload(raw)


def verify_snapshot_response(payload: dict) -> dict:
    if payload.get("source_mode") != "snapshot" or payload.get("authority") != "NONE":
        raise RuntimeError("Snapshot or authority invariant failed")
    if payload.get("eligibility") != "NOT_ASSESSED" or payload.get("execution") != "DISABLED":
        raise RuntimeError("Eligibility or execution invariant failed")
    if payload.get("status") not in {
        "CANDIDATES_FOR_HUMAN_REVIEW", "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW",
        "NO_SUPPORTED_MATCH", "PARTIAL_SEARCH_NO_MATCH",
    }:
        raise RuntimeError("Unexpected upstream candidate status")
    missing = payload.get("unexamined_count")
    if type(missing) is not int or missing < 0:
        raise RuntimeError("Missing unexamined row count")
    if (missing > 0) != payload["status"].startswith("PARTIAL_"):
        raise RuntimeError("Partial status misrepresented")
    if not isinstance(payload.get("source_warning"), str):
        raise RuntimeError("Missing upstream source warning")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) > 10:
        raise RuntimeError("Candidate bound exceeded")
    for c in candidates:
        if c.get("eligibility_assessed") is not False:
            raise RuntimeError("Candidate asserts eligibility")
        if c.get("source_name") not in ("HumanAIOS Funding Pipeline", "DEV Community"):
            raise RuntimeError("Non-public source leaked")
        if not isinstance(c.get("source_url"), str) or not c["source_url"].startswith("https://"):
            raise RuntimeError("Candidate lost HTTPS provenance")
        if c.get("source_verification") != "UPSTREAM_SNAPSHOT_NOT_INDEPENDENTLY_VERIFIED":
            raise RuntimeError("Missing provenance uncertainty")
    digest = payload.get("receipt_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RuntimeError("Source receipt hash missing")
    return {
        "status": payload["status"],
        "source_mode": "snapshot",
        "source_status": payload.get("source_status"),
        "source_warning": payload["source_warning"],
        "matched_count": payload.get("matched_count"),
        "shown_count": payload.get("shown_count"),
        "unshown_match_count": payload.get("unshown_match_count"),
        "unexamined_count": missing,
        "candidates": [{"resource_id": c["resource_id"], "title": c["title"],
                        "source_name": c["source_name"], "source_url": c["source_url"],
                        "route": c["route"], "source_verification": c["source_verification"]}
                       for c in candidates],
        "authority": "NONE", "eligibility": "NOT_ASSESSED", "execution": "DISABLED",
        "receipt_sha256": digest,
        "receipt_kind": "UNSIGNED_UPSTREAM_SELECTION_DIGEST",
    }


async def start_candidate(*, package: Path, token: str, miner_port: int):
    context = Path.home() / "Library/Application Support/HumanAIOS/context"
    env = clean_env()
    env["PYTHONPATH"] = str(package / "src")
    env["HAIOS_RESOURCE_MINER_ORIGIN"] = f"http://127.0.0.1:{miner_port}"
    env["HAIOS_MCP_TOKEN"] = token
    env.pop("HAIOS_MODEL", None)
    port = local_free_port()
    url = f"http://127.0.0.1:{port}/mcp"
    child = subprocess.Popen(
        [sys.executable, "-m", "haios_mcp.server", "--transport", "http",
         "--repo", str(context), "--port", str(port)],
        cwd=str(package), env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        await wait_for_server(url, child)
        await test_authenticated_connection(url, token)
        return child, url
    except Exception:
        stop_child(child)
        raise


def stop_child(child: subprocess.Popen | None) -> None:
    if child is None or child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill(); child.wait(timeout=5)


async def test_fixture(package: Path, token: str) -> dict:
    SyntheticPublicMiner.mode = "positive"
    SyntheticPublicMiner.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), SyntheticPublicMiner)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    child = None
    try:
        child, url = await start_candidate(package=package, token=token, miner_port=server.server_port)
        payload = await call_resources(url, token)
        if payload.get("status") != "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW":
            raise RuntimeError("Synthetic partial status not preserved")
        if "NEVER_EXPOSE_E3_CANARY" in json.dumps(payload):
            raise RuntimeError("Private payload field leaked through allowlist")
        if len(payload.get("candidates", [])) != 1:
            raise RuntimeError("Synthetic public candidate lost")
        SyntheticPublicMiner.mode = "private"
        challenge = await call_resources(url, token, expected_error=True)
        if SyntheticPublicMiner.seen != [
            {"objective": OBJECTIVE, "source_mode": "snapshot"},
            {"objective": OBJECTIVE, "source_mode": "snapshot"},
        ]:
            raise RuntimeError("Unexpected path, query mode or payload used")
        normalized = verify_snapshot_response(payload)
        return {"fixture": "SYNTHETIC_NOT_A_LIVE_RESOURCE", "private_source_refused": challenge["refused_private_source"],
                "private_canary_hidden": True, "requests": len(SyntheticPublicMiner.seen),
                "projection": normalized}
    finally:
        stop_child(child)
        server.shutdown(); server.server_close(); thread.join(timeout=3)


async def test_real_miner(package: Path, token: str, root: Path) -> dict:
    original = root / "data/resources.snapshot.jsonl"
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    app = root / "app.py"
    app_sha = hashlib.sha256(app.read_bytes()).hexdigest()
    port = local_free_port()
    miner_env = clean_env()
    miner_env.pop("HAIOS_RESOURCE_MINER_ORIGIN", None)
    miner_env["PYTHONPATH"] = str(root)
    # The Miner is run in its own separate process on loopback only. E3 sends
    # source_mode=snapshot; there is no live scan, store, or provider fetch.
    miner = subprocess.Popen(
        [sys.executable, str(app), "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(root), env=miner_env, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    child = None
    hold_probe = None
    try:
        import httpx2
        for _ in range(65):
            if miner.poll() is not None:
                raise RuntimeError("Local Resource Miner subprocess failed to start")
            try:
                async with httpx2.AsyncClient(timeout=0.5) as http:
                    r = await http.get(f"http://127.0.0.1:{port}/api/health")
                    if r.status_code == 200:
                        break
            except (httpx2.RequestError, OSError):
                pass
            await asyncio.sleep(0.2)
        else:
            raise RuntimeError("Local Resource Miner loopback listener unavailable")
        # Prove stale-resource feedback crosses the actual HTTP snapshot path.
        # Checking the Witness's first ten results alone would miss a stale
        # candidate silently present in the upstream hidden result set.
        disputed_url = (
            "https://jobs.lever.co/convergentresearch/"
            "7b0506c1-caf2-4e92-9a44-d062c7a9b988"
        )
        async with httpx2.AsyncClient(timeout=15) as http:
            negative = await http.post(
                f"http://127.0.0.1:{port}/api/intent",
                json={"objective": "Convergent Research Program Launch Manager",
                      "source_mode": "snapshot"},
            )
        if negative.status_code != 200:
            raise RuntimeError("Corrected Miner rejected the source-hold query")
        observed = negative.json()
        if not isinstance(observed, dict) or not isinstance(observed.get("candidates"), list):
            raise RuntimeError("Source-hold query returned malformed candidates")
        if any(row.get("source_url") == disputed_url or row.get("resource_id") == "RES-26D48CDE47BB2BB0"
               for row in observed["candidates"] if isinstance(row, dict)):
            raise RuntimeError("Held Convergent role leaked through stored snapshot")
        if ("withheld" not in str(observed.get("source_warning", "")).lower()
                or observed.get("authority") != "NONE"
                or observed.get("eligibility") != "NOT_ASSESSED"
                or observed.get("execution") != "DISABLED"):
            raise RuntimeError("Corrected Miner did not retain held-source explanation or authority")
        hold_probe = {
            "result": "PASS_HELD_RESOURCE_EXCLUDED_FROM_FULL_SNAPSHOT_SEARCH",
            "source_url": disputed_url,
            "candidate_count": len(observed["candidates"]),
            "source_warning": str(observed["source_warning"])[:350],
        }
        child, url = await start_candidate(package=package, token=token, miner_port=port)
        projection = verify_snapshot_response(await call_resources(url, token))
    finally:
        stop_child(child)
        stop_child(miner)
    after = hashlib.sha256(original.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError("Miner snapshot changed during E3 read-only execution")
    return {"real_backend": "LOCAL_RESOURCE_MINER_APP_READ_ONLY_SNAPSHOT",
            "miner_root": str(root), "app_sha256": app_sha, "snapshot_sha256": before,
            "snapshot_unchanged": True, "projection": projection,
            "held_source_regression": hold_probe}


async def main() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("This script is intended for the operator's Mac")
    package = Path(__file__).resolve().parent.parent
    context = Path.home() / "Library/Application Support/HumanAIOS/context"
    if not (package / "src/haios_mcp/server.py").is_file() or not all(
        (context / name).is_file() for name in ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md")
    ):
        raise RuntimeError("v0.2 candidate or local public context is missing")
    token = keychain_value("ai.humanaios.mcp-token")
    if len(token) < 32:
        raise RuntimeError("Keychain MCP token missing or too short")
    synthetic = await test_fixture(package, token)
    root, source_status = find_miner_checkout()
    real = None
    if root is not None:
        real = await test_real_miner(package, token, root)
    report = {
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "milestone": "E3_WITNESS_PUBLIC_RESOURCE_MINER_PROJECTION",
        "candidate_only": True, "changed_installed_service": False,
        "anthropic_requests": 0, "miner_network_scan_requests": 0,
        "synthetic_contract_passed": True,
        "real_miner_verified": real is not None,
        "real_miner_source_state": source_status,
        "synthetic": synthetic, "real": real,
        "authority": "NONE",
    }
    basis = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["receipt_sha256"] = hashlib.sha256(basis).hexdigest()
    report["receipt_kind"] = "UNSIGNED_LOCAL_E3_TEST_DIGEST_NOT_REMOTE_ATTESTATION"
    print("HAIOS v0.2 E3 TEST: PASS" if real is not None else "HAIOS v0.2 E3 TEST: PARTIAL (synthetic contract only)")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"HAIOS v0.2 E3 TEST: FAIL ({type(exc).__name__})")
        sys.exit(1)