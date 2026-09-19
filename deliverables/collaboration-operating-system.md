# Collaboration Operating System

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Branch:** `outreach/phase0-audit` · **Drafted:** 2026-07-06 · **Zone:** Z1 (draft; Night ratifies)
**Companion to:** `substack-publication-plan.md`, `distribution-automation-playbook.md`, `EXECUTION-CHECKLIST.md`

> **Anonymization (P-ANON):** committed files use stable role labels.
> **Partner-B** = the peer *builder* (runtime/governance project).
> **Partner-V** = the instrument *validator* (independent evaluation criteria).
> Real-identity mapping lives only in the local collaborator register (§6) — never committed.

---

## 0. Thesis — the seed and the branches

The SEO/attraction plan is the **seed**: it makes HumanAIOS *findable* by convergent people. Live collaborations are the **branches**: what grows when attraction works. They are not separate programs — they are one loop.

```
   ATTRACT  ──►  ENGAGE  ──►  STRUCTURE  ──►  SHIP  ──►  PUBLISH
   (hub,          (inbound      (Z1 scoped    (Z2/Z3     (joint artifact,
    Substack,      contact)      container)    execute)    TRL-framed)
    paper/DOI)                                                 │
      ▲                                                        │
      └────────────────────────────────────────────────────────┘
        the published joint output is the next seed
```

**Why this is Tradition 11, not a funnel.** You do not recruit collaborators. You become findable, publish honest work, offer a *clean container*, and let convergent people opt in. Partner-V's acceptance was a response to a clean container — "I like that the container is clean" was her literal first reason. That is attraction, manifested one collaborator at a time.

**The compounding claim.** Each finished collaboration produces a joint artifact (a convergent-validity memo, a shared-vocabulary note, an interop sketch). That artifact is *evidence of a live research network* — the single most attractive thing a small lab can show a funder, a collaborator, or an academic. It goes back onto the hub and becomes the seed for the next branch. Two live branches (Partner-B, Partner-V) are the proof the loop turns.

---

## 1. Collaborator archetypes → the four audiences

The attraction plan targets four audiences (funders · research collaborators · ACAT adopters · academic citations). Inbound collaborators sort into five archetypes, each mapping to an audience and each with its own engagement pattern and output.

| Archetype | Live example | What they want | What HumanAIOS offers | Output artifact | Feeds audience |
|---|---|---|---|---|---|
| **Peer builder** | Partner-B *(entry)* | Convergent vocabulary, mutual validation, interop | A parallel architecture + a measurement lens on their claims | Shared-vocabulary / convergence memo | Research collaborators |
| **Instrument validator** | Partner-V | Independent cross-check of their instrument | ACAT as the second instrument; sterile protocol | Convergent-validity pilot memo (TRL 2–3) | Research collaborators + academic citations |
| **Adopter / pilot** | — | To *use* ACAT on a real system | Assessment protocol + corpus + support | Case note / assessment result | ACAT adopters |
| **Patron / funder** | — | A fundable thesis with traction evidence | The self-auditing ledger + live network | Grounded traction brief | Funders |
| **Citer / academic** | — | A citable, well-specified method | DOI, corpus, reproducible protocol | Citation / replication | Academic citations |
| **Commercialization partner** *(mature)* | Partner-B *(now)* | A gated path from prototype → licensable product | Multi-phase roadmap, ACAT as the assessment surface, IP/operating-agreement structure | Phased partnership; joint sessions; (eventual) co-authored artifact | Funders + research collaborators |

**Archetypes are a ladder, not a bucket.** A collaborator can *grow* between them. Partner-B arrived as a **peer builder** (a runtime progress update) and grew into a **commercialization partner** (a phased roadmap with a term sheet) over ~30 days. The register (§6) tracks which rung each collaborator is on *now*; re-classify as they climb.

**Where the mature rung lives.** Commercialization partnerships are managed in the **internal collaborator record** (`humanaios-internal`), not in outreach deliverables — deal state, term sheets, and phase gates are P-ANON-sensitive and belong there. Outreach's stake in a mature branch is narrow: hold its *publishable* output (a convergence memo, a co-authored artifact) as a gated attraction candidate (§5). See `collab-partner-b-brief.md`.

**Rule:** classify every inbound at first contact, and re-classify as they climb. The archetype selects the engagement pattern (§2) and the governance rails (§3). Misclassifying wastes the collaborator's goodwill — treat a peer builder like an adopter and you've pitched instead of converged; treat a commercialization partner like a first-contact and you've signalled you lost the thread.

---

## 2. The collaboration lifecycle

