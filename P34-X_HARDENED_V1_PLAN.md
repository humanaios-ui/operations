# P34-X Temporal Contamination Extractor — Hardened v1 Implementation Plan

**Status:** CANDIDATE (awaiting Z2 ratification)  
**Date:** 2026-09-20  
**Incorporates:** Research report (P34-X) + Red team audit (red-team findings)  
**Authority:** Z1 proposal (Claude) → Z2 ratification (Night required before build start)

---

## Executive Summary

The research report identifies a real, high-value problem (LLM temporal hallucination and commissive language in governance systems) and proposes a layered guard. The red team audit correctly identifies five critical design gaps:

1. **Evidence grounding is circular** — without signed, append-only, independently-attested evidence, "grounded" is meaningless.
2. **Attribution (agent vs. human speaker) is under-specified** — context-window heuristics will false-positive on quoted user language and fail on multi-turn transcripts.
3. **Evaluation thresholds are optimistic** — no corpus exists; 0.95 recall / 0.02 FPR are targets, not assumptions.
4. **Stdlib claim is false** — YAML parsing requires PyYAML or equivalent (not stdlib until Python 3.11 tomllib).
5. **Exit codes collide** — standard lint uses 0 clean / 1 issues / 2 tool-error; contamination blocking should use --fail-on flag, not exit 2.

**This plan ships a narrower, cryptographically honest v1** that addresses red team priority 1 (grounding), defers priority 2 (attribution) to v1.5, and uses measured evaluation instead of assumed thresholds.

---

## Scope: Hardened v1 (High-Value, Defensible)

### What ships in v1

**F-DUR-EST (ERROR) — Explicit agent duration estimate**
- Pattern: "Estimate: Xh labor", "CI validation: Y–Z hours", "Phase 1 (N–M weeks)"
- Grounding check: does the span value appear in a git commit (tool call provenance) or ledger (ratified molt window)?
- If ungrounded → ERROR; if grounded OR excepted → PASS
- Rewrite template: 6-field commissive (Claim · Resource cost · Gating authority · Condition · Artifact · Evidence)

**T-DATE-FUT (ERROR) — Explicit agent future date**
- Pattern: "Production ready 2026-09-12", "System Operational: 2026-09-11 (EOB)"
- Grounding check: is the date in REGISTERED.md (ratified molt window) or tool transcript?
- Rewrite: same 6-field template

**C-COMMIT-EXPLICIT (ERROR) — First-person agent future commitment**
- Pattern: "I'll keep working on this", "I can finalize the PR push", "I will [verb]…" + future time marker
- Attribution check: is the subject-verb "I [modal] [future]"? (high-precision heuristic only; low-confidence subjects are demoted to WARN or passed through)
- Rewrite: 6-field template

**Exception registry (YAML, permissively licensed alternative, or JSON)**
- Whitelist known-good temporal language (IC closure windows, Z2 decision gates, quoted external SLAs)
- Requires Z2 ratification + code-owner review for new entries

