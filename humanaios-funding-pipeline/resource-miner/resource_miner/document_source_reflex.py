from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote

from .models import EvidenceRef, ResourceCandidate


ALLOWED_REPOSITORIES = frozenset(
    {
        "humanaios-ui/operations",
        "humanaios-ui/humanaios",
        "humanaios-ui/lasting-light-ai",
    }
)
MAX_SOURCES = 50
MAX_BINDINGS = 500
MAX_PULL_REQUESTS = 50
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_OID = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
_STATUS = {
    "ci_status": frozenset({"PASS", "FAIL", "MISSING", "UNKNOWN"}),
    "coderabbit_status": frozenset(
        {"APPROVED", "CHANGES_REQUESTED", "MISSING", "UNKNOWN"}
    ),
    "human_approval": frozenset(
        {"APPROVED", "CHANGES_REQUESTED", "MISSING", "UNKNOWN"}
    ),
    "admission_status": frozenset({"PASS", "FAIL", "MISSING", "UNKNOWN"}),
}


def _fail(message: str) -> None:
    raise ValueError(message)


def _fields(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict) or not required.issubset(value):
        _fail("Expected object with required fields")
    if set(value) - required - optional:
        _fail("Unexpected input field")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        _fail(f"Invalid {label}")
    return value


def _repo(value: Any) -> str:
    if not isinstance(value, str) or value not in ALLOWED_REPOSITORIES:
        _fail("Repository is not an allowlisted GitHub evidence source")
    return value


