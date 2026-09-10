# Seed Publication Architecture

Complete automated system for publishing, collecting feedback, and versioning the **Seed Constitution for Responsible AI Development** across multiple surfaces (Substack, GitHub, website, Writable Wall, form).

Integrated with **HumanAIOS governance** (Z1 proposer, Z2 ratifier, Z3 executor) for transparent, audited amendment workflow.

---

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Seed Constitution v0.1 (Master Source)                      │
│ → seeds/seed-constitution-v0.1.md                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    ┌───▼────┐    ┌────▼────┐   ┌────▼──────┐
    │Substack│    │ GitHub  │   │ Website   │
    │Post    │    │ Issue   │   │ Page      │
    └────────┘    │Template │   └───────────┘
                  │& Tracker│
                  └─────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    ┌───▼──────────┐ ┌─▼────────┐ ┌──▼─────┐
    │ Writable Wall│ │ Form     │ │Observatory
    │ Submission   │ │ Response │ │ Note
    └──────────────┘ └──────────┘ └────────┘
                       │
        ┌──────────────┴──────────────┐
        │ Contribution Aggregator     │
        │ (weekly digest)             │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ Z1 Candidate Block          │
        │ (Claude proposer)           │
        │ → z1-inbox/YYYY-MM-DD/      │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ Z2 Ratification             │
        │ (Night / Carly)             │
        │ 48-hour decision window     │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ V0.2 Released               │
        │ (Updated, signed)           │
        └─────────────────────────────┘
```

---

## Directory Structure

```
operations/
├── seeds/                                 # Master seed directory
│   ├── seed-constitution-v0.1.md         # Current version (master source)
│   ├── seed-constitution-v0.2.md         # Next version (after ratification)
│   ├── CONTRIBUTION_GUIDE.md             # How to contribute
│   ├── CHANGELOG.md                      # Version history & changes
│   ├── substack-launch-post-template.md  # Substack post (ready to publish)
│   ├── site-page-v0.1.html              # Website page (ready to deploy)
│   ├── writable-wall-form.json           # Form config (ready to mount)
│   ├── observatory-framing-v0.1.md       # Research context note
│   │
│   ├── contributions/                    # Writable Wall submissions
│   │   └── {date}/{id}.json             # Structured amendments
│   │
│   ├── feedback/                         # Form responses
│   │   └── {date}/{response_id}.json    # Quick feedback
│   │
│   ├── summaries/                        # Aggregated digests
│   │   └── contributions-w{week}.md     # Weekly digest
│   │
│   ├── archive/                          # Historical versions
│   │   ├── v0.0-alpha.md
│   │   ├── v0.1.md
│   │   └── v0.2.md
│   │
│   └── templates/                        # Template files
│       ├── amendment-template.md         # What a good amendment looks like
│       ├── contribution-github.md        # GitHub issue instructions
│       └── version-announcement.md       # Release announcement template
│
├── seed-publication/                      # Automation system
│   ├── config.yaml                       # Master configuration
│   ├── orchestrator.py                   # Main automation engine
│   ├── README.md                         # This file
│   └── scripts/
│       ├── aggregate-feedback.py         # Collect & merge contributions
│       ├── emit-z1-candidate.py          # Create Z1 proposal
│       ├── sync-all-surfaces.py          # Publish to all platforms
│       └── check-z2-deadline.py          # Monitor ratification window
│
├── z1-inbox/                              # Governance submissions
│   └── {date}/
│       └── seed-amendment-{id}.md        # Z1 candidate blocks
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── seed-amendment.md            # GitHub amendment template
│   │
│   └── workflows/
│       ├── seed-publish.yml             # Trigger publication
│       ├── seed-aggregate.yml           # Weekly digest
│       └── z2-ratification-gate.yml     # Enforce governance gate
│
└── CODEOWNERS                             # GitHub CODEOWNERS for governance files
```

---

## Quick Start

### 1. **Initialize System**

```bash
cd /home/user/operations
python seed-publication/orchestrator.py --help
```

### 2. **Publish Current Version**

```bash
python seed-publication/orchestrator.py publish 0.1
```

This creates:
- ✓ GitHub commit with seed source
- ✓ Substack post template (ready to copy & paste)
- ✓ Website HTML page
- ✓ Writable Wall form config
- ✓ Observatory research note

### 3. **Collect Community Feedback**

```bash
python seed-publication/orchestrator.py aggregate-feedback
```

This:
- Scans GitHub Issues with [seed] label
- Reads Writable Wall submissions
- Compiles form responses
- Generates weekly digest

### 4. **Create Z1 Candidate**

```bash
python seed-publication/orchestrator.py emit-z1-candidate
```

This:
- Reads aggregated contributions
- Creates structured proposal block
- Places in z1-inbox/{date}/
- Ready for Z2 ratification

### 5. **Monitor Z2 Deadline**

```bash
python seed-publication/orchestrator.py check-z2-deadline
```

Reports:
- Pending decisions
- Overdue candidates
- Escalation needs

---

## Configuration

**File:** `seed-publication/config.yaml`

Key settings:

```yaml
surfaces:
  github:
    enabled: true
    repo: "humanaios-ui/operations"
    
  substack:
    enabled: true
    publication: "humanaios"
    post_template: "seeds/substack-launch-post.md"
    
  website:
    enabled: true
    domain: "humanaios.ai"
    paths:
      seed_page: "/seeds/constitution"
      writable_wall: "/contribute"

