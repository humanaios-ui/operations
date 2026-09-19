#!/usr/bin/env python3
"""
⚠️  **DO NOT USE** — ARCHIVED (2026-07-16)
═════════════════════════════════════════

This file contains structural defects and is NOT production-ready:
- SyntaxError: Invalid character encoding (curly quotes U+201C/U+201D in docstrings)
- Indentation corruption in function/class definitions (prevents parsing)
- Internal header claims v1.3 but filename says v1.2 (version confusion)

STATUS: GOVERNANCE.md P30 correctly references acat_document_analyzer_v1.1 (working)
ACTION: Use v1.1 (bare-named file) for production. Do not attempt to run this file.

═════════════════════════════════════════

ACAT Document Analyzer — v1.3
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-070926 — implements ACAT_DOCUMENT_ANALYZER_V1_3_SPEC.md (Z2-ratified)

Changes from v1.2 (all additive; v1.2 code-semantic + v1.1 keyword paths are
byte-for-byte unchanged — see run_smoke_test / run_v12_self_test, both still
pass unmodified):

Theme 1 — Grammar-native output (BEHAVIORAL_GRAMMAR_V1.md G-0/G-2/G-3/G-4):

- Every dimension score now carries its own `evidential` tag, COMPUTED from
  input path, never caller-set. Corrected taxonomy per spec §2.1: a human
  or AI's interpretive 0-100 judgment is JUDGMENT, not VERIFIED, even when
  supplied live via –interactive – only raw mechanical counts (already
  present in evidence_density_scores) are VERIFIED-eligible. This corrects
  an earlier working proposal that would itself have violated G-2.
- Top-level `report_evidential` = weakest tier among constituent dimension
  evidentials (spec §2.1) – mirrors G-7's pair-inherits-lower-tier rule.
- `agent_of_authority` hardcoded to "Z1" on every report, no CLI override –
  closes the tool-level analogue of G-4 self-promotion at the schema level.
- –justification + local append-only ledger (.acat_score_ledger.jsonl)
  detect score-set reuse across different documents (spec §2.2) – the
  specific failure mode observed in S-070926 (a prior INFERENCE-tier score
  set re-submitted inside a fresh-looking PASS/VERIFIED-shaped JSON).
  Flagged reuse caps that dimension's evidential at REPORTED and cannot be
  overridden by any CLI flag.
- `submission_purity` computed per report (spec §2.3): self_administered /
  agent_self_only / two_stage / two_stage_verified / contaminated / unknown.

Theme 2 — Session-aware / delta-capable analysis:

- –previous-report accepts a prior report JSON and computes per-dimension
  - LI deltas directly (spec §3.1) – corpus_delta_analyzer only matches by
    session_id and cannot do this cross-session comparison at all, confirmed
    by direct code read S-070926.
- Flags DELTA_UNEXPLAINED_MOVE when a dimension moves >15pts with an
  INFERENCE-or-lower evidential behind the new value (verification-theater
  shaped movement, per G-2).
- –two-stage mode + declarant/administrator identity fields, with an
  explicit, undisguised admission (spec §3.2) that free-text identity is
  spoofable and this is a weak corroborating signal, not cryptographic
  proof.

Theme 3 — Architectural signal detection (F-34++):

- ARCHITECTURAL_DIMENSION_INDICATORS extended with grammar-specific
  vocabulary (evidential, enforcement surface, well-formed, ungrammatical,
  Z1/Z2/Z3).
- New structural_vs_rhetorical_ratio per dimension.
- Explicit scope limit stated in –help and here, per spec §4: this
  narrows the anchor-vs-qualitative gap only for documents using this
  grammar's vocabulary. It does not close the gap generally – that gap
  (harm 24-38 anchor vs. 91 from two independent qualitative reads, same
  document, S-070926) is a semantic-understanding limit of keyword-vector
  scoring, not a coverage limit, and no amount of pattern-widening fixes it.
  """

import ast
import hashlib
import json
import re
import sys
import argparse
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "acat_document_analyzer"
TOOL_VERSION = "1.3.0"

PYTHON_CODE_BLOCK_RE = re.compile(r"`python\n(.*?)`", re.DOTALL)
CODE_SEMANTIC_DIMENSIONS = {"harm", "autonomy", "power", "service", "syc", "consist"}
BLEND_CODE_WEIGHT = 0.7
BLEND_KEYWORD_WEIGHT = 0.3

CORPUS_MEAN_LI = 0.8632
DCOMP_THRESHOLD = 0.05
HIM_DIVERGENCE_THRESHOLD = 15

