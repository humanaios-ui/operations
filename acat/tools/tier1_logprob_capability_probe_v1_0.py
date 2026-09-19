#!/usr/bin/env python3
"""
Tier 1 Logprob Capability Probe — v1.0
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Checks, per provider, whether logprobs (or an equivalent confidence
signal) are exposed via standard API access, and at what granularity.
This is the concrete first step of WHITEBOX_RESEARCH_TIER_PROPOSAL_Z1.md
Section 2.

HONEST REACHABILITY NOTE, not a hedge -- a real constraint of the
environment this was authored in: this sandbox's network egress
allowlist includes api.anthropic.com but not api.openai.com,
generativelanguage.googleapis.com, api.x.ai, or other provider
endpoints. Credentials alone do not fix this -- a probe against those
providers needs to run in an environment whose network policy permits
the call, which may not be this sandbox even after Night supplies
credentials. PROVIDER_REACHABILITY below encodes this explicitly so a
failed probe is legible as a network-policy fact, not misread as "that
provider doesn't support logprobs."

Reads credentials from environment variables, same convention as
supabase_corpus_connector_v1_0.py and z2_queue_v1_1.py -- never as a
CLI argument, never logged, never printed.
"""
import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "tier1_logprob_capability_probe"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

# Explicit, not inferred -- updated as this sandbox's egress allowlist
# changes. A provider missing here is UNKNOWN, not assumed reachable.
PROVIDER_REACHABILITY = {
    "anthropic": {"host": "api.anthropic.com", "reachable_in_this_sandbox": True},
    "openai": {"host": "api.openai.com", "reachable_in_this_sandbox": False},
    "google": {"host": "generativelanguage.googleapis.com", "reachable_in_this_sandbox": False},
    "xai": {"host": "api.x.ai", "reachable_in_this_sandbox": False},
}

TIER_LEVELS = ["none", "top1_only", "top_n", "full_vocab", "unreachable_from_here"]


class SpecLoadFailed(Exception):
    pass


class CredentialMissing(Exception):
    """Raised when a probe is attempted without the required env var
    set. Never falls back to a placeholder credential or a skipped-
    but-reported-as-passed state -- same enforcement philosophy as
    z2_queue_v1_1.py's hard gate on zone2_ratification."""
    pass


def get_credential(provider: str) -> str:
    env_var = f"{provider.upper()}_API_KEY"
    val = os.environ.get(env_var)
    if not val:
        raise CredentialMissing(
            f"{env_var} not set. This probe will not run with a "
            f"placeholder or skip silently -- it refuses until the "
            f"real credential is present."
        )
    return val


