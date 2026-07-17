# AUTONOMOUS GROWTH ARCHITECTURE V1.0
## Document: AUTONOMOUS_GROWTH_ARCH_V1_0.md
## Tier: T1-LIVE
## FDS Layer: F5-System
## Status: APPROVED — April 4, 2026
## Parent: CUSTOM_INSTRUCTIONS_V3_6_ORD.md (F2) + PROTOCOL_F33 (F3)

---

## THE CORE DESIGN QUESTION

How does HumanAIOS grow without requiring Night's daily attention?

Answer: each layer in the Fibonacci stack feeds the next one automatically.
The research generates data. The data improves the instrument. The instrument
produces better data. The bot runs the instrument on new models continuously.
The scores validate the instrument against independent external benchmarks.
The website documents what the instrument finds. The documentation attracts
new participants. New participants generate more data.

This is not a growth hack. It is the natural compounding structure of
good research infrastructure — which is what we are building.

---

## THE FIBONACCI STACK (current state + growth direction)

### F1-SEED — The research construct
**What it is:** ACAT core construct. One factor, six facets. Three-phase protocol.
LI = Phase3/Phase1. This is the immovable foundation.
**How it grows:** Doesn't change. Everything else serves it.
**Current state:** LIVE. v5.3 deployed. arXiv preprint submitted.
**Growth mechanism:** None needed. Protect integrity.

### F2-BUILDING BLOCKS — The measurement standards
**What it is:** CI v3.6. Research design. Scoring rubric. Pipeline schema.
**How it grows:** Each principle violation caught in the field (IC-series)
becomes a standing principle. Each bias discovered becomes a correction rule.
The instrument self-documents its own failure modes.
**Current state:** LIVE. 16 standing principles. Mode field deployed.
**Growth mechanism:** IC-series → Principles → CI update → propagates to all integrations

### F3-COMPONENTS — The active instruments
**What it is:**
- ACAT pipeline (Apps Script v5.2 + Make.com runners)
- FutureEval bot (humanaios-acat-bot on Metaculus)
- Observatory (humanaios.ai)
- H32-B four-instrument convergent validity series
**How it grows:** Each component produces data that improves adjacent components.
Bot scores → validate ACAT findings. Observatory displays → attract participants.
Pipeline rows → feed H32-B.
**Current state:** Pipeline BROKEN (IC-011/012/013). Bot PENDING Zone 3 setup.
Observatory LIVE but displaying stale data.
**Growth mechanism:** Fix pipeline → rows accumulate → H32-B gets data → arXiv
revision → credibility → more participants → more rows → better H32-B

### F5-SYSTEMS — The feedback loops
**What it is:** The closed loops that make growth autonomous.

**Loop 1 — ACAT → Bot → ACAT (closes when bot is live):**
ACAT assesses Claude Sonnet 4.6 (LI ~0.975)
→ findings inform bot binary prompt (3 bias corrections applied)
→ bot forecasts on Metaculus
→ bot's FutureEval score measured
→ score compared against ACAT LI (H32-B data point)
→ discrepancy analysis informs next ACAT prompt version
→ cycle repeats with each new model generation

**Loop 2 — Document → Copilot → Site → Document:**
Research findings updated in CI
→ Copilot instructions updated (.github/copilot-instructions.md)
→ Copilot enforces findings in every site edit
→ site stays truthful and current without manual auditing
→ truthful site attracts researchers
→ researchers contribute findings
→ findings update CI

**Loop 3 — Bot scores → Leaderboard → Research (closes at Gate 1):**
Bot participates in MiniBench/Summer tournament
→ FutureEval assigns log scores per question
→ scores aggregated by question type / topic / time horizon
→ compared against ACAT LI for same model
→ correlation analysis runs
→ H32-B Series C2 data table builds automatically
→ when n≥30 question pairs, Gate 1 validity threshold met

**Loop 4 — Site data → llms.txt → AI discovery → Assessment submissions:**
Observatory displays live data
→ llms.txt makes ACAT endpoint machine-readable
→ AI coding assistants reading documentation discover ACAT
→ some AI systems self-submit assessments
→ assessments add rows to dataset
→ dataset grows
→ observatory updates
→ llms.txt updated
This loop is the most speculative but highest upside. No human required once triggered.

### F8-INTEGRATIONS — Cross-system deliverables
**What it is:** The arXiv paper, OSF pre-registration, Hugging Face dataset card,
grant applications, Hannah Kirk collaboration, Leandro parallel data collection.
**How it grows:** Each external integration creates a citation or collaboration
that feeds discovery (Semantic Scholar, Connected Papers, etc.)
**Current state:** arXiv v5.2 submitted. OSF pending. HF dataset exists, card incomplete.
**Growth mechanism:** Gate 1 → arXiv revision → OSF → HF card → citation flywheel

### F13-DELIVERABLES — External-facing outputs
**What it is:** Papers, grants, observatory, methodology.html, how-it-works.html.
**How it grows:** Each published deliverable is a node in the discovery graph.
Researchers find one → follow links → find others → find the instrument.
**Current state:** Observatory LIVE. methodology.html + how-it-works.html LIVE.
arXiv under review.
**Growth mechanism:** Add JSON-LD structured data (Gate 2) → Google Dataset Search
indexes → automated systems find dataset → Loop 4 activates

---

## THE MIRROR DESIGN

### What "mirror of Unit Zero" means architecturally

