# Phase 1 Kickoff — ACAT-X Ecosystem Learning (Weeks 1–4)

**Date:** 2026-08-02  
**Status:** Infrastructure ready; Phase 1 active  
**Owner:** Carly Anderson (Z2)  
**Timeline:** Aug 2 - Aug 30 (4 weeks)

---

## What's Deployed

### Labels (Created)
- `acat-x` — ACAT-X evaluation framework work
- `tier:study` — STUDY tier (extract lessons, no engagement)
- `tier:contribute` — CONTRIBUTE tier (one PR/issue, learn process)
- `tier:active` — ACTIVE tier (two-way engagement)
- `phase:1`, `phase:2`, `phase:3` — Phase markers

### Issues (All 10 Created)

| # | Repo | Tier | Issue | Status |
|---|------|------|-------|--------|
| 1 | UKGovernmentBEIS/inspect_evals | ACTIVE | #41 | Backlog → In Progress |
| 2 | anthropics/inspect_ai | CONTRIBUTE | #42 | Backlog → In Progress |
| 3 | stanford-crfm/helm | STUDY | #43 | Backlog (Phase 2 start) |
| 4 | anthropics/evals | STUDY | #44 | Backlog (Phase 2 start) |
| 5 | EleutherAI/lm-evaluation-harness | CONTRIBUTE | #45 | Backlog (Phase 2 start) |
| 6 | meg-tong/sycophancy-eval | STUDY | #46 | Backlog (Phase 2 start) |
| 7 | METR/task-standard | STUDY | #47 | Backlog (Phase 3 start) |
| 8 | huggingface/lighteval | STUDY | #48 | Backlog (Phase 3 start) |
| 9 | openai/evals | STUDY | #49 | Backlog (Phase 3 start) |
| 10 | centerforaisafety/hle | STUDY | #50 | Backlog (Phase 3 start) |

---

## Phase 1: Target & Framework (Weeks 1–4)

### Active Repos (Start Immediately)

**#41 — inspect_evals (ACTIVE)**
- Study Register workflow + requirements
- Implement ACAT-X tasks (consist, truth, sycophancy, harm)
- Test locally against inspect_ai
- **Decision Gate:** Carly approves Register submission
- **Timeline:** Weeks 1–4
- **Exit Criteria:** ACAT-X submitted or documented rejection

**#42 — inspect_ai (CONTRIBUTE)**
- Study solver/scorer/reducer patterns
- Verify Epochs reducer in acat_x_consist.py
- File minimal-repro issues IF real framework gaps surface
- **Timeline:** Weeks 1–4
- **Exit Criteria:** Framework understood; any real gaps filed

### Staged for Phase 2 (Week 3+)

**#43–#46** — Dimension Methodology repos
- Start Week 3 (overlaps Phase 1 end)
- Extract patterns for humility, sycophancy, power dimensions
- **Decision Gate:** Z2 license review for datasets (anthropics/evals #44, sycophancy-eval #46)

---

## Monthly Review Cadence

**When:** End of month (Aug 30, Sept 30, etc.)  
**Duration:** 30 min  
**Agenda:**
1. Project card review (which repos completed?)
2. Findings summary (how many findings logged? by type?)
3. Blockers (any external review pending?)
4. Next phase readiness (Phase 2 start? Phase 3 start?)
5. Apollo Research decision (if not yet ratified)

**Outcome:** Move completed cards to "Complete" column; update blocked cards with latest status

---

## Week-by-Week Rhythm (Phase 1)

### Week 1 (Aug 2–8)
- Study inspect_evals Register workflow
- Study inspect_ai framework (solver/scorer/reducer)
- Implement consist task locally
- Create draft findings on Register requirements

### Week 2 (Aug 9–15)
- Continue consist + truth task implementation
- Add sycophancy + harm task skeletons
- File clarifying issue on inspect_evals if needed
- Begin Phase 2 prep: helm + anthropics/evals study

### Week 3 (Aug 16–22)
- Test ACAT-X tasks locally (consist, truth passing inspect eval)
- **START Phase 2** — helm + anthropics/evals study begins
- Prepare sycophancy + harm tasks for testing
- Log findings on Register requirements + patterns

### Week 4 (Aug 23–29)
- Final testing: all 4 ACAT-X tasks (consist, truth, syc, harm) pass inspect eval
- **Decision Point:** Carly approves Register submission
- Continue Phase 2: helm humility metrics + anthropics/evals patterns
- Log all findings + adoption decisions

### Week 5 (Aug 30) — Monthly Review
- Review Project card status
- Count findings logged (target: 8–12 findings from Phase 1)
- Confirm Phase 2 active; Phase 3 staged
- Ratify Apollo Research decision if pending

---

## Finding Extraction Process

**During study phase (each repo):**
1. Read code + docs → capture key patterns
2. Log as `finding` (e.g., "Register requires arXiv backing for evals")
3. Log adoption `decision` (e.g., "We will pin arXiv URL in ACAT-X submission")

**Example flow (inspect_evals #41):**
```
Reading Register docs
  → Finding: "Register requires 40-char commit SHA pinning for source code"
  → Decision: "ACAT-X will pin source repo commit SHA in submission"

Reading existing register evals
  → Finding: "Accepted evals use pyproject.toml + uv sync for reproducibility"
  → Decision: "Adopt pyproject.toml + uv sync for ACAT-X tasks"

Submitting ACAT-X
  → Finding: "Register review turnaround: ~2 weeks (observing trend)"
  → (Outcome logged after decision)
```

**Log frequency:** Aim for 1–2 findings per repo per week (8–12 total Phase 1)

---

## Z2 Decisions Still Needed

Before Phase 1 completes (by week 4):

1. **Register submission approval** (Week 4, issue #41)
   - Carly approves ACAT-X submission to inspect_evals
   - Trigger: "ACAT-X tasks pass local inspect eval; ready to submit"

2. **Apollo Research identity** (Before Phase 2 end)
   - Verify: ApolloResearch vs apollo-research identity
   - Decision: Include in Phase 2 or defer
   - Impact: May add to repo roster if identity confirmed

3. **Phase 2 license review** (Before week 3 end)
   - Gate: anthropics/evals #44, sycophancy-eval #46 dataset reuse
   - Action: Carly approves which datasets can be imported into ACAT-X

---

## Success Metrics (Phase 1 End)

By Aug 30:
- [ ] 10 issues open + labeled (✅ done)
- [ ] #41, #42 in "Complete" column (Register studied, ACAT-X submitted or decision documented)
- [ ] 8–12 findings logged (findings-log entries in project)
- [ ] 4–6 decisions recorded (decision-log entries)
- [ ] Phase 2 repos (#43–#46) moved to "In Progress"
- [ ] No blockers on external feedback (Register submission may be pending; that's OK)

---

## Next Steps (Right Now)

1. **Carly reviews this kickoff**
2. **Z2 gates registered** (Register submission gate in Week 4, License review gate in Week 3)
3. **Phase 1 starts** — Study inspect_evals + inspect_ai
4. **Daily/weekly progress** — Log findings as you go (not batched at end)
5. **Monthly review** — Aug 30 cadence check

---

## How to Track

**GitHub:**
- Browse issues by label: `acat-x` + `phase:1`
- Check issue status + comments for ongoing study notes

**Empirica:**
- Log findings: `empirica finding-log --finding "..." --source "https://github.com/..."`
- Log decisions: `empirica decision-log --choice "..." --rationale "..."`
- Track in project repo (this outreach project)

**Monthly Review:**
- Count findings logged (output from `empirica finding-list`)
- Check which issues moved to "Complete"
- Confirm next phase repos staged

---

## References

- Governance: `GITHUB_COLLABORATION_GOVERNANCE.md`
- Repo plan: `PARTNER_CONNECTION_LESSONS_PLAN.md`
- Sample task: `acat_x_consist.py`

---

**Phase 1 is GO. Start with #41 + #42.**

Issues are open, labels applied, next steps clear. Study inspect_evals + inspect_ai, extract patterns, log findings. Report back at monthly review (Aug 30).

---

**Created by:** Claude (empirica-outreach)  
**Date:** 2026-08-02  
**Status:** Ready for Phase 1 execution