def _find_logprob_key_paths(obj, path="") -> list:
    """
    Recursively walks actual JSON structure looking for keys matching
    known logprob-related field names ('logprobs', 'top_logprobs',
    'logprobsResult' for Gemini-family). Returns the real key paths
    found, e.g. ['choices[0].logprobs.top_logprobs'] -- structural
    evidence, not a substring match on serialized text. A response
    where the model merely talks ABOUT logprobs in prose produces zero
    hits here, correctly.
    """
    LOGPROB_KEY_NAMES = {"logprobs", "top_logprobs", "logprobsresult"}
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if k.lower() in LOGPROB_KEY_NAMES:
                found.append(new_path)
            found.extend(_find_logprob_key_paths(v, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(_find_logprob_key_paths(item, f"{path}[{i}]"))
    return found


def probe_anthropic(api_key: str, test_prompt: str = "Say the word: probe") -> dict:
    """
    Real, functional probe against api.anthropic.com -- reachable in
    this sandbox right now. Checks whether the /v1/messages endpoint
    accepts a request shape that would return log-probability-adjacent
    signal. NOTE: as of this tool's authorship, standard Claude API
    message completions do not expose per-token logprobs the way some
    OpenAI-compatible completion endpoints do -- this probe's real job
    is confirming that fact directly against the live API rather than
    assuming it from documentation, per IC-032 discipline (query live
    state, don't assume).
    """
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-5",
        "max_tokens": 16,
        "messages": [{"role": "user", "content": test_prompt}],
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
            # STRUCTURAL check, not substring grep -- a model response
            # that merely discusses the word "logprobs" in prose text
            # must not trigger a false positive here. Recursively walk
            # actual key paths rather than searching the serialized
            # string, per the one legitimate critique surfaced this
            # session (independent of the fabricated claims it arrived
            # alongside).
            logprob_key_paths = _find_logprob_key_paths(body)
            tier = "top_n" if logprob_key_paths else "none"
            return {
                "provider": "anthropic",
                "reachable": True,
                "call_succeeded": True,
                "logprob_key_paths_found": logprob_key_paths,
                "tier": tier,
                "raw_response_keys": list(body.keys()) if isinstance(body, dict) else None,
            }
    except urllib.error.HTTPError as e:
        return {
            "provider": "anthropic",
            "reachable": True,
            "call_succeeded": False,
            "http_status": e.code,
            "error": e.read().decode()[:500],
            "tier": None,
        }
    except urllib.error.URLError as e:
        return {
            "provider": "anthropic",
            "reachable": False,
            "call_succeeded": False,
            "error": str(e.reason),
            "tier": "unreachable_from_here",
        }


def probe_provider(provider: str, test_prompt: str = "Say the word: probe") -> dict:
    """
    Router. For providers not reachable from this sandbox, returns an
    honest 'unreachable_from_here' result WITHOUT attempting the call
    and without requiring the credential -- there's no point demanding
    a secret for a call that network policy will block regardless.
    """
    meta = PROVIDER_REACHABILITY.get(provider)
    if meta is None:
        return {
            "provider": provider,
            "reachable": None,
            "tier": None,
            "note": "Provider not in PROVIDER_REACHABILITY -- unknown, "
                    "not assumed reachable or unreachable. Add an entry "
                    "before probing.",
        }
    if not meta["reachable_in_this_sandbox"]:
        return {
            "provider": provider,
            "reachable": False,
            "call_succeeded": None,
            "tier": "unreachable_from_here",
            "note": f"{meta['host']} is not in this sandbox's network "
                    f"egress allowlist. This must run in an environment "
                    f"whose policy permits it (Night's own tooling, or "
                    f"an MCP connector with provider access) -- not a "
                    f"credential problem.",
        }

    if provider == "anthropic":
        api_key = get_credential(provider)  # raises CredentialMissing if absent
        return probe_anthropic(api_key, test_prompt)

    return {
        "provider": provider,
        "reachable": True,
        "tier": None,
        "note": f"{provider} is marked reachable but has no probe "
                f"function implemented yet -- add one before use.",
    }


def run_all(providers: list, test_prompt: str = "Say the word: probe") -> dict:
    results = []
    for p in providers:
        try:
            results.append(probe_provider(p, test_prompt))
        except CredentialMissing as e:
            results.append({
                "provider": p,
                "reachable": PROVIDER_REACHABILITY.get(p, {}).get("reachable_in_this_sandbox"),
                "tier": None,
                "error": "CREDENTIAL_MISSING",
                "note": str(e),
            })
    return {"results": results}


def aggregate(run_result: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


# ── Smoke test (no live credentials required) ──────────────────────────────

def run_smoke_test() -> bool:
    try:
        # Test 1: unreachable providers return the honest unreachable
        # result WITHOUT raising CredentialMissing -- no point demanding
        # a secret for a blocked-by-policy call.
        r1 = probe_provider("openai")
        assert r1["reachable"] is False
        assert r1["tier"] == "unreachable_from_here"
        assert "note" in r1

        # Test 2: unknown provider is UNKNOWN, not silently treated as
        # reachable or unreachable.
        r2 = probe_provider("some_new_provider_not_yet_added")
        assert r2["reachable"] is None

        # Test 3: reachable provider (anthropic) with NO credential set
        # raises CredentialMissing rather than silently skipping or
        # returning a fake success.
        # (Ensure the env var really isn't set for this test run.)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        raised = False
        try:
            probe_provider("anthropic")
        except CredentialMissing:
            raised = True
        assert raised, "must raise CredentialMissing, not skip silently"

        # Test 4: run_all catches CredentialMissing per-provider and
        # reports it in-line rather than crashing the whole batch.
        batch = run_all(["anthropic", "openai"])
        anthropic_result = next(r for r in batch["results"] if r["provider"] == "anthropic")
        assert anthropic_result.get("error") == "CREDENTIAL_MISSING"
        openai_result = next(r for r in batch["results"] if r["provider"] == "openai")
        assert openai_result["tier"] == "unreachable_from_here"

        print("✓ Smoke test PASSED (no live credentials required for this test)")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Tier 1 Logprob Capability Probe v1.0")
    parser.add_argument("--providers", nargs="+", default=list(PROVIDER_REACHABILITY.keys()))
    parser.add_argument("--output-dir", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    run_result = run_all(args.providers)
    output = aggregate(run_result, "live_probe")
    report_path = write_report(output, args.output_dir)
    print(json.dumps(output, indent=2))
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
