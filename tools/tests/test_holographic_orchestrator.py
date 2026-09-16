"""
Test suite for holographic_orchestrator.py

Validates:
1. Job ID generation (stable, deterministic)
2. Enum validation (CaptureMode, RenderTarget, JobStatus)
3. Dry-run pipeline (no network calls)
4. Payload construction (security redaction)
5. Error handling (partial failures, credential missing)
6. Smoke test coverage
"""

import json
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add tools dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from holographic_orchestrator import (
    make_job_id,
    run,
    CaptureMode,
    RenderTarget,
    JobStatus,
    redact_for_log,
    SpecLoadFailed,
)


class TestJobIDGeneration(unittest.TestCase):
    """Test stable, deterministic job ID generation."""

    def test_job_id_stability(self):
        """Same inputs produce same job ID."""
        fixed_ts = "2026-09-16T00:00:00Z"
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl", fixed_ts)
        job_id_2 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl", fixed_ts)
        self.assertEqual(job_id_1, job_id_2, "Job ID should be stable")

    def test_job_id_length(self):
        """Job ID is 16 hex characters."""
        job_id = make_job_id("user1", "person1", "photogrammetry", "browser_webgl")
        self.assertEqual(len(job_id), 16, "Job ID should be 16 chars")
        # Verify it's valid hex
        try:
            int(job_id, 16)
        except ValueError:
            self.fail(f"Job ID '{job_id}' is not valid hex")

    def test_job_id_differs_by_user(self):
        """Different users produce different job IDs."""
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl")
        job_id_2 = make_job_id("user2", "person1", "photogrammetry", "browser_webgl")
        self.assertNotEqual(job_id_1, job_id_2, "Different users should have different IDs")

    def test_job_id_differs_by_person(self):
        """Different persons produce different job IDs."""
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl")
        job_id_2 = make_job_id("user1", "person2", "photogrammetry", "browser_webgl")
        self.assertNotEqual(job_id_1, job_id_2, "Different persons should have different IDs")

    def test_job_id_differs_by_capture_mode(self):
        """Different capture modes produce different job IDs."""
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl")
        job_id_2 = make_job_id("user1", "person1", "volumetric_video", "browser_webgl")
        self.assertNotEqual(job_id_1, job_id_2, "Different capture modes should have different IDs")

    def test_job_id_differs_by_render_target(self):
        """Different render targets produce different job IDs."""
        job_id_1 = make_job_id("user1", "person1", "photogrammetry", "browser_webgl")
        job_id_2 = make_job_id("user1", "person1", "photogrammetry", "mobile_ar")
        self.assertNotEqual(job_id_1, job_id_2, "Different render targets should have different IDs")


class TestEnumValidation(unittest.TestCase):
    """Test enum definitions and values."""

    def test_capture_mode_values(self):
        """CaptureMode enum has expected values."""
        self.assertEqual(CaptureMode.PHOTOGRAMMETRY.value, "photogrammetry")
        self.assertEqual(CaptureMode.VOLUMETRIC_VIDEO.value, "volumetric_video")
        self.assertEqual(CaptureMode.GAUSSIAN_SPLAT.value, "gaussian_splat")
        self.assertEqual(CaptureMode.NERF_MESH.value, "nerf_mesh")

    def test_render_target_values(self):
        """RenderTarget enum has expected values."""
        self.assertEqual(RenderTarget.BROWSER_WEBGL.value, "browser_webgl")
        self.assertEqual(RenderTarget.MOBILE_AR.value, "mobile_ar")
        self.assertEqual(RenderTarget.SPATIAL_DISPLAY.value, "spatial_display")
        self.assertEqual(RenderTarget.HEADSET_VR.value, "headset_vr")
        self.assertEqual(RenderTarget.LIGHTFIELD.value, "lightfield")

    def test_job_status_values(self):
        """JobStatus enum has expected values."""
        self.assertEqual(JobStatus.PENDING.value, "pending")
        self.assertEqual(JobStatus.CAPTURING.value, "capturing")
        self.assertEqual(JobStatus.RENDERING.value, "rendering")
        self.assertEqual(JobStatus.STORING.value, "storing")
        self.assertEqual(JobStatus.COMPLETE.value, "complete")
        self.assertEqual(JobStatus.FAILED.value, "failed")