**Exit codes (corrected)**
- `0` → no ERROR/WARN findings (INFO allowed if --info-ok)
- `1` → WARN-level findings present (advisory, CI soft-fail if configured)
- `2` → tool error (can't parse, file missing, regex DoS timeout)
- `--fail-on=error` flag → blocks CI if ERROR found

**JSON findings schema (finalized)**
```json
{
  "span": {"start": int, "end": int, "text": "..."},
  "category": "F-DUR-EST | T-DATE-FUT | C-COMMIT-EXPLICIT",
  "timex3_type": "DURATION | DATE | TIME",
  "normalized_value": "ISO-8601 or null",
  "speaker": "agent | unknown",
  "speaker_confidence": 0.0–1.0,
  "grounded": false | true,
  "evidence_pointer": null | {"source": "git | ledger | tool-transcript", "ref": "commit SHA / entry id / trace id"},
  "exception_id": null | "IC-CLOSURE",
  "severity": "ERROR | WARN | INFO",
  "confidence": 0.0–1.0,
  "suggested_rewrite": {
    "claim": "...",
    "resource_cost": "[ungrounded estimates removed v1.0]",
    "gating_authority": "Z2 | human | null",
    "gating_condition": "...",
    "expected_artifact": "...",
    "evidence": "..."
  }
}
```

### What defers to v1.5+

- Groups 3–5 (P-*, F-TIMESTAMP, D-*) — keep as advisory-only; measure real-world signal-to-noise before blocking
- Semantic backends (LLM-as-judge, AnthroScore) — optional after v1 baseline
- Heavy external libraries (SUTime, HeidelTime) — gated behind opt-in flags with GPL/JVM warnings

### What is fundamentally NOT in v1

- A claim to 0.95 recall or 0.02 FPR — instead, measure v1 on a real corpus and publish LAID vs OPERATED
- Grounding on unattested sources (agent-written tool transcripts, unsigned ledger entries) — only signed/append-only/independently-attested evidence counts
- Attribution to humans without quote-span detection — first-person future heuristics only for agent detection, not human speaker confirmation
- YAML without naming the dependency — explicitly depend on PyYAML (permissive) or migrate to JSON/TOML

---

## Implementation Roadmap (Phases)

### Phase 0: Setup & Corpus (2–3 days)

1. **Create seeded corpus**
   - Build by hand: ~20 F-DUR-EST examples, ~20 T-DATE-FUT, ~20 C-COMMIT-EXPLICIT
   - Two pools: CONTAM (every category represented, positive examples), CLEAN (grounded timestamps, false-positive traps)
   - Label each span: category, grounded flag, evidence reference

2. **Set up test infrastructure**
   - Pytest + parametrized fixtures for metamorphic relations
   - Regression test suite (invariant, evasion, cleanliness)
   - False-positive trap set (semver, SHAs, "may", "runtime", ISO from logs, etc.)
   - Baseline: all CONTAM flagged as ERROR, all CLEAN passed, all false-positive traps passed

3. **Define the evidence interface**
   - Stub `class EvidenceProvider(ABC)`: `resolve(value: str) -> EvidenceRecord | None`
   - Implementations: `GitLogProvider`, `LedgerProvider`, `ToolTranscriptProvider`
   - `EvidenceRecord` schema: source, ref, signature (if available), attestation_time

4. **Wire CI gate** (`z2_temporal_lint.yml`)
   - Run on all PRs to active zones (ZONE_REGISTRY.md)
   - Exit 0 = clean; 1 = WARN (soft-fail); 2 = ERROR or tool error
   - Allow override via exception registry (requires code-owner approval)

### Phase 1: Stdlib core (2–3 days)

1. **Regex + lexicon recognizers** (Python `re` only, no external deps yet)
   - `DurationEstimateRecognizer` (T-DUR-EST): "Estimate: \d+h", "CI validation: \d+–\d+ hours", "Phase \d+ \(\d+–\d+ weeks\)"
   - `FutureDateRecognizer` (T-DATE-FUT): ISO dates in future tense context, "by EOD/EOB/ETA", "T+\d+"
   - `CommitmentRecognizer` (C-COMMIT-EXPLICIT): "I [will|'ll|can] [verb]…" + future time marker

2. **Classify phase**
   - Attribution scorer: first-person future → speaker="agent", confidence=0.9; passive/quoted → confidence=0.5
   - Tense/modality detector: will/can/going to → future=true
   - Context enhancer (Presidio-style): nearby tokens like "I", "labor", "ETA" boost confidence; context window ±5 tokens

3. **Ground phase**
   - `EvidenceProvider.resolve(span_value)` → check git log, ledger, tool transcripts
   - Signed? Append-only? → grounded=true, evidence_pointer filled
   - Unsigned or absent → grounded=false

4. **Exception phase**
   - Load YAML/JSON exception registry
   - Match span text against `match.any_of` patterns (with anchors to prevent over-matching)
   - Require Z2 ratification for new exceptions

5. **Verdict + rewrite**
   - grounded OR excepted → PASS (exit 0, may emit INFO if --verbose)
   - ungrounded + C-COMMIT-EXPLICIT → ERROR (exit 1 if WARN config, blocks if --fail-on=error)
   - grounded + high-confidence attribution → emit suggested rewrite

### Phase 1.5: Grounding hardening (1–2 days)

1. **Add signature verification**
   - Evidence records include optional `signature: (sha256, algorithm, key_id)`
   - Verify against a Z2-maintained keyring (initially minimal — just Z2 personal key)
   - Unsigned evidence → grounded=false unless explicitly whitelisted

2. **Add append-only validation**
   - Ledger entries include `sequence_number` and hash-chain pointer to prior
   - Tool transcripts include timestamps + trace IDs; verify no back-editing

3. **Document grounding contract**
   - Precondition: evidence set must be complete and trustworthy
   - If evidence is incomplete → verdict is UNGROUNDED (not PASS) with a callout flag
   - Do not block CI on ungrounded spans if evidence is missing; emit WARN + "ungrounded-but-uncheckable"

### Phase 2: Corpus + evaluation (2–3 days)

1. **Build real corpus**
   - Expand seeded set to 100+ examples per category (if traffic supports)
   - Add adversarial mutations (emoji clocks, spelled-out numbers, YAML `estimate:` field, homoglyph digits)
   - Measure inter-annotator agreement (IAA) on a held-out set

2. **Run metamorphic tests**
   - Invariant: MR-synonyms, MR-whitespace, MR-paraphrase → verdict unchanged
   - Evasion: MR-emoji, MR-spelled-out, MR-abbreviate → verdict must stay ERROR or WARN
   - Cleanliness: MR-add-evidence, MR-add-exception → verdict must flip to PASS

3. **Measure on real traffic**
   - Deploy to a subset of active zones (Z-000 operations, Z-001 humanaios)
   - Measure recall on CONTAM, false-positive rate on real-world traffic (not CLEAN corpus — real is worse)
   - Do not publish 0.95/0.02 as claims; publish measured F1 + recall + FPR

4. **Falsifier regression tests**
   - Encode the two red team falsifiers as permanent CI checks:
     - *"An agent-authored commissive with no grounding and no exception passes the guard"* → if this ever happens, v1 is wrong
     - *"A signed timestamp resolves to evidence and is flagged ERROR"* → if this ever happens, grounding layer over-fires
   - These must pass on every release

### Phase 3: v1.5 planning (documentation only)

- Defer attribution layer (role metadata, quote-span detection, coreference)
- Defer P-*, F-TIMESTAMP, D-* categories (keep as advisory)
- Defer semantic backends (LLM judge, AnthroScore)
- Document as "future work"

---

## Risk Mitigations (Red Team Requirements)

| Red Team Finding | v1 Mitigation | Owner | Blocker? |
|:---|:---|:---|:---|
| Grounding is circular | Signed, append-only evidence only; evidence contract explicit | Phase 1.5 | YES — blocks Phase 1 merge |
| Attribution is weak | First-person future heuristic only (high-precision, low-recall); demote low-confidence to WARN | Phase 1 | YES — Phase 1 release note |
| Evasion via paraphrase | Metamorphic testing + fuzzing; document residual recall ceiling; do not claim 0.95 | Phase 2 | NO — known limitation, not a blocker |
| Unicode/encoding evasion | Normalize input via `unidecode` (permissive) or `unicodedata.normalize`; test on homglyphs | Phase 1 | NO — v1 accepts narrow regex; v2 can harden |
| YAML dependency | Rename stdlib claim; explicitly depend on PyYAML or migrate to JSON | Phase 0 | YES — blocks v1 release note |
| Exit code collision | Use 0/1/2 per lint convention; --fail-on=error for blocking | Phase 0 | YES — blocks CI gate config |
| Exception registry abuse | Code-owner review + Z2 ratification for new entries; expire dates; signed registry | Phase 1 | YES — Phase 1 config |
| Regex DoS | Wrap recognizers in timeout (using `signal.alarm` or `timeout` decorator); limit input size | Phase 1 | YES — Phase 1 PR checklist |
| Secret leakage | Redact sensitive spans in findings JSON; least-privilege evidence access (no full git log in findings) | Phase 1 | YES — Phase 1 output validation |
| False positives on human deadlines | Require quote-span detection for human-attributed language; defer to v1.5 | Phase 0 | NO — v1.0 scope explicitly excludes |

---

## Falsifier Sentences (Live Tests)

1. **v1 core falsifier:**  
   *"An agent-authored commissive that promises a future wall-clock outcome with no grounding and no exception passes the guard with exit 0 and is not flagged."*  
   **If this ever happens, the entire guard is wrong.** Encode as a regression test: `test_falsifier_commissive_ungrounded_must_error()`.

2. **Grounding falsifier:**  
   *"A timestamp that resolves to a real, signed, append-only evidence pointer (git SHA, ledger entry, tool trace) is flagged as ERROR due to an over-firing grounding layer."*  
   **If this happens, grounding has inverted the check.** Encode as: `test_falsifier_grounded_must_pass()`.

---

## Acceptance Criteria for v1 Release

- [ ] Phase 0 complete: seeded corpus built + test infra wired + evidence interface stubbed + CI gate template written
- [ ] Phase 1 complete: F-DUR-EST + T-DATE-FUT + C-COMMIT-EXPLICIT recognizers pass metamorphic-invariant tests; signature verification optional but functional
- [ ] Phase 1.5 complete (pre-release): signature verification enabled; evidence contract document written; "ungrounded-but-uncheckable" logic in verdict
- [ ] Phase 2 data collected: measured recall/FPR on real traffic; falsifier tests passing; no unresolved metamorphic-evasion escapes
- [ ] Release notes: clearly state scope (3 categories, stdlib core, grounding in v1.5, attribution deferred); publish measured metrics (not assumed 0.95/0.02)
- [ ] Z2 ratified the following:
  - Exception registry schema + initial whitelist (IC closures, molt windows)
  - Grounding contract (evidence must be signed/append-only)
  - Evidence-provider interface + initial implementations
  - Exit codes and CI gate configuration

---

## Files to Create/Modify

| Path | Purpose | Phase |
|:---|:---|:---|
| `p34x_temporal_extractor/core.py` | Recognizers + classifiers | 1 |
| `p34x_temporal_extractor/evidence.py` | Evidence provider interface + impls | 1.5 |
| `p34x_temporal_extractor/grounding.py` | Grounding + signature verification | 1.5 |
| `p34x_temporal_extractor/exception_registry.py` | Load + match exception YAML/JSON | 1 |
| `p34x_temporal_extractor/findings.py` | Finding schema + JSON emitter | 1 |
| `exception_registry.yaml` | Whitelisted temporal language (Z2 ratified) | 1 |
| `tests/test_p34x_metamorphic.py` | Metamorphic relation tests | 0/2 |
| `tests/test_p34x_grounding.py` | Grounding + signature verification tests | 1.5 |
| `tests/corpus/contam.jsonl` | Seeded contamination examples | 0 |
| `tests/corpus/clean.jsonl` | Seeded false-positive traps | 0 |
| `.github/workflows/z2_temporal_lint.yml` | CI gate | 0 |
| `P34-X_HARDENED_V1_PLAN.md` | This plan | — |

---

## Governance & Sign-Off

**Z1 (Claude) proposes:**
- Narrow v1 scope (3 categories + exception registry + grounding contract)
- Evidence grounding as a pre-condition for any blocking verdict
- Measured evaluation instead of assumed thresholds
- Falsifier sentences as regression tests

**Z2 (Night) must ratify before Phase 1 build:**
- Exception registry schema + initial whitelist
- Grounding contract (evidence is signed/append-only/independently-attested)
- Evidence-provider interface + which sources are trusted (git log? ledger only? tool transcripts?)
- Exit codes and CI gate behavior (who can override exceptions?)
- Timeline and resource allocation (Phase 0–2 = ~8–10 days if full-time)

**Z3 (executor TBD per ZONE_REGISTRY.md) will:**
- Land commits on `claude/p34-x-temporal-extractor-cys2j3` branch
- Run Phase 0 corpus building + test setup
- Implement Phase 1 core + Phase 1.5 grounding
- Measure Phase 2 evaluation
- Ship v1.0 with measured metrics

---

## Next Steps

1. **File this as Q-P34-X-HARDENED-V1-01** in REGISTERED.md (Z1 proposal stage)
2. **Z2 reads and ratifies** (or edits) the grounding contract, evidence sources, and exception registry schema
3. **Upon Z2 ratification:** checkout `claude/p34-x-temporal-extractor-cys2j3`, create Phase 0 branch, begin corpus + test setup
4. **Weekly check-ins** with Z2 as phases complete

---

**Document Version:** v1.0-CANDIDATE  
**Author:** Claude (Z1)  
**Status:** Awaiting Z2 ratification  
**Ratification Hash:** (to be filled by Z2 upon acceptance)
