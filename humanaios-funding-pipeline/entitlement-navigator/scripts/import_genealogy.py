#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from entitlement.genealogy import import_gedcom_file, profile_patch_from_genealogy


def main() -> None:
    ap = argparse.ArgumentParser(description="Import a GEDCOM into the local private evidence boundary")
    ap.add_argument("gedcom")
    ap.add_argument("--focus", default=None, help="Unique focus-person name or GEDCOM ID")
    ap.add_argument("--private-name", default="family-tree.ged")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    src = Path(args.gedcom).expanduser().resolve()
    private_dir = root / "private" / "evidence" / "genealogy"
    derived_dir = root / "private" / "derived"
    manifest_dir = root / "private" / "manifests"
    for p in (private_dir, derived_dir, manifest_dir): p.mkdir(parents=True, exist_ok=True)

    result, graph = import_gedcom_file(src, args.focus)
    dest = private_dir / args.private_name
    shutil.copy2(src, dest)

    private_graph = {
        "import": result.to_dict(include_private_ids=True),
        "profile_patch": profile_patch_from_genealogy(result),
        "direct_ancestors": [
            {
                "person_id": pid,
                "generation": gen,
                "name": graph.people[pid].name,
                "birth_date": graph.people[pid].birth_date,
                "birth_place": graph.people[pid].birth_place,
                "death_date": graph.people[pid].death_date,
                "death_place": graph.people[pid].death_place,
            }
            for pid, gen in sorted(graph.direct_ancestors(result.focus_person_id).items(), key=lambda x: (x[1], x[0]))
        ] if result.focus_person_id else [],
    }
    (derived_dir / "genealogy-evidence-graph.private.json").write_text(json.dumps(private_graph, indent=2, ensure_ascii=False))

    public_manifest = result.to_dict(include_private_ids=False)
    private_clues = public_manifest.pop("clues", [])
    clue_counts = {}
    clue_generations = {}
    for c in private_clues:
        clue_counts[c["clue_type"]] = clue_counts.get(c["clue_type"], 0) + 1
        clue_generations.setdefault(c["clue_type"], set()).add(c["generation"])
    public_manifest["clue_counts"] = clue_counts
    public_manifest["clue_generations"] = {k: sorted(v) for k, v in clue_generations.items()}
    public_manifest["raw_file_committed"] = False
    public_manifest["private_storage_path"] = "private/evidence/genealogy/<redacted>"
    public_manifest["evidence_policy"] = "GEDCOM is a user-file evidence source. Clues do not establish enrollment, allotment, title, heirship, or entitlement until corroborated by the relevant authority."
    (manifest_dir / "genealogy-manifest.json").write_text(json.dumps(public_manifest, indent=2, ensure_ascii=False))
    print(json.dumps({"manifest": str(manifest_dir / 'genealogy-manifest.json'), "private_copy": str(dest), "sha256": result.sha256, "clues": len(result.clues)}, indent=2))


if __name__ == "__main__":
    main()
