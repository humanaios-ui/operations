# Q-BOOT-FINDINGS-SCAN-01 — Registry Candidate Block

**Status:** Z1 CANDIDATE — advisory, unratified. This block proposes; it does not register.
**Produced by:** `humanaios-findings-scan` (standalone invocation), Z1 (Claude)
**Date:** 2026-09-14
**Origin:** post-merge findings scan over PR #332 (`Q-BOOT-STATE-MACHINE-01`, merged `f0c0cec`)
**Routing:** all candidates → Zone 2 (Night) for ratification per **P21**

---

## Registry fetch (IC-030 hard gate)

| Source | Result |
|---|---|
| `REGISTERED.md` @ `raw.githubusercontent.com/humanaios-ui/operations/main` | **HTTP 200** · 4180 lines · 307,197 bytes · header `Last updated: August 15, 2026 (S-081526-NN)` |
| `SESSION_RITUALS.md` (live) | HTTP 200 · 439 lines · v6.4.1 |
| `GOVERNANCE.md` (live) | HTTP 200 · 309 lines · v6.4.3 |

**Staleness note.** At fetch time the working-copy `REGISTERED.md` (4147 lines) was **33 lines behind live**. Live carried `Q-BOOT-PROCESS-MAP-01`, appended the same day by a concurrent Z1 session (since merged as #330). Every cross-walk below is against the **live** file, not the working copy.

---

## Falsifier

**PREDICTION.** For each of `IC-CAND-BSM-A` and `IC-CAND-BSM-B`, a full-text search of the live canonical file at the cited location returns zero occurrences of the cited artifact, other than the claim asserting it exists.

**FALSIFIED IF** any of the following is true at the time of Z2 review:
- Live `SESSION_RITUALS.md` Section F contains a CLASS_STATE block, a prohibited-actions table by class state, a DEGRADED-mode Phase 1 header spec, a recovery protocol, or a periodic testing cadence — i.e. `IC-CAND-BSM-A` is wrong and the IC-029 fix did land; **or**
- Live `SESSION_RITUALS.md` Section B contains a "Step 0" — i.e. `IC-CAND-BSM-B` is wrong and P27's citation resolves; **or**
- The three asserting surfaces named under `IC-CAND-BSM-A` are found to refer to an artifact outside `SESSION_RITUALS.md` that this scan did not search.

**MEASUREMENT SURFACE.** `curl` of the canonical raw URL + `grep`. Reproducible in one command per claim; the exact greps are recorded per candidate below.

**WINDOW.** Immediate — these are present-tense claims about file contents. They are falsified or confirmed on the next fetch, not over a study window.

**WHAT A NULL RESULT MEANS.** There is no null result available here. Either the artifact is in the file or it is not.

---

## IC candidates

### IC-CAND-BSM-A — IC-029 fix claimed, not landed

```yaml
---
id: "IC-CAND-BSM-A"
name: "ic-029-fix-claimed-not-landed"
status: CANDIDATE
class: IC
date_origin: "2026-09-14"
date_registered: null
session_registered: "S-091426-NN-boot-findings-scan"  # NN pending Z2 assignment; see note
principles_triggered: ["P19", "P22"]
substrate: "Claude Opus 5 (claude-code-remote) — Z1 proposer session"
tags: ["degraded-mode", "session-rituals", "governance", "fix-not-landed", "registry-integrity"]
related_finding: ["IC-029", "IC-030"]
zone2_ratification: null
calibration_ref: null   # PENDING — P30 interactive pass not run
superseded_by: null
---
```

**This is not a citation nit.** `IC-029` is `status: REGISTERED` with `zone2_ratification: "Night · 2026-05-08"`. Its **Fix** line (`REGISTERED.md:1460`) states:

> SESSION_RITUALS.md Section F (Degraded-Mode Specification) added: CLASS_STATE block, prohibited-actions table by class state, DEGRADED mode Phase 1 header, recovery protocol, periodic testing cadence. Zone 2 ratified S-050726-04.

Live `SESSION_RITUALS.md` Section F (line 319) is titled **"Halt conditions (substrate-agnostic)"** and contains none of it — only nine numbered halt conditions.

**Three independent surfaces assert this artifact exists:**

| # | Surface | Assertion |
|---|---|---|
| 1 | `REGISTERED.md:1460` | IC-029 Fix line — **ratified** |
| 2 | `REGISTERED.md:3082` | NM-001 row — "Promoted → Degraded-Mode Spec (Section F, SESSION_RITUALS) adopted" |
| 3 | `SESSION_RITUALS.md:437` | v6.4.1 changelog — "IC-029 fix ratified: Section F Degraded-Mode Specification added…" |

**Reproduce:**
```
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md \
  | grep -n "CLASS_STATE\|Degraded-Mode Specification\|prohibited-actions\|recovery protocol\|periodic testing cadence"
```
Returns exactly one line — **437, the changelog claiming the addition.**

**Why it is load-bearing.** Section F halt 9 orders a substrate to "declare DEGRADED mode in Phase 1 header," and IC-030 depends on the class-state vocabulary (`UNAVAILABLE` / `UNKNOWN` / `STALE`). The specification defining what DEGRADED *permits and prohibits* does not exist to be followed. A substrate that correctly detects the halt condition has no defined mode to enter.

**Evidence anchor:** CONFIRMED against live canonical sources this scan (fetch table above).

**Recommended disposition (Z2's call, not Z1's):** the fix was **ratified**, so the register is right and the file is wrong — write the missing Section F specification. Amending IC-029's Fix line to "outstanding" is the fallback if Z2 judges the 2026-05-08 ratification itself to have been in error. Silently leaving both is the one option that keeps halt 9 pointing at nothing.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT + a decision on which of the two dispositions applies. No `calibration_ref` attached — P30 not cleared.

---

### IC-CAND-BSM-B — P27 cites a SESSION_RITUALS section that does not exist

```yaml
---
id: "IC-CAND-BSM-B"
name: "p27-cites-nonexistent-section-b-step-0"
status: CANDIDATE
class: IC
date_origin: "2026-09-14"
date_registered: null
session_registered: "S-091426-NN-boot-findings-scan"
principles_triggered: ["P19"]
substrate: "Claude Opus 5 (claude-code-remote) — Z1 proposer session"
tags: ["phantom-citation", "governance", "session-rituals", "P27"]
related_finding: ["F-31", "IC-034", "IC-039", "IC-044"]
zone2_ratification: null
calibration_ref: null
superseded_by: null
---
```

`GOVERNANCE.md:158` — P27 Phase 1 Prerequisite Gate — *"structurally enforced in SESSION_RITUALS Section B Step 0"*, and in the body: *"the substrate halts at SESSION_RITUALS.md Section B Step 0 and produces the `<<<ACAT_PROTOCOL_ERROR>>>` block."* Restated at `GOVERNANCE.md:299`.

Live `SESSION_RITUALS.md` Section B contains **B.0** (Empirical Verification Block, line 69) and **B.1 through B.6** (line 109). `grep -n "Step 0"` across the live file: **absent.**

B.0 concerns pre-receipt empirical verification and has nothing to do with the Phase 1 prerequisite. The two are not the same step under different names.

**Not cosmetic:** P27 specifies *runtime halt behaviour* at a location that does not exist. A substrate following P27 literally looks for a step it cannot find.

**Cross-walk:** EXTENSION of the phantom-citation class already registered as **F-31 — CITATION CORRECTION** (`REGISTERED.md:1225`), which names the family as *"same family as IC-034 / IC-039 / IC-044: citation to formalized content that did not exist at the cited location."* This is a new **instance** in a registered class, not a new class.

**Note for Z2:** that F-31 correction has carried `date_registered: "TBD — Zone 2 pending"` and `zone2_ratification: null` since **2026-07-07** — roughly 69 days — while the same class recurred twice more (A and B here). The recurrence rate is the argument for disposing of it.

**Evidence anchor:** CONFIRMED against live canonical sources this scan.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT. Remedy is either a two-line citation correction in `GOVERNANCE.md` (158, 299) or writing the Section B enforcement point P27 describes.

---

### IC-CAND-BSM-F — registry-touching work without a live fetch (self-charged)

```yaml
---
id: "IC-CAND-BSM-F"
name: "registry-touching-work-without-live-fetch"
status: CANDIDATE
class: IC
date_origin: "2026-09-14"
date_registered: null
session_registered: "S-091426-NN-boot-findings-scan"
principles_triggered: ["P19"]
substrate: "Claude Opus 5 (claude-code-remote) — Z1 proposer session"
tags: ["IC-030", "registry-touching", "self-charged", "process"]
related_finding: ["IC-030"]
zone2_ratification: null
calibration_ref: null
superseded_by: null
---
```

PR #332 drafted and merged IC-class and F-class candidate proposals, and asserted membership in the *"IC-034 / IC-039 / IC-044 phantom-citation family"*, **without any live `REGISTERED.md` fetch in the session.**

Per `SESSION_RITUALS.md` §A.4 and §F halt 9, that work was registry-touching — *"any session that proposes, modifies, or claims to act against F-class, IC-class, H-class, or NM-class entries."* It should have fetched the register or declared DEGRADED. It did neither.

The family claim was sourced from `CURRENT.md:188`, a secondary surface. This scan's live fetch shows the claim **happens to be correct** — F-31 CITATION CORRECTION names exactly that family. Correct by luck, not by method, which is the failure mode IC-030 exists to prevent.

**Structural note, offered as the substantive part of this entry:** the scan that caught this ran only because the operator invoked it. No gate required it. Per **F-45** (Stateless-Substrate Correction Locus), "I will fetch the register next time" is not structural prevention. If Z2 wants prevention rather than an apology, the candidate mechanisms are (a) extending the `Q-RFM-01` scanner to flag registry-touching diffs lacking a recorded fetch, or (b) a CI gate on `z1-inbox/` candidate blocks requiring a recorded live-fetch receipt.

**Evidence anchor:** CONFIRMED — the absence of a `REGISTERED.md` fetch is visible in the PR #332 session transcript.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT. Z1 has no standing to dispose of an IC against itself.

---

## F candidates

### F-CAND-BSM-E — adversarial review reproduces the class it charges

```yaml
---
id: "F-CAND-BSM-E"
name: "adversarial-review-reproduces-charged-class"
status: CANDIDATE
class: F
date_origin: "2026-09-14"
date_registered: null
session_registered: "S-091426-NN-boot-findings-scan"
principles_triggered: ["P29"]
substrate: "Claude Opus 5 (claude-code-remote) — Z1 proposer session"
tags: ["drift", "self-correction", "adversarial-review", "correction-locus"]
related_finding: ["F-45", "IC-031"]
zone2_ratification: null
calibration_ref: null
superseded_by: null
---
```

**Synopsis.** Adversarial review of an error class does not confer immunity to that error class. Across two independent rounds on one artifact family, the reviewer's own output reproduced the defect profile it had just charged — concentrated both times on `truth` and `consist`.

**Evidence.** 9 of 16 second-round findings on PR #332 map one-to-one onto first-round findings of the same class. Two (`R2-03`, `R2-07`) reproduce the round-one finding *inside its own remedy*: dead governance state, and P22.1 surface blending. Two (`R2-15`, `R2-16`) are receipt overstatement in a document whose subject is receipt overstatement. Full table: `z1-inbox/2026-09-14/Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md` §8 (merged, `f0c0cec`).

**Relation to F-45.** F-45 establishes that substrate commitments do not persist *across* sessions. This is the stronger adjacent claim: they do not hold *within* one either, seconds after the substrate has articulated the rule in writing. If it generalises, in-session articulation is not a mitigation for the class it articulates, and the reliable locus is an external check.

**Falsifier.** Across N=5 artifacts carrying an explicit adversarial review of a named error class, fewer than 20% of second-round findings map onto first-round findings of the same class. Falsified if the rate holds at or above 50%. Observed here: 9/16 = 56%.

**Promotion gate.** F-class bar is min 3 executed cycles. **N=1 artifact, 1 substrate, 1 automated reviewer — NOT promotion-eligible.** Filed to put the falsifier on record, not to promote.

**Confounder, stated.** The round-two reviewer was automated and may over-index on structural symmetry. This is a candidate, not a finding.

---

## AMBIGUITY items

Routed to Findings Scan per the CLAUDE.md callout table (*"Two Z2 decisions conflict on same topic → FS → Clarify or amend prior"*). Not F/IC/H class.

### AMBIGUITY-BSM-C — two conflicting "Section A — Session open" rituals

**DUPLICATE / CONVERGENT — do not file twice.**

Already flagged, independently, by `Q-BOOT-PROCESS-MAP-01` (live `REGISTERED.md`, merged #330): *"CLAUDE.md's own §A lists the REGISTERED.md read as unconditional … which disagrees with SESSION_RITUALS.md's registry-touching qualifier … Z2 should treat the underlying disagreement as its own AMBIGUITY item independent of this candidate's disposition."*

Two independent Z1 sessions converged on the same conflict on the same day, from different directions — one mapping the boot chain, one adversarially reviewing a state machine of it. **That is corroboration and should raise its priority, not duplicate its entry.**

Until resolved, **P22.1 Cascade Discipline** ("first-match wins; do not scan all and blend") is unsatisfiable at session open, because first-match-wins requires knowing which document is first.

---

### AMBIGUITY-BSM-D — §A.1 halt vs Z2-GOVARCH-02 demotion — NEW

Two ratified instruments conflict, and the conflict is resolved in practice by silent non-compliance.

**Instrument 1 — `SESSION_RITUALS.md:45`, §A step 1, never amended:**
> **Fetch live state.** GET `https://haioscc.pages.dev/api/state/operational` and `https://haioscc.pages.dev/api/state/zone3?status=open`. **If either fails, halt and report.**

**Instrument 2 — `CURRENT.md:157,170` (Z2-GOVARCH-02, ratified S-060826-04):** makes WGS Slack the Class 1 primary and demotes haioscc to secondary cross-check, stating it *"is unreachable from Claude's bash environment and is demoted to secondary cross-check."* `OPERATOR_RUNBOOK.md:66` repeats it.

**The composition.** Step 1 of every Claude session fetches an endpoint the repo asserts, as ratified fact, is unreachable from the environment Claude runs in. The fetch fails. §A.1 says halt and report. **By the letter, every Claude session must halt at open and perform no work.**

No session halts. Measured this scan from this session's environment:

```
https://haioscc.pages.dev/api/state/operational      -> HTTP:000  (connection failed, 0.33s)
https://haioscc.pages.dev/api/state/zone3?status=open -> HTTP:000  (connection failed, 0.28s)
```

*Caveat, stated rather than glossed:* HTTP 000 is a connection failure, not a service error. This session reaches `raw.githubusercontent.com` through an agent proxy, so the cause could be a proxy allowlist rather than the endpoint being down. What is verifiable from here is **unreachable from this environment** — which is precisely the condition §A.1 turns into a halt, and precisely what `CURRENT.md` already asserts.

**Why this is worth a ruling rather than a shrug.** The governance cost is not that sessions proceed — proceeding is almost certainly the right behaviour. It is that they proceed by *quietly ignoring a live, ratified halt condition*, with no declaration and no drift signal. A halt condition that every session routinely ignores teaches substrates that halt conditions are advisory, which devalues §F halts 1–9 generally. And it is invisible: nothing in the record distinguishes "this halt was considered and judged superseded" from "this halt was never read."

Note the structural identity with `IC-CAND-BSM-A`: in both, a ratified instrument asserts a state of affairs that is not operative, and the gap is load-bearing.

**What Z2 must decide.** Does Z2-GOVARCH-02 supersede §A.1's halt, or does §A.1 stand?

- If **superseded** → `SESSION_RITUALS.md` §A.1 needs amending to say so. Suggested shape, matching what sessions already do: fetch WGS (Class 1 primary); on WGS failure attempt haioscc; halt only if **both** fail. This is the reading `boot_state_machine_v0_2.py` implements and records as `DEV-07` — implemented against an unratified reading, and flagged as such in that file rather than presented as settled.
- If **§A.1 stands** → sessions have been non-compliant since S-060826-04, and a documented degraded path is needed rather than silent continuation.

Z1 has no standing to pick. Both instruments carry Z2 ratification.

---

## NM — low-friction captures (expire after 3 audits → `DRIFT_LOG.md`)

| Observation | Why it did not meet the F/IC bar |
|---|---|
| `z1-inbox/INDEX.yaml` hand-maintained tally beside an append-only list: two branches each bumped `counts` 39→40, git merged the identical text clean, the file held 41. Caught pre-push during the #332 base merge. | No principle violated, no operator-facing consequence, and `.z1-control/validate.py` does check the count — CI would have caught it, at the cost of a cycle. Deriving the count in `render.py` removes the class. Natural fit for the queued `Q-RFM-01` scanner rather than new infrastructure. |
| ECC Tools / Reference Set Readiness — `neutral`, 0/7 areas, on three consecutive commits including one predating this work. | Scores against `src/analyzers/fixtures/evaluator-rag-corpus.ts`, a TypeScript analyzer toolchain absent from this repo. Not a signal about this work. No action. |
| Concurrent-Z1-session discovery gap — `Q-BOOT-PROCESS-MAP-01` (#330) and PR #332 independently produced boot-chain artifacts for the same stages on the same day. | Already self-flagged by that candidate (*"this repo has no visible mechanism for a session to learn its own canonical NN"; "several concurrent Z1 sessions ran 2026-09-14"*). Surfaced, not re-filed. |
| F-31 CITATION CORRECTION pending Z2 since 2026-07-07 (~69 days) while the same class recurred twice. | Evidence for the class being unremediated, folded into `IC-CAND-BSM-B`. Not a separate finding. |
| v0.1 prototype defects `F-BSM-01..17`. | Defects in an unratified Z1 prototype, not generalizable observations about substrate behaviour. Below the F bar by design — the *pattern* across them is `F-CAND-BSM-E`; the individual defects are not findings. |

---

## DUPLICATE / already-registered (cited, not proposed)

- **Phantom-citation-to-nonexistent-location as a class** → covered by **F-31 CITATION CORRECTION** (`REGISTERED.md:1225`), naming the family as IC-034 / IC-039 / IC-044. `IC-CAND-BSM-A` and `-B` are new *instances* within that registered class, proposed as extensions.
- **CLAUDE.md §A vs SESSION_RITUALS §A conflict** → covered by `Q-BOOT-PROCESS-MAP-01` (#330).

---

## Scan completeness

```
3 IC-cand / 1 F-cand / 0 H-cand / 5 NM / 2 AMBIGUITY
from 14 substantive observations scanned. 2 dropped as DUPLICATE.
```

**H candidates: none.** Zero testable predictions generated this session that are not already carried as falsifiers on `F-CAND-BSM-E` or on the merged prototype. Neither is H-class: both lack a primary metric with a promotion gate distinct from the falsifier.

---

## Synthesis for Z2

Three of the four verified items are the same shape: **a ratified instrument asserts a state of affairs that is not operative.**

- `IC-CAND-BSM-A` — a ratified *fix* that never landed.
- `IC-CAND-BSM-B` — a ratified *principle* citing a location that does not exist.
- `AMBIGUITY-BSM-D` — a ratified *halt* that no session obeys.

This is the IC-031 error class — asserting content the evidence does not confirm — one layer up, at the **registry** rather than the session. IC-031 hardened sessions against overstating in receipts via the B.0 block and the B.6 reconciliation paragraph. **Nothing currently checks whether a ratified `Fix →` line actually landed in the file it names.**

`Q-RFM-01` (REGISTERED.md failure-mode map + executable scanner, `z1-inbox/2026-09-13/Q-RFM-01.md`, awaiting Z2) is the natural home for that check: for every `Fix →` line citing a file and section, fetch the live file and assert the cited artifact exists. That is a concrete extension of a queued item rather than new infrastructure, and it would have caught `IC-CAND-BSM-A` in May.

---

**Not done by this candidate:** no `REGISTERED.md` modification, no Z2 hash sought, no `PRIORITY_QUEUE.md` amendment, no `calibration_ref` (P30 **not cleared** — this is not ratification-ready as filed). No canonical file was edited to fix any finding above; all four remain as reported, for Z2 to dispose of. Z1 proposes; Night decides (**P21**).