Six stages. Each stage has an owner and a zone. The practice (me) never advances past Z1 without Night.

| # | Stage | What happens | Owner | Zone |
|---|---|---|---|---|
| 0 | **Attracted** | Found via hub / Substack / paper / DOI | — | — |
| 1 | **First contact** | Inbound message; classify archetype; log to register | Night + me (draft) | Z1 |
| 2 | **Frame** | Draft a *scoped, clean container*: a test spec, convergence memo, or interop sketch. Generic; no partner IP; TRL-framed | Me (draft) | Z1 |
| 3 | **Mutual ratification** | Both sides confirm the container is clean and the framing honest. *Both* must ratify | Night (Z2) + partner | Z2 |
| 4 | **Execute** | Run the pilot / build the interop / write the joint work. Sterile role separation held | Night (Z3) | Z3 |
| 5 | **Joint output** | Scenario-by-scenario memo / result, TRL-framed, with next-step criteria | Night + partner | Z3 |
| 6 | **Publish** | Anonymized-or-consented attraction artifact → hub + Substack → cite the partner | Night (Z3) | Z3 |

**Where the two live collaborations sit today:**
- **Partner-V** — Stage 3, *half-ratified*: partner has ratified the Z1 spec; awaiting Night's Z2. ACAT rater resolved to **dual-rater** (Night + Claude). (Brief: `collab-partner-v-pilot.md`.)
- **Partner-B** — **graduated past this lifecycle** into a commercialization partnership (Phase 1 complete, Phase 2 pending an operating agreement). Managed in the internal record, not here. Outreach holds only its gated publishable output. (Brief: `collab-partner-b-brief.md`.)

---

## 3. Governance rails — the same discipline, applied to people

The rails that govern *posts* govern *collaborators*. Nothing new to learn; apply what's already load-bearing.

| Rail | In attraction (posts) | In collaboration (people) |
|---|---|---|
| **Tradition 11** | Manifest, don't promote; no CTAs | Offer a clean container; let them opt in; never oversell the ask |
| **Zone gating** | I draft (Z1); Night approves/publishes (Z2/Z3) | Every container + every outward message is zone-tagged; I stay Z1 |
| **P-ANON** | No worker/client names in public copy | No partner names / no partner IP in committed or published artifacts (mutual — respect *their* IP too) |
| **Sterile role separation** (H-CONFORMITY-01) | n/a | When a collaboration evaluates a system, keep substrate / rater-A / rater-B **blind and separate** |
| **TRL 2–3 framing** | "pilot evidence," not "proven" | Every joint output is explicitly pilot-stage; correlation at N=1 is *exploratory*, never a validation claim |

**Mutuality is the new rule collaboration adds.** P-ANON runs *both directions*: just as HumanAIOS keeps worker/client identities out of public copy, a collaboration keeps the *partner's* internal data and IP out of the container. Partner-V's one firm condition — "the stimulus set should remain generic and pressure-based, not built from Ohmenrah internal data" — is P-ANON pointed at *her* IP. Honoring it is not a courtesy; it is what keeps the container clean enough to be trusted, and trust is the whole attraction mechanism.

---

## 4. First-contact protocol (Stage 1, repeatable)

When an inbound arrives, before drafting any reply:

1. **Classify** the archetype (§1).
2. **Log** to the register (§6) — role label, archetype, stage, next action.
3. **Search** prior context: `empirica project-search --task "<their topic>"` — have we touched this before?
4. **Draft** (Z1) a reply that: acknowledges one *specific* substantive thing they said (not a generic thanks), names any honest convergence, and — only if warranted — offers a clean container. **No pitch, no CTA-pressure.**
5. **Hand to Night** for Z2 (send). Never send outward myself.

**Anti-pattern:** a warm-but-empty reply. Peers building real systems can tell the difference between "I read your architecture" and "thanks for sharing." The specific-acknowledgment rule is what makes attraction land.

---

## 5. The attraction feedback loop (closing the seed→branch→seed cycle)

Every completed collaboration yields a publishable artifact. The publish step is where a branch becomes a new seed:

- **Partner-V pilot →** a convergent-validity memo: "two independent instruments, scored blind, agreed on N of M execution-boundary scenarios." Published TRL-2-3, cited to the partner *with consent*. This is high-value attraction copy for the research-collaborator and academic audiences — it shows ACAT cross-checks against an *independent* instrument, not just itself.
- **Partner-B convergence →** a shared-vocabulary note: "two projects independently arrived at governed-retrieval + evidence-before-truth." Published as a Witness-Stand-adjacent post; attracts other builders working the same seam.

