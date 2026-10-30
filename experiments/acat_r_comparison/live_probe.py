#!/usr/bin/env python3
"""Live read-only probe of the supported GNER-E1 entry point ``verify_lead``.

Issue #1081 "Real authenticated verify_lead() gate". This script is NOT run by
CI. It runs only when a human invokes it with an authorized read-only GitHub
credential in the environment variable ``GITHUB_TOKEN`` (the same convention as
``tools/gner_verify_e1.py``). The credential value is never printed, hashed or
written anywhere.

Before importing the runtime, the script verifies that ``tools/gner_verify_e1.py``
and ``tools/gner_notification_e0.py`` hash to the frozen Git blobs pinned by
``study.py`` and refuses to run otherwise, so "unmodified" is checked, not
asserted (Copilot r4428945853). The verified identifiers go into the receipt.

What it does, per probe in the spec file:
  1. Builds ONLY the lead (the untrusted email-side hint) from the spec. The
     canonical mapping is fetched by ``verify_lead`` itself; no caller-created
     canonical dictionary is passed anywhere.
  2. Calls the unmodified ``verify_lead`` with a pass-through observer on
     ``urllib.request.urlopen`` that records the exact bytes, HTTP status and
     URL the function consumed, without altering them. The receipt hashes
     THOSE bytes, so the hash and the result come from the same response
     (Copilot r4428945818).
  3. Separately GETs the same endpoint once more as a second observation and
     records whether it matched the consumed bytes.

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
# Same values as study.PINNED_BLOBS; tests/test_acat_r_gner_e1_study.py asserts equality.
PINNED_BLOBS = {
    "tools/gner_verify_e1.py": "8290c51cd75c7de78a226770936a8f48766c24f0",
    "tools/gner_notification_e0.py": "e8f893a3d433f900b10c101828d1cbb013413fa6",
}
PUBLIC_FIELDS = ("id", "name", "event", "status", "conclusion", "head_sha",
                 "run_attempt", "created_at", "updated_at", "run_started_at")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    """Git's blob object id, computed without invoking git."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def verify_source_pins(root: pathlib.Path = ROOT) -> dict:
    """Return {path: {expected, observed, verified}}; raise if any pin fails."""
    report = {}
    for rel, expected in PINNED_BLOBS.items():
        observed = git_blob_sha1((root / rel).read_bytes())
        report[rel] = {"expected_git_blob": expected, "observed_git_blob": observed,
                       "sha256": _sha((root / rel).read_bytes()), "verified": observed == expected}
    failed = [k for k, v in report.items() if not v["verified"]]
    if failed:
        raise SystemExit(f"source pin mismatch, refusing to probe a modified runtime: {failed}")
    return report


SOURCE_PINS = verify_source_pins()
sys.path.insert(0, str(ROOT / "tools"))
from gner_verify_e1 import REPO, VerificationDenied, verify_lead  # noqa: E402  (after pin check by design)

API = f"https://api.github.com/repos/{REPO}/actions/runs/"


class _Observed:
    """Pass-through wrapper: forwards every call, records what was read."""

    def __init__(self, inner, capture: dict):
        self._inner = inner
        self._cap = capture
        capture["http_status"] = inner.status
        capture["url"] = inner.geturl()
        capture["date_header"] = inner.headers.get("Date")
        capture["ratelimit_remaining"] = inner.headers.get("X-RateLimit-Remaining")

    def __enter__(self):
        self._inner.__enter__()
        return self

    def __exit__(self, *exc):
        return self._inner.__exit__(*exc)

    @property
    def status(self):
        return self._inner.status

    @property
    def headers(self):
        return self._inner.headers

    def read(self, amt=-1):
        data = self._inner.read(amt)
        self._cap["raw"] = self._cap.get("raw", b"") + data
        return data


class observe_urlopen:
    """Context manager: records the response verify_lead actually consumed."""

    def __init__(self):
        self.capture: dict = {}
        self._real = urllib.request.urlopen

    def __enter__(self):
        cap = self.capture
        real = self._real

        def wrapper(request, *args, **kwargs):
            cap["request_url"] = request.full_url if hasattr(request, "full_url") else str(request)
            cap["authorization_header_present"] = bool(request.has_header("Authorization")) if hasattr(request, "has_header") else None
            try:
                inner = real(request, *args, **kwargs)
            except urllib.error.HTTPError as exc:
                cap["http_status"] = exc.code
                cap["error"] = "HTTPError"
                raise
            except Exception as exc:  # network / TLS / timeout: recorded, then re-raised to verify_lead
                cap["error"] = type(exc).__name__
                raise
            return _Observed(inner, cap)
        urllib.request.urlopen = wrapper
        return self

    def __exit__(self, *exc):
        urllib.request.urlopen = self._real
        return False


