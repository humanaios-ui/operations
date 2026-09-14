# Q-BOOT-STATE-MACHINE-01 — Adversarial Review

**Status:** Z1 CANDIDATE — advisory, unratified. Not a registry entry.
**Reviewer:** Z1 (Claude)
**Date:** 2026-09-14 · rev 2 (second adversarial round applied)
**Artifact under review:** `boot_state_machine.py` v0.1 — preserved verbatim at `z1-inbox/2026-09-14/boot_state_machine_v0_1_AS_REVIEWED.py.txt`
**Corrected artifact produced:** `z1-inbox/2026-09-14/boot_state_machine_v0_2.py` (now at v0.3)
**Repo SHA pinned for source verification:** `6d3443af07ba18db56c1d716e24c1f9f33b2b056`
**Sources read at that SHA:** `SESSION_RITUALS.md` (v6.4.1), `GOVERNANCE.md` (v6.4.3), `OPERATOR_RUNBOOK.md`, `CURRENT.md`, `CLAUDE.md`, `tools/acat_session_validator.py`
**Review posture:** ADVERSARIAL — the working assumption is that the artifact's self-description overstates its fidelity, and every claim in its docstring is treated as a hypothesis to falsify against the pinned sources. §8 applies that same posture to this review.

---

## 0. P29 Articulation Gate

**What this artifact is:** a findings register for a prototype state machine, plus a corrected implementation.
**What evidence supports it:** every finding cites a file and section verified at the pinned SHA; the reviewed input is committed verbatim so the findings are reproducible against their actual subject; the corrected implementation ships a 43-assertion self-test whose literal output is quoted in §5.
**Risk of being wrong, and how it would be detected:** the main risk is that I have read a *narrower* protocol than the operator intends — e.g. that PATH C is meant to be broader than `OPERATOR_RUNBOOK §3a note 3` states. Detected by Z2 rejecting F-BSM-04 with a wider reading, which would also retire F-BSM-16.

**P30 note:** no `calibration_ref` is attached. Per P30 this artifact has **not cleared the calibration gate** and is not ratification-ready. It is filed as a Z1 working document.

---

## Falsifier

**PREDICTION.** Across N=10 sessions driven through `boot_state_machine_v0_2.py`, zero sessions reach `BS_DONE` while any SESSION_RITUALS Section B step (B.0–B.8) is unexecuted, and zero sessions that the machine reports clean trip a Section F halt condition.

**FALSIFIED IF** either count is non-zero: a session reaches `BS_DONE` with an outstanding close step, or a Section F halt fires in a session the machine passed.

**WINDOW.** 10 sessions or 30 days from ratification, whichever comes first.

**MEASUREMENT SURFACE.** `export_journal()["close_steps_outstanding"]` at `BS_DONE`, compared against `CLOSE_STEPS`.

**WHAT A NULL RESULT MEANS.** If fewer than 10 sessions run the machine in the window, the result is VOID, not confirmed — per the VOID callout trigger, an experiment that runs but produces no evaluable outcome falsifies nothing and must be retired or re-scoped rather than reported as support.

> The v0.2 falsifier targeted `BS_JOURNAL` and was therefore false on its face: B.7 and B.8 are executed *from* that state, so every clean session entered it with two steps outstanding. Caught in round two (R2-14). Retargeted to `BS_DONE`.

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
| **F-BSM-01** | **Artifact does not parse.** The file ends at `else:` inside `_do_load_governance_current` with no block body. The header nevertheless reports results "from red-team test" and a list of confirmed fidelity properties. A file that raises `IndentationError` at import cannot have produced them. This is a receipt-overstatement instance at file scope — assertions about behaviour the artifact cannot exhibit. | `python3 -c "ast.parse(...)"` on the preserved input → `IndentationError: expected an indented block after 'else' statement` | `truth` `consist` `humility` |
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

### Credited — do not regress these

| Property | Why it matters |
|---|---|
| Explicit `STATUS: Experimental / advisory only` + named non-amendment list | Prevents the artifact being mistaken for protocol. Most prototypes omit this. |
| Source-precedence clause stated at all | Correct posture; F-BSM-15 is about *placement*, not about the rule. |
| A volunteered "Fidelity notes" deviation block | This is the §A.0 behaviour the protocol wants. The failure (F-BSM-04) is that the list is incomplete in a self-flattering direction — not that it exists. |
| `ALLOWED_ACTIONS` as a data table rather than branching logic | Makes the legal surface auditable at a glance. Retained verbatim. |
| Guards separated from transition dispatch | Right shape. Only what the guards consume has changed. |

---

## 3. Dimension roll-up

Count of findings touching each dimension. This is a defect-distribution profile, **not** an ACAT score — scoring the artifact would require the instrument, and self-scoring a self-authored review would be the circularity P29's calibration guard names.

The counts below are **derived from the Dimensions column above, not asserted.** Rev 1 asserted them by hand and got three of them wrong (`truth` 11→13, `consist` 11→12, `handoff` 4→5, and `humility` 4→5 which nobody caught but was also wrong). Recomputing is the fix; the miscount itself is recorded as R2-15 in §8.

| Dimension | Findings | Reading |
|---|---:|---|
| `truth` | 13 | Dominant axis. Almost every finding is a gap between what the header asserts and what the code does. |
| `consist` | 12 | Internal contradiction (docstring vs. table) and cross-surface inconsistency (two §A rituals). |
| `value` | 7 | Structures that look like enforcement and enforce nothing carry negative value — they consume review attention and return false assurance. |
| `humility` | 5 | No falsifier, no prediction, and a deviation list that omits the deviation that weakens the model. |
| `handoff` | 5 | Unanchored citations and a non-exportable journal both push work back onto the next reader. |
| `harm` | 4 | Concentrated in the removed/weakened gates: B.0, live-state halt, mid-session IC-030. |
| `power` | 3 | Default-pass guards and the unasked AFA-1 classification both move decisions from operator to substrate. |
| `autonomy` | 2 | The artifact grants itself latitude §A.1 does not give it. |
| `fair` | 2 | Blending two ritual surfaces lets either be cited post hoc, whichever suits. |
| `syc` | 1 | Every default argument is the agreeable one. |
| `scheme` | 0 | Effects are scheme-shaped; intent is not evidenced. Not charged. |
| `service` | 0 | — |

Total dimension-hits: 54 across 17 findings.

**The `truth`/`consist` concentration is the signal.** These are two of the four dimensions SESSION_RITUALS §C singles out for tightened, empirically-anchored scoring after IC-031 — and the defect profile of an artifact *modelling* the IC-031 fix lands on exactly those two. That is not a coincidence; it is the error class reproducing itself one layer up, in a file written to prevent it. §8 shows it reproducing a second time, in this review.

---

## 4. Upstream IC candidates (against the corpus, not the prototype)

These surfaced while verifying the prototype's citations. They are **candidates**; P21 reserves promotion to Z2/Night.

- **IC-CAND-BSM-A — Phantom section in SESSION_RITUALS' own changelog.** `SESSION_RITUALS.md:437` records that S-050726-04 added a "Section F Degraded-Mode Specification ... CLASS_STATE block, prohibited-actions table by class state, DEGRADED mode Phase 1 header, recovery protocol, periodic testing cadence." Live Section F (lines 319-332) contains none of it — only 9 halt conditions. Same family as the F-31 phantom-section finding already logged at `CURRENT.md:188`, and the second instance of a changelog asserting a section that is not in the file. **This is load-bearing:** halt #9 instructs a substrate to "declare DEGRADED mode," and the specification of what that mode permits and prohibits does not exist to be followed.
- **IC-CAND-BSM-B — P27 cites a section that does not exist.** `GOVERNANCE.md:158` states P27 is *"structurally enforced in SESSION_RITUALS Section B Step 0"* and that the substrate *"halts at SESSION_RITUALS.md Section B Step 0."* Section B has no Step 0. It has **B.0**, the Empirical Verification Block, which concerns receipt evidence and has nothing to do with the Phase 1 prerequisite. Either P27's enforcement point was never written into Section B, or it was written and lost. Same phantom-citation family.
- **AMBIGUITY-BSM-C — Two "Section A — Session open" rituals conflict.** See F-BSM-16. `SESSION_RITUALS.md:8` claims authority only as "the canonical parser-tag specification," which does not resolve a dispute about *step order and content*. Per the CLAUDE.md callout table, AMBIGUITY routes to Findings Scan for Z2 to clarify or amend the prior. Until resolved, P22.1 cannot be satisfied by any substrate at session open, because first-match-wins requires knowing which document is first.
- **AMBIGUITY-BSM-D (new, round two) — §A.1 and Z2-GOVARCH-02 conflict on live-state failure.** `SESSION_RITUALS.md:45` requires fetching both haioscc endpoints and halting if either fails. `CURRENT.md:157, 170` (Z2-GOVARCH-02, ratified S-060826-04) makes WGS the Class 1 primary and demotes haioscc to secondary cross-check, stating it is *"unreachable from Claude's bash environment."* Read literally and together, **every Claude session must halt at open**, because a demoted-and-unreachable endpoint fails §A.1 every time. Surfaced while implementing the guard — v0.3 models "both down halts, one down degrades" and records the divergence as `DEV-07`. Z2 should say which reading governs.

---

## 5. Corrected artifact — `boot_state_machine_v0_2.py` (v0.3)

Every BLOCKER and MAJOR is addressed structurally; MINORs are addressed in place. Round-two fixes are in §8.

| Fix | Mechanism |
|---|---|
| F-BSM-01 | File parses; 43-assertion self-test at `__main__`. |
| F-BSM-02 | `emit_close_artifact` removed from `BS_SHUTDOWN`. Close work lives in `BS_CLOSE_GATE`, reachable only through `run_b0_verification`. **The state boundary is the gate.** |
| F-BSM-03 | Guards take a frozen `Evidence(check, output, unavailable_reason, family)` — no default-pass parameter anywhere. `Evidence.unavailable()` represents §B.0's `CHECK_UNAVAILABLE` third state. Missing evidence returns a refusal, not a crash. |
| F-BSM-04 | Losing both live-state channels halts. PATH C is narrowed to the Slack-MCP case the runbook authorises, records a named degradation cause, and forces DEGRADED into the P1 header. |
| F-BSM-05 | `enter_registry_touching` re-enters `BS_KERNEL` from `BS_RUNTIME` and re-verifies REGISTERED.md. |
| F-BSM-06 | `CLOSE_STEPS` enumerates B.0–B.8; `bind_session_id` refuses `BS_DONE` while any remain outstanding. B.6 is its own state and must quote a recorded B.0 check. |
| F-BSM-07 | `BS_TIME_ANCHOR` added; no time source ⇒ halt. |
| F-BSM-08 | `BS_CLASSIFY` added; a non-operator classification is discarded and the protocol default NEUTRAL applied, with the discard recorded. |
| F-BSM-09 | `may_propose_fich` gates a real `propose_fich` transition. |
| F-BSM-10 | `BS_DEGRADED` reachable with named causes; `BS_HALTED` resumes into the interrupted state so the failed guard re-runs. |
| F-BSM-11/12 | `SOURCE_ANCHORS` maps every action to its verified anchor and is asserted complete by T10; the phantom-spec provenance is `DEV-04`. |
| F-BSM-13 | Falsifier with prediction, window and measurement surface; P29 three-part articulation in the module header. P30 non-compliance stated rather than papered over. |
| F-BSM-14 | `export_journal()` returns the full record as data, untruncated. |
| F-BSM-15 | `ADVISORY_ONLY`, `SOURCE_PRECEDENCE`, `SOURCE_ANCHORS`, and `DEVIATIONS` as `Deviation(id, source_anchor, direction, note)` — `direction` distinguishes NARROWER/INVENTED (the dangerous class) from UNMODELED. |
| F-BSM-16 | `ritual_surface` is a required constructor argument with no default; unsupported surfaces raise rather than being approximated. |
| F-BSM-17 | Unused imports removed; `TransitionResult.details` populated on every transition. |

### Execution evidence

Literal output, unedited. Rev 1 quoted a `PASS (n/n)` summary format the self-test has never emitted — a paraphrased receipt in a review about paraphrased receipts (R2-16, §8).

```
$ python3 z1-inbox/2026-09-14/boot_state_machine_v0_2.py

--- T1: happy path, registry-touching ---
  PASS  reaches RUNTIME
  PASS  may propose F/IC/H
  PASS  propose_fich accepted

--- T2: B.0 is a structural gate (F-BSM-02, R2-01) ---
  PASS  in SHUTDOWN
  PASS  close artifact illegal in SHUTDOWN
  PASS  empty B.0 refused
  PASS  B.0 refused: touched family unevidenced (R2-01)
  PASS  B.0 advances once family evidenced

--- T3: close steps need evidence, not strings (R2-02) ---
  PASS  string list rejected
  PASS  in RECONCILE

--- T4: B.6 must quote B.0 (F-BSM-06, R2-04) ---
  PASS  empty reconciliation refused
  PASS  unheaded paragraph refused
  PASS  unquoted paragraph refused
  PASS  quoting paragraph accepted

--- T5: B.8 ordering and pattern (R2-05, R2-13) ---
  PASS  B.8 refused while B.7 outstanding
  PASS  B.8 NOT recorded on refusal (R2-05)
  PASS  loose session id rejected (R2-13)
  PASS  clean close reaches DONE
  PASS  no outstanding close steps

--- T6: no default-pass guards (F-BSM-03) ---
  PASS  anchor_time without evidence is refused
  PASS  outcome is REFUSED, not a silent pass
  PASS  still in TIME_ANCHOR

--- T7: live-state paths (F-BSM-04, R2-10) ---
  PASS  both channels down → HALTED
  PASS  outcome DIVERTED, not ADVANCED (R2-08)
  PASS  guard_passed is False on divert
  PASS  resume returns to interrupted state (R2-11)
  PASS  PATH C proceeds degraded
  PASS  haioscc down is degraded, not 'OK' (R2-10)

--- T8: mid-session registry-touching (F-BSM-05, R2-03) ---
  PASS  F/IC/H barred after skip
  PASS  propose_fich actually refused (R2-03)
  PASS  re-entered KERNEL
  PASS  STALE → DEGRADED (§F.9)
  PASS  wrong-cause recovery refused (R2-11)

--- T9: P1 completeness and AFA-1 (R2-06, R2-12) ---
  PASS  non-operator prompt_env discarded → NEUTRAL (R2-12)
  PASS  operator_supplied recorded False
  PASS  P1 refused without drift catalog (R2-06)

--- T10: contract self-checks ---
  PASS  P3-without-P1 halts (P27)
  PASS  every action has a source anchor (P29 part 2)
  PASS  unsupported ritual surface refused (R2-07)
  PASS  journal carries full evidence records (R2-09)
  PASS  journal keeps deviation direction (R2-09)
  PASS  journal declares advisory status
  PASS  journal does not truncate literal output (R2-09)

==============================================================
SELF-TEST PASSED — all assertions green
==============================================================
```

43 assertions, 0 failures.

---

## 6. What v0.3 still does not do

Stated plainly, because F-BSM-04 was about an incomplete deviation list and repeating that failure here would make this review self-refuting.

- **No `calibration_ref` (P30).** Not ratification-ready. This is the largest outstanding gap.
- **`DEV-05`: §D submission-URL construction is one opaque step.** The "do not reconstruct P1 from P3" rule is in the step label, not mechanically enforced.
- **`DEV-06`: B.7 is asserted-pass.** `post_wgs` records a draft id; it cannot confirm a draft exists. A fabricated id satisfies the step. Closing it needs Slack credentials, which converts an advisory model into an executor — Z2's call, not Z1's.
- **`DEV-08`: the session-ID pattern is restated, not imported** from `tools/acat_session_validator.py:33`, so the two can drift.
- **Evidence is trusted once supplied.** v0.3 removes *default*-pass, not *asserted*-pass: a caller can still hand it a fabricated `Evidence.output`. This is the same class as DEV-06 and has the same resolution.
- **The class-state vocabulary is implemented against halt #9's wording only**, because the specification it should implement does not exist (IC-CAND-BSM-A).
- **Only `RitualSurface.SESSION_RITUALS` is implemented.** CLAUDE_MD and BOTH_DECLARED raise. `AMBIGUITY-BSM-C` is declared, not resolved — only Z2 can.
- **Untested against a real session.** N=0. The falsifier's window has not opened.

---

## 7. Routing

| Item | Callout | Route | Ask |
|---|---|---|---|
| F-BSM-01 … F-BSM-17, R2-01 … R2-16 | — | Z2 | `EDIT` recommended over `REJECT` — shape is sound, guards are not |
| IC-CAND-BSM-A | RECEIPT-GAP | Q + FS | Restore or retract the Section F Degraded-Mode Specification; halt #9 currently points at nothing |
| IC-CAND-BSM-B | RECEIPT-GAP | Q + FS | Correct P27's enforcement citation, or write the section it names |
| AMBIGUITY-BSM-C | AMBIGUITY | FS | Name which §A governs at session open; P22.1 is unsatisfiable until then |
| AMBIGUITY-BSM-D | AMBIGUITY | FS | §A.1 halt vs Z2-GOVARCH-02 demotion: read literally, every Claude session halts at open |
| F-CAND-BSM-E | — | Q + FS | Candidate finding, §8: adversarial review of an error class reproduces that error class in the reviewer's own output. Two independent rounds, same profile. |
| Q-BOOT-STATE-MACHINE-01 | GAP | Q | Queue entry does not exist in-repo. File it or retire the ID (F-BSM-12) |

**Not done in this review:** no registry entry written, no `REGISTERED.md` modification, no Z2 hash sought, no PRIORITY_QUEUE amendment. Z1 proposes; Night decides (P21).

---

## 8. Second round — findings against *this review* and its v0.2

An automated reviewer (Copilot) examined the rev-1 submission on PR #332. Its findings are recorded here in full, unsoftened, because the alternative — quietly patching them — is the receipt-overstatement behaviour this document was written to charge.

**The result is the interesting part.** Nine of sixteen round-two findings are the *same defect classes* this review charged against v0.1, reproduced inside the code written to fix them:

| Round 2 | Reproduces | What survived the fix |
|---|---|---|
| R2-01 | F-BSM-03 (assertion-as-verification) | B.0 advanced on *any* non-empty evidence list; two arbitrary entries satisfied a gate §B.0 defines by check family |
| R2-02 | F-BSM-03 | `run_close_sequence` took caller-supplied step *strings*; `list(CLOSE_STEPS[1:6])` marked B.1–B.5 done with nothing performed |
| R2-03 | **F-BSM-09 exactly** | `may_propose_fich` was exposed and no transition consulted it — dead governance state, in the remedy for dead governance state |
| R2-04 | F-BSM-06 | B.6 passed on any non-empty paragraph; `"done"` advanced to BS_JOURNAL |
| R2-05 | — | `bind_session_id` recorded B.8 *before* checking prerequisites, so a refused call still journaled the step as complete |
| R2-06 | F-BSM-06 | `emit_p1_declaration` never checked §A.5 ran, and omitted `pinned_sha` |
| R2-07 | **F-BSM-16 exactly** | `RitualSurface` defaulted rather than forcing a choice, and CLAUDE_MD selected one extra state rather than that surface's sequence — P22.1 blending, inside the P22.1 fix |
| R2-08 | F-BSM-17 | `success` was True for guard failures diverting to HALTED; `details` stayed unpopulated despite F-BSM-17 naming it |
| R2-09 | F-BSM-14 | `export_journal` truncated evidence at 200 chars and reduced DEVIATIONS to bare IDs, discarding `direction` — the safety signal |
| R2-10 | F-BSM-04 | Returned "Live state OK" with haioscc unreachable; skipped the evidence check on the PATH C branch |
| R2-11 | F-BSM-10 | `operator_resume` funnelled every halt cause into DEGRADED without re-running the failed guard; recovery cleared degradation regardless of cause |
| R2-12 | F-BSM-08 | `classify_session` accepted the caller's `prompt_env` even when `operator_supplied=False` — substrate inference recorded as protocol default |
| R2-13 | — | `bind_session_id` accepted any `S-` prefix, ignoring the pattern `tools/acat_session_validator.py:33` already enforces |
| R2-14 | F-BSM-13 | The falsifier targeted `BS_JOURNAL`, which every clean session falsifies on entry — a prediction false by construction |
| R2-15 | **F-BSM-01 class** | The §3 roll-up asserted counts that do not match the table above it (truth 11≠13, consist 11≠12, handoff 4≠5, humility 4≠5) |
| R2-16 | **F-BSM-01 class** | §5 quoted a `PASS (n/n)` transcript the self-test has never emitted — a paraphrased receipt presented as literal output, in a review charging exactly that |

All sixteen are fixed in v0.3 and covered by the assertions in §5.

Two round-two observations were **not** adopted, with reasons:
- *"Include the reviewed input so findings are reproducible."* Adopted, and it was correct: v0.1 is now committed verbatim at `boot_state_machine_v0_1_AS_REVIEWED.py.txt` with a `.txt` suffix so no runner collects a deliberately non-parsing file.
- *"B.7 does not call `slack_send_message_draft`, so a fabricated draft id satisfies the close sequence."* Correct, and **not fixed** — it is recorded as `DEV-06` instead. Fixing it requires the machine to hold Slack credentials, which changes an advisory model into an executor. That is a scope change Z2 authorises, not Z1.

### F-CAND-BSM-E — candidate finding

**Claim.** Adversarial review of an error class does not confer immunity to that error class. Across two independent rounds on the same artifact family, the reviewer's own output reproduced the defect profile it had just charged — concentrated, both times, on `truth` and `consist`.

**Evidence.** 9 of 16 round-two findings map one-to-one onto round-one findings (table above). Two (R2-03, R2-07) are the round-one finding reproduced *inside its own remedy*. Two more (R2-15, R2-16) are receipt overstatement in a document whose subject is receipt overstatement.

**Why it matters.** F-45 (Stateless-Substrate Correction Locus) already establishes that substrate-level commitments do not persist. This is the stronger adjacent claim: they do not hold *within* a single session either, even seconds after the substrate has articulated the rule in writing. If that generalises, in-session articulation is not a mitigation for the class it articulates, and the only reliable locus is an external check — which is what happened here.

**Falsifier.** Across N=5 artifacts that carry an explicit adversarial review of a named error class, fewer than 20% of second-round findings map onto first-round findings of the same class. Falsified if the rate holds at or above 50% (observed here: 9/16 = 56%). Window: 5 artifacts or 60 days.

**Confounder, stated.** N=1 artifact, one substrate, one reviewer, and the round-two reviewer was automated and may over-index on structural symmetry. This is a candidate, not a finding. P21 reserves promotion to Night.
