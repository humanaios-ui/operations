"""Z1 advisory intersection search for human-submitted ideas and claims.

Offline, read-only, standard library. This does not attest source availability,
identity, claim truth, approval, or production implementation. Match rules are
hand-maintained topic hints over a dated public GitHub snapshot, not semantic truth.

No submitted text is emitted in the result. Never pass private text on a CLI
shared with untrusted process-list observers; use a local protected input file.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

SCHEMA = "humanaios.claim_intersection_e0.v0.1"
SNAPSHOT = "2026-10-30 public GitHub issue/PR inspection; mutable and not live-verified at replay"
KINDS = frozenset({"IDEA", "CLAIM", "OBSERVATION", "CHALLENGE"})
MAX_TEXT = 4000
MAX_HITS = 8

# This registry maps CURRENT, EXISTING work to suggested review junctions.
# Links are evidence *pointers*, not verified claim or runtime outcomes.
INTERSECTIONS = (
    {
        "id": "typed-intent", "title": "Human wording to typed resource intent",
        "terms": ("natural language", "typed intent", "verified resource", "intent-os", "resource discovery"),
        "issues": (1063,), "prs": (1064,),
        "review_question": "Does the proposed interpretation preserve the human's intent and reject unproved resource status?",
    },
    {
        "id": "source-correction", "title": "Broken source to independently reviewed correction",
        "terms": ("404", "broken link", "source review", "job listing", "grant verified", "source correction"),
        "issues": (992, 1002), "prs": (),
        "review_question": "Was the source independently checked, without turning link failure into a claim of closure?",
    },
    {
        "id": "runtime-calibration", "title": "Runtime claim to P1/P2/P3 test",
        "terms": ("acat-r", "runtime calibration", "runtime behavior", "currentness", "p1 p2 p3"),
        "issues": (1068,), "prs": (1069, 1071),
        "review_question": "Is the observed runtime independently captured, or only an offline/synthetic fixture?",
    },
    {
        "id": "external-capability", "title": "External capability claim to source replay",
        "terms": ("dase", "third-party capability", "capability proof", "external runtime"),
        "issues": (1067,), "prs": (),
        "review_question": "Are authorized source files and raw results available for independent reproduction?",
    },
    {
        "id": "preparation", "title": "Human task to version-bound readiness",
        "terms": ("odin", "preparation checks", "file versions", "recording readiness", "task accepted"),
        "issues": (1049,), "prs": (1050,),
        "review_question": "Are checks bound to exact file versions, without implying task acceptance or completion?",
    },
    {
        "id": "review-support", "title": "Review-tool idea to bounded Resource Miner test",
        "terms": ("coderabbit", "discount adapter", "coupon search", "code review replacement"),
        "issues": (1055,), "prs": (1056, 1054),
        "review_question": "Does the proposed change reuse existing tools and keep independent review separate from admission?",
    },
    {
        "id": "human-admission", "title": "Human idea to issue, PR, audit and human gate",
        "terms": ("human review", "admission", "ready for review", "project desk", "issue first", "human submits"),
        "issues": (598, 1043, 1057), "prs": (1058,),
        "review_question": "Are implementation completion, independent audit and human approval separately recorded?",
    },
    {
        "id": "oracle-challenge", "title": "Evidence claim to independent Oracle challenge",
        "terms": ("source oracle", "oracle review", "oracle challenge", "independent challenge", "knowledge graph", "p1 retention", "graph telemetry", "p1 p2 p3 record", "original incorrect answer"),
        "issues": (1065,), "prs": (1066,),
        "review_question": "Is the P1 commitment independent and earlier than P2, rather than retrospective?",
    },
    {
        "id": "workspace-ux", "title": "Resource tracking and source feedback in the existing workspace",
        "terms": ("track this resource", "find resources", "work queue", "stay on find resources",
                  "source card", "my opportunities", "record an outcome", "notify the user"),
        "issues": (1002,), "prs": (),
        "review_question": "Does the resource tracking action preserve the user's current page and surface a non-authoritative notification?",
    },
    {
        "id": "resource-portfolio", "title": "Owned machine and migration resources",
        "terms": ("macbook pro", "windows desktop", "desktop windows", "owned hardware",
                  "hardware migration", "machine migration", "device inventory", "local work on my", "machine substrate"),
        "issues": (1052, 1051), "prs": (),
        "review_question": "Are the machines actually owned/available and are their capabilities evidenced independently?",
    },
    {
        "id": "prior-art", "title": "External idea to scoped prior-art and attribution review",
        "terms": ("prior art", "prior art engine", "novel", "earlier work", "name ledger", "term ledger"),
        "issues": (1043, 1002, 1065), "prs": (),
        "review_question": "What was searched, what remains unsearched, and who contributed the earlier idea?",
    },
)


def _public_source_ref(raw: object) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not 1 <= len(raw) <= 1600:
        raise ValueError("source_ref must be a bounded public HTTPS URL")
    try:
        parts = urlsplit(raw)
        host = (parts.hostname or "").lower().rstrip(".")
        valid = (parts.scheme == "https" and not parts.username and
                 not parts.password and parts.port in (None, 443))
    except ValueError as exc:
        raise ValueError("invalid source_ref URL") from exc
    if not valid:
        raise ValueError("source_ref must be public HTTPS")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass  # A domain name, to be checked against the tight allowlist below.
    else:
        raise ValueError("IP source references are not supported")
    if host not in {"github.com", "www.linkedin.com", "linkedin.com"}:
        raise ValueError("source_ref host is outside this pilot's public allowlist")
    if any(c.isspace() for c in parts.path) or chr(92) in parts.path:
        raise ValueError("invalid source_ref path")
    if host == "github.com":
        if not re.fullmatch(r"/humanaios-ui/[A-Za-z0-9._-]+/(?:issues|pull)/[1-9][0-9]*", parts.path):
            raise ValueError("only public HumanAIOS issue/PR source references are allowed")
    elif not parts.path.startswith("/posts/"):
        raise ValueError("only public LinkedIn post references are allowed")
    # Tracking query strings and fragments are intentionally never exported.
    return urlunsplit(("https", host, parts.path, "", ""))


def _normalize(raw: str) -> str:
    """Collapse arbitrary separators, including arrows, into word boundaries."""
    plain = unicodedata.normalize("NFKC", raw).casefold()
    plain = plain.replace("\u2019", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", plain, flags=re.UNICODE)).strip()


def _hit(text: str, signal: str) -> bool:
    pattern = _normalize(signal)
    return bool(pattern and re.search(r"(?<!\w)" + re.escape(pattern) + r"(?!\w)", text))


def _read_opt_in_context(raw: object, original_source: str | None) -> tuple[str, str] | None:
    """Use one explicitly opted-in, bounded *human-supplied* description.

    Never fetch a URL, inspect the attachment, or treat the descriptor as verified.
    Source references are checked for equivalence to the claim's existing source.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != {"opt_in", "kind", "text", "source_ref"}:
        raise ValueError("context must have exactly opt_in, kind, text, source_ref")
    if raw["opt_in"] is not True:
        raise ValueError("context requires explicit opt-in")
    if raw["kind"] not in {"IMAGE_DESCRIPTION", "PUBLIC_POST_EXCERPT", "DOCUMENT_EXCERPT", "HUMAN_SUMMARY"}:
        raise ValueError("unsupported context kind")
    if not isinstance(raw["text"], str) or not 1 <= len(raw["text"].strip()) <= 800:
        raise ValueError("context text outside the bounded 1..800 character range")
    canonical = _public_source_ref(raw["source_ref"])
    if canonical != original_source:
        raise ValueError("context source_ref must match the submission source_ref")
    return raw["kind"], raw["text"]


