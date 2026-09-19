"""
loader.py — HumanAIOS Funding Pipeline
Load / save Opportunity objects from CSV or JSON.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from .schema import Opportunity, PipelineSummary

# ─── Bool coercion ─────────────────────────────────────────────────────────

_BOOL_TRUE  = {"true", "1", "yes", "y", "t"}
_BOOL_FALSE = {"false", "0", "no", "n", "f", ""}


def _to_bool(val) -> bool:
    return str(val).strip().lower() in _BOOL_TRUE


def _opt(val) -> str | None:
    s = str(val).strip() if val is not None else ""
    return s if s else None


# ─── CSV ───────────────────────────────────────────────────────────────────

def load_csv(path: str | Path) -> List[Opportunity]:
    path = Path(path)
    out: List[Opportunity] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Normalise None-like empties
            row = {k: _opt(v) for k, v in row.items()}
            # eligibility_tags: pipe-separated
            tags_raw = row.get("eligibility_tags") or ""
            row["eligibility_tags"] = [t.strip() for t in tags_raw.split("|") if t.strip()]
            # Booleans
            row["native_eligible"]    = _to_bool(row.get("native_eligible"))
            row["ai_safety_relevant"] = _to_bool(row.get("ai_safety_relevant"))
            row["url_ok"] = (
                None if row.get("url_ok") is None
                else _to_bool(row["url_ok"])
            )
            out.append(Opportunity(**row))
    return out


def save_csv(items: List[Opportunity], path: str | Path) -> None:
    path = Path(path)
    if not items:
        return
    fieldnames = list(Opportunity.model_fields.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in items:
            row = item.model_dump()
            # Serialise list as pipe-separated
            row["eligibility_tags"] = "|".join(row["eligibility_tags"])
            w.writerow(row)


# ─── JSON ──────────────────────────────────────────────────────────────────

def load_json(path: str | Path) -> List[Opportunity]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Opportunity(**rec) for rec in data]


def save_json(items: List[Opportunity], path: str | Path) -> None:
    Path(path).write_text(
        json.dumps([i.model_dump() for i in items], indent=2, default=str),
        encoding="utf-8",
    )


# ─── Auto-dispatch ─────────────────────────────────────────────────────────

def load_any(path: str | Path) -> List[Opportunity]:
    p = Path(path)
    if p.suffix.lower() == ".json":
        return load_json(p)
    return load_csv(p)


# ─── Summary ───────────────────────────────────────────────────────────────

def summarise(items: List[Opportunity]) -> PipelineSummary:
    from datetime import date
    from collections import Counter

    by_cat = Counter(i.category.value for i in items)
    return PipelineSummary(
        generated=date.today().isoformat(),
        total=len(items),
        native_eligible=sum(i.native_eligible for i in items),
        ai_safety_relevant=sum(i.ai_safety_relevant for i in items),
        both_flags=sum(i.native_eligible and i.ai_safety_relevant for i in items),
        by_category=dict(by_cat),
        deadline_soon_30d=sum(i.is_deadline_soon(30) for i in items),
        active_rolling=sum(
            i.status.value in ("active", "rolling") for i in items
        ),
    )
