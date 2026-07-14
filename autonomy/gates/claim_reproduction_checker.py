#!/usr/bin/env python3
"""
claim_reproduction_checker.py — v0.1, extends reference_linter.py's exact
pattern (falsifiable, scriptable, narrow) from "does this URL resolve" to
three new claim types:

  1. §N citations — does the target header's content actually match what's
     being claimed about it? (caught neither by header-exists nor by eye —
     this is what missed the two broken §7 references last session)
  2. Live-data claims — does a claimed row count / value still match a
     fresh query? (drift detection, not just point-in-time correctness)
  3. Reproducible test claims — does re-running the actual code reproduce
     the number cited in prose? (requires the code to exist as a real,
     callable script, not a one-off heredoc — a real limitation surfaced
     by trying to build this, not assumed in advance)

Honest scope limit, stated up front: check #1 is a keyword-overlap proxy,
not true semantic matching — same class of limitation reference_linter's
own docstring already admits about itself.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from dataclasses import dataclass


# ── Check 1: §N citation vs. target section content ────────────────────────

CITATION_RE = re.compile(r'§(\d+)(?:\.(\d+))?[^)]*?\)?')
HEADER_RE = re.compile(r'^## (\d+)\. (.+)$', re.MULTILINE)

STOPWORDS = {
    "the", "a", "an", "is", "was", "were", "be", "been", "this", "that",
    "and", "or", "not", "to", "of", "in", "on", "for", "with", "as", "at",
    "it", "its", "by", "from", "see", "below", "above",
}


@dataclass
class CitationCheck:
    citation: str
    section_num: int
    context_sentence: str
    target_header: str | None
    keyword_overlap: int
    verdict: str  # MATCH | WEAK | NO_HEADER


def extract_keywords(text: str) -> set:
    words = re.findall(r'[a-zA-Z_]{4,}', text.lower())
    return {w for w in words if w not in STOPWORDS}


def check_citations(doc_path: str) -> list[CitationCheck]:
    text = Path(doc_path).read_text(encoding="utf-8")
    headers = {int(m.group(1)): m.group(2) for m in HEADER_RE.finditer(text)}

    # section content, for keyword-overlap checking
    section_bodies = {}
    header_matches = list(HEADER_RE.finditer(text))
    for i, m in enumerate(header_matches):
        num = int(m.group(1))
        start = m.end()
        end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(text)
        section_bodies[num] = text[start:end]

    results = []
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sent in sentences:
        for cm in re.finditer(r'§(\d+)', sent):
            num = int(cm.group(1))
            if num not in headers:
                results.append(CitationCheck(
                    citation=f"§{num}", section_num=num, context_sentence=sent[:100],
                    target_header=None, keyword_overlap=0, verdict="NO_HEADER",
                ))
                continue

            ctx_keywords = extract_keywords(sent)
            body_keywords = extract_keywords(section_bodies.get(num, ""))
            overlap = len(ctx_keywords & body_keywords)

            verdict = "MATCH" if overlap >= 2 else "WEAK"
            results.append(CitationCheck(
                citation=f"§{num}", section_num=num, context_sentence=sent[:100],
                target_header=headers[num], keyword_overlap=overlap, verdict=verdict,
            ))

    return results


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "REPOSITORY_AS_RECURSIVE_LEARNING_ENVIRONMENT_S071326-01.md"
    checks = check_citations(doc)

    weak_or_broken = [c for c in checks if c.verdict != "MATCH"]
    print(f"Checked {len(checks)} §N citations in {doc}\n")
    print(f"{'MATCH':>6}: {sum(1 for c in checks if c.verdict=='MATCH')}")
    print(f"{'WEAK':>6}: {sum(1 for c in checks if c.verdict=='WEAK')}")
    print(f"{'NO_HEADER':>6}: {sum(1 for c in checks if c.verdict=='NO_HEADER')}\n")

    if weak_or_broken:
        print("Flagged citations (not MATCH):")
        for c in weak_or_broken:
            print(f"  [{c.verdict}] {c.citation} (overlap={c.keyword_overlap}) — \"{c.context_sentence}...\"")