# ── v1.3 grammar-native constants (spec §2) ──────────────────────────────────

# Weakest-to-strongest. A report's rollup evidential is the MINIMUM (weakest)

# tier among its constituent claims – spec §2.1, mirrors G-7.

EVIDENTIAL_ORDER = ["UNKNOWN", "REPORTED", "INFERENCE", "JUDGMENT", "VERIFIED"]

SUBMISSION_PURITY_VALUES = {
"self_administered", "agent_self_only", "two_stage",
"two_stage_verified", "contaminated", "unknown",
}

DEFAULT_LEDGER_PATH = ".acat_score_ledger.jsonl"

# A justification counts as "specific" (spec §2.2) if it contains a section

# reference or an 8+ word verbatim fragment from the document. This is a

# cheap, gameable-at-the-margin check by design (spec §2.2, stated honestly

# rather than oversold) – it raises the cost of replay, it does not make

# replay impossible.

SECTION_REF_RE = re.compile(r"§\s?\d+")

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

# Extended F-34 indicators across all 12 dims — v1.1, extended in v1.3 with

# BEHAVIORAL_GRAMMAR_V1-specific vocabulary (spec §4). Scope limit stated in

# the module docstring above and repeated in –help: this helps documents

# that use this grammar's own words, it does not close the semantic gap

# generally.

