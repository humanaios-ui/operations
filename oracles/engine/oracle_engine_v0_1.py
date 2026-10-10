#!/usr/bin/env python3
"""HumanAIOS Federated Oracle pilot engine.

Implements the bounded Phase 1 pilot from issue #735:
- Workspace Oracle over normalized Google Drive observations.
- Repository Oracle over the checked-out operations repository.
- Global Oracle federation with identity reconciliation and contradiction retention.
- Candidate-change adapter into the existing Repository Coordinator.

This module does not call Google Drive or GitHub. Source connectors produce snapshots;
the engine deterministically projects them. All outputs remain advisory-only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

AUTHORITY = {
    "advisory_only": True,
    "can_authorize": False,
    "authority_effect": "NONE",
    "can_ratify": False,
    "can_merge": False,
}

SYSTEM_GRAPH_REF = "repo:humanaios-ui/operations:path:system_graph.json"


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(x) for x in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _authority_copy() -> dict[str, Any]:
    return dict(AUTHORITY)


def _assert_advisory(value: dict[str, Any]) -> None:
    authority = value.get("authority") or {}
    if authority.get("authority_effect") not in (None, "NONE"):
        raise ValueError("Oracle input attempted non-NONE authority_effect")
    if authority.get("can_authorize") is True:
        raise ValueError("Oracle input attempted can_authorize=true")


def _claim_value_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def detect_conflicts(assertions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve contradictory assertions instead of selecting a winner."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for assertion in assertions:
        grouped[(assertion["subject_ref"], assertion["predicate"])].append(assertion)

    conflicts: list[dict[str, Any]] = []
    for (subject_ref, predicate), group in sorted(grouped.items()):
        values = {_claim_value_key(item["value"]) for item in group}
        if len(values) <= 1:
            continue
        conflicts.append({
            "conflict_id": _stable_id("CONFLICT", subject_ref, predicate, *sorted(values)),
            "subject_ref": subject_ref,
            "predicate": predicate,
            "assertion_ids": [item["assertion_id"] for item in group],
            "observed_values": [item["value"] for item in group],
            "source_roles": [item.get("source_role") for item in group],
            "resolution_state": "OPEN",
            "resolution": None,
            "authority": _authority_copy(),
        })
    return conflicts


class WorkspaceOracle:
    oracle_id = "ORACLE-DOMAIN-WORKSPACE"

    def project(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        _assert_advisory(snapshot)
        if (snapshot.get("source") or {}).get("substrate") != "google_drive":
            raise ValueError("Workspace Oracle pilot accepts normalized Google Drive snapshots only")

        observed_at = snapshot["observed_at"]
        entities: list[dict[str, Any]] = []
        identities: list[dict[str, Any]] = []
        assertions: list[dict[str, Any]] = []

        for artifact in snapshot.get("artifacts") or []:
            source_id = str(artifact["id"])
            source_ref = f"drive:{source_id}"
            entities.append({
                "entity_id": source_ref,
                "entity_type": "SOURCE_OBJECT",
                "name": artifact["title"],
                "source_ref": source_ref,
                "observed_at": observed_at,
                "projection_role": artifact.get("projection_role"),
                "authority": _authority_copy(),
            })

            canonical_ref = artifact.get("canonical_ref")
            if canonical_ref:
                identities.append({
                    "source_entity_id": source_ref,
                    "canonical_ref": canonical_ref,
                    "basis": artifact.get("identity_basis") or "explicit_snapshot_binding",
                    "authority": _authority_copy(),
                })

            for claim in artifact.get("claims") or []:
                subject_ref = claim.get("subject_ref") or canonical_ref or source_ref
                predicate = str(claim["predicate"])
                value = claim["value"]
                assertions.append({
                    "assertion_id": _stable_id(
                        "WASSERT", source_ref, subject_ref, predicate, _claim_value_key(value)
                    ),
                    "oracle_id": self.oracle_id,
                    "subject_ref": subject_ref,
                    "predicate": predicate,
                    "value": value,
                    "as_of": claim.get("as_of") or artifact.get("as_of") or observed_at,
                    "recorded_at": observed_at,
                    "source_ref": source_ref,
                    "source_role": artifact.get("projection_role"),
                    "observation": claim.get("observation") or (
                        f"{artifact['title']} states {predicate}={value!r}"
                    ),
                    "authority": _authority_copy(),
                })

        conflicts = detect_conflicts(assertions)
        return {
            "schema": "humanaios.oracle.workspace-projection.v1",
            "oracle_id": self.oracle_id,
            "projection_name": "WORKSPACE_ADVISORY_GRAPH",
            "observed_at": observed_at,
            "entities": entities,
            "identity_candidates": identities,
            "assertions": assertions,
            "conflicts": conflicts,
            "authority": _authority_copy(),
        }


class RepositoryOracle:
    oracle_id = "ORACLE-DOMAIN-REPOSITORY"

    def project_operations(
        self,
        root: Path,
        *,
        observed_at: str,
        repository: str = "humanaios-ui/operations",
    ) -> dict[str, Any]:
        graph_path = root / "system_graph.json"
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        canonical_ref = f"repo:{repository}:path:system_graph.json"
        node_count = len(graph.get("nodes") or {})
        edge_count = len(graph.get("edges") or [])
        generated_at = str(graph.get("generated_at") or observed_at)

        entity = {
            "entity_id": canonical_ref,
            "entity_type": "REPOSITORY_OBJECT",
            "name": "system_graph.json",
            "repository": repository,
            "path": "system_graph.json",
            "observed_at": observed_at,
            "authority": _authority_copy(),
        }
        assertions = []
        for predicate, value in (
            ("node_count", node_count),
            ("edge_count", edge_count),
            ("generated_at", generated_at),
            ("validation_valid", bool((graph.get("validation_status") or {}).get("valid"))),
        ):
            assertions.append({
                "assertion_id": _stable_id(
                    "RASSERT", canonical_ref, predicate, _claim_value_key(value)
                ),
                "oracle_id": self.oracle_id,
                "subject_ref": canonical_ref,
                "predicate": predicate,
                "value": value,
                "as_of": generated_at,
                "recorded_at": observed_at,
                "source_ref": f"{repository}:system_graph.json",
                "source_role": "canonical_repository_observation",
                "observation": f"Checked-out system_graph.json reports {predicate}={value!r}",
                "authority": _authority_copy(),
            })

        return {
            "schema": "humanaios.oracle.repository-projection.v1",
            "oracle_id": self.oracle_id,
            "projection_name": "REPOSITORY_ADVISORY_GRAPH",
            "observed_at": observed_at,
            "entities": [entity],
            "identity_candidates": [{
                "source_entity_id": canonical_ref,
                "canonical_ref": canonical_ref,
                "basis": "repository_path_identity",
                "authority": _authority_copy(),
            }],
            "assertions": assertions,
            "conflicts": [],
            "authority": _authority_copy(),
        }


class GlobalOracle:
    oracle_id = "ORACLE-GLOBAL-001"

    def federate(
        self,
        workspace: dict[str, Any],
        repository: dict[str, Any],
        *,
        objective_issue_number: int = 735,
    ) -> dict[str, Any]:
        _assert_advisory(workspace)
        _assert_advisory(repository)

        workspace_refs: dict[str, list[str]] = defaultdict(list)
        repository_refs: dict[str, list[str]] = defaultdict(list)
        for item in workspace.get("identity_candidates") or []:
            workspace_refs[item["canonical_ref"]].append(item["source_entity_id"])
        for item in repository.get("identity_candidates") or []:
            repository_refs[item["canonical_ref"]].append(item["source_entity_id"])

        reconciliations: list[dict[str, Any]] = []
        for canonical_ref in sorted(set(workspace_refs) & set(repository_refs)):
            reconciliations.append({
                "reconciliation_id": _stable_id("IDENTITY", canonical_ref),
                "canonical_ref": canonical_ref,
                "workspace_entities": sorted(workspace_refs[canonical_ref]),
                "repository_entities": sorted(repository_refs[canonical_ref]),
                "state": "RECONCILED",
                "basis": "explicit canonical_ref equality",
                "authority": _authority_copy(),
            })

        assertions = list(workspace.get("assertions") or []) + list(
            repository.get("assertions") or []
        )
        conflicts = detect_conflicts(assertions)

        candidate_changes: list[dict[str, Any]] = []
        for conflict in conflicts:
            candidate_changes.append({
                "candidate_change_id": _stable_id(
                    "CANDIDATE", conflict["conflict_id"], objective_issue_number
                ),
                "kind": "ADVISORY_PROJECTION_CONFLICT",
                "objective_issue_number": objective_issue_number,
                "target_repository": "humanaios-ui/operations",
                "target_scope": "oracles/workspace",
                "summary": (
                    f"Preserve and review conflicting advisory values for "
                    f"{conflict['subject_ref']}::{conflict['predicate']}; "
                    "no assertion is deleted or promoted automatically."
                ),
                "evidence_assertion_ids": list(conflict["assertion_ids"]),
                "coordinator_input_only": True,
                "authority_effect": "NONE",
                "advisory_only": True,
                "can_authorize": False,
            })

        return {
            "schema": "humanaios.oracle.global-advisory-graph.v1",
            "oracle_id": self.oracle_id,
            "projection_name": "GLOBAL_ADVISORY_GRAPH",
            "identity_reconciliations": reconciliations,
            "assertions": assertions,
            "conflicts": conflicts,
            "candidate_changes": candidate_changes,
            "authority": _authority_copy(),
        }


class CoordinatorAdapter:
    """Translate an Oracle candidate into the existing coordinator's PR vocabulary.

    In this pilot the adapter emits a draft/workbench-shaped object. It cannot create a
    repository-coordinator admission record and therefore cannot self-admit work.
    """

    def to_pr_record(
        self,
        candidate: dict[str, Any],
        *,
        number: int = 999999,
    ) -> dict[str, Any]:
        if candidate.get("authority_effect") != "NONE":
            raise ValueError("Candidate change authority_effect must be NONE")
        if candidate.get("can_authorize") is True:
            raise ValueError("Candidate change cannot authorize")
        issue = int(candidate.get("objective_issue_number") or 0)
        body = (
            (f"Closes #{issue}\n\n" if issue else "")
            + "Oracle advisory candidate. Coordinator input only.\n\n"
            + str(candidate.get("summary") or "")
            + "\n\nAUTHORITY_EFFECT=NONE"
        )
        return {
            "number": number,
            "title": f"[Oracle candidate] {candidate.get('kind', 'ADVISORY_CHANGE')}",
            "body": body,
            "author": "oracle-advisory",
            "draft": True,
            "files": [],
            "files_complete": True,
            "reviews": [],
            "labels": [],
        }

    def route_with_repository_coordinator(
        self,
        candidate: dict[str, Any],
        *,
        repo_root: Path,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tool_path = repo_root / "tools" / "repository_coordinator_v0_1.py"
        spec = importlib.util.spec_from_file_location("repository_coordinator_v0_1", tool_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Cannot load repository coordinator")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        policy = json.loads(
            (repo_root / "REPOSITORY_COORDINATOR_POLICY.json").read_text(encoding="utf-8")
        )
        pr = self.to_pr_record(candidate)
        coordinator_state = state or {
            "admitted_issue_numbers": [],
            "admitted_pull_request_numbers": [],
            "active_admissions": {},
        }
        issue = int(candidate.get("objective_issue_number") or 0)
        referenced_items = {}
        if issue:
            referenced_items[str(issue)] = {
                "number": issue,
                "is_pull_request": False,
                "body": "**State:** ADMISSION_REQUESTED",
            }

        lane, details = module._base_lane(
            pr,
            policy=policy,
            state=coordinator_state,
            referenced_items=referenced_items,
        )
        return {
            "lane": lane,
            "details": details,
            "pr_record": pr,
            "authority": _authority_copy(),
        }


def run_pilot(repo_root: Path, workspace_snapshot: dict[str, Any]) -> dict[str, Any]:
    observed_at = workspace_snapshot["observed_at"]
    workspace = WorkspaceOracle().project(workspace_snapshot)
    repository = RepositoryOracle().project_operations(
        repo_root, observed_at=observed_at
    )
    global_graph = GlobalOracle().federate(workspace, repository)
    routes = [
        CoordinatorAdapter().route_with_repository_coordinator(
            candidate, repo_root=repo_root
        )
        for candidate in global_graph["candidate_changes"]
    ]
    return {
        "workspace": workspace,
        "repository": repository,
        "global": global_graph,
        "coordinator_routes": routes,
        "authority": _authority_copy(),
    }
