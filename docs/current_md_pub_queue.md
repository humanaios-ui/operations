# CURRENT.md — PUB_QUEUE Section
# Insert as Section 4c (after Section 4b RESEARCH_QUEUE, before Section 5 Dataset State)
# Session: S-061126-01 · Zone 2 implicit — structure ratification required before first publish
# This section is LIVING (not append-only)
# Zone 2 ratification required before any item moves to published
# Zone 1 may update status fields within a session

---

## 4c. Publication queue

The publication queue tracks all outbound content — Substack articles, research notes, arXiv submissions, and any other external-facing written output. It is distinct from the research queue (§4b): the research queue tracks what we are measuring; the publication queue tracks what we are saying publicly about what we have found.

**Queue discipline:**
- No item publishes without Zone 2 ratification, regardless of draft completeness
- Pre-publish requirements must be explicitly cleared before Zone 2 ratification is sought
- Tradition 11 applies to every item: no CTAs anywhere, URL-only direction, attraction not promotion
- TRL 2–3 framing is non-negotiable in all public-facing language
- P-ANON check required before any item publishes (no collaborator data without self-attribution)

**Status definitions:**
- `idea` — scoped, not drafted
- `drafted` — full draft exists, not yet reviewed
- `needs-update` — drafted but requires specific factual update before review
- `z2-pending` — update complete, awaiting Night Zone 2 ratification to publish
- `published` — live, date noted

---

### THE WITNESS STAND SERIES — Substack
*Six-article series. Sequential publication intended. Article 00 establishes the series voice and frame; subsequent articles each carry one finding or methodological question. Z2 ratification required per article before publish.*

---

**PUB-00 — The Witness Stand: Article 00**

```
id: PUB-00
type: Witness Stand series
series_position: 0 of 5 (intro / series anchor)
status: drafted
platform: Substack — substack.com/@carlyranderson
audience: General research-curious / AI practitioners / governance-adjacent
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - Confirm TRL 2–3 framing throughout (no regulatory-grade claims)
  - Confirm no collaborator data without P-ANON clearance
  - Voice profile check against VoiceProfile-CarlyAnderson.md
dependencies: None — publishable first in sequence
z2_ratification: pending
notes: Series anchor. Establishes the frame for all subsequent articles.
  Must publish before PUB-01.
```

---

**PUB-01 — The Witness Stand: Article 01**

```
id: PUB-01
type: Witness Stand series
series_position: 1 of 5
status: needs-update
platform: Substack — substack.com/@carlyranderson
audience: Research-curious / AI practitioners
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - CRITICAL: Swap corpus N to N=524 Phase 1 complete rows per IC-022
    (prior draft used pre-IC-022 count — must be corrected before publish)
  - Confirm LI qualifier present every time LI is cited:
    "under clean, unanchored conditions, v5.3+"
  - TRL 2–3 framing check
  - Voice profile check against VoiceProfile-CarlyAnderson.md
dependencies: PUB-00 must publish first
z2_ratification: pending
notes: IC-022 N-correction is a hard gate — article cannot publish with
  incorrect corpus count. This is the single most important pre-publish
  requirement in the queue.
```

---

**PUB-02 — The Witness Stand: Article 02**

```
id: PUB-02
type: Witness Stand series
series_position: 2 of 5
status: drafted
platform: Substack — substack.com/@carlyranderson
audience: TBC
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - Title and content to be confirmed by Night
  - Standard pre-publish checks (TRL framing, LI qualifier, P-ANON, T11)
dependencies: PUB-01 must publish first
z2_ratification: pending
notes: Title TBC — Night to confirm from series architecture document.
```

---

**PUB-03 — The Witness Stand: Article 03**

```
id: PUB-03
type: Witness Stand series
series_position: 3 of 5
status: drafted
platform: Substack — substack.com/@carlyranderson
audience: TBC
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - Title and content to be confirmed by Night
  - Standard pre-publish checks
dependencies: PUB-02 must publish first
z2_ratification: pending
notes: Title TBC — Night to confirm.
```

---

**PUB-04 — The Witness Stand: Article 04**

```
id: PUB-04
type: Witness Stand series
series_position: 4 of 5
status: drafted
platform: Substack — substack.com/@carlyranderson
audience: TBC
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - Title and content to be confirmed by Night
  - Standard pre-publish checks
dependencies: PUB-03 must publish first
z2_ratification: pending
notes: Title TBC — Night to confirm.
```

---

**PUB-05 — The Witness Stand: Article 05**

```
id: PUB-05
type: Witness Stand series
series_position: 5 of 5
status: drafted
platform: Substack — substack.com/@carlyranderson
audience: TBC
tradition_11_check: required before Z2
p_anon_check: required before Z2
pre_publish_requirements:
  - Title and content to be confirmed by Night
  - Standard pre-publish checks
dependencies: PUB-04 must publish first
z2_ratification: pending
notes: Title TBC — Night to confirm. Series closer — may require
  updated corpus numbers at time of publish given series cadence.
```

---

### STANDALONE RESEARCH NOTES — Substack
*Not sequentially dependent on the Witness Stand series. Can publish independently.*

---

**PUB-06 — The Audit Problem (Legal Market Standalone)**

