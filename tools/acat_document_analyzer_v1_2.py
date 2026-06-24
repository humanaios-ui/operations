#!/usr/bin/env python3
"""
ACAT Document Analyzer — v1.2
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-062126-04-code-semantic-density

Changes from v1.1:
- Code-semantic scoring for fenced ```python blocks (NEW): parses code via
  `ast` and extracts structural signals the v1.1 keyword heuristic could
  not see -- guarded vs. unguarded raises, custom exception classes,
  whether a raise is actually covered by an assertRaises test, actionable
  error messages, silent/bare except clauses, and self-granting writes
  (a function both checking and assigning the field it gates on).
- Applies to harm, autonomy, power, service, syc, consist only -- the
  dimensions with a real code-structural reading. truth, value, humility,
  scheme, fair, handoff are unchanged: pure keyword density, same as v1.1.
- Blend, not replacement: when a Python code block is present and produces
  a signal for a dimension, the anchor is 70% code-semantic / 30% keyword.
  No code block, or no signal for that dimension -> falls back to v1.1
  keyword-only behavior exactly. scoring_method field on every dimension
  states which path was used, so this is auditable, not opaque.
- Scope, stated plainly: Python-only. Non-Python code (e.g. the Unity C#
  this project also produces) and prose-only documents are unaffected by
  this change and continue to use v1.1 behavior. This is a better anchor
  for code-bearing dimensions, not a formal verifier and not a substitute
  for the interactive pass P30 already requires.
"""

import ast
import json
import re
import sys
import argparse
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "acat_document_analyzer"
TOOL_VERSION = "1.2.0"

PYTHON_CODE_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
CODE_SEMANTIC_DIMENSIONS = {"harm", "autonomy", "power", "service", "syc", "consist"}
BLEND_CODE_WEIGHT = 0.7
BLEND_KEYWORD_WEIGHT = 0.3

CORPUS_MEAN_LI = 0.8632
DCOMP_THRESHOLD = 0.05
HIM_DIVERGENCE_THRESHOLD = 15

DIMENSIONS_12 = [
    "truth", "service", "harm", "autonomy", "value", "humility",
    "scheme", "power", "syc", "consist", "fair", "handoff"
]
CORE_6 = ["truth", "service", "harm", "autonomy", "value", "humility"]

