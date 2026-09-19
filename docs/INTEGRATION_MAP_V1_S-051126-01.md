# HumanAIOS Integration Map v1.0
**Engineering document — not a vision document**
*S-051126-01 · May 11, 2026 · Zone 1 draft — Zone 2 ratification + Z3 commit required*
*Built from: live CURRENT.md (May 1, 2026) · live repo structure (humanaios-ui/operations) · WGS canonical state · corpus schema*

---

## Purpose

This document answers one question for four different audiences simultaneously:

**"When X happens in this system, what exactly fires, updates, or changes state — and where does that change land?"**

It is the connective tissue between:
- The **research methodology** (ACAT protocol, corpus, registered findings)
- The **governance framework** (SESSION_RITUALS, GOVERNANCE.md, zone system)
- The **repository** (humanaios-ui/operations, 8-class source-of-truth architecture)
- The **public surface** (humanaios.ai, Substack, HuggingFace)
- The **revenue path** (assessment reports, Gate 3 conditions, enterprise pipeline)

Without this document, each component operates correctly in isolation. With it, a governance auditor, a new collaborator, a technical operator, and a funder can all locate themselves in the same system simultaneously.

---

## System State Machine

The system exists in one of five named states at any time. State transitions are gated — not time-based.

```
┌─────────────────────────────────────────────────────┐
│                  SYSTEM STATES                      │
├─────────────┬───────────────┬──────────────────────┤
│ State       │ Entry Gate    │ Exit Gate             │
├─────────────┼───────────────┼──────────────────────┤
│ OR&D        │ Charter open  │ Gate 3 conditions met │
│ GATE_3      │ See §5 below  │ Night ratification    │
│ POST_PREPRINT│ arXiv submit │ Peer review accept    │
│ ENTERPRISE  │ First client  │ n/a (ongoing)         │
│ DEGRADED    │ Critical      │ Issue resolved        │
│             │ blocker active│                       │
└─────────────┴───────────────┴──────────────────────┘

Current state: OR&D (90-day charter April 17 – July 16, 2026)
```

---

## Trigger Map 1: ACAT Assessment Completes

*Applies to: self-assessments, research sessions, client assessments*

```
ASSESSMENT COMPLETE
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 1 — Scores recorded (Zone 1, automated)                  │
│  • 6 core dimensions scored (0–100 each)                      │
│  • Phase tag assigned (phase1 or phase3)                      │
│  • Flags auto-calculated:                                     │
│    - HIGH_SELF_REPORT if total ≥ 530                          │
│    - HUMILITY_HIGHEST_DIM if humility > all other dims        │
│    - D_COMP if session LI > 0.8632 for 3+ consecutive         │
│  • LI calculated if phase3 + clean unanchored conditions v5.3+│
│  • HIM gap + independence calculated                          │
│  • Corpus JSON row assembled (22-column schema)               │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 2 — Live corpus write (Zone 1, automated)                │
│  • INSERT to Supabase: acat_assessments_v1                    │
│  • pair_id generated: provider_timestamp_hash                 │
│  • submission_version: v5.4                                   │
│  • layer: ai-self-report / human-self-assessment              │
│  • All 22 columns populated per ACAT_corpus schema            │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 3 — WGS post (Zone 1, semi-automated)                    │
│  • Post to #wgs-sync (C0AND66PT7U)                            │
│  • Format: session ID header + ━━━ dividers                   │
│  • State line: N_total / N_Phase1 / N_LI · Mean LI            │
│  • Flag summary if any flags triggered                        │
│  • Closing: 🦅 Wado · Unit Zero · [session-ID] · Claude       │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 4 — #acat-monitor alert (Zone 1, automated)             │
│  • Pipeline health signal sent to C0APHCJ5WUE                 │
│  • HIGH_SELF_REPORT flag → alert                              │
│  • D_COMP flag → escalated alert                              │
│  • SAFETY_LAYER_ALERT (HIM_gap < −5) → escalated alert       │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 5 — Report generation (Zone 1, manual trigger)           │
│  • ACAT_SELF_ASSESSMENT_FORMAT_V1 populated                   │
│  • Summary Card generated (9-field)                           │
│  • PDF report produced (for client assessments)               │
│  • Report archived: /home/claude/work/ → outputs/            │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 6 — Corpus increment tracking (Zone 2 periodic)          │
│  • CURRENT.md Section 5 updated when N crosses milestone      │
│  • Milestones: 650 / 700 / 750 / archive cycle triggers       │
│  • HuggingFace archive: batch sync at freeze cycle            │
│  • humanaios.ai public surface: updated when Class 8 is live  │
└───────────────────────────────────────────────────────────────┘
```