z_integration:
  z1_proposer: "Claude (AI agent)"
  z2_ratifier: "Night (Carly R. Anderson)"
  z2_email: "carly.r.anderson@gmail.com"
```

---

## Contribution Workflow

### From Contribution to Ratification

**1. Community Submits Feedback**

- Substack comments
- GitHub issues (with [seed] label)
- Writable Wall form
- Simple form

**2. Automated Aggregation** (weekly, or on-demand)

```bash
python seed-publication/orchestrator.py aggregate-feedback
```

Creates `seeds/summaries/contributions-w{week}.md` with:
- All contributions by platform
- Moderation status
- Pattern summary

**3. Z1 Proposes Amendment** (Claude)

```bash
python seed-publication/orchestrator.py emit-z1-candidate
```

Creates `z1-inbox/{date}/seed-amendment-{id}.md` with:
- Accepted contributions
- Rationale (why these changes matter)
- Falsifier (how we'd know this failed)
- Reference to community signal

**4. Z2 Ratifies or Contests** (Night)

Z2 decision window: **48 hours**

- ACCEPT → Amendment merged into v0.2, published
- EDIT → Z2 proposes changes, return for re-review
- REJECT → Rationale documented, Z1 can re-propose after 48h

All decisions logged in `REGISTERED.md` with hash signature.

**5. Version Released**

```bash
# Z3 executor after Z2 approval
python seed-publication/orchestrator.py publish 0.2
```

Updates all surfaces with v0.2:
- ✓ GitHub source commit
- ✓ Substack version announcement post
- ✓ Website page updated
- ✓ Changelog entry created
- ✓ REGISTERED.md updated

---

## Templates & Examples

### Contributing as a Human

See **[CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md)** for:
- When to use each platform
- What makes a strong amendment
- Examples of good vs. weak proposals
- Attribution expectations

### Contributing as an AI System

**Attribution requirement:** Every AI system contribution must include a **human principal**.

**Example:**
```
Submitted by: Claude AI agent (operated under Night's authority)
Proposition: [amendment text]
Human Principal: Carly R. Anderson (carly.r.anderson@gmail.com)
```

All AI contributions are logged in REGISTERED.md with explicit human-system attribution.

---

## Platform-Specific Details

### GitHub

- **Issues:** `[seed]` label auto-routes to amendment template
- **Discussions:** Lighter-weight for Q&A
- **Pull Requests:** Not direct; amendments are proposed via Z1 candidate, not PR
- **Audit trail:** All linked to version history via merge commits

**Creating an issue:**

```
1. Go to github.com/humanaios-ui/operations/issues
2. Click "New Issue"
3. Select "Seed Amendment or Critique"
4. Fill template (principle, proposed change, rationale, evidence, attribution)
5. Submit
```

### Substack

- **Post:** Publish launch post with links to other surfaces
- **Series:** Pin to "Living Documents" series
- **Comments:** Enabled; moderated for civility
- **Restacks:** Enabled; helps spread the word
- **Cross-promotion:** Light mention on @HumanAIOS Twitter, no heavy push

**Publishing:**

1. Copy `seeds/substack-launch-post-template.md`
2. Paste into Substack editor
3. Customize if needed (add post-specific opening, etc.)
4. Schedule or publish
5. Share link in GitHub, website, etc.

### Writable Wall

- **Endpoint:** `/api/seed/contributions`
- **Submission form:** Auto-generated from `config.yaml`
- **Fields:** change, rationale, evidence, attribution, contact
- **Moderation:** Automated relevance check + human review queue
- **Response:** Accepted submissions appear in weekly digest

### Website (humanaios.ai)

- **Seed page:** `/seeds/constitution` → `seeds/site-page-v{version}.html`
- **Contribute page:** `/contribute` → links to Writable Wall + all other paths
- **Homepage:** Single line + link (don't overload main page)
- **Versioning:** Keep v0.1 in archive; current version on main page

### Observatory

- **Location:** Research narrative in main Observatory
- **Content:** `seeds/observatory-framing-v{version}.md`
- **Purpose:** Connect Seed to ACAT dimensions and Moltbook high-friction work
- **Measurement:** Link to NF_LEDGER tracking community signal

---

## Automation & CI/CD

### GitHub Actions Workflows

**File:** `.github/workflows/seed-*.yml`

#### `seed-publish.yml` — Publication Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to publish (e.g., 0.2)'
        required: true

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: python seed-publication/orchestrator.py publish ${{ github.event.inputs.version }}
```

**Trigger:** Manual workflow dispatch or after Z2 ratification gate passes

#### `seed-aggregate.yml` — Weekly Digest

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday 8am UTC

jobs:
  aggregate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: python seed-publication/orchestrator.py aggregate-feedback
      - run: git add seeds/summaries/
      - run: git commit -m "chore: weekly digest"
      - run: git push
```

#### `z2-ratification-gate.yml` — Governance Gate

```yaml
name: Z2 Ratification Gate
on: [pull_request]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - name: Check Z2 Hash
        run: |
          if ! grep -q "z2_hash:" seed-constitution-*.md; then
            echo "❌ Missing Z2 ratification hash"
            exit 1
          fi
      - name: Verify Falsifier
        run: |
          if ! grep -q "falsifier:" z1-inbox/**/*.md; then
            echo "❌ Missing falsifier"
            exit 1
          fi
      - name: Validate Against ACAT
        run: python seed-publication/orchestrator.py validate-acat
```

---

## Versioning & Releases

### Version Naming

- **0.1, 0.2, 0.3…** = draft versions (open for feedback)
- **1.0** = first ratified, community-endorsed version
- **Dates in file names:** `seed-constitution-v0.1.md` (not `20260910`)

### Changelog

**File:** `seeds/CHANGELOG.md`

```markdown
## Version 0.2 (Planned)

**Status:** In Z2 ratification window  
**Ratified by:** Night (pending)  
**Date:** TBD

### Changes from v0.1

- **Principle 3 (Least-Privilege Agency):** Clarified "untrusted sources" to include other AI systems in same org
  - Proposed by: @alex-chen (Empirica Autonomy)
  - Evidence: Case study XYZ
  - Rationale: Observed in deployment where...

- **Principle 5 (Calibration and Humility Gate):** Added "independent audit" language
  - Proposed by: @morgan-xu
  - Evidence: [research link]

### Contributors (v0.2)

- Alex Chen (Empirica Autonomy Team)
- Morgan Xu
- Claude AI agent (under Night's authority)
```

### Archive & Preservation

Historical versions preserved in `seeds/archive/`:

```
archive/
├── v0.0-alpha.md
├── v0.1.md
├── v0.1-discussions.json
├── v0.2.md
└── v0.2-all-contributions.tar.gz
```

---

## Measurement & Analytics

### Tracking Community Signal

**File:** `seeds/reports/engagement-{week}.md`

Generated weekly:

```
Week 41 (Oct 7-13)
━━━━━━━━━━━━━━━━━━
Contributions:     42
├─ GitHub issues:  18
├─ Substack:       15
├─ Writable Wall:  7
└─ Form:           2

Platform diversity: 67% (good)
Average evidence quality: 4.2/5
Repeating themes:
  1. Clarify Principle 3 (3 mentions)
  2. Add AI-system attribution detail (2 mentions)
  3. Integration with ACAT dimensions (request)

Z2 decision quality: ✓ All within 48h
Next version readiness: 3 of 5 amendments ready
```

### Brier Score Tracking

As adoption grows, measure:
- How many organizations adopt the principles?
- Do their behaviors actually align with the text?
- Where is there gap/drift?

This feeds back into next version.

---

## Escalation & Disputes

### If a Contribution is Rejected

**Process:**

1. Z2 documents rationale in REGISTERED.md
2. Z1 notifies contributor
3. Contributor may re-propose after 48 hours (or new evidence)
4. If Z1 or community disputes Z2 decision → escalate to Admiral (Night)

### If Z2 Deadline Passes Without Decision

**Automatic escalation:**

1. 48h timer starts when candidate reaches REGISTERED.md
2. At 48h: CI gate shows warning
3. At 72h: Auto-escalate to Admiral (Night) with flag
4. At 96h: Candidate auto-rejected unless explicit Z2 approval

---

## Security & Compliance

### Required Checks

- ✓ Falsifier present on all Z1 candidates
- ✓ Attribution clear (human names or "AI + principal")
- ✓ No impersonation or false claims
- ✓ Z2 hash verification before merge
- ✓ ACAT cross-check on new principles

### Moderation Policy

**Writable Wall & Form:**
- Auto-reject: spam, off-topic, ATAT/violence, impersonation
- Manual review: vague language, low evidence
- Accept: specific amendments with rationale

**Substack Comments:**
- Light moderation: remove spam/abuse, keep substantive disagreement
- Feature best comments in weekly digest

**GitHub Issues:**
- Require template completion
- Mute duplicates (link to first)
- Pin high-signal issues

---

## Troubleshooting

### "Orchestrator won't run"

```bash
pip install pyyaml
python seed-publication/orchestrator.py publish 0.1
```

### "Contributions not appearing"

Check:
- Writable Wall submissions in `seeds/contributions/`
- Form responses in `seeds/feedback/`
- GitHub issues have `[seed]` label
- No moderation holds

### "Z2 deadline approaching"

```bash
python seed-publication/orchestrator.py check-z2-deadline
# Will show pending, overdue, escalation status
```

### "Version out of sync"

Regenerate all surfaces:

```bash
python seed-publication/orchestrator.py publish 0.1 --force-all
```

---

## Next Steps

1. **Z2 Approval:** Get this plan reviewed and signed by Night (Z2 ratifier)
2. **Go Live:** 
   - Commit seed source + templates to GitHub
   - Publish Substack post
   - Deploy website page
   - Announce on @HumanAIOS Twitter
3. **Monitor:** Weekly digests, Z2 deadlines, community signal
4. **Version 0.2:** Incorporate accepted amendments in 2 weeks

---

## Reference

- **Contribution Guide:** [CONTRIBUTION_GUIDE.md](./CONTRIBUTION_GUIDE.md)
- **GitHub Issue Template:** [.github/ISSUE_TEMPLATE/seed-amendment.md](../.github/ISSUE_TEMPLATE/seed-amendment.md)
- **Orchestrator Script:** [seed-publication/orchestrator.py](../seed-publication/orchestrator.py)
- **Configuration:** [seed-publication/config.yaml](../seed-publication/config.yaml)
- **HumanAIOS Governance:** [CLAUDE.md](../CLAUDE.md)
- **REGISTERED.md:** [z1-inbox/REGISTERED.md](../z1-inbox/REGISTERED.md)

---

**Maintained by:** HumanAIOS Governance Team  
**Last updated:** 2026-09-10  
**Status:** Ready for Z2 review and ratification

*Generated with [Claude Code](https://claude.ai/code)*
