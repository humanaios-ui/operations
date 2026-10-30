"""Offline, proposal-only INTENT-OS -> Project Desk reconciliation (E0).

No persistence, network access, status promotion, or execution authority.
Original source IDs travel with proposals; existing Desk IDs are never replaced.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

WORKSPACE_SCHEMA = "humanaios.workspace_view.v1"
DESK_SCHEMA = "humanaios.project-desk.v1"
ORIGIN_PREFIX = "INTENT-OS snapshot · "
IMPORT_ID = "intent-workspace"


class BridgeInputError(ValueError):
    """Fail closed when identity or revision is unclear."""


def _list(value: Any, label: str) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise BridgeInputError(f"{label} must be a list of objects")
    return value


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 256:
        raise BridgeInputError(f"{label} must be a nonempty exact ID")
    return value


def _unique(items: list[dict], label: str) -> None:
    seen: set[str] = set()
    for item in items:
        key = _id(item.get("id"), label)
        if key in seen:
            raise BridgeInputError(f"duplicate {label}: {key}")
        seen.add(key)


def _source_link(origin: Any) -> str | None:
    if not isinstance(origin, str) or not origin.startswith(ORIGIN_PREFIX):
        return None
    parts = origin[len(ORIGIN_PREFIX):].split(" · ", 1)
    if len(parts) != 2 or not parts[1].startswith("revision "):
        raise BridgeInputError("ambiguous Project Desk origin")
    return _id(parts[0], "source opportunity ID")


def propose_sync(desk: dict, workspace: dict) -> dict:
    """Return deterministic import proposals. Do not apply without human approval.

    A source-side DONE means only 'reported DONE', not accepted completion.
    Existing Desk items retain their IDs, statuses, evidence and decisions.
    """
    if not isinstance(desk, dict) or desk.get("schema") != DESK_SCHEMA:
        raise BridgeInputError("unrecognized Project Desk schema")
    if not isinstance(workspace, dict) or workspace.get("schema") != WORKSPACE_SCHEMA:
        raise BridgeInputError("unrecognized INTENT-OS schema")
    revision = workspace.get("revision")
    if type(revision) is not int or revision < 0:
        raise BridgeInputError("workspace revision must be a nonnegative integer")
    records = _list(workspace.get("records"), "workspace records")
    projects = _list(desk.get("projects"), "Desk projects")
    tasks = _list(desk.get("tasks"), "Desk tasks")
    imports = _list(desk.get("imports"), "Desk imports")
    _unique(records, "workspace opportunity")
    _unique(projects, "Desk project")
    _unique(tasks, "Desk task")
    _unique(imports, "Desk import")
    prior = next((entry for entry in imports if entry["id"] == IMPORT_ID), None)
    if prior is not None:
        prev_revision = prior.get("revision")
        if type(prev_revision) is not int or revision < prev_revision:
            raise BridgeInputError("stale or malformed workspace revision")
        if revision == prev_revision and workspace != prior.get("data"):
            raise BridgeInputError("same revision has conflicting contents")

    project_by_source: dict[str, dict] = {}
    for project in projects:
        key = _source_link(project.get("origin"))
        if key is not None:
            if key in project_by_source:
                raise BridgeInputError(f"duplicate Desk mapping for {key}")
            project_by_source[key] = project
    task_by_source: dict[str, dict] = {}
    for task in tasks:
        source = task.get("source")
        if not isinstance(source, str) or not source.startswith("OPP-"):
            continue
        if source in task_by_source:
            raise BridgeInputError(f"duplicate Desk task mapping for {source}")
        task_by_source[source] = task

    plan: dict[str, Any] = {
        "schema": "humanaios.project-desk.bridge.proposal.v0",
        "mode": "OFFLINE_PROPOSALS_ONLY", "requires_human_approval": True,
        "authority_effect": "NONE", "source_revision": revision,
        "source_sha256": sha256(json.dumps(workspace, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
        "new_projects": [], "linked_projects": [], "new_tasks": [],
        "linked_tasks": [], "conflicts": [],
    }
    all_task_ids: set[str] = set()
    for record in records:
        source_id = record["id"]
        source_title = record.get("title")
        if not isinstance(source_title, str) or not source_title.strip():
            raise BridgeInputError(f"missing title for {source_id}")
        project = project_by_source.get(source_id)
        if project is None:
            if any(p["id"] == source_id for p in projects):
                raise BridgeInputError(f"unrelated Desk ID collision: {source_id}")
            plan["new_projects"].append({
                "proposed_id": source_id, "source_opportunity_id": source_id,
                "name": source_title, "status": "REVIEW_REQUIRED",
                "origin": f"{ORIGIN_PREFIX}{source_id} · revision {revision}",
                "source_reported_pursuit": record.get("pursuit", "UNKNOWN"),
                "source_reported_hold": record.get("hold_reason", ""),
            })
            destination_id = source_id
        else:
            destination_id = project["id"]
            plan["linked_projects"].append({
                "source_opportunity_id": source_id, "desk_project_id": destination_id,
                "decision": "UNCHANGED_PENDING_REVIEW",
            })
            if project.get("name") != source_title:
                plan["conflicts"].append({"source_id": source_id, "type": "PROJECT_TITLE_DRIFT"})

        for source_task in _list(record.get("tasks"), "workspace tasks"):
            source_task_id = _id(source_task.get("id"), "workspace task")
            if source_task_id in all_task_ids:
                raise BridgeInputError(f"duplicate workspace task: {source_task_id}")
            all_task_ids.add(source_task_id)
            source_key = f"{source_id}/{source_task_id}"
            source_state = source_task.get("state", "UNKNOWN")
            if not isinstance(source_state, str):
                raise BridgeInputError(f"invalid task state: {source_key}")
            existing = task_by_source.get(source_key)
            if existing is None:
                if any(t["id"] == source_task_id for t in tasks):
                    raise BridgeInputError(f"unrelated Desk task ID collision: {source_task_id}")
                plan["new_tasks"].append({
                    "proposed_id": source_task_id, "source_task_id": source_task_id,
                    "source_opportunity_id": source_id, "desk_project_id": destination_id,
                    "source": source_key, "title": source_task.get("title", "Untitled task"),
                    "proposed_status": "TODO", "source_reported_state": source_state,
                    "evidence_status": "UNVERIFIED", "approval": "REQUIRED",
                })
            else:
                plan["linked_tasks"].append({
                    "source": source_key, "source_task_id": source_task_id,
                    "desk_task_id": existing["id"], "desk_project_id": existing.get("project"),
                    "current_desk_status": existing.get("status"),
                    "source_reported_state": source_state,
                    "decision": "KEEP_DESK_STATE_UNCHANGED",
                })
                if existing.get("project") != destination_id:
                    plan["conflicts"].append({"source_id": source_key, "type": "TASK_PROJECT_MISMATCH"})
                if existing.get("status") != source_state:
                    plan["conflicts"].append({"source_id": source_key, "type": "TASK_STATE_DISAGREEMENT"})
    return plan