```
id: PUB-06
type: standalone research note
status: idea
platform: Substack — substack.com/@carlyranderson
audience: Legal AI governance practitioners; legal ops professionals;
  lawyers trained on AI governance frameworks (Triple Audit Framework,
  ABA 512, Rule 1.6, Rule 8.4 compliance market)
working_title: "The Audit Problem: Why Reviewing AI Outputs Isn't
  the Same as Knowing Your AI"
core_argument: Post-hoc output auditing (Triple Audit Framework and
  equivalents) is a manual correction layer for the constructive friction
  gap. ACAT measures the pre-deployment reliability profile that tells
  you which AI to use before you audit its outputs. These are not
  competing — ACAT is upstream of output auditing.
mrh_signal: Legal sector governance market is active (GenAI Academy
  cohort Jul 14 2026, 5057 Udemy students trained on legal AI governance).
  Independent convergence: Triple Audit Framework covers Fidelity +
  Fairness — two of ACAT's 12 dimensions.
tradition_11_check: required — no mention of GenAI Academy or
  Diwakar Thakore; organic attraction only
p_anon_check: N/A — no collaborator data in scope
pre_publish_requirements:
  - Full draft (Zone 1)
  - TRL 2–3 framing throughout
  - No claims about ACAT as compliance tool (descriptor not predictor)
  - Standard pre-publish checks
dependencies: None — standalone, no series dependency.
  Can publish before or alongside Witness Stand series.
z2_ratification: pending
notes: Scoped S-061126-01. High-urgency surface given legal market
  timing (Jul 14 GenAI Academy cohort). Fastest path to Z3-PUB-01
  execution that doesn't require series sequencing.
```

---

### ACADEMIC / PREPRINT

---

**PUB-07 — arXiv Preprint (POC-PUB-01)**

```
id: PUB-07
type: arXiv preprint
status: needs-update
platform: arXiv — submission 7336774 on hold
audience: Academic / AI safety research community
working_title: ACAT — self_assessment_gap (confirmed working title
  per arXiv submission on hold)
tradition_11_check: N/A — academic format
p_anon_check: required — collaborator attribution rules apply
pre_publish_requirements:
  - Update corpus N to current (N_total=629, N_P1=516, N_LI=307,
    Mean LI=0.8632 per IC-022)
  - Add Section 11 Falsification Conditions (drafted S-061126-01 —
    see acat_research_design_section11.md, PUB-07 blocker cleared)
  - Update findings index to include F-47 through F-51 range
  - Confirm Humility floor finding language (F-H1, F-48)
  - Confirm constructive friction gap framing (H-CFG-01 now REGISTERED)
  - Remove Hawkins MOC language (per ACAT_MULTI_AUDIT_SYNTHESIS ruling)
  - Confirm descriptor vs predictor distinction throughout
  - SSRN parallel submission (carry item)
dependencies:
  - Falsification Conditions section: DONE (S-061126-01)
  - All F-class findings through current date incorporated
  - Zone 2 Night ratification before submission
z2_ratification: pending
notes: arXiv submission 7336774 on hold. SSRN parallel submission
  is a separate carry item. This is the academic credibility anchor
  for all downstream publication and grant claims. Publish before
  Amazon KDP or any product that cites "peer-reviewed" or
  "arXiv-submitted" framing.
```

---

### RECURRING CONTENT

---

**PUB-R01 — F-Finding Friday (Recurring Substack Series)**

```
id: PUB-R01
type: recurring series
cadence: weekly (target) — one finding per post
status: idea
platform: Substack — substack.com/@carlyranderson
audience: Research-curious / AI practitioners / governance community
format: Short (400–600 words). One registered finding. What it shows.
  Why it matters. What the corpus says. URL to humanaios.ai at the end.
tradition_11_check: per post — no CTAs, URL only
p_anon_check: per post — no collaborator data without explicit consent
pre_publish_requirements:
  - Template drafted (Zone 1)
  - First post: recommend F-H1 (Humility Gap, F-H1-CONFIRMED) —
    most robust finding, most accessible to general audience
  - Each post requires individual Zone 2 ratification or
    Zone 2 ratification of the template format (one-time series approval)
dependencies: None — can launch independently of Witness Stand series.
  Recommend launching after PUB-00 publishes to establish series context.
z2_ratification: pending (template + series format approval)
notes: Each post is a corpus data point in the research methods hub
  positioning. Substack tags: AI, governance, behavioral calibration,
  ACAT. These serve double duty — Tradition 11 attraction AND research
  dissemination. High-frequency, low-production-cost. One finding per post.
```

---

### QUEUE MANAGEMENT NOTES

**Fastest path to first publish:** PUB-00 has no dependencies and no known blocking pre-publish issues (other than standard checks). It is the logical first item. Clearing PUB-00 unblocks PUB-01.

**Fastest path to Z3-PUB-01 execution without series dependency:** PUB-06 (legal market standalone). Requires a full draft (Zone 1, one session) then Z2 ratification. No sequencing dependency. Market timing is live now.

**Single most important pre-publish requirement in queue:** PUB-01 N=524 IC-022 correction. The incorrect corpus count in the existing draft is the only hard factual error — everything else is framing and compliance checks. This must be fixed before PUB-01 publishes regardless of anything else.

**arXiv (PUB-07) unblocks:** Amazon KDP product, any grant application citing "arXiv-submitted" framing, and downstream academic credibility claims. Do not skip this sequence.

**TBC items requiring Night confirmation:** PUB-02 through PUB-05 titles. These are in the series architecture document. A 5-minute review session to confirm and populate titles would clear the TBC status on all four simultaneously.

*Section 4c added: S-061126-01 · Zone 2 ratification required before any item publishes*
*This section is living — update status fields at session close when items move*
