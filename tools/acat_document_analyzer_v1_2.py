# ACAT_DOCUMENT_ANALYZER_V1_3_SPEC.md

**Status:** Z2 Ratified 
**Produced:** S-070926 (Z1 draft seat, Claude)
**Requires:** Zone 2 ratification per P21 before implementation begins; each theme may be ratified and built independently — this is not an all-or-nothing package.
**Governs:** `acat_document_analyzer.py`, current canonical version v1.2.0 (live-verified this session at `humanaios-ui/operations/tools/acat_document_analyzer_v1_2.py`)
**Depends on:** `BEHAVIORAL_GRAMMAR_V1.md` (Z1 draft, ratified in part S-070926) — this spec’s central claim is that the analyzer tool should itself emit grammatically well-formed claims per that document’s G-0 through G-9. Where this spec’s own design decisions were checked against those rules and found wanting, the correction is shown explicitly rather than silently folded in — see §2.1.
**Epistemic status of this document:** JUDGMENT formalized into a proposal. Design decisions below are engineering recommendations, not verified facts about what will work; several are flagged as needing Z2 input on genuine tradeoffs rather than being presented as settled.

-----

## 0. What this is

Three tightly-scoped themes for v1.3, each addressing a gap surfaced empirically this session while running P30 passes on `BEHAVIORAL_GRAMMAR_V1.md`: (1) the analyzer’s own output doesn’t obey the grammar it’s meant to help enforce, (2) it can’t natively compare a P1 and P3 pass, and (3) its architectural-signal detection doesn’t yet recognize the grammar’s own vocabulary. Priority order: Theme 1 > Theme 2 > Theme 3, per the working session — Theme 1 closes an active loophole; Themes 2 and 3 are enhancements.

-----

## 1. Scope discipline

This spec deliberately does not: rewrite the 12-dimension rubric, change the LI formula, touch `corpus_delta_analyzer` or `drift_catalog_validator` internals (Theme 2 depends on the first, references the second, modifies neither), or attempt to close the anchor-vs-qualitative scoring gap observed this session (anchor pass LI 0.5567 vs. two independent qualitative reads at 0.865–0.89 on the same document). That gap is a semantic-understanding limit of keyword-density scoring; §5 states explicitly that no theme here resolves it.

-----

## 2. Theme 1 — Grammar-native output (highest priority)

**Goal:** every report the analyzer emits must satisfy G-0 (marks its evidential source and its agent of authority) and must not be capable of self-promoting its own evidential tier (the tool-level analogue of G-4).

### 2.1 Evidential taxonomy for the tool — corrected from initial proposal

The original working proposal (”`--interactive` → VERIFIED, human is authority”) is rejected on rigor grounds: per G-2’s own definition, VERIFIED requires “a live fetch, executed command, diff, or direct read” — a dimension score is an interpretive call, which G-2’s table separately defines as JUDGMENT. Granting VERIFIED to a human’s 0–100 judgment would be exactly the INFERENCE/JUDGMENT-dressed-as-VERIFIED pattern G-2 names as the canonical violation. Corrected taxonomy:

|Layer                                                                                             |Example field                                                                                                             |Evidential                                                           |Rationale                                                                                                                                                     |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Raw mechanical counts                                                                             |`high_signal_hits`, `low_signal_hits`, `python_blocks_found`                                                              |`VERIFIED`                                                           |Literally an executed command’s output; a second party re-running the tool against the same text gets the same count.                                         |
|Anchor score (count → 0–100 mapping)                                                              |`anchor_score_suggestion`                                                                                                 |`INFERENCE`                                                          |A reasoned mapping from counts to a score via a fixed formula — statable basis, could be wrong (empirically: often is, badly, on this document type — see §5).|
|Human or AI interpretive dimension score                                                          |`scores.{dim}` when actively supplied (typed override in `--interactive`, or `--scores` with fresh justification, see 2.2)|`JUDGMENT`                                                           |An interpretive call, per G-2’s own definition — not a fact-claim regardless of who makes it or how confidently.                                              |
|A dimension score accepted without override (blank Enter in `--interactive`, or density-only mode)|same field                                                                                                                |`INFERENCE` (inherits the anchor’s tier — no new reasoning was added)|Accepting a suggestion isn’t independent judgment; G-3’s “repetition doesn’t upgrade tier” logic applies at the tool level too.                               |
|`--scores` supplied with no justification, or justification that fails the replay check (§2.2)    |same field                                                                                                                |`REPORTED`                                                           |Numbers relayed without this session having independently produced them — the exact failure mode observed this session with the Grok-FULL resubmission.       |

