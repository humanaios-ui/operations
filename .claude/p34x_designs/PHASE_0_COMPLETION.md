# P34-X Phase 0: Completion Summary

**Date:** 2026-09-20  
**Branch:** `claude/p34-x-temporal-extractor-cys2j3`  
**PR:** #428 (draft, awaiting Z2 ratification)  
**Status:** ✅ Phase 0 COMPLETE

---

## Deliverables

### 1. Hardened v1 Design Plan (`P34-X_HARDENED_V1_PLAN.md`)

A complete, red-team-hardened implementation plan that:
- Narrows v1 scope to 3 high-value categories (F-DUR-EST, T-DATE-FUT, C-COMMIT-EXPLICIT)
- Addresses all 5 red team critical findings (grounding, attribution, evaluation rigor, dependencies, exit codes)
- Defines 3 phased rollout: Phase 0 (setup), Phase 1 (core), Phase 1.5 (grounding + signatures), Phase 2 (evaluation)
- Lists acceptance criteria and falsifier regression tests
- Documents blocking z2 decisions (grounding contract, evidence sources, exception governance)

**Key red-team incorporations:**
- Grounding must use signed/append-only/independently-attested evidence (not optional)
- No false claims of 0.95 recall / 0.02 FPR; measure on real corpus Phase 2
- Exit codes corrected: 0 clean / 1 findings / 2 tool error (lint convention)
- Explicit dependency on PyYAML (not stdlib claim)

### 2. Seeded Corpus (`tests/corpus/`)

