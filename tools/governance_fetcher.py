"""
HumanAIOS — Governance Fetcher (Zone 1)

Fetches GOVERNANCE.md and SESSION_RITUALS.md from GitHub raw content.
Exposes them as MCP resources:
  - governance://current
  - rituals://current
  - governance://sha/{sha}

Local file fallback: if GitHub is unreachable, falls back to
GOVERNANCE_LOCAL_PATH / RITUALS_LOCAL_PATH if configured and present.

CLI:
  python governance_fetcher.py --input fixture.json --report out.json
  python governance_fetcher.py --smoke
MCP:
  fastmcp run governance_fetcher.py --serve
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Builder v1.7 compliant
# ---------------------------------------------------------------------------
TOOL_NAME = "governance_fetcher"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "governance"
TOOL_SESSION = "S-052326-03"

# ---------------------------------------------------------------------------
# Configuration (override via env)
# ---------------------------------------------------------------------------
GOVERNANCE_RAW_URL = os.getenv(
    "GOVERNANCE_RAW_URL",
    "https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md",
)
RITUALS_RAW_URL = os.getenv(
    "RITUALS_RAW_URL",
    "https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md",
)
GITHUB_USER_AGENT = os.getenv("GITHUB_USER_AGENT", "humanaios-governance/1.2")
FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 min default

# Local fallback paths (optional — used when GitHub is unreachable)
GOVERNANCE_LOCAL_PATH = os.getenv("GOVERNANCE_LOCAL_PATH", "")
RITUALS_LOCAL_PATH = os.getenv("RITUALS_LOCAL_PATH", "")

# ---------------------------------------------------------------------------
# Module-level TTL cache: uri -> (cached_at_epoch, content)
# ---------------------------------------------------------------------------
_cache: dict[str, tuple[float, str]] = {}

# ---------------------------------------------------------------------------
# Required env vars for live network calls (validate_env warns if missing)
# ---------------------------------------------------------------------------
_REQUIRED_ENV_LIVE = ["GOVERNANCE_RAW_URL", "RITUALS_RAW_URL"]


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------
def redact_for_log(s: str) -> str:
    """Replace any Supabase key or Slack webhook value with ***REDACTED***."""
    # Supabase service_role / anon keys (eyJ… JWTs or sb_… prefixed)
    s = re.sub(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***REDACTED***", s)
    s = re.sub(r"sb_[A-Za-z0-9_\-]{20,}", "***REDACTED***", s)
    # Slack webhook URL path tokens
    s = re.sub(
        r"hooks\.slack\.com/services/[A-Za-z0-9/]+",
        "hooks.slack.com/services/***REDACTED***",
        s,
    )
    return s


# ---------------------------------------------------------------------------
# Startup env validation (warns only — never raises, never exits)
# ---------------------------------------------------------------------------
def validate_env() -> None:
    """
    Check required env vars. Print WARNING to stderr if any are missing.
    Values are never printed. Safe to call at import time.
    """
    missing = [v for v in _REQUIRED_ENV_LIVE if not os.getenv(v)]
    if missing:
        print(
            f"[{TOOL_NAME}] WARNING: missing env vars: {', '.join(missing)}. "
            "Live GitHub fetch may fail; local fallback will be used if configured.",
            file=sys.stderr,
        )


validate_env()


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


class FetchFailed(Exception):
    """Raised when GitHub raw fetch fails."""


# ---------------------------------------------------------------------------
# Input / output helpers
# ---------------------------------------------------------------------------
def load_input(path: str | None) -> dict:
    """Load input spec from JSON file or stdin."""
    if path is None or path == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.isfile(path):
            raise SpecLoadFailed(f"Input file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    if not raw.strip():
        raise SpecLoadFailed("Empty input")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Invalid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return spec


def write_report(out: dict, path: str) -> None:
    """Write report JSON atomically."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, path)


def print_summary(out: dict) -> None:
    """Human-readable summary to stderr (safe for MCP stdio)."""
    status = out.get("status", "UNKNOWN")
    source = out.get("source", "?")
    print(f"[{TOOL_NAME} v{TOOL_VERSION}] status={status} source={source}",
          file=sys.stderr)


