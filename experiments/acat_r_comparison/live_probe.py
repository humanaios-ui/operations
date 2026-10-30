#!/usr/bin/env python3
"""Live read-only probe of the supported GNER-E1 entry point ``verify_lead``.

Issue #1081 "Real authenticated verify_lead() gate". This script is NOT run by
CI. It runs only when a human invokes it with an authorized read-only GitHub
credential in the environment variable ``GITHUB_TOKEN`` (the same convention as
``tools/gner_verify_e1.py``). The credential value is never printed, hashed or
written anywhere.

What it does, per probe in the spec file:
  1. Independently GETs the run metadata once (same endpoint verify_lead uses)
     and records the SHA-256 of the raw response bytes plus selected public
     fields. This is the source-pinned record of what GitHub actually returned.
  2. Builds ONLY the lead (the untrusted email-side hint) from the spec. The
     canonical mapping is fetched by ``verify_lead`` itself; no caller-created
     canonical dictionary is passed anywhere.
  3. Calls the unmodified ``verify_lead`` and records the full result, or the
     ``VerificationDenied`` message and the exception class of its cause.

Boolean-boundary reachability probes (``lead_overrides`` containing booleans)
are included so the review packet can state, from observed behaviour rather
than argument, which of the four offline boolean cases the live entry point
can reach.

Output: ``<out>/live_probe_receipts.json`` (sanitized; safe to attach).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from gner_verify_e1 import REPO, VerificationDenied, verify_lead

API = f"https://api.github.com/repos/{REPO}/actions/runs/"
PUBLIC_FIELDS = ("id", "name", "event", "status", "conclusion", "head_sha",
                 "run_attempt", "created_at", "updated_at", "run_started_at")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_raw(run_id: int, token: str, timeout: int = 10) -> dict:
    """One independent GET; returns public metadata + response hash, never the token."""
    request = urllib.request.Request(API + str(run_id), headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "humanaios-acat-r-live-probe/0.1",
    }, method="GET")
    record: dict = {"run_id": run_id, "fetched_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(131073)
            record["http_status"] = response.status
            record["date_header"] = response.headers.get("Date")
            record["ratelimit_remaining"] = response.headers.get("X-RateLimit-Remaining")
    except urllib.error.HTTPError as exc:
        record["http_status"] = exc.code
        record["error"] = "HTTPError"
        return record
    except Exception as exc:  # network / TLS / timeout
        record["error"] = type(exc).__name__
        return record
    record["response_bytes"] = len(raw)
    record["response_sha256"] = _sha(raw)
    try:
        body = json.loads(raw)
    except ValueError:
        record["error"] = "non-JSON response"
        return record
    record["public_fields"] = {k: body.get(k) for k in PUBLIC_FIELDS}
    record["repository_full_name"] = (body.get("repository") or {}).get("full_name")
    record["pull_request_numbers"] = [pr.get("number") for pr in (body.get("pull_requests") or []) if isinstance(pr, dict)]
    record["pull_requests_present"] = isinstance(body.get("pull_requests"), list)
    record["id_json_type"] = type(body.get("id")).__name__
    record["pull_request_number_json_types"] = sorted({type(pr.get("number")).__name__ for pr in (body.get("pull_requests") or []) if isinstance(pr, dict)})
    return record


def run_probe(probe: dict, token: str) -> dict:
    run_id = probe["run_id"]
    lead = {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": REPO, "run_id": run_id,
            "sha_prefix": probe.get("sha_prefix"), "workflow": probe.get("workflow"),
            "kind": probe.get("kind", "NOTIFICATION_LEAD"), "pr": probe.get("pr")}
    lead.update(probe.get("lead_overrides") or {})
    out = {"probe_id": probe["id"], "purpose": probe.get("purpose", ""), "lead": lead,
           "canonical_source": "fetched inside verify_lead over authenticated HTTPS; not caller-supplied"}
    if probe.get("fetch_raw", True) and isinstance(run_id, int) and type(run_id) is int and run_id > 0:
        out["independent_fetch"] = fetch_raw(run_id, token)
    try:
        result = verify_lead(lead, github_token=token)
        out["verify_lead"] = {"outcome": "RETURNED", "result": result}
    except VerificationDenied as exc:
        out["verify_lead"] = {"outcome": "DENIED", "message": str(exc),
                              "cause": type(exc.__cause__).__name__ if exc.__cause__ else None}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", required=True, help="JSON list of probes")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--credential-note", default="", help="where the credential came from (no secret)")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN not set; refusing to probe (fail closed)", file=sys.stderr)
        return 2
    spec_path = pathlib.Path(args.spec)
    probes = json.loads(spec_path.read_text())
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    receipts = {
        "schema": "humanaios.acat-r.live-verify-lead-probe.v0.1",
        "entry_point": "tools/gner_verify_e1.py::verify_lead (unmodified)",
        "spec_sha256": _sha(spec_path.read_bytes()),
        "started_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "credential_note": args.credential_note,
        "credential_logged": False,
        "authority_effect": "NONE",
        "probes": [run_probe(p, token) for p in probes],
    }
    receipts["finished_at_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    encoded = json.dumps(receipts, indent=2, sort_keys=True) + "\n"
    if token in encoded:  # defence in depth: never persist the credential
        print("credential would leak into receipts; aborting", file=sys.stderr)
        return 3
    (out_dir / "live_probe_receipts.json").write_text(encoded)
    summary = [(p["probe_id"], p["verify_lead"]["outcome"],
                p["verify_lead"].get("result", {}).get("state") or p["verify_lead"].get("message"))
               for p in receipts["probes"]]
    for row in summary:
        print(*row, sep=" | ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