def _oid(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _OID.fullmatch(value):
        _fail(f"Invalid {label}")
    return value


def _path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or value.startswith("/")
        or "\\" in value
        or "//" in value
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        _fail("Invalid Git path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail("Invalid Git path")
    return value


def _timestamp(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 40:
        _fail("Invalid observation timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail("Invalid observation timestamp")
    if parsed.tzinfo is None:
        _fail("Observation timestamp must include a timezone")
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _candidate(
    *,
    finding_code: str,
    title: str,
    repo: str,
    url: str,
    observed_at: str,
    source_identity: str,
    receipt_identity: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    identity = _digest(
        {
            "finding_code": finding_code,
            "repo": repo,
            "url": url,
            "details": details,
        }
    )
    resource = ResourceCandidate(
        resource_id=f"RES-DOC-{identity[:16].upper()}",
        title=title,
        source_name=repo,
        source_url=url,
        canonical_url=url,
        discovery_method="document_source_reflex:caller_supplied",
        discovered_at=observed_at,
        description="Evidence-gathering opportunity only; input transport is unverified.",
        primary_source_url=url,
        evidence=[
            EvidenceRef(
                url=url,
                kind="caller_supplied_evidence",
                observed_at=observed_at,
                claim="Caller supplied this evidence reference; its transport provenance is unverified.",
            )
        ],
        tags=[finding_code],
        route="VERIFY_NOW",
        status="UNVERIFIED",
        resource_state="CANDIDATE",
        next_operation="VERIFY",
        opportunity_kind="evidence_gathering",
        raw={
            "finding_code": finding_code,
            "source_identity": source_identity,
            "receipt_identity": receipt_identity,
            **details,
        },
    )
    result = resource.to_dict(include_raw=True)
    result.update(
        {
            "finding_code": finding_code,
            "observation_state": "OBSERVED_FROM_CALLER_INPUT",
            "evidence_state": "UNVERIFIED",
            "transport_provenance": "UNVERIFIED_CALLER_SUPPLIED",
            "authority_effect": "NONE",
            "merge_authority": False,
        }
    )
    return result


def project_report(report: dict[str, Any]) -> dict[str, Any]:
    """Project bounded caller-supplied Git and PR facts into advisory candidates.

    This function performs no I/O. A report records what the caller supplied;
    it does not authenticate the source, receipt, review, CI, or admission facts.
    """
    report = _fields(
        report,
        {
            "source_identity",
            "receipt_identity",
            "observed_at",
            "sources",
            "bindings",
            "pull_requests",
        },
    )
    source_identity = _identifier(report["source_identity"], "source identity")
    receipt_identity = _identifier(report["receipt_identity"], "receipt identity")
    observed_at = _timestamp(report["observed_at"])
    sources = report["sources"]
    bindings = report["bindings"]
    pull_requests = report["pull_requests"]
    if (
        not isinstance(sources, list)
        or len(sources) > MAX_SOURCES
        or not isinstance(bindings, list)
        or len(bindings) > MAX_BINDINGS
        or not isinstance(pull_requests, list)
        or len(pull_requests) > MAX_PULL_REQUESTS
    ):
        _fail("Input collection is invalid or exceeds its bound")

    source_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for item in sources:
        item = _fields(
            item, {"repo", "path", "before_oid", "after_oid", "source_kind"}
        )
        repo = _repo(item["repo"])
        path = _path(item["path"])
        key = (repo, path)
        if key in source_by_key:
            _fail("Duplicate Git source")
        source_by_key[key] = {
            "repo": repo,
            "path": path,
            "before_oid": _oid(item["before_oid"], "before blob OID"),
            "after_oid": _oid(item["after_oid"], "after blob OID"),
            "source_kind": _identifier(item["source_kind"], "source kind"),
        }

    binding_rows: dict[tuple[str, str], list[dict[str, str]]] = {
        key: [] for key in source_by_key
    }
    seen_bindings: set[tuple[str, str, str, str, str]] = set()
    for item in bindings:
        item = _fields(
            item,
            {"repo", "path", "claim_id", "document_id"},
            {"claim_fingerprint"},
        )
        repo = _repo(item["repo"])
        path = _path(item["path"])
        key = (repo, path)
        if key not in source_by_key:
            _fail("Binding references an undeclared source")
        claim_id = _identifier(item["claim_id"], "claim ID")
        document_id = _identifier(item["document_id"], "document ID")
        fingerprint = item.get("claim_fingerprint", "")
        if fingerprint and (
            not isinstance(fingerprint, str) or not re.fullmatch(r"[a-f0-9]{64}", fingerprint)
        ):
            _fail("Invalid claim fingerprint")
        binding_key = (repo, path, claim_id, document_id, fingerprint)
        if binding_key in seen_bindings:
            _fail("Duplicate source-to-claim binding")
        seen_bindings.add(binding_key)
        binding_rows[key].append(
            {
                "claim_id": claim_id,
                "document_id": document_id,
                "claim_fingerprint": fingerprint,
            }
        )

    candidates: list[dict[str, Any]] = []
    source_observations = []
    for key, source in sorted(source_by_key.items()):
        links = sorted(
            binding_rows[key],
            key=lambda row: (
                row["claim_id"],
                row["document_id"],
                row["claim_fingerprint"],
            ),
        )
        changed = source["before_oid"] != source["after_oid"]
        state = "CHANGED_FROM_INPUT" if changed else "UNCHANGED_FROM_INPUT"
        source_observations.append(
            {
                "repo": source["repo"],
                "path": source["path"],
                "state": state,
                "observation_state": "OBSERVED_FROM_CALLER_INPUT",
                "transport_provenance": "UNVERIFIED_CALLER_SUPPLIED",
                "linked_claim_count": len({row["claim_id"] for row in links}),
                "dependent_document_count": len({row["document_id"] for row in links}),
                "impact_state": "UNKNOWN",
            }
        )
        if changed:
            url = (
                f"https://github.com/{source['repo']}/blob/{source['after_oid']}/"
                f"{quote(source['path'], safe='/')}"
            )
            if links:
                candidates.append(
                    _candidate(
                        finding_code="SOURCE_CHANGED_REVERIFY",
                        title="Reverify linked claims and documents after source change",
                        repo=source["repo"],
                        url=url,
                        observed_at=observed_at,
                        source_identity=source_identity,
                        receipt_identity=receipt_identity,
                        details={
                            "path": source["path"],
                            "source_kind": source["source_kind"],
                            "before_oid": source["before_oid"],
                            "after_oid": source["after_oid"],
                            "claim_ids": sorted({row["claim_id"] for row in links}),
                            "dependent_document_ids": sorted(
                                {row["document_id"] for row in links}
                            ),
                            "bindings": [
                                {
                                    "claim_id": row["claim_id"],
                                    "document_id": row["document_id"],
                                    **(
                                        {"claim_fingerprint": row["claim_fingerprint"]}
                                        if row["claim_fingerprint"]
                                        else {}
                                    ),
                                }
                                for row in links
                            ],
                            "smallest_next_steps": [
                                "ask linked document owners to reverify the listed claims"
                            ],
                            "recommendation": "VERIFY",
                        },
                    )
                )
            else:
                candidates.append(
                    _candidate(
                        finding_code="SOURCE_CHANGE_UNMAPPED",
                        title="Map changed source to claims and dependent documents",
                        repo=source["repo"],
                        url=url,
                        observed_at=observed_at,
                        source_identity=source_identity,
                        receipt_identity=receipt_identity,
                        details={
                            "path": source["path"],
                            "source_kind": source["source_kind"],
                            "before_oid": source["before_oid"],
                            "after_oid": source["after_oid"],
                            "claim_ids": [],
                            "dependent_document_ids": [],
                            "smallest_next_steps": [
                                "request explicit claim and dependent-document bindings"
                            ],
                            "recommendation": "VERIFY",
                        },
                    )
                )

        fingerprints: dict[str, set[str]] = {}
        for row in links:
            if row["claim_fingerprint"]:
                fingerprints.setdefault(row["claim_id"], set()).add(
                    row["claim_fingerprint"]
                )
        for claim_id, values in sorted(fingerprints.items()):
            if len(values) > 1:
                candidates.append(
                    _candidate(
                        finding_code="CONFLICTING_CLAIM_BINDINGS",
                        title="Resolve conflicting explicit claim bindings",
                        repo=source["repo"],
                        url=(
                            f"https://github.com/{source['repo']}/blob/"
                            f"{source['after_oid']}/{quote(source['path'], safe='/')}"
                        ),
                        observed_at=observed_at,
                        source_identity=source_identity,
                        receipt_identity=receipt_identity,
                        details={
                            "path": source["path"],
                            "claim_id": claim_id,
                            "claim_fingerprints": sorted(values),
                            "bindings": [
                                {
                                    "document_id": row["document_id"],
                                    "claim_fingerprint": row["claim_fingerprint"],
                                }
                                for row in links
                                if row["claim_id"] == claim_id
                            ],
                            "dependent_document_ids": sorted(
                                {
                                    row["document_id"]
                                    for row in links
                                    if row["claim_id"] == claim_id
                                }
                            ),
                            "smallest_next_steps": [
                                "ask claim owners to reconcile the explicit fingerprints"
                            ],
                            "recommendation": "ESCALATE",
                        },
                    )
                )

    seen_prs: set[tuple[str, int]] = set()
    pr_observations = []
    for item in pull_requests:
        item = _fields(
            item,
            {
                "repo",
                "number",
                "head_oid",
                "merged",
                "ci_status",
                "coderabbit_status",
                "human_approval",
                "admission_status",
                "receipt_head",
            },
        )
        repo = _repo(item["repo"])
        number = item["number"]
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            _fail("Invalid pull request number")
        pr_key = (repo, number)
        if pr_key in seen_prs:
            _fail("Duplicate pull request evidence")
        seen_prs.add(pr_key)
        head_oid = _oid(item["head_oid"], "pull request head OID")
        receipt_head = item["receipt_head"]
        if receipt_head is not None:
            receipt_head = _oid(receipt_head, "receipt head OID")
        if not isinstance(item["merged"], bool):
            _fail("Invalid merged state")
        for name, allowed in _STATUS.items():
            value = item[name]
            if not isinstance(value, str) or value not in allowed:
                _fail(f"Invalid {name}")
        exact_receipt = receipt_head == head_oid
        pr_observations.append(
            {
                "repo": repo,
                "number": number,
                "head_oid": head_oid,
                "merged": item["merged"],
                "receipt_head": receipt_head,
                "receipt_exact_head": exact_receipt,
                "observation_state": "OBSERVED_FROM_CALLER_INPUT",
                "transport_provenance": "UNVERIFIED_CALLER_SUPPLIED",
            }
        )
        url = f"https://github.com/{repo}/pull/{number}"
        common = {
            "pull_request": f"{repo}#{number}",
            "head_oid": head_oid,
            "receipt_head": receipt_head,
            "receipt_exact_head": exact_receipt,
            "reported_statuses": {
                name: item[name] for name in sorted(_STATUS)
            },
        }
        if receipt_head is not None and not exact_receipt:
            candidates.append(
                _candidate(
                    finding_code="STALE_RECEIPT",
                    title="Refresh PR evidence receipt for the current head",
                    repo=repo,
                    url=url,
                    observed_at=observed_at,
                    source_identity=source_identity,
                    receipt_identity=receipt_identity,
                    details={**common, "recommendation": "VERIFY"},
                )
            )
        if item["merged"] and item["admission_status"] == "FAIL" and exact_receipt:
            candidates.append(
                _candidate(
                    finding_code="MERGED_WITH_FAILED_ADMISSION",
                    title="Investigate merged PR with an exact-head admission failure",
                    repo=repo,
                    url=url,
                    observed_at=observed_at,
                    source_identity=source_identity,
                    receipt_identity=receipt_identity,
                    details={
                        **common,
                        "recommendation": "ESCALATE",
                        "note": "Investigation only; no retrofit approval or merge authority.",
                    },
                )
            )
        missing_actions = []
        if item["ci_status"] != "PASS":
            missing_actions.append("verify exact-head CI")
        if item["coderabbit_status"] != "APPROVED":
            missing_actions.append("obtain independent CodeRabbit review")
        if item["human_approval"] != "APPROVED":
            missing_actions.append("obtain human approval")
        if item["admission_status"] in {"MISSING", "UNKNOWN"} or not exact_receipt:
            missing_actions.append("verify an exact-head admission receipt")
        elif item["admission_status"] == "FAIL" and not item["merged"]:
            missing_actions.append("request an admission review decision")
        if missing_actions:
            candidates.append(
                _candidate(
                    finding_code="MISSING_VERIFICATION",
                    title="Collect missing exact-head PR verification",
                    repo=repo,
                    url=url,
                    observed_at=observed_at,
                    source_identity=source_identity,
                    receipt_identity=receipt_identity,
                    details={
                        **common,
                        "smallest_next_steps": missing_actions,
                        "recommendation": "VERIFY",
                    },
                )
            )

    candidates.sort(key=lambda row: (row["finding_code"], row["resource_id"]))
    output = {
        "schema": "humanaios.resource_miner.document_source_reflex.v0.1",
        "observed_at": observed_at,
        "source_identity": source_identity,
        "receipt_identity": receipt_identity,
        "transport_provenance": "UNVERIFIED_CALLER_SUPPLIED",
        "source_observations": source_observations,
        "pull_request_observations": pr_observations,
        "candidates": candidates,
        "overall": "UNVERIFIED",
        "authority_effect": "NONE",
        "merge_authority": False,
        "limitations": [
            "Caller-supplied facts and bindings are not authenticated observations.",
            "Missing mappings mean unknown impact, not no impact.",
            "No source payload is read; no network, branch mutation, or issue creation occurs.",
            "Candidates are evidence-gathering recommendations, never approvals or decisions.",
        ],
    }
    output["snapshot_sha256"] = _digest(output)
    return output