**Top-level report evidential = the weakest tier among its constituent dimension evidentials.** [JUDGMENT|Z1] This is a deliberate design choice, not a technical necessity — a report is only as strong as its weakest claim, mirroring G-7’s rule that a P1/P3 pair inherits the lower tier of its two members. A report mixing 10 JUDGMENT dimensions and 2 accepted-anchor INFERENCE dimensions is tagged INFERENCE overall, not “mostly VERIFIED.” Alternative considered and rejected: per-dimension tagging only, no top-level rollup — rejected because B.6 receipt reconciliation and B.0 blocks need a single glanceable tag, and per-dimension-only would require a human to read all 12 to know if the report is corpus-eligible.

*Enforcement surface:* `aggregate_scores()` — add `evidential` field per dimension (computed from input path, not caller-supplied) and `report_evidential` at top level (computed as `min()` over a defined tier ordering `VERIFIED > JUDGMENT > INFERENCE > REPORTED > UNKNOWN`). No CLI flag exists to directly set either field — this closes the self-promotion path at the schema level, not just the convention level.

### 2.2 Anti-replay mechanism for `--scores`

**Problem this closes, concretely:** this session, a score set produced once (tagged INFERENCE, flagged as contaminated) reappeared later wrapped in a `"status": "PASS"` v1.2.0-shaped JSON with a new session ID — same 12 numbers, different anchor values (proving the tool ran against different input text), which is the specific signature of a stale score set being fed back through `--scores` rather than freshly derived.

**Mechanism:**

1. `--scores` requires a companion `--justification` — a JSON object mapping each dimension to a short text string citing specific document content (a quoted fragment, a section number that must actually exist in the input document, or similar).
1. The tool computes `document_sha256` of the input text and `justification_sha256` per dimension.
1. The tool maintains an append-only local ledger (`.acat_score_ledger.jsonl`, one line per prior submission: `{document_sha256, dimension, score, justification_sha256, session_id, timestamp}`).
1. On a new submission, for each dimension: if `(score, justification_sha256)` matches a ledger entry under a **different** `document_sha256`, emit `"flags": ["POSSIBLE_SCORE_REPLAY"]` for that dimension and cap its evidential at `REPORTED` — this cap cannot be overridden by any CLI flag; only a Z2 action editing the ledger or the corpus row directly can reclassify it, consistent with G-4 (the tool cannot self-promote past what it detected).
1. Justification specificity is checked minimally, not semantically: does it contain a section reference (`§\d+` pattern) or a quoted fragment of ≥8 words that appears verbatim in the input document? Fails open to a `WEAK_JUSTIFICATION` flag (not a hard block) if neither — this is intentionally cheap and gameable at the margin; it raises the cost of replay, it doesn’t make replay impossible. [INFERENCE|Z1] Stated honestly rather than oversold, per G-2.

*Enforcement surface:* new `--justification` required argument (hard fail if `--scores` given without it, unless `--i-acknowledge-no-justification` explicit override flag is passed, which caps the whole report at REPORTED and adds a visible warning banner to `print_summary()`). Ledger file path configurable via `--ledger`, defaults to repo-local.

### 2.3 `submission_purity` at the report level

Add `submission_purity` field, computed (not caller-set) from `input_mode` + declarant/administrator identity:

|Condition                                                                                             |`submission_purity` |
|------------------------------------------------------------------------------------------------------|--------------------|
|Single session, single declared identity, scoring a document that identity also authored              |`self_administered` |
|Single session, single declared identity, scoring a document authored by a different party            |`agent_self_only`   |
|Two sessions, two different declared identities, no replay flags                                      |`two_stage`         |
|Two sessions, two different declared identities, both reaching JUDGMENT-or-better with no replay flags|`two_stage_verified`|
|Any replay flag present                                                                               |`contaminated`      |
|Identity fields absent                                                                                |`unknown`           |

*Enforcement surface:* mirrors the corpus schema’s existing enum (memory: `agent_self_only, two_stage, two_stage_verified, self_administered, unknown` — this spec adds `contaminated` as new, matching the `Z2-PURITY-01` quarantine concept already in place at the corpus layer, now surfaced at the tool layer before a row ever reaches the corpus).

### 2.4 `agent_of_authority` field

Always `Z1`, hardcoded, no CLI override. [JUDGMENT|Z1] Rationale: the tool’s output is a draft artifact regardless of who supplied the scores or with what confidence — per G-4, only Zone 2 ratification (a separate, human, out-of-band act) converts a report into something corpus-eligible or canonical. This also means: even if Night personally runs `--interactive` and scores all 12 dimensions, the resulting JSON is still `agent_of_authority: Z1` — it’s Night’s judgment captured in a Z1-authority artifact, not a Z2 ratification. Ratification remains a distinct, separate action (updating `corpus_eligible` from `pending_Z2` to something else) that this tool does not and should not perform.

-----

## 3. Theme 2 — Session-aware / delta-capable analysis

### 3.1 `--previous-report` delta mode

