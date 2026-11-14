#!/bin/bash
# Keychain-backed MCP stdio launcher for a trusted local MCP client or tunnel.
# Usage: launch_stdio_macos.sh /absolute/operations/path /absolute/service/path
set -euo pipefail
REPO_ROOT="${1:?operations checkout required}"
SERVICE_HOME="${2:?service install directory required}"
ACCOUNT="$(/usr/bin/id -un)"
ANTHROPIC_API_KEY="$(/usr/bin/security find-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w)"
export ANTHROPIC_API_KEY
exec "$SERVICE_HOME/.venv/bin/haios-mcp" --transport stdio --repo "$REPO_ROOT"
