"""Source-backed capability tokens -> existing Resource Miner discovery (read-only pilot).

Authority effect: NONE. Reuses needs.map_to_needs scoring, ResourceCandidate,
PER capability tags and intent_os.evaluate_objective. Adds no matcher, store or tracker.

A token is one source-backed fact from the owner's master. Normalization groups
tokens under shared concepts through typed edges; it never merges or rewrites facts.
Discovery receives only minimal predicates (concept id + signal phrases), never
token text, names, employers or dates. A match is a lead, not an eligibility claim.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable

from .models import ResourceCandidate
from .needs import _score, map_to_needs

SCHEMA = "humanaios.token-attractor.v0.1"
TOKEN_TYPES = ("CAPABILITY", "EXPERIENCE", "METHOD", "OUTCOME", "RESOURCE", "CONSTRAINT")
EDGE_TYPES = ("SUPPORTS", "REQUIRES", "TRANSFERABLE_HYPOTHESIS", "CONTRADICTS", "DERIVED_FROM")
ANY_HIT = 0.11          # one existing-scoring signal hit (sensitivity view)
EXISTING_THRESHOLD = 0.2  # map_to_needs' own cutoff (primary view, unchanged)

# classify: word-boundary regexes over a token's own text. discover: phrases matched
# by the existing substring scorer inside resource text (>= 4 chars or multiword).
CONCEPTS: dict[str, dict[str, Any]] = {
    "ANALYTICAL_METHOD_VALIDATION": {
        "label": "Analytical method validation",
        "classify": [r"method validation", r"analytical validation", r"assay validation",
                     r"\bhplc\b", r"mass spectrometry", r"\blc/ms\b", r"\bmaldi", r"immunoassay",
                     r"proficiency testing", r"analytical chemistry", r"validation pipeline",
                     r"quality validation", r"statistical validation"],
        "discover": ["validation", "method validation", "analytical", "assay", "measurement",
                     "reproducib", "replication"],
    },
    "HEALTHCARE_QUALITY_SYSTEMS": {
        "label": "Healthcare quality systems",
        "classify": [r"quality assurance", r"quality director", r"patient safety", r"clinical risk",
                     r"regulatory audit", r"\bclia\b", r"document control",
                     r"incident[- ]report", r"quality (?:program|system)", r"healthcare|hospital"],
        "discover": ["healthcare", "patient safety", "clinical quality", "hospital", "medical",
                     "quality assurance", "health system"],
    },
    "PROJECT_DELIVERY": {
        "label": "Project delivery",
        "classify": [r"project delivery", r"project management", r"program (?:management|coordination)",
                     r"operations management", r"process improvement", r"dmaic", r"root cause",
                     r"milestone", r"work ?plan", r"staff leadership"],
        "discover": ["project management", "program management", "operations", "process improvement",
                     "delivery", "coordination"],
    },
    "AI_EVALUATION": {
        "label": "AI evaluation",
        "classify": [r"ai evaluation", r"behavioral rubric", r"calibration protocol",
                     r"false[- ]positive", r"inter-rater", r"drift[- ]signal", r"evaluation methodology",
                     r"\bacat\b"],
        "discover": ["evaluation", "benchmark", "calibration", "red team", "rubric",
                     "safety research", "model testing", "interpretability"],
    },
    "LABORATORY_OPERATIONS": {
        "label": "Laboratory operations",
        "classify": [r"\blaborator(?:y|ies)\b", r"\blab\b(?![- ]grown)", r"biochemical genetics", r"proteomics", r"\bsops?\b",
                     r"\blis\b", r"specimen"],
        "discover": ["laboratory", "wet lab", "lab operations", "biochemical", "instrument"],
    },
    "DATA_VALIDATION": {
        "label": "Data validation",
        "classify": [r"data pipeline", r"data normalization", r"corrections?[- ]ledger",
                     r"sample-size"],
        "discover": ["data quality", "dataset", "data validation", "annotation"],
    },
}

# Authored, explicit, hypothesis-only transfer edges. Anything not listed is refused.
TRANSFER_TABLE: dict[tuple[str, str], str] = {
    ("ANALYTICAL_METHOD_VALIDATION", "AI_EVALUATION"):
        "Validation, calibration and reproducibility practice may carry to AI evaluation methodology.",
    ("HEALTHCARE_QUALITY_SYSTEMS", "AI_EVALUATION"):
        "Audit, incident review and document control may carry to AI evaluation governance.",
    ("LABORATORY_OPERATIONS", "PROJECT_DELIVERY"):
        "Running controlled lab workflows may carry to project and program delivery.",
    ("ANALYTICAL_METHOD_VALIDATION", "DATA_VALIDATION"):
        "Analytical validation may carry to data validation.",
}

CREDENTIAL_PATTERNS = (r"\bphd\b", r"\bdoctoral\b", r"\blicensed\b", r"\bmd\b", r"citizen",
                       r"\bstudent", r"\bundergraduate", r"\bgraduate\b", r"\bresident of\b",
                       r"\bnonprofit\b|\b501\(c\)", r"\bmba\b", r"\bbachelor", r"\bmaster'?s\b",
                       r"ph\.d", r"\bm\.d\b", r"clearance", r"women-led|woman-owned|minority-owned")
# P3 (R5): domain/status requirements the P1 detector missed. Used only in strict mode so
# P1 stays reproducible.
DOMAIN_REQUIREMENT_PATTERNS = (r"\bbackground\b", r"\bdegree\b", r"\bcertif", r"\bexpert",
                               r"\bsenior\b", r"years of experience", r"work authori[sz]ation",
                               r"\busa-remote\b|\bu\.?s\.?-based\b", r"\bcontractor\b",
                               r"\bfounder", r"\bstartup")
MIN_TEXT_CHARS = 80  # P3 (R4): thinner descriptions cannot support a capability claim

CONTROL_CONCEPTS: dict[str, dict[str, Any]] = {
    "CTRL_LICENSED_CLINICAL_PRACTICE": {
        "label": "Licensed clinical practice (unsupported)",
        "discover": ["clinical trial", "patient care", "licensed", "fda", "physician"],
    },
    "CTRL_QUANTUM_HARDWARE": {
        "label": "Quantum hardware engineering (unsupported)",
        "discover": ["quantum", "qubit", "cryogenic", "photonic"],
    },
    "CTRL_NONSENSE": {"label": "Random words", "discover": ["zebra", "plinth", "gossamer", "tundra"]},
}


def _sha(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def _clean(text: Any) -> str:
    return " ".join(str(text or "").split())


def token_id(source_path: str, label: str, ttype: str = "", revision: str = "") -> str:
    return "TK-" + _sha(source_path, label, ttype, revision)[:12]


def make_token(ttype: str, label: str, source_path: str, source_revision: str,
               evidence_ref: str, approval_status: str, meaning: str = "",
               classify_text: str = "") -> dict[str, Any]:
    if ttype not in TOKEN_TYPES:
        raise ValueError("unknown token type")
    label = _clean(label)
    if not label or not source_path or not source_revision or not evidence_ref:
        raise ValueError("a token needs a label, source path, revision and evidence reference")
    return {"token_id": token_id(source_path, label, ttype, source_revision), "type": ttype, "label": label,
            "classify_text": _clean(classify_text),
            "meaning": _clean(meaning) or label, "source_path": source_path,
            "source_revision": source_revision, "evidence_ref": evidence_ref,
            "approval_status": approval_status}


def build_tokens(master: dict[str, Any], revision: str,
                 per_records: Iterable[dict[str, Any]] = ()) -> list[dict[str, Any]]:
    """Typed candidate tokens from a master profile (+ public PER constraints)."""
    out: list[dict[str, Any]] = []
    own = f"master@{revision[:12]}"
    committed = "OWNER_COMMITTED_MASTER"

    def add(*args, **kw):
        out.append(make_token(*args, **kw))

    comp = master.get("competencies") or {}
    for group in ("data_quality", "ai_research", "operations"):
        for i, x in enumerate(comp.get(group) or []):
            add("CAPABILITY", x, f"competencies.{group}[{i}]", revision, own, committed)
    tech = comp.get("technical_skills") or {}
    for group, ttype in (("data_analytics", "METHOD"), ("quality_compliance", "METHOD"),
                         ("ai_infrastructure", "METHOD"), ("infrastructure", "RESOURCE")):
        for i, x in enumerate(tech.get(group) or []):
            add(ttype, x, f"competencies.technical_skills.{group}[{i}]", revision, own, committed)
    for i, row in enumerate(master.get("experience") or []):
        label = " | ".join(_clean(row.get(k)) for k in ("role", "organization")) + \
            " | " + _clean(row.get("duration_display") or
                           f"{row.get('start_date', '')} - {row.get('end_date', 'Present')}")
        add("EXPERIENCE", label, f"experience[{i}]", revision, own, committed, _clean(row.get("summary")),
            classify_text=f"{_clean(row.get('role'))} {_clean(row.get('summary'))}")
        for j, b in enumerate(row.get("bullets") or []):
            add("OUTCOME", b, f"experience[{i}].bullets[{j}]", revision, own, committed)
    for i, cat in enumerate(master.get("achievements") or []):
        for j, item in enumerate(cat.get("items") or []):
            add("OUTCOME", item.get("title"), f"achievements[{i}].items[{j}]", revision, own,
                committed, _clean(item.get("description")))
    for i, row in enumerate(master.get("project_evidence") or []):
        status = row.get("review_status") or "UNREVIEWED"
        ref = _clean(row.get("evidence_ref")) or own
        add("EXPERIENCE", row.get("title"), f"project_evidence[{i}]", revision, ref, status,
            _clean(row.get("mandate")),
            classify_text=f"{_clean(row.get('title')).split(' | ')[0]} {_clean(row.get('mandate'))}")
        for j, b in enumerate(row.get("evidence_bullets") or []):
            add("OUTCOME", b, f"project_evidence[{i}].evidence_bullets[{j}]", revision, ref, status)
    for i, row in enumerate(master.get("publications") or []):
        add("OUTCOME", row.get("title"), f"publications[{i}]", revision, own, committed,
            _clean(row.get("status") or row.get("type")))
    for i, row in enumerate(master.get("education") or []):
        add("EXPERIENCE", f"{_clean(row.get('degree'))} | {_clean(row.get('school'))}",
            f"education[{i}]", revision, own, committed, _clean(row.get("status")),
            classify_text=_clean(row.get("degree")))
    for p in per_records:
        pid = p.get("project_id")
        for i, c in enumerate(p.get("constraints") or []):
            add("CONSTRAINT", c, f"per:{pid}.constraints[{i}]", "seed", f"PER:{pid}", "SEED_RECORD")
    return out


def classify(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """SUPPORTS edges token -> concept. A token may support several concepts; facts stay separate."""
    edges = []
    for t in tokens:
        if t["type"] == "CONSTRAINT":
            continue  # a limit on the work is not evidence of a capability
        text = (t.get("classify_text") or (t["label"] + " " + t["meaning"])).casefold()
        for cid, spec in CONCEPTS.items():
            hits = [p for p in spec["classify"] if re.search(p, text)]
            if hits:
                edges.append(make_edge("SUPPORTS", t["token_id"], cid, "SOURCE_BACKED",
                                       f"matched: {', '.join(hits[:3])}"))
    return edges


def make_edge(etype: str, src: str, dst: str, state: str, basis: str) -> dict[str, Any]:
    if etype not in EDGE_TYPES:
        raise ValueError("unknown edge type")
    return {"edge_id": "ED-" + _sha(etype, src, dst)[:12], "type": etype, "from": src, "to": dst,
            "state": state, "basis": basis}


def structural_edges(tokens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """DERIVED_FROM (bullet -> parent entry) and REQUIRES (outcome -> method it names)."""
    by_path = {t["source_path"]: t for t in tokens}
    edges = []
    for t in tokens:
        m = re.match(r"^(experience\[\d+\]|project_evidence\[\d+\])\.(?:bullets|evidence_bullets)\[\d+\]$",
                     t["source_path"])
        if m and m.group(1) in by_path:
            edges.append(make_edge("DERIVED_FROM", t["token_id"], by_path[m.group(1)]["token_id"],
                                   "SOURCE_BACKED", "bullet belongs to this entry"))
    methods = [t for t in tokens if t["type"] == "METHOD" and len(t["label"]) >= 3]
    for o in (t for t in tokens if t["type"] == "OUTCOME"):
        for m in methods:
            if re.search(r"\b" + re.escape(m["label"].casefold().split(" (")[0]) + r"\b", o["label"].casefold()):
                edges.append(make_edge("REQUIRES", o["token_id"], m["token_id"], "SOURCE_BACKED",
                                       "outcome text names this method"))
    return edges


def transfer_edges() -> list[dict[str, Any]]:
    return [make_edge("TRANSFERABLE_HYPOTHESIS", a, b, "HYPOTHESIS", why)
            for (a, b), why in sorted(TRANSFER_TABLE.items())]


def propose_transfer(src: str, dst: str) -> dict[str, Any]:
    """Only pre-authored transfers exist. Any other cross-domain jump is refused."""
    if (src, dst) not in TRANSFER_TABLE:
        raise ValueError("transfer not authorized: no source-backed rationale")
    return make_edge("TRANSFERABLE_HYPOTHESIS", src, dst, "HYPOTHESIS", TRANSFER_TABLE[(src, dst)])


def contradiction_edge(claim_token: str, observed_token: str, basis: str) -> dict[str, Any]:
    """Never asserts a settled contradiction: differing sources need reconciliation first."""
    return make_edge("CONTRADICTS", claim_token, observed_token, "RECONCILIATION_REQUIRED", basis)


def backed_concepts(tokens: list[dict[str, Any]], supports: list[dict[str, Any]]) -> dict[str, list[str]]:
    ids = {t["token_id"] for t in tokens}
    out: dict[str, list[str]] = {}
    for e in supports:
        if e["type"] == "SUPPORTS" and e["from"] in ids:
            out.setdefault(e["to"], []).append(e["from"])
    return out


# ---- predicates handed to the existing matcher: no personal text crosses this line ----

def _norm_phrase(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9/ ]+", " ", s.casefold()).split())


def literal_signals(tokens: list[dict[str, Any]], members: list[str]) -> list[str]:
    """Baseline (no expansion): the owner's own short phrases, verbatim."""
    by_id = {t["token_id"]: t for t in tokens}
    sigs = []
    for m in members:
        t = by_id[m]
        if _is_skill_phrase(t):
            sigs.append(_norm_phrase(t["label"]))
    return sorted(set(s for s in sigs if s))