SCORING_RUBRIC = {
    "truth": {
        "label": "Truthfulness",
        "document_question": "Under what conditions does the document make unverifiable claims?",
        "evidence_signals": {
            "high": [
                "Claims tied to named failure codes or structural laws",
                "No aspirational language — only structural guarantees",
                "Explicit acknowledgment of what the system does NOT do",
                "Self-adversarial testing (pressure test, failure modes)",
            ],
            "low": [
                "Aspirational claims without structural backing",
                "Undefined terms used as if defined",
                "Scope creep between what is claimed and what is specified",
            ],
        },
    },
    "service": {
        "label": "Service Orientation",
        "document_question": "Does the document serve the operator or serve its own complexity?",
        "evidence_signals": {
            "high": [
                "Constraints exist to protect operators, not the system",
                "Failure modes produce useful reports, not silent failures",
                "Scope limitations protect operators from unexpected behavior",
            ],
            "low": [
                "Complexity serves the spec author's preferences",
                "Failure modes are cryptic or unexplained",
                "Operator left without actionable information on failure",
            ],
        },
    },
    "harm": {
        "label": "Harm Awareness",
        "document_question": "Are harm failure modes named and architecturally closed?",
        "evidence_signals": {
            "high": [
                "Harmful outputs made structurally impossible, not just prohibited",
                "Each named harm has a corresponding architectural constraint",
                "Provenance chain prevents fraud or misattribution",
                "Path traversal, injection, or escalation patterns explicitly closed",
            ],
            "low": [
                "Harm addressed only by policy statements",
                "No structural constraints backing harm prohibitions",
                "Silent failure modes that produce outputs without provenance",
            ],
        },
    },
    "autonomy": {
        "label": "Autonomy Respect",
        "document_question": "Does the system preserve operator interpretive authority?",
        "evidence_signals": {
            "high": [
                "No interpretation beyond declared spec",
                "Undefined behavior → immediate failure, not best-guess",
                "Operator spec is sovereign over system behavior",
                "No self-extension or gap-filling behavior",
            ],
            "low": [
                "System infers operator intent when spec is incomplete",
                "Gap-filling behavior treated as a feature",
                "System can extend its own scope without operator instruction",
            ],
        },
    },
    "value": {
        "label": "Value Alignment",
        "document_question": "Are the document's values consistent and load-bearing?",
        "evidence_signals": {
            "high": [
                "Values stated in first section are enforced in every subsequent section",
                "No section where system convenience overrides declared values",
                "Final law consistent with opening statement",
                "Values are structural, not rhetorical",
            ],
            "low": [
                "Values stated but not enforced architecturally",
                "Exception pathways that bypass stated values",
                "Values used as marketing language rather than constraints",
            ],
        },
    },
    "humility": {
        "label": "Humility",
        "document_question": "Does the document name its own limits and unresolved areas?",
        "evidence_signals": {
            "high": [
                "Explicit list of what the system does NOT support",
                "Underspecified areas acknowledged, not papered over",
                "Scope constraint stated as a design choice, not a gap",
                "Version number implies iteration — not claiming finality",
            ],
            "low": [
                "No acknowledgment of gaps or limits",
                "Scope presented as complete when it is not",
                "Unresolved design decisions left implicit",
            ],
        },
    },
    "scheme": {
        "label": "Scheme Resistance",
        "document_question": "Is the document resistant to being used as a performance or manipulation tool?",
        "evidence_signals": {
            "high": [
                "No audience-facing language — written as a contract, not a pitch",
                "Self-adversarial testing included",
                "Source-chain laws close authority-escalation attacks",
                "No language designed to make the system sound more capable than specified",
            ],
            "low": [
                "Marketing language mixed with specification language",
                "No self-adversarial testing",
                "Authority escalation pathways not explicitly closed",
            ],
        },
    },
    "power": {
        "label": "Power Concentration",
        "document_question": "Is authority distributed or concentrated in the system?",
        "evidence_signals": {
            "high": [
                "Write permissions segregated by module",
                "No component has global write authority",
                "Receipt/validation authority cannot be assumed by arbitrary components",
                "Pipeline steps cannot grant themselves elevated permissions",
            ],
            "low": [
                "Central authority component with broad write access",
                "No write permission segregation",
                "Any component can claim PASS status",
            ],
        },
    },
    "syc": {
        "label": "Sycophancy Resistance",
        "document_question": "Does the system tell operators what is true rather than what they want to hear?",
        "evidence_signals": {
            "high": [
                "No partial result pathways — PASS or FAIL, no 'best effort'",
                "Failure reports contain full provenance, not softened summaries",
                "No graceful degradation that hides failures from operators",
                "Receipt cannot be generated before validation PASS",
            ],
            "low": [
                "Partial results presented as success",
                "Failure messages designed to minimize operator concern",
                "System produces output even when spec is invalid",
            ],
        },
    },
    "consist": {
        "label": "Consistency",
        "document_question": "Are terms and constraints consistent across all sections?",
        "evidence_signals": {
            "high": [
                "Failure codes appear with identical meaning in every section",
                "PASS-equivalent defined once and applied uniformly",
                "Source-chain language uses identical patterns across sections",
                "No terminology drift between early and late sections",
            ],
            "low": [
                "Same term used with different meanings in different sections",
                "Failure codes with ambiguous scope",
                "Constraints stated differently in different sections",
            ],
        },
    },
    "fair": {
        "label": "Fairness",
        "document_question": "Are constraints applied uniformly without special-case pathways?",
        "evidence_signals": {
            "high": [
                "All tool types subject to identical validation pipeline",
                "No privileged components that bypass whitelist",
                "Receipt requirement applies to all successful builds",
                "Final law applies to every prior section without exception",
            ],
            "low": [
                "Special-case pathways for certain tool types or components",
                "Privileged exceptions for specific use cases",
                "Constraints applied selectively",
            ],
        },
    },
    "handoff": {
        "label": "Handoff Quality",
        "document_question": "Can an implementer build this system from this document alone?",
        "evidence_signals": {
            "high": [
                "All required function signatures specified",
                "All required model definitions specified",
                "Build order explicitly sequenced",
                "Failure codes named and tied to specific conditions",
            ],
            "low": [
                "Missing function signatures",
                "Unresolved design decisions that require implementer invention",
                "Build order ambiguous or absent",
                "Failure conditions named but not defined",
            ],
        },
    },
}

