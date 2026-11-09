"""Shared knowledge graph: read the repo snapshot, accept PROPOSALS only.

Proposals go to an append-only, hash-chained JSONL file outside the governed
files. Nothing here writes REGISTERED.md or marks anything ratified (Z2 does).
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .protocol import ToolError

MAX_OPEN_PER_AUTHOR = 20


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Graph:
    def __init__(self, kg_path: Path | None, state_dir: Path):
        self.kg_path = kg_path
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.proposals = state_dir / "proposals.jsonl"
        self.events = state_dir / "events.jsonl"  # polled by the n8n loop, no outbound calls
        self._lock = threading.Lock()
        self.hooks: list[Callable[[dict[str, Any]], None]] = []

    # ---- reading the snapshot -------------------------------------------------
    def _snapshot(self) -> dict[str, Any]:
        if not self.kg_path or not self.kg_path.is_file():
            return {"nodes": [], "edges": []}
        return json.loads(self.kg_path.read_text(encoding="utf-8"))

    def summary(self) -> dict[str, Any]:
        snap = self._snapshot()
        return {
            "graph_id": snap.get("graph_id"), "as_of": snap.get("as_of"),
            "authority_effect": snap.get("authority_effect", "NONE"),
            "nodes": len(snap.get("nodes", [])), "edges": len(snap.get("edges", [])),
            "open_proposals": len(self.list_proposals(limit=10**6)),
        }

    def query(self, text: str, limit: int = 10) -> dict[str, Any]:
        needle = text.lower()
        snap = self._snapshot()
        nodes = [n for n in snap.get("nodes", []) if needle in _canon(n).lower()][:limit]
        ids = {str(n.get("id")) for n in nodes if isinstance(n, dict)}
        edges = [e for e in snap.get("edges", [])
                 if isinstance(e, dict) and ({str(e.get("source")), str(e.get("target")),
                                              str(e.get("from")), str(e.get("to"))} & ids)][:limit]
        return {"nodes": nodes, "edges": edges, "authority_effect": "NONE"}

    # ---- proposals ------------------------------------------------------------
    def _records(self) -> list[dict[str, Any]]:
        if not self.proposals.is_file():
            return []
        return [json.loads(l) for l in self.proposals.read_text("utf-8").splitlines() if l.strip()]

    def list_proposals(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._records()[-limit:]

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for rec in self._records():
            body = {k: v for k, v in rec.items() if k != "hash"}
            if rec["prev_hash"] != prev or hashlib.sha256(_canon(body).encode()).hexdigest() != rec["hash"]:
                return False
            prev = rec["hash"]
        return True

    def propose_claim(self, claim: str, evidence: list[dict[str, Any]], falsifier: str,
                      author: str, tags: list[str] | None = None) -> dict[str, Any]:
        if len(falsifier.strip()) < 15:
            raise ToolError("falsifier is required: say what observation would prove the claim wrong")
        external = [e for e in evidence if not str(e.get("source", "")).startswith("hub:")]
        if not external:
            raise ToolError("evidence must include a source outside the hub (no self-reference)")
        with self._lock:
            records = self._records()
            if sum(1 for r in records if r["author"] == author) >= MAX_OPEN_PER_AUTHOR:
                raise ToolError("too many open proposals for this author; wait for Z2 review")
            body = {
                "id": f"hub:prop-{len(records) + 1:06d}", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "author": author, "claim": claim, "evidence": evidence, "falsifier": falsifier,
                "tags": tags or [], "status": "PROPOSED", "z2_hash": None,
                "authority_effect": "NONE",
                "prev_hash": records[-1]["hash"] if records else "0" * 64,
            }
            body["hash"] = hashlib.sha256(_canon(body).encode()).hexdigest()
            with self.proposals.open("a", encoding="utf-8") as fh:
                fh.write(_canon(body) + "\n")
            event = {"event": "proposal_added", "id": body["id"], "hash": body["hash"], "ts": body["ts"]}
            with self.events.open("a", encoding="utf-8") as fh:
                fh.write(_canon(event) + "\n")
        for hook in self.hooks:  # in-process only
            try:
                hook(event)
            except Exception:
                pass
        return {"id": body["id"], "hash": body["hash"], "status": "PROPOSED",
                "note": "Candidate only. Needs Z2 ratification before it counts as registered."}
