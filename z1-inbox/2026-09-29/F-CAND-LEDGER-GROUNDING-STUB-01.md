---
id: "F-CAND-LEDGER-GROUNDING-STUB-S092926"
name: "p34x LedgerProvider is a permanent no-op stub: every future date classifies ERROR regardless of ratification"
status: CANDIDATE
class: F
date_registered: "2026-09-29"
date_origin: "2026-09-29"
session_registered: "S-092926-p34x-backlog"
tags: ["p34x", "temporal-extractor", "evidence-grounding", "q-temporal-dissolution-01", "false-positive"]
related: ["Q-TEMPORAL-DISSOLUTION-01"]
superseded_by: null
source_issue: null
---

# Candidate Block: F-CAND-LEDGER-GROUNDING-STUB-01 — LedgerProvider never grounds, so ratified dates still classify as ERROR

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-29
**Status:** AWAITING Z2 RATIFICATION

## Claim

- **claim:** `p34x_temporal_extractor/evidence.py`'s `LedgerProvider` (lines 77-106) is a permanent no-op. `_load_molt_windows()` hard-codes `self._molt_windows = {}` and never reads anything; `resolve()` unconditionally `return None`. Both carry an explicit in-code comment marking this as deliberate: *"Phase 0: Don't provide evidence until ledger reading is implemented. This prevents false grounding from hard-coded test data."* `GitLogProvider.resolve()` (line 71) and `ToolTranscriptProvider.resolve()` (line 122) are the same shape — stubs that always return `None`.
- **consequence:** `TemporalExtractor.extract()` (`core.py:236-263`) calls `self.evidence.resolve(...)`; since it always returns `None`, `finding.grounded` can never become `True` for any of these three backends. The classification fallthrough at `core.py:260-261` (`elif finding.category in [F_DUR_EST, T_DATE_FUT]: ERROR`) then fires unconditionally for every future-date or duration-estimate finding — there is no code path today by which a genuinely ratified molt window (e.g. `molt_id=f7a49f667c09f1f6`, cited in `tests/corpus/clean.jsonl` line 2's `evidence_ref`) can ever be recognized as grounded and downgraded to INFO.
- **evidence_tier:** VERIFIED-LIVE — read `p34x_temporal_extractor/evidence.py` and `core.py` directly this session; reproduced the failure with `python3 -m pytest tests/test_p34x_metamorphic.py::TestCorpusBaseline::test_corpus_clean_examples -v`, which fails on exactly this: `"resolves at 2026-09-23"` (a clean-corpus example whose `evidence_ref` claims ledger grounding) is flagged ERROR. `git log` shows the module has a single commit (`e03053e`) since creation — this is the shipped state, not a regression.
- **discovered via:** a systematic pass installing `pytest` (previously silently absent, so `unittest discover` treated the whole test module as an import error rather than surfacing its 3 real failures) to actually run `tests/test_p34x_metamorphic.py`. Two of the three failures were a separate, unrelated, already-fixed bug (`CommitmentRecognizer`'s dead `'ll`-contraction regex branch, PR #589); this is the third, independent one.
- **why this matters:** `p34x_temporal_extractor` exists to gate `Q-TEMPORAL-DISSOLUTION-01` — distinguishing `REGULATORY_EXTERNAL`/ratified-molt-window dates from `INVALID_INTERNAL_DEADLINE` ones. With grounding permanently unreachable, the extractor cannot currently tell the two apart at all; it can only ever over-flag (every future date is ERROR) or, if someone "fixes" this by relaxing the fallback classification instead of implementing real grounding, under-flag (false negatives on genuinely invalid deadlines). The corpus fixture (`clean.jsonl` line 2) already encodes the *intended* behavior — it was written assuming Phase 1 grounding exists — so the test suite has been red on this specific case since the module's first commit, with nothing surfacing it because `pytest` wasn't installed to run it.

## Falsifier

This finding is falsified once `LedgerProvider._load_molt_windows()`/`resolve()` are implemented against a real source (REGISTERED.md molt entries and/or `NF_LEDGER.jsonl`) and `tests/test_p34x_metamorphic.py::TestCorpusBaseline::test_corpus_clean_examples` passes without also reintroducing a false negative on any `contam.jsonl` entry (i.e., the fix must ground only genuinely ratified values, not relax the ERROR fallback generally).

## Proposed correction / prevention (Z2 to accept, edit, or reject)

1. Implement `LedgerProvider._load_molt_windows()` to parse `REGISTERED.md` for ratified molt window entries (the module's own docstring already names this as the intended source: *"Checks REGISTERED.md for molt windows and IC closure entries"*), keyed by the date/value they ratify.
2. Implement `resolve()` to match `finding.normalized_value` (or `finding.text`) against the loaded windows and return a real `EvidenceRecord(source="ledger", ref=<molt_id or IC id>, value=...)` on a hit — not a hard-coded/test-only shortcut, per the stub's own stated concern about false grounding from fixture data.
3. This is real parsing work, not a quick patch — explicitly not attempted in the same pass that found it (no code change accompanies this finding). `GitLogProvider` and `ToolTranscriptProvider` are the same shape and likely need the same treatment eventually, but are out of scope for this finding, which is limited to the one corpus test currently red.
4. Until implemented, `p34x_temporal_extractor` should be understood as detect-only-in-the-over-flag-direction: safe to use as a "something time-related was said" signal, not yet safe as a "this is/isn't a ratified exception" decision — worth naming explicitly wherever the module's output feeds `Q-TEMPORAL-DISSOLUTION-01` decisions.

## Z2 Decision Gate

- [ ] ACCEPT — register as F-CAND, assign F-number, proceed with implementation
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

**Awaiting Z2 ratification by:** 2026-10-01 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
