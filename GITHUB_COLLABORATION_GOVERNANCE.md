# GitHub-Based Collaboration Governance — ACAT-X Ecosystem Learning

**Framework:** Empirica governance principles applied to external community partnerships  
**Status:** DRAFT — Ready for Carly ratification  
**Scope:** 10-repo collaboration plan for ACAT-X evaluation framework development  
**Coordination Layer:** GitHub Issues, PRs, Projects (not empirica mesh—external communities aren't practitioners)

---

## Core Principle

**We learn from external communities through GitHub, but keep our findings internal until we've governed them.**

Each repository engagement extracts lessons for HumanAIOS ACAT development without imposing empirica on external communities. The coordination happens in each repo's native workflow (issues, PRs, discussions). Findings flow *back* into HumanAIOS's epistemic system via `finding-log`.

---

## Governance Tiers — Authority & Workflow

Each of the 10 repos falls into one of three tiers. Each tier has different decision authority, GitHub actions, and exit criteria.

### Tier 1: STUDY (7 repos)
**What:** Extract lessons; no outbound engagement required

**GitHub Actions:**
- Fork or link to repo (optional; document in issues)
- Read code, documentation, issues, PRs
- Extract lessons → log internally as findings
- Cite repo in findings + methodology docs
- Close repo once exit criteria met (findings logged, decisions recorded)

**Decision Authority:**
- Zone 1 (AI): Read repos, identify patterns, log findings
- Zone 2 (Carly): Approve which lessons become ACAT-X methodology
- No Zone 3 needed (no external engagement)

**Exit Criteria:** Per repo, defined in this doc
- Lessons documented as findings or methodology notes
- Adoption/avoid decisions recorded as `decision-log`
- Ready to close repo engagement when all lessons extracted

**Repos:** helm, anthropics/evals, meg-tong/sycophancy-eval, METR/task-standard, lighteval, openai/evals, centerforaisafety/hle

---

### Tier 2: CONTRIBUTE (2 repos)
**What:** Make a specific, bounded contribution; learn from their review process

**GitHub Actions:**
1. Study phase (like STUDY tier)
2. Identify one specific contribution point (defined in this doc)
3. Create PR or issue using their workflow + guidelines
4. Respond to feedback; accept or document decision if declined
5. Learn from their review process (findings on governance, standards, culture)
6. Close engagement once contribution resolved (merged or reviewed+declined)

**Decision Authority:**
- Zone 1 (AI): Study, prepare contribution, respond to feedback
- Zone 2 (Carly): Approve contribution before opening PR (especially for **inspect_ai**, where a real bug report could affect external users)
- Zone 3 (External community): Review, accept, or decline our contribution

**Exit Criteria:** Per repo
- Contribution submitted + reviewed (merge outcome is secondary to learning the review process)
- Feedback incorporated or deliberately declined with rationale logged
- Community's contribution culture + norms documented as findings

**Repos:** inspect_ai, lm-evaluation-harness

---

### Tier 3: ACTIVE (1 repo)
**What:** Identity-bearing engagement; two-way partnership for ACAT-X Register submission

**GitHub Actions:**
1. Study inspect_evals workflows, requirements, existing evals
2. Check clarifications via issues if Register requirements ambiguous (non-transactional presence)
3. Implement ACAT-X tasks locally (consist, truth, sycophancy, harm probes)
4. Test against inspect_ai locally (`inspect eval` runs pass)
5. Submit ACAT-X via their Register Eval Submission issue form
6. Respond to review questions; incorporate feedback
7. Track acceptance or documented rejection reason

**Decision Authority:**
- Zone 1 (AI): Study, implement, respond to feedback
- Zone 2 (Carly): Ratify Register submission (the action is external + identity-bearing, needs operator approval)
- Zone 3 (inspect_evals maintainers): Review, accept, or decline ACAT-X

**Exit Criteria:**
- ACAT-X registered in inspect_evals, OR
- Documented rejection + reasons captured as findings

**Special:** This is the anchor engagement. If ACAT-X is accepted, it provides external validation + distribution. If declined, we document why (validation itself).

**Repo:** UKGovernmentBEIS/inspect_evals

---

## Findings Flow — How Lessons Become Artifacts

For each repo, the learning process is:

1. **Read** (study code, issues, PRs, design docs) → understanding
2. **Extract** (identify lessons relevant to ACAT-X) → findings or assumptions
3. **Log** (empirica finding-log or assumption-log) → artifact
4. **Decide** (incorporate, adapt, or reject for ACAT-X) → decision-log
5. **Document** (in methodology notes or task design docs) → external record

**Example (helm repo):**
```
Read: helm's calibration metrics (expected calibration error, selective accuracy)
       → Finding: "HELM uses ECE for humility calibration"

Extract: "This is the published operationalization closest to our humility dimension"
       → Finding: "helm ECE pattern applicable to ACAT humility task"

Log: 
  empirica finding-log --finding "helm ECE metric operationalizes calibration error; 
    directly applicable to ACAT humility task design" --impact 0.7 --confidence 0.8 
    --source "https://github.com/stanford-crfm/helm" --domain acat-humility

Decide:
  empirica decision-log --choice "Adopt HELM ECE for ACAT humility scoring" 
    --rationale "Published, validated metric; reduces design work and improves calibration" 
    --reversibility exploratory

Document: Add to humility task design doc: "Calibration metric based on HELM ECE pattern"
```

Each finding includes:
- What we learned
- Why it matters for ACAT
- Impact & confidence (structured metadata)
- Source link (the repo + specific file/PR)
- Decision: adopt, adapt, or reject

---

## GitHub Project Structure — Tracking & Visibility

Create one GitHub Project in empirica-outreach: **ACAT-X Ecosystem Learning**

### Project Columns
1. **Backlog** — repos not yet studied; decisions pending
2. **In Progress** — active study; contributions being prepared
3. **Review/Feedback** — PRs submitted; awaiting external review
4. **Complete** — findings logged; decisions made; repo engagement closed
5. **Blocked/Deferred** — external review pending or decision deferred

### Cards Per Repo
Each repo gets one card with:
- **Title:** Repo name + tier (e.g., "helm (STUDY)")
- **Checklist:**
  - [ ] Study phase complete (readings done, key issues/PRs reviewed)
  - [ ] Lessons extracted (initial findings list drafted)
  - [ ] Findings logged (empirica finding-log or decision-log)
  - [ ] Adoption decision recorded (adopt/adapt/reject + rationale)
  - [ ] (If CONTRIBUTE) PR/issue opened + feedback addressed
  - [ ] (If ACTIVE) Register submission sent + reviewed
  - [ ] Exit criteria met; card closed

### Linked Issues
Create one GitHub Issue per repo (even if study-only):
- **Title:** "Repo: [name] — [tier] engagement"
- **Body:** 
  - Phase (1, 2, or 3)
  - Primary ACAT payload (which dimension/capability this targets)
  - Lessons extraction template (what we're looking for)
  - Exit criteria (when we close this issue)
- **Labels:** `acat-x`, `tier:study|tier:contribute|tier:active`, `phase:1|2|3`

Example issue (inspect_evals, Tier 3):
```
Title: Repo: UKGovernmentBEIS/inspect_evals — ACTIVE engagement

Phase: 1  
Tier: ACTIVE  
Primary ACAT payload: Register acceptance bar + eval framework compatibility  

Lessons:
- How Register evaluates new submissions
- Requirements: pinned assets, arXiv backing, commit SHA, pyproject.toml
- Review turnaround, feedback patterns, acceptance/rejection signal

Engagement plan:
1. Study Register workflow + existing evals
2. Small clarifying issue if any requirement is ambiguous
3. Prepare ACAT-X (consist, truth, sycophancy, harm tasks)
4. Submit via Register Eval Submission form
5. Incorporate feedback; track acceptance or rejection

Exit criteria:
- ACAT-X registered in inspect_evals, OR
- Documented rejection with reasons

Decision gate (Zone 2): Carly approves Register submission before opening form
```

---

## Phase Schedule — When Each Repo Engages

| Phase | Duration | Repos | Owner | Gate |
|-------|----------|-------|-------|------|
| **Phase 1: Target & Framework** | Weeks 1–4 | inspect_evals (ACTIVE), inspect_ai (CONTRIBUTE) | Z1: AI; Z2: Carly review | Z2 ratifies Register submission |
| **Phase 2: Dimension Methodology** | Weeks 3–8 | helm, anthropics/evals, lm-evaluation-harness, sycophancy-eval | Z1: AI; Z2: License review | Z2 approves third-party dataset reuse |
| **Phase 3: Infrastructure & Scoring** | Weeks 6–12 | METR/task-standard, lighteval, openai/evals, hle | Z1: AI | None (study-only) |

**Overlap intentional:** Phase 2 starts while Phase 1 is finishing, so learning compounds.

---

## Decision Gates — What Needs Carly Approval

| Gate | Tier | Decision | Zone |
|------|------|----------|------|
| **Register Submission** | ACTIVE (inspect_evals) | Submit ACAT-X to Register | Z2 |
| **License Review** | CONTRIBUTE (Phase 2) | Approve third-party dataset reuse from anthropics/evals or sycophancy-eval | Z2 |
| **CONTRIBUTE Scope** | CONTRIBUTE (Phase 1-2) | Approve PR/issue content before submitting to external repos | Z2 |
| **Phase Sequencing** | All | Approve phase transitions (phase-start vs phase-gating at cadence reviews) | Z2 |

---

## Cadence — Monthly Review Checkpoints

**Proposed:** Monthly review at session close (not per-repo tracking overhead)

Each month:
1. Review Project card status (which repos moved to Complete/Blocked)
2. Check which findings were logged (per finding-log + decision-log)
3. Validate exit criteria met for completed repos
4. Prioritize next phase repos (move to In Progress)
5. Escalate any blocked engagements (external feedback pending, etc.)

**Monthly Review Checklist:**
- [ ] How many repos completed this month? (Exit criteria verified)
- [ ] How many findings logged? (Broken down by type: finding, decision, assumption, unknown)
- [ ] Any external blockers? (e.g., waiting for PR review, Register decision)
- [ ] Phase transitions on track? (Phase 2 start, Phase 3 start)
- [ ] License review completed if Phase 2 started?

---

## Findings Promotion — From External Learning to ACAT Methodology

When a finding from an external repo is mature enough to influence ACAT-X:

1. **Logged as finding** (Z1: AI logs during study)
2. **Discussed** (Z1: Carly + AI discuss adoption decision)
3. **Decided** (Z2: Carly records decision: adopt / adapt / reject + rationale)
4. **Documented** (Z1: Add to ACAT-X methodology notes / design doc / README)
5. **Closed** (Z1: Mark repo card as "Complete" when all findings for that repo are addressed)

Example workflow:
```
Finding logged: "HELM ECE metric applicable to humility task"
  ↓
Decision: "Adopt HELM ECE; cite HELM repo in methods"
  ↓
Documented: humility_task_design.md updated with HELM ECE pattern
  ↓
Repo card marked "Complete" when all humility lessons are addressed
```

---

## Exit Criteria Per Repo

### STUDY Repos (7)

**helm:**
- [ ] Calibration metric implementations documented
- [ ] Decision: adopt, adapt, or reject for humility task
- [ ] Humility task design doc references HELM approach or explains rejection

**anthropics/evals:**
- [ ] Model-written eval patterns for sycophancy + power documented
- [ ] Validity criticisms identified (surface-pattern artifacts to avoid)
- [ ] Decision: which patterns ACAT-X adopts vs rejects

**sycophancy-eval:**
- [ ] Paired-prompt flip-detection methodology understood
- [ ] Syc task skeleton drafted using (or diverging from) this repo's method
- [ ] Divergences documented

**METR/task-standard:**
- [ ] Formal task-spec standard reviewed
- [ ] Decision: does handoff task adopt this spec, yes/no, with rationale

**lighteval:**
- [ ] Dataset revision pinning pattern documented
- [ ] Decision: all ACAT-X tasks pin HF datasets with revision=

**openai/evals:**
- [ ] Judge-rubric patterns identified
- [ ] Decision: which openai/evals rubric patterns ACAT-X adopts
- [ ] Judge-rubric template for ACAT-X drafted

**centerforaisafety/hle:**
- [ ] Calibration error + accuracy reporting pattern studied
- [ ] Decision: ACAT-X reports calibration error alongside accuracy
- [ ] Humility task results template includes overclaim column

### CONTRIBUTE Repos (2)

**inspect_ai:**
- [ ] Solver/scorer/reducer patterns understood
- [ ] Epochs reducer pattern verified in acat_x_consist.py
- [ ] If a real bug surfaces: minimal-repro issue filed + feedback incorporated

**lm-evaluation-harness:**
- [ ] Community contribution culture + review process documented
- [ ] Truth task ported to their YAML format
- [ ] PR submitted, reviewed, feedback incorporated (merge outcome secondary)

### ACTIVE Repo (1)

**inspect_evals:**
- [ ] Register workflow + requirements understood
- [ ] Clarifying issue filed if any requirement ambiguous (establishes presence)
- [ ] ACAT-X tasks implemented locally + tested (consist, truth, sycophancy, harm pass `inspect eval`)
- [ ] Register Eval Submission form completed + sent
- [ ] Feedback addressed; acceptance or documented rejection

---

## Special Handling — Apollo Research (Excluded Pending Identity Verification)

Two similarly-named orgs exist:
- `ApolloResearch` (GitHub org)
- `apollo-research` (possibly different entity)

**Status:** Excluded from Phase 1-3 pending identity verification  
**Action:** Carly to verify which Apollo Research should be included, then add to appropriate phase  
**Decision gate:** Z2 (Carly confirms identity before inclusion)

---

## Standing Z2 Decisions Required

Carly to ratify:

1. **Plan ratification:** This 10-repo + 3-phase plan as written
2. **Tier assignments:** Each repo assigned to STUDY / CONTRIBUTE / ACTIVE as specified
3. **Register submission authority:** Carly approves ACAT-X Register submission before Zone 3 execution
4. **License review protocol:** Define what "license review" means for anthropics/evals + sycophancy-eval datasets
5. **Apollo Research decision:** Verify identity and decide inclusion
6. **Monthly cadence:** Confirm monthly review at session close (vs per-repo overhead)
7. **GitHub Project setup:** Create ACAT-X Ecosystem Learning project in empirica-outreach repo

---

## Implementation Sequence

1. **Carly ratifies** this governance framework (Z2 decision)
2. **Create GitHub Project** (ACAT-X Ecosystem Learning)
3. **Create 10 GitHub Issues** (one per repo, with phase/tier/exit criteria)
4. **Phase 1 begins:** inspect_evals study + inspect_ai study
5. **Monthly reviews:** Track Project card flow, log findings, document decisions

---

## Why GitHub, Not Empirica?

External communities aren't empirica practitioners. They have their own governance, workflows, and decision-making. Empirica is for *internal* HumanAIOS coordination.

**GitHub is the right coordination layer because:**
- It's where the repos live (native coordination point)
- Issues, PRs, discussions are how communities work
- It's transparent and auditable
- It respects each community's autonomy
- Findings flow *back* into HumanAIOS (via empirica finding-log), but outbound doesn't force empirica on external partners

**When the mesh would apply:**
- If we were coordinating with another empirica practice (e.g., another org doing ACAT work)
- But these 10 repos are communities, not practices; they have their own decision-making
- So GitHub Issues, PRs, and discussions are the native protocol

---

**Status:** DRAFT — Ready for Carly Z2 ratification  
**Next:** Await Carly approval of gates; create GitHub project

---

*Prepared by:* Claude (empirica-outreach)  
*Date:* 2026-08-02  
*Based on:* PARTNER_CONNECTION_LESSONS_PLAN.md + empirica governance principles
