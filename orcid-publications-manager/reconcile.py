#!/usr/bin/env python3
"""Read-only ORCID ↔ research registry reconciliation (Milestone B).

    python3 reconcile.py --fetch --research ../../research          # live ORCID
    python3 reconcile.py --works-json works.json --research <path>  # offline

Writes a report to --out (default data/reconcile/, gitignored):
    orcid_works.json   normalized ORCID manifest (no raw ORCID responses)
    report.json        matched / orcid_only / research_only / mismatches
    report.md          the same, for a human

Never writes to ORCID, to research, or to any registry. Every difference is
UNVERIFIED until a human resolves it; an ORCID entry never makes a draft
"published". Exit code is 0 unless --fail-on-diff is set and differences
exist (for a scheduled drift check that stays quiet when nothing changed).
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import orcid_works as ow  # noqa: E402


def title_key(title):
    """Case- and punctuation-insensitive key that keeps letters in any script."""
    return re.sub(r"[\W_]+", " ", (title or "").casefold()).strip()


def load_research(research_root):
    """Research publication registry entries, or [] with a note if absent."""
    if not research_root:
        return [], "no --research path given"
    reg = Path(research_root) / "registry" / "publications.json"
    if not reg.is_file():
        return [], f"{reg} not found (research registry not on this checkout)"
    pubs = json.loads(reg.read_text(encoding="utf-8")).get("publications") or []
    return pubs, None


def reconcile(records, pubs):
    by_doi, by_title = {}, {}
    for p in pubs:
        doi = ow.normalize_doi(p.get("doi"))
        if doi:
            by_doi.setdefault(doi, []).append(p)
        key = title_key(p.get("title"))
        if key:  # an empty key would match every other untitled work
            by_title.setdefault(key, []).append(p)

    matched, orcid_only, used = [], [], set()
    assigned = {}  # id(registry entry) -> first ORCID work_id matched to it
    for r in records:
        cands, how = [], None
        for doi in r["self_dois"]:
            for p in by_doi.get(doi, []):
                if all(p is not c for c in cands):
                    cands.append(p)
        if cands:
            how = "doi"
        elif title_key(r["title"]):
            cands, how = list(by_title.get(title_key(r["title"]), [])), "title"
        if not cands:
            orcid_only.append(dict(r, research_status="unknown",
                                   differences=["not in research registry"]))
            continue
        cands.sort(key=lambda p: str(p.get("release_tag")))
        pub = cands[0]
        used.update(id(p) for p in cands)
        diffs = []
        if len(cands) > 1:
            diffs.append("ambiguous: matches registry entries "
                         f"{[p.get('release_tag') for p in cands]}")
        if id(pub) in assigned:
            diffs.append(f"duplicate: registry entry {pub.get('release_tag')} matched by "
                         f"multiple ORCID groups (also {assigned[id(pub)]})")
        assigned.setdefault(id(pub), r["work_id"])
        pub_doi = ow.normalize_doi(pub.get("doi"))
        if pub_doi not in r["self_dois"] and (pub_doi or r["self_dois"]):
            diffs.append(f"doi: orcid={r['self_dois'] or None} research={pub_doi}")
        pref = r.get("preferred_dois") or []
        if pub_doi and pref and pub_doi in r["self_dois"] and pub_doi not in pref:
            diffs.append(f"doi: research={pub_doi} is another version in the ORCID group; "
                         f"preferred version has {pref}")
        if title_key(r["title"]) != title_key(pub.get("title")):
            diffs.append(f"title: orcid={r['title']!r} research={pub.get('title')!r}")
        if r["doi_candidates"]:
            diffs.append(f"orcid group carries several DOIs: {r['doi_candidates']}")
        matched.append(dict(r, matched_by=how, local_release_tag=pub.get("release_tag"),
                            research_status="candidate", differences=diffs))
    research_only = [{"release_tag": p.get("release_tag"), "title": p.get("title"),
                      "doi": ow.normalize_doi(p.get("doi")),
                      "differences": ["not on ORCID"]}
                     for p in pubs if id(p) not in used]
    mismatches = [m for m in matched if m["differences"]]
    return {"matched": matched, "orcid_only": orcid_only,
            "research_only": research_only, "mismatches": mismatches}


def md_cell(value):
    """One Markdown table cell: single line, no column breaks."""
    text = " ".join(str(value).split())
    return text.replace("\\", "\\\\").replace("|", "\\|")


def render_md(report):
    s = report["summary"]
    lines = ["# ORCID reconciliation report", "",
             f"- ORCID: `{report['researcher_orcid']}`, fetched "
             f"{report['fetched_at'] or 'unknown (offline file)'}",
             f"- ORCID response sha256: `{report['source_sha256']}`",
             f"- Research registry: {report['research_note'] or 'loaded'}",
             f"- Works on ORCID: {s['orcid_works']} · matched: {s['matched']} · "
             f"ORCID only: {s['orcid_only']} · research only: {s['research_only']} · "
             f"mismatches: {s['mismatches']}", "",
             "All rows are **UNVERIFIED**. ORCID entries are assertions, not proof of "
             "publication. Nothing was written anywhere.", ""]
    for name, rows in (("Mismatches", report["mismatches"]),
                       ("On ORCID, not in research", report["orcid_only"]),
                       ("In research, not on ORCID", report["research_only"])):
        lines += [f"## {name}", ""]
        if not rows:
            lines += ["None.", ""]
            continue
        lines += ["| Title | DOI | Date | Notes |", "|:--|:--|:--|:--|"]
        for r in rows:
            cells = (r.get("title") or "", r.get("doi") or "—", r.get("date") or "—",
                     "; ".join(r["differences"]))
            lines.append("| " + " | ".join(md_cell(c) for c in cells) + " |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--fetch", action="store_true", help="Fetch works from the ORCID public API")
    src.add_argument("--works-json", help="Saved /works JSON (offline)")
    ap.add_argument("--orcid", default=config.ORCID_ID)
    ap.add_argument("--research", help="Path to a humanaios-ui/research checkout")
    ap.add_argument("--out", default=str(Path(config.DATA_DIR) / "reconcile"))
    ap.add_argument("--fail-on-diff", action="store_true")
    args = ap.parse_args(argv)

    if args.fetch:
        from utils.orcid_client import OrcidClient
        raw = OrcidClient(args.orcid).get_works_raw()
        fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        raw = Path(args.works_json).read_bytes()
        fetched_at = None  # the file's fetch time is not known
    records = ow.normalize_works(json.loads(raw), args.orcid, fetched_at, raw)

    pubs, note = load_research(args.research)
    result = reconcile(records, pubs)
    report = {
        "schema": "orcid_reconcile_v1",
        "researcher_orcid": args.orcid,
        "fetched_at": fetched_at,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "research_note": note,
        "summary": {"orcid_works": len(records), **{k: len(v) for k, v in result.items()}},
        **result,
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in (("orcid_works.json", json.dumps(records, indent=2, sort_keys=True)),
                       ("report.json", json.dumps(report, indent=2, sort_keys=True)),
                       ("report.md", render_md(report))):
        (out / name).write_text(text + "\n", encoding="utf-8")

    n_diff = sum(len(result[k]) for k in ("orcid_only", "research_only", "mismatches"))
    print(f"{len(records)} ORCID works; {n_diff} difference(s); report in {out}")
    return 1 if (args.fail_on_diff and n_diff) else 0


if __name__ == "__main__":
    sys.exit(main())