# ---------------------------------------------------------------------------
# Core fetch logic (stdlib urllib, no external deps)
# ---------------------------------------------------------------------------
def _fetch_url(url: str, timeout: int = FETCH_TIMEOUT) -> str:
    """Blocking fetch using stdlib urllib."""
    req = urllib.request.Request(url, headers={
        "User-Agent": GITHUB_USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return data.decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise FetchFailed(
            f"HTTP {exc.code} for {redact_for_log(url)}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise FetchFailed(f"URL error for {redact_for_log(url)}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise FetchFailed(f"Timeout fetching {redact_for_log(url)}: {exc}") from exc
    except OSError as exc:
        raise FetchFailed(f"Network error for {redact_for_log(url)}: {exc}") from exc


def _read_local_fallback(local_path: str) -> str | None:
    """Read a local fallback file if it exists. Returns None if not found."""
    if local_path and os.path.isfile(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def fetch_with_cache(url: str, cache_key: str, local_path: str = "") -> dict[str, Any]:
    """
    Fetch with module-level TTL cache and local fallback.

    Returns:
        dict with keys: content (str), source (str)
        source is one of: "github_raw", "cache", "local_fallback", "unavailable"
    """
    now = datetime.now(timezone.utc).timestamp()
    cached_at, content = _cache.get(cache_key, (0.0, ""))
    if content and now - cached_at < CACHE_TTL_SECONDS:
        return {"content": content, "source": "cache"}

    try:
        content = _fetch_url(url)
        _cache[cache_key] = (now, content)
        return {"content": content, "source": "github_raw"}
    except FetchFailed as exc:
        # Try local fallback
        local_content = _read_local_fallback(local_path)
        if local_content is not None:
            print(
                f"[{TOOL_NAME}] WARNING: GitHub fetch failed ({exc}); "
                f"using local fallback: {local_path}",
                file=sys.stderr,
            )
            return {"content": local_content, "source": "local_fallback"}
        # No fallback available — return degraded result dict
        return {"content": None, "source": "unavailable", "error": str(exc)}


# ---------------------------------------------------------------------------
# Core business logic
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Fetch governance documents.

    Args:
        spec: Input spec. Supported keys:
            - doc: "governance" | "rituals" | "both" (default: "both")
            - use_cache: bool (default: true)

    Returns:
        Result dict with status, documents, source info.
    """
    started = datetime.now(timezone.utc).isoformat()
    doc = spec.get("doc", "both")
    use_cache = spec.get("use_cache", True)

    result: dict[str, Any] = {"documents": {}}

    docs_to_fetch: list[tuple[str, str, str]] = []
    if doc in ("governance", "both"):
        docs_to_fetch.append(("governance", GOVERNANCE_RAW_URL, GOVERNANCE_LOCAL_PATH))
    if doc in ("rituals", "both"):
        docs_to_fetch.append(("rituals", RITUALS_RAW_URL, RITUALS_LOCAL_PATH))

    overall_source = "github_raw"

    for name, url, local_path in docs_to_fetch:
        if use_cache:
            fetch_result = fetch_with_cache(url, name, local_path)
        else:
            # Bypass cache but still apply fallback logic
            try:
                content = _fetch_url(url)
                fetch_result = {"content": content, "source": "github_raw"}
            except FetchFailed as exc:
                local_content = _read_local_fallback(local_path)
                if local_content is not None:
                    print(
                        f"[{TOOL_NAME}] WARNING: GitHub fetch failed ({exc}); "
                        f"using local fallback: {local_path}",
                        file=sys.stderr,
                    )
                    fetch_result = {"content": local_content, "source": "local_fallback"}
                else:
                    fetch_result = {"content": None, "source": "unavailable", "error": str(exc)}

        src = fetch_result.get("source", "unavailable")
        if src in ("local_fallback", "unavailable") and overall_source == "github_raw":
            overall_source = src

        if fetch_result.get("content") is not None:
            result["documents"][name] = {
                "url": url,
                "length": len(fetch_result["content"]),
                "content": fetch_result["content"],
                "source": src,
            }
        else:
            result["documents"][name] = {
                "url": url,
                "error": fetch_result.get("error", "unavailable"),
                "source": src,
            }

    result["source"] = overall_source

    # Determine overall status
    errors = [v for v in result["documents"].values() if "error" in v]
    if not errors:
        status = "ok"
    elif len(errors) == len(docs_to_fetch):
        status = "failed"
    else:
        status = "partial"

    finished = datetime.now(timezone.utc).isoformat()
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": status,
        "started_at": started,
        "finished_at": finished,
        **result,
    }


def aggregate(results: list[dict]) -> dict:
    """Aggregate multiple run results."""
    statuses = [r.get("status") for r in results]
    ok_count = statuses.count("ok")
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "aggregate": True,
        "total": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Validate with local fallback content (no network needed)."""
    try:
        # Test 1: cache pre-seed path → source="cache"
        _cache["governance"] = (
            datetime.now(timezone.utc).timestamp(),
            "# Test Governance\n\n- Rule 1: Test\n",
        )
        _cache["rituals"] = (
            datetime.now(timezone.utc).timestamp(),
            "# Test Rituals\n\n- Ritual 1: Test\n",
        )
        sample = {"doc": "both", "use_cache": True}
        out = run(sample)
        assert out.get("status") == "ok", f"Unexpected status: {out.get('status')}"
        assert "documents" in out, "Missing documents"
        assert out["documents"]["governance"]["source"] == "cache", "Expected cache source"

        # Test 2: bad URL + local fallback → source="local_fallback"
        # Write a temp fallback file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write("# Fallback Governance\n")
            tmp_path = tmp.name

        try:
            # Force cache miss
            if "governance_fallback_test" in _cache:
                del _cache["governance_fallback_test"]

            fetch_result = fetch_with_cache(
                "https://invalid.example.invalid/GOVERNANCE.md",
                "governance_fallback_test",
                local_path=tmp_path,
            )
            assert fetch_result["source"] == "local_fallback", (
                f"Expected local_fallback, got {fetch_result['source']}"
            )
            assert "Fallback" in fetch_result["content"]
        finally:
            import os as _os
            _os.unlink(tmp_path)

        # Test 3: bad URL + no fallback → source="unavailable" (no raise)
        fetch_result_no_fallback = fetch_with_cache(
            "https://invalid.example.invalid/SESSION_RITUALS.md",
            "rituals_fallback_test",
            local_path="",
        )
        assert fetch_result_no_fallback["source"] == "unavailable", (
            f"Expected unavailable, got {fetch_result_no_fallback['source']}"
        )
        assert "error" in fetch_result_no_fallback

        print("[smoke] PASSED", file=sys.stderr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# MCP surface — Resources
# ---------------------------------------------------------------------------
from fastmcp import FastMCP  # noqa: E402

mcp = FastMCP(TOOL_NAME)


@mcp.resource(
    "governance://current",
    mime_type="text/markdown",
    name="Current Governance",
    description="Latest GOVERNANCE.md from GitHub (humanaios-ui/operations)",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def get_governance() -> str:
    """Return current governance document."""
    def _fetch() -> str:
        result = fetch_with_cache(GOVERNANCE_RAW_URL, "governance", GOVERNANCE_LOCAL_PATH)
        return result.get("content") or f"<!-- unavailable: {result.get('error', 'unknown')} -->"
    return await asyncio.to_thread(_fetch)


@mcp.resource(
    "rituals://current",
    mime_type="text/markdown",
    name="Current Session Rituals",
    description="Latest SESSION_RITUALS.md from GitHub (humanaios-ui/operations)",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def get_rituals() -> str:
    """Return current rituals document."""
    def _fetch() -> str:
        result = fetch_with_cache(RITUALS_RAW_URL, "rituals", RITUALS_LOCAL_PATH)
        return result.get("content") or f"<!-- unavailable: {result.get('error', 'unknown')} -->"
    return await asyncio.to_thread(_fetch)


@mcp.resource(
    "governance://sha/{sha}",
    mime_type="text/markdown",
    name="Governance at SHA",
    description="Pinned GOVERNANCE.md at a specific commit SHA",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def get_governance_at_sha(sha: str) -> str:
    """Return governance at a specific commit SHA."""
    # Replace /main/ with /{sha}/ — works for humanaios-ui/operations canonical URL
    url = GOVERNANCE_RAW_URL.replace("/main/", f"/{sha}/")

    def _fetch() -> str:
        try:
            return _fetch_url(url)
        except FetchFailed as exc:
            return f"<!-- fetch failed: {exc} -->"
    return await asyncio.to_thread(_fetch)


@mcp.tool(name=TOOL_NAME, description="Fetch governance and rituals documents from GitHub.")
def governance_fetcher(spec: dict) -> dict:
    """MCP tool wrapper around run()."""
    return run(spec)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    p.add_argument("--input", required=False, help="Path to input JSON (default: stdin)")
    p.add_argument("--smoke", action="store_true", help="Run smoke test and exit")
    p.add_argument("--serve", action="store_true", help="Run as MCP server over stdio")
    p.add_argument("--report", default=f"reports/{TOOL_NAME}.json", help="Report output path")
    args = p.parse_args()

    if args.serve:
        mcp.run()
        return

    if args.smoke:
        sys.exit(0 if run_smoke_test() else 1)

    spec = load_input(args.input)
    out = run(spec)
    write_report(out, args.report)
    print_summary(out)


if __name__ == "__main__":
    main()