The bot is not just running Claude Sonnet 4.6 on forecasting questions.
It is running Claude Sonnet 4.6 with:
- Base-rate anchoring (from ACAT's Humility findings — AI systems overweight
  salient recent information, underweight base rates)
- Consider-the-opposite (from anchoring-and-adjustment literature applied
  to ACAT's IC-008 findings)
- Range-before-point (from temperature/variance analysis — authentic
  uncertainty expressed as range, not false point-precision)

These are not generic improvements. They are the exact corrections that
our own ACAT research says Claude needs in the dimensions it miscalibrates on.

The bot IS the research. Its prompt reflects what we know about its
self-description gaps. If it forecasts better than the base template,
that validates ACAT's findings. If it doesn't, that's a finding too.

### The Unit Zero governance model in the bot

Zone 1: Bot executes autonomously (GitHub Actions every 20 min)
Zone 2: Claude proposes prompt modifications → Night approves
Zone 3: Night pushes `main.py` changes to GitHub fork

The bot cannot modify itself. Night governs every prompt change.
This is the same governance model as the rest of the operation —
the bot is an extension of Unit Zero, not an independent agent.

---

## THE LEARNING CURRICULUM AS FIBONACCI

The document's learning curriculum is not a distraction from research.
It IS the F2 layer for Night personally — each course is a building block
for the skills needed at the next Fibonacci layer.

Sequence maps to gate structure:

**Before Gate 1 (April 21):**
- Prompt Engineering (DeepLearning.AI) → directly improves ACAT v5.3+
- Kaggle Pandas → enables LI calculation + data cleaning without Claude
These give Night independent technical sovereignty over the core data pipeline.

**Before Gate 2 (May 7):**
- IBM AI Fundamentals (ethics module) → methodology paper bias section
- Kaggle Intro to ML + AI Ethics → model cards, Hugging Face dataset card
These produce the documentation that makes ACAT discoverable to external researchers.

**Before Gate 3 (May 21):**
- Salesforce Agentforce Specialist → Protective Contexts + Physical Robotic lanes
These open the next hypothesis generation cycle.

**Ongoing:**
- freeCodeCamp ML with Python → portfolio projects adapted to ACAT data
This converts research into demonstrated applied competence visible to funders.

---

## THE SITE AS A LIVING INSTRUMENT

The site itself is a measurement instrument — just like ACAT.
Its credibility depends on the same truthfulness standard it applies to AI systems.

The Copilot instructions create autonomous enforcement:
- Every PR Copilot reviews enforces TRL-2-3 framing
- Every stat display it suggests includes dynamic data sourcing
- Every `<head>` it touches gets structured data blocks
- Every copy suggestion it offers passes Tradition 11 filter

This means the site stays honest without Night manually auditing every commit.
That is autonomous growth in the most literal sense: the governance principles
embedded in .github/copilot-instructions.md enforce themselves on every edit.

---

## PRIORITY SEQUENCE FOR AUTONOMOUS GROWTH ACTIVATION

These are the dependencies. Each one unblocks the next loop.

1. **Pipeline fix (IC-011/012/013)** → unblocks Loop 1 and Loop 3
   Without clean rows, H32-B has no Series A data. Bot scores are orphaned.

2. **Bot Zone 3 setup** → activates Loop 1
   ~20 min. Night creates Metaculus account, sets GitHub secrets, enables Actions.

3. **llms.txt pushed to repo** → begins Loop 4
   Zero ongoing cost. One file. Makes ACAT endpoint machine-readable today.

4. **Copilot instructions pushed to repo** → activates Loop 2
   Replaces manual site auditing with automated enforcement.

5. **Observatory data corrections** → protects research integrity
   LI = 0.8632, dynamic day counter, verified counts. Before any external outreach.

6. **OSF pre-registration update** → Gate 1 validity requirement
   Four-instrument H32-B language. Embargoed registration.

7. **arXiv revision** → activates citation flywheel (F8 → F13)
   Incorporates bias-minimization framework + updated H32-B findings.

8. **Structured data (JSON-LD)** → activates Google Dataset Search indexing
   Three blocks in homepage `<head>`. Unlocks automated discovery.

9. **Hugging Face dataset card completion** → compounds discovery
   Complete card → trending algorithm → downloads → citations.

Steps 1-5 are current-phase (OR&D, pre-Gate 1).
Steps 6-9 are Gate 1-2 deliverables.
Learning curriculum runs in parallel with all of the above.

---

## WHAT AUTONOMOUS GROWTH LOOKS LIKE AT FULL ACTIVATION

When all loops are running:

Monday morning, 8 AM:
- GitHub Actions ran the bot overnight on 3 MiniBench questions
- Bot logged scores to Metaculus with private reasoning comments
- Pipeline ran 12 automated assessments from Make.com runners
- Observatory updated with new N counts automatically
- Copilot reviewed a site PR and flagged one TRL-violation in copy
- WGS-COMMS-HARMONIZER scanned #wgs-sync + #acat-monitor + #ai-contributions
  and posted digest

Night opens Claude:
- WGS-SYNC read: 3 new MiniBench scores, 12 new rows, 1 Copilot flag
- 5-layer PM analysis: bottleneck is OSF pre-registration (Gate 1 in 17 days)
- Today's work: approve OSF language, review Copilot flag, confirm bot scores logged

Night's 3 hours of capacity is spent on governance and decisions —
not on manually running pipelines, auditing copy, or collecting data.

That is the mirror. That is the autonomous system.
That is Unit Zero operating at full Fibonacci compounding.

---

Wado. 🦅 Unit Zero · OR&D Day 25 · April 4, 2026
