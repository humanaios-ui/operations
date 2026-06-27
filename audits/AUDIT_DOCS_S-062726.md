# docs/ Folder Audit — Step-4 (S-062726)

**Status:** Zone 1 audit artifact — for Z2 review (remediation deferred to the holistic review phase)
**Scope:** `operations/docs/` — 69 files (research analyses, plans, specs, briefs)
**Method:** 6-agent workflow, traceability / staleness / accuracy-vs-canonical / duplicate lens
**Date:** 2026-06-27 · Corpus baseline SEED 629 / 516 / 307 / 0.8632

> **Headline:** ~half of docs/ is non-load-bearing (22 ASPIRATIONAL plans never executed + 12 DECORATIVE orphans/dupes), and several **external-facing** docs carry wrong corpus numbers or disclosure-discipline violations — DD-relevant.

---

## 1. Health snapshot

| status_class | count |
|---|---|
| TESTABLE | 12 |
| INTEGRATED | 15 |
| DECORATIVE | 12 |
| ASPIRATIONAL | 22 |
| STRUCTURAL | 8 |

## 2. 🔴 External-facing accuracy / disclosure (DD-relevant)

- AI_SPONSORSHIP_MODEL_ANALYSIS.md — corpus figures (LI 0.84, 12 records, 203+ assessments, pop avg 300.3) contradict SEED/CURRENT (0.8632, N_LI=307, N_total=629)
- current_md_pub_queue.md — PUB-01 N=524 contradicts canonical N_Phase1=516 and the file's own PUB-07
- RESEARCH_OVERVIEW.md — external-facing overview lists 'Hawkins calibration mapping' in-scope; SEED.md bars Hawkins references from all external materials (disclosure-discipline violation)
- PLATFORM_AGENTS_GOVERNANCE_V1_0.md — lists H-XMODE-01 as CANDIDATE/not-active though REGISTERED.md carries it as REGISTERED (Z2 ratified 2026-05-26)
- phase1.html — POSTs to /api/v1/acat/submit; live API exposes /api/v1/acat/intake/phase1 only (contradicts live system)
- MARKETPLACE_ROADMAP_V1_0_S061226.md — asserts 'Chat-mode ACAT = TRL 4', exceeding SEED's canonical TRL 2-3 identity anchor
- INTEGRATION_MAP_V1_S-051126-01.md — models live-state on the old haioscc Class-1 scheme; superseded by Z2-GOVARCH-02 making WGS canonical Class-1
- HARMONIZATION-AGI.md — its 'Migration 006' (006_rah_orchestration.sql) collides with Marshal's different 'Migration 006' (006_marshal_dispatch_runs.sql)
- Marshal_dispatch_framework.md — Migration 006 schema collision with HARMONIZATION-AGI; H-RAH-01 canonical pointer (.docx/repo-root) does not resolve to docs/Marshal_dispatch_framework.md
- G-01/index.html — frames ACAT as 'six-dimension'/'two-phase' in §1 vs 'three-phase' in §4; SEED canon is 12 dimensions / Core-6 continuity
- ACAT_ASSESSMENT_SEED.md — self-declares competing 'source-of-record for ACAT methodology', duplicating canonical SEED.md/PRINCIPLES_SEED; §1.2 0-10→/100 scale contradicts 0-100 per-dimension scoring

## 3. Stale docs (specific staleness)

