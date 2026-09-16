"""
HumanAIOS — Holographic Orchestrator (Zone 1)
Builder v1.7 compliant

Orchestrates holographic person representation via external services:
- Capture: photogrammetry/volumetric input (Polycam, Matterport, etc.)
- Render: neural radiance fields (Replicate, RunwayML, etc.)
- Display: volumetric output targets (AR/VR platforms, browsers)

Follows supabase_logger/slack_notifier pattern:
  - Env-based config + security redaction
  - Idempotent upsert + retry/backoff
  - MCP + CLI dual surface
  - Smoke test (no network required)

CLI:
  python holographic_orchestrator.py --input spec.json --report out.json
  python holographic_orchestrator.py --smoke
MCP:
  fastmcp run holographic_orchestrator.py --serve
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Literal
from enum import Enum

# ---------------------------------------------------------------------------
# Builder v1.7 compliant
# ---------------------------------------------------------------------------
TOOL_NAME = "holographic_orchestrator"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "capability_integration"
TOOL_SESSION = "S-091626-01"

# ---------------------------------------------------------------------------
# Configuration (override via env)
# ---------------------------------------------------------------------------
CAPTURE_SERVICE_URL = os.getenv("CAPTURE_SERVICE_URL", "")  # Polycam, Matterport API
CAPTURE_SERVICE_KEY = os.getenv("CAPTURE_SERVICE_KEY", "")
RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "")  # Replicate, RunwayML
RENDER_SERVICE_KEY = os.getenv("RENDER_SERVICE_KEY", "")
STORAGE_BUCKET_URL = os.getenv("STORAGE_BUCKET_URL", "")  # Supabase Storage
STORAGE_KEY = os.getenv("STORAGE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "holographic_jobs")

POST_TIMEOUT = int(os.getenv("POST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", "2.0"))

# ---------------------------------------------------------------------------
# Required env vars for live service calls
# ---------------------------------------------------------------------------
_REQUIRED_ENV_LIVE = [
    "CAPTURE_SERVICE_URL",
    "CAPTURE_SERVICE_KEY",
    "RENDER_SERVICE_URL",
    "RENDER_SERVICE_KEY",
]


# ---------------------------------------------------------------------------
# Enums for holographic pipeline stages
# ---------------------------------------------------------------------------
class CaptureMode(str, Enum):
    """Input mode for holographic capture."""
    PHOTOGRAMMETRY = "photogrammetry"  # Static point cloud
    VOLUMETRIC_VIDEO = "volumetric_video"  # Dynamic sequence
    GAUSSIAN_SPLAT = "gaussian_splat"  # Pre-computed splat
    NERF_MESH = "nerf_mesh"  # NeRF export


class RenderTarget(str, Enum):
    """Output target for holographic display."""
    BROWSER_WEBGL = "browser_webgl"  # Three.js, Babylon.js
    MOBILE_AR = "mobile_ar"  # ARCore, ARKit
    SPATIAL_DISPLAY = "spatial_display"  # Spatial Computing (Vision Pro, Magic Leap)
    HEADSET_VR = "headset_vr"  # VR headset (Meta Quest, Valve Index)
    LIGHTFIELD = "lightfield"  # Lightfield display (holographic)


class JobStatus(str, Enum):
    """Status of holographic rendering job."""
    PENDING = "pending"
    CAPTURING = "capturing"
    RENDERING = "rendering"
    STORING = "storing"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------
def redact_for_log(s: str) -> str:
    """Replace sensitive credential patterns with ***REDACTED*** before logging."""
    # API keys (JWT eyJ… or service_key patterns)
    s = re.sub(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", "***REDACTED***", s)
    s = re.sub(r"sk_[A-Za-z0-9_\-]{20,}", "***REDACTED***", s)
    s = re.sub(r"pk_[A-Za-z0-9_\-]{20,}", "***REDACTED***", s)
    # URL tokens
    s = re.sub(r"(apikey=)[A-Za-z0-9_\-\.]+", r"\1***REDACTED***", s)
    return s


# ---------------------------------------------------------------------------
# Startup env validation
# ---------------------------------------------------------------------------
def validate_env() -> None:
    """Check required env vars. Print WARNING to stderr if any are missing."""
    missing = [v for v in _REQUIRED_ENV_LIVE if not os.getenv(v)]
    if missing:
        print(
            f"[{TOOL_NAME}] WARNING: missing env vars: {', '.join(missing)}. "
            "Live holographic orchestration will fail; use dry_run=True for testing.",
            file=sys.stderr,
        )


validate_env()


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


class HolographicJobFailed(Exception):
    """Raised when holographic pipeline fails at any stage."""


class CaptureServiceError(HolographicJobFailed):
    """Raised when capture service call fails."""


class RenderServiceError(HolographicJobFailed):
    """Raised when render service call fails."""


class StorageServiceError(HolographicJobFailed):
    """Raised when storage call fails."""


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
    job_id = out.get("job_id", "?")
    final_status = out.get("final_status", "?")
    print(
        f"[{TOOL_NAME} v{TOOL_VERSION}] status={status} job_id={job_id} final_status={final_status}",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Job ID generation (stable, deterministic)
# ---------------------------------------------------------------------------
def make_job_id(
    user_id: str,
    person_id: str,
    capture_mode: str,
    render_target: str,
    timestamp: str | None = None,
) -> str:
    """Generate stable job ID for holographic capture+render."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    raw = f"{user_id}|{person_id}|{capture_mode}|{render_target}|{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Pipeline stage: Capture
# ---------------------------------------------------------------------------
def submit_capture_job(
    person_id: str,
    capture_mode: CaptureMode,
    input_source: str,  # URL or file path
    metadata: dict | None = None,
) -> dict:
    """
    Submit photogrammetry/volumetric capture job to external service.

    Args:
        person_id: Identifier for the person being captured
        capture_mode: CaptureMode enum
        input_source: URL or path to image sequence / video
        metadata: Optional metadata (lighting, calibration, etc.)

    Returns:
        {"capture_job_id": str, "status": str, "asset_url": str}

    Raises:
        CaptureServiceError
    """
    if not CAPTURE_SERVICE_URL:
        raise CaptureServiceError("CAPTURE_SERVICE_URL not configured")

    url = f"{CAPTURE_SERVICE_URL}/api/v1/jobs"
    key = CAPTURE_SERVICE_KEY
    if not key:
        raise CaptureServiceError("CAPTURE_SERVICE_KEY not configured")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "person_id": person_id,
        "capture_mode": capture_mode.value,
        "input_source": input_source,
        "metadata": metadata or {},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    # Retry with exponential backoff on 5xx errors
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=POST_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "capture_job_id": result.get("id"),
                    "status": result.get("status", "submitted"),
                    "asset_url": result.get("asset_url"),
                }
        except urllib.error.HTTPError as exc:
            # Retry on 5xx errors
            if 500 <= exc.code < 600 and attempt < max_retries:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                time.sleep(delay)
                continue
            body = exc.read().decode("utf-8", errors="replace")[:500]
            raise CaptureServiceError(
                f"Capture service HTTP {exc.code}: {redact_for_log(body)}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CaptureServiceError(f"Capture service request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Pipeline stage: Render
# ---------------------------------------------------------------------------
def submit_render_job(
    capture_job_id: str,
    render_target: RenderTarget,
    rendering_config: dict | None = None,
) -> dict:
    """
    Submit neural rendering job (NeRF/Gaussian Splat) to external service.

    Args:
        capture_job_id: ID from capture stage
        render_target: RenderTarget enum
        rendering_config: Optional config (quality, resolution, fps, etc.)

    Returns:
        {"render_job_id": str, "status": str, "model_url": str}

    Raises:
        RenderServiceError
    """
    if not RENDER_SERVICE_URL:
        raise RenderServiceError("RENDER_SERVICE_URL not configured")

    url = f"{RENDER_SERVICE_URL}/api/v1/jobs"
    key = RENDER_SERVICE_KEY
    if not key:
        raise RenderServiceError("RENDER_SERVICE_KEY not configured")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "input_job_id": capture_job_id,
        "render_target": render_target.value,
        "config": rendering_config or {
            "quality": "high",
            "resolution": 2048,
            "fps": 30,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=POST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "render_job_id": result.get("id"),
                "status": result.get("status", "submitted"),
                "model_url": result.get("model_url"),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RenderServiceError(
            f"Render service HTTP {exc.code}: {redact_for_log(body)}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RenderServiceError(f"Render service request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Pipeline stage: Storage + Metadata
# ---------------------------------------------------------------------------
def log_holographic_job(
    job_id: str,
    person_id: str,
    user_id: str,
    capture_job_id: str | None,
    render_job_id: str | None,
    status: JobStatus,
    assets: dict | None = None,
) -> dict:
    """
    Log holographic job metadata to Supabase.

    Args:
        job_id: Master job ID
        person_id: Person identifier
        user_id: User who initiated job
        capture_job_id: External capture job ID
        render_job_id: External render job ID
        status: JobStatus enum
        assets: Optional asset URLs dict

    Returns:
        {"row_id": str, "status": str}

    Raises:
        StorageServiceError
    """
    if not SUPABASE_URL:
        raise StorageServiceError("SUPABASE_URL not configured")

    url = (
        f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}"
        f"?on_conflict=job_id"
    )
    key = SUPABASE_KEY
    if not key:
        raise StorageServiceError("SUPABASE_KEY not configured")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }

    row = {
        "job_id": job_id,
        "person_id": person_id,
        "user_id": user_id,
        "capture_job_id": capture_job_id,
        "render_job_id": render_job_id,
        "status": status.value,
        "assets": assets or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    data = json.dumps([row]).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=POST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if isinstance(result, list) and len(result) > 0:
                return {"row_id": result[0].get("id"), "status": "logged"}
            return {"row_id": None, "status": "logged"}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise StorageServiceError(
            f"Storage HTTP {exc.code}: {redact_for_log(body)}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise StorageServiceError(f"Storage request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Core business logic: orchestrate full pipeline
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Orchestrate holographic capture + render + storage pipeline.

    Args:
        spec: Input spec with keys:
            - user_id: User initiating the capture
            - person_id: Identifier for person being captured
            - capture_mode: 'photogrammetry' | 'volumetric_video' | 'gaussian_splat' | 'nerf_mesh'
            - input_source: URL or path to input data
            - render_target: 'browser_webgl' | 'mobile_ar' | 'spatial_display' | 'headset_vr' | 'lightfield'
            - rendering_config: Optional rendering parameters
            - dry_run: if true, compute job_id without calling services

    Returns:
        Result dict with status, job_id, stages, final_assets.
    """
    started = datetime.now(timezone.utc).isoformat()
    dry_run = spec.get("dry_run", False)

    user_id = spec.get("user_id", "anonymous")
    person_id = spec.get("person_id", "unknown")
    capture_mode_str = spec.get("capture_mode", "photogrammetry")
    input_source = spec.get("input_source", "")
    render_target_str = spec.get("render_target", "browser_webgl")
    rendering_config = spec.get("rendering_config")

    try:
        capture_mode = CaptureMode(capture_mode_str)
        render_target = RenderTarget(render_target_str)
    except ValueError as exc:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "failed",
            "error": f"Invalid capture_mode or render_target: {exc}",
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "job_id": None,
        }

    # Generate job ID
    job_id = make_job_id(user_id, person_id, capture_mode_str, render_target_str)

    if dry_run:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "ok",
            "action": "dry_run",
            "job_id": job_id,
            "stages": {
                "capture": {"status": "dry_run", "job_id": None},
                "render": {"status": "dry_run", "job_id": None},
                "storage": {"status": "dry_run", "row_id": None},
            },
            "final_assets": None,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    stages: dict[str, Any] = {}
    final_assets: dict[str, Any] = {}

    try:
        # Stage 1: Submit capture job
        capture_result = submit_capture_job(
            person_id=person_id,
            capture_mode=capture_mode,
            input_source=input_source,
            metadata=spec.get("capture_metadata"),
        )
        capture_job_id = capture_result.get("capture_job_id")
        stages["capture"] = {
            "status": JobStatus.CAPTURING.value,
            "job_id": capture_job_id,
            "asset_url": capture_result.get("asset_url"),
        }
        final_assets["capture_asset"] = capture_result.get("asset_url")

        # Stage 2: Submit render job
        render_result = submit_render_job(
            capture_job_id=capture_job_id,
            render_target=render_target,
            rendering_config=rendering_config,
        )
        render_job_id = render_result.get("render_job_id")
        stages["render"] = {
            "status": JobStatus.RENDERING.value,
            "job_id": render_job_id,
            "model_url": render_result.get("model_url"),
        }
        final_assets["render_model"] = render_result.get("model_url")

        # Stage 3: Log to storage
        storage_result = log_holographic_job(
            job_id=job_id,
            person_id=person_id,
            user_id=user_id,
            capture_job_id=capture_job_id,
            render_job_id=render_job_id,
            status=JobStatus.COMPLETE,
            assets=final_assets,
        )
        stages["storage"] = {
            "status": JobStatus.STORING.value,
            "row_id": storage_result.get("row_id"),
        }

        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "ok",
            "job_id": job_id,
            "stages": stages,
            "final_assets": final_assets,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    except HolographicJobFailed as exc:
        # Log partial failure
        try:
            log_holographic_job(
                job_id=job_id,
                person_id=person_id,
                user_id=user_id,
                capture_job_id=stages.get("capture", {}).get("job_id"),
                render_job_id=stages.get("render", {}).get("job_id"),
                status=JobStatus.FAILED,
                assets=final_assets,
            )
        except Exception:  # noqa: BLE001
            pass  # Ignore logging failure on failure path

        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "failed",
            "job_id": job_id,
            "error": redact_for_log(str(exc)),
            "stages": stages,
            "final_assets": final_assets if final_assets else None,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Smoke test (no network required)
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Validate job ID generation, payload building, enum validation."""
    try:
        # Test 1: Job ID stability (with fixed timestamp)
        fixed_ts = "2026-09-16T00:00:00Z"
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl", fixed_ts)
        job_id_2 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl", fixed_ts)
        assert job_id_1 == job_id_2, f"Job ID not stable: {job_id_1} != {job_id_2}"
        assert len(job_id_1) == 16, f"Job ID should be 16 chars, got {len(job_id_1)}"

        # Test 2: Enum validation
        assert CaptureMode.PHOTOGRAMMETRY.value == "photogrammetry"
        assert RenderTarget.BROWSER_WEBGL.value == "browser_webgl"
        assert JobStatus.COMPLETE.value == "complete"

        # Test 3: Dry run mode
        sample = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(sample)
        assert out.get("status") == "ok", f"Unexpected status: {out.get('status')}"
        assert out.get("action") == "dry_run", f"Unexpected action: {out.get('action')}"
        assert len(out["job_id"]) == 16, "Job ID should be 16 hex chars"
        assert "stages" in out, "Missing stages in dry run"

        # Test 4: Redaction
        sample_key = "sk_FAKETEST_NOTREAL_abcdefghijklmnop"
        redacted = redact_for_log(f"key={sample_key}")
        assert sample_key not in redacted, "Service key not redacted"
        assert "***REDACTED***" in redacted, "Redaction marker missing"

        print("[smoke] PASSED", file=sys.stderr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# MCP surface (optional, loaded only if available)
# ---------------------------------------------------------------------------
mcp = None
try:
    from fastmcp import FastMCP  # noqa: E402

    mcp = FastMCP(TOOL_NAME)

    @mcp.tool(
        name=TOOL_NAME,
        description=(
            "Orchestrate holographic person representation via capture + render pipeline. "
            "Coordinates with external services (Polycam, Replicate, etc.). "
            "Returns job_id, stage status, and asset URLs. Use dry_run=True to test."
        ),
    )
    def holographic_orchestrator(spec: dict) -> dict:
        """MCP tool wrapper around run()."""
        return run(spec)
except ImportError:
    print(
        "[holographic_orchestrator] WARNING: FastMCP not available; MCP surface disabled. "
        "Use CLI interface instead.",
        file=sys.stderr,
    )


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
        if mcp is None:
            print("[holographic_orchestrator] ERROR: FastMCP not available; cannot run MCP server",
                  file=sys.stderr)
            sys.exit(1)
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