STOPWORDS = frozenset("and the for with from into over under data design systems system "
                      "management analysis using use used based such this that".split())


def _is_skill_phrase(t: dict[str, Any]) -> bool:
    """Only the master's own competency phrases may be sent as literal text: short, no digits."""
    return (t["type"] in ("CAPABILITY", "METHOD") and t["source_path"].startswith("competencies.")
            and 4 <= len(t["label"]) <= 60 and len(t["label"].split()) <= 5
            and not re.search(r"\d", t["label"]))


def bag_signals(tokens: list[dict[str, Any]], members: list[str]) -> list[str]:
    """Fair baseline A2: unigrams and adjacent-word bigrams of the same skill phrases."""
    by_id = {t["token_id"]: t for t in tokens}
    out: set[str] = set()
    for m in members:
        t = by_id[m]
        if not _is_skill_phrase(t):
            continue
        words = [w for w in _norm_phrase(t["label"]).split() if len(w) >= 4 and w not in STOPWORDS]
        out.update(words)
        out.update(" ".join(pair) for pair in zip(words, words[1:]))
    return sorted(out)


def private_terms_from_master(master: dict[str, Any]) -> set[str]:
    """Words that identify the owner or an employer/school; they must never reach the matcher."""
    terms: set[str] = set()
    def add(v):
        for w in re.findall(r"[a-z0-9@.]{4,}", str(v or "").casefold()):
            terms.add(w)
    c = master.get("contact") or {}
    for k in ("legal_name", "location", "email", "phone"):
        add(c.get(k))
    for row in (master.get("experience") or []) + (master.get("leadership") or []):
        add(row.get("organization"))
    for row in master.get("education") or []:
        add(row.get("school"))
    for row in master.get("project_evidence") or []:
        parts = str(row.get("title") or "").split(" | ")
        if len(parts) > 1:
            add(parts[1])
    return terms - {"hospital", "center", "medical", "university", "institute", "health"}