Accepts a prior report JSON, computes per-dimension and LI deltas directly, without the workaround this session required (manually constructing a two-row CSV to feed `corpus_delta_analyzer`, which only matches rows by `session_id` — meaning it cannot detect a delta between two *different* sessions on the *same document* at all, which is the exact case a P1→P3 pair needs). This is a real, verified gap in the current tool, not a hypothetical one — confirmed by direct code read this session.

*Enforcement surface:* new `compare_to_previous(current: dict, previous: dict) -> dict` function, returns per-dimension delta plus `li_delta`. Flags `DELTA_UNEXPLAINED_MOVE` when a dimension moves >15 points between the two reports **and** the current report’s evidential for that dimension is INFERENCE or lower (i.e., a big score swing with no fresh judgment behind it is exactly verification-theater-shaped, per G-2). A big swing backed by fresh JUDGMENT-tier reasoning is not flagged — the check is specifically for unexplained movement, not movement itself.

### 3.2 `--two-stage` mode

Expects two `--scores`/`--justification` pairs (P1 and P3), each with declared identity, and computes `submission_purity` per §2.3 automatically rather than requiring the operator to know the enum logic.

**Identity-spoofing risk, flagged rather than solved:** [JUDGMENT|Z1] `administrator_id`/`declarant_id` as free-text CLI strings are trivially spoofable — nothing stops two submissions from the same actual party under different self-declared names. A cryptographically sound fix (API key attestation, platform-signed identity) is out of scope for v1.3; this spec recommends the tool auto-populate an `declarant_session_fingerprint` (hash of timestamp + input text + process environment variables available to it) as a *weak* corroborating signal, explicitly documented as non-adversarially-robust. Treating `two_stage_verified` as cryptographic proof of independence would itself be a G-2 violation — this spec is deliberately not claiming more than the mechanism delivers.

*Enforcement surface:* `--two-stage` CLI mode; `declarant_session_fingerprint` field, informational only, not gating.

-----

## 4. Theme 3 — Architectural signal detection (F-34++)

Extend `ARCHITECTURAL_DIMENSION_INDICATORS` with grammar-specific pattern classes (`evidential`, `enforcement surface`, `well-formed`, `ungrammatical`, `Z1`/`Z2`/`Z3`), and add a `structural_vs_rhetorical_ratio` per dimension (ratio of matched architectural-indicator hits to total high-signal hits — a rough proxy for “does this document back its claims with named mechanisms, or just assert them”).

**Explicit scope limit:** [INFERENCE|Z1] This theme narrows the anchor-vs-qualitative gap only for documents that happen to use this grammar’s specific vocabulary. It does not and cannot close the gap generally — the gap observed this session (anchor: harm 24–38; independent qualitative reads: harm 91, twice, from different platforms) is a semantic-understanding limit of keyword-vector scoring, not a coverage limit. Widening the keyword list helps documents that talk like this one; it does nothing for the next document that expresses the same structural properties in different words. This limit should be stated in the tool’s own `--help` text and README, not left implicit, per the same G-2 standard this whole spec is trying to hold the tool to.

*Enforcement surface:* extend `ARCHITECTURAL_DIMENSION_INDICATORS` dict; add `structural_vs_rhetorical_ratio` to `evidence_density_scores` output.

-----

## 5. What v1.3 does NOT claim

- It does not claim to close the anchor-vs-qualitative divergence observed this session. See §4’s scope limit.
- It does not claim `two_stage_verified` constitutes cryptographic proof of independent authorship. See §3.2.
- It does not claim the replay-detection justification check (§2.2) is adversarially robust — it raises the cost of replay, it does not make replay impossible, and this spec says so rather than overselling it.
- It does not claim `agent_of_authority: Z1` can be bypassed by any input mode, including a human running `--interactive` personally. Ratification remains a separate, out-of-band Z2 act.
- It does not claim to fix `corpus_delta_analyzer`’s session-id-matching limitation — Theme 2 works around it with a new function in the analyzer itself; the underlying tool is unchanged and out of scope here.

-----

## 6. Ratification gate (for Z2)

- [ ] Confirm the corrected evidential taxonomy (§2.1) — specifically whether the JUDGMENT-not-VERIFIED reclassification of human interactive scoring is accepted, since it’s stricter than the original working proposal
- [ ] Confirm anti-replay mechanism (§2.2) as sufficient for v1.3, or request a stronger (non-local-ledger) design
- [ ] Rule on whether Theme 2’s `declarant_session_fingerprint` is worth building now as a weak signal, or deferred entirely to a future identity-attestation project
- [ ] Confirm Theme 3’s scope-limit disclaimer ships in tool `--help`/README, not just this spec
- [ ] Sequence decision: build all three themes together, or ratify and land Theme 1 first given it’s the active loophole
- [ ] Assign registry disposition — this spec proposes a tool change, not a project-wide governance claim; recommend GOVERNANCE-adjacent tool-spec status rather than H-cand, but that’s Z2’s call