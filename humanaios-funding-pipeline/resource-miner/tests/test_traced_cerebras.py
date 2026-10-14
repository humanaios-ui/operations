import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace as NS
from unittest.mock import patch

from resource_miner.traced_cerebras import (
    PUBLIC_PROMPT, call_with_trace, digest, main, required_live_settings,
)


class FakeObservation:
    def __init__(self, owner, as_type, name, **kwargs):
        self.owner, self.data = owner, {"type": as_type, "name": name, **kwargs}
    def __enter__(self):
        self.owner.entries.append(self.data)
        return self
    def __exit__(self, typ, value, tb):
        return False
    def update(self, **kwargs):
        self.data.update(kwargs)


class FakeLangfuse:
    def __init__(self):
        self.entries = []
    def start_as_current_observation(self, *, as_type, name, **kwargs):
        return FakeObservation(self, as_type, name, **kwargs)
    def get_current_trace_id(self):
        return "a" * 32


class CompletionStub:
    def __init__(self, *, failure=False):
        self.calls, self.failure = [], failure
        self.chat = NS(completions=self)
    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.failure:
            raise ValueError("PRIVATE PROVIDER RESPONSE 1234")
        return NS(choices=[NS(message=NS(content="Public test answer."))],
                  usage=NS(prompt_tokens=8, completion_tokens=6))


class TracedCerebrasTests(unittest.TestCase):
    def test_nested_generation_has_model_tokens_but_no_raw_text(self):
        lf, cc = FakeLangfuse(), CompletionStub()
        out = call_with_trace(cerebras=cc, langfuse=lf)
        self.assertEqual([x["type"] for x in lf.entries], ["span", "generation"])
        self.assertEqual(lf.entries[1]["model"], "qwen-3.8-27b")
        self.assertEqual(lf.entries[1]["usage_details"], {"input_tokens": 8, "output_tokens": 6})
        self.assertEqual(out["trace_id"], "a" * 32)
        self.assertEqual(out["response_sha256"], digest("Public test answer."))
        self.assertEqual(out["trace_readback"], "NOT_VERIFIED")
        self.assertEqual(cc.calls[0]["model"], "qwen-3.8-27b")
        self.assertEqual(cc.calls[0]["max_completion_tokens"], 128)
        self.assertNotIn(PUBLIC_PROMPT, str(lf.entries))
        self.assertNotIn("Public test answer.", str(lf.entries))

    def test_error_sanitized_and_no_provider_text_export(self):
        lf, cc = FakeLangfuse(), CompletionStub(failure=True)
        with self.assertRaisesRegex(RuntimeError, "^CEREBRAS_CALL_FAILED$"):
            call_with_trace(cerebras=cc, langfuse=lf)
        self.assertEqual(lf.entries[1]["level"], "ERROR")
        self.assertNotIn("PRIVATE PROVIDER RESPONSE", str(lf.entries))

    def test_public_prompt_only(self):
        lf, cc = FakeLangfuse(), CompletionStub()
        with self.assertRaisesRegex(ValueError, "pinned public"):
            call_with_trace(cerebras=cc, langfuse=lf, prompt="client secret here")
        self.assertEqual(cc.calls, [])

    def test_strict_output_bound(self):
        with self.assertRaises(ValueError):
            call_with_trace(cerebras=CompletionStub(), langfuse=FakeLangfuse(),
                            max_tokens=129)
        with self.assertRaises(ValueError):
            call_with_trace(cerebras=CompletionStub(), langfuse=FakeLangfuse(),
                            max_tokens=True)

    def test_missing_settings_sanitized_and_https_required(self):
        self.assertEqual(len(required_live_settings({})), 4)
        env = dict(CEREBRAS_API_KEY="test", LANGFUSE_SECRET_KEY="test",
                   LANGFUSE_PUBLIC_KEY="test", LANGFUSE_BASE_URL="http://evil.example")
        self.assertIn("LANGFUSE_BASE_URL_HTTPS_REQUIRED", required_live_settings(env))
        env["LANGFUSE_BASE_URL"] = "https://us.cloud.langfuse.com"
        self.assertEqual(required_live_settings(env), [])

    def test_preflight_does_not_import_or_call_providers(self):
        with patch("sys.argv", ["traced_cerebras"]), patch.dict("os.environ", {}, clear=True):
            stream = io.StringIO()
            with redirect_stdout(stream):
                main()
        result = __import__("json").loads(stream.getvalue())
        self.assertEqual(result["external_calls"], 0)
        self.assertEqual(result["mode"], "PREFLIGHT_ONLY")


if __name__ == "__main__":
    unittest.main()