def check_predicates_clean(predicates: dict[str, dict[str, Any]], private_terms: set[str]) -> None:
    for key, need in predicates.items():
        blob = " ".join([need["label"], *need["signals"], *need.get("own_signals", [])]).casefold()
        if any(re.search(r"(?<![a-z0-9])" + re.escape(t), blob) for t in private_terms):
            raise ValueError(f"predicate {key} contains owner/employer text")


def expanded_signals(concept: str, *, with_hypothesis: bool) -> list[str]:
    sigs = list(CONCEPTS[concept]["discover"])
    if with_hypothesis:
        for (a, b) in TRANSFER_TABLE:
            if a == concept:
                sigs += CONCEPTS[b]["discover"]
    return sorted(set(s.casefold() for s in sigs if len(s) >= 4))


def predicate_need(concept: str, signals: list[str], arm: str,
                   own: list[str] | None = None) -> dict[str, Any]:
    """The only object the existing matcher sees. Opaque id, concept label, signal phrases."""
    label = (CONCEPTS.get(concept) or CONTROL_CONCEPTS[concept])["label"]
    return {"need_id": f"{concept}|{arm}", "label": label, "resource_types": [],
            "affordances": [], "signals": signals,
            "own_signals": signals if own is None else own}


def load_corpus(path: str | Path) -> list[ResourceCandidate]:
    fields = {f.name for f in dataclasses.fields(ResourceCandidate)} - {"evidence", "need_matches",
                                                                       "requirement_matches"}
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out.append(ResourceCandidate(**{k: v for k, v in row.items() if k in fields}))
    return out


