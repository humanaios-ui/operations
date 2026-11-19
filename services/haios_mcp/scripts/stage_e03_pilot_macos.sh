#!/bin/bash
# Witness E0.3 review-only staging: no LaunchAgent, no port bind, no provider call.
# Modes: --preflight /ABSOLUTE/OPERATIONS/ROOT
#        --stage     /ABSOLUTE/OPERATIONS/ROOT   (explicit operator choice)
#        --rollback
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
if [[ "$MODE" != --preflight && "$MODE" != --stage && "$MODE" != --rollback ]]; then
  echo 'Usage: bash scripts/stage_e03_pilot_macos.sh --preflight|--stage /absolute/operations/root' >&2
  echo 'Or: bash scripts/stage_e03_pilot_macos.sh --rollback' >&2
  exit 2
fi

if [[ "$MODE" == --rollback ]]; then
  # Pilot owns only two marked directories. It never touches production mcp,
  # E0.3 workspaces, credential stores, or LaunchAgent registrations.
  if [[ -L "$PILOT" || -L "$CONTEXT" || ! -f "$PILOT/$MARKER" || ! -f "$CONTEXT/$MARKER" ]]; then
    echo 'STOP: pilot ownership markers missing; refusing removal.' >&2
    exit 3
  fi
  if /usr/sbin/lsof -nP -iTCP:8768 -sTCP:LISTEN >/dev/null 2>&1; then
    echo 'STOP: port 8768 active. Stop the pilot manually and inspect the listener first.' >&2
    exit 3
  fi
  /bin/rm -R "$PILOT"
  /bin/rm -R "$CONTEXT"
  echo 'PILOT ROLLBACK COMPLETE: staged pilot directories removed only.'
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

# Values come from the operator's prior exact-commit E2 receipt. These ensure
# the local context equals the reviewed PUBLIC source, not mutable private data.
for name in CURRENT.md REGISTERED.md GOVERNANCE.md; do
  if [[ ! -f "$ROOT/$name" || -L "$ROOT/$name" ]]; then
    echo "STOP: missing or linked source document: $name" >&2
    exit 2
  fi
  case "$name" in
    CURRENT.md) expected='d719fc3242fb3b3b2a05e85d2c024c45cb011de5f3291233b835f4e4cf13015e' ;;
    REGISTERED.md) expected='da56fc433bb928cc433982055e3d39d3e1dc460873a1de3c1a98c5e6b1f097cc' ;;
    GOVERNANCE.md) expected='1c1b76ce91e039301ce45422f6950a5446b3b9927951e2c0322482c4ca8acb2a' ;;
  esac
  actual="$(/usr/bin/shasum -a 256 "$ROOT/$name" | /usr/bin/awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "STOP: $name differs from the verified E2 public snapshot." >&2
    exit 3
  fi
done
if [[ -e "$PILOT" || -L "$PILOT" || -e "$CONTEXT" || -L "$CONTEXT" ]]; then
  echo 'STOP: stage directory already exists. Inspect before any changes.' >&2
  exit 3
fi
if /usr/sbin/lsof -nP -iTCP:8768 -sTCP:LISTEN >/dev/null 2>&1; then
  echo 'STOP: existing listener on port 8768. No stage or overwrite.' >&2
  exit 3
fi

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
for name in CURRENT.md REGISTERED.md GOVERNANCE.md; do
  /bin/cp "$ROOT/$name" "$CONTEXT/$name"
  /bin/chmod 600 "$CONTEXT/$name"
done
"$PY313" -m venv "$PILOT/.venv"
"$PILOT/.venv/bin/python" -m pip install --disable-pip-version-check --only-binary=:all: -e "$PILOT"
"$PILOT/.venv/bin/python" -m pip check

echo 'PILOT STAGED: no service started, no API call, no consent assumed.'
echo 'Rollback: bash scripts/stage_e03_pilot_macos.sh --rollback'
