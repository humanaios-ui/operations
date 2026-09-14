# Q-BOOT-FINDINGS-SCAN-01 — Registry Candidate Block

**Status:** Z1 CANDIDATE — advisory, unratified. This block proposes; it does not register.
**Produced by:** `humanaios-findings-scan` (standalone invocation), Z1 (Claude)
**Date:** 2026-09-14 · rev 2 (review round applied — see §Revision note)
**Origin:** post-merge findings scan over PR #332 (`Q-BOOT-STATE-MACHINE-01`, merged `f0c0cec`)
**Routing:** all candidates → Zone 2 (Night) for ratification per **P21**
**Contract:** `tools/skills/humanaios-findings-scan/SKILL.md` (in-repo). Where this block and that contract disagree, the contract wins.

---

## Registry fetch — pinned (IC-030 + CLAUDE.md §A.1/§A.5)

Rev 1 recorded only `main` plus line/byte counts. `main` is mutable and those counts are not a hash, so the evidence below is re-pinned to an immutable commit and every claim re-run against it.

**Pinned commit:** `99b113698507dd82d39d8a9acc1cb7804e2b6c79`
**Fetch base:** `https://raw.githubusercontent.com/humanaios-ui/operations/99b1136.../<FILE>`

| File | HTTP | `git hash-object` (blob SHA) | Lines |
|---|---|---|---|
| `REGISTERED.md` | **200** | `1e2455cdd0c9bce0feb1c146e3f99cae33479673` | 4180 |
| `SESSION_RITUALS.md` | **200** | `29cc99ae4dac6e700cb04afe60cc6a96f1081e0c` | 439 |
| `GOVERNANCE.md` | **200** | `9415715532f3067c9b825597eab46333e6124a27` | 309 |
| `CURRENT.md` | **200** | `df35e561aee469f859208399f104f7e06b370f16` | 213 |

**Fetch-success precondition.** Every absence claim below is conditioned on **HTTP 200 plus a matching blob SHA** for the file searched. A zero-match grep over a failed or truncated fetch is `CHECK_UNAVAILABLE`, not evidence of absence — this block distinguishes the two explicitly, and the HTTP-000 result under `AMBIGUITY-BSM-D` is exactly why.

