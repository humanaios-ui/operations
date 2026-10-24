"""Normalize ORCID public-API works into a small, provenance-preserving manifest.

Pure functions, stdlib only, no network. Input is the JSON of
`GET https://pub.orcid.org/v3.0/<orcid>/works` (and optionally per-work
detail). Output follows the Milestone B metadata contract (research PR #6
review): one record per ORCID work *group*, with every put-code kept.

Authority: ORCID is asserted researcher metadata, not proof of publication.
Every record starts `doi_verified: false` and `research_status: "unknown"`.
Nothing here writes to ORCID, research, or any registry.
"""
import hashlib
import json
import re

DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)
DOI_SHAPE = re.compile(r"^10\.\d{4,9}/\S+$")

# ORCID work types -> BibTeX entry types. Anything else is @misc.
BIBTEX_TYPES = {
    "journal-article": "article",
    "conference-paper": "inproceedings",
    "book": "book",
    "book-chapter": "incollection",
    "dissertation-thesis": "phdthesis",
    "report": "techreport",
    "working-paper": "techreport",
    "preprint": "misc",
    "data-set": "misc",
    "software": "misc",
}


def dig(obj, *keys):
    """Nested get that survives ORCID's explicit nulls: dig(w, 'title', 'title', 'value')."""
    for key in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def normalize_doi(raw):
    """'https://doi.org/10.1/ABC' -> '10.1/abc'. Returns None when not DOI-shaped."""
    if not raw or not isinstance(raw, str):
        return None
    doi = DOI_PREFIX.sub("", raw.strip()).strip().lower()
    return doi if DOI_SHAPE.match(doi) else None


def self_dois(external_ids):
    """DOIs that identify the work itself (relationship 'self'), normalized, sorted."""
    found = set()
    for ext in dig(external_ids, "external-id") or []:
        if not isinstance(ext, dict) or ext.get("external-id-type") != "doi":
            continue
        if (ext.get("external-id-relationship") or "self") != "self":
            continue  # part-of / version-of DOIs point at something else
        doi = normalize_doi(dig(ext, "external-id-normalized", "value")
                            or ext.get("external-id-value"))
        if doi:
            found.add(doi)
    return sorted(found)


def work_date(summary):
    parts = [dig(summary, "publication-date", k, "value") for k in ("year", "month", "day")]
    out = []
    for p in parts:
        if not p:
            break
        out.append(str(p))
    return "-".join(out) or None


def preferred(summaries):
    """ORCID's preferred representation: highest display-index, then lowest put-code."""
    def key(s):
        try:
            idx = int(s.get("display-index") or 0)
        except (TypeError, ValueError):
            idx = 0
        return (-idx, int(s.get("put-code") or 0))
    return sorted(summaries, key=key)[0]


def normalize_works(works_json, researcher_orcid, fetched_at, source_bytes=None):
    """ORCID /works JSON -> list of contract records, deterministically sorted.

    `source_bytes` is the raw response body; its SHA-256 is recorded so a
    report can be traced to exactly what ORCID returned.
    """
    if source_bytes is None:
        source_bytes = json.dumps(works_json, sort_keys=True).encode()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    records = []
    for group in (works_json or {}).get("group") or []:
        summaries = [s for s in (dig(group, "work-summary") or []) if isinstance(s, dict)]
        if not summaries:
            continue
        pref = preferred(summaries)
        dois = set(self_dois(dig(group, "external-ids")))
        for s in summaries:
            dois.update(self_dois(dig(s, "external-ids")))
        put_codes = sorted(int(s["put-code"]) for s in summaries if s.get("put-code") is not None)
        title = (dig(pref, "title", "title", "value") or "").strip() or None
        records.append({
            "work_id": f"orcid:{researcher_orcid}:{put_codes[0] if put_codes else 'none'}",
            "researcher_orcid": researcher_orcid,
            "orcid_put_codes": put_codes,
            "title": title,
            "work_type": pref.get("type"),
            "date": work_date(pref),
            "doi": sorted(dois)[0] if dois else None,
            "doi_candidates": sorted(dois) if len(dois) > 1 else [],
            "doi_verified": False,
            "journal_title": dig(pref, "journal-title", "value"),
            "external_source": dig(pref, "source", "source-name", "value"),
            "external_url": dig(pref, "url", "value"),
            "fetched_at": fetched_at,
            "source_sha256": source_sha,
            "local_release_tag": None,
            "git_commit": None,
            "research_status": "unknown",
            "differences": [],
            "human_decision_ref": None,
        })
    records.sort(key=lambda r: (r["date"] or "", (r["title"] or "").lower(), r["work_id"]))
    return records


def bibtex_type(orcid_type):
    return BIBTEX_TYPES.get(orcid_type or "", "misc")


def contributor_names(work_detail):
    names = []
    for c in dig(work_detail, "contributors", "contributor") or []:
        name = dig(c, "credit-name", "value")
        if name:
            names.append(name.strip())
    return names