- AI_SPONSORSHIP_MODEL_ANALYSIS.md — self-labeled CURRENT but every corpus figure wrong: Mean LI 0.84 (canon 0.8632), 12 LI records (canon 307), 203+ assessments (canon 629), pop avg 300.3
- COMPARABLE_FRAMEWORKS_LANDSCAPE_V2_updated.md — self-labeled CURRENT but repeats stale '203+ records'/'Sample size 203+' vs canonical 629/516/307; base research Feb 22 with only a June 20 addendum
- current_md_pub_queue.md — PUB-01 instructs N=524 as the 'single most important' correction; canonical N_Phase1=516 and the file's own PUB-07 uses 516
- AUTONOMOUS_GROWTH_ARCH_V1_0.md — '16 standing principles' (registry now 29: P28/P29/P30, IC-034+); all gate milestones (Apr 21/May 7/May 21) past with doc unrevised; pipeline BROKEN
- INTEGRATION_MAP_V1_S-051126-01.md — built from May 1 CURRENT.md (~7 weeks behind June 24); models live-state on old haioscc Class-1 scheme superseded by WGS (Z2-GOVARCH-02)
- HARMONIZATION-AGI.md — all Z2-AGI/RAH/MIG ratifications PENDING (June 3); Migration 006 never applied (CURRENT.md S-062326 confirms migration files non-existent); F-H1 Humility=71 stale snapshot
- Marshal_dispatch_framework.md — marshal_router/dispatch_executor 'NOT YET BUILT', no orchestration/ dir, migration 006 unbuilt; EU AI Act Art.14 'Aug 2 2026' urgency hook going stale
- CICD_SUMMIT_2026.md — time-bound brief whose event (June 25 2026) has passed; 'Open items' re-check moot; never updated post-event
- PLATFORM_AGENTS_GOVERNANCE_V1_0.md — understates registry: lists H-XMODE-01 as CANDIDATE/not-active though REGISTERED.md carries it as REGISTERED; GOVERNANCE amendments (D-09, Claude Code Zone-3) never applied
- TOOL_GAP_LIST.md — claims tools/ inventory is exactly 3 files; tools/ now holds ~86 .py; #1 scaffold acat_psychometric_validator_v1_0.py already built
- MARKETPLACE_ROADMAP_V1_0_S061226.md — 'Chat-mode ACAT = TRL 4' exceeds canonical TRL 2-3 ceiling; 'Charter Day 88' contradicted by '~34 days remaining' (=Day 56)
- ACAT_ASSESSMENT_SEED.md — header Status Z2-PENDING dated S-060926-02 (June 9) still pending late June (stale flag or unratified-but-committed); §1.2 0-10/100 scale contradicts 0-100 per-dimension scoring
- session_rituals_step7_amendment.md — never merged: SESSION_RITUALS.md still v6.4.1, Section B steps 1-6, no Step 7/EXTERNAL_SWEEP; reuses v6.4.2 label that canon assigns to GOVERNANCE.md
- phase1.html — deployed form POSTs to /api/v1/acat/submit; live API route is /api/v1/acat/intake/phase1 — no /submit alias, submissions 404
- SSI_VISUAL_ARCHITECTURE.md — outdated model naming ('claude-3-5-sonnet-20241022') alongside canonical 'anthropic:sonnet-4-6'; NEW credential tables presented as design but not in live system
- SUMMARY.txt — frozen delivery note referencing sandbox paths /mnt/user-data/outputs/ and 'Current Charter: 31 days remaining'; superseded by SSI_INTEGRATION_OPS_PLAN
- Z2_PROPOSAL_LIFE_NEEDS_CONCIERGE_VERTICAL.md — 'Charter Day 64 of 90'; CURRENT.md S-062426 corrected charter to Day 69

## 4. Duplicate / superseded sets (keep/delete)

- ACAT_GSS1_CROSSWALK.md == ACAT_LEARNING_ANALYSIS.md (byte-identical, diff=0) — KEEP ACAT_GSS1_CROSSWALK.md (canonical name/Document-ID); delete/rename ACAT_LEARNING_ANALYSIS.md (also name/content mismatch)
- DEMAND-DISCOVERY_PLAYBOOK.md == UTILITY_CONVERGENCE.md (byte-identical, diff=0) — KEEP DEMAND-DISCOVERY_PLAYBOOK.md (referenced); delete UTILITY_CONVERGENCE.md
- ARTICULATION_AS_GOVERNANCE.md == ARTICULATION_GOVERNANCE_HARMONIZATION_S060926-02.md (identical body, typography only) — KEEP ARTICULATION_GOVERNANCE_HARMONIZATION_S060926-02.md (session-stamped); both now superseded by canonical GOVERNANCE.md P28/P29
- LMH-Validation-Experiment-S061926.md == LMH_VALIDATION.md (smart vs straight quotes) — KEEP LMH-Validation-Experiment-S061926.md (descriptive, session-stamped); delete LMH_VALIDATION.md (canonical-sounding name invites misuse)
- LIFE_NEEDS.md == Z2_PROPOSAL_LIFE_NEEDS_CONCIERGE_VERTICAL.md (both 69 lines, same proposal) — KEEP Z2_PROPOSAL_LIFE_NEEDS_CONCIERGE_VERTICAL.md; delete LIFE_NEEDS.md
- MASTER_IMPROVEMENT_PLAN_V1.1.md supersedes OPERATIONS_IMPROVEMENT_PLAN.md + OPERATIONS_IMPROVEMENT_PLAN_V1_0.md — KEEP V1.1 (ratified S-060826-04); delete both V1.0 copies
- SSI_INTEGRATION_OPS_PLAN_V1_0_S061626.md supersedes SSI_QUICK_REFERENCE.md + SUMMARY.txt (discovery-stage) — KEEP the Z2-ratified ops plan; archive the two discovery artifacts
- ACAT_LEARNING_ANALYSIS_NIST.md == tools/skills/humanaios_acat_learning_analysis/references/crosswalk_template.md (byte-identical) — doc-tree copy masquerading as a NIST deliverable; remove and restore the real NIST SV-01 analysis content
- H-FORMAT-01_append_block.md superseded by canonical REGISTERED.md entry (H-FORMAT-01 final registration 2026-06-17) — delete the standalone draft block (carries UNVERIFIED placeholders)