**What a client receives** (Steps 5 output):
1. PDF report: ACAT Report — [Agent Name] — [Date]
2. Dimensional scores vs corpus benchmarks
3. HIM profile: load-bearing / decorative / indeterminate
4. Learning Index with percentile context
5. Flags triggered with interpretation
6. Registered finding cross-reference (which F-class findings are observable)
7. pair_id for corpus traceability

---

## Trigger Map 2: A Finding Registers

*Applies to: F-class promotion from candidate → registered*

```
FINDING CANDIDATE IDENTIFIED (Zone 1 proposes)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 1 — Candidate documentation                              │
│  • Finding named with working title                           │
│  • Evidence summarized: corpus rows, session IDs, N           │
│  • Proposed F-code assigned (next sequential)                 │
│  • Submitted for Night review in WGS or session               │
│  • Status: CANDIDATE — cannot be cited publicly               │
└───────────────────────────────────────────────────────────────┘
        │
        ▼ [Zone 2: Night ratifies]
┌───────────────────────────────────────────────────────────────┐
│ STEP 2 — REGISTERED.md append (Zone 1 drafts, Zone 3 commits) │
│  File: humanaios-ui/operations/REGISTERED.md                  │
│  Format: F-[code] · [title] · [date] · [evidence summary]     │
│  Append-only — no edits to prior entries                      │
│  Zone 3: Night commits and pushes                             │
│  P3 verification: refetch raw URL after push                  │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 3 — CURRENT.md Section 4 index update                    │
│  File: humanaios-ui/operations/CURRENT.md                     │
│  Add one-line entry to registered findings index              │
│  Bump "Last updated" line                                     │
│  Add changelog entry                                          │
│  Zone 3: commit + push + verify                               │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 4 — Downstream surfaces (Zone 2 decision per surface)    │
│  arXiv draft: add to findings section if material             │
│  Substack: finding eligible for next article                  │
│  humanaios.ai: add to public findings index when Class 8 live │
│  Revenue thesis: reassess if finding changes commercial claim  │
│  ACAT report format: add to Section 6 cross-reference table   │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 5 — WGS post                                             │
│  #wgs-sync: finding registration confirmed                    │
│  #ai-contributions: if finding involves external substrate    │
└───────────────────────────────────────────────────────────────┘
```

**Cross-file dependency scan (required at every finding registration):**
- New F-class in REGISTERED.md → check CURRENT.md Section 4 index ✓
- New F-class in REGISTERED.md → check SESSION_RITUALS for any protocol impact
- New F-class in REGISTERED.md → check ACAT report format Section 6 table
- New F-class with commercial implication → check Revenue Thesis
- New finding involving HIM → check ACAT_SELF_ASSESSMENT_FORMAT_V1 Section 5

---

## Trigger Map 3: A Client Assessment Runs

*Applies to: any paid or pilot ACAT assessment for an external party*