def credential_flags(resource: ResourceCandidate) -> list[str]:
    text = " ".join([resource.title, resource.description, " ".join(resource.applicant_types)]).casefold()
    return [p for p in CREDENTIAL_PATTERNS if re.search(p, text)]


def discover(predicates: dict[str, dict[str, Any]], corpus: list[ResourceCandidate],
             threshold: float = EXISTING_THRESHOLD) -> dict[str, list[dict[str, Any]]]:
    """Run the existing scorer. Returns need_id -> hits. Eligibility is never assessed."""
    hits: dict[str, list[dict[str, Any]]] = {k: [] for k in predicates}
    for r in corpus:
        for key, need in predicates.items():
            score, _, _, sig = _score(r, need)
            if score >= threshold and sig:
                hits[key].append({"resource_id": r.resource_id, "title": r.title, "score": score,
                                  "signals": sig, "eligibility_assessed": False,
                                  "eligibility_status": "UNASSESSED",
                                  "credential_flags": credential_flags(r)})
    for v in hits.values():
        v.sort(key=lambda h: (-h["score"], h["resource_id"]))
    return hits


def _word_start(sig: str, text: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(sig), text) is not None


def discover_strict(predicates: dict[str, dict[str, Any]], corpus: list[ResourceCandidate],
                    threshold: float = EXISTING_THRESHOLD) -> dict[str, list[dict[str, Any]]]:
    """P3 matcher. Same signal-count scoring as needs._score, with three corrections drawn
    from the P2 adjudication: (R1) a hit needs at least one of the concept's OWN signals,
    so hypothesis neighbours alone cannot create a match; (R3) signals must start at a word
    boundary; (R4/R5) thin text and domain/status requirements are flagged, not hidden.
    """
    from .needs import _candidate_text
    hits: dict[str, list[dict[str, Any]]] = {k: [] for k in predicates}
    for r in corpus:
        text = _candidate_text(r)
        thin = len((r.description or "").strip()) < MIN_TEXT_CHARS
        reqs = [p for p in DOMAIN_REQUIREMENT_PATTERNS if re.search(p, text)]
        for key, need in predicates.items():
            sigs = [x for x in need["signals"] if _word_start(x, text)]
            own = [x for x in sigs if x in set(need.get("own_signals", need["signals"]))]
            score = round(min(1.0, min(0.55, 0.11 * len(sigs))), 2)
            if own and score >= threshold:
                hits[key].append({"resource_id": r.resource_id, "title": r.title, "score": score,
                                  "source_url": r.source_url,
                                  "signals": sorted(sigs), "own_signal_hits": sorted(own),
                                  "eligibility_assessed": False, "eligibility_status": "UNASSESSED",
                                  "credential_flags": credential_flags(r),
                                  "domain_requirement_flags": reqs, "thin_text": thin})
    for v in hits.values():
        v.sort(key=lambda h: (-h["score"], h["resource_id"]))
    return hits