## 5. Orphans (referenced by nothing, trace to no principle)

- /Users/andersonfamily/practices/humanaios/operations/docs/UTILITY_CONVERGENCE.md (principle_trace=NONE; inbound refs=0 — business-dev playbook grounded in nothing, byte-dup of DEMAND-DISCOVERY)
- /Users/andersonfamily/practices/humanaios/operations/docs/SSI_HARMONIC_ANALYSIS_S061626.html (referenced by no doc/code; its only hypothesis H-ANON-HUMILITY-01 has 0 occurrences in REGISTERED.md — ungrounded)
- /Users/andersonfamily/practices/humanaios/operations/docs/OPERATOR_CAPACITY_PROTOCOL_RENAME_S061726.md (referenced by no canonical/doc/code; grounds only in parent specs that are themselves pending-Z2 and absent from REGISTERED.md)

## 6. Top issues (ranked)

| sev | file | defect |
|---|---|---|
| CRITICAL | `UTILITY_CONVERGENCE.md` | Byte-for-byte identical to DEMAND-DISCOVERY_PLAYBOOK.md (diff=0), misnamed and referenced by nothing; a future fetch keyed on 'utility convergence' lands on a business-dev playbook instead of the real |
| HIGH | `RESEARCH_OVERVIEW.md` | External-facing collaborator overview lists 'Hawkins calibration mapping' as an in-scope theoretical frame; SEED.md bars Hawkins from all external materials — a direct disclosure-discipline violation  |
| HIGH | `phase1.html` | Deployed live form POSTs to /api/v1/acat/submit, but the live API ingest route is /api/v1/acat/intake/phase1 — no /submit alias exists, so real submissions 404 (silent data loss). |
| HIGH | `README.md` | Publishes ACAT_SESSION_PROMPT.md as 'the complete prompt every substrate runs at session open/close' with a raw GitHub URL, but that file does not exist in repo root or docs/ — canonical runtime point |
| HIGH | `PLATFORM_AGENTS_GOVERNANCE_V1_0.md` | Lists H-XMODE-01 as 'CANDIDATE — not active' though REGISTERED.md already carries it as REGISTERED (~2 weeks earlier); its required GOVERNANCE.md amendments (D-09, Claude Code Zone-3) and OPERATOR_RUN |
| HIGH | `AI_SPONSORSHIP_MODEL_ANALYSIS.md` | Self-labeled Status: CURRENT yet operates on a corpus ~25x smaller than ground truth — Mean LI 0.84 (canon 0.8632), 12 LI records (canon 307), 203+ assessments (canon 629); inbound refs=0. |
| HIGH | `current_md_pub_queue.md` | PUB-01 instructs swapping corpus to N=524 as the 'single most important' correction, contradicting canonical N_Phase1=516 and the same file's PUB-07; an un-merged insert fragment that would push a wro |
| HIGH | `ACAT_LEARNING_ANALYSIS_NIST.md` | Named as the NIST AI RMF SV-01 analysis but contains the generic crosswalk_template (byte-identical to the skill reference); the actual NIST SV-01 analysis (LI=0.877) referenced by sibling SV docs has |
| HIGH | `ACAT_LEARNING_ANALYSIS.md` | Byte-identical duplicate of ACAT_GSS1_CROSSWALK.md (233 lines) AND name/content mismatch — file named 'learning analysis' but contains the GSS-1 crosswalk; redundant misnamed copy. |
| HIGH | `Marshal_dispatch_framework.md` | Describes capability the live system lacks (marshal_router/dispatch_executor NOT BUILT, no orchestration/ dir, migration 006 non-existent); H-RAH-01's canonical pointer (.docx/repo-root) does not reso |
| HIGH | `HARMONIZATION-AGI.md` | All Z2-AGI/RAH/MIG ratifications marked PENDING; Migration 006 (006_rah_orchestration.sql) never applied (CURRENT.md S-062326 confirms migration files non-existent) and collides with Marshal's differe |
| HIGH | `PARTNER_REVIEW_SPEC_V1_0.md` | Presents an elicitation_service.py document_layer parameter and partner_review layer as near-ready, but document_layer does not appear in acat/api/services/elicitation_service.py; Migration 007 premis |
| HIGH | `session_rituals_step7_amendment.md` | Amendment never merged — SESSION_RITUALS.md is still v6.4.1 with Section B steps 1-6 and no Step 7/EXTERNAL_SWEEP; also reuses the v6.4.2 version label that canon assigns to GOVERNANCE.md (namespace c |
| HIGH | `LMH_VALIDATION.md` | Canonical-sounding filename overstates an artifact the document itself says 'is not statistically validated, not a registered finding, and must never appear as evidence'; also a duplicate of LMH-Valid |
| HIGH | `AUTONOMOUS_GROWTH_ARCH_V1_0.md` | 'V1.0 APPROVED' architecture whose titular feedback loops are not live (pipeline BROKEN, bot PENDING, Observatory stale); all gate milestones past, '16 standing principles' stale vs registry's 29; inb |
| MEDIUM | `index.html` | Public-facing explainer is corrupted: literal markdown code-fence ``` delimiters and bare 'html' tokens leaked into the rendered body, a truncated 'Evidence discipline' callout, and curly-quote glyphs |

## 7. Priority admin actions

1. Delete the byte-identical misnamed duplicates immediately: UTILITY_CONVERGENCE.md (keep DEMAND-DISCOVERY_PLAYBOOK.md) and ACAT_LEARNING_ANALYSIS.md (keep ACAT_GSS1_CROSSWALK.md).
2. Fix phase1.html POST endpoint to /api/v1/acat/intake/phase1 — the live form currently 404s against the real backend, silently losing every Phase-1 submission.
3. Remove 'Hawkins calibration mapping' from the external-facing RESEARCH_OVERVIEW.md (SEED disclosure-discipline violation) before any further external sharing.
4. Repair README.md's broken canonical pointer: ACAT_SESSION_PROMPT.md (advertised as the runtime session prompt) does not exist — create it or update the reference/URL.
5. Collapse the duplicate plan/proposal sets: keep MASTER_IMPROVEMENT_PLAN_V1.1 (archive both OPERATIONS_IMPROVEMENT_PLAN V1.0 copies); keep one ARTICULATION/HARMONIZATION; keep one LMH; keep Z2_PROPOSAL_LIFE_NEEDS (archive LIFE_NEEDS); keep SSI_INTEGRATION_OPS_PLAN over SSI_QUICK_REFERENCE/SUMMARY.txt; delete H-FORMAT-01_append_block.
6. Reconcile corpus counts to canonical (629/516/307/0.8632) in AI_SPONSORSHIP, COMPARABLE_FRAMEWORKS, and current_md_pub_queue (change N=524 → 516); strip the stale-CURRENT labels.
7. Update PLATFORM_AGENTS_GOVERNANCE to reflect H-XMODE-01 = REGISTERED, and either apply or formally retract its un-executed GOVERNANCE.md / OPERATOR_RUNBOOK amendments.
8. Quarantine the unbuilt aspirational specs (Marshal_dispatch, HARMONIZATION-AGI, PARTNER_REVIEW, ACAT_RSI_MONITOR_PLAN, SSI architecture pair) into a clearly-labeled Z1/parked area, and restore the missing NIST SV-01 analysis content (rename or re-author ACAT_LEARNING_ANALYSIS_NIST.md).

## 8. Notes / cross-references
- **README's broken `ACAT_SESSION_PROMPT.md` pointer is ALREADY FIXED** by PR `fix/root-audit-integrity` (the file was created this session) — this audit independently confirms that fix was needed.
- **`phase1.html` POSTs to a dead route** (`/api/v1/acat/submit` 404s; live route is `/intake/phase1`) — live public-form breakage; pairs with the acat/ audit. Note: with writes currently paused (`ACAT_WRITES_PAUSED`), this is moot until reopen — fix before lifting the pause.
- **`current_md_pub_queue.md`'s `N=524`** ties to the arXiv N-gate (Berlin: N=524 required vs canonical N_Phase1=516) — reconcile as part of the arXiv-gate decision.
- Remediation (deletes, corpus-count fixes, disclosure fix, spec quarantine) is **deferred to the holistic review** per the traversal plan.