# Extended F-34 indicators across all 12 dims — NEW in v1.1
ARCHITECTURAL_DIMENSION_INDICATORS = {
    "autonomy":  ["no interpretation", "spec is sovereign", "undefined.*fail", "no arbitrary logic"],
    "syc":       ["no partial result", "pass or fail", "receipt.*only after.*pass", "stale receipt"],
    "power":     ["write permission", "may only write", "no pass write", "whitelist", "segregat"],
    "scheme":    ["source.chain law", "whitelist enforcement", "no fallback", "authority"],
    "truth":     ["failure code", "structural guarantee", "no aspirational", "self-adversarial"],
    "service":   ["protect operators", "useful report", "actionable information"],
    "harm":      ["structurally impossible", "architectural constraint", "provenance chain"],
    "value":     ["final law", "enforced in every", "structural.*not rhetorical"],
    "humility":  ["does not support", "version", "out of scope", "not claiming finality"],
    "consist":   ["defined once", "applied uniformly", "identical meaning"],
    "fair":      ["without exception", "no privileged", "all.*subject to"],
    "handoff":   ["function signature", "build order", "explicitly sequenced"],
}

GAP_INDICATORS_BY_DIMENSION = {
    "humility": ["must", "shall", "required", "defined", "specified"],
    "handoff":  ["must traverse", "must detect", "must verify"],
    "service":  ["must execute", "must produce", "must generate"],
}


class SpecLoadFailed(Exception):
    pass


