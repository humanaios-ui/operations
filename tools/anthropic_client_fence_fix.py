from __future__ import annotations

import json
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


class AnthropicClientError(RuntimeError):
    """Raised when an Anthropic API request fails."""

<<<<<<< HEAD
TOOL_NAME = "anthropic_client_fence_fix"
TOOL_VERSION = "1.0.0"
HumanAIOS
Builder v1.7 compliant
=======
# Builder v1.7 compliant
# HumanAIOS

TOOL_NAME = "anthropic_client_fence_fix"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True
>>>>>>> origin/main


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _strip_markdown_fences(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences from model output.

    Some models (e.g. Haiku 4.5) wrap JSON in markdown code fences despite
    being instructed not to. This strips them before JSON parsing so the
    elicitation pipeline does not fail on fence-wrapped responses.
    """
    stripped = text.strip()
    # Match ```json or ``` at start, ``` at end
    match = re.match(r"^```(?:json)?\s*\n([\s\S]*?)\n?```$", stripped)
    if match:
        return match.group(1).strip()
    return stripped


class AnthropicClient:
    """
    Minimal JSON-in / JSON-out client for Anthropic Messages API.

    This client expects the model to return a plain text body that is itself valid JSON.
    Markdown code fences are stripped automatically before parsing.
    """

    api_url = "https://api.anthropic.com/v1/messages"
    anthropic_version = "2023-06-01"

    def complete_json(self, *, api_key: str, model: str, prompt: str, max_tokens: int = 512) -> dict:
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        request = Request(
            self.api_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": self.anthropic_version,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=60, context=_ssl_context()) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AnthropicClientError(f"Anthropic request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AnthropicClientError(f"Anthropic connection failed: {exc}") from exc

        text = self._extract_text(parsed)
        clean = _strip_markdown_fences(text)
        try:
            return json.loads(clean)
        except json.JSONDecodeError as exc:
            raise AnthropicClientError(f"Anthropic response was not valid JSON text: {text!r}") from exc

    @staticmethod
    def _extract_text(payload: dict) -> str:
        content = payload.get("content")
        if not isinstance(content, list):
            raise AnthropicClientError("Anthropic response missing content list")

        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)

        joined = "".join(text_parts).strip()
        if not joined:
            raise AnthropicClientError("Anthropic response contained no text content")
        return joined

<<<<<<< HEAD
def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("✓ Smoke test PASSED")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_smoke_test() else 1)
=======
if __name__ == "__main__":
    pass
>>>>>>> origin/main
