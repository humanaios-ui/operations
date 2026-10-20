"""Opt-in, bounded Cerebras SDK call with Langfuse v5 tracing.

Run on an approved Azure workload. Nothing here deploys to Azure or upgrades
admission standing. Only a fixed PUBLIC test prompt is accepted by the CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from typing import Any
from urllib.parse import urlsplit

PUBLIC_PROMPT = "Why is fast inference important?"
DEFAULT_MODEL = "qwen-3.8-27b"
MAX_OUTPUT_TOKENS = 128


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def required_live_settings(env: dict[str, str]) -> list[str]:
    names = ("CEREBRAS_API_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_BASE_URL")
    missing = [n for n in names if not env.get(n, "").strip()]
    url = env.get("LANGFUSE_BASE_URL", "")
    u = urlsplit(url)
    if url and (u.scheme != "https" or not u.hostname or u.username or u.password or u.query):
        missing.append("LANGFUSE_BASE_URL_HTTPS_REQUIRED")
    return missing


def call_with_trace(
    *, cerebras: Any, langfuse: Any, prompt: str = PUBLIC_PROMPT,
    model: str = DEFAULT_MODEL, max_tokens: int = MAX_OUTPUT_TOKENS,
) -> dict[str, Any]:
    """Capture nested generation, tokens, latency, and IDs; never export raw text."""
    if prompt != PUBLIC_PROMPT:
        raise ValueError("Pilot allows only the pinned public test prompt")
    if not isinstance(model, str) or not model or len(model) > 100:
        raise ValueError("Invalid model")
    if type(max_tokens) is not int or not 1 <= max_tokens <= MAX_OUTPUT_TOKENS:
        raise ValueError("Max tokens must be 1..128")
    with langfuse.start_as_current_observation(
        as_type="span",
        name="resource-miner-public-inference-pilot",
        input={"task": "PINNED_PUBLIC_QUESTION", "prompt_sha256": digest(prompt)},
        metadata={"provider": "cerebras", "data_class": "PUBLIC_SYNTHETIC", "authority": "NONE"},
    ) as root:
        trace_id = langfuse.get_current_trace_id()
        with langfuse.start_as_current_observation(
            as_type="generation", name="cerebras-chat-completion",
            model=model,
            input={"prompt_sha256": digest(prompt), "prompt_length": len(prompt)},
        ) as gen:
            start = time.perf_counter()
            failure = None
            response = None
            try:
                response = cerebras.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model, max_completion_tokens=max_tokens,
                )
            except Exception as exc:  # do not send unredacted provider errors into traces
                failure = type(exc).__name__
            elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
            if failure:
                gen.update(level="ERROR", status_message="CEREBRAS_CALL_FAILED",
                           metadata={"error_type": failure, "latency_ms": elapsed_ms})
            else:
                answer = getattr(response.choices[0].message, "content", None) or ""
                usage = getattr(response, "usage", None)
                amounts = {}
                for source, target in (("prompt_tokens", "input_tokens"),
                                       ("completion_tokens", "output_tokens")):
                    value = getattr(usage, source, None)
                    if type(value) is int and value >= 0:
                        amounts[target] = value
                gen.update(
                    output={"response_sha256": digest(answer), "response_characters": len(answer)},
                    usage_details=amounts or None,
                    metadata={"provider": "cerebras", "latency_ms": elapsed_ms,
                              "raw_text_exported": False},
                )
        if failure:
            root.update(output={"completed": False, "error_type": failure})
        else:
            root.update(output={"completed": bool(answer), "output_sha256": digest(answer)})
    if failure:
        raise RuntimeError("CEREBRAS_CALL_FAILED") from None
    return {
        "schema": "humanaios.cerebras-langfuse-pilot.v0.1",
        "model": model, "trace_id": trace_id,
        "prompt_sha256": digest(prompt),
        "response_sha256": digest(answer),
        "response_nonempty": bool(answer),
        "token_usage": amounts, "elapsed_provider_ms": elapsed_ms,
        "raw_prompt_or_output_logged": False, "provider_status": "CALLED",
        "trace_export": "FLUSH_REQUIRED", "trace_readback": "NOT_VERIFIED",
        "authority_effect": "NONE", "actionability_state": "NOT_ACTIONABLE",
        "provider_cost_usd": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="HumanAIOS Cerebras/Langfuse opt-in public prompt")
    parser.add_argument("--live", action="store_true", help="Explicitly authorize one bounded API call")
    parser.add_argument("--model", default=os.environ.get("CEREBRAS_MODEL", DEFAULT_MODEL))
    parser.add_argument("--max-tokens", type=int, default=MAX_OUTPUT_TOKENS)
    args = parser.parse_args()
    missing = required_live_settings(dict(os.environ))
    if not args.live:
        print(json.dumps({"mode": "PREFLIGHT_ONLY", "missing_setting_names": missing,
                          "external_calls": 0, "authority_effect": "NONE"}))
        return
    if missing:
        parser.error("Missing or invalid required environment setting(s): " + ", ".join(missing))
    # Import lazily: no SDK or credential evaluation during offline tests.
    from cerebras.cloud.sdk import Cerebras
    from langfuse import get_client
    langfuse = get_client()
    if not langfuse.auth_check():
        parser.error("Langfuse project authentication failed; no model call made.")
    # Disable default Cerebras TCP warming. Avoid hidden requests/retries and cap cost.
    cerebras = Cerebras(api_key=os.environ["CEREBRAS_API_KEY"],
                        max_retries=0, timeout=20.0, warm_tcp_connection=False)
    try:
        result = call_with_trace(cerebras=cerebras, langfuse=langfuse,
                                 model=args.model, max_tokens=args.max_tokens)
    except RuntimeError as exc:
        parser.error(str(exc))  # no provider response or secrets in logs
    finally:
        langfuse.flush()
    result["trace_export"] = "FLUSH_CALLED_DELIVERY_NOT_INDEPENDENTLY_VERIFIED"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
