# HumanAIOS SEO/Attraction — Execution Checklist & Session State

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Branch:** `outreach/phase0-audit` · **Checkpoint:** 2026-07-02
**North star:** attraction, not promotion. One consolidated entity → all four audiences find you.

---

## ✅ Done (this collaboration)
- **Discoverability audit** + strategy; **canonical identity locked**; **license locked** (CC-BY-4.0 paper / Apache-2.0 code+data).
- **Zenodo preprint PUBLISHED** → DOI `10.5281/zenodo.21135723` (live, wired into all deliverables).
- **Substack publication plan** ("The Witness Stand") + growth-evidence strategy.
- **Post 1 (anchor)** and **Post 5 (mission bridge)** drafted.
- **Distribution system built**: `scripts/repurpose.py` (one post → 4 channels, format-only), Notes bank, Recommendations tracker, scheduler comparison, automation playbook.
- **RentAHuman**: leaked API key **rotated**; server-side **key-proxy spec**; Z1 **integration concept** (queued, gated).
- **Collaboration Operating System** built (attraction seed → collaboration branches): `collaboration-operating-system.md` (lifecycle, archetypes, governance rails, feedback loop, register) + two live-collaborator briefs — **Partner-B** builder (`collab-partner-b-brief.md`, reply drafted) and **Partner-V** convergent-validity pilot (`collab-partner-v-pilot.md`, half-ratified).

---

## 🟢 Ready to apply — drafts waiting on you
| Task | Draft | Note |
|---|---|---|
| ORCID edits | `p0-3-orcid-edits.md` | Do the Works auto-import now (Zenodo live) |
| HuggingFace card redline | `p0-1-corpus-fix.md` | ⚠️ Fix 4 needs the stats decision |
| Substack edits | `p0-3-substack-edits.md` | confirm publication name |
| GitHub edits | `p0-3-github-edits.md` | check user-vs-org first |
| Hub JSON-LD | `p0-3-hub-jsonld.md` | confirm logo/API URLs; needs a deploy |
| arXiv hold | `arxiv-hold-action-plan.md` | check TeX-source upload first; 2 emails ready |
| Zenodo References field | (in `p0-2` §ref / paper) | 9-item bibliography provided |
| Post 1 + Post 5 | `witness-stand-post-1.md`, `-5.md` | schedule via Substack when ready |

---

## 🌿 Live collaborations (the branches)
| Partner | Archetype | Stage | Waiting on | Next |
|---|---|---|---|---|
| **Partner-B** | Commercialization partner *(grew from peer builder)* | Phase 1 done / Phase 2 pending op-agreement | internal seat + counsel | Managed in `humanaios-internal`; outreach holds only the gated convergence artifact (`collab-partner-b-brief.md` §3) |
| **Partner-V** | Instrument validator | 3 (half-ratified) | **Night Z2** | Work Z2 checklist + approve stimulus set; ACAT = **dual-rater** (Night+Claude) (`collab-partner-v-pilot.md` §3,§5) |

**Metaculus bot** → plan + cost research + **AIB entry runbook** (`metaculus-management-plan.md`, `-cost-optimization.md`, `-aib-entry-runbook.md`). Entry = free sponsor credits (OpenRouter form) + tournament-mode deploy (eng). Supabase **authed + baselined**: `acat_forecast_runs`=**0 rows** — no track record yet (bot in test_questions mode). Track record *starts* at AIB tournament-mode deploy. Standing monitoring queries ready (`metaculus-monitoring-queries.md`). Still gated: Gate-3 (LI placeholder) before any ACAT-on-forecasting surfacing.

**Register populated** → Empirica `entity_registry` (contacts + orgs + engagements, local). **Publish-consent policy** → 5-gate standing policy (`collaboration-operating-system.md` §5.1) + offerable **Stage-3 consent clause** (`collaborator-ops/playbooks/stage-3-consent-clause.md`). **New seat:** `collaborator-ops` practice stood up (`~/practices/collaborator-ops`) — owns the collaboration *manage* half; mesh-wiring deferred to you.

## 🟡 Open decisions (only you)
1. **Canonical stats** — LI 0.87 (paper) vs 0.843 (card) vs 0.8632 (portfolio); N 629/608. *Gates HF Fix 4, portfolio reconcile, Posts 2–6.* Decide, or authenticate Supabase and I'll verify.
2. **"Magnifica Humanitas"** — confirm it's a real citable encyclical, or it's illustrative (gates Post 6).
3. **Canonical email** — `aioshuman@gmail.com` everywhere (+ fix the paper) or keep the paper's?
4. **Substack publication name**; **GitHub account type** (user/org).
5. **Collaboration register** — populate Empirica `entity_registry` (contacts + engagements) now? · **publish-consent** default? · **who plays the ACAT rater** in the Partner-V pilot? (see `collaboration-operating-system.md` §7)

---

## 🔵 Gated / blocked (not on my critical path)
- **RAH integration** — all outward/financial/migration steps **Z2/Z3-gated for Night** (Migration 006 unapplied; listings/hire/spend pending). I stay Z1.
- **Key proxy** — deploy is yours (infra + new secret); I can flesh out full `worker.js` on request.
- **X + LinkedIn** identity pass — needs the Claude browser extension connected.
- **Supabase** — needs your OAuth; then I verify canonical stats.
- **`lasting-light-ai`** indexation — needs SSR/prerender (dev).

---

## 📁 Deliverable index (`deliverables/`, branch `outreach/phase0-audit`)
`phase0-discoverability-audit.md` · `p0-1-corpus-fix.md` · `p0-2-zenodo-submission-pack.md` · `zenodo-api-helpers.md` · `arxiv-hold-action-plan.md` · `p0-3-canonical-identity-map.md` · `p0-3-orcid-edits.md` · `p0-3-substack-edits.md` · `p0-3-github-edits.md` · `p0-3-hub-jsonld.md` · `substack-publication-plan.md` · `witness-stand-post-1.md` · `witness-stand-post-5.md` · `distribution-automation-playbook.md` · `notes-bank.md` · `recommendations-tracker.md` · `scheduler-comparison.md` · `rah-integration-concept.md` · `rah-key-proxy-spec.md` · `collaboration-operating-system.md` · `collab-partner-b-brief.md` · `collab-partner-v-pilot.md` · `EXECUTION-CHECKLIST.md`
Plus: `scripts/repurpose.py`, `.mcp.json` (supabase + rentahuman).

---

## ▶ Resume points (pick any next session)
1. **Draft Post 2** — reconcile "When AI Rates Itself" to canonical stats (needs the stats call).
2. **Draft Post 4** — the self-correction pivot (your strongest differentiator).
3. **Full `worker.js` + `wrangler.toml`** for the key proxy.
4. **Apply the identity edits** (ORCID → HF → Substack → GitHub → hub JSON-LD).
5. When ready: authenticate **Supabase** (stats) / connect **Chrome** (X+LinkedIn).
6. **Ratify + send the Partner-B reply**; **work the Partner-V Z2 checklist** + approve the stimulus set (the two live branches).
7. **Populate the collaborator register** (Empirica `entity_registry`) on your go.

*State persisted: all work committed on `outreach/phase0-audit`; empirica goals/findings logged; umbrella goal `180abcc2` remains open.*