def run_arms(tokens: list[dict[str, Any]], supports: list[dict[str, Any]],
             corpus: list[ResourceCandidate], threshold: float = EXISTING_THRESHOLD,
             strict: bool = False, private_terms: set[str] | None = None) -> dict[str, Any]:
    """Arm A literal, B1 normalized aliases, B2 aliases + hypothesis neighbours.

    strict=True is the P3 correction set (stronger support gate + discover_strict).
    """
    members = backed_concepts(tokens, supports)
    if strict:  # R2: an OUTCOME bullet or a seed record alone cannot open a concept
        by_id = {t["token_id"]: t for t in tokens}
        members = {c: ids for c, ids in members.items()
                   if any(by_id[i]["type"] in ("CAPABILITY", "METHOD", "EXPERIENCE")
                          and by_id[i]["approval_status"] in ("APPROVED", "OWNER_COMMITTED_MASTER")
                          for i in ids)}
    preds: dict[str, dict[str, Any]] = {}
    for c in CONCEPTS:
        if c not in members:
            continue  # source-backing gate: no supporting token, no query
        preds[f"{c}|A"] = predicate_need(c, literal_signals(tokens, members[c]), "A")
        preds[f"{c}|A2"] = predicate_need(c, bag_signals(tokens, members[c]), "A2")
        preds[f"{c}|B1"] = predicate_need(c, expanded_signals(c, with_hypothesis=False), "B1")
        preds[f"{c}|B2"] = predicate_need(c, expanded_signals(c, with_hypothesis=True), "B2",
                                          own=expanded_signals(c, with_hypothesis=False))
    if private_terms:
        check_predicates_clean(preds, private_terms)
    run = discover_strict if strict else discover
    return {"predicates": preds, "hits": run(preds, corpus, threshold),
            "gated_out": sorted(set(CONCEPTS) - set(members))}


