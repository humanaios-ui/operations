"""Deterministic query-quality controls for public Resource Miner candidates.

This is a bounded lexical/taxonomy fusion stage, NOT web search, vector search,
a semantic LLM, eligibility determination, or authority. All text is untrusted.
No I/O, persistence, external calls, or user profiling.
"""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = frozenset({
    "a", "about", "an", "and", "are", "can", "could", "find", "for", "from",
    "help", "humanaios", "i", "in", "me", "my", "need", "of", "on", "our",
    "please", "resource", "resources", "some", "that", "the", "to", "us",
    "want", "we", "with", "would",
    "busco", "buscar", "para", "por", "que", "una", "uno", "unos", "unas",
    "las", "los", "del", "con", "necesito", "encontrar", "ayuda",
})
ALIASES = {
    "grants": "grant", "fund": "funding", "funds": "funding",
    "money": "funding", "capital": "funding", "financing": "funding",
    "jobs": "work", "job": "work", "employment": "work", "paid": "work",
    "certificates": "training", "certificate": "training",
    "certifications": "training", "certification": "training",
    "courses": "training", "course": "training",
    "cloud": "compute", "credits": "credit", "gpus": "gpu",
    "competitions": "challenge", "contest": "challenge",
    "contests": "challenge", "hackathons": "hackathon",
    "researchers": "research", "evaluations": "evaluation",
    "partnerships": "partner",
    # Explicit, bounded vocabulary: this is NOT general-purpose translation.
    "subvencion": "grant", "subvenciones": "grant",
    "beca": "scholarship", "becas": "scholarship",
    "credito": "credit", "creditos": "credit",
    "computacion": "compute", "computo": "compute",
    "investigacion": "research", "investigaciones": "research",
    "formacion": "training", "capacitacion": "training",
    "trabajo": "work", "trabajos": "work",
    "financiacion": "funding", "financiamiento": "funding",
    "premios": "prize", "premio": "prize",
}
_IDENTIFIER_RE = re.compile(r"(?<!\w)[a-z][a-z0-9]*[-_][a-z0-9_-]*\d[a-z0-9_-]*(?!\w)")
_FINANCING_NEGATION = re.compile(
    r"(?<!\w)(?:no|without|avoid|excluding|do\s+not\s+want|don['’]?t\s+want)\s+(?:a\s+)?(?:loans?|debt|borrowing)(?!\w)"
)


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


def query_terms(text: str) -> set[str]:
    """Stable Unicode-aware bounded term normalization; no query rewriting."""
    if not isinstance(text, str):
        return set()
    folded = _fold(text)
    words = {
        ALIASES.get(word, word)
        for word in re.findall(r"[^\W_]{3,}", folded, re.UNICODE)
        if word not in STOPWORDS
    }
    # Preserve short structured IDs (AB-12, H-1B) in both query and evidence.
    return words | set(_IDENTIFIER_RE.findall(folded))


def exact_anchors(objective: str) -> frozenset[str]:
    """Preserve structured identifiers instead of turning them into loose tokens."""
    return frozenset(_IDENTIFIER_RE.findall(_fold(objective)))


def has_exact_anchors(objective: str, text: str) -> bool:
    anchors = exact_anchors(objective)
    if not anchors:
        return True
    haystack = _fold(text)
    return all(
        re.search(r"(?<![\w-])" + re.escape(anchor) + r"(?![\w-])", haystack)
        for anchor in anchors
    )


def blocked_resource_types(objective: str) -> frozenset[str]:
    """Only act on explicit English loan/debt exclusions; no inferred preferences."""
    if _FINANCING_NEGATION.search(_fold(objective)):
        return frozenset({"financing", "loan", "debt"})
    return frozenset()


def fuse_rankings(matches: list[dict]) -> list[dict]:
    """RRF for independently observed lexical and declared-taxonomy matches.

    Candidate matching is upstream. No fabricated semantic/vector hits are added.
    The lexical lane retains the existing title/description score. The taxonomy
    lane uses declared tags/types/affordances/need labels only. Both are auditable.
    """
    lex = sorted(
        range(len(matches)),
        key=lambda i: (-matches[i]["relevance_score"], matches[i]["title"].casefold(),
                       matches[i]["resource_id"]),
    )
    taxonomy = sorted(
        (i for i, row in enumerate(matches) if row.get("_taxonomy_hit_count", 0) > 0),
        key=lambda i: (-matches[i]["_taxonomy_hit_count"], matches[i]["title"].casefold(),
                       matches[i]["resource_id"]),
    )
    lex_ranks = {idx: rank for rank, idx in enumerate(lex, 1)}
    taxonomy_ranks = {idx: rank for rank, idx in enumerate(taxonomy, 1)}
    output = []
    for i, row in enumerate(matches):
        item = dict(row)
        item.pop("_taxonomy_hit_count", None)
        # Keep the meaning of relevance_score intact for compatibility.
        item["ranking_signals"] = {
            "lexical_rank": lex_ranks[i],
            "taxonomy_rank": taxonomy_ranks.get(i),
            "fusion": "RRF_K60_LEXICAL_TAXONOMY",
        }
        fused = 1.0 / (60 + lex_ranks[i])
        if i in taxonomy_ranks:
            fused += 1.0 / (60 + taxonomy_ranks[i])
        output.append((fused, item))
    output.sort(key=lambda pair: (-pair[0], -pair[1]["relevance_score"],
                                   pair[1]["title"].casefold(), pair[1]["resource_id"]))
    return [item for _score, item in output]
