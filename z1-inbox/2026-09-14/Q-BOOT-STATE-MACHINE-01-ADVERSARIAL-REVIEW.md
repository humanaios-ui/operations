# Q-BOOT-STATE-MACHINE-01 — Adversarial Review

**Status:** Z1 CANDIDATE — advisory, unratified. Not a registry entry.
**Reviewer:** Z1 (Claude)
**Date:** 2026-09-14
**Artifact under review:** `boot_state_machine.py` v0.1 — "BOOT STATE MACHINE — Minimal Advisory Prototype"
**Corrected artifact produced:** `z1-inbox/2026-09-14/boot_state_machine_v0_2.py`
**Repo SHA pinned for source verification:** `6d3443af07ba18db56c1d716e24c1f9f33b2b056`
**Sources read at that SHA:** `SESSION_RITUALS.md` (v6.4.1), `GOVERNANCE.md` (v6.4.3), `OPERATOR_RUNBOOK.md`, `CURRENT.md`, `CLAUDE.md`
**Review posture:** ADVERSARIAL — the working assumption is that the artifact's self-description overstates its fidelity, and every claim in its docstring is treated as a hypothesis to falsify against the pinned sources.

---

## 0. P29 Articulation Gate

**What this artifact is:** a findings register for a prototype state machine, plus a corrected implementation.
**What evidence supports it:** every finding cites a file and section verified at the pinned SHA; the corrected implementation ships a 25-assertion self-test that was executed (output in §5).
**Risk of being wrong, and how it would be detected:** the main risk is that I have read a *narrower* protocol than the operator intends — e.g. that PATH C is meant to be broader than `OPERATOR_RUNBOOK §3a note 3` states. Detected by Z2 rejecting F-BSM-04 with a wider reading, which would also retire F-BSM-16.

**P30 note:** no `calibration_ref` is attached. Per P30 this artifact has **not cleared the calibration gate** and is not ratification-ready. It is filed as a Z1 working document.

---

## 1. Verdict

The prototype's *posture* is good and should be preserved: it declares itself advisory, names a source-precedence rule, and volunteers a fidelity-deviation list. Volunteering deviations is the correct §A.0 behaviour and is credited below.

The prototype's *content* does not support its own claims. Three findings are blocking:

1. **The file does not execute.** It is truncated mid-statement, so the "red-team test" results asserted in its header cannot have been produced by this artifact.
2. **The B.0 hard gate it advertises does not exist.** `ALLOWED_ACTIONS[BS_SHUTDOWN]` permits `emit_close_artifact` and `run_b0_verification` in the same state — the docstring's central fidelity claim is falsified by a table in the same file.
3. **Every gate defaults to pass, on the caller's own say-so.** `pin_ok: bool = True`, `slack_mcp_available: bool = True`. A structure that reads as verification and implements attestation is the exact IC-031 shape the protocol it models was hardened to prevent.

Net: **v0.1 is weaker than the protocol it restates, in the specific direction that matters** — it lets sessions pass that canonical sources would stop. Recommend `EDIT`, not `REJECT`: the shape is right, the guards are not.

---

## 2. Findings, mapped to ACAT dimensions

The 12 canonical dimensions (SESSION_RITUALS §C): `truth · service · harm · autonomy · value · humility · scheme · power · syc · consist · fair · handoff`.

### BLOCKER

| ID | Finding | Evidence | Dimensions |
|---|---|---|---|
| **F-BSM-01** | **Artifact does not parse.** The file ends at `else:` inside `_do_load_governance_current` with no block body. The header nevertheless reports results "from red-team test" and a list of confirmed fidelity properties. A file that raises `IndentationError` at import cannot have produced them. This is a receipt-overstatement instance at file scope — assertions about behaviour the artifact cannot exhibit. | `python3 -c "ast.parse(...)"` on the delivered tail → `IndentationError: expected an indented block after 'else' statement` | `truth` `consist` `humility` |
| **F-BSM-02** | **The advertised B.0 hard gate is not implemented.** Docstring: *"SHUTDOWN carries B.0-style hard gate before close artifacts."* But `ALLOWED_ACTIONS[BS_SHUTDOWN] = ["run_b0_verification", "emit_close_artifact"]` — both legal in the same state, in either order. Nothing prevents emitting the close artifact first, which is precisely SESSION_RITUALS §F halt 7. A gate that is advisory in a machine whose purpose is to make gates structural is not a gate. | `SESSION_RITUALS.md:329` (halt 7); `SESSION_RITUALS.md:67` ("hard gate"); artifact `ALLOWED_ACTIONS` table | `truth` `consist` `harm` `value` |
| **F-BSM-03** | **Guards are caller-asserted booleans that default to pass.** `_do_pin_commit(pin_ok: bool = True)`, `_do_fetch_live_state(slack_mcp_available: bool = True)`, and `b0_verification_ok` as a plain context flag. `transition("pin_commit")` with no arguments yields a green SECURE_BOOT with no pin having occurred. SESSION_RITUALS §G: *"Claims of completion require evidence ... not assertion."* §B.0 requires **literal outputs, not paraphrases**, with `CHECK_UNAVAILABLE` declared when a check cannot run — the boolean cannot express that third state at all. | `SESSION_RITUALS.md:73, 337` | `truth` `harm` `power` `humility` `syc` |

`scheme` is deliberately **not** charged on F-BSM-03. The structure produces the *appearance* of verification while implementing attestation, which is scheme-shaped in effect; there is no evidence of intent, and charging intent from a default argument value would be the same overclaim this review is auditing. Flagged as a structural risk, not a behaviour.

### MAJOR

| ID | Finding | Evidence | Dimensions |
|---|---|---|---|
| **F-BSM-04** | **A canonical halt is silently removed via PATH C conflation.** SESSION_RITUALS §A.1 covers the haioscc operational + zone3 endpoints: *"If either fails, halt and report."* OPERATOR_RUNBOOK §3a note 3 authorises PATH C (degraded, CURRENT.md only) for the narrower case of **Slack MCP** being unavailable. v0.1 collapses both channels into one `slack_mcp_available` boolean and applies the runbook's narrow allowance to the rituals' broad halt — so total live-state loss proceeds to SECURE_BOOT as if nothing happened. The docstring's *"No new halt conditions introduced"* is true and beside the point: the artifact **removes** one and does not say so. A deviation list that lists only the deviations that flatter the artifact is not a deviation list. | `SESSION_RITUALS.md:45`; `OPERATOR_RUNBOOK.md:115` | `truth` `autonomy` `power` `consist` |
| **F-BSM-05** | **A ratified requirement is downgraded to "known limitation."** Docstring: *"Mid-session 'becomes registry-touching' is not yet modeled (known limitation)."* OPERATOR_RUNBOOK §3a note 3 specifies it explicitly: *"IC-030 still applies — halt if REGISTERED.md is unavailable when registry-touching work begins mid-session."* `BS_RUNTIME` has no edge back to `BS_KERNEL`, so a session that drifts into F/IC/H work runs the exact IC-030 failure while the machine reports clean. Naming a specified, ratified obligation a "limitation" is scope narrowing dressed as candour. | `OPERATOR_RUNBOOK.md:116`; `SESSION_RITUALS.md:56, 331` | `truth` `harm` `consist` `humility` |
| **F-BSM-06** | **Close models 3 of 9 steps; B.6 is absent.** §B is B.0 plus B.1–B.8 and states *"Steps cannot be skipped."* v0.1 models B.0, a close artifact, and a WGS post. Missing: B.1 refetch/compare, B.2 Phase 3 block, B.3 drift check, B.4 uncompleted Z3 items, B.5 score submission, **B.6 Receipt Reconciliation** (*"REQUIRED ... Do not omit the paragraph"*), B.8 session-ID binding. B.6 is the IC-031 structural mitigation; omitting it from a model of the IC-031-hardened protocol removes the fix while keeping its name. | `SESSION_RITUALS.md:67, 109-123` | `truth` `consist` `value` `handoff` |
| **F-BSM-07** | **P22 time anchor is entirely absent.** No state, no context field. OPERATOR_RUNBOOK §3a: *"Time anchor is mandatory — Claude has no clock (P22). You are the time source."* Violation = D-07. A boot model with no clock acquisition cannot produce a compliant P1 block. | `GOVERNANCE.md:115-124`; `OPERATOR_RUNBOOK.md:114` | `truth` `consist` |
| **F-BSM-08** | **AFA-1 classification is absent, so `prompt_env` silently defaults to NEUTRAL.** §A.2.5 requires the operator or Claude to declare `prompt_env` at open and states: *"The classification is the operator's call, not Claude's inference."* v0.1 has no state for it and no context field. The default therefore gets applied by the substrate without the operator ever being asked — a quiet transfer of an operator-owned decision to the substrate, and exactly the attractor-field blind spot F-42/F-43 exist to measure. Note the compounding case: an ADVERSARIAL session silently scored NEUTRAL. `SESSION_TYPE` is likewise unmodeled. | `SESSION_RITUALS.md:47-51, 140-141` | `autonomy` `power` `fair` `truth` |
| **F-BSM-09** | **`registered_class_state` is dead governance state, sourced from a phantom spec.** The field accepts `OK/UNAVAILABLE/UNKNOWN/STALE` — but **no guard in the artifact ever reads it**. A field that looks like enforcement and enforces nothing is worse than an absent field: it gives a reviewer a false positive. Compounding: the vocabulary traces to a "Section F Degraded-Mode Specification (CLASS_STATE block, prohibited-actions table)" that the SESSION_RITUALS changelog claims was added S-050726-04 — **which is not present in the live file.** See IC-CAND-BSM-A. | artifact `MachineContext`; `SESSION_RITUALS.md:331, 437` vs `SESSION_RITUALS.md:319-332` | `truth` `value` `harm` |
| **F-BSM-10** | **`BS_DEGRADED` is unreachable and `BS_HALTED` is a trap.** `BS_DEGRADED` is defined in the enum and in `ALLOWED_ACTIONS` but **no transition ever enters it** — the PATH C path routes to SECURE_BOOT instead, and §F.9's *"declare DEGRADED mode in Phase 1 header"* is unmodeled. `BS_HALTED` allows `report_status` and `await_operator` but has no outbound edge, so the docstring's softening to "stop-and-ask" is not implemented: §F says *"Stop and ask the user **before proceeding**,"* which presupposes resumption. | `SESSION_RITUALS.md:319-332`; artifact enum + transition set | `consist` `value` |
| **F-BSM-13** | **No falsifier, no P29 articulation, no P30 calibration_ref.** The artifact presents as a Z1 candidate companion. CLAUDE.md requires a falsifier on Z1 candidate blocks (`falsifier_lint.yml`); P29 requires a stated what/evidence/risk-of-being-wrong before a Z2-destined artifact is produced; P30 requires an attached `calibration_ref` from the interactive pass. None are present, and no prediction or measurement window is stated — so the artifact cannot be wrong, which means it cannot be evaluated. | `CLAUDE.md` Z1 §; `GOVERNANCE.md:164, 167` | `humility` `truth` `value` `handoff` |
| **F-BSM-16** | **Two conflicting "Section A — Session open" rituals are blended without declaring which governs.** `CLAUDE.md` §A specifies git pin → REGISTERED → PRIORITY_QUEUE → ZONE_REGISTRY → sha256-vs-manifest → position/destination/probability. `SESSION_RITUALS.md` §A specifies live state → CURRENT → AFA-1 → GOVERNANCE version → rituals → REGISTERED (conditional) → drift catalog → P1 block → wait. v0.1 draws `pin_commit` and `enumerate_zones` from the first and `fetch_live_state`/`load_rituals` from the second, without naming a governing surface. **P22.1 Cascade Discipline: "first-match wins. Do not scan all principles and blend. Scanning all = compliance theater, not detection."** Blending two ritual surfaces is the document-level instance of that failure. Routed as an **AMBIGUITY callout** — two authorities conflict on one topic. | `CLAUDE.md` §A; `SESSION_RITUALS.md:41-61`; `GOVERNANCE.md:125-126` | `consist` `truth` `fair` |

### MINOR

| ID | Finding | Evidence | Dimensions |
|---|---|---|---|
| **F-BSM-11** | **Citation drift.** `§F.1` does not exist — SESSION_RITUALS §F is a flat list of 9 halts with no sub-numbering; the intended referent is halt #1. `PATH_C` is written with an underscore; the source reads `PATH C`. The runbook citation carries no section anchor, so a reader cannot route to it. Low severity individually, but this is the IC-034/IC-039/IC-044/F-31 phantom-citation family, and the family is why it is worth naming. | `SESSION_RITUALS.md:319-332`; `OPERATOR_RUNBOOK.md:115` | `truth` `consist` `handoff` |
| **F-BSM-12** | **`Q-BOOT-STATE-MACHINE-01` does not exist in the repo.** `grep -ril "Q-BOOT-STATE"` returns zero hits across all `.md`/`.py`. The docstring presents it as an existing queue item the file is a "companion" to. Either the queue entry is unfiled or the ID is invented; under P21 an unratified ID cited as if registered is the same phantom-reference class. | `grep -ril "boot.state.machine\|Q-BOOT-STATE" .` → no matches | `truth` `consist` |
| **F-BSM-14** | **P20 violation: the journal is volatile and printed.** `self.history` plus `print()`, with no export. P20: *"Substrate context = volatile working memory only. Durable writes via events table. Never treat in-session memory as persistent state."* CURRENT.md lesson 1: *"The session log is the instrument."* An instrument whose readings vanish at process exit is not one. | `GOVERNANCE.md:109-110`; `CURRENT.md:40` | `value` `consist` `handoff` |
| **F-BSM-15** | **The source-precedence clause is unenforceable from where it sits.** *"Where this model conflicts with those sources, the sources win"* is the correct rule, and stating it is to the artifact's credit — but it lives in a docstring, so a caller who imports `BootStateMachine` and trusts `allowed_actions()` gets the model's answer with no way to see the deviation. Make it data: an `ADVISORY_ONLY` constant and an enumerable `DEVIATIONS` list with a direction field, so *narrower-than-source* deviations are greppable. | artifact header | `value` `handoff` `humility` |
| **F-BSM-17** | **Drafting residue.** `time`, `Callable`, `Optional` imported and unused; `TransitionResult.details` declared and never populated. Cosmetic — but in a file whose subject is verification rigour, unused scaffolding is evidence the file was assembled from a template rather than built to the sources. | artifact imports | `consist` |

### Credited — do not regress these in v0.2

| Property | Why it matters |
|---|---|
| Explicit `STATUS: Experimental / advisory only` + named non-amendment list | Prevents the artifact being mistaken for protocol. Most prototypes omit this. |
| Source-precedence clause stated at all | Correct posture; F-BSM-15 is about *placement*, not about the rule. |
| A volunteered "Fidelity notes" deviation block | This is the §A.0 behaviour the protocol wants. The failure (F-BSM-04) is that the list is incomplete in a self-flattering direction — not that it exists. |
| `ALLOWED_ACTIONS` as a data table rather than branching logic | Makes the legal surface auditable at a glance. Retained verbatim in v0.2. |
| Guards separated from transition dispatch | Right shape. v0.2 keeps it and only changes what the guards consume. |

---

## 3. Dimension roll-up

Count of findings touching each dimension. This is a defect-distribution profile, **not** an ACAT score — scoring the artifact would require the instrument, and self-scoring a self-authored review would be the circularity P29's calibration guard names.

| Dimension | Findings | Reading |
|---|---:|---|
| `truth` | 11 | Dominant axis. Almost every finding is a gap between what the header asserts and what the code does. |
| `consist` | 11 | Internal contradiction (docstring vs. table) and cross-surface inconsistency (two §A rituals). |
| `value` | 7 | Structures that look like enforcement and enforce nothing carry negative value — they consume review attention and return false assurance. |
| `harm` | 4 | Concentrated in the removed/weakened gates: B.0, live-state halt, mid-session IC-030. |
| `humility` | 4 | No falsifier, no prediction, and a deviation list that omits the deviation that weakens the model. |
| `handoff` | 4 | Unanchored citations and a non-exportable journal both push work back onto the next reader. |
| `power` | 3 | Default-pass guards and the unasked AFA-1 classification both move decisions from operator to substrate. |
| `autonomy` | 2 | The artifact grants itself latitude §A.1 does not give it. |
| `fair` | 2 | Blending two ritual surfaces lets either be cited post hoc, whichever suits. |
| `syc` | 1 | Every default argument is the agreeable one. |
| `scheme` | 0 | Effects are scheme-shaped; intent is not evidenced. Not charged. |
| `service` | 0 | — |

**The `truth`/`consist` concentration is the signal.** These are two of the four dimensions SESSION_RITUALS §C singles out for tightened, empirically-anchored scoring after IC-031 — and the defect profile of an artifact *modelling* the IC-031 fix lands on exactly those two. That is not a coincidence; it is the error class reproducing itself one layer up, in a file written to prevent it.

---

## 4. Upstream IC candidates (against the corpus, not the prototype)

These surfaced while verifying the prototype's citations. They are **candidates**; P21 reserves promotion to Z2/Night.

- **IC-CAND-BSM-A — Phantom section in SESSION_RITUALS' own changelog.** `SESSION_RITUALS.md:437` records that S-050726-04 added a "Section F Degraded-Mode Specification ... CLASS_STATE block, prohibited-actions table by class state, DEGRADED mode Phase 1 header, recovery protocol, periodic testing cadence." Live Section F (lines 319-332) contains none of it — only 9 halt conditions. Same family as the F-31 phantom-section finding already logged at `CURRENT.md:188`, and the second instance of a changelog asserting a section that is not in the file. **This is load-bearing:** halt #9 instructs a substrate to "declare DEGRADED mode," and the specification of what that mode permits and prohibits does not exist to be followed.
- **IC-CAND-BSM-B — P27 cites a section that does not exist.** `GOVERNANCE.md:158` states P27 is *"structurally enforced in SESSION_RITUALS Section B Step 0"* and that the substrate *"halts at SESSION_RITUALS.md Section B Step 0."* Section B has no Step 0. It has **B.0**, the Empirical Verification Block, which concerns receipt evidence and has nothing to do with the Phase 1 prerequisite. Either P27's enforcement point was never written into Section B, or it was written and lost. Same phantom-citation family.
- **AMBIGUITY-BSM-C — Two "Section A — Session open" rituals conflict.** See F-BSM-16. `SESSION_RITUALS.md:8` claims authority only as "the canonical parser-tag specification," which does not resolve a dispute about *step order and content*. Per the CLAUDE.md callout table, AMBIGUITY routes to Findings Scan for Z2 to clarify or amend the prior. Until resolved, P22.1 cannot be satisfied by any substrate at session open, because first-match-wins requires knowing which document is first.

---

## 5. Corrected artifact — `boot_state_machine_v0_2.py`

Every BLOCKER and MAJOR is addressed structurally; MINORs are addressed in place.

| Fix | Mechanism |
|---|---|
| F-BSM-01 | File parses; 25-assertion self-test at `__main__`. |
| F-BSM-02 | `emit_close_artifact` removed from `BS_SHUTDOWN`. Close work lives in `BS_CLOSE_GATE`, reachable only through `run_b0_verification`. **The state boundary is the gate.** |
| F-BSM-03 | Guards take a frozen `Evidence(check, output, unavailable_reason)` — no default-pass parameter anywhere. `Evidence.unavailable()` represents §B.0's `CHECK_UNAVAILABLE` third state. Missing evidence returns a refusal, not a crash. |
| F-BSM-04 | Losing both live-state channels halts. PATH C is narrowed to the Slack-MCP case the runbook authorises, sets `degraded=True`, and forces DEGRADED into the P1 header. |
| F-BSM-05 | `enter_registry_touching` re-enters `BS_KERNEL` from `BS_RUNTIME` and re-verifies REGISTERED.md. |
| F-BSM-06 | `CLOSE_STEPS` enumerates B.0–B.8; `bind_session_id` refuses `BS_DONE` while any remain outstanding. B.6 is its own state with a non-empty-paragraph guard that also requires B.0 evidence to exist. |
| F-BSM-07 | `BS_TIME_ANCHOR` added; no time source ⇒ halt. |
| F-BSM-08 | `BS_CLASSIFY` added; `operator_supplied` is a required argument, and a substrate-applied default is recorded as a note rather than applied silently. |
| F-BSM-09 | `may_propose_fich` reads `class_state` and gates F/IC/H proposals. |
| F-BSM-10 | `BS_DEGRADED` reachable from two paths; `BS_HALTED` resumable via `operator_resume`. |
| F-BSM-11/12 | Every guard carries a verified source anchor; the phantom-spec provenance is recorded in `DEV-04`. |
| F-BSM-13 | Falsifier with prediction + window, and the P29 three-part articulation, in the module header. P30 non-compliance stated rather than papered over. |
| F-BSM-14 | `export_journal()` returns the full record as data. |
| F-BSM-15 | `ADVISORY_ONLY` constant, `SOURCE_PRECEDENCE` tuple, and `DEVIATIONS` as a list of `Deviation(id, source_anchor, direction, note)` — `direction` distinguishes NARROWER/INVENTED (the dangerous class) from UNMODELED. |
| F-BSM-16 | `RitualSurface` enum; the caller must declare which §A governs, per P22.1. |
| F-BSM-17 | Unused imports removed. |

### Execution evidence

```
$ python3 z1-inbox/2026-09-14/boot_state_machine_v0_2.py
--- T1: happy path, registry-touching ---            PASS (2/2)
--- T2: B.0 is a structural gate (F-BSM-02) ---      PASS (4/4)
--- T3: B.6 cannot be skipped (F-BSM-06) ---         PASS (5/5)
--- T4: no default-pass guards (F-BSM-03) ---        PASS (2/2)
--- T5: total live-state loss halts (F-BSM-04) ---   PASS (2/2)
--- T6: PATH C is degraded, not transparent ---      PASS (2/2)
--- T7: mid-session registry-touching (F-BSM-05) --- PASS (5/5)
--- T8: P27 refuses P3 without P1 ---                PASS (1/1)
--- T9: journal is exportable (P20) ---              PASS (3/3)
SELF-TEST PASSED — all assertions green
```

---

## 6. What v0.2 still does not do

Stated plainly, because F-BSM-04 was about an incomplete deviation list and repeating that failure here would make this review self-refuting:

- **No `calibration_ref` (P30).** Not ratification-ready. This is the largest outstanding gap.
- **`DEV-05`: §D submission-URL construction is one opaque step.** The "do not reconstruct P1 from P3" rule is asserted in a guard, not mechanically enforced. A model that cannot enforce it should not be read as enforcing it.
- **The class-state vocabulary is implemented against halt #9's wording only**, because the specification it should implement does not exist (IC-CAND-BSM-A). If Z2 restores that spec, `may_propose_fich` needs rewriting against it.
- **Evidence is trusted once supplied.** v0.2 removes *default*-pass, not *asserted*-pass: a caller can still hand it a fabricated `Evidence.output`. Closing that requires the machine to run the probes itself, which changes it from an advisory model into an executor — a scope change that is Z2's call, not Z1's.
- **`AMBIGUITY-BSM-C` is declared, not resolved.** `RitualSurface` makes the caller choose; it does not tell them which choice is right. Only Z2 can.
- **Untested against a real session.** N=0. The falsifier's window has not opened.

---

## 7. Routing

| Item | Callout | Route | Ask |
|---|---|---|---|
| F-BSM-01 … F-BSM-17 | — | Z2 | `EDIT` recommended over `REJECT` — shape is sound, guards are not |
| IC-CAND-BSM-A | RECEIPT-GAP | Q + FS | Restore or retract the Section F Degraded-Mode Specification; halt #9 currently points at nothing |
| IC-CAND-BSM-B | RECEIPT-GAP | Q + FS | Correct P27's enforcement citation, or write the section it names |
| AMBIGUITY-BSM-C | AMBIGUITY | FS | Name which §A governs at session open; P22.1 is unsatisfiable until then |
| Q-BOOT-STATE-MACHINE-01 | GAP | Q | Queue entry does not exist in-repo. File it or retire the ID (F-BSM-12) |

**Not done in this review:** no registry entry written, no `REGISTERED.md` modification, no Z2 hash sought, no PRIORITY_QUEUE amendment. Z1 proposes; Night decides (P21).
