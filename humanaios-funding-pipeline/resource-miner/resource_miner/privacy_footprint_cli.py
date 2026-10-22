"""Local command wrapper for one bounded Privacy Footprint Mine audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import secrets
import sys
from typing import Any

from .privacy_footprint import (
    AuditDenied,
    MAX_TOTAL_BYTES,
    PrivacyAuditGrant,
    PrivacyAuditQuery,
    PrivacySource,
    run_privacy_footprint_audit,
)

__all__ = ["main"]

MAX_REQUEST_BYTES = MAX_TOTAL_BYTES + (1024 * 1024)


def _read_bounded(path: str) -> bytes:
    if path == "-":
        data = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    else:
        target = Path(path)
        if not target.is_file():
            raise AuditDenied("input must be a readable regular file or stdin")
        if target.stat().st_size > MAX_REQUEST_BYTES:
            raise AuditDenied("input exceeds the bounded request size")
        data = target.read_bytes()
    if len(data) > MAX_REQUEST_BYTES:
        raise AuditDenied("input exceeds the bounded request size")
    return data


def _tuple_fields(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    out = dict(row)
    for name in fields:
        value = out.get(name)
        if not isinstance(value, list):
            raise AuditDenied(f"{name} must be a JSON array")
        out[name] = tuple(value)
    return out


def _request(payload: Any) -> tuple[PrivacyAuditGrant, PrivacyAuditQuery, tuple[PrivacySource, ...]]:
    if not isinstance(payload, dict):
        raise AuditDenied("request must be a JSON object")
    if not isinstance(payload.get("grant"), dict):
        raise AuditDenied("request requires a grant object")
    if not isinstance(payload.get("query"), dict):
        raise AuditDenied("request requires a query object")
    if not isinstance(payload.get("sources"), list):
        raise AuditDenied("request requires a sources array")
    try:
        grant = PrivacyAuditGrant(
            **_tuple_fields(
                payload["grant"],
                ("allowed_source_ids", "allowed_operations"),
            )
        )
        query = PrivacyAuditQuery(
            **_tuple_fields(payload["query"], ("source_ids", "operations"))
        )
        sources = tuple(PrivacySource(**row) for row in payload["sources"])
    except TypeError as exc:
        raise AuditDenied("request fields do not match the privacy audit contract") from exc
    return grant, query, sources


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one local, read-only Privacy Footprint audit. Input defaults to stdin; "
            "output contains no raw detected values."
        )
    )
    parser.add_argument(
        "--input",
        default="-",
        help="JSON request file, or '-' for stdin (default)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent the privacy-minimized JSON result",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        raw = _read_bounded(args.input)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuditDenied("input must be valid UTF-8 JSON") from exc
        grant, query, sources = _request(payload)
        result = run_privacy_footprint_audit(
            grant,
            query,
            sources,
            pseudonymization_key=secrets.token_bytes(32),
        )
    except (AuditDenied, OSError) as exc:
        print(f"privacy audit denied: {exc}", file=sys.stderr)
        return 2

    json.dump(
        result.to_dict(),
        sys.stdout,
        ensure_ascii=False,
        sort_keys=True,
        indent=2 if args.pretty else None,
        separators=None if args.pretty else (",", ":"),
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
