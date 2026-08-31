#!/usr/bin/env python3
"""
Shared-Memory Census (SMC) v0.1 — Copilot implementation.
Mechanical enumeration of units, extraction of referenced stores,
bipartite graph construction, tier classification, and metrics.
No interpretation of prior SMC results; runs fresh from this specification.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

POPULATIONS = {
    "tools_py": "tools/*.py",
    "docs": "docs/**",
    "workflows": ".github/workflows/*",
    "agents_skills": ".agents/skills/**",
    "root_md": "root *.md",
}

STORE_EXTS = (".py", ".yml", ".yaml", ".md", ".json", ".jsonl", ".sh", ".csv", ".html")

SPINE_NAMES = {
    "REGISTERED.md",
    "GOVERNANCE.md",
    "SESSION_RITUALS.md",
    "CURRENT.md",
}

QUOTED_RE = re.compile(
    r'''(?P<q>["\'`])(?P<path>[^"\'`\n]+?\.(?:py|yml|yaml|md|json|jsonl|sh|csv|html))\1''',
    re.IGNORECASE,
)
INLINE_RE = re.compile(
    r'''(?P<path>(?:[\w./-]+/)?[\w.-]+\.(?:py|yml|yaml|md|json|jsonl|sh|csv|html))\b''',
    re.IGNORECASE,
)

L0_MARKERS = re.compile(
    r'''(?:session[-_]?|tmp|temp|scratch|transient|stamped|timestamp|_\d{8}|T\d{6}Z)''',
    re.IGNORECASE,
)


def normalize_ref(raw: str) -> str:
    s = raw.strip().lstrip("./")
    for prefix in ("operations/", "humanaios-ui/operations/", "repo/"):
        if s.startswith(prefix):
            s = s[len(prefix) :]
    return s


def basename_key(path: str) -> str:
    return Path(path).name


def enumerate_units() -> Dict[str, List[Path]]:
    units: Dict[str, List[Path]] = {
        "tools_py": [],
        "docs": [],
        "workflows": [],
        "agents_skills": [],
        "root_md": [],
    }
    tools_dir = REPO_ROOT / "tools"
    if tools_dir.is_dir():
        units["tools_py"] = sorted(tools_dir.glob("*.py"))
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.is_dir():
        units["docs"] = sorted(p for p in docs_dir.rglob("*") if p.is_file())
    wf_dir = REPO_ROOT / ".github" / "workflows"
    if wf_dir.is_dir():
        units["workflows"] = sorted(p for p in wf_dir.iterdir() if p.is_file())
    agents_dir = REPO_ROOT / ".agents" / "skills"
    if agents_dir.is_dir():
        units["agents_skills"] = sorted(p for p in agents_dir.rglob("*") if p.is_file())
    units["root_md"] = sorted(
        p for p in REPO_ROOT.glob("*.md") if p.is_file() and p.parent == REPO_ROOT
    )
    return units


def extract_refs(text: str) -> Set[str]:
    refs: Set[str] = set()
    for m in QUOTED_RE.finditer(text):
        refs.add(normalize_ref(m.group("path")))
    for m in INLINE_RE.finditer(text):
        candidate = normalize_ref(m.group("path"))
        if len(Path(candidate).name) > 3:
            refs.add(candidate)
    return refs


def build_graph(
    units: Dict[str, List[Path]],
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, str]]:
    unit_to_stores: Dict[str, Set[str]] = {}
    store_to_units: Dict[str, Set[str]] = defaultdict(set)
    unit_pop: Dict[str, str] = {}
    for pop, paths in units.items():
        for p in paths:
            try:
                rel = str(p.relative_to(REPO_ROOT))
            except ValueError:
                rel = str(p)
            unit_pop[rel] = pop
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            refs = extract_refs(text)
            unit_to_stores[rel] = refs
            for r in refs:
                store_to_units[r].add(rel)
    return unit_to_stores, dict(store_to_units), unit_pop


def is_shared(store: str, store_to_units: Dict[str, Set[str]]) -> bool:
    return len(store_to_units.get(store, set())) >= 2


def classify_tier(store: str, store_to_units: Dict[str, Set[str]]) -> str:
    bn = basename_key(store).lower()
    if bn in {s.lower() for s in SPINE_NAMES} or bn in (
        "governance.md",
        "registered.md",
        "session_rituals.md",
        "current.md",
        "seed.md",
        "constitution.json",
        "principles_seed_v1_0.md",
    ):
        return "L3"
    if bn in (
        "registered.md",
        "governance.md",
        "session_rituals.md",
        "current.md",
        "control_documents.md",
        "document-registry.yaml",
    ) or "governance" in bn or "registered" in bn:
        return "L2"
    if L0_MARKERS.search(store) or "session" in bn or "tmp" in bn or "scratch" in bn:
        return "L0"
    n = len(store_to_units.get(store, set()))
    if n == 1:
        return "L1"
    if n >= 2:
        return "L2"
    return "L1"


def file_exists_in_repo(ref: str) -> bool:
    candidate = REPO_ROOT / ref
    if candidate.exists() and candidate.is_file():
        return True
    bn = basename_key(ref)
    if not bn or bn in (".", ".."):
        return False
    for root, _dirs, files in os.walk(REPO_ROOT):
        if bn in files:
            return True
    return False


def compute_metrics(
    units: Dict[str, List[Path]],
    unit_to_stores: Dict[str, Set[str]],
    store_to_units: Dict[str, Set[str]],
    unit_pop: Dict[str, str],
) -> dict:
    shared_stores = {s for s, us in store_to_units.items() if len(us) >= 2}
    all_refs = set(store_to_units.keys())
    exists_map = {r: file_exists_in_repo(r) for r in all_refs}
    per_pop = {}
    for pop in POPULATIONS:
        pop_units = [u for u, p in unit_pop.items() if p == pop]
        n = len(pop_units)
        if n == 0:
            per_pop[pop] = {
                "unit_count": 0,
                "isolation_rate": None,
                "spine_attachment": None,
                "dangling_rate": None,
                "sha256_users": 0,
                "chain_users": 0,
            }
            continue
        isolated = 0
        spine = 0
        dangling_units = 0
        sha256_users = 0
        chain_users = 0
        for u in pop_units:
            stores = unit_to_stores.get(u, set())
            shared_hits = stores & shared_stores
            if not shared_hits:
                isolated += 1
            bn_stores = {basename_key(s).lower() for s in stores}
            if bn_stores & {s.lower() for s in SPINE_NAMES}:
                spine += 1
            if any(not exists_map.get(s, False) for s in stores):
                dangling_units += 1
            try:
                text = (REPO_ROOT / u).read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            if re.search(r"sha256|hashlib\.sha256", text, re.IGNORECASE):
                sha256_users += 1
            if re.search(
                r"previous[_-]?hash|chain[_-]?hash|parent[_-]?hash|prev_sha",
                text,
                re.IGNORECASE,
            ):
                chain_users += 1
        per_pop[pop] = {
            "unit_count": n,
            "isolation_rate": round(isolated / n, 4),
            "spine_attachment": round(spine / n, 4),
            "dangling_rate": round(dangling_units / n, 4),
            "sha256_users": sha256_users,
            "chain_users": chain_users,
        }
    shared_ranked = sorted(
        ((s, len(us)) for s, us in store_to_units.items() if len(us) >= 2),
        key=lambda x: (-x[1], x[0]),
    )[:25]
    dangling_ranked = sorted(
        ((s, len(us)) for s, us in store_to_units.items() if not exists_map.get(s, False)),
        key=lambda x: (-x[1], x[0]),
    )[:25]
    tier_counts = defaultdict(int)
    for s in shared_stores:
        tier_counts[classify_tier(s, store_to_units)] += 1
    return {
        "version": "smc_copilot_v0.1",
        "repo_root": str(REPO_ROOT),
        "populations": {k: {"glob": v, "count": per_pop[k]["unit_count"]} for k, v in POPULATIONS.items()},
        "per_population_metrics": per_pop,
        "shared_store_count": len(shared_stores),
        "total_store_refs": len(store_to_units),
        "top_shared_stores": [{"store": s, "unit_count": c} for s, c in shared_ranked],
        "top_dangling_targets": [{"store": s, "unit_count": c} for s, c in dangling_ranked],
        "shared_tier_distribution": dict(tier_counts),
        "spine_documents": sorted(SPINE_NAMES),
    }


def main() -> int:
    units = enumerate_units()
    unit_to_stores, store_to_units, unit_pop = build_graph(units)
    metrics = compute_metrics(units, unit_to_stores, store_to_units, unit_pop)
    out_dir = REPO_ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / "smc_copilot_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Wrote {metrics_path}")
    print(json.dumps({k: metrics["per_population_metrics"][k] for k in metrics["per_population_metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
