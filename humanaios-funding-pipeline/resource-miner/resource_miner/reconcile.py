from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_OBSERVATION_TYPES = {"CURRENTNESS", "OWNERSHIP"}
ALLOWED_SOURCE_KINDS = {
    "PRIMARY_SOURCE",
    "HUMAN_ATTESTED",
    "SYSTEM_RECEIPT",
    "REPOSITORY_EVIDENCE",
}
OWNERSHIP_SOURCE_KINDS = {"HUMAN_ATTESTED", "SYSTEM_RECEIPT", "REPOSITORY_EVIDENCE"}
CLOSED_STATES = {"CLOSED", "EXPIRED", "NOT_AVAILABLE"}
WATCH_STATES = {"NOT_CURRENTLY_OPEN", "PAUSED", "UPCOMING"}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def validate_receipt(receipt: dict[str, Any]) -> None:
    required = ("receipt_id", "resource_id", "observed_at", "observation_type", "source_kind")
    for key in required:
        if not str(receipt.get(key) or "").strip():
            raise ValueError(f"State receipt missing {key}")

    observation_type = str(receipt["observation_type"]).upper()
    source_kind = str(receipt["source_kind"]).upper()
    if observation_type not in ALLOWED_OBSERVATION_TYPES:
        raise ValueError(f"Unsupported observation_type: {observation_type}")
    if source_kind not in ALLOWED_SOURCE_KINDS:
        raise ValueError(f"Unsupported source_kind: {source_kind}")
    if str(receipt.get("authority_effect") or "NONE").upper() != "NONE":
        raise ValueError("State reconciliation cannot grant authority")

    if observation_type == "CURRENTNESS":
        if source_kind != "PRIMARY_SOURCE":
            raise ValueError("CURRENTNESS transition requires PRIMARY_SOURCE evidence")
        if not str(receipt.get("to_status") or "").strip():
            raise ValueError("CURRENTNESS receipt missing to_status")

    if observation_type == "OWNERSHIP":
        if source_kind not in OWNERSHIP_SOURCE_KINDS:
            raise ValueError("OWNERSHIP transition requires user/system/repository evidence")
        if str(receipt.get("to_resource_state") or "").upper() != "ALREADY_ACQUIRED":
            raise ValueError("OWNERSHIP receipt must establish ALREADY_ACQUIRED")


def _append_receipt(row: dict[str, Any], receipt_id: str) -> None:
    ids = list(row.get("state_receipt_ids") or [])
    if receipt_id not in ids:
        ids.append(receipt_id)
    row["state_receipt_ids"] = ids


def _is_older_currentness(row: dict[str, Any], receipt: dict[str, Any]) -> bool:
    last = str(row.get("last_verified_at") or "")
    observed = str(receipt.get("observed_at") or "")
    return bool(last and observed and observed < last)


def apply_receipt(row: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    validate_receipt(receipt)
    if str(row.get("resource_id") or "") != str(receipt["resource_id"]):
        raise ValueError("Receipt resource_id does not match candidate")

    out = dict(row)
    receipt_id = str(receipt["receipt_id"])
    if receipt_id in set(out.get("state_receipt_ids") or []):
        return out

    observation_type = str(receipt["observation_type"]).upper()

    if observation_type == "CURRENTNESS":
        if _is_older_currentness(out, receipt):
            _append_receipt(out, receipt_id)
            return out

        to_status = str(receipt["to_status"]).upper()
        out["status"] = to_status
        out["last_verified_at"] = receipt["observed_at"]

        if to_status in CLOSED_STATES:
            out["route"] = "ARCHIVE"
            out["next_operation"] = "NONE"
        elif to_status in WATCH_STATES:
            out["route"] = "WATCH"
            out["next_operation"] = "MONITOR"
        else:
            # Currentness may reopen a candidate, but it cannot establish
            # eligibility or authorization. Preserve existing match routing.
            out["next_operation"] = "VERIFY_ELIGIBILITY"

    elif observation_type == "OWNERSHIP":
        out["resource_state"] = "ALREADY_ACQUIRED"
        # Keep the discovery object visible but remove it from the pursuit
        # frontier. The next operation belongs to resource management.
        out["route"] = "WATCH"
        out["next_operation"] = "MANAGE"
        if receipt.get("observed_at"):
            out["last_verified_at"] = max(
                str(out.get("last_verified_at") or ""),
                str(receipt["observed_at"]),
            )

    _append_receipt(out, receipt_id)
    return out


def reconcile_rows(
    rows: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {str(row.get("resource_id") or ""): dict(row) for row in rows}
    audit: list[dict[str, Any]] = []

    for receipt in sorted(receipts, key=lambda r: (str(r.get("observed_at") or ""), str(r.get("receipt_id") or ""))):
        validate_receipt(receipt)
        resource_id = str(receipt["resource_id"])
        row = by_id.get(resource_id)
        if row is None:
            audit.append({
                "receipt_id": receipt["receipt_id"],
                "resource_id": resource_id,
                "result": "RESOURCE_NOT_IN_SNAPSHOT",
            })
            continue

        before = {
            "status": row.get("status"),
            "resource_state": row.get("resource_state", "CANDIDATE"),
            "route": row.get("route"),
            "next_operation": row.get("next_operation", "VERIFY"),
        }
        updated = apply_receipt(row, receipt)
        by_id[resource_id] = updated
        after = {
            "status": updated.get("status"),
            "resource_state": updated.get("resource_state", "CANDIDATE"),
            "route": updated.get("route"),
            "next_operation": updated.get("next_operation", "VERIFY"),
        }
        audit.append({
            "receipt_id": receipt["receipt_id"],
            "resource_id": resource_id,
            "result": "APPLIED" if before != after else "NO_STATE_CHANGE",
            "before": before,
            "after": after,
        })

    # Preserve original ordering to keep snapshot diffs reviewable.
    reconciled = [by_id[str(row.get("resource_id") or "")] for row in rows]
    return reconciled, audit


def reconcile_snapshot(
    snapshot_path: str | Path,
    receipts_path: str | Path,
    out_path: str | Path | None = None,
    audit_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    rows = _read_jsonl(snapshot_path)
    receipts = _read_jsonl(receipts_path)
    reconciled, audit = reconcile_rows(rows, receipts)
    _write_jsonl(out_path or snapshot_path, reconciled)
    if audit_path:
        _write_jsonl(audit_path, audit)
    return audit
