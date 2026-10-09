from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from ..models import EvidenceRef, ResourceCandidate, ResourceMine
from ..normalize import normalize_generic

FORBIDDEN_PRIVATE_FIELDS = {
    "gmail_message_id",
    "gmail_thread_id",
    "raw_body",
    "body",
    "raw_mime",
    "mailbox_url",
    "display_url",
    "private_event_ref",
}


def _projection_path(mine: ResourceMine) -> Path:
    env_name = str(
        mine.config.get("projection_env")
        or "HUMANAIOS_GMAIL_MINE_SNAPSHOT"
    ).strip()
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise ModuleNotFoundError(
            f"private Gmail Mine requires privacy-minimized runtime projection via {env_name}"
        )
    return Path(value)


def _validate_projection(row: dict, mine: ResourceMine) -> None:
    leaked = sorted(FORBIDDEN_PRIVATE_FIELDS.intersection(row))
    if leaked:
        raise ValueError(
            "private Gmail projection contains forbidden private fields: "
            + ", ".join(leaked)
        )
    mailbox = str(row.get("mailbox") or "").strip().lower()
    expected = str(mine.config.get("mailbox") or "").strip().lower()
    if expected and mailbox != expected:
        raise ValueError("private Gmail projection mailbox binding mismatch")
    required = [
        "observed_at",
        "opportunity_identity",
        "opportunity_kind",
        "title",
        "canonical_url",
        "evidence_claim",
    ]
    missing = [field for field in required if not str(row.get(field) or "").strip()]
    if missing:
        raise ValueError(
            "private Gmail projection missing required fields: "
            + ", ".join(missing)
        )


def discover(mine: ResourceMine) -> Iterable[ResourceCandidate]:
    """Read a privacy-minimized projection produced by the private Gmail runtime.

    This adapter never authenticates to Gmail and never accepts raw message bodies,
    Gmail message/thread IDs, mailbox URLs, or private event references. The private
    Gmail adapter owns those values. This public-side resolver consumes only bounded
    projections suitable for Resource Miner.
    """
    path = _projection_path(mine)
    if not path.exists():
        raise ModuleNotFoundError(
            "private Gmail Mine projection path is not available in this runtime"
        )

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError("private Gmail projection rows must be JSON objects")
        _validate_projection(row, mine)

        candidate = normalize_generic(
            title=str(row["title"]),
            url=str(row["canonical_url"]),
            source_name=mine.name,
            discovery_method="private_gmail_projection",
            description=str(row.get("description") or ""),
            sponsor=str(row.get("sponsor") or ""),
            tags=[str(x) for x in row.get("tags") or []],
            source_category=str(row.get("source_category") or ""),
            body_text=str(row.get("normalized_text") or ""),
            observed_at=str(row["observed_at"]),
            mine_name=mine.name,
            mine_url=mine.canonical_url,
            opportunity_identity=str(row["opportunity_identity"]),
            opportunity_kind=str(row["opportunity_kind"]),
            opportunity_source_kind="private_gmail_projection",
            raw={
                "privacy_minimized": True,
                "content_trust": "UNTRUSTED_EVIDENCE",
                "instruction_authority": "NONE",
                "authority_effect": "NONE",
            },
        )
        candidate.evidence.append(
            EvidenceRef(
                url=str(row["canonical_url"]),
                kind=str(row.get("evidence_kind") or "private_mail_projection"),
                observed_at=str(row["observed_at"]),
                claim=str(row["evidence_claim"]),
            )
        )
        yield candidate
