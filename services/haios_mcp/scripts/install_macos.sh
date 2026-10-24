#!/bin/bash
# Local, user-owned install only. Never writes passwords to files or service plist.
set -euo pipefail
if [[ "$(uname -s)" != Darwin ]]; then
  echo "macOS LaunchAgent installer only. Use pip install -e . for other systems." >&2
  exit 1
fi
HOME_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
REPO_ROOT="${1:-}"
if [[ -z "$REPO_ROOT" || "$REPO_ROOT" != /* ]]; then
  echo "Pass the actual absolute path to the operations checkout." >&2
  echo "Example: bash scripts/install_macos.sh "$HOME/Desktop/HAIOS-Main/operations-staging"" >&2
  exit 2
fi
if [[ ! -d "$REPO_ROOT" ]]; then
  echo "Not a directory: $REPO_ROOT" >&2
  exit 2
fi
for required in CURRENT.md REGISTERED.md; do
  if [[ ! -f "$REPO_ROOT/$required" || -L "$REPO_ROOT/$required" ]]; then
    echo "Missing required regular file: $REPO_ROOT/$required" >&2
    echo "Check that this is your HumanAIOS operations checkout, then retry." >&2
    exit 2
  fi
done
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
python3 -m venv "$HOME_DIR/.venv"
"$HOME_DIR/.venv/bin/python" -m pip install --disable-pip-version-check -e "$HOME_DIR"
ACCOUNT="$(id -un)"
if ! security find-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w >/dev/null 2>&1; then
  echo "Paste your Anthropic key at the secure Keychain prompt (not in chat)."
  security add-generic-password -a "$ACCOUNT" -s ai.humanaios.anthropic -w
fi
if ! security find-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w >/dev/null 2>&1; then
  echo "Generate a secret token (32+ chars), then enter it at the Keychain prompt."
  echo "Suggested command in a separate terminal: openssl rand -hex 32"
  security add-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w
fi
TOKEN_LENGTH="$(security find-generic-password -a "$ACCOUNT" -s ai.humanaios.mcp-token -w | wc -c | tr -d ' ')"
if [[ "$TOKEN_LENGTH" -lt 32 ]]; then
  echo "Token too short. No LaunchAgent installed." >&2
  exit 3
fi
PLIST="$HOME/Library/LaunchAgents/ai.humanaios.mcp.plist"
if launchctl print "gui/$(id -u)/ai.humanaios.mcp" >/dev/null 2>&1; then
  echo "Existing agent is running. Not changing it. Stop it first before reinstalling." >&2
  exit 4
fi
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
"$HOME_DIR/.venv/bin/python" - "$PLIST" "$HOME_DIR" "$REPO_ROOT" <<'PY'
import plistlib, sys
from pathlib import Path
plist, home, repo = sys.argv[1:]
launcher = str(Path(home) / 'scripts' / 'launch_http_macos.sh')
info = {
    'Label': 'ai.humanaios.mcp',
    'ProgramArguments': ['/bin/bash', launcher],
    'EnvironmentVariables': {'HAIOS_MCP_HOME': home, 'HAIOS_REPO_ROOT': repo},
    'RunAtLoad': True, 'KeepAlive': {'SuccessfulExit': False},
    'StandardErrorPath': str(Path.home() / 'Library' / 'Logs' / 'haios-mcp.log'),
    'ProcessType': 'Background',
}
with open(plist, 'wb') as fh:
    plistlib.dump(info, fh)
PY
chmod 600 "$PLIST"
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed local HAIOS MCP on http://127.0.0.1:8768/mcp"
echo "Only this Mac can connect; HTTP requests must include the Keychain-held bearer token."
echo "Uninstall: launchctl bootout gui/$(id -u) '$PLIST'"