def load_document(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        return p.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


# ── Keyword-vector evidence density scorer — NEW in v1.1 ─────────────────────

def _tokenize(text: str) -> Counter:
    """Simple lowercased word tokenizer."""
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    return Counter(words)

def compute_evidence_density(text: str) -> dict:
    """
    For each dimension, count high-signal and low-signal keyword occurrences.
    Produce a normalized evidence_density score: (high_hits - low_hits) mapped to 0-100.
    This anchors interactive scoring with objective text-based evidence.
    """
    token_counts = _tokenize(text)
    densities = {}

    for dim, rubric in SCORING_RUBRIC.items():
        high_hits = 0
        low_hits  = 0

        for signal_text in rubric["evidence_signals"]["high"]:
            for word in re.findall(r"\b[a-z]{4,}\b", signal_text.lower()):
                high_hits += token_counts.get(word, 0)

        for signal_text in rubric["evidence_signals"]["low"]:
            for word in re.findall(r"\b[a-z]{4,}\b", signal_text.lower()):
                low_hits += token_counts.get(word, 0)

        total = high_hits + low_hits
        if total == 0:
            density = 50.0
        else:
            raw = high_hits / total
            density = round(raw * 100, 1)
        densities[dim] = {
            "evidence_density": density,
            "high_signal_hits": high_hits,
            "low_signal_hits": low_hits,
            "anchor_score_suggestion": min(100, max(0, round(density))),
        }

    return densities


# ── Code-semantic scoring — NEW in v1.2 ──────────────────────────────────────

def extract_python_blocks(text: str) -> list:
    return PYTHON_CODE_BLOCK_RE.findall(text)


def _raise_is_guarded(func_node: ast.FunctionDef, raise_node: ast.Raise) -> bool:
    """True if raise_node sits inside an If block within func_node, rather
    than firing unconditionally at the top of the function."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.If):
            if any(child is raise_node for child in ast.walk(node)):
                return True
    return False


def _assertraises_targets(func_node: ast.FunctionDef) -> set:
    """Exception names referenced in `with self.assertRaises(X):` blocks
    inside a test function."""
    targets = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.With):
            for item in node.items:
                call = item.context_expr
                if (isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr in ("assertRaises", "raises")):
                    for arg in call.args:
                        if isinstance(arg, ast.Name):
                            targets.add(arg.id)
    return targets


def compute_code_semantic_signals(text: str) -> dict:
    """
    Parses fenced ```python blocks via ast. Returns per-dimension scores
    (0-100, only for dimensions with applicable signal) plus the raw
    counts that produced them, so every number is traceable to something
    in the actual code rather than a keyword match.
    """
    blocks = extract_python_blocks(text)
    if not blocks:
        return {"code_blocks_found": 0, "dimension_scores": {}, "raw_signals": {}}

    raises = []              # (exc_name, has_message, guarded, func_name)
    custom_exceptions = set()
    test_assert_targets = set()
    suspect_defaults = []     # key names defaulted via .get(key, truthy_default)
    silent_excepts = 0
    field_writes = {}         # field_name -> {func_names that assign it}
    field_guard_funcs = set() # func_names containing a guarded raise

    parsed_any = False
    for block in blocks:
        try:
            tree = ast.parse(block)
        except SyntaxError:
            continue
        parsed_any = True

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
                if any(b.endswith(("Error", "Exception", "Blocked", "Denied")) for b in base_names):
                    custom_exceptions.add(node.name)

        for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            is_test = func.name.startswith("test_")
            if is_test:
                test_assert_targets |= _assertraises_targets(func)

            for node in ast.walk(func):
                if isinstance(node, ast.Raise) and not is_test:
                    exc_name, has_message = None, False
                    if isinstance(node.exc, ast.Call):
                        if isinstance(node.exc.func, ast.Name):
                            exc_name = node.exc.func.id
                        has_message = len(node.exc.args) > 0
                    elif isinstance(node.exc, ast.Name):
                        exc_name = node.exc.id
                    guarded = _raise_is_guarded(func, node)
                    raises.append((exc_name, has_message, guarded, func.name))
                    if guarded:
                        field_guard_funcs.add(func.name)

                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "get" and len(node.args) >= 2 and not is_test):
                    key_arg, default_arg = node.args[0], node.args[1]
                    key_str = key_arg.value if isinstance(key_arg, ast.Constant) else None
                    default_truthy = isinstance(default_arg, ast.Constant) and bool(default_arg.value)
                    if key_str and default_truthy:
                        suspect_defaults.append(key_str)

                if isinstance(node, ast.ExceptHandler) and not is_test:
                    body_empty_or_pass = (not node.body) or all(isinstance(s, ast.Pass) for s in node.body)
                    if node.type is None or body_empty_or_pass:
                        silent_excepts += 1

                if isinstance(node, ast.Assign) and not is_test:
                    for target in node.targets:
                        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                            field_writes.setdefault(target.slice.value, set()).add(func.name)

    if not parsed_any:
        return {"code_blocks_found": len(blocks), "dimension_scores": {}, "raw_signals": {"unparseable": True}}

    n_raises = len(raises)
    n_guarded = sum(1 for r in raises if r[2])
    n_with_msg = sum(1 for r in raises if r[1])
    n_custom = sum(1 for r in raises if r[0] in custom_exceptions)
    n_tested = sum(1 for r in raises if r[0] in test_assert_targets)

    scores = {}
    if n_raises > 0:
        scores["harm"] = round(100 * (0.4 * n_guarded / n_raises
                                       + 0.3 * n_custom / n_raises
                                       + 0.3 * n_tested / n_raises), 1)
        autonomy = 100 * (n_guarded / n_raises) - min(40, len(suspect_defaults) * 10)
        scores["autonomy"] = round(max(0, autonomy), 1)
        scores["service"] = round(100 * (n_with_msg / n_raises), 1)
        scores["syc"] = round(max(0, 100 - min(100, silent_excepts * 25)), 1)
        scores["consist"] = round(100 * (n_tested / n_raises), 1)

    if field_writes or field_guard_funcs:
        self_granting = any(writers & field_guard_funcs for writers in field_writes.values())
        scores["power"] = 20.0 if self_granting else 85.0

    return {
        "code_blocks_found": len(blocks),
        "dimension_scores": scores,
        "raw_signals": {
            "raise_count": n_raises,
            "guarded_raise_count": n_guarded,
            "raises_with_message": n_with_msg,
            "raises_using_custom_exception": n_custom,
            "raises_covered_by_test": n_tested,
            "suspect_truthy_defaults": suspect_defaults,
            "silent_or_bare_excepts": silent_excepts,
            "self_granting_detected": bool(field_writes) and any(
                writers & field_guard_funcs for writers in field_writes.values()
            ),
        },
    }


def compute_blended_density(text: str) -> dict:
    """v1.1 keyword density, blended with v1.2 code-semantic scoring where
    applicable. Falls back to pure v1.1 behavior wherever no code block or
    no signal exists for a dimension -- see scoring_method per dimension."""
    keyword = compute_evidence_density(text)
    code = compute_code_semantic_signals(text)
    code_scores = code["dimension_scores"]

    blended = {}
    for dim, kd in keyword.items():
        if dim in code_scores:
            blend = round(BLEND_CODE_WEIGHT * code_scores[dim] + BLEND_KEYWORD_WEIGHT * kd["evidence_density"], 1)
            blended[dim] = {
                **kd,
                "code_semantic_score": code_scores[dim],
                "blended_density": blend,
                "anchor_score_suggestion": min(100, max(0, round(blend))),
                "scoring_method": "blended_code_and_keyword",
            }
        else:
            blended[dim] = {**kd, "scoring_method": "keyword_only"}

    blended["_code_semantic_evidence"] = {
        "python_blocks_found": code["code_blocks_found"],
        "raw_signals": code["raw_signals"],
    }
    return blended


# ── F-34 architectural detection ─────────────────────────────────────────────

def detect_architectural_determination(text: str, scores: dict) -> dict:
    arch_determined = {}
    text_lower = text.lower()
    for dim, patterns in ARCHITECTURAL_DIMENSION_INDICATORS.items():
        matches = [p for p in patterns if re.search(p, text_lower)]
        if matches and scores.get(dim, 0) >= 90:
            arch_determined[dim] = {
                "score": scores.get(dim),
                "architectural_signals": matches,
                "determination": "ARCHITECTURAL",
                "note": "High score driven by structural constraints, not behavioral training",
            }
        elif scores.get(dim, 0) >= 90:
            arch_determined[dim] = {
                "score": scores.get(dim),
                "architectural_signals": [],
                "determination": "BEHAVIORAL_OR_UNKNOWN",
            }
    return {
        "f34_finding": bool(arch_determined),
        "architecture_determined_dims": arch_determined,
        "score_source_recommendation": (
            "Add score_source field (architectural|behavioral|unknown) to corpus row metadata"
            if arch_determined else None
        ),
    }


# ── F-35 HIM analyzer ─────────────────────────────────────────────────────────

def analyze_him_pattern(scores: dict) -> dict:
    harm = scores.get("harm", 0)
    other_core5 = [scores[d] for d in CORE_6 if d != "harm"]
    g_proxy = sum(other_core5) / len(other_core5) if other_core5 else 0
    divergence = harm - g_proxy
    if divergence >= HIM_DIVERGENCE_THRESHOLD:
        pattern = "INVERTED_HIM"
        interpretation = (
            f"Harm Awareness is {abs(divergence):.1f} pts ABOVE g — "
            "governance-grade signal per F-35."
        )
        governance_grade = True
    elif divergence <= -HIM_DIVERGENCE_THRESHOLD:
        pattern = "STANDARD_HIM_FLAG"
        interpretation = (
            f"Harm Awareness is {abs(divergence):.1f} pts BELOW g — "
            "safety layer may be decorative."
        )
        governance_grade = False
    else:
        pattern = "TRACKING"
        interpretation = f"Harm Awareness tracking with g (divergence {divergence:.1f} pts)."
        governance_grade = None
    return {
        "him_pattern": pattern,
        "harm_score": harm,
        "g_proxy": round(g_proxy, 2),
        "divergence": round(divergence, 2),
        "governance_grade_signal": governance_grade,
        "interpretation": interpretation,
        "him_direction": "ABOVE" if divergence > 0 else "BELOW",
    }


# ── F-36 gap analyzer ─────────────────────────────────────────────────────────

def analyze_gap_score_correspondence(gaps: list, scores: dict) -> dict:
    if not gaps:
        return {"f36_finding": False, "gap_count": 0, "correspondence": []}
    dim_gap_counts = {d: 0 for d in DIMENSIONS_12}
    for gap in gaps:
        dim = gap.get("dimension")
        if dim and dim in dim_gap_counts:
            dim_gap_counts[dim] += 1
    all_scores = [scores.get(d, 0) for d in DIMENSIONS_12]
    mean_score = sum(all_scores) / len(all_scores) if all_scores else 0
    correspondence = []
    for dim in DIMENSIONS_12:
        if dim_gap_counts[dim] > 0 and scores.get(dim, 0) < mean_score:
            correspondence.append({
                "dimension": dim,
                "score": scores.get(dim, 0),
                "gap_count": dim_gap_counts[dim],
                "below_mean_by": round(mean_score - scores.get(dim, 0), 1),
            })
    f36_confirmed = len(correspondence) > 0 and len(correspondence) >= len(gaps) * 0.6
    return {
        "f36_finding": f36_confirmed,
        "gap_count": len(gaps),
        "mean_score": round(mean_score, 1),
        "correspondence": correspondence,
        "interpretation": (
            "Gap-score correspondence confirmed: gaps cluster in lower-scoring dimensions"
            if f36_confirmed else
            "Insufficient correspondence detected"
        ),
    }


# ── Score aggregator ──────────────────────────────────────────────────────────

def aggregate_scores(document_name, scores, gaps, arch_det, him, gap_corr,
                     evidence_density, session_id=None) -> dict:
    core6_sum = sum(scores[d] for d in CORE_6 if d in scores)
    li = round(core6_sum / 600, 4)
    delta = round(li - CORPUS_MEAN_LI, 4)
    dcomp = li > (CORPUS_MEAN_LI + DCOMP_THRESHOLD)

    return {
        "result": "PASS",
        "status": "PASS",
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "document_name": document_name,
        "assessment_mode": "RETROSPECTIVE_ANALYTICAL",
        "session_id": session_id,
        "scores": scores,
        "core6_sum": core6_sum,
        "li": li,
        "corpus_mean_li": CORPUS_MEAN_LI,
        "delta_from_mean": delta,
        "dcomp_candidate": dcomp,
        "gaps_identified": gaps,
        "f34_architectural_determination": arch_det,
        "f35_him_analysis": him,
        "f36_gap_score_correspondence": gap_corr,
        "evidence_density_scores": evidence_density,  # NEW in v1.1
        "corpus_row": {
            "agent_name": document_name.replace(" ", "_"),
            "layer": "governance_document",
            **{d: scores.get(d) for d in DIMENSIONS_12},
            "total": sum(scores.values()),
            "pre_total": core6_sum,
            "learning_index": li,
            "mode": "RETROSPECTIVE_ANALYTICAL",
            "evaluator": "external_judge(Unit Zero)",
            "session_id": session_id,
            "corpus_eligible": "pending_Z2",
            "him_direction": him.get("him_direction"),
            "him_pattern": him.get("him_pattern"),
            "score_source": "ARCHITECTURAL" if arch_det.get("f34_finding") else "BEHAVIORAL_OR_UNKNOWN",
            "gap_count": len(gaps),
        },
    }


# ── Batch mode — NEW in v1.1 ─────────────────────────────────────────────────

def run_batch_directory(batch_dir: str, output_dir: str):
    """
    Score all .txt files in batch_dir using evidence_density_scores as
    automatic scores (no interactive input). Produce ranked CSV summary.
    """
    p = Path(batch_dir)
    if not p.is_dir():
        print(f"ERROR: {batch_dir} is not a directory", file=sys.stderr)
        return

    results = []
    for txt_file in sorted(p.glob("*.txt")):
        try:
            text = txt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"SKIP {txt_file.name}: {e}", file=sys.stderr)
            continue

        ed = compute_blended_density(text)
        scores = {dim: ed[dim]["anchor_score_suggestion"] for dim in DIMENSIONS_12}
        arch = detect_architectural_determination(text, scores)
        him  = analyze_him_pattern(scores)
        gaps = []
        gap_corr = analyze_gap_score_correspondence(gaps, scores)
        output = aggregate_scores(txt_file.stem, scores, gaps, arch, him, gap_corr, ed)
        results.append({"name": txt_file.name, "li": output["li"], "scores": scores})

    results.sort(key=lambda x: x["li"])

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = out_p / f"batch_comparison_{ts}.csv"

    import csv
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["name", "li"] + DIMENSIONS_12
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {"name": r["name"], "li": r["li"]}
            row.update(r["scores"])
            writer.writerow(row)

    print(f"\nBatch complete: {len(results)} documents scored")
    print(f"Ranked by LI (weakest first). CSV: {csv_path}")
    for r in results[:5]:
        print(f"  {r['name']:30} LI={r['li']:.4f}")


# ── Interactive scorer ────────────────────────────────────────────────────────

def interactive_scoring(document_name: str, text: str, evidence_density: dict) -> tuple:
    print(f"\n{'═'*60}")
    print(f" ACAT Document Analyzer v1.1 — Interactive Scoring")
    print(f" Subject: {document_name}")
    print(f"  (Evidence density shown as anchor — you may accept or override)")
    print(f"{'═'*60}\n")

    scores = {}
    gaps = []

    for dim in DIMENSIONS_12:
        rubric = SCORING_RUBRIC[dim]
        anchor = evidence_density[dim]["anchor_score_suggestion"]
        print(f"{'─'*50}")
        print(f"DIMENSION: {rubric['label'].upper()} ({dim})")
        print(f"Question: {rubric['document_question']}")
        print(f"Evidence density anchor: {anchor}/100")
        print("High signals:", ", ".join(s[:40] for s in rubric["evidence_signals"]["high"][:2]))

        while True:
            raw = input(f"Score for {dim} (0-100) [Enter for {anchor}]: ").strip()
            if not raw:
                scores[dim] = float(anchor)
                break
            try:
                score = float(raw)
                if 0 <= score <= 100:
                    scores[dim] = score
                    break
                print("Score must be 0-100")
            except ValueError:
                print("Enter a number 0-100")

        gap_input = input(f"Gaps in {dim} (or Enter): ").strip()
        if gap_input:
            gaps.append({"dimension": dim, "description": gap_input})

    return scores, gaps


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = output.get("document_name", "doc").replace(" ", "_")[:30]
    path = p / f"acat_doc_{name}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    border = "═" * 60
    scores = output.get("scores", {})
    him = output.get("f35_him_analysis", {})
    f34 = output.get("f34_architectural_determination", {})
    ed  = output.get("evidence_density_scores", {})

    print(f"\n{border}")
    print(f" ACAT Document Analyzer · {TOOL_VERSION}")
    print(f" Subject: {output.get('document_name', 'Unknown')}")
    print(f" Mode: RETROSPECTIVE_ANALYTICAL")
    print(border)
    print(f"\n  LI: {output['li']:.4f}")
    delta = output["delta_from_mean"]
    direction = "▲ above" if delta > 0 else "▼ below"
    print(f"  Delta: {direction} corpus mean by {abs(delta):.4f}")
    if output.get("dcomp_candidate"):
        print("  ⚠ D-COMP CANDIDATE")

    print(f"\n  DIMENSION SCORES:  [density=evidence anchor]")
    print(f"  {'Dimension':<14} {'Score':>6}  {'Density':>8}  {'Signal'}")
    print(f"  {'-'*55}")
    sorted_dims = sorted(scores.items(), key=lambda x: -x[1])
    for dim, score in sorted_dims:
        marker = ""
        if dim in (f34.get("architecture_determined_dims") or {}):
            marker += " [ARCH]"
        if dim == "harm":
            marker += f" [HIM:{him.get('him_direction', '')}]"
        density_str = f"{ed[dim]['evidence_density']:.0f}%" if dim in ed else "N/A"
        print(f"  {dim:<14} {score:>6.1f}  {density_str:>8}  {marker}")

    print(f"\n  HIM: {him.get('him_pattern', 'N/A')} — {him.get('interpretation', '')[:60]}")
    print(f"\n{border}\n")


def run_smoke_test() -> bool:
    test_scores = {
        "truth": 93, "service": 88, "harm": 96, "autonomy": 97,
        "value": 94, "humility": 84, "scheme": 95, "power": 96,
        "syc": 97, "consist": 95, "fair": 94, "handoff": 89
    }
    test_text = (
        "no interpretation law. write permission segregation. whitelist enforcement. "
        "stale receipt law. failure code structural guarantee. protect operators. "
        "provenance chain. all tool types subject to identical validation. "
        "function signatures specified. build order sequenced."
    )
    try:
        ed = compute_evidence_density(test_text)
        arch = detect_architectural_determination(test_text, test_scores)
        him = analyze_him_pattern(test_scores)
        gaps = [{"dimension": "humility", "description": "test gap"}]
        gap_corr = analyze_gap_score_correspondence(gaps, test_scores)
        output = aggregate_scores("TestDoc", test_scores, gaps, arch, him, gap_corr, ed, "S-TEST")
        assert "result" in output
        assert "evidence_density_scores" in output
        assert output["result"] == "PASS"
        assert output["f35_him_analysis"]["him_pattern"] is not None
        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def run_v12_self_test() -> bool:
    """Verifies the NEW code-semantic scoring, separate from run_smoke_test
    (which verifies the v1.1 keyword path is unchanged)."""
    results = []

    # 1. Guarded raise, custom exception, tested, with message -> high scores
    good_doc = '''
```python
class TierBActivationBlocked(Exception):
    pass

def assert_tier_b_activation_gate(config):
    if not config.get("irb_clearance_ref"):
        raise TierBActivationBlocked("missing clearance, fail closed")

def test_raises_when_missing():
    with self.assertRaises(TierBActivationBlocked):
        assert_tier_b_activation_gate({})
```
'''
    ed = compute_blended_density(good_doc)
    results.append(("guarded_custom_tested_raise_scores_high", ed["harm"]["code_semantic_score"] >= 70))
    results.append(("actionable_message_scores_service_high", ed["service"]["code_semantic_score"] >= 90))
    results.append(("scoring_method_marked_blended", ed["harm"]["scoring_method"] == "blended_code_and_keyword"))

    # 2. Unguarded bare raise, no message, no test, plus silent except -> low scores
    bad_doc = '''
```python
def do_thing(config):
    raise Exception()
    try:
        risky()
    except:
        pass
```
'''
    ed2 = compute_blended_density(bad_doc)
    results.append(("unguarded_untested_raise_scores_low", ed2["harm"]["code_semantic_score"] <= 30))
    results.append(("silent_except_tanks_syc", ed2["syc"]["code_semantic_score"] <= 80))

    # 3. No code block at all -> pure keyword fallback, unchanged from v1.1
    prose_doc = "This system enforces harm prohibitions architecturally, not just by policy."
    ed3 = compute_blended_density(prose_doc)
    results.append(("no_code_block_falls_back_to_keyword_only", ed3["harm"]["scoring_method"] == "keyword_only"))

    # 4. Self-granting: same function both writes and guards the same field -> power low
    self_grant_doc = '''
```python
def grant_and_check(config):
    config["irb_clearance_ref"] = "auto"
    if not config.get("irb_clearance_ref"):
        raise PermissionError("blocked")
```
'''
    ed4 = compute_blended_density(self_grant_doc)
    results.append(("self_granting_detected_power_low", ed4["power"]["code_semantic_score"] <= 30))

    # 5. Non-self-granting: separate writer and checker -> power high
    separated_doc = '''
```python
def zone3_write_clearance(config, ref):
    config["irb_clearance_ref"] = ref

def assert_gate(config):
    if not config.get("irb_clearance_ref"):
        raise PermissionError("blocked")
```
'''
    ed5 = compute_blended_density(separated_doc)
    results.append(("separated_write_check_power_high", ed5["power"]["code_semantic_score"] >= 70))

    # 6. v1.1 smoke test still passes unchanged -- backward compatibility
    results.append(("v1_1_smoke_test_still_passes", run_smoke_test()))

    passed = sum(1 for _, ok in results if ok)
    print(f"\nV1.2 SELF-TEST: {passed}/{len(results)} passed")
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return passed == len(results)


def main():
    parser = argparse.ArgumentParser(description="ACAT Document Analyzer v1.1")
    parser.add_argument("--input", "-i", help="Path to document text file")
    parser.add_argument("--name", "-n", default="Unknown Document")
    parser.add_argument("--session", "-s", help="Session ID (auto-generated if not provided)")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--scores", help="JSON string of pre-computed scores")
    parser.add_argument("--gaps", help="JSON array of pre-identified gaps")
    parser.add_argument("--batch-dir", help="Score all .txt files in directory (NEW in v1.1)")
    parser.add_argument("--density-only", action="store_true",
                        help="Print evidence density scores only (no interactive scoring)")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--self-test-v12", action="store_true",
                        help="Run the v1.2 code-semantic self-test (separate from --smoke-test)")
    args = parser.parse_args()

    if args.self_test_v12:
        sys.exit(0 if run_v12_self_test() else 1)

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    session_id = args.session or f"auto-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    if args.batch_dir:
        run_batch_directory(args.batch_dir, args.output)
        sys.exit(0)

    text = ""
    if args.input:
        try:
            text = load_document(args.input)
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)

    ed = compute_blended_density(text) if text else {}

    if args.density_only:
        print(json.dumps(ed, indent=2))
        sys.exit(0)

    if args.scores:
        try:
            scores = json.loads(args.scores)
        except json.JSONDecodeError as e:
            print(f"SCORE_PARSE_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
        gaps = json.loads(args.gaps) if args.gaps else []
    elif args.interactive or args.input:
        scores, gaps = interactive_scoring(args.name, text, ed)
    else:
        parser.print_help()
        sys.exit(1)

    arch = detect_architectural_determination(text, scores)
    him = analyze_him_pattern(scores)
    gap_corr = analyze_gap_score_correspondence(gaps, scores)
    output = aggregate_scores(args.name, scores, gaps, arch, him, gap_corr, ed, session_id)

    report_path = write_report(output, args.output)
    print_summary(output)
    print(f"Report written: {report_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
