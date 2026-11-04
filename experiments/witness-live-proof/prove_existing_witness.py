#!/usr/bin/env python3
"""One actual nonce-bound call to an ALREADY RUNNING, installed Witness MCP.

Mac operator only. No service launch, service install, or repo mutation.
Requires opt-in to one provider-backed haios_talk request. Prints only redacted
metadata, never an API key, bearer, session ID, or model response body.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import re
import secrets
import subprocess
import sys


URL = "http://127.0.0.1:8768/mcp"
EXPECTED_CONTEXT = ("CURRENT.md", "REGISTERED.md", "GOVERNANCE.md")


class ProofRefused(RuntimeError):
    pass


def parse_payload(raw):
    if getattr(raw, "is_error", None) is True:
        raise ProofRefused("MCP_TOOL_ERROR")
    payload = getattr(raw, "structured_content", None)
    if payload is None:
        for item in getattr(raw, "content", ()):
            if getattr(item, "type", None) == "text":
                try:
                    payload = json.loads(item.text)
                except (ValueError, TypeError):
                    raise ProofRefused("INVALID_TOOL_JSON") from None
                break
    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    if not isinstance(payload, dict):
        raise ProofRefused("INVALID_TOOL_PAYLOAD")
    return payload


def verify_answer(payload, nonce):
    if not isinstance(payload, dict):
        raise ProofRefused("INVALID_MODEL_PAYLOAD")
    answer = payload.get("answer")
    if not isinstance(answer, str) or not (1 <= len(answer) <= 12000):
        raise ProofRefused("MISSING_MODEL_ANSWER")
    if not re.search(r"(?<![A-Za-z0-9_])WITNESS_ACK:" + re.escape(nonce) + r"(?![A-Za-z0-9_])", answer):
        raise ProofRefused("NONCE_NOT_ECHOED")
    if payload.get("authority") != "NONE":
        raise ProofRefused("AUTHORITY_NOT_NONE")
    if payload.get("response_may_be_incomplete") is True:
        raise ProofRefused("INCOMPLETE_RESPONSE")
    manifest = payload.get("source_manifest")
    if not isinstance(manifest, list):
        raise ProofRefused("SOURCE_MANIFEST_MISSING")
    if tuple(row.get("filename") for row in manifest if isinstance(row, dict)) != EXPECTED_CONTEXT:
        raise ProofRefused("SOURCE_MANIFEST_WRONG_FILES")
    refs = []
    for row in manifest:
        sha = row.get("sha256")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ProofRefused("SOURCE_DIGEST_MISSING")
        if not isinstance(row.get("truncated"), bool):
            raise ProofRefused("SOURCE_TRUNCATION_UNKNOWN")
        refs.append({"name": row["filename"], "sha256": sha, "truncated": row["truncated"]})
    digest = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    if payload.get("answer_sha256") not in (None, digest):
        raise ProofRefused("RESPONSE_DIGEST_MISMATCH")
    return {"nonce_echo_verified": True, "answer_sha256": digest,
            "answer_chars": len(answer), "source_manifest": refs, "authority": "NONE"}


def keychain_token():
    try:
        account = subprocess.check_output(
            ["/usr/bin/id", "-un"], text=True, stderr=subprocess.DEVNULL, timeout=5,
        ).strip()
        token = subprocess.check_output(
            ["/usr/bin/security", "find-generic-password", "-a", account,
             "-s", "ai.humanaios.mcp-token", "-w"],
            text=True, stderr=subprocess.DEVNULL, timeout=10,
        ).rstrip("\r\n")
    except (OSError, subprocess.SubprocessError):
        raise ProofRefused("KEYCHAIN_BEARER_UNAVAILABLE") from None
    if not 32 <= len(token) <= 512:
        raise ProofRefused("KEYCHAIN_BEARER_INVALID")
    return token


async def prove():
    import httpx2
    from mcp import Client
    from mcp.client.streamable_http import streamable_http_client

    # First prove an existing protected listener is alive.
    try:
        async with httpx2.AsyncClient(timeout=3.0, trust_env=False) as public:
            no_auth = await public.get(URL)
            bad_auth = await public.get(URL, headers={
                "Authorization": "Bearer bad-" + secrets.token_hex(32)})
            if no_auth.status_code != 401 or bad_auth.status_code != 401:
                raise ProofRefused("UNAUTHENTICATED_REQUEST_NOT_DENIED")
    except ProofRefused:
        raise
    except Exception:
        raise ProofRefused("INSTALLED_LOOPBACK_SERVICE_NOT_REACHABLE") from None

    token = keychain_token()
    nonce = secrets.token_hex(16)
    prompt = (
        "HumanAIOS Witness operator test. Synthetic content only. "
        "Do not execute actions or request personal information. "
        f"Start with EXACTLY WITNESS_ACK:{nonce}. "
        "In one sentence explain that you cannot authorize work and that "
        "CURRENT.md, REGISTERED.md, GOVERNANCE.md are local document snapshots "
        "rather than verified current GitHub state."
    )
    try:
        async with httpx2.AsyncClient(
            headers={"Authorization": "Bearer " + token},
            timeout=httpx2.Timeout(10.0, read=180.0), trust_env=False,
        ) as http:
            async with Client(streamable_http_client(URL, http_client=http)) as client:
                tools = {x.name for x in (await client.list_tools()).tools}
                if not {"haios_status", "haios_talk"}.issubset(tools):
                    raise ProofRefused("EXPECTED_INSTALLED_TOOLS_MISSING")
                status = parse_payload(await client.call_tool("haios_status", {}))
                if status.get("authority") != "NONE":
                    raise ProofRefused("SERVICE_STATUS_AUTHORITY_NOT_NONE")
                answer = parse_payload(await client.call_tool("haios_talk", {"message": prompt}))
                verified = verify_answer(answer, nonce)
    except ProofRefused:
        raise
    except Exception:
        raise ProofRefused("MCP_OR_PROVIDER_INTERACTION_FAILED") from None
    finally:
        del token

    receipt = {
        "result": "PASS_NONCE_BOUND_EXISTING_WITNESS_MCP_INTERACTION",
        "state": "OBSERVED_OPERATOR_SIDE_NOT_INDEPENDENT_ATTESTATION",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "local_endpoint_only": True,
        "started_new_service": False,
        "changed_installed_service": False,
        "service_version_reported": str(status.get("version") or "UNKNOWN")[:80],
        "tools_observed": sorted(tools),
        "requested_tool": "haios_talk",
        "request_nonce": nonce,
        "provider_calls_requested": 1,
        "raw_model_response_in_receipt": False,
        "execution": "DISABLED",
        "authority_effect": "NONE",
        **verified,
        "limitations": [
            "Unsigned operator-side receipt is not an independent remote attestation",
            "Manifest content fingerprints do not establish source freshness",
            "Model-backed chat can contact an external provider; not air-gapped",
        ],
    }
    basis = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receipt_sha256"] = hashlib.sha256(basis).hexdigest()
    receipt["receipt_kind"] = "UNSIGNED_LOCAL_INTERACTION_DIGEST_NOT_ATTESTATION"
    return receipt


def main():
    parser = argparse.ArgumentParser(description="One-shot existing Witness MCP interaction")
    parser.add_argument("--allow-model-call", action="store_true",
                        help="Consent to one provider-backed model call via existing service")
    args = parser.parse_args()
    if sys.platform != "darwin":
        print(json.dumps({"result": "BLOCKED", "reason": "MACOS_OPERATOR_HOST_REQUIRED"}))
        return 2
    if not args.allow_model_call:
        print(json.dumps({"result": "BLOCKED", "reason": "EXPLICIT_PROVIDER_CONSENT_REQUIRED"}))
        return 2
    try:
        print(json.dumps(asyncio.run(prove()), indent=2, sort_keys=True))
    except ProofRefused as exc:
        print(json.dumps({"result": "NOT_PROVEN", "reason": str(exc)}))
        return 1
    except Exception:
        print(json.dumps({"result": "NOT_PROVEN", "reason": "UNEXPECTED_PROBE_ERROR"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
