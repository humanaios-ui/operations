#!/usr/bin/env python3
"""
Streaming text generation through Vercel AI Gateway.

Uses the OpenAI-compatible Chat Completions API endpoint.
Requires AI_GATEWAY_API_KEY environment variable.
"""

import os
import sys
from openai import OpenAI, APIConnectionError, APIError

def stream_text_generation(
    prompt: str,
    model: str = "openai/gpt-6-astra",
    max_tokens: int = 256,
) -> None:
    """Stream text generation through AI Gateway.

    Args:
        prompt: The input text prompt
        model: The model to use (provider/model format)
        max_tokens: Maximum tokens to generate
    """
    api_key = os.getenv("AI_GATEWAY_API_KEY")
    if not api_key:
        print("ERROR: AI_GATEWAY_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Initialize OpenAI client pointing to AI Gateway
    client = OpenAI(
        api_key=api_key,
        base_url="https://ai-gateway.vercel.sh/v1"
    )

    print(f"Streaming text generation...")
    print(f"Model: {model}")
    print(f"Prompt: {prompt}")
    print("\n--- Generated Text ---\n")

    try:
        # Stream text using Chat Completions API
        with client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=max_tokens,
            stream=True,  # Enable streaming
        ) as stream:
            collected_text = ""
            for text in stream.text_stream:
                print(text, end="", flush=True)
                collected_text += text

        print("\n\n--- Stream Complete ---")
        return collected_text

    except APIConnectionError as e:
        print(f"\nConnection Error: {e}", file=sys.stderr)
        print("Ensure AI_GATEWAY_API_KEY is set and the gateway is accessible", file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI Error ({e.status_code}): {e.message}", file=sys.stderr)
        if e.status_code == 401:
            print("Authentication failed. Check AI_GATEWAY_API_KEY.", file=sys.stderr)
        elif e.status_code == 429:
            print("Rate limited. Check spend budgets and retry later.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    prompt = "Explain quantum computing in 2-3 sentences"
    stream_text_generation(prompt)
