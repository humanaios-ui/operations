# Phase 1: GitHub Organization Setup

**Status:** READY TO CREATE  
**Timeline:** Week 1 (Aug 8-14)  
**Owner:** outreach  
**Blockers:** None (ACAT assessment on hold)

---

## Organization Structure

### Org Name
- **Name:** `empirica-research-bounties`
- **Description:** "Transparent, fair research task coordination — behavioral assessment + open accounting"
- **URL:** https://github.com/empirica-research-bounties
- **Visibility:** Public (all work transparent)

---

## Repositories

### 1. `tasks` (Main task board)
**Purpose:** Public task repository where employers post research bounties

```
empirica-research-bounties/tasks/
├── README.md (How to post a task + how to apply)
├── TASK_TEMPLATE.md (markdown template for new tasks)
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── task.md (GitHub Issue template for tasks)
├── projects/
│   └── Task Board (GitHub Projects board: Open → In Progress → Complete → Closed)
└── docs/
    ├── ELIGIBILITY.md (Who can post tasks, who can apply)
    ├── PAYMENT.md (How payment works, escrow via Open Collective)
    └── FAQ.md
```

**Workflow:**
1. Employer creates GitHub Issue using task template
2. Issue auto-populates: task title, budget, deadline, requirements, acceptance criteria
3. Issue appears on Project board (Open column)
4. Workers comment to apply (link GitHub profile + Substack portfolio if applicable)
5. Empirica closes Issue with selection comment (winner + runner-ups)
6. Payment processed via Open Collective
7. Issue moves to Complete column

### 2. `transparency-reports` (Monthly reporting)
**Purpose:** Public record of all matches, earnings, coordination fees

```
empirica-research-bounties/transparency-reports/
├── README.md (Reporting methodology + how to read reports)
├── reports/
│   ├── 2026-08-report.md (First pilot report: what we matched, worker earnings, our cut)
│   ├── 2026-09-report.md
│   └── ...
├── data/
│   └── aggregate-stats.json (JSON: total matches, total worker earnings, coordination fees)
└── templates/
    └── monthly-report-template.md (Markdown template for consistency)
```

**Monthly Report Contents:**
- Matches completed this month (count, total budget)
- Worker earnings (aggregate + anonymized individual outcomes)
- Coordination fee collected ($ amount + %)
- Verification bonus returned to workers ($)
- Platform costs (GitHub, Open Collective fees)
- Net revenue to empirica
- Qualitative: worker feedback, employer satisfaction, ACAT predictive signals
- Next month: forecast + any changes

### 3. `assessment` (On hold — ACAT methodology pending mesh feedback)
**Purpose:** Behavioral assessment design + validation (CREATED BUT LOCKED)

```
empirica-research-bounties/assessment/
├── README.md (PLACEHOLDER: Assessment design pending mesh feedback)
├── ACAT_LITE_DESIGN.md (DRAFT: 5-question behavioral fit assessment)
├── VALIDATION_PLAN.md (DRAFT: How we'll measure ACAT predictive validity)
└── BLOCKED_PENDING.txt (ACAT lite assessment frozen until humanaios validates)
```

**Note:** This repo exists but is NOT in use until humanaios provides methodology feedback.

### 4. `research-findings` (Public research journal)
**Purpose:** Document what we learn from Phase 1 pilot

```
empirica-research-bounties/research-findings/
├── README.md (How to interpret these findings)
├── monthly-findings/
│   ├── 2026-08-findings.md (Early patterns, lessons learned)
│   └── ...
├── worker-case-studies/ (With permission)
│   └── case-study-1.md (Optional: how a worker experienced the platform)
└── methodology/
    └── MATCHING_ALGORITHM.md (How we score worker-task fit)
```

---

## GitHub Projects Board (Task Management)

**Board name:** `Research Task Workflow`

**Columns:**
1. **Open** — New tasks posted, awaiting applicants
2. **In Progress** — Task assigned to worker, work underway
3. **Pending Payment** — Task complete, payment processing via Open Collective
4. **Complete** — Task paid, closed
5. **Cancelled** — Task withdrawn or no applicants

**Automation:**
- Issue created → auto-add to "Open" column
- Issue closed → auto-add to "Complete" column
- (Manual moves for In Progress / Pending Payment)

---

## Access & Permissions

**Organization members:**
- Owner: `carly.anderson` (empirica-outreach lead)
- Maintainers: outreach team (can manage issues, repos, settings)
- Public: Anyone can view, apply to tasks, read transparency reports

**Branch protection:**
- `main` branch locked (only maintainers can merge)
- All task posts reviewed before appearing (no spam)

---

## First Tasks (Sample Data for Pilot)

Create these as issues in `tasks` repo to test workflow:

1. **Task: "Analyze Research Ethics Review Process"**
   - Budget: $500
   - Deadline: 2026-09-01
   - Skills: Writing, research methodology, ethics background
   - Acceptance: 2000-word analysis of REB decisions for 10 sample cases
   - Employer: [fictional, for testing]

2. **Task: "Validate ACAT Assessment Reliability"**
   - Budget: $750
   - Deadline: 2026-09-15
   - Skills: Statistics, behavioral science, data analysis
   - Acceptance: Test report on consistency of ACAT grading across 5 raters
   - Employer: humanaios (internal)

3. **Task: "User Experience Testing for Orchestration Platform"**
   - Budget: $400
   - Deadline: 2026-09-05
   - Skills: UX research, attention to detail, communication
   - Acceptance: Usability report + video walkthrough feedback
   - Employer: [internal, for self-testing]

---

## Checklist: Week 1 Setup

- [ ] Create GitHub org `empirica-research-bounties`
- [ ] Create repos: `tasks`, `transparency-reports`, `assessment` (locked), `research-findings`
- [ ] Create GitHub Projects board `Research Task Workflow`
- [ ] Set branch protection on all repos (main locked)
- [ ] Create `.github/ISSUE_TEMPLATE/task.md` (task posting template)
- [ ] Write README for each repo
- [ ] Populate sample tasks (3 test cases)
- [ ] Share org link with mesh for feedback visibility
- [ ] Document: "How to post a task" + "How to apply" guides

---

## Success Criteria (Week 1-2)

✅ Public GitHub org created + configured  
✅ Task repos + board ready  
✅ Sample tasks visible (ready for Week 3 recruitment)  
✅ Transparency reporting structure in place  
✅ ACAT assessment repo created but locked (await mesh feedback)

---

**Status:** Ready to execute immediately (no mesh gate)  
**Estimated effort:** 4-6 hours (org setup, template creation, sample tasks)  
**Owner:** outreach infrastructure lead
