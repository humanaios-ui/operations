#!/usr/bin/env python3
"""Supabase client connection utility for agents."""

import os
from typing import Optional

TOOL_NAME = "supabase_client"
TOOL_VERSION = "1.0.0"


def get_supabase_client():
    """
    Get Supabase client with connection pooling.
    Returns None if credentials not configured (non-blocking).
    """
    try:
        from supabase import create_client
    except ImportError:
        return None

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)


def write_to_pipeline_health(status: str, integration_name: str, note: str = ""):
    """Write status to pipeline_health table."""
    client = get_supabase_client()
    if not client:
        return False

    try:
        from datetime import datetime, timezone

        client.table("pipeline_health").insert({
            "integration_name": integration_name,
            "status": status,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "note": note,
        }).execute()
        return True
    except Exception as e:
        print(f"Error writing to pipeline_health: {e}")
        return False


def run_smoke_test() -> bool:
    """Smoke test."""
    try:
        client = get_supabase_client()
        if client:
            print("✓ Supabase client initialized")
        else:
            print("⚠ Supabase credentials not configured (non-blocking)")
        return True
    except Exception as e:
        print(f"✗ Supabase error: {e}")
        return False


if __name__ == "__main__":
    run_smoke_test()