def summarize_consumed(capture: dict) -> dict:
    out = {k: v for k, v in capture.items() if k != "raw"}
    raw = capture.get("raw")
    if raw is not None:
        out["response_bytes"] = len(raw)
        out["response_sha256"] = _sha(raw)
        try:
            body = json.loads(raw)
            out["public_fields"] = {k: body.get(k) for k in PUBLIC_FIELDS}
            out["repository_full_name"] = (body.get("repository") or {}).get("full_name")
            out["pull_request_numbers"] = [pr.get("number") for pr in (body.get("pull_requests") or []) if isinstance(pr, dict)]
            out["pull_requests_present"] = isinstance(body.get("pull_requests"), list)
            out["id_json_type"] = type(body.get("id")).__name__
            out["pull_request_number_json_types"] = sorted({type(pr.get("number")).__name__ for pr in (body.get("pull_requests") or []) if isinstance(pr, dict)})
        except ValueError:
            out["error"] = "non-JSON response"
    return out


def fetch_independent(run_id: int, token: str, timeout: int = 10) -> dict:
    """Second observation of the same endpoint; never the token."""
    request = urllib.request.Request(API + str(run_id), headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "humanaios-acat-r-live-probe/0.2",
    }, method="GET")
    record: dict = {"run_id": run_id, "fetched_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(131073)
            record["http_status"] = response.status
    except urllib.error.HTTPError as exc:
        record["http_status"] = exc.code
        record["error"] = "HTTPError"
        return record
    except Exception as exc:
        record["error"] = type(exc).__name__
        return record
    record["response_bytes"] = len(raw)
    record["response_sha256"] = _sha(raw)
    return record


def run_probe(probe: dict, token: str) -> dict:
    run_id = probe["run_id"]
    lead = {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": REPO, "run_id": run_id,
            "sha_prefix": probe.get("sha_prefix"), "workflow": probe.get("workflow"),
            "kind": probe.get("kind", "NOTIFICATION_LEAD"), "pr": probe.get("pr")}
    lead.update(probe.get("lead_overrides") or {})
    out = {"probe_id": probe["id"], "purpose": probe.get("purpose", ""), "lead": lead,
           "canonical_source": "fetched inside verify_lead over authenticated HTTPS; observed pass-through; not caller-supplied"}
    with observe_urlopen() as obs:
        try:
            result = verify_lead(lead, github_token=token)
            out["verify_lead"] = {"outcome": "RETURNED", "result": result}
        except VerificationDenied as exc:
            out["verify_lead"] = {"outcome": "DENIED", "message": str(exc),
                                  "cause": type(exc.__cause__).__name__ if exc.__cause__ else None}
    out["consumed_response"] = summarize_consumed(obs.capture)
    out["network_call_made"] = "request_url" in obs.capture
    if out["network_call_made"] and probe.get("fetch_independent", True) and type(run_id) is int and run_id > 0:
        second = fetch_independent(run_id, token)
        out["independent_fetch"] = second
        out["consumed_matches_independent_fetch"] = (
            second.get("response_sha256") is not None
            and second.get("response_sha256") == out["consumed_response"].get("response_sha256"))
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
        "schema": "humanaios.acat-r.live-verify-lead-probe.v0.2",
        "entry_point": "tools/gner_verify_e1.py::verify_lead",
        "entry_point_verified_unmodified": all(v["verified"] for v in SOURCE_PINS.values()),
        "source_pins": SOURCE_PINS,
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
    for p in receipts["probes"]:
        vl = p["verify_lead"]
        print(p["probe_id"], vl["outcome"], vl.get("result", {}).get("state") or vl.get("message"),
              p["consumed_response"].get("response_sha256", "-")[:16],
              "match2nd=" + str(p.get("consumed_matches_independent_fetch")), sep=" | ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
