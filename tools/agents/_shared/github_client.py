#!/usr/bin/env python3
"""GitHub API client utility for agents."""

import os
import json
from typing import Optional, List
from datetime import datetime, timezone

TOOL_NAME = "github_client"
TOOL_VERSION = "1.0.0"


def get_github_client():
    """Get GitHub API client (uses gh CLI)."""
    return GitHubClient()


class GitHubClient:
    """GitHub API wrapper using gh CLI."""

    def __init__(self):
        self.owner = "humanaios-ui"
        self.repo = "operations"

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[dict]:
        """Create a GitHub issue."""
        import subprocess

        labels_arg = ""
        if labels:
            labels_arg = " ".join([f"--label {l}" for l in labels])

        cmd = f'gh issue create -R {self.owner}/{self.repo} --title "{title}" --body "{body}" {labels_arg} --json url,number'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception as e:
            print(f"Error creating issue: {e}")
            return None

    def get_recent_commits(self, limit: int = 10) -> List[dict]:
        """Get recent commits."""
        import subprocess

        cmd = f'gh api repos/{self.owner}/{self.repo}/commits --limit {limit} --jq ".[].commit"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout) if result.stdout else []
            return []
        except Exception:
            return []


def run_smoke_test() -> bool:
    """Smoke test."""
    try:
        client = GitHubClient()
        print(f"✓ GitHub client initialized ({client.owner}/{client.repo})")
        return True
    except Exception as e:
        print(f"✗ GitHub error: {e}")
        return False


if __name__ == "__main__":
    run_smoke_test()
