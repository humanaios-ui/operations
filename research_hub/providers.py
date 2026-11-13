"""Bot adapters. One interface, any model. Keys are read from env, never logged."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

from .protocol import ToolError


@dataclass
class Completion:
    text: str
    stop_reason: str = "end_turn"
    usage: dict[str, int] = field(default_factory=dict)


class Provider:
    name: str
    tags: list[str]
    kind: str

    def complete(self, system: str, user: str, max_tokens: int) -> Completion:
        raise NotImplementedError

    def info(self) -> dict[str, Any]:
        return {"name": self.name, "kind": self.kind, "tags": self.tags}


class MockProvider(Provider):
    """Deterministic stand-in for tests and for trying the hub with no keys."""

    def __init__(self, name: str, tags: list[str] | None = None,
                 reply: Callable[[str, str], str] | None = None):
        self.name, self.tags, self.kind = name, tags or [], "mock"
        self._reply = reply or self._default

    @staticmethod
    def _default(system: str, user: str) -> str:
        if "VERIFIER" in system:
            n = user.count('"claim"') or 1
            return json.dumps({"verdicts": [{"index": i, "verdict": "unverifiable",
                                             "note": "mock verifier"} for i in range(n)]})
        return json.dumps({"answer": "mock answer", "claims": [{
            "claim": "Mock claim for wiring tests.", "sources": ["https://example.com/mock"],
            "falsifier": "Any real source contradicting the mock claim."}]})

    def complete(self, system: str, user: str, max_tokens: int) -> Completion:
        return Completion(self._reply(system, user), usage={"input_tokens": 0, "output_tokens": 0})


class AnthropicProvider(Provider):
    """Claude through the official SDK. Server-side refusal fallback is on by default."""

    def __init__(self, name: str, model: str, key_env: str, tags: list[str]):
        self.name, self.model, self.tags, self.kind = name, model, tags, "anthropic"
        self.key_env = key_env

    def complete(self, system: str, user: str, max_tokens: int) -> Completion:
        import anthropic  # lazy: the hub runs without the SDK when Claude is not configured

        client = anthropic.Anthropic(api_key=os.environ[self.key_env])
        with client.beta.messages.stream(
            model=self.model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise ToolError(f"{self.name} declined this request")
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return Completion(text, msg.stop_reason or "", {
            "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens})


class OpenAICompatProvider(Provider):
    """Grok (xAI), OpenAI, and anything else that speaks /chat/completions."""

    def __init__(self, name: str, base_url: str, model: str, key_env: str, tags: list[str]):
        u = urlparse(base_url)
        local = u.hostname in ("localhost", "127.0.0.1")
        if u.scheme != "https" and not local:
            raise ValueError(f"{name}: base_url must be https")
        self.name, self.base, self.model = name, base_url.rstrip("/"), model
        self.key_env, self.tags, self.kind = key_env, tags, "openai_compat"

    def complete(self, system: str, user: str, max_tokens: int) -> Completion:
        body = json.dumps({"model": self.model, "max_tokens": max_tokens, "messages": [
            {"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
        req = urllib.request.Request(f"{self.base}/chat/completions", data=body, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {os.environ[self.key_env]}"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise ToolError(f"{self.name} returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError):
            raise ToolError(f"{self.name} unreachable") from None
        choice = data["choices"][0]
        u = data.get("usage", {})
        return Completion(choice["message"].get("content") or "", choice.get("finish_reason", ""),
                          {"input_tokens": u.get("prompt_tokens", 0),
                           "output_tokens": u.get("completion_tokens", 0)})


def load_providers(env: dict[str, str] | None = None) -> dict[str, Provider]:
    """HUB_PROVIDERS is a JSON list. Providers whose key env var is unset are skipped."""
    env = env if env is not None else dict(os.environ)
    raw = env.get("HUB_PROVIDERS", "")
    if not raw:  # no config: two mocks so the wiring can be tried safely
        return {p.name: p for p in (MockProvider("mock-a", ["fresh", "web"]),
                                    MockProvider("mock-b", ["long", "analysis"]))}
    out: dict[str, Provider] = {}
    for spec in json.loads(raw):
        key_env = spec.get("key_env", "")
        if key_env and key_env not in env:
            continue
        tags = list(spec.get("tags", []))
        kind = spec["kind"]
        if kind == "anthropic":
            p: Provider = AnthropicProvider(spec["name"], spec.get("model", "claude-opus-5-5"), key_env, tags)
        elif kind == "openai_compat":
            p = OpenAICompatProvider(spec["name"], spec["base_url"], spec["model"], key_env, tags)
        elif kind == "mock":
            p = MockProvider(spec["name"], tags)
        else:
            raise ValueError(f"unknown provider kind: {kind}")
        out[p.name] = p
    return out