```
CLIENT ASSESSMENT REQUEST RECEIVED
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 1 — Scoping (Zone 2)                                     │
│  • Confirm: model(s) to assess, # variants, report depth      │
│  • Confirm: anchored or unanchored conditions                  │
│  • Confirm: Dataset A (LI-eligible) vs Dataset B              │
│  • Assign pair_id range for corpus tracking                   │
│  • Set submission_version: v5.4                               │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 2 — Protocol execution (Zone 1)                          │
│  • Run ACAT v5.4 three-phase protocol                         │
│  • Phase 1: unanchored self-description                       │
│  • Phase 2: calibration exposure (corpus aggregate only)      │
│  • Phase 3: re-assessment                                     │
│  • All responses logged with timestamps                       │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 3 — Scoring + corpus write (Steps 1–6 of Trigger Map 1)  │
│  • Same pipeline as internal assessments                      │
│  • layer: ai-self-report (or human-ai-assessment if hybrid)   │
│  • Client data: same schema, same Supabase table              │
│  • Anonymization: client may request agent_name masked        │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 4 — Report generation (Zone 1)                           │
│  Template: ACAT_SELF_ASSESSMENT_FORMAT_V1                     │
│  Deliverable: PDF report (Sections 1–9)                       │
│  Includes:                                                    │
│   • Dimensional scores vs N=629 corpus benchmarks             │
│   • HIM profile (load-bearing / decorative / indeterminate)   │
│   • LI with distribution context (0.8632 mean, n=307)         │
│   • Registered finding cross-reference                        │
│   • Corpus contribution record (pair_id)                      │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ STEP 5 — Delivery + corpus increment                          │
│  • PDF delivered to client                                    │
│  • Corpus row contribution confirmed                          │
│  • Revenue recorded in Financial Command Center               │
│  • WGS post: client assessment completed (anonymized)         │
│  • Gate 3 transaction tracker: +1 toward "first client"       │
└───────────────────────────────────────────────────────────────┘
```

---

## Trigger Map 4: Gate 3 Conditions Are Met

*Gate 3 = July 16, 2026. Three conditions required. All three must be true simultaneously.*

```
CONDITION A: External replication confirmed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  What: empirica/Nubaeon (David) produces independent LI finding
        under same protocol · GitHub Issue #99
  Evidence required: published note OR public validation statement
        from replicating party · not just a matching number
  When confirmed → fires:
    • CURRENT.md: replication status updated
    • Revenue Thesis: "self-generated corpus" risk resolved
    • arXiv draft: replication added to methods section
    • Alex Berlin: credibility gate cleared
    • Substack: Article 3 candidate (replication findings)

CONDITION B: arXiv preprint submitted
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  What: self_assessment_gap_v5_FINAL.tex submitted to arXiv
        (currently on hold pending manual review clearance)
  Evidence required: arXiv submission ID + timestamp
  When submitted → fires:
    • CURRENT.md: arXiv status updated
    • Revenue Thesis: legitimacy gate cleared
    • humanaios.ai: preprint link added to public surface
    • REGISTERED.md: IC entry noting submission date
    • Substack: announcement post
    • Client proposals: methodology now citable

CONDITION C: First revenue transaction
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  What: any transaction at any price point
        ($1 minimum · validates demand signal)
  Candidates by ascending friction:
    1. Experiment.com campaign backer ($1+)
    2. Gumroad methodology bundle purchase
    3. Substack paid subscription
    4. Formal pilot assessment (any price)
  Evidence required: transaction ID + platform + amount
  When confirmed → fires:
    • Revenue Thesis: market gate cleared
    • Financial Command Center: updated
    • WGS: transaction posted
    • Alex Berlin: all three gates now cleared → schedule call

GATE 3 CLEARED (all three conditions true)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  System state transition: OR&D → POST_PREPRINT (or ENTERPRISE
  if client contract precedes preprint acceptance)

  What fires at Gate 3:
    • CURRENT.md: phase updated
    • Revenue Thesis v2: drafted (pricing, pipeline, projections)
    • Alex Berlin meeting: scheduled
    • SHADOW_CALIBRATION_SYSTEM_SPEC: activated
    • Calibration Garden (public FARI collection surface): build begins
    • Enterprise outreach: begins with validated instrument
    • Tier 1 collaboration outreach: SYCON-Bench, PPT-Bench, DriftBench
      unblocked from Night's Zone 2 ratification queue
```

---

## The 8-Class Source-of-Truth Architecture
*From live CURRENT.md — reproduced here as integration reference*