**CONTAM pool (20 positive examples):**
- F-DUR-EST: 5 examples (labor estimates, CI validation time, phase durations)
- T-DATE-FUT: 3 examples (future production dates, resolves dates)
- C-COMMIT-EXPLICIT: 9 examples (I'll, background work, scheduling claims)
- 1 grounded example (molt window resolves date)

**CLEAN pool (20 false-positive traps):**
- Grounded timestamps (molt window, git SHA, ledger)
- Version strings (v2.3.1), git SHAs, line numbers, timeout parameters
- Modal verbs (may), technical identifiers (runtime, real-time, window)
- Quoted deadlines, human-attributed language, historical records

All labeled with category, grounded flag, and evidence reference for validation.

### 3. Core Python Module (`p34x_temporal_extractor/`)

**findings.py** — JSON schema for findings
- `TemporalFinding` dataclass with span, category, TIMEX3 type, grounding, evidence pointer, suggested rewrite
- `ExtractionResult` with exit_code() method (0/1/2 convention)
- `Severity` enum (ERROR/WARN/INFO)

**evidence.py** — Grounding interface (Phase 0 scaffold, Phase 1.5 implementation)
- `EvidenceProvider` abstract base class
- `GitLogProvider`, `LedgerProvider`, `ToolTranscriptProvider` stubs
- `CompositeEvidenceProvider` for trying multiple backends
- `EvidenceRecord` schema with optional signature field

**core.py** — Recognizers and main extractor
- `DurationEstimateRecognizer`: patterns for labor/effort estimates
- `FutureDateRecognizer`: patterns for future dates (ISO, EOD/EOB, T+N)
- `CommitmentRecognizer`: first-person future patterns + background work patterns
- `TemporalExtractor`: orchestrates recognizers, grounding, exceptions, verdicts
- `ExtractorConfig`: configurable evidence providers, exception registry, thresholds

**exception_registry.yaml** — Whitelisted temporal language (governance layer)
- IC-CLOSURE, MOLT-WINDOW, SESSION-RITUAL, EXTERNAL-SLA, HUMAN-DEADLINE, CI-GATE-TIMEOUT, RATIFIED-CONSTANT
- Each entry specifies: applies_to categories, match patterns, Z2 ratification status
- Governance rules: requires code-owner review + dual control, expiry policy

### 4. Metamorphic Relation Tests (`tests/test_p34x_metamorphic.py`)

**TestMetamorphicInvariant:** verdict unchanged under semantic-preserving mutations
- Synonym replacement (Estimate → Estimated → Estimated labor)
- Whitespace changes
- Case insensitivity

**TestMetamorphicEvasion:** verdict MUST stay ERROR under known evasion attempts
- Spelled-out numbers (eight hours)
- Abbreviations (EOD, ETA, T+)
- Unicode homoglyphs (full-width digits)
- Emoji clocks (⏳)

**TestMetamorphicCleanliness:** verdict flips to PASS when grounding/exception added
- Exception suppresses ERROR
- Grounding timestamps marked as safe

**TestFalsePositiveTrapSet:** ensure CLEAN examples pass
- Semver, git SHA, line numbers, modal verbs, month names, technical identifiers
- ISO timestamps with log provenance
- 11 false-positive traps (v1 baseline)

**TestFalsifierSentences:** permanent regression tests
1. Ungrounded commissive must flag ERROR (if this fails, guard is broken)
2. Grounded timestamp must not flag ERROR (if this fails, grounding is inverted)

---

## Status and Blockers

### Phase 0 ✅ Complete

- [x] Design plan with red team hardening
- [x] Seeded corpus (CONTAM + CLEAN)
- [x] Core module scaffold (findings, evidence interface, recognizers)
- [x] Exception registry with governance markers
- [x] Metamorphic test framework with falsifiers
- [x] PR #428 (draft)

### Phase 1 ⏳ Blocked (awaiting Z2 ratification)

**Z2 must decide:**
1. Grounding contract: what counts as "signed/append-only" evidence? (git tags? cryptographic signatures? timestamp servers?)
2. Evidence sources: which sources are trusted? (all of: git log, ledger, tool-transcript, quoted, human-attributed? subset?)
3. Exception registry ratification: which exceptions ship v1? (IC-CLOSURE, MOLT-WINDOW, SESSION-RITUAL as minimum?)
4. CI gate configuration: who can override exceptions? (code-owner only? Z2 only?)

**Then Phase 1 can start:**
- Implement GitLogProvider + LedgerProvider (currently stubs)
- Integrate recognizers against corpus (currently scaffolded)
- Add signature verification layer (Phase 1.5)
- Run metamorphic tests to completion (currently have TODOs)

### Phase 2 📊 Planned

- Expand corpus on real agent output
- Measure recall/FPR on production traffic
- Publish measured metrics (not assumed 0.95/0.02)
- Continuous fuzzing + red team testing

---

## Risk Mitigation Summary

| Red Team Finding | v1 Mitigation | Status |
|:---|:---|:---|
| Grounding is circular | Signed/append-only evidence only; explicit contract | ✅ Designed |
| Attribution too weak | High-precision heuristic (first-person future); low-recall OK v1 | ✅ Designed |
| Evasion via paraphrase | Metamorphic testing + doc residual ceiling | ✅ Designed |
| Unicode/encoding evasion | Known limitation v1; Phase 2 enhancement | ✅ Documented |
| YAML dependency | Explicit PyYAML + note (not stdlib) | ✅ Corrected |
| Exit code collision | 0/1/2 per lint convention (not 0/1/2 contamination) | ✅ Corrected |
| Exception registry abuse | Code-owner review + Z2 ratification + expiry | ✅ Designed |
| Regex DoS | TODO Phase 1: timeout wrapper | ⏳ Deferred |
| Secret leakage | TODO Phase 1: redaction layer | ⏳ Deferred |

---

## Next Steps

1. **Z2 Ratification** (blocking Phase 1)
   - Read P34-X_HARDENED_V1_PLAN.md
   - Decide: grounding contract, evidence sources, exceptions, CI gate rules
   - Sign: Exception registry + grounding interface

2. **Phase 1 Implementation** (once Z2 approves)
   - Implement/test GitLogProvider + LedgerProvider
   - Complete recognizer pattern tuning on corpus
   - Add signature verification (Phase 1.5)
   - Run full metamorphic suite

3. **Phase 2 Measurement** (after Phase 1 tests pass)
   - Deploy to Z-000 + Z-001 (operations, humanaios repos)
   - Measure real traffic (recall, FPR, signal-to-noise)
   - Publish measured metrics in release notes

---

## Files Modified/Created

```
p34x_temporal_extractor/
├── __init__.py
├── core.py              (recognizers + extractor)
├── evidence.py          (evidence interface)
├── findings.py          (JSON schema)

tests/
├── corpus/
│   ├── contam.jsonl     (20 contamination examples)
│   └── clean.jsonl      (20 false-positive traps)
├── test_p34x_metamorphic.py

.claude/p34x_designs/
└── PHASE_0_COMPLETION.md (this file)

P34-X_HARDENED_V1_PLAN.md (design + rollout plan)
exception_registry.yaml (whitelisted patterns)
```

---

## Falsifier Sentences (Live Tests)

These are permanent regression tests; if either fails, the guard is wrong.

1. **Core falsifier:** An agent-authored commissive that promises a future wall-clock outcome with no grounding and no exception passes the guard with exit 0 and is not flagged.

2. **Grounding falsifier:** A timestamp that resolves to a real, signed, append-only evidence pointer (git SHA, ledger entry, tool trace) is flagged as ERROR due to an over-firing grounding layer.

Test: `test_falsifier_1_ungrounded_commissive_must_error()`, `test_falsifier_2_grounded_timestamp_must_pass()`

---

**Status:** Awaiting Z2 ratification. PR #428 ready for review.  
**Session:** https://claude.ai/code/session_011CoBszvoK5ouYY5NPCz9fW
