"""Tool registry. Three groups: route_*, kg_*, research_*. Everything is advisory."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .datasets import Datasets
from .graph import Graph
from .protocol import Tool
from .providers import load_providers
from .router import Router


class Hub:
    def __init__(self, env: dict[str, str] | None = None):
        env = env if env is not None else dict(os.environ)
        state = Path(env.get("HUB_STATE_DIR", ".hub_state"))
        kg = env.get("HUB_KG_PATH", "kg/humanaios_kg_v0_1.json")
        ds = env.get("HUB_DATASET_ROOT")
        self.router = Router(load_providers(env), state, int(env.get("HUB_MAX_CALLS_PER_HOUR", "60")))
        self.graph = Graph(Path(kg), state)
        self.datasets = Datasets(Path(ds) if ds else None)

    def tools(self) -> dict[str, Tool]:
        S = lambda **kw: {"type": "string", **kw}
        obj = lambda props, req=(): {"type": "object", "properties": props,
                                     "required": list(req), "additionalProperties": False}
        ts = [
            Tool("route_bots", "List configured bots, their tags, and model-judged reliability.",
                 obj({}), lambda a: {"bots": [p.info() for p in self.router.providers.values()],
                                     "reliability": self.router.reliability()}),
            Tool("route_research",
                 "Send a research question to the best bot, then have a DIFFERENT bot check its claims. "
                 "Returns candidate claims with sources and falsifiers. Advisory only.",
                 obj({"question": S(minLength=5, maxLength=4000),
                      "bot": S(maxLength=64),
                      "verify": {"type": "boolean"},
                      "max_calls": {"type": "integer", "minimum": 1, "maximum": 8}}, ["question"]),
                 lambda a: self.router.research(a["question"], a.get("bot"), a.get("verify", True),
                                                a.get("max_calls", 3)), read_only=False),
            Tool("kg_summary", "Counts and status of the shared knowledge graph.",
                 obj({}), lambda a: self.graph.summary()),
            Tool("kg_query", "Search graph nodes and edges by text.",
                 obj({"text": S(minLength=2, maxLength=200),
                      "limit": {"type": "integer", "minimum": 1, "maximum": 50}}, ["text"]),
                 lambda a: self.graph.query(a["text"], a.get("limit", 10))),
            Tool("kg_propose_claim",
                 "Stage a claim as a PROPOSAL. Needs evidence outside the hub and a falsifier. "
                 "Never registered until Z2 ratifies.",
                 obj({"claim": S(minLength=10, maxLength=2000),
                      "evidence": {"type": "array", "minItems": 1, "maxItems": 10,
                                   "items": obj({"source": S(minLength=3, maxLength=500),
                                                 "quote": S(maxLength=1000)}, ["source"])},
                      "falsifier": S(minLength=15, maxLength=1000),
                      "author": S(minLength=1, maxLength=64),
                      "tags": {"type": "array", "maxItems": 10, "items": S(maxLength=40)}},
                     ["claim", "evidence", "falsifier", "author"]),
                 lambda a: self.graph.propose_claim(a["claim"], a["evidence"], a["falsifier"],
                                                    a["author"], a.get("tags")), read_only=False),
            Tool("kg_proposals", "List staged proposals (newest last) and check the hash chain.",
                 obj({"limit": {"type": "integer", "minimum": 1, "maximum": 100}}),
                 lambda a: {"proposals": self.graph.list_proposals(a.get("limit", 20)),
                            "chain_ok": self.graph.verify_chain()}),
            Tool("research_datasets", "List files in the configured research data directory (read-only).",
                 obj({}), lambda a: {"datasets": self.datasets.list()}),
            Tool("research_dataset_read", "Read part of one dataset file (read-only, 64KB max per call).",
                 obj({"name": S(minLength=1, maxLength=300),
                      "offset": {"type": "integer", "minimum": 0},
                      "length": {"type": "integer", "minimum": 1, "maximum": 65536}}, ["name"]),
                 lambda a: self.datasets.read(a["name"], a.get("offset", 0), a.get("length", 65536))),
        ]
        return {t.name: t for t in ts}