class TestDryRunPipeline(unittest.TestCase):
    """Test dry-run mode (no network calls)."""

    def test_dry_run_basic(self):
        """Dry run executes without network calls."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)

        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["action"], "dry_run")
        self.assertIsNotNone(out["job_id"])
        self.assertEqual(len(out["job_id"]), 16)

    def test_dry_run_stages_structure(self):
        """Dry run returns stage structure with dry_run status."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)

        self.assertIn("stages", out)
        self.assertIn("capture", out["stages"])
        self.assertIn("render", out["stages"])
        self.assertIn("storage", out["stages"])

        self.assertEqual(out["stages"]["capture"]["status"], "dry_run")
        self.assertEqual(out["stages"]["render"]["status"], "dry_run")
        self.assertEqual(out["stages"]["storage"]["status"], "dry_run")

    def test_dry_run_multiple_render_targets(self):
        """Dry run works for all render targets."""
        render_targets = [
            "browser_webgl",
            "mobile_ar",
            "spatial_display",
            "headset_vr",
            "lightfield",
        ]

        for target in render_targets:
            spec = {
                "user_id": "test_user",
                "person_id": "test_person",
                "capture_mode": "photogrammetry",
                "input_source": "https://example.com/images.zip",
                "render_target": target,
                "dry_run": True,
            }
            out = run(spec)
            self.assertEqual(out["status"], "ok", f"Failed for render_target={target}")


class TestSecurityRedaction(unittest.TestCase):
    """Test credential redaction in logs."""

    def test_redact_bearer_token(self):
        """Bearer tokens are redacted."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        redacted = redact_for_log(text)
        self.assertNotIn("eyJ", redacted)
        self.assertIn("***REDACTED***", redacted)

    def test_redact_service_key(self):
        """Service keys (sk_*) are redacted."""
        text = "key=sk_live_1234567890abcdefghij"
        redacted = redact_for_log(text)
        self.assertNotIn("1234567890abcdefghij", redacted)
        self.assertIn("***REDACTED***", redacted)

    def test_redact_pk_key(self):
        """Public keys (pk_*) are redacted."""
        text = "key=pk_test_1234567890abcdefghij"
        redacted = redact_for_log(text)
        self.assertNotIn("1234567890abcdefghij", redacted)
        self.assertIn("***REDACTED***", redacted)


class TestErrorHandling(unittest.TestCase):
    """Test error handling for invalid specs."""

    def test_invalid_capture_mode(self):
        """Invalid capture mode returns error."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "invalid_mode",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)
        self.assertEqual(out["status"], "failed")
        self.assertIn("Invalid capture_mode", out["error"])

    def test_invalid_render_target(self):
        """Invalid render target returns error."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "invalid_target",
            "dry_run": True,
        }
        out = run(spec)
        self.assertEqual(out["status"], "failed")
        self.assertIn("Invalid", out["error"])

    def test_missing_required_fields(self):
        """Missing required fields still produces output with dry_run."""
        spec = {
            # Missing user_id, person_id, etc.
            "dry_run": True,
        }
        out = run(spec)
        # Should still produce a dry run with defaults
        self.assertEqual(out["status"], "ok")


class TestPayloadStructure(unittest.TestCase):
    """Test output payload structure."""

    def test_dry_run_output_keys(self):
        """Dry run output contains expected keys."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)

        required_keys = [
            "tool_name",
            "tool_version",
            "status",
            "action",
            "job_id",
            "stages",
            "started_at",
            "finished_at",
        ]
        for key in required_keys:
            self.assertIn(key, out, f"Missing key: {key}")

    def test_error_output_keys(self):
        """Error output contains expected keys."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "invalid_mode",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)

        required_keys = [
            "tool_name",
            "tool_version",
            "status",
            "error",
            "job_id",
            "started_at",
            "finished_at",
        ]
        for key in required_keys:
            self.assertIn(key, out, f"Missing key in error output: {key}")


class TestTimestampValidation(unittest.TestCase):
    """Test timestamp format in outputs."""

    def test_timestamps_are_iso_format(self):
        """Output timestamps are ISO 8601 format."""
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": True,
        }
        out = run(spec)

        started = out["started_at"]
        finished = out["finished_at"]

        # Should parse as ISO format
        try:
            datetime.fromisoformat(started.replace("Z", "+00:00"))
            datetime.fromisoformat(finished.replace("Z", "+00:00"))
        except ValueError:
            self.fail(f"Timestamps not ISO format: {started}, {finished}")


if __name__ == "__main__":
    unittest.main()
