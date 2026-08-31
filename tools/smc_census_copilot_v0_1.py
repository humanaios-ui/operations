#!/usr/bin/env python3
"""Shared-Memory Census (SMC) v0.1.

This script performs the fresh repository census described in the issue:
1. enumerate the named populations,
2. extract referenced artifact filenames,
3. build the unit ↔ store graph,
4. classify stores by memory tier,
5. report isolation, danglingness, spine attachment, and hash-chain coverage.

The script writes both machine-readable JSON metrics and a human-readable
findings summary to the repository outputs and docs locations.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ASSET_SUFFIXES = (".py", ".yml", ".md", ".json", ".jsonl", ".sh", ".csv", ".html")
SPINE_STORES = {"REGISTERED.md", "GOVERNANCE.md", "SESSION_RITUALS.md", "CURRENT.md"}
ROOT_ANCHORS = {
    "README.md",
    "START_HERE.md",
    "SEED.md",
    "CURRENT.md",
    "GOVERNANCE.md",
    "SESSION_RITUALS.md",
    "REGISTERED.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_reference(raw: str) -> str:
    value = raw.strip().strip("`\"'[](){}<>\n\r")
    value = value.replace("\\", "/")
    while value and value[0] in "./":
        value = value[1:]
    while value.endswith((",", ".", ":", ";", "!", "?")):
        value = value[:-1]
    return value


def list_unit_files(root: Path) -> Dict[str, List[Path]]:
    """Return the five mandated unit populations as relative file paths."""
    populations: Dict[str, List[Path]] = {}

    tools_files = sorted((root / "tools").glob("*.py"))
    populations["tools/*.py"] = tools_files

    docs_files = sorted(path for path in (root / "docs").rglob("*") if path.is_file())
    populations["docs/**"] = docs_files

    workflows_files = sorted((root / ".github" / "workflows").glob("*"))
    populations[".github/workflows/*"] = [p for p in workflows_files if p.is_file()]

    skills_files = sorted(path for path in (root / ".agents" / "skills").rglob("*") if path.is_file())
    populations[".agents/skills/**"] = skills_files

    root_md_files = sorted(path for path in root.glob("*.md") if path.is_file())
    populations["root *.md"] = root_md_files

    return populations


def extract_references_from_text(text: str) -> Set[str]:
    quoted_pattern = re.compile(r'(["\'])([^"\']+\.(?:py|yml|md|json|jsonl|sh|csv|html))\1')
    inline_pattern = re.compile(
        r'(?<![A-Za-z0-9_.*?/\\-])([A-Za-z0-9_./-]+\.(?:py|yml|md|json|jsonl|sh|csv|html))(?![A-Za-z0-9_.*?/\\-])'
    )

    matches: Set[str] = set()
    for pattern in (quoted_pattern, inline_pattern):
        for match in pattern.finditer(text):
            candidate = match.group(0) if pattern is quoted_pattern else match.group(1)
            if candidate.startswith(('"', "'")) and candidate.endswith(('"', "'")):
                candidate = candidate[1:-1]
            if any(token in candidate for token in ('*', '?', ' ', '\t')):
                continue
            normalized = normalize_reference(candidate)
            if normalized:
                matches.add(normalized)
    return matches


def normalize_repo_store(ref: str, unit_path: Path | None = None, root: Path | None = None) -> str:
    ref = normalize_reference(ref)
    if not ref:
        return ""

    if root is not None:
        root_str = str(root).replace("\\", "/")
        if ref.startswith(root_str):
            ref = ref[len(root_str):].lstrip("/")

    if ref.startswith("/"):
        ref = ref.lstrip("/")

    if ref.startswith("./"):
        ref = ref[2:]

    if ref.startswith("../"):
        ref = ref[3:]

    if unit_path is not None and "/" not in ref and not ref.startswith("."):
        candidate = str(Path(unit_path).parent / ref)
        candidate = candidate.replace("\\", "/")
        if root is not None:
            root_str = str(root).replace("\\", "/")
            if candidate.startswith(root_str):
                candidate = candidate[len(root_str):].lstrip("/")
        if candidate.startswith("./"):
            candidate = candidate[2:]
        if candidate.startswith("/"):
            candidate = candidate.lstrip("/")
        if candidate != ref:
            ref = candidate

    return ref


def candidate_exists(store: str, root: Path) -> bool:
    if not store:
        return False
    normalized = normalize_repo_store(store)
    if not normalized:
        return False

    if (root / normalized).exists():
        return True
    if (root / normalized).is_file():
        return True

    basename = Path(normalized).name
    matches = [p for p in root.rglob(basename) if p.is_file()]
    return bool(matches)


def classify_store(store: str) -> str:
    lower = store.lower()
    name = Path(store).name.lower()

    if name in SPINE_STORES or "governance" in lower or "registered" in lower or "session_rituals" in lower or "current.md" in lower:
        return "L2"

    if lower.startswith("outputs/") or "/outputs/" in lower or re.search(r"(?:_output|_summary|_report|_metrics|_findings|_result|_snapshot)", name):
        return "L1"

    if "session" in lower or "transient" in lower or "temp" in lower or "scratch" in lower or re.search(r"(?:session|tmp|draft|archive|checkpoint|log)-?\d", lower):
        return "L0"

    if Path(store).parent.name == "." and name in ROOT_ANCHORS:
        return "L3"

    if lower.startswith("docs/") or "doc" in lower:
        return "L2"

    if lower.startswith(".github/") or lower.startswith(".agents/"):
        return "L1"

    return "L1"


def scan_unit(root: Path, unit_path: Path) -> Dict[str, object]:
    text = unit_path.read_text(encoding="utf-8", errors="replace")
    references = sorted(
        normalize_repo_store(ref, unit_path, root)
        for ref in extract_references_from_text(text)
        if ref.lower().endswith(ASSET_SUFFIXES)
    )
    return {
        "path": str(unit_path.relative_to(root)),
        "references": references,
        "dangling": [ref for ref in references if not candidate_exists(ref, root)],
        "uses_sha256": "sha256" in text.lower(),
        "chained_hash": bool(re.search(r"(?:previous|prior|ancestor|parent|last).*sha256|sha256.*(?:previous|prior|ancestor|parent|last)", text.lower())),
    }


def build_bipartite_graph(root: Path, units: Dict[str, List[Path]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, Dict[str, object]]]:
    unit_to_stores: Dict[str, List[str]] = {}
    store_to_units: Dict[str, List[str]] = defaultdict(list)
    unit_scan: Dict[str, Dict[str, object]] = {}

    for population, paths in units.items():
        for unit in paths:
            rel = str(unit.relative_to(root))
            scan = scan_unit(root, unit)
            unique_refs = sorted(set(scan["references"]))
            unit_to_stores[rel] = unique_refs
            for store in unique_refs:
                store_to_units[store].append(rel)
            unit_scan[rel] = scan

    return unit_to_stores, dict(store_to_units), unit_scan


def summarize_population(
    population: str,
    units: List[Path],
    store_to_units: Dict[str, List[str]],
    unit_to_stores: Dict[str, List[str]],
    unit_scan: Dict[str, Dict[str, object]],
    root: Path,
) -> Dict[str, object]:
    population_names = {str(unit.relative_to(root)) for unit in units}
    population_unit_to_stores = {key: refs for key, refs in unit_to_stores.items() if key in population_names}
    population_store_to_units: Dict[str, List[str]] = defaultdict(list)
    for key, refs in population_unit_to_stores.items():
        for ref in refs:
            population_store_to_units[ref].append(key)

    total_units = len(units)
    shared_stores = {store: units_for_store for store, units_for_store in population_store_to_units.items() if len(units_for_store) >= 2}
    isolation_count = sum(1 for record in population_unit_to_stores.values() if not any(store in shared_stores for store in record))
    spine_count = sum(1 for record in population_unit_to_stores.values() if any(Path(store).name in SPINE_STORES for store in record))
    population_scan = {key: info for key, info in unit_scan.items() if key in population_names}
    dangling_units = sum(1 for info in population_scan.values() if info["dangling"])
    dangling_refs = Counter()
    for info in population_scan.values():
        for ref in info["dangling"]:
            dangling_refs[ref] += 1
    uses_sha256 = sum(1 for info in population_scan.values() if info["uses_sha256"])
    chained_hash = sum(1 for info in population_scan.values() if info["chained_hash"])

    report = {
        "population": population,
        "unit_count": total_units,
        "isolation_rate": round((isolation_count / total_units * 100.0), 2) if total_units else 0.0,
        "spine_attachment_rate": round((spine_count / total_units * 100.0), 2) if total_units else 0.0,
        "dangling_rate": round((dangling_units / total_units * 100.0), 2) if total_units else 0.0,
        "chain_coverage": {
            "using_sha256": uses_sha256,
            "chaining_to_previous_hash": chained_hash,
            "coverage_rate": round((chained_hash / total_units * 100.0), 2) if total_units else 0.0,
        },
        "shared_store_count": len(shared_stores),
        "top_shared_stores": [
            {"store": store, "count": len(population_store_to_units[store]), "tier": classify_store(store)}
            for store, _ in sorted(shared_stores.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
        ],
        "top_dangling_targets": [
            {"store": store, "count": count}
            for store, count in dangling_refs.most_common(10)
        ],
        "isolated_units": sorted(
            key for key, refs in population_unit_to_stores.items() if not any(store in shared_stores for store in refs)
        ),
        "spine_units": sorted(
            key for key, refs in population_unit_to_stores.items() if any(Path(store).name in SPINE_STORES for store in refs)
        ),
        "dangling_units": sorted(key for key, info in population_scan.items() if info["dangling"]),
    }
    return report


def render_findings(metrics: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Shared-Memory Census Findings")
    lines.append("")
    lines.append("Generated from a fresh repository scan of the five mandated unit populations: tools/*.py, docs/**, .github/workflows/*, .agents/skills/**, and root *.md.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Population | Units | Isolation | Spine | Dangling | Chain coverage |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for population in ["tools/*.py", "docs/**", ".github/workflows/*", ".agents/skills/**", "root *.md"]:
        report = metrics["population_metrics"][population]
        lines.append(
            f"| {population} | {report['unit_count']} | {report['isolation_rate']}% | {report['spine_attachment_rate']}% | {report['dangling_rate']}% | {report['chain_coverage']['coverage_rate']}% |"
        )

    lines.append("")
    lines.append("## Findings")
    lines.append("")

    findings = metrics.get("findings", [])
    for idx, finding in enumerate(findings, start=1):
        lines.append(f"### {idx}. {finding['title']}")
        lines.append("")
        lines.append(f"- Metric: {finding['metric']}")
        lines.append(f"- Finding: {finding['finding']}")
        lines.append(f"- Falsifier: {finding['falsifier']}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def generate_metrics(root: Path) -> Dict[str, object]:
    unit_map = list_unit_files(root)
    unit_to_stores, store_to_units, unit_scan = build_bipartite_graph(root, unit_map)
    population_metrics: Dict[str, Dict[str, object]] = {}
    for population, paths in unit_map.items():
        population_metrics[population] = summarize_population(population, paths, store_to_units, unit_to_stores, unit_scan, root)

    shared_store_counts = Counter()
    for store, refs in store_to_units.items():
        if len(refs) >= 2:
            shared_store_counts[store] = len(refs)

    dangling_counts = Counter()
    for info in unit_scan.values():
        for ref in info["dangling"]:
            dangling_counts[ref] += 1

    findings: List[Dict[str, str]] = []
    for population, report in population_metrics.items():
        if report["isolation_rate"] > 0 and report["unit_count"]:
            findings.append(
                {
                    "title": f"{population} units remain isolated from shared stores",
                    "metric": f"isolation_rate={report['isolation_rate']}% ({len(report['isolated_units'])}/{report['unit_count']})",
                    "finding": (
                        "A measurable fraction of units never touch a store that is referenced by more than one unit, which means the repo's shared memory is not the default operating substrate for this population."
                    ),
                    "falsifier": "This finding would be falsified if the unshared population is actually consumed through repo-level side channels that the file-reference grep cannot observe, such as runtime-generated state or sibling repository files.",
                }
            )
            break

    total_dangling = sum(dangling_counts.values())
    if total_dangling:
        top = ", ".join(f"{store} ({count})" for store, count in dangling_counts.most_common(3))
        findings.append(
            {
                "title": "Dangling references point at absent artifacts",
                "metric": f"dangling_rate={sum(1 for info in unit_scan.values() if info['dangling']) / max(1, len(unit_scan)) * 100:.2f}% (top targets: {top})",
                "finding": "The repo contains references to files that do not exist in the checked-out tree, which weakens traceability and can silently break operational hand-offs.",
                "falsifier": "This would be falsified if the missing references resolve successfully in a sibling repository, alternate branch, or generated artifact directory outside the checked-out tree.",
            }
        )

    spine_coverage = []
    for population, report in population_metrics.items():
        if report["spine_attachment_rate"] > 0:
            spine_coverage.append(f"{population}={report['spine_attachment_rate']}%")
    if spine_coverage:
        findings.append(
            {
                "title": "Spine attachment is concentrated in governance and session anchors",
                "metric": f"spine_attachment={'; '.join(spine_coverage)}",
                "finding": "The repository repeatedly points at governance and session anchors, indicating that the canonical spine is serving as a coordination substrate even when the surrounding units are otherwise fragmented.",
                "falsifier": "This finding would be falsified if the referenced spine files are only incidental citations and not actually read or acted on by the units that mention them.",
            }
        )

    chain_units = sum(1 for info in unit_scan.values() if info["chained_hash"])
    if chain_units == 0:
        findings.append(
            {
                "title": "Hash chaining is effectively absent",
                "metric": f"chain_coverage={sum(1 for info in unit_scan.values() if info['uses_sha256'])}/{len(unit_scan)} units use SHA-256; {chain_units} chain to a previous hash",
                "finding": "The repo does not appear to maintain a consistent SHA-256 provenance chain across units, making audit trails harder to validate and replay.",
                "falsifier": "This would be falsified if the hash-chain logic is emitted outside the text patterns the census is scanning, for example through generated artifacts or non-text hash manifests.",
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "population_metrics": population_metrics,
        "shared_memory": [
            {"store": store, "count": len(store_to_units[store]), "tier": classify_store(store), "units": sorted(store_to_units[store])}
            for store, _ in sorted(shared_store_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "dangling_targets": [
            {"store": store, "count": count}
            for store, count in dangling_counts.most_common(10)
        ],
        "findings": findings,
    }


def main() -> int:
    root = repo_root()
    metrics = generate_metrics(root)

    output_path = root / "outputs" / "smc_copilot_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    findings_path = root / "docs" / "SMC_COPILOT_FINDINGS.md"
    findings_path.write_text(render_findings(metrics), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
