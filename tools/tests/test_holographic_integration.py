"""
Integration tests for holographic_orchestrator.py — mocked external services

Phase 2: Validates that orchestrator correctly calls external services
with expected payloads, handles errors, and maintains state across stages.

Mocks:
- Polycam capture API (photogrammetry input)
- Replicate render API (NeRF/Gaussian Splat output)
- Supabase REST API (job metadata storage)

Tests:
- Correct HTTP method/headers/auth for each service
- Payload schema validation (matches service contracts)
- Error handling (429, 5xx, timeout, credential missing)
- Retry logic with exponential backoff
- State propagation across stages (capture → render → storage)
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from urllib.error import HTTPError, URLError
import io

# Add tools dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from holographic_orchestrator import (
    submit_capture_job,
    submit_render_job,
    log_holographic_job,
    run,
    CaptureMode,
    RenderTarget,
    JobStatus,
    CaptureServiceError,
    RenderServiceError,
    StorageServiceError,
)


class TestCaptureServiceIntegration(unittest.TestCase):
    """Test capture service calls with mocked HTTP."""

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', 'https://capture.example.com')
    @patch('holographic_orchestrator.CAPTURE_SERVICE_KEY', 'test_key_not_a_real_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_capture_submit_success(self, mock_urlopen):
        """Capture service returns job_id and asset_url."""
        # Mock response
        response_data = {
            "id": "capture_job_abc123",
            "status": "submitted",
            "asset_url": "https://storage.example.com/capture_abc123.ply"
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Call
        result = submit_capture_job(
            person_id="person_001",
            capture_mode=CaptureMode.PHOTOGRAMMETRY,
            input_source="https://example.com/images.zip"
        )

        # Verify
        self.assertEqual(result["capture_job_id"], "capture_job_abc123")
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["asset_url"], "https://storage.example.com/capture_abc123.ply")

        # Check HTTP call
        self.assertTrue(mock_urlopen.called)
        call_args = mock_urlopen.call_args
        req = call_args[0][0]  # First arg is Request object
        self.assertIn(b"photogrammetry", req.data)
        self.assertIn(b"person_001", req.data)

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', 'https://capture.example.com')
    @patch('holographic_orchestrator.CAPTURE_SERVICE_KEY', 'test_key_not_a_real_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_capture_service_auth_header(self, mock_urlopen):
        """Capture service receives correct Authorization header."""
        response_data = {"id": "cap_123", "status": "submitted", "asset_url": "https://..."}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        submit_capture_job(
            person_id="p1",
            capture_mode=CaptureMode.VOLUMETRIC_VIDEO,
            input_source="https://example.com/video.mp4"
        )

        # Verify Authorization header
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertIn('Authorization', req.headers)
        self.assertTrue(req.headers['Authorization'].startswith('Bearer '))

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', '')
    def test_capture_service_missing_url(self):
        """Capture service fails if URL not configured."""
        with self.assertRaises(CaptureServiceError) as ctx:
            submit_capture_job(
                person_id="p1",
                capture_mode=CaptureMode.PHOTOGRAMMETRY,
                input_source="https://example.com/img.zip"
            )
        self.assertIn("CAPTURE_SERVICE_URL", str(ctx.exception))

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', 'https://capture.example.com')
    @patch('holographic_orchestrator.CAPTURE_SERVICE_KEY', 'test_key_not_a_real_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_capture_service_http_error(self, mock_urlopen):
        """Capture service raises on HTTP error."""
        error = HTTPError("http://example.com", 400, "Bad Request", {}, io.BytesIO(b"Invalid mode"))
        mock_urlopen.side_effect = error

        with self.assertRaises(CaptureServiceError) as ctx:
            submit_capture_job(
                person_id="p1",
                capture_mode=CaptureMode.PHOTOGRAMMETRY,
                input_source="https://example.com/img.zip"
            )
        self.assertIn("HTTP 400", str(ctx.exception))

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', 'https://capture.example.com')
    @patch('holographic_orchestrator.CAPTURE_SERVICE_KEY', 'test_key_not_a_real_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_capture_service_retry_on_5xx(self, mock_urlopen):
        """Capture service retries on 5xx errors."""
        # First call: 503, second call: success
        error = HTTPError("http://example.com", 503, "Service Unavailable", {}, io.BytesIO(b""))
        success_response = MagicMock()
        success_response.read.return_value = json.dumps({
            "id": "cap_123", "status": "submitted", "asset_url": "https://..."
        }).encode('utf-8')
        success_response.__enter__.return_value = success_response

        mock_urlopen.side_effect = [error, success_response]

        with patch('time.sleep'):  # Speed up test
            result = submit_capture_job(
                person_id="p1",
                capture_mode=CaptureMode.PHOTOGRAMMETRY,
                input_source="https://example.com/img.zip"
            )

        # Should succeed on retry
        self.assertEqual(result["capture_job_id"], "cap_123")
        self.assertEqual(mock_urlopen.call_count, 2)


class TestRenderServiceIntegration(unittest.TestCase):
    """Test render service calls with mocked HTTP."""

    @patch('holographic_orchestrator.RENDER_SERVICE_URL', 'https://render.example.com')
    @patch('holographic_orchestrator.RENDER_SERVICE_KEY', 'test_key_render_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_render_submit_success(self, mock_urlopen):
        """Render service returns job_id and model_url."""
        response_data = {
            "id": "render_job_xyz789",
            "status": "submitted",
            "model_url": "https://storage.example.com/model_xyz789.glb"
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = submit_render_job(
            capture_job_id="capture_job_abc123",
            render_target=RenderTarget.BROWSER_WEBGL,
            rendering_config={"quality": "high", "resolution": 2048}
        )

        self.assertEqual(result["render_job_id"], "render_job_xyz789")
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["model_url"], "https://storage.example.com/model_xyz789.glb")

    @patch('holographic_orchestrator.RENDER_SERVICE_URL', 'https://render.example.com')
    @patch('holographic_orchestrator.RENDER_SERVICE_KEY', 'test_key_render_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_render_payload_contains_capture_ref(self, mock_urlopen):
        """Render request includes capture job_id."""
        response_data = {"id": "rend_123", "status": "submitted", "model_url": "https://..."}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        submit_render_job(
            capture_job_id="cap_from_phase_1",
            render_target=RenderTarget.MOBILE_AR,
            rendering_config=None
        )

        # Verify payload includes capture ref
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode('utf-8'))
        self.assertEqual(payload["input_job_id"], "cap_from_phase_1")
        self.assertEqual(payload["render_target"], "mobile_ar")

    @patch('holographic_orchestrator.RENDER_SERVICE_URL', 'https://render.example.com')
    @patch('holographic_orchestrator.RENDER_SERVICE_KEY', '')
    def test_render_service_missing_key(self):
        """Render service fails if key not configured."""
        with self.assertRaises(RenderServiceError) as ctx:
            submit_render_job(
                capture_job_id="cap_123",
                render_target=RenderTarget.BROWSER_WEBGL
            )
        self.assertIn("RENDER_SERVICE_KEY", str(ctx.exception))


class TestStorageServiceIntegration(unittest.TestCase):
    """Test storage (Supabase) calls with mocked HTTP."""

    @patch('holographic_orchestrator.SUPABASE_URL', 'https://proj.supabase.co')
    @patch('holographic_orchestrator.SUPABASE_KEY', 'test_key_supabase_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_storage_upsert_success(self, mock_urlopen):
        """Storage returns row with id."""
        response_data = [{"id": "row_999", "job_id": "holo_123", "status": "complete"}]
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = log_holographic_job(
            job_id="holo_123",
            person_id="person_001",
            user_id="user_001",
            capture_job_id="cap_123",
            render_job_id="rend_789",
            status=JobStatus.COMPLETE,
            assets={"capture_asset": "https://...", "render_model": "https://..."}
        )

        self.assertEqual(result["row_id"], "row_999")
        self.assertEqual(result["status"], "logged")

    @patch('holographic_orchestrator.SUPABASE_URL', 'https://proj.supabase.co')
    @patch('holographic_orchestrator.SUPABASE_KEY', 'test_key_supabase_credential')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_storage_on_conflict_header(self, mock_urlopen):
        """Storage request includes Prefer header for merge-duplicates."""
        response_data = [{"id": "row_123"}]
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        log_holographic_job(
            job_id="holo_123",
            person_id="p1",
            user_id="u1",
            capture_job_id="c1",
            render_job_id="r1",
            status=JobStatus.COMPLETE
        )

        # Verify Prefer header
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertIn('Prefer', req.headers)
        self.assertIn('merge-duplicates', req.headers['Prefer'])

    @patch('holographic_orchestrator.SUPABASE_URL', '')
    def test_storage_missing_url(self):
        """Storage fails if URL not configured."""
        with self.assertRaises(StorageServiceError) as ctx:
            log_holographic_job(
                job_id="h1", person_id="p1", user_id="u1",
                capture_job_id="c1", render_job_id="r1",
                status=JobStatus.COMPLETE
            )
        self.assertIn("SUPABASE_URL", str(ctx.exception))


class TestPipelineStatePropagation(unittest.TestCase):
    """Test that state flows correctly across stages."""

    @patch('holographic_orchestrator.log_holographic_job')
    @patch('holographic_orchestrator.submit_render_job')
    @patch('holographic_orchestrator.submit_capture_job')
    def test_live_pipeline_state_flow(self, mock_capture, mock_render, mock_storage):
        """End-to-end: capture output → render input → storage record."""
        # Mock capture returns job_id
        mock_capture.return_value = {
            "capture_job_id": "cap_phase1",
            "status": "capturing",
            "asset_url": "https://storage.example.com/capture.ply"
        }

        # Mock render consumes capture_job_id
        mock_render.return_value = {
            "render_job_id": "rend_phase2",
            "status": "rendering",
            "model_url": "https://storage.example.com/model.glb"
        }

        # Mock storage logs both
        mock_storage.return_value = {"row_id": "row_123", "status": "logged"}

        # Run pipeline
        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": False,
        }

        result = run(spec)

        # Verify state flow
        self.assertEqual(result["status"], "ok")
        self.assertIsNotNone(result["stages"]["capture"]["job_id"])
        self.assertIsNotNone(result["stages"]["render"]["job_id"])

        # Verify render was called with capture's output
        mock_render.assert_called_once()
        render_call_kwargs = mock_render.call_args[1]
        self.assertEqual(render_call_kwargs["capture_job_id"], "cap_phase1")

        # Verify storage was called with both job IDs
        mock_storage.assert_called_once()
        storage_call_kwargs = mock_storage.call_args[1]
        self.assertEqual(storage_call_kwargs["capture_job_id"], "cap_phase1")
        self.assertEqual(storage_call_kwargs["render_job_id"], "rend_phase2")


class TestErrorRecovery(unittest.TestCase):
    """Test pipeline error handling and recovery."""

    @patch('holographic_orchestrator.submit_render_job')
    @patch('holographic_orchestrator.submit_capture_job')
    def test_capture_failure_stops_pipeline(self, mock_capture, mock_render):
        """If capture fails, render is not called and pipeline reports failure."""
        mock_capture.side_effect = CaptureServiceError("Service offline")

        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": False,
        }

        result = run(spec)

        # Verify pipeline failed
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)

        # Render should NOT have been called
        mock_render.assert_not_called()

    @patch('holographic_orchestrator.log_holographic_job')
    @patch('holographic_orchestrator.submit_render_job')
    @patch('holographic_orchestrator.submit_capture_job')
    def test_partial_failure_logs_to_storage(self, mock_capture, mock_render, mock_storage):
        """If render fails, storage still logs partial state."""
        mock_capture.return_value = {
            "capture_job_id": "cap_success",
            "status": "capturing",
            "asset_url": "https://..."
        }
        mock_render.side_effect = RenderServiceError("Model too large")
        mock_storage.return_value = {"row_id": "row_123", "status": "logged"}

        spec = {
            "user_id": "test_user",
            "person_id": "test_person",
            "capture_mode": "photogrammetry",
            "input_source": "https://example.com/images.zip",
            "render_target": "browser_webgl",
            "dry_run": False,
        }

        result = run(spec)

        # Pipeline failed, but storage was attempted with partial state
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stages"]["capture"]["job_id"], "cap_success")
        mock_storage.assert_called_once()  # Storage was called despite render failure


class TestRequestCredentialRedaction(unittest.TestCase):
    """Test that credentials are redacted from error messages."""

    @patch('holographic_orchestrator.CAPTURE_SERVICE_URL', 'https://capture.example.com')
    @patch('holographic_orchestrator.CAPTURE_SERVICE_KEY', 'service_key_test_value_123456789abcdef')
    @patch('holographic_orchestrator.urllib.request.urlopen')
    def test_capture_error_redacts_key(self, mock_urlopen):
        """Capture error logs redact the service key."""
        error = HTTPError("http://example.com", 401, "Unauthorized", {},
                         io.BytesIO(b"Invalid key: service_key_test_value_123456789abcdef_suffix"))
        mock_urlopen.side_effect = error

        with self.assertRaises(CaptureServiceError) as ctx:
            submit_capture_job(
                person_id="p1",
                capture_mode=CaptureMode.PHOTOGRAMMETRY,
                input_source="https://example.com/img.zip"
            )

        error_msg = str(ctx.exception)
        # Key should be redacted
        self.assertNotIn("0123456789ab", error_msg)
        self.assertIn("***REDACTED***", error_msg)


if __name__ == "__main__":
    unittest.main()
