# GitHub Repo Verification Checklist
**empirica-foundation/acat — Aug 8, 2026**

---

## Pre-Launch Verification (Aug 8, 2026, Morning)

### ✅ Repository Configuration

- [ ] Repository exists: `empirica-foundation/acat`
- [ ] Repository is public (not private)
- [ ] Main branch is stable (no uncommitted changes)
- [ ] Branch protection rules in place (if needed)
- [ ] Default branch is set to `main`

### ✅ Essential Files Present

- [ ] `README.md` — Project overview + quick start
  - [ ] Includes ACAT headline concept
  - [ ] Links to TERMS_OF_USE.md
  - [ ] Links to /docs folder
  - [ ] Links to /examples folder
- [ ] `LICENSE` — Apache 2.0 license file
  - [ ] Copyright notice: "Copyright 2026 HumanAIOS LLC"
  - [ ] Full Apache 2.0 text included
- [ ] `TERMS_OF_USE.md` — Explicit licensing terms
  - [ ] Covers: forking, modification, commercial use, redistribution
  - [ ] Addresses: "Can I fork?" "Can I modify?" "Can I sell this?"
- [ ] `CONTRIBUTING.md` — Contribution guidelines
  - [ ] Issue report format specified
  - [ ] PR review process documented
  - [ ] Expected response time (48h for questions, 1w for PRs)

### ✅ Documentation Folder (/docs)

- [ ] `acat-framework.md` — Measurement methodology
  - [ ] 12 dimensions documented
  - [ ] Phase 1 + Phase 3 explained
  - [ ] Learning Index formula clear
  - [ ] Scoring rubric for each dimension
  - [ ] Measurement uncertainty explanation
- [ ] `zone-model.md` — Authority model
  - [ ] Zone 1/2/3 gates explained
  - [ ] Technical implementation examples
  - [ ] Drift signal triggers documented
  - [ ] Use cases + examples
- [ ] `drift-signals.md` — Signal catalog
  - [ ] D-* (authority) signals documented
  - [ ] IC-* (integrity) signals documented
  - [ ] E-* (execution) signals documented
  - [ ] Severity levels clear
  - [ ] Corrective actions specified

### ✅ Examples Folder (/examples)

- [ ] `single-practice-setup/` exists
  - [ ] `README.md` present
  - [ ] Python implementation guide included
  - [ ] Zone gate code (zone_1_gate, zone_2_gate, zone_3_gate)
  - [ ] Step-by-step setup instructions
  - [ ] Customization guidance

### ✅ Git History + Commits

- [ ] Recent commits are clean (no merge conflicts)
- [ ] Commit messages follow format: "feat/docs/fix: description"
- [ ] No sensitive data in git history (no API keys, credentials, emails)
- [ ] Git log readable (good commit messages, not "WIP" or "asdf")

### ✅ GitHub Settings

- [ ] Repo visibility: PUBLIC
- [ ] Issues enabled (for community questions)
- [ ] Discussions enabled (for "How do I apply ACAT?" threads)
- [ ] Wiki disabled (docs live in /docs folder, not wiki)
- [ ] Pages disabled (or points to correct location if enabled)
- [ ] Branch protection: main branch requires review (if strict)

### ✅ GitHub Features Ready

**Issues Tab:**
- [ ] Issue template created (or can file manually)
- [ ] Labels created: `acat-x`, `bug`, `enhancement`, `documentation`, `question`

**Discussions Tab:**
- [ ] Enabled for community questions
- [ ] Welcome template prepared (optional but recommended)
- [ ] Categories set: General, Ideas, Q&A

**Releases Tab:**
- [ ] Initial v0.9 release tagged (optional for launch day, but good to have)
- [ ] Release notes describe: ACAT framework, zones, drift signals

**README Badges (Optional but Professional):**
- [ ] Apache 2.0 license badge
- [ ] Latest release badge (if v0.9 tagged)
- [ ] "Auditable & Open-Source" badge (custom or text)

### ✅ Documentation Links

In README, verify all links point correctly:
- [ ] Link to TERMS_OF_USE.md ✓
- [ ] Link to /docs/zone-model.md ✓
- [ ] Link to /docs/drift-signals.md ✓
- [ ] Link to /docs/acat-framework.md ✓
- [ ] Link to /examples/single-practice-setup/README.md ✓
- [ ] No broken links (404s)
- [ ] No external URLs that might change

### ✅ Content Quality Review

**README Quality:**
- [ ] Headline is compelling and clear
- [ ] Problem statement is clear
- [ ] Solution is actionable
- [ ] Call-to-action is present (fork, try it, audit it)
- [ ] Code example included (if space allows)

**Documentation Quality:**
- [ ] Zone model is understandable to non-specialists
- [ ] Drift signals are clearly defined with examples
- [ ] Framework methodology is reproducible
- [ ] Scoring logic is transparent
- [ ] No jargon without explanation

**Examples Quality:**
- [ ] Setup guide is complete (can someone follow it?)
- [ ] Code is copy-paste ready
- [ ] Comments explain key sections
- [ ] Error handling included (or documented as TODO)

---

## Launch Day (Aug 9, 9am PT)

### Final Checks (30 minutes before public launch)

- [ ] Pull latest from origin (any last-minute fixes?)
- [ ] Verify all links still work (one final 404 check)
- [ ] Confirm /docs and /examples folders are accessible
- [ ] Check README renders correctly on GitHub
- [ ] Verify license is displayed correctly (GitHub auto-detects)

### Public Launch

- [ ] Repository made public (if it was private during prep)
- [ ] Repository link ready to paste in LinkedIn/Substack posts
- [ ] Link format: `https://github.com/empirica-foundation/acat`

### Post-Launch Monitoring (2 hours)

- [ ] Monitor Issues tab for questions (respond within 48h)
- [ ] Monitor Discussions for "How do I...?" threads
- [ ] Check GitHub traffic (visitors, clones, forks)
- [ ] Verify no immediate bug reports or broken links

---

## Success Criteria (Aug 9)

**Minimum viable launch:**
- [x] Repo is public
- [x] README + LICENSE + TERMS_OF_USE present
- [x] /docs folder has 3+ files (zone-model, drift-signals, acat-framework)
- [x] /examples folder has setup guide
- [x] No broken links
- [x] All external links work

**Stretch goals:**
- [ ] 50+ GitHub stars by Sept 30
- [ ] 20+ discussion threads (audit + implementation questions)
- [ ] 10+ forks (organizations adopting)
- [ ] 2+ external contributors (PRs with improvements)

---

## Troubleshooting (Common Issues)

| Issue | Cause | Fix |
|-------|-------|-----|
| README not rendering | Markdown syntax error | Check for unclosed code fences, link brackets |
| Links return 404 | File path wrong or file missing | Verify file exists, use relative paths |
| License not detected | File not named exactly "LICENSE" | Rename to LICENSE (all caps, no extension) |
| GitHub Actions failing | Workflows not configured | Can skip for open-source library (not needed) |
| Discussions not visible | Feature not enabled in settings | Enable in Repo Settings → Features |

---

## Sign-Off

**Repository verified by:** [Name/Date]  
**Status:** ✅ READY FOR PUBLIC LAUNCH  
**Confidence:** 0.95 (all items checked, no blockers)

---

**Next:** Proceed with LinkedIn/Substack publication (10am/11am PT)

**Monitor:** Check Issues + Discussions hourly for first 4 hours post-launch
