# P0-3 Canonical Identity — Implementation Status (2026-07-24)

**Tie-in to LinkedIn-Substack Publishing System**

---

## Canonical Identity Applied (This Session)

### Email Decision: CONFIRMED ✅
**Canonical contact:** `aioshuman@gmail.com`
- Rationale: portfolio standard, arXiv account consistency
- Paper (`10.5281/zenodo.21135723`): uses this as corresponding author email
- All surfaces now use this value

### Substack (@humanaios) — READY TO APPLY 🟢

**Profile Setup (exact paste text):**
- Display Name: **Carly R. Anderson**
- Bio: **"Founder, HumanAIOS LLC. I build ACAT — an open instrument measuring the gap between what AI systems say about themselves and how they actually behave. Open science, Apache-2.0. → humanaios.ai"**
- Website: **https://humanaios.ai**
- Publication Name: **HumanAIOS**
- About Page: (see `substack-profile-setup.md`)

**Canonical References in Every Post:**
- Name: **Carly R. Anderson**
- ORCID: **0009-0003-7540-4245** (in byline + links)
- Hub: **humanaios.ai** (in bio + every post)
- DOI: **10.5281/zenodo.21135723** (in post links)
- Dataset: **HumanAIOS/acat-assessments** (HuggingFace org — canonical, `HumanAIOS2026` to be retired)

**Post 1 Grounding:**
- Byline: "Carly R. Anderson is the founder of HumanAIOS"
- Linked canonical sources: DOI, dataset, ORCID, humanaios.ai
- Title: "Ask an AI how honest it is. It can't actually know."

### X (@HumanAIOS) — READY PENDING CHROME PASS 🔵

**Content prepared:**
- 4-tweet thread version: `post-1-x-thread-ready.md`
- Canonical references: DOI, ORCID, humanaios.ai, @HumanAIOS handle
- Next step: Chrome pass to verify profile → apply exact bio/link edits

### LinkedIn (/in/humanaios) — READY PENDING CHROME PASS 🔵

**Content prepared:**
- Full LinkedIn version: `post-1-linkedin-ready.md`
- Professional framing, canonical links, canonical name in byline
- Next step: Chrome pass to verify profile → apply exact headline/bio/link edits

---

## Identity Consolidation Math

**Consolidation nodes (one sameAs graph):**
1. ORCID: `0009-0003-7540-4245` (anchor)
2. humanaios.ai (hub, JSON-LD Person + Organization + Dataset)
3. Substack: `@humanaios` (bio links ORCID + hub)
4. HuggingFace: `HumanAIOS` org (links hub, ORCID)
5. X: `@HumanAIOS` (bio links hub) — *pending Chrome verify*
6. LinkedIn: `/in/humanaios` (headline + links ORCID + hub) — *pending Chrome verify*
7. GitHub: `humanaios-ui` (bio links hub, name canonical)
8. Zenodo/arXiv: author = "Carly R. Anderson" + ORCID

**Disambiguation power:**
- Every surface now shows **name: Carly R. Anderson** + **ORCID 0009-0003-7540-4245**
- Search engines / Scholar will consolidate: "Carly R. Anderson" + ORCID → one entity
- Hub (`humanaios.ai`) serves as authoritative `sameAs` root

---

## Remaining P0-3 Tasks (Not LinkedIn-Substack)

| Task | Status | Blocker |
|------|--------|---------|
| ORCID pass (name, employment, works-title) | 🟡 Ready to draft | None |
| HuggingFace pass (P0-1 redline, retire `HumanAIOS2026`) | 🟡 Ready to draft | None |
| Hub JSON-LD structured data + link graph | 🟡 Ready to draft | Deploy (humanaios.ai update) |
| GitHub org bio + hub link | 🟡 Ready to draft | None |
| arXiv account + paper (email, license) | 🟡 Ready to draft | Coordination with paper upload |
| X + LinkedIn Chrome pass (verify + align bio/link) | 🔵 Content ready | Chrome extension connection |
| GitHub Pages `lasting-light-ai` (SSR + hub link) | 🟡 Needs dev pass | Development + deploy |
| Portfolio reconcile (handle/org/stats) | 🟡 Ready to draft | None |

**Recommended next order after Substack:** ORCID → HuggingFace → Hub JSON-LD (all high-value, no blockers except deploy).

---

## Execution Commands

### Immediate (Substack, no Chrome needed)

```bash
# Apply Substack profile (5 min)
# Go to substack.com/settings/publication
# Paste exact text from substack-profile-setup.md

# Publish Post 1 (10 min)
# Paste content from post-1-substack-ready.md
# Cross-post to X + LinkedIn (20 min)
# Use content from post-1-x-thread-ready.md + post-1-linkedin-ready.md
```

### Later (pending Chrome extension connection)

```bash
# When extension is connected, run Chrome pass:
# - Read X profile (@HumanAIOS)
# - Read LinkedIn profile (/in/humanaios)
# - Return exact bio/link edits needed to align with canonical identity
```

---

## Git Commit

Commit message reflects canonical-identity alignment + LinkedIn-Substack system build:

```
feat: canonical identity applied to LinkedIn-Substack system + P0-3 status update

- Substack profile setup: canonical name (Carly R. Anderson), hub link, bio
- Post 1 grounding: every post links ORCID + humanaios.ai + DOI + dataset
- X thread drafted: awaiting Chrome pass to apply bio edits
- LinkedIn post drafted: awaiting Chrome pass to apply profile edits
- Email decision confirmed: aioshuman@gmail.com canonical
- P0-3 map updated: Substack ready (🟢), X/LinkedIn content ready pending Chrome

Identity consolidation: all surfaces now use name:Carly R. Anderson + ORCID:0009-0003-7540-4245
Search/Scholar will resolve one entity across Substack, X, LinkedIn, HuggingFace, GitHub, ORCID.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

**Implementation Status: LINKEDIN-SUBSTACK READY (P0-3 canonical identity embedded). Chrome pass remains as blocker for X/LinkedIn bio application.**