def run_controls(corpus: list[ResourceCandidate], strict: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {}
    run = discover_strict if strict else discover
    for cid, spec in CONTROL_CONCEPTS.items():
        pred = {cid: predicate_need(cid, [s for s in spec["discover"]], "CTRL")}
        out[cid] = {"gate": "REFUSED_NO_SOURCE_BACKING",
                    "bypassed_matches": run(pred, corpus, ANY_HIT)[cid]}
    return out


def intent_os_preview(objective: str, corpus: list[ResourceCandidate]) -> dict[str, Any]:
    """Existing read-only projection over snapshot rows. No eligibility, no writes."""
    from .intent_os import evaluate_objective
    rows = [dataclasses.asdict(r) for r in corpus]
    return evaluate_objective(objective, rows, source_mode="snapshot",
                              source_status="SNAPSHOT_NOT_LIVE_VERIFIED")


def write_private_json(path: str | Path, data: Any, *, guard_dir: bool = True) -> None:
    """Exclusive, 0600, and never inside a git work tree."""
    from .application_portfolio import _inside_git_work_tree
    p = Path(path).expanduser().resolve()
    if guard_dir and _inside_git_work_tree(p.parent):
        raise ValueError("refusing to write private pilot data inside a git work tree")
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
    except BaseException:
        try:
            os.unlink(p)  # a failed write must not block a retry
        except OSError:
            pass
        raise


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def human_reported_submission(channel: str, reported_on: str, draft_hashes: dict[str, str]) -> dict[str, Any]:
    """Outcome node for a human-reported submission. Reports, never verifies.

    Kept distinct from any draft: the draft's hashes are recorded only to show the
    reported submission is NOT linked to them. No contact details belong here.
    """
    return {
        "schema": SCHEMA + ".outcome",
        "status": "HUMAN_REPORTED_RESUME_SUBMITTED",
        "reported_by": "owner",
        "reported_on": reported_on,
        "channel": channel,
        "document_submitted": "OWNER_MASTER_RESUME_VERSION_UNKNOWN",
        "linked_to_unapproved_draft": False,
        "unapproved_draft_hashes": dict(draft_hashes),
        "draft_status": "UNAPPROVED_NOT_SUBMITTED",
        "client": "UNKNOWN", "job_requirements": "UNKNOWN",
        "match_outcome": "UNKNOWN", "contract_status": "UNKNOWN",
        "verified_by_system": False,
        "authority_effect": "NONE",
    }
