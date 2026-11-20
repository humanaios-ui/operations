#!/bin/bash
# Witness E0.3 review-only staging: no LaunchAgent, no port bind, no provider call.
# Modes: --preflight /ABSOLUTE/OPERATIONS/ROOT
#        --stage     /ABSOLUTE/OPERATIONS/ROOT   (explicit operator choice)
#        --rollback-check                    (read-only process/marker check)
#        --rollback                          (requires clear checks; removes only pilot)
set -euo pipefail
umask 077

MODE="${1:---preflight}"
ROOT="${2:-}"
BASE="$HOME/Library/Application Support/HumanAIOS"
PILOT="$BASE/witness-pilot-e03-z1"
CONTEXT="$BASE/witness-pilot-e03-context"
MARKER='.witness-pilot-e03-z1'
PY313="${HAIOS_PILOT_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13}"
SOURCE_HOME="$(cd "$(dirname "$0")/.." && pwd -P)"

if [[ "$(uname -s)" != Darwin ]]; then
  echo 'STOP: this procedure supports macOS only.' >&2
  exit 2
fi
if [[ "$MODE" != --preflight && "$MODE" != --stage && "$MODE" != --rollback-check && "$MODE" != --rollback ]]; then
  echo 'Usage: bash scripts/stage_e03_pilot_macos.sh --preflight|--stage /absolute/operations/root' >&2
  echo 'Or: bash scripts/stage_e03_pilot_macos.sh --rollback-check|--rollback' >&2
  exit 2
fi

if [[ "$MODE" == --rollback-check || "$MODE" == --rollback ]]; then
  # The helper verifies exact ownership markers, denies symlink path redirects,
  # and checks all pilot cwd/file references and MCP processes (ANY port) with
  # lsof + ps. Any unavailable/ambiguous evidence refuses deletion.
  # Run from the reviewed source checkout, not from inside the staged pilot.
  if [[ ! -x "$PY313" ]] || ! "$PY313" -c 'import sys; assert sys.version_info[:2] == (3,13)' 2>/dev/null; then
    echo 'STOP: explicit Python 3.13 is required for safe rollback inspection.' >&2
    exit 3
  fi
  GUARD="$SOURCE_HOME/scripts/pilot_rollback_guard.py"
  if [[ ! -f "$GUARD" || -L "$GUARD" ]]; then
    echo 'STOP: reviewed rollback guard missing or linked.' >&2
    exit 3
  fi
  "$PY313" "$GUARD"
  if [[ "$MODE" == --rollback-check ]]; then
    echo 'NO FILES CHANGED. --rollback requires separate, explicit human approval.'
    exit 0
  fi
  # Recheck immediately before removal, narrowing the inspection/delete gap.
  # This is not an atomic process lock; new unexpected process starts remain a
  # platform risk. The deletion action needs a separate human decision.
  "$PY313" "$GUARD"
  /bin/rm -R "$PILOT"
  /bin/rm -R "$CONTEXT"
  echo 'PILOT ROLLBACK COMPLETE: only the two marked pilot folders removed.'
  exit 0
fi

if [[ "$ROOT" != /* || ! -d "$ROOT" || -L "$ROOT" ]]; then
  echo 'STOP: supply an absolute, non-symlink operations root as the second argument.' >&2
  exit 2
fi
if [[ ! -f "$SOURCE_HOME/pyproject.toml" || ! -f "$SOURCE_HOME/src/haios_mcp/server.py" ]]; then
  echo 'STOP: unrecognized Witness candidate source directory.' >&2
  exit 2
fi
if [[ ! -x "$PY313" ]] || ! "$PY313" -c 'import sys; assert sys.version_info[:2] == (3,13)' 2>/dev/null; then
  echo 'STOP: explicit Python 3.13 is required (not default python3).' >&2
  exit 2
fi

# The helper refuses destination ancestor symlinks and ambiguous lsof errors.
# It opens pinned public sources without following symlinks, hashes exact bytes
# and refuses all unexpected changes before staging mutates the filesystem.
STAGE_GUARD="$SOURCE_HOME/scripts/pilot_stage_guard.py"
if [[ ! -f "$STAGE_GUARD" || -L "$STAGE_GUARD" ]]; then
  echo 'STOP: reviewed staging guard missing or linked.' >&2
  exit 3
fi
"$PY313" "$STAGE_GUARD" preflight "$ROOT" "$BASE"

echo 'PREFLIGHT PASS: macOS, Python 3.13, three pinned public documents.'
echo 'No existing pilot directories, no 8768 listener, no LaunchAgent changes.'
if [[ "$MODE" == --preflight ]]; then
  echo 'NO FILES CHANGED. Pass --stage only after code review and human approval.'
  exit 0
fi

# Explicit --stage only: installs an isolated venv and public snapshot. No
# LaunchAgent, no credentials, no provider calls, no sockets, no E0.3 changes.
if [[ ! -d "$BASE" ]]; then
  /bin/mkdir -m 700 -p "$BASE"
fi
/bin/mkdir -m 700 "$PILOT" "$CONTEXT"
/usr/bin/printf 'E0.3 Witness pilot, not released\n' > "$PILOT/$MARKER"
/usr/bin/printf 'E0.3 Witness public context snapshot\n' > "$CONTEXT/$MARKER"
/bin/cp -R "$SOURCE_HOME/src" "$SOURCE_HOME/scripts" "$PILOT/"
/bin/cp "$SOURCE_HOME/pyproject.toml" "$PILOT/"
# Re-open and rehash all three no-follow source descriptors at copy time.
# Only the verified in-memory bytes may reach the staged context directory.
# A source swapped after preflight is refused; no shell cp of source docs.
"$PY313" "$STAGE_GUARD" copy-public "$ROOT" "$BASE"
"$PY313" -m venv "$PILOT/.venv"
"$PILOT/.venv/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: -e "$PILOT"
"$PILOT/.venv/bin/python" -m pip check

echo 'PILOT STAGED: no service started, no API call, no consent assumed.'
echo 'Rollback: bash scripts/stage_e03_pilot_macos.sh --rollback'
