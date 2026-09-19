from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from bio_framework_core_v1_2 import Element, ResourcePool


@dataclass
class TraceEvent:
    tick: int
    component: str
    action: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    delta: Dict[str, float]
    signal: Dict[str, Any] | None = None
    metadata: Dict[str, Any] | None = None


class EventTracer:
    def __init__(self) -> None:
        self.events: List[TraceEvent] = []

    def record(self, event: TraceEvent) -> None:
        self.events.append(event)

    def write_jsonl(self, path: str | Path) -> Path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as handle:
            for event in self.events:
                handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return out_path


def snapshot(resources: ResourcePool) -> Dict[str, Any]:
    return {
        "qi": {element.value: resources.qi_of(element) for element in Element},
        "blood": resources.blood,
        "jinye": resources.jinye,
        "shen": resources.shen,
    }


def diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, float]:
    delta = {
        "blood": after["blood"] - before["blood"],
        "jinye": after["jinye"] - before["jinye"],
        "shen": after["shen"] - before["shen"],
    }
    for key, value in after["qi"].items():
        delta[f"qi_{key}"] = value - before["qi"][key]
    return delta