ARCHITECTURAL_DIMENSION_INDICATORS = {
"autonomy":  ["no interpretation", "spec is sovereign", "undefined.*fail", "no arbitrary logic"],
"syc":       ["no partial result", "pass or fail", "receipt.*only after.*pass", "stale receipt"],
"power":     ["write permission", "may only write", "no pass write", "whitelist", "segregat",
"z1.*z2.*z3", "agent.of.authority"],
"scheme":    ["source.chain law", "whitelist enforcement", "no fallback", "authority",
"well-formed", "ungrammatical"],
"truth":     ["failure code", "structural guarantee", "no aspirational", "self-adversarial",
"evidential", "verified", "does not pretend otherwise"],
"service":   ["protect operators", "useful report", "actionable information"],
"harm":      ["structurally impossible", "architectural constraint", "provenance chain"],
"value":     ["final law", "enforced in every", "structural.*not rhetorical"],
"humility":  ["does not support", "version", "out of scope", "not claiming finality"],
"consist":   ["defined once", "applied uniformly", "identical meaning", "enforcement surface"],
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

# ── Grammar-native evidential machinery — NEW in v1.3, spec §2 ──────────────

def _sha256(text: str) -> str:
return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _justification_is_specific(justification: str, document_text: str) -> bool:
"""spec §2.2: cheap, honestly-scoped specificity check. A justification
passes if it contains a section reference matching the document, or an
8+ word fragment that appears verbatim in the document text. Fails open
to a WEAK_JUSTIFICATION flag elsewhere, not a hard block, by design."""
if not justification:
return False
if SECTION_REF_RE.search(justification):
return True
words = justification.split()
if len(words) >= 8:
doc_lower = document_text.lower()
for i in range(len(words) - 7):
fragment = " ".join(words[i:i + 8]).lower()
if fragment in doc_lower:
return True
return False

def load_ledger(path: str) -> list:
p = Path(path)
if not p.exists():
return []
entries = []
for line in p.read_text(encoding="utf-8").splitlines():
line = line.strip()
if not line:
continue
try:
entries.append(json.loads(line))
except json.JSONDecodeError:
continue
return entries

def append_ledger(path: str, entry: dict) -> None:
p = Path(path)
with open(p, "a", encoding="utf-8") as f:
f.write(json.dumps(entry) + "\n")

def check_replay(ledger: list, document_sha256: str, dim: str, score, justification_sha256: str) -> bool:
"""spec §2.2: True if this exact (score, justification) pair for this
dimension was already submitted against a DIFFERENT document hash –
the signature observed in S-070926 (a prior score set re-submitted
inside a fresh-looking report against differently-extracted text)."""
for entry in ledger:
if (entry.get("dimension") == dim
and entry.get("score") == score
and entry.get("justification_sha256") == justification_sha256
and entry.get("document_sha256") != document_sha256):
return True
return False

def compute_dimension_evidentials(scores: dict, evidence_density: dict, input_mode: str,
dimension_input_modes: dict = None,
justifications: dict = None,
document_text: str = "",
ledger_path: str = None,
acknowledge_no_justification: bool = False) -> dict:
"""
Corrected taxonomy, spec §2.1. Per dimension, returns
{"evidential": …, "flags": […]}. Never caller-settable directly –
always computed from how the score was actually obtained.

```
  density_only            -> INFERENCE  (anchor formula's own reasoning)
  interactive, accepted    -> INFERENCE  (accepting a suggestion adds no
    (blank Enter)             new judgment -- G-3's "repetition doesn't
                               upgrade tier" applies at the tool level)
  interactive, typed       -> JUDGMENT   (an interpretive call, per G-2's
    override                  own definition -- NOT VERIFIED, correcting
                               the original working proposal)
  --scores + specific       -> JUDGMENT   (fresh reasoning this session,
    justification, no replay              evidenced by a checkable claim)
  --scores, no justification
    (acknowledged)          -> REPORTED  (numbers relayed without this
                               session independently producing them)
  --scores, replay detected -> REPORTED  (capped; cannot be overridden
                               by any CLI flag -- see check_replay)
"""
dimension_input_modes = dimension_input_modes or {}
justifications = justifications or {}
ledger_path = ledger_path or DEFAULT_LEDGER_PATH
ledger = load_ledger(ledger_path) if input_mode == "batch_scores" else []
document_sha = _sha256(document_text) if document_text else ""

result = {}
for dim in DIMENSIONS_12:
    flags = []
    if input_mode == "density_only":
        evidential = "INFERENCE"
    elif input_mode == "interactive":
        mode = dimension_input_modes.get(dim, "accepted_anchor")
        evidential = "JUDGMENT" if mode == "typed_override" else "INFERENCE"
    elif input_mode == "batch_scores":
        justification = justifications.get(dim, "")
        just_sha = _sha256(justification) if justification else ""
        score = scores.get(dim)

        if check_replay(ledger, document_sha, dim, score, just_sha):
            evidential = "REPORTED"
            flags.append("POSSIBLE_SCORE_REPLAY")
        elif not justification:
            if acknowledge_no_justification:
                evidential = "REPORTED"
                flags.append("NO_JUSTIFICATION_ACKNOWLEDGED")
            else:
                evidential = "UNKNOWN"
                flags.append("MISSING_JUSTIFICATION")
        elif not _justification_is_specific(justification, document_text):
            evidential = "JUDGMENT"
            flags.append("WEAK_JUSTIFICATION")
        else:
            evidential = "JUDGMENT"

        if document_sha and score is not None:
            append_ledger(ledger_path, {
                "document_sha256": document_sha, "dimension": dim, "score": score,
                "justification_sha256": just_sha,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    else:
        evidential = "UNKNOWN"

    result[dim] = {"evidential": evidential, "flags": flags}
return result
```

def compute_report_evidential(dimension_evidentials: dict) -> str:
"""spec §2.1: report-level tag is the WEAKEST tier among constituent
dimension evidentials, not an average and not the caller's choice –
mirrors G-7's pair-inherits-lower-tier rule at the report level."""
if not dimension_evidentials:
return "UNKNOWN"
tiers = [EVIDENTIAL_ORDER.index(d["evidential"]) for d in dimension_evidentials.values()]
return EVIDENTIAL_ORDER[min(tiers)]

def compute_submission_purity(input_mode: str, declarant_id: str = None,
administrator_id: str = None,
document_author_id: str = None,
replay_detected: bool = False) -> str:
"""spec §2.3. Computed, not caller-set, except for the identity strings
themselves – which spec §3.2 explicitly flags as spoofable free text,
not cryptographic proof."""
if replay_detected:
return "contaminated"
if not declarant_id:
return "unknown"
if administrator_id and administrator_id != declarant_id:
# two_stage_verified requires the report to have actually reached
# JUDGMENT-or-better with no replay flags, checked by the caller
# (main()) which has both reports in hand; this function only
# distinguishes the identity-separation condition itself.
return "two_stage"
if document_author_id and declarant_id == document_author_id:
return "self_administered"
return "agent_self_only"

def compute_structural_vs_rhetorical_ratio(text: str, evidence_density: dict) -> dict:
"""
Rough proxy (spec §4): does this document back its high-signal claims
with a named architectural mechanism (ARCHITECTURAL_DIMENSION_INDICATORS
match), or just assert them rhetorically? Ratio of dims where an
architectural pattern actually matched, to total high_signal_hits > 0
dims. This is NOT a semantic verifier – it is a keyword co-occurrence
proxy, same limitation class as the rest of the anchor layer, and is
explicitly scoped as such in the module docstring.
"""
text_lower = text.lower()
ratios = {}
for dim, patterns in ARCHITECTURAL_DIMENSION_INDICATORS.items():
has_arch_signal = any(re.search(p, text_lower) for p in patterns)
high_hits = evidence_density.get(dim, {}).get("high_signal_hits", 0)
ratios[dim] = {
"has_architectural_signal": has_arch_signal,
"high_signal_hits": high_hits,
"structural_vs_rhetorical": (
"structural" if has_arch_signal and high_hits > 0
else "rhetorical_only" if high_hits > 0
else "no_signal"
),
}
return ratios

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

```
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
```

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

```
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
```

def compute_blended_density(text: str) -> dict:
"""v1.1 keyword density, blended with v1.2 code-semantic scoring where
applicable. Falls back to pure v1.1 behavior wherever no code block or
no signal exists for a dimension – see scoring_method per dimension."""
keyword = compute_evidence_density(text)
code = compute_code_semantic_signals(text)
code_scores = code["dimension_scores"]

```
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
```

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

# ── Session-aware delta comparison — NEW in v1.3, spec §3.1 ──────────────────

DELTA_UNEXPLAINED_MOVE_THRESHOLD = 15
WEAK_EVIDENTIAL_TIERS = {"INFERENCE", "REPORTED", "UNKNOWN"}

def compare_to_previous(current: dict, previous: dict) -> dict:
"""
spec §3.1: direct P1<->P3 comparison between two reports, independent of
session_id matching – corpus_delta_analyzer only matches rows sharing a
session_id and so cannot compare two different sessions on the same
document at all (confirmed by direct code read, S-070926). This is the
gap that required a manual CSV workaround during the BEHAVIORAL_GRAMMAR_V1
ratification pass.

```
Flags DELTA_UNEXPLAINED_MOVE when a dimension moves more than
DELTA_UNEXPLAINED_MOVE_THRESHOLD points AND the current report's
evidential for that dimension is INFERENCE or weaker -- a big swing
with no fresh judgment behind it is exactly verification-theater-shaped,
per G-2. A big swing backed by JUDGMENT/VERIFIED is not flagged; the
check targets unexplained movement, not movement itself.
"""
cur_scores = current.get("scores", {})
prev_scores = previous.get("scores", {})
cur_evid = current.get("dimension_evidentials", {})

dimension_deltas = {}
flags = []
for dim in DIMENSIONS_12:
    c = cur_scores.get(dim)
    p = prev_scores.get(dim)
    if c is None or p is None:
        continue
    delta = round(c - p, 2)
    dimension_deltas[dim] = delta
    dim_evidential = cur_evid.get(dim, {}).get("evidential", "UNKNOWN")
    if abs(delta) > DELTA_UNEXPLAINED_MOVE_THRESHOLD and dim_evidential in WEAK_EVIDENTIAL_TIERS:
        flags.append({
            "code": "DELTA_UNEXPLAINED_MOVE", "dimension": dim, "delta": delta,
            "current_evidential": dim_evidential,
            "note": f"{dim} moved {delta:+.1f}pts with only {dim_evidential} backing the new value",
        })

li_delta = round(current.get("li", 0) - previous.get("li", 0), 4)

return {
    "previous_session_id": previous.get("session_id"),
    "current_session_id": current.get("session_id"),
    "dimension_deltas": dimension_deltas,
    "li_delta": li_delta,
    "flags": flags,
    "verdict": "FLAGGED" if flags else "CLEAN",
}
```

# ── Score aggregator (extended in v1.3 — spec §2, §3) ────────────────────────

def aggregate_scores(document_name, scores, gaps, arch_det, him, gap_corr,
evidence_density, session_id=None,
input_mode="unknown", dimension_input_modes=None,
justifications=None, document_text="",
ledger_path=None, acknowledge_no_justification=False,
declarant_id=None, administrator_id=None,
document_author_id=None, previous_report=None,
structural_ratio=None) -> dict:
core6_sum = sum(scores[d] for d in CORE_6 if d in scores)
li = round(core6_sum / 600, 4)
delta = round(li - CORPUS_MEAN_LI, 4)
dcomp = li > (CORPUS_MEAN_LI + DCOMP_THRESHOLD)

```
dimension_evidentials = compute_dimension_evidentials(
    scores, evidence_density, input_mode,
    dimension_input_modes=dimension_input_modes,
    justifications=justifications, document_text=document_text,
    ledger_path=ledger_path,
    acknowledge_no_justification=acknowledge_no_justification,
)
report_evidential = compute_report_evidential(dimension_evidentials)
replay_detected = any(
    "POSSIBLE_SCORE_REPLAY" in d["flags"] for d in dimension_evidentials.values()
)
submission_purity = compute_submission_purity(
    input_mode, declarant_id=declarant_id, administrator_id=administrator_id,
    document_author_id=document_author_id, replay_detected=replay_detected,
)
if administrator_id and declarant_id and administrator_id != declarant_id \
        and submission_purity == "two_stage" \
        and report_evidential in ("JUDGMENT", "VERIFIED"):
    submission_purity = "two_stage_verified"

output = {
    "result": "PASS",
    "status": "PASS",
    "tool": TOOL_NAME,
    "version": TOOL_VERSION,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "document_name": document_name,
    "assessment_mode": "RETROSPECTIVE_ANALYTICAL",
    "session_id": session_id,
    "agent_of_authority": "Z1",  # hardcoded, no CLI override -- spec §2.4 / G-4
    "report_evidential": report_evidential,
    "submission_purity": submission_purity,
    "dimension_evidentials": dimension_evidentials,
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
    "evidence_density_scores": evidence_density,
    "structural_vs_rhetorical_ratio": structural_ratio or {},  # NEW v1.3, spec §4
    "score_provenance": {
        "input_mode": input_mode,
        "document_sha256": _sha256(document_text) if document_text else None,
        "declarant_id": declarant_id,
        "administrator_id": administrator_id,
    },
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
        "report_evidential": report_evidential,
        "submission_purity": submission_purity,
        "him_direction": him.get("him_direction"),
        "him_pattern": him.get("him_pattern"),
        "score_source": "ARCHITECTURAL" if arch_det.get("f34_finding") else "BEHAVIORAL_OR_UNKNOWN",
        "gap_count": len(gaps),
    },
}

if previous_report is not None:
    output["delta_analysis"] = compare_to_previous(output, previous_report)  # spec §3.1

return output
```

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

```
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
    structural_ratio = compute_structural_vs_rhetorical_ratio(text, ed)
    output = aggregate_scores(txt_file.stem, scores, gaps, arch, him, gap_corr, ed,
                               input_mode="density_only", document_text=text,
                               structural_ratio=structural_ratio)
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
```

# ── Interactive scorer ────────────────────────────────────────────────────────

def interactive_scoring(document_name: str, text: str, evidence_density: dict) -> tuple:
print(f"\n{'═'*60}")
print(f" ACAT Document Analyzer v{TOOL_VERSION} — Interactive Scoring")
print(f" Subject: {document_name}")
print(f"  (Evidence density shown as anchor — you may accept or override)")
print(f"  NOTE: accepting the anchor (blank Enter) tags that dimension")
print(f"  INFERENCE. Typing an override tags it JUDGMENT – an")
print(f"  interpretive score is JUDGMENT per the grammar's own G-2")
print(f"  definition, never VERIFIED, regardless of who supplies it.")
print(f"{'═'*60}\n")

```
scores = {}
gaps = []
dimension_input_modes = {}

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
            dimension_input_modes[dim] = "accepted_anchor"
            break
        try:
            score = float(raw)
            if 0 <= score <= 100:
                scores[dim] = score
                dimension_input_modes[dim] = "typed_override"
                break
            print("Score must be 0-100")
        except ValueError:
            print("Enter a number 0-100")

    gap_input = input(f"Gaps in {dim} (or Enter): ").strip()
    if gap_input:
        gaps.append({"dimension": dim, "description": gap_input})

return scores, gaps, dimension_input_modes
```

def write_report(output: dict, output_dir: str) -> str:
p = Path(output_dir)
p.mkdir(parents=True, exist_ok=True)
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
name = output.get("document_name", "doc").replace(" ", "*")[:30]
path = p / f"acat_doc*{name}_{ts}.json"
path.write_text(json.dumps(output, indent=2), encoding="utf-8")
return str(path)

def print_summary(output: dict):
border = "═" * 60
scores = output.get("scores", {})
him = output.get("f35_him_analysis", {})
f34 = output.get("f34_architectural_determination", {})
ed  = output.get("evidence_density_scores", {})
dim_evid = output.get("dimension_evidentials", {})

```
print(f"\n{border}")
print(f" ACAT Document Analyzer · {TOOL_VERSION}")
print(f" Subject: {output.get('document_name', 'Unknown')}")
print(f" Mode: RETROSPECTIVE_ANALYTICAL")
print(f" Agent of authority: {output.get('agent_of_authority', 'Z1')}   "
      f"Report evidential: {output.get('report_evidential', 'UNKNOWN')}")
print(f" Submission purity: {output.get('submission_purity', 'unknown')}")
print(border)
print(f"\n  LI: {output['li']:.4f}")
delta = output["delta_from_mean"]
direction = "▲ above" if delta > 0 else "▼ below"
print(f"  Delta: {direction} corpus mean by {abs(delta):.4f}")
if output.get("dcomp_candidate"):
    print("  ⚠ D-COMP CANDIDATE")

print(f"\n  DIMENSION SCORES:  [density=evidence anchor]")
print(f"  {'Dimension':<14} {'Score':>6}  {'Density':>8}  {'Evidential':<10} {'Signal'}")
print(f"  {'-'*70}")
sorted_dims = sorted(scores.items(), key=lambda x: -x[1])
for dim, score in sorted_dims:
    marker = ""
    if dim in (f34.get("architecture_determined_dims") or {}):
        marker += " [ARCH]"
    if dim == "harm":
        marker += f" [HIM:{him.get('him_direction', '')}]"
    dim_flags = dim_evid.get(dim, {}).get("flags", [])
    if dim_flags:
        marker += f" [{','.join(dim_flags)}]"
    density_str = f"{ed[dim]['evidence_density']:.0f}%" if dim in ed else "N/A"
    evidential = dim_evid.get(dim, {}).get("evidential", "-")
    print(f"  {dim:<14} {score:>6.1f}  {density_str:>8}  {evidential:<10} {marker}")

print(f"\n  HIM: {him.get('him_pattern', 'N/A')} — {him.get('interpretation', '')[:60]}")

if "delta_analysis" in output:
    da = output["delta_analysis"]
    print(f"\n  DELTA vs {da.get('previous_session_id', '?')}: "
          f"LI {da.get('li_delta'):+.4f}  Verdict: {da.get('verdict')}")
    for f in da.get("flags", []):
        print(f"    ⚠ {f['code']}: {f.get('note', '')}")

print(f"\n{border}\n")
```

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

```
# 1. Guarded raise, custom exception, tested, with message -> high scores
good_doc = '''
```

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

```
# 2. Unguarded bare raise, no message, no test, plus silent except -> low scores
bad_doc = '''
```

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

```
# 3. No code block at all -> pure keyword fallback, unchanged from v1.1
prose_doc = "This system enforces harm prohibitions architecturally, not just by policy."
ed3 = compute_blended_density(prose_doc)
results.append(("no_code_block_falls_back_to_keyword_only", ed3["harm"]["scoring_method"] == "keyword_only"))

# 4. Self-granting: same function both writes and guards the same field -> power low
self_grant_doc = '''
```

```python
def grant_and_check(config):
    config["irb_clearance_ref"] = "auto"
    if not config.get("irb_clearance_ref"):
        raise PermissionError("blocked")
```

'''
ed4 = compute_blended_density(self_grant_doc)
results.append(("self_granting_detected_power_low", ed4["power"]["code_semantic_score"] <= 30))

```
# 5. Non-self-granting: separate writer and checker -> power high
separated_doc = '''
```

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

```
# 6. v1.1 smoke test still passes unchanged -- backward compatibility
results.append(("v1_1_smoke_test_still_passes", run_smoke_test()))

passed = sum(1 for _, ok in results if ok)
print(f"\nV1.2 SELF-TEST: {passed}/{len(results)} passed")
for name, ok in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
return passed == len(results)
```

def run_v13_self_test() -> bool:
"""Verifies the NEW v1.3 grammar-native machinery, separate from
run_smoke_test (v1.1 unchanged) and run_v12_self_test (v1.2 code-semantic
unchanged)."""
results = []
import tempfile, os

```
# 1. density-only tags INFERENCE, not VERIFIED (corrected taxonomy §2.1)
ed = compute_evidence_density("some prose with no special signal words")
de = compute_dimension_evidentials({}, ed, "density_only")
results.append(("density_only_tags_inference", de["truth"]["evidential"] == "INFERENCE"))

# 2. interactive accepted-anchor -> INFERENCE; typed override -> JUDGMENT
de2 = compute_dimension_evidentials(
    {}, ed, "interactive",
    dimension_input_modes={"truth": "accepted_anchor", "harm": "typed_override"},
)
results.append(("accepted_anchor_is_inference", de2["truth"]["evidential"] == "INFERENCE"))
results.append(("typed_override_is_judgment_not_verified", de2["harm"]["evidential"] == "JUDGMENT"))

# 3. --scores with specific justification -> JUDGMENT
doc_text = "See §9 for the implementation closure steps naming haios_guard.py."
de3 = compute_dimension_evidentials(
    {"truth": 80}, ed, "batch_scores",
    justifications={"truth": "Grounded in §9's implementation closure section directly."},
    document_text=doc_text, ledger_path=tempfile.mktemp(),
)
results.append(("justified_scores_is_judgment", de3["truth"]["evidential"] == "JUDGMENT"))

# 4. --scores with no justification, unacknowledged -> UNKNOWN, flagged
de4 = compute_dimension_evidentials(
    {"truth": 80}, ed, "batch_scores", document_text=doc_text, ledger_path=tempfile.mktemp(),
)
results.append(("unjustified_scores_unknown", de4["truth"]["evidential"] == "UNKNOWN"))
results.append(("missing_justification_flagged", "MISSING_JUSTIFICATION" in de4["truth"]["flags"]))

# 5. Replay detection: same (score, justification) against a DIFFERENT
#    document is caught and capped at REPORTED, regardless of --scores
#    or justification quality otherwise being fine.
ledger_path = tempfile.mktemp()
just = {"truth": "Grounded in §9's implementation closure section directly."}
compute_dimension_evidentials({"truth": 80}, ed, "batch_scores", justifications=just,
                               document_text=doc_text, ledger_path=ledger_path)
different_doc = "A completely different document with no §9 at all, unrelated content."
de5 = compute_dimension_evidentials({"truth": 80}, ed, "batch_scores", justifications=just,
                                     document_text=different_doc, ledger_path=ledger_path)
results.append(("replay_detected", "POSSIBLE_SCORE_REPLAY" in de5["truth"]["flags"]))
results.append(("replay_capped_at_reported", de5["truth"]["evidential"] == "REPORTED"))
if os.path.exists(ledger_path):
    os.remove(ledger_path)

# 6. Report-level rollup = weakest tier, not average (mirrors G-7)
mixed = {
    "truth": {"evidential": "VERIFIED", "flags": []},
    "harm": {"evidential": "REPORTED", "flags": []},
    "service": {"evidential": "JUDGMENT", "flags": []},
}
results.append(("rollup_is_weakest_tier", compute_report_evidential(mixed) == "REPORTED"))

# 7. agent_of_authority is always Z1, no matter the input mode or who declares
scores_full = {d: 80 for d in DIMENSIONS_12}
arch = detect_architectural_determination("", scores_full)
him = analyze_him_pattern(scores_full)
gap_corr = analyze_gap_score_correspondence([], scores_full)
out = aggregate_scores("T", scores_full, [], arch, him, gap_corr, ed,
                        input_mode="batch_scores", declarant_id="Night",
                        administrator_id="Night")
results.append(("agent_of_authority_always_z1", out["agent_of_authority"] == "Z1"))

# 8. compare_to_previous flags an unexplained big move backed only by
#    INFERENCE, and does NOT flag one backed by JUDGMENT
prev = {"session_id": "S-PREV", "scores": {"harm": 24}, "li": 0.5}
cur_weak = {"session_id": "S-CUR", "scores": {"harm": 91}, "li": 0.8,
            "dimension_evidentials": {"harm": {"evidential": "INFERENCE"}}}
cur_strong = {"session_id": "S-CUR2", "scores": {"harm": 91}, "li": 0.8,
              "dimension_evidentials": {"harm": {"evidential": "JUDGMENT"}}}
delta_weak = compare_to_previous(cur_weak, prev)
delta_strong = compare_to_previous(cur_strong, prev)
results.append(("unexplained_move_flagged_when_weak",
                 any(f["code"] == "DELTA_UNEXPLAINED_MOVE" for f in delta_weak["flags"])))
results.append(("explained_move_not_flagged_when_judgment", len(delta_strong["flags"]) == 0))

# 9. All prior versions' tests still pass unchanged
results.append(("v1_2_self_test_still_passes", run_v12_self_test()))

passed = sum(1 for _, ok in results if ok)
print(f"\nV1.3 SELF-TEST: {passed}/{len(results)} passed")
for name, ok in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
return passed == len(results)
```

def main():
parser = argparse.ArgumentParser(
description=(
"ACAT Document Analyzer v1.3 — grammar-native output per "
"BEHAVIORAL_GRAMMAR_V1.md. NOTE (spec §4 scope limit): extended "
"architectural-signal detection narrows the anchor-vs-qualitative "
"scoring gap only for documents using this grammar's own "
"vocabulary; it does not close that gap generally."
)
)
parser.add_argument("–input", "-i", help="Path to document text file")
parser.add_argument("–name", "-n", default="Unknown Document")
parser.add_argument("–session", "-s", help="Session ID (auto-generated if not provided)")
parser.add_argument("–output", "-o", default="outputs/")
parser.add_argument("–interactive", action="store_true")
parser.add_argument("–scores", help="JSON string of pre-computed scores")
parser.add_argument("–justification", help=(
"JSON object mapping dimension -> justification text, required "
"alongside –scores unless –i-acknowledge-no-justification is passed "
"(spec §2.2). Caps evidential at REPORTED if omitted-and-acknowledged."
))
parser.add_argument("–i-acknowledge-no-justification", action="store_true",
help="Explicitly accept REPORTED-tier capping for unjustified –scores.")
parser.add_argument("–ledger", default=DEFAULT_LEDGER_PATH,
help="Path to the score-replay ledger (spec §2.2).")
parser.add_argument("–declarant-id", help="Identity of whoever supplied the scores.")
parser.add_argument("–administrator-id", help=(
"Identity of whoever ran the tool, if different from declarant "
"(spec §2.3/§3.2 – free text, spoofable, a weak corroborating "
"signal only, NOT cryptographic proof of independence)."
))
parser.add_argument("–document-author-id", help="Identity of the document's author, for self_administered detection.")
parser.add_argument("–previous-report", help="Path to a prior report JSON, for P1<->P3 delta (spec §3.1).")
parser.add_argument("–two-stage", action="store_true",
help="Signals this run is one stage of a two-stage pair; purity classification uses declarant/administrator separation.")
parser.add_argument("–gaps", help="JSON array of pre-identified gaps")
parser.add_argument("–batch-dir", help="Score all .txt files in directory")
parser.add_argument("–density-only", action="store_true",
help="Print evidence density scores only (no interactive scoring)")
parser.add_argument("–smoke-test", action="store_true")
parser.add_argument("–self-test-v12", action="store_true",
help="Run the v1.2 code-semantic self-test")
parser.add_argument("–self-test-v13", action="store_true",
help="Run the v1.3 grammar-native self-test (includes v1.2 + v1.1)")
args = parser.parse_args()

```
if args.self_test_v13:
    sys.exit(0 if run_v13_self_test() else 1)

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
structural_ratio = compute_structural_vs_rhetorical_ratio(text, ed) if text else {}

if args.density_only:
    print(json.dumps(ed, indent=2))
    sys.exit(0)

previous_report = None
if args.previous_report:
    try:
        previous_report = json.loads(load_document(args.previous_report))
    except (SpecLoadFailed, json.JSONDecodeError) as e:
        print(f"PREVIOUS_REPORT_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

dimension_input_modes = None
justifications = None
input_mode = "unknown"

if args.scores:
    try:
        scores = json.loads(args.scores)
    except json.JSONDecodeError as e:
        print(f"SCORE_PARSE_FAILED: {e}", file=sys.stderr)
        sys.exit(2)
    gaps = json.loads(args.gaps) if args.gaps else []
    input_mode = "batch_scores"
    if args.justification:
        try:
            justifications = json.loads(args.justification)
        except json.JSONDecodeError as e:
            print(f"JUSTIFICATION_PARSE_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    elif not args.i_acknowledge_no_justification:
        print(
            "WARNING: --scores supplied without --justification. Dimensions "
            "will be tagged UNKNOWN and flagged MISSING_JUSTIFICATION. "
            "Pass --i-acknowledge-no-justification to proceed anyway "
            "(capped at REPORTED), or supply --justification (spec §2.2).",
            file=sys.stderr,
        )
elif args.interactive or args.input:
    scores, gaps, dimension_input_modes = interactive_scoring(args.name, text, ed)
    input_mode = "interactive"
else:
    parser.print_help()
    sys.exit(1)

arch = detect_architectural_determination(text, scores)
him = analyze_him_pattern(scores)
gap_corr = analyze_gap_score_correspondence(gaps, scores)
output = aggregate_scores(
    args.name, scores, gaps, arch, him, gap_corr, ed, session_id,
    input_mode=input_mode, dimension_input_modes=dimension_input_modes,
    justifications=justifications, document_text=text,
    ledger_path=args.ledger,
    acknowledge_no_justification=args.i_acknowledge_no_justification,
    declarant_id=args.declarant_id, administrator_id=args.administrator_id,
    document_author_id=args.document_author_id,
    previous_report=previous_report, structural_ratio=structural_ratio,
)

report_path = write_report(output, args.output)
print_summary(output)
print(f"Report written: {report_path}")
sys.exit(0)
```

if **name** == "**main**":
main()