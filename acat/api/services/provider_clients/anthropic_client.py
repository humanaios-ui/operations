from __future__ import annotations

import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi


class AnthropicClientError(RuntimeError):
    """Raised when an Anthropic API request fails."""


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


class AnthropicClient:
    """
    Minimal JSON-in / JSON-out client for Anthropic Messages API.

    This client expects the model to return a plain text body that is itself valid JSON.
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
        try:
            return json.loads(text)
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