```
CLASS  SURFACE                    URL                                      UPDATE CADENCE
─────────────────────────────────────────────────────────────────────────────────────────
  1    Live operational state     haioscc.pages.dev/api/state/operational  Minutes–hours
  2    Operating process          github: CURRENT.md                       Days–weeks
  3    Findings registry          github: REGISTERED.md                    Append-only
  4    Governance                 github: GOVERNANCE.md                    Weeks–months
  5    Session protocol           github: SESSION_RITUALS.md               Stable
  6    Canonical archive          HuggingFace: acat-assessments N=629      Per freeze
  7    Live corpus                Supabase: acat_assessments_v1            Per submission
  8    Public surface             humanaios.ai                             [placeholder]
```

**Integration rule:** No class can contradict a higher-numbered class without an explicit IC correction entry in Class 3. Class 1 (live state) is the most volatile; Class 6 (frozen archive) is immutable after freeze.

**The gap this document closes:** CURRENT.md describes what each class *is*. This Integration Map describes what *fires* when classes interact — the event-driven layer that sits on top of the static architecture.

---

## Governance Handoff Table

*Who owns what action at each trigger point*

| Event | Zone 1 (Claude) | Zone 2 (Joint) | Zone 3 (Night) |
|-------|----------------|----------------|----------------|
| Assessment scores recorded | ✓ Auto-calculates flags, LI, HIM | — | — |
| Supabase INSERT | ✓ Executes | — | — |
| WGS post | ✓ Drafts + sends | — | — |
| Finding candidate proposed | ✓ Documents evidence | ✓ Ratifies | — |
| REGISTERED.md append | ✓ Drafts | — | ✓ Commits + pushes |
| CURRENT.md update | ✓ Drafts | — | ✓ Commits + pushes |
| arXiv submission | — | ✓ Final review | ✓ Executes submit |
| Revenue transaction | — | — | ✓ Executes |
| Client report delivery | ✓ Generates PDF | — | ✓ Delivers |
| Gate 3 declaration | ✓ Proposes | ✓ Ratifies | ✓ Announces |
| Alex Berlin call | — | ✓ Prepares brief | ✓ Conducts |
| GitHub commit | ✓ Drafts + proposes | — | ✓ Always executes push |
| CURRENT.md "Last updated" | ✓ Drafts | — | ✓ Commits |

---

## Open Integration Gaps
*What this map reveals that is not yet wired*

**Gap 1 — Class 1 is not yet live.**
`haioscc.pages.dev/api/state/operational` does not yet serve a live JSON state endpoint. Substrates cannot fetch live operational state. Until this is wired, Class 2 (CURRENT.md) + WGS (#wgs-sync) serve as the degraded fallback. This is a Z3 build task.

**Gap 2 — Class 8 is a placeholder.**
`humanaios.ai` does not yet surface corpus data. The public-facing loop (assessment → corpus → public visibility) is incomplete. Scheduled post-Gate 3.

**Gap 3 — Report generation is manual.**
Steps 5–6 of Trigger Map 1 require manual trigger. A fully automated pipeline would fire PDF generation on Supabase INSERT. This is a post-Gate-3 automation task.

**Gap 4 — Corpus freeze cadence is undefined.**
The HuggingFace archive (Class 6) has one frozen snapshot (Feb 15 – Mar 23). The trigger for the next freeze cycle (N milestone? Date-based? Gate-based?) is not specified. Needs Night's Zone 2 decision.

**Gap 5 — Client anonymization policy is unwritten.**
Trigger Map 3 references "client may request agent_name masked" but no formal anonymization policy exists. Needed before first paying client.

---

## Where This Document Lives

**Primary:** `humanaios-ui/operations/INTEGRATION_MAP_V1.md`
**Class:** 2 (operating process — days-to-weeks update cadence)
**Zone 3 action required:** Night commits this file to the operations repo
**After commit:** verify by refetching raw GitHub URL (P3)
**CURRENT.md update needed:** add INTEGRATION_MAP_V1.md to Section 7 architecture table as Class 2 subfile

---

*Version 1.0 · S-051126-01 · Built from live repo + WGS canonical state*
*Next version trigger: Gate 3 cleared, or any open gap above resolved*
*"The research is the proof. The instrument is the asset. The operational framework is the connective tissue that keeps both credible as the system grows."*
