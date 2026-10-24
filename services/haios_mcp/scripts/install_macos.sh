#!/bin/bash
# Single-operator macOS installation. No credentials are saved in plist/files.
# Never run the background job directly out of Downloads or Desktop (TCC).
set -euo pipefail
umask 077
if [[ "$(uname -s)" != Darwin ]]; then
  echo "macOS LaunchAgent installer only; use pip install -e . for other systems." >&2
  exit 1
fi
SOURCE_HOME="$(cd "$(dirname "$0")/.." && pwd -P)"
REPO_ROOT="${1:-}"
if [[ -z "$REPO_ROOT" || "$REPO_ROOT" != /* ]]; then
  echo 'Usage: bash scripts/install_macos.sh "$HOME/Desktop/HAIOS-Main/operations-staging"' >&2
  exit 2
fi
if [[ ! -d "$REPO_ROOT" ]]; then
  echo "Not a directory: $REPO_ROOT" >&2
  exit 2
fi
for required in CURRENT.md REGISTERED.md GOVERNANCE.md; do
  if [[ ! -f "$REPO_ROOT/$required" || -L "$REPO_ROOT/$required" ]]; then
    echo "Missing or linked required document: $REPO_ROOT/$required" >&2
    exit 2
  fi
done
# Before any dependency, Keychain or filesystem mutation, refuse an active job.
if launchctl print "gui/$(id -u)/ai.humanaios.mcp" >/dev/null 2>&1; then
  echo 'MCP LaunchAgent is already loaded; stop it with launchctl bootout before upgrading.' >&2
  exit 4
fi
BASE="$HOME/Library/Application Support/HumanAIOS"
INSTALL_DIR="$BASE/mcp"
CONTEXT_DIR="$BASE/context"
mkdir -p "$INSTALL_DIR" "$CONTEXT_DIR" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
chmod 700 "$BASE" "$INSTALL_DIR" "$CONTEXT_DIR"
if [[ "$SOURCE_HOME" != "$INSTALL_DIR" ]]; then
  cp -R "$SOURCE_HOME/src" "$SOURCE_HOME/scripts" "$INSTALL_DIR/"
  cp "$SOURCE_HOME/pyproject.toml" "$INSTALL_DIR/"
fi
# Explicit read-only source snapshot. This is never called live synced state.
cp "$REPO_ROOT/CURRENT.md" "$REPO_ROOT/REGISTERED.md" "$REPO_ROOT/GOVERNANCE.md" "$CONTEXT_DIR/"
chmod 600 "$CONTEXT_DIR/CURRENT.md" "$CONTEXT_DIR/REGISTERED.md" "$CONTEXT_DIR/GOVERNANCE.md"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/python" -m pip install --disable-pip-version-check -e "$INSTALL_DIR"
ACCOUNT="$(id -un)"
if ! security find-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w >/dev/null 2>&1; then
  echo "Enter your Anthropic key privately into the macOS Keychain prompt."
  security add-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w
fi
if ! security find-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w >/dev/null 2>&1; then
  echo 'Generate a 32+ character random token privately (example: openssl rand -hex 32).'
  security add-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w
fi
TOKEN_LENGTH="$(security find-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w | tr -d '\r\n' | wc -c | tr -d ' ')"
if [[ "$TOKEN_LENGTH" -lt 32 ]]; then
  echo 'MCP bearer token must be at least 32 characters. No LaunchAgent installed.' >&2
  exit 3
fi
PLIST="$HOME/Library/LaunchAgents/ai.humanaios.mcp.plist"
"$INSTALL_DIR/.venv/bin/python" - "$PLIST" "$INSTALL_DIR" "$CONTEXT_DIR" <<'PY'
import plistlib, sys
from pathlib import Path
plist, install, context = sys.argv[1:]
info = {
    'Label': 'ai.humanaios.mcp',
    'ProgramArguments': ['/bin/bash', str(Path(install) / 'scripts' / 'launch_http_macos.sh')],
    'EnvironmentVariables': {'HAIOS_MCP_HOME': install, 'HAIOS_REPO_ROOT': context},
    'RunAtLoad': True, 'KeepAlive': {'SuccessfulExit': False},
    'StandardErrorPath': str(Path.home() / 'Library' / 'Logs' / 'haios-mcp.log'),
    'ProcessType': 'Background',
}
with open(plist, 'wb') as fh:
    plistlib.dump(info, fh)
PY
chmod 600 "$PLIST"
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo 'Installed HumanAIOS MCP on http://127.0.0.1:8768/mcp (bearer required).'
echo "Context is a deliberately stale-prone local snapshot at: $CONTEXT_DIR"
echo "Uninstall service only: launchctl bootout gui/$(id -u) '$PLIST'"
