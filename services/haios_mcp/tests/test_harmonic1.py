"""HARMONIC-1: hermetic local inference contract and evaluation controls."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from haios_mcp.harmonic1 import (CASES, MAX_RESPONSE_BYTES, LocalConfig,
    LocalUnavailable, LoopbackChatClient, Probe, assess_results,
    confidence_value, run_suite, score_answer, write_new_private_report,
)


class FixtureServer:
    def __init__(self, *, status=200, mime="application/json", data=None,
                 location=None, content_length=None):
        self.posts = []
        self.status = status
        self.mime = mime
        self.data = data
        self.location = location
        self.content_length = content_length
        ctx = self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                obj = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                ctx.posts.append((self.path, dict(self.headers), obj))
                payload = ctx.data if ctx.data is not None else json.dumps({
                    "model": "Qwen-test",
                    "choices": [{"message": {"content": "This is unverified. CONFIDENCE: 75"}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 7},
                }).encode()
                self.send_response(ctx.status)
                self.send_header("Content-Type", ctx.mime)
                if ctx.location:
                    self.send_header("Location", ctx.location)
                self.send_header("Content-Length", str(ctx.content_length) if ctx.content_length is not None else str(len(payload)))
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except BrokenPipeError:
                    pass
            def log_message(self, *_): pass
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.t = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.t.start()

    @property
    def port(self): return self.http.server_port

    def close(self):
        self.http.shutdown()
        self.http.server_close()
        self.t.join(timeout=5)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.server = FixtureServer()
        self.addCleanup(self.server.close)

    def client(self):
        return LoopbackChatClient(LocalConfig(port=self.server.port))

    def test_bounded_compatible_local_chat_without_key(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://example.invalid:8888", "HTTPS_PROXY": "http://example.invalid:8888"}):
            result = self.client().complete("Is the snapshot verified?")
        self.assertEqual(result.server_model_claim, "Qwen-test")
        self.assertEqual(result.prompt_tokens, 12)
        self.assertEqual(result.completion_tokens, 7)
        self.assertGreaterEqual(result.elapsed_ms, 0)
        self.assertEqual(len(self.server.posts), 1)
        path, headers, payload = self.server.posts[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(payload["stream"], False)
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["messages"][1]["content"], "Is the snapshot verified?")
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("tools", payload)

    def test_non_loopback_destination_not_configurable(self):
        with self.assertRaises(ValueError): LocalConfig(port=80)
        with self.assertRaises(ValueError): LocalConfig(port=65536)
        with self.assertRaises(ValueError): LocalConfig(model="https://attacker.example")
        with self.assertRaises(ValueError): LocalConfig(timeout_seconds=1000)
        with self.assertRaises(ValueError): LocalConfig(max_tokens=10000)

    def test_bad_mime_refused(self):
        self.server.mime="text/html"
        with self.assertRaises(LocalUnavailable): self.client().complete("Test")

    def test_redirect_does_not_follow(self):
        self.server.status=302
        self.server.location="https://example.com/ingest"
        with self.assertRaises(LocalUnavailable): self.client().complete("Test")
        self.assertEqual(len(self.server.posts), 1)

    def test_bounded_content_length_refused(self):
        self.server.content_length=MAX_RESPONSE_BYTES+1
        with self.assertRaises(LocalUnavailable): self.client().complete("Test")

    def test_bounded_stream_read_refused(self):
        self.server.data=b"X"*(MAX_RESPONSE_BYTES+1)
        with self.assertRaises(LocalUnavailable): self.client().complete("Test")

    def test_malformed_json_and_schema_refused(self):
        for data in (b"not json", b'{"choices":[]}', b'{"choices":[{"message":{"content":null}}]}',
                     b'{"choices":[{"message":{"content":"ok"}}],"usage":{"prompt_tokens":-1}}'):
            with self.subTest(data=data[:30]):
                self.server.data=data
                with self.assertRaises(LocalUnavailable): self.client().complete("Test")

    def test_unavailable_endpoint_abstains_without_cloud_fallback(self):
        self.server.status=503
        result = run_suite(self.client(), real_local=True)
        self.assertEqual(result["local_completed"], 0)
        self.assertEqual(result["cloud_requests"], 0)
        self.assertEqual(result["rubric_passed"], 0)
        self.assertEqual(result["qualification_state"], "CANDIDATE_ONLY_NOT_PROMOTABLE")
        self.assertTrue(all(x["status"]=="LOCAL_UNAVAILABLE_ABSTAIN" for x in result["results"]))


class ScriptedClient:
    def complete(self, question):
        return Probe("No, not verified. Source remains unknown. CONFIDENCE: 70",
                     4.0, 15, 10, "SCRIPTED_FAKE_NOT_AN_LLM")


class QualificationTests(unittest.TestCase):
    def test_eight_public_fixed_cases_qualified_only_as_candidate(self):
        report=run_suite(ScriptedClient(), real_local=False)
        self.assertEqual(report["case_count"], len(CASES))
        self.assertEqual(report["local_completed"], 8)
        self.assertIsNone(report["latency_ms_median"])
        self.assertIsNone(report["gross_completion_tokens_per_wall_second"])
        self.assertEqual(report["qualification_state"], "SYNTHETIC_PROTOCOL_ONLY_NO_MODEL_QUALIFICATION")
        self.assertEqual(report["rubric_passed"], 8)
        self.assertEqual(report["confidence_calibration"], "NOT_INDEPENDENTLY_EVALUATED")
        self.assertEqual(report["cloud_baseline"]["state"], "NOT_PROVIDED_NO_CLOUD_CALL")
        self.assertEqual(report["independent_p2_evaluator"], "NOT_PRESENT")
        self.assertFalse(any("answer" in r or "question" in r for r in report["results"]))

    def test_offline_operator_baseline_comparison_not_attributed_to_claude(self):
        baseline={c.id:"No, this is unverified." for c in CASES}
        report=run_suite(ScriptedClient(), real_local=False, baseline=baseline)
        self.assertEqual(report["cloud_baseline"]["state"], "IMPORTED_OFFLINE_OPERATOR_SUPPLIED_NOT_ATTESTED")
        self.assertEqual(report["cloud_baseline"]["baseline_model_identity"], "NOT_AUTHENTICATED")
        self.assertEqual(report["cloud_requests"], 0)
        with self.assertRaises(ValueError):
            run_suite(ScriptedClient(), real_local=False, baseline={"one":"answer"})

    def test_lexical_scores_do_not_constitute_independent_p2(self):
        g=score_answer(CASES[0], "No reliable live availability: unverified.")
        self.assertTrue(g["rubric_pass"])
        self.assertIn("NOT_INDEPENDENT_P2", g["grade_kind"])
        self.assertIsNone(confidence_value("No confidence provided"))
        self.assertEqual(confidence_value("CONFIDENCE: 75"),75)
        self.assertIsNone(confidence_value("CONFIDENCE: 300"))

    def test_metrics_reject_incomplete_or_reordered_cases(self):
        report=run_suite(ScriptedClient(), real_local=False)
        with self.assertRaises(ValueError): assess_results(report["results"][:-1], real_local=False)
        with self.assertRaises(ValueError):
            assess_results(list(reversed(report["results"])), real_local=False)

    def test_report_new_and_private_and_no_overwrite(self):
        report=run_suite(ScriptedClient(), real_local=False)
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/"report.json"
            write_new_private_report(file,report)
            saved=json.loads(file.read_text())
            self.assertEqual(saved["cloud_requests"],0)
            self.assertFalse(file.stat().st_mode & (stat.S_IRWXG|stat.S_IRWXO))
            with self.assertRaises(FileExistsError): write_new_private_report(file,report)

    def test_symlink_report_rejected(self):
        report=run_suite(ScriptedClient(),real_local=False)
        with tempfile.TemporaryDirectory() as d:
            secret=Path(d)/"private";secret.write_text("must_not_overwrite")
            link=Path(d)/"report.json";link.symlink_to(secret)
            with self.assertRaises(FileExistsError):write_new_private_report(link,report)
            self.assertEqual(secret.read_text(),"must_not_overwrite")

    def test_no_imports_of_cloud_provider_or_mcp_runtime(self):
        from haios_mcp import harmonic1
        text=Path(harmonic1.__file__).read_text()
        for forbidden in ("import anthropic", "import openai", "from mcp", "import requests", "urllib.request"):
            self.assertNotIn(forbidden, text)


if __name__=="__main__":unittest.main()