def project(payload: dict) -> dict:
    """Offer candidate intersections; human must verify every proposed equivalence."""
    if not isinstance(payload, dict) or set(payload) not in (
        {"schema", "claim_text", "kind", "source_ref"},
        {"schema", "claim_text", "kind", "source_ref", "context"},
    ):
        raise ValueError("expect exact v0.1 fields, optionally context")
    if payload["schema"] != SCHEMA or not isinstance(payload["kind"], str) or payload["kind"] not in KINDS:
        raise ValueError("unknown schema or kind")
    claim = payload["claim_text"]
    if not isinstance(claim, str) or not 1 <= len(claim.strip()) <= MAX_TEXT:
        raise ValueError("claim_text must contain 1..4000 characters")
    source_ref = _public_source_ref(payload["source_ref"])
    context = _read_opt_in_context(payload.get("context"), source_ref)
    normalized = _normalize(claim)
    context_words = _normalize(context[1]) if context else ""
    scored = []
    for entry in INTERSECTIONS:
        primary_hits = tuple(t for t in entry["terms"] if _hit(normalized, t))
        context_hits = tuple(t for t in entry["terms"] if context_words and _hit(context_words, t))
        if primary_hits or context_hits:
            refs = [f"https://github.com/humanaios-ui/operations/issues/{n}" for n in entry["issues"]]
            refs.extend(f"https://github.com/humanaios-ui/operations/pull/{n}" for n in entry["prs"])
            # Direct human wording wins tie with indirect contextual description.
            score = (len(primary_hits) + len(context_hits), bool(primary_hits))
            scored.append((score, {
                "intersection_id": entry["id"], "title": entry["title"],
                "match_basis": "UNVERIFIED_HUMAN_TEXT_HINT" if primary_hits else "UNVERIFIED_OPT_IN_CONTEXT_HINT",
                "matched_terms": list(dict.fromkeys((*primary_hits, *context_hits))),
                "existing_work_refs": refs, "review_question": entry["review_question"],
                "review_state": "UNVERIFIED", "status_of_linked_work": "NOT_RECHECKED",
            }))
    scored.sort(key=lambda item: (-item[0][0], -int(item[0][1]), item[1]["intersection_id"]))
    matches = [item[1] for item in scored[:MAX_HITS]]
    return {
        "schema": SCHEMA, "snapshot": SNAPSHOT, "kind": payload["kind"],
        "claim_sha256": hashlib.sha256(claim.encode("utf-8")).hexdigest(),
        "claim_text_in_output": False, "source_ref": source_ref,
        "context_consumed": bool(context), "context_kind": context[0] if context else None,
        "context_evidence_state": "HUMAN_SUPPLIED_UNVERIFIED" if context else "NOT_SUPPLIED",
        "context_content_in_output": False,
        "origin_authentication": "NOT_PERFORMED",
        "candidate_intersections": matches,
        "needs_human_mapping": not bool(matches),
        "next_step": "HUMAN_INTERPRETATION_AND_EXISTING_WORK_REVIEW",
        "prior_art_status": "NOT_SEARCHED", "claim_truth": "NOT_ESTABLISHED",
        "authority_effect": "NONE", "execution": "DISABLED", "can_authorize": False,
        "merge_authority": False, "human_approval": "NOT_INFERRED",
        "notes": "Lexical hints and optional human-supplied descriptions are not evidence authentication or novelty claims.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Offline advisory mapping: human claim to existing HumanAIOS work")
    p.add_argument("--input", type=Path, required=True, help="Local UTF-8 JSON intake; keep private")
    args = p.parse_args()
    if args.input.stat().st_size > 8192:
        p.error("input file too large")
    print(json.dumps(project(json.loads(args.input.read_text(encoding="utf-8"))), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
