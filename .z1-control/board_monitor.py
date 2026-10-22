#!/usr/bin/env python3
"""Mesh build-board monitor — surfaces board status changes at end of turn.

Builder v1.7 compliant · monitoring_tool

Canonical, versioned copy (the `~/.empirica/scripts/board_monitor.py` copy is unversioned
and should be removed or symlinked to this one to avoid the 3-copy drift that bit B6b).

Wired as a **Stop** hook (a real Claude Code hook event — fires when the agent finishes a
turn), NOT the fictional `FileChanged` event the first draft used. On each turn-end it
diffs ~/.empirica/MESH_BUILD_BOARD.md against the last seen state and prints a
`{"systemMessage": ...}` JSON object, which Claude Code surfaces to the user. State is
tracked in ~/.empirica/.board_state.json so it survives across sessions.

Read-only on the board; never writes it. Safe to run on every turn.
"""

import json
import re
import sys
from pathlib import Path

TOOL_NAME = "board_monitor"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "monitoring_tool"
TOOL_ZONE = 1

BOARD_PATH = Path.home() / ".empirica" / "MESH_BUILD_BOARD.md"
STATE_FILE = Path.home() / ".empirica" / ".board_state.json"


def parse_board() -> dict:
    """Parse the task table into {item_id: {owner, status}}."""
    if not BOARD_PATH.exists():
        return {}
    state = {}
    for line in BOARD_PATH.read_text().split("\n"):
        if "| **B" in line and "Owner" not in line and "---|" not in line:
            m = re.match(r"\|\s*\*\*([^*]+)\*\*.*?\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
            if not m:
                continue
            item_id = m.group(1).strip()
            owner = m.group(2).strip()
            status_cell = m.group(4).strip()
            if "DONE" in line:
                status = "DONE"
            elif "BLOCKED" in line:
                status = "BLOCKED"
            elif "PARTIAL" in line or "⚠️" in status_cell or "REBASE" in line:
                status = "PENDING"
            elif "IN PROGRESS" in status_cell:
                status = "IN_PROGRESS"
            elif "OPEN" in status_cell:
                status = "OPEN"
            else:
                status = status_cell or "?"
            state[item_id] = {"owner": owner, "status": status}
    return state


def detect_changes(new_state: dict) -> list:
    if not STATE_FILE.exists():
        return []  # first run: nothing to compare against
    try:
        prev = json.loads(STATE_FILE.read_text()).get("board_state", {})
    except (json.JSONDecodeError, OSError):
        return []
    changes = []
    for item, info in new_state.items():
        if item not in prev:
            changes.append({"type": "new", "item": item, "to": info["status"]})
        elif prev[item]["status"] != info["status"]:
            changes.append({"type": "status", "item": item,
                            "from": prev[item]["status"], "to": info["status"]})
        elif prev[item]["owner"] != info["owner"]:
            changes.append({"type": "owner", "item": item, "to": info["owner"]})
    return changes


def save_state(board_state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "board_state": board_state,
        "timestamp": str(BOARD_PATH.stat().st_mtime) if BOARD_PATH.exists() else None,
    }, indent=2))


def format_notification(changes: list) -> dict:
    if not changes:
        return {}
    lines = []
    for c in changes:
        if c["type"] == "status":
            emoji = "✅" if c["to"] == "DONE" else "⛔" if c["to"] == "BLOCKED" else "⚠️" if c["to"] == "PENDING" else "📋"
            lines.append(f"{emoji} {c['item']}: {c['from']} → {c['to']}")
        elif c["type"] == "owner":
            lines.append(f"👤 {c['item']}: now {c['to']}")
        elif c["type"] == "new":
            lines.append(f"🆕 {c['item']}: {c['to']}")
    return {"systemMessage": "🔔 Mesh board update:\n" + "\n".join(lines)} if lines else {}


def main() -> int:
    new_state = parse_board()
    changes = detect_changes(new_state)
    save_state(new_state)
    note = format_notification(changes)
    if note:
        print(json.dumps(note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