**Staleness note.** At first fetch the working-copy `REGISTERED.md` (4147 lines) was **33 lines behind live**. Live carried `Q-BOOT-PROCESS-MAP-01`, appended the same day by a concurrent Z1 session (since merged as #330). All cross-walks are against the **pinned** file, not the working copy.

---

## Revision note (rev 2)

An automated review of rev 1 raised eleven findings. All were correct; all are applied. Three are worth naming because they bear on this block's own subject:

1. **The observed value in the headline falsifier was wrong.** Rev 1 stated `9/16 = 56%`. The §8 table it cites maps **14 of 16** (only `R2-05` and `R2-13` carry no mapping), across **11 distinct** round-one classes. Corrected throughout to **14/16 = 87.5%**.
2. **This is the third occurrence of one sub-class** — *a stated count that does not match the artifact's own table*. Prior two: the dimension roll-up in #332 rev 1 (`R2-15`), and the "25-assertion" figure against a 26-assertion suite. It has now recurred in the document filed to register the pattern. Folded into `H-CAND-BSM-E` as evidence, not hidden.
3. **Rev 1 called `F-31 CITATION CORRECTION` a "registered class."** It is not: `date_registered: "TBD — Zone 2 pending"`, `zone2_ratification: null`. Rev 1 stated that pending status correctly in one paragraph and contradicted it in another. Corrected.

---

## Falsifier

**This block carries no composite falsifier, by design.** Rev 1 did, and it was wrong: a single `OR`-joined condition falsifies the whole block as soon as any one candidate is refuted, even while the others stand — so Z2 could not dispose of them independently. Each candidate now carries its own prediction, falsification condition, measurement surface and window, stated inline with it:

| Candidate | Falsifier location | Shape |
|---|---|---|
| `IC-CAND-BSM-A` | §IC candidates → BSM-A | all five named components present within §F body (319–334) falsifies; partial presence and relocation are handled as separate, smaller outcomes |
| `IC-CAND-BSM-B` | §IC candidates → BSM-B | `grep -c "Step 0"` > 0, or a differently-named step discharging P27 |
| `IC-CAND-BSM-F` | §IC candidates → BSM-F | a `REGISTERED.md` fetch present in the #332 transcript, or Z2 ruling candidate blocks non-registry-touching |
| `H-CAND-BSM-E` | §H candidate | N=5 artifacts, rate below 20% → H₀ holds, hypothesis falsified |
| `AMBIGUITY-BSM-D` | — | **RULED by Z2 2026-09-14**; no longer an open prediction |

Every absence claim is additionally conditioned on the fetch-success precondition in the header: **HTTP 200 plus matching blob SHA**, else `CHECK_UNAVAILABLE` rather than "absent."

---

## Part 2 cross-walk — status per candidate (contract §Part 2)

The contract requires **one** of NEW / DUPLICATE / EXTENSION recorded for **every** surviving F/IC/H candidate. Rev 1 gave this in prose for `-B` only.

| Candidate | Class | Status | Against |
|---|---|---|---|
| `IC-CAND-BSM-A` | IC | **EXTENSION** | `IC-029` (REGISTERED, ratified Night · 2026-05-08) — extends it with the fix-not-landed fact. Forward-pointer needed on IC-029. |
| `IC-CAND-BSM-B` | IC | **EXTENSION** | `F-31 CITATION CORRECTION` — itself a **pending candidate**, not a registered entry. See note below. |
| `IC-CAND-BSM-F` | IC | **EXTENSION** | `IC-030` (REGISTERED) — a new instance of the violation IC-030 defines. |
| `H-CAND-BSM-E` | H | **NEW** | No existing H-class entry covers within-session correction-locus failure. Adjacent to `F-45`, which covers the across-session case. |

**Forward-pointer flag for Z2 (contract §Part 2):** the register is append-only, so if `-A` is accepted it needs a `related_finding` link from `IC-029`, and `-F` one from `IC-030`. Z1 cannot write those.

**On the `-B` base entry.** `F-31 CITATION CORRECTION` (`REGISTERED.md:1225`) carries `date_registered: "TBD — Zone 2 pending"` and `zone2_ratification: null`. It is the **pending correction candidate** that *names* the phantom-citation family (IC-034 / IC-039 / IC-044) — it is not itself a ratified class. `-B` extends a candidate, not a registered entry, and Z2 may reasonably want to dispose of F-31's correction first. That it has been pending since **2026-07-07 (~69 days)** while the class recurred twice more is the argument for doing so.

---

## IC candidates

### IC-CAND-BSM-A — IC-029 fix claimed, not landed

```yaml
---
id: "IC-CAND-BSM-A"
name: "ic-029-fix-claimed-not-landed"
status: CANDIDATE
class: IC
crosswalk: EXTENSION            # of IC-029
date_origin: "2026-09-14"
date_registered: null
session_registered: "S-091426-NN-boot-findings-scan"   # NN pending Z2 assignment
principles_triggered: ["P19", "P22"]
substrate: "Claude Opus 5 (claude-code-remote) — Z1 proposer session"
tags: ["degraded-mode", "session-rituals", "governance", "fix-not-landed", "registry-integrity"]
related_finding: ["IC-029", "IC-030"]
zone2_ratification: null
calibration_ref: null           # PENDING — P30 interactive pass not run
superseded_by: null
---
```

**This is not a citation nit.** `IC-029` is `status: REGISTERED` with `zone2_ratification: "Night · 2026-05-08"`. Its **Fix** line (`REGISTERED.md:1460`) states:

> SESSION_RITUALS.md Section F (Degraded-Mode Specification) added: CLASS_STATE block, prohibited-actions table by class state, DEGRADED mode Phase 1 header, recovery protocol, periodic testing cadence. Zone 2 ratified S-050726-04.

At the pinned SHA, `SESSION_RITUALS.md` **Section F spans lines 319–334** (`## Section F — Halt conditions` → `## Section G — Verification posture`) and contains nine numbered halt conditions. Each named component of the claimed fix occurs **exactly once in the whole file, at line 437 — inside the changelog asserting the addition — and therefore outside Section F's body entirely**:

| Component | Occurrences in file | At line | Inside §F body (319–334)? |
|---|---:|---|---|
| `CLASS_STATE` | 1 | 437 | **no** |
| `prohibited-actions` | 1 | 437 | **no** |
| `recovery protocol` | 1 | 437 | **no** |
| `periodic testing cadence` | 1 | 437 | **no** |
| `Degraded-Mode Specification` | 1 | 437 | **no** |

**Three surfaces assert the artifact exists (common-mode, not independent):**

| # | Surface | Assertion |
|---|---|---|
| 1 | `REGISTERED.md:1460` | IC-029 Fix line — **ratified**, source of truth |
| 2 | `REGISTERED.md:3082` | NM-001 row — copies the IC-029 claim "Degraded-Mode Spec adopted" |
| 3 | `SESSION_RITUALS.md:437` | v6.4.1 changelog — copies the IC-029 claim from ratification |

**Reproduce (pinned, component-wise):**
```bash
SHA=99b113698507dd82d39d8a9acc1cb7804e2b6c79
curl -sSf "https://raw.githubusercontent.com/humanaios-ui/operations/$SHA/SESSION_RITUALS.md" -o SR.md \
  && [ "$(git hash-object SR.md)" = "29cc99ae4dac6e700cb04afe60cc6a96f1081e0c" ] \
  || { echo "CHECK_UNAVAILABLE"; exit 1; }
for p in "CLASS_STATE" "prohibited-actions" "recovery protocol" \
         "periodic testing cadence" "Degraded-Mode Specification"; do
  printf "%-28s %s\n" "$p" "$(grep -n "$p" SR.md | tr '\n' ' ')"
done
sed -n '319,334p' SR.md      # Section F body in full
```
The `|| exit 1` guard stops the block if the fetch fails or the hash does not match; a failed fetch cannot produce a zero-match result.

**Why it is load-bearing.** §F halt 9 orders a substrate to "declare DEGRADED mode in Phase 1 header," and IC-030 depends on the class-state vocabulary (`UNAVAILABLE` / `UNKNOWN` / `STALE`). The specification defining what DEGRADED *permits and prohibits* does not exist to be followed. A substrate that correctly detects the halt has no defined mode to enter.

**Falsifier (this candidate only).**
- **PREDICTION:** at the pinned SHA, zero of the five named components appear within `SESSION_RITUALS.md` Section F's body (lines 319–334).
- **FALSIFIED IF:** **all five** named components are present within Section F's body — i.e. the fix as described did land. A *partial* implementation (some components present) does **not** falsify this candidate; it converts it to a narrower "fix partially landed" finding, which Z2 should dispose of as such rather than as a clean confirm or refute.
- **RELOCATED CASE, handled separately:** if the components are found in some other canonical file, the fix landed *somewhere other than where IC-029 says it did*. That falsifies the location claim but not the core defect — IC-029's Fix line would still misdirect any reader. Z2 should treat that outcome as "citation wrong, fix exists," a strictly smaller finding.
- **MEASUREMENT SURFACE:** the pinned command block above.
- **WINDOW:** immediate — a present-tense claim about file contents.

**Evidence anchor:** CONFIRMED at pinned SHA `99b1136`, blob `29cc99a`, HTTP 200.

**Recommended disposition (Z2's call, not Z1's):** the fix was **ratified**, so the register is right and the file is wrong — write the missing Section F specification. Amending IC-029's Fix line to "outstanding" is the fallback if Z2 judges the 2026-05-08 ratification itself erroneous. Leaving both as-is is the one option that keeps halt 9 pointing at nothing.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT + a decision between the two dispositions + a `related_finding` forward-pointer on IC-029. No `calibration_ref` — P30 not cleared.

---

### IC-CAND-BSM-B — P27 cites a SESSION_RITUALS section that does not exist

```yaml
---
id: "IC-CAND-BSM-B"
name: "p27-cites-nonexistent-section-b-step-0"
status: CANDIDATE
class: IC
crosswalk: EXTENSION            # of the F-31 CITATION CORRECTION *candidate* (not a registered class)
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

`GOVERNANCE.md` lines **158, 159, 299** — P27 Phase 1 Prerequisite Gate — *"structurally enforced in SESSION_RITUALS Section B Step 0"* and, in the body, *"the substrate halts at SESSION_RITUALS.md Section B Step 0 and produces the `<<<ACAT_PROTOCOL_ERROR>>>` block."*

At the pinned SHA, `SESSION_RITUALS.md` Section B contains **B.0** (Empirical Verification Block, line 69) and **B.1 through B.6** (line 109). The string `Step 0` occurs **0 times in the entire file**. B.0 concerns pre-receipt empirical verification and has nothing to do with the Phase 1 prerequisite; they are not the same step under different names.

**Reproduce (pinned, runnable):**
```bash
SHA=99b113698507dd82d39d8a9acc1cb7804e2b6c79
curl -sSf "https://raw.githubusercontent.com/humanaios-ui/operations/$SHA/SESSION_RITUALS.md" -o SR.md \
  && [ "$(git hash-object SR.md)" = "29cc99ae4dac6e700cb04afe60cc6a96f1081e0c" ] \
  || { echo "CHECK_UNAVAILABLE"; exit 1; }
grep -c "Step 0" SR.md                        # -> 0
grep -n "^### B\.\|^## Section B" SR.md        # -> Section B, B.0, B.1 through B.6

curl -sSf "https://raw.githubusercontent.com/humanaios-ui/operations/$SHA/GOVERNANCE.md" -o GOV.md \
  && [ "$(git hash-object GOV.md)" = "9415715532f3067c9b825597eab46333e6124a27" ] \
  || { echo "CHECK_UNAVAILABLE"; exit 1; }
grep -n "Section B Step 0" GOV.md              # -> 158, 159, 299
```

**Not cosmetic:** P27 specifies *runtime halt behaviour* at a location that does not exist. A substrate following P27 literally looks for a step it cannot find.

**Falsifier (this candidate only).**
- **PREDICTION:** at the pinned SHA, `grep -c "Step 0"` over `SESSION_RITUALS.md` returns 0.
- **FALSIFIED IF:** the string appears, or Section B is found to contain a step that discharges P27's Phase 1 prerequisite under a different name (in which case the defect reduces to a naming mismatch — smaller, and Z2 should dispose of it as such).
- **MEASUREMENT SURFACE:** the command block above.
- **WINDOW:** immediate.

**Evidence anchor:** CONFIRMED at pinned SHA `99b1136`, blobs `29cc99a` / `9415715`, both HTTP 200.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT. Remedy is either a citation correction in `GOVERNANCE.md` (158, 159, 299) or writing the Section B enforcement point P27 describes. Z2 may prefer to dispose of the pending F-31 correction first, since this extends it.

---

### IC-CAND-BSM-F — registry-touching work without a live fetch (self-charged)

```yaml
---
id: "IC-CAND-BSM-F"
name: "registry-touching-work-without-live-fetch"
status: CANDIDATE
class: IC
crosswalk: EXTENSION            # of IC-030
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

Per `SESSION_RITUALS.md` §A.4 and §F halt 9, that work was registry-touching — *"any session that proposes, modifies, or claims to act against F-class, IC-class, H-class, or NM-class entries."* It should have fetched the register or declared DEGRADED. It did neither. The family claim was sourced from `CURRENT.md:188`, a secondary surface. This scan's pinned fetch shows the claim **happens to be correct**. Correct by luck, not by method — which is the failure mode IC-030 exists to prevent.

**Falsifier (this candidate only).**
- **PREDICTION:** no `REGISTERED.md` fetch (canonical URL, any SHA) appears in the PR #332 session transcript prior to the candidate blocks being drafted.
- **FALSIFIED IF:** such a fetch is present in that transcript, or Z2 rules that a candidate block naming existing IC IDs is not "registry-touching" under §A.4 — in which case this charge dissolves and the §A.4 definition should be tightened to say so.
- **MEASUREMENT SURFACE:** the PR #332 session transcript.
- **WINDOW:** immediate.

**Structural note, offered as the substantive part of this entry.** The scan that caught this ran only because the operator invoked it; no gate required it. Per **F-45**, "I will fetch the register next time" is not structural prevention. If Z2 wants prevention rather than an apology, the candidate mechanisms are (a) extending the `Q-RFM-01` scanner to flag registry-touching diffs lacking a recorded fetch, or (b) a CI gate on `z1-inbox/` candidate blocks requiring a recorded live-fetch receipt — a pinned SHA + blob hash, of the shape this block's header now carries.

**Evidence anchor:** CONFIRMED — absence of a `REGISTERED.md` fetch is visible in the PR #332 session transcript.

`Fix → Principle P19.`

**Promotion gate:** Z2 ACCEPT. Z1 has no standing to dispose of an IC against itself.

---

## H candidate

### H-CAND-BSM-E — adversarial review reproduces the class it charges

```yaml
---
id: "H-CAND-BSM-E"
name: "adversarial-review-reproduces-charged-class"
status: CANDIDATE
class: H
crosswalk: NEW
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

**Reclassified from F to H in rev 2.** The contract's F bar requires *"(c) generalizable beyond the single instance."* At one artifact family, one substrate, one automated reviewer, generalizability is precisely what is **not** established — so F was the wrong class, and rev 1 filing it as F while simultaneously marking it not-promotion-eligible misclassified the scan's own routing. It does state all four H elements, so H is the class it actually meets.

**Null hypothesis (H₀).** Adversarial review of a named error class is independent of the reviewer's own subsequent rate of that class: ≤20% of second-round findings map onto first-round findings of the same class.

**Falsification condition.** Across **N=5** artifacts each carrying an explicit adversarial review of a named error class, the mapping rate falls **below 20%** → H₀ holds, hypothesis falsified. A rate at or above 50% across that N supports the alternative.

**Primary metric.** Percentage of second-round findings that map one-to-one onto a first-round finding of the same class, counted by **round-two row** (a row with any mapping counts once; a row with none does not).

**Promotion gate.** N=5 artifacts, **≥2 substrates**, **≥2 distinct reviewers** — the single-reviewer confound below must be broken before promotion is eligible. Not promotion-eligible at N=1.

**Observed, this artifact family.** **14 of 16 = 87.5%**, across **11 distinct** round-one classes. Source table: `z1-inbox/2026-09-14/Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md` §8 (merged, `f0c0cec`). Only `R2-05` and `R2-13` carry no mapping. Two rows (`R2-03`, `R2-07`) reproduce the round-one finding *inside its own remedy*; two (`R2-15`, `R2-16`) are receipt overstatement in a document whose subject is receipt overstatement.

**Third occurrence, within this filing.** One sub-class — *a stated count that does not match the artifact's own table* — has now recurred three times: the dimension roll-up in #332 rev 1 (`R2-15`); the "25-assertion" figure against a 26-assertion suite; and rev 1 of **this** block stating `9/16` where its own cited table shows `14/16`. The third occurred in the document filed to register the pattern, after the pattern was written down twice. Recorded as evidence rather than corrected silently.

**Relation to F-45.** F-45 establishes that substrate commitments do not persist *across* sessions. This is the stronger adjacent claim: they do not hold *within* one either, minutes after the substrate has articulated the rule in writing. If it survives N=5, in-session articulation is not a mitigation for the class it articulates, and the reliable locus is an external check.

**Confounder, stated.** Rounds two and three were the same automated reviewer, which may over-index on structural symmetry — hence the ≥2-reviewer promotion gate. N=1 artifact family. This is a candidate hypothesis, not a finding.

---

## AMBIGUITY items

Routed to Findings Scan per the CLAUDE.md callout table (*"Two Z2 decisions conflict on same topic → FS → Clarify or amend prior"*). Not F/IC/H class, so not cross-walked per contract §Part 2.

### AMBIGUITY-BSM-C — two conflicting "Section A — Session open" rituals

**DUPLICATE / CONVERGENT — dropped, not filed.**

Already flagged, independently, by `Q-BOOT-PROCESS-MAP-01` (pinned `REGISTERED.md`, merged #330): *"CLAUDE.md's own §A lists the REGISTERED.md read as unconditional … which disagrees with SESSION_RITUALS.md's registry-touching qualifier … Z2 should treat the underlying disagreement as its own AMBIGUITY item independent of this candidate's disposition."*

Two Z1 sessions surfaced the same conflict on the same day from different directions — one mapping the boot chain, one adversarially reviewing a state machine of it.

**Rev 2 correction — this is not independent corroboration, and rev 1 claimed it was.** Applying the `Witch` invariant from `Q-EXTERNAL-CHECK-FRAMEWORK-01` (issue #335), `AGGREGATED ≠ INDEPENDENT`: both sessions ran the same substrate family, on the same repo, against the same corpus, on the same day, with the same source documents in context. That is a **common-mode** configuration, not two independent observers. The agreement raises confidence that *the text says what both read it to say*; it does **not** independently confirm that the reading is correct, because a shared misreading would produce the identical result. Downgraded from "corroboration" to "two same-mode readings agree." Still worth Z2's attention as a live conflict; not worth the weight rev 1 gave it.

Until resolved, **P22.1 Cascade Discipline** ("first-match wins; do not scan all and blend") is unsatisfiable at session open, because first-match-wins requires knowing which document is first.

---

### AMBIGUITY-BSM-D — §A.1 halt vs Z2-GOVARCH-02 demotion — **RULED (Z2, 2026-09-14)**

> **Z2 ruling, Night, in-session 2026-09-14:** *"Superseded → amend §A.1. Accepting suggested shape."*
> Landed as `SESSION_RITUALS.md` v6.4.2, Section A Step 1 only. Ruling transcribed at `z1-inbox/2026-09-14/Z2_RULING_AMBIGUITY_BSM_D.md`; `z2_hash` **unsigned**, pending `ratify.py`. The analysis below is retained as the record of what was ruled on.

Two **canonical** instruments conflict, and the conflict is resolved in practice by silent non-compliance.

*Rev 2 correction:* rev 1 called these "two ratified instruments." Only one carries a ratification record this scan verified. Stated precisely:

**Instrument 1 — `SESSION_RITUALS.md:45`, §A step 1.** Status LIVE, v6.4.1. The file's v6.4.0 changelog records "Z2 ratification S-051926-01" and v6.4.1 "committed via S-051926-02-z3-closeout"; **no ratification record specific to the §A.1 halt text was located**, and that text is unchanged across both. Canonical and in force; ratification provenance for this line, unverified.

> **Fetch live state.** GET `https://haioscc.pages.dev/api/state/operational` and `https://haioscc.pages.dev/api/state/zone3?status=open`. **If either fails, halt and report.**

**Instrument 2 — `CURRENT.md:157,170` — Z2-GOVARCH-02, ratified S-060826-04.** Makes WGS Slack the Class 1 primary and demotes haioscc to secondary cross-check, stating it *"is unreachable from Claude's bash environment and is demoted to secondary cross-check."* `OPERATOR_RUNBOOK.md:66` repeats it.

**The composition.** Step 1 of every Claude session fetches an endpoint the repo asserts, as ratified fact, is unreachable from the environment Claude runs in. The fetch fails. §A.1 says halt. **By the letter, every Claude session must halt at open and perform no work.** No session halts.

Measured this scan, from this session's environment:

```
https://haioscc.pages.dev/api/state/operational       -> HTTP:000  (connection failed, 0.33s)
https://haioscc.pages.dev/api/state/zone3?status=open -> HTTP:000  (connection failed, 0.28s)
```

*Caveat, stated rather than glossed:* HTTP 000 is a **connection failure, not a service error**, and this is the `CHECK_UNAVAILABLE` case the header defines — it is not evidence the service is down. This session reaches `raw.githubusercontent.com` through an agent proxy, so the cause may be a proxy allowlist. What is verifiable from here is **unreachable from this environment** — which is precisely the condition §A.1 converts into a halt, and precisely what `CURRENT.md` already asserts.

**Why this needs a ruling rather than a shrug.** The cost is not that sessions proceed — proceeding is almost certainly correct. It is that they proceed by *quietly ignoring a live halt condition*, with no declaration and no drift signal. A halt every session ignores teaches substrates that halt conditions are advisory, which devalues §F halts 1–9 generally. And it is invisible: nothing distinguishes "this halt was considered and judged superseded" from "this halt was never read."

Note the structural identity with `IC-CAND-BSM-A`: a canonical instrument asserting a state of affairs that is not operative, with the gap load-bearing.

**What Z2 must decide.** Does Z2-GOVARCH-02 supersede §A.1's halt, or does §A.1 stand?

- **Superseded** → amend §A.1. Suggested shape, matching what sessions already do: fetch WGS (Class 1 primary); on WGS failure attempt haioscc; halt only if **both** fail. This is the reading `boot_state_machine_v0_2.py` implements and records as `DEV-07` — implemented against an unratified reading and flagged as such in that file, not presented as settled.
- **§A.1 stands** → sessions have been non-compliant since S-060826-04, and need a documented degraded path rather than silent continuation.

Z1 has no standing to pick: Z2-GOVARCH-02 carries Night's ratification, and §A.1 is canonical protocol text.

---

## NM — low-friction captures (expire after 3 audits → `DRIFT_LOG.md`)

| # | Observation | Why it did not meet the F/IC bar |
|---|---|---|
| 1 | `z1-inbox/INDEX.yaml` hand-maintained tally beside an append-only list: two branches each bumped `counts` 39→40, git merged the identical text clean, the file held 41. Caught pre-push during the #332 base merge. | No principle violated, no operator-facing consequence, and `.z1-control/validate.py` does check the count — CI would have caught it, at the cost of a cycle. Deriving the count in `render.py` removes the class. Fits the queued `Q-RFM-01` scanner. |
| 2 | ECC Tools / Reference Set Readiness — `neutral`, 0/7 areas, on every commit across both PRs including one predating this work. | Scores against `src/analyzers/fixtures/evaluator-rag-corpus.ts`, a TypeScript analyzer toolchain absent from this repo. Not a signal about this work. |
| 3 | Working-copy `REGISTERED.md` was 33 lines behind live at scan start. | Expected for an in-flight branch; caught by the pinned fetch, which is the control. No consequence — no claim was made from the stale copy. |
| 4 | `F-31 CITATION CORRECTION` pending Z2 since 2026-07-07 (~69 days) while the same class recurred twice. | Evidence for the class being unremediated, folded into `IC-CAND-BSM-B`. Not a separate finding. |
| 5 | v0.1 prototype defects `F-BSM-01..17`. | Defects in an unratified Z1 prototype, not generalizable observations about substrate behaviour. Below the F bar by design — the *pattern* across them is `H-CAND-BSM-E`. |

---

## DUPLICATE — dropped, cited not proposed (contract §Part 2)

| Observation | Covered by |
|---|---|
| `AMBIGUITY-BSM-C` — CLAUDE.md §A vs SESSION_RITUALS §A conflict | `Q-BOOT-PROCESS-MAP-01` (#330), which flags it independently |
| Phantom-citation-to-nonexistent-location **as a class** | `F-31 CITATION CORRECTION` (`REGISTERED.md:1225`) — a pending candidate naming the IC-034/IC-039/IC-044 family. `-B` extends it as a new instance. |
| Concurrent-Z1-session discovery gap — #330 and #332 independently produced boot-chain artifacts for the same stages the same day | `Q-BOOT-PROCESS-MAP-01` self-flags it (*"no visible mechanism for a session to learn its own canonical NN"*) |
| CLAUDE.md "REGISTERED.md is Z2 sole write" vs "Z1 candidate-block writes" tension | `Q-BOOT-PROCESS-MAP-01` self-flags it (*"this candidate is itself a live instance of that ambiguity"*) |

---

## Scan completeness

```
14 substantive observations scanned
   3  IC candidates   (BSM-A, BSM-B, BSM-F)
   1  H  candidate    (BSM-E)
   0  F  candidates   (BSM-E reclassified F -> H in rev 2)
   1  AMBIGUITY filed (BSM-D; BSM-C dropped as DUPLICATE)
   5  NM captures
   4  dropped as DUPLICATE
   ————
  14  total          (3 + 1 + 0 + 1 + 5 + 4 = 14)
```

Rev 1 reported `3 + 1 + 0 + 5 + 2 = 11` retained plus 2 duplicates against a claimed 14 scanned — which does not balance. The ledger above is the reconciled version: the discrepancy was two under-counted DUPLICATE drops (concurrent-Z1 gap, Z2-sole-write tension) and one uncounted NM (stale working copy).

---

## Synthesis for Z2

Three of the four verified items share one shape: **a canonical instrument asserting a state of affairs that is not operative.**

- `IC-CAND-BSM-A` — a ratified *fix* that never landed.
- `IC-CAND-BSM-B` — a principle *citing* a location that does not exist.
- `AMBIGUITY-BSM-D` — a *halt* that no session obeys.

This is the IC-031 error class — asserting content the evidence does not confirm — one layer up, at the **registry and protocol** layer rather than the session layer. IC-031 hardened sessions against overstating in receipts via the B.0 block and the B.6 reconciliation paragraph. **Nothing currently checks whether a ratified `Fix →` line actually landed in the file it names.**

`Q-RFM-01` (REGISTERED.md failure-mode map + executable scanner, `z1-inbox/2026-09-13/Q-RFM-01.md`, awaiting Z2) is the natural home: for every `Fix →` line citing a file and section, fetch that file at a pinned SHA and assert the cited artifact exists **within the cited section's line range**, not merely somewhere in the file — the distinction that separates `IC-CAND-BSM-A` from a clean pass. That is a concrete extension of a queued item rather than new infrastructure, and it would have caught `IC-CAND-BSM-A` in May.

---

---

## Relation to Q-EXTERNAL-CHECK-FRAMEWORK-01 (issue #335)

These findings were produced before reading #335, and they land on its invariants without having been aimed at them. That makes them useful to it: the framework's current test suite (T1–T6) is **synthetic**, and these are **live cases from this repo's own corpus with established ground truth.**

| ECF invariant | Live instance found this scan |
|---|---|
| `AUTHORITY ≠ EVIDENCE` | `IC-CAND-BSM-A`. IC-029 carries Night's ratification (authority). Its named fix is absent from the file (evidence). The strongest instance in the set — the authority is genuine and the artifact still isn't there. |
| `AGGREGATED ≠ INDEPENDENT` | The three surfaces asserting the Degraded-Mode Specification are **one claim copied three times**, not three confirmations. Also `AMBIGUITY-BSM-C` — see the rev-2 correction above, where this scan made the error itself. |
| `NO_GATE ≠ PASS` | Nothing verifies that a ratified `Fix →` line landed. Absence of that gate read as passing for ~4 months. |
| `UNKNOWN ≠ SAFE` | The `CHECK_UNAVAILABLE` vs zero-match distinction now enforced in this block's header. A failed fetch producing no grep matches is not evidence of absence — the HTTP-000 result under `-D` is the live case. |
| `evidence ≠ conclusion` | `H-CAND-BSM-E`, and the three count-mismatches inside this artifact family. |

**Layer mapping.** `Witness` → does the cited artifact exist (A, B). `Jester` → does the evidence support the conclusion (E, and the count errors). `Witch` → false independence (C's correction, and the three-surfaces case). `Oracle` → bounded expectation (every per-candidate falsifier and promotion gate here).

**Proposed first non-synthetic deployment.** Point `Witness` at `REGISTERED.md`'s `Fix →` lines: for each, fetch the cited file at a pinned SHA and assert the artifact exists **within the cited section's line range**. That is the `Q-RFM-01` extension already proposed in this block, it is the check that would have caught `IC-CAND-BSM-A` in May, and it now has four known-truth cases to validate against before any coverage claim is made.

---

**Not done by this candidate:** no `REGISTERED.md` modification, no `PRIORITY_QUEUE.md` amendment, no `calibration_ref` (P30 **not cleared**). `AMBIGUITY-BSM-D` was ruled by Z2 in session and the amendment has landed; its `z2_hash` is **unsigned** pending `ratify.py`. No canonical file was edited to fix any *other* finding — A, B, F, E and C remain as reported, for Z2 to dispose of. Z1 proposes; Night decides (**P21**).