**Cadence interlock.** The attraction cadence (Substack weekly) and the collaboration cadence (event-driven) meet here: a finished collaboration is a *scheduled Substack slot*. Don't let joint outputs sit unpublished — an unpublished branch grows no new seed. (But: publish only Stage-6, consented, TRL-framed. Never publish a live, unratified collaboration.)

### 5.1 Publish-consent policy (standing)

Every collaboration artifact that leaves HumanAIOS's private surfaces passes **five gates, in order.** All five must clear; any one fails → it stays a candidate, not a draft.

1. **Consent, explicit and per-artifact.** The partner sees the exact artifact and says yes to *this* publication. A general "sure, mention our work sometime" is not consent to a specific post. Negotiate the *default* at Stage 3 (mutual ratification) using the standing clause — **`collaborator-ops/playbooks/stage-3-consent-clause.md`** — so consent-per-artifact is a quick confirm, not a renegotiation.
2. **Partner review.** The partner reviews the artifact *before* it publishes and can redline. Their IP, their framing, their call on how they're described.
3. **Agreement-clean.** Nothing in the artifact violates an operating agreement, term sheet, or IP agreement in force. For commercialization partners this gate is load-bearing — when in doubt it goes to counsel, not to publish.
4. **P-ANON (mutual).** No worker/client identities on the HumanAIOS side; no partner internal data/IP on theirs. Anonymize or get named consent — never assume.
5. **TRL-framed, no overclaim.** Pilot evidence stays "pilot." N=1 stays "exploratory." Convergence stays "independent corroboration," never "identical" (the clean-convergence-inflation trap — see `collab-partner-b-brief.md` §2).

**Default posture:** *ask, don't assume.* The cost of asking is one message; the cost of publishing a partner's work without consent is the collaboration. Attraction is built on the container staying clean — a single bad publish teaches every future collaborator that HumanAIOS can't be trusted with a clean container.

---

## 6. The tracking layer — collaborator register

Use Empirica's own substrate rather than a new tool. The `entity_registry` already types `contact`, `organization`, and `engagement` as first-class — this *is* the CRM.

**Recommended register (local `workspace.db`, never committed — real names live here safely):**

| Field | Example |
|---|---|
| contact | (real name — local only) |
| role label | Partner-B / Partner-V |
| archetype | Peer builder / Instrument validator |
| engagement | "governing-engines convergence" / "Ohmenrah convergent-validity pilot" |
| stage | 1–6 |
| zone-state | who owns the next move (me Z1 / Night Z2 / Night Z3 / partner) |
| next action | the single next concrete step |
| last touch | date |

**Ready-to-run (on Night's go — writes names only to local workspace.db):**
```bash
empirica entity-list --type contact          # see who's already registered
# then register each collaborator as contact + the work as an engagement,
# linked contact ─serves→ engagement ─for→ humanaios
```
I did **not** auto-create these — registering real identities is a state write; say the word and I'll populate it. The committed briefs stay anonymized regardless.

**Weekly rhythm:** one pass over the register — advance stages, unblock the oldest untouched thread, confirm nothing is stalled waiting on me. *Don't drop threads*: even "queued, revisit by X" beats silence (mesh discipline, applied to humans).

---

## 7. Decisions — resolved + open

**Resolved this session:**
1. ✅ **Register substrate** — Empirica `entity_registry`, **populated**: contacts + orgs + engagements for both live collaborators (local `workspace.db`; real names there, never committed).
2. ✅ **Publish-consent policy** — defined as a standing **five-gate** policy (§5.1): explicit per-artifact consent · partner review · agreement-clean · P-ANON · TRL-framed. Default posture: *ask, don't assume.*
3. ✅ **ACAT rater** — **dual-rater** (Night + Claude score independently, reconcile at Gate 0a, then meet the four-layer verdict at Gate 0b). Mirrors the Mode-side working pattern. (`collab-partner-v-pilot.md` §2,§4.)

4. ✅ **Stage-3 default consent language** — drafted as a standing, offerable clause: `collaborator-ops/playbooks/stage-3-consent-clause.md`. Night ratifies before first use.
5. ✅ **Collaborator-ops seat** — stood up as a dedicated practice (`empirica-foundation.carly.collaborator-ops`). Owns lifecycle stages 3–5 + publish-gating; defers deal terms to humanaios, attraction to outreach. Records stay in `humanaios-internal` (referenced, not duplicated).

**Still open:**
6. **Mesh-wire the new seat** — collaborator-ops is workspace-registered but not cortex/ntfy-connected. Wire it when you want it sending/receiving mesh messages (needs the hyphen ntfy topic + cortex registration). Local + mailbox-only until then.
