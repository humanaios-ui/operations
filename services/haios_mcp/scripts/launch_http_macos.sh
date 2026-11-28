#!/bin/bash
# User LaunchAgent entrypoint. Reads secrets from macOS Keychain at launch time.
set -euo pipefail
: "${HAIOS_MCP_HOME:?Missing installed service directory}"
: "${HAIOS_REPO_ROOT:?Missing operations checkout directory}"
ACCOUNT="$(/usr/bin/id -un)"
ANTHROPIC_API_KEY="$(/usr/bin/security find-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w)"
export ANTHROPIC_API_KEY
HAIOS_MCP_TOKEN="$(/usr/bin/security find-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w)"
export HAIOS_MCP_TOKEN
exec "$HAIOS_MCP_HOME/.venv/bin/haios-mcp" --repo "$HAIOS_REPO_ROOT" --transport http --port 8768
