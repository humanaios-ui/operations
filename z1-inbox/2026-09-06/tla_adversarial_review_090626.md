# Adversarial review — HumanAIOS_Final.tla v7.1 + .cfg
Z1 · 2026-09-06 · method: read + TLC 2.19 model check (tla2tools.jar from github.com/tlaplus, run in this session) · all findings VERIFIED-LIVE by run unless marked

## Grade: NOT integration grade. Not verification grade either — it has never been run.
The header lists ten amendments as done. TLC finds the spec does not parse. Every amendment is a claim; none left a receipt. Same failure class as the fifteen Phase 1 audits: status adjectives ("Final", "atomic", "terminal", "enforced") with no run behind them. The one honest line is the last: "to be discharged by TLC on a machine that has the toolchain." This machine had it in 40 seconds.

## Findings (in the order TLC hit them)

| # | finding | evidence | severity | fix |
|---|---|---|---|---|
| 1 | **Does not parse.** `CredPolicy(p) WITH cred := cred'` (line 227) — `WITH` is not a TLA+ expression operator | TLC parse error, line 227 col 63 | blocks everything | `CredPolicyOf(c)` taking a value; call with `cred'[p]` (patched) |
| 2 | **Config contradicts spec.** `.cfg` sets `Principals = {P1, A1, C1}` (model values); spec `ASSUME Principals ⊆ STRING` | "Assumption line 36 is false" | blocks run | quote them, or drop the STRING assumption |
| 3 | **Unbounded domain.** `Observation.value : Int` — TLC cannot enumerate `∃ obs ∈ Observation`; the field is also never read (dead state) | "can't enumerate Int" | blocks run | bound or delete `value` |
| 4 | **Dead constants.** `N`, `Cores` declared, assumed, never used | read | smell | delete or use |
| 5 | **Unbounded history.** `hist` grows without bound; no CONSTRAINT → infinite state space | read; needed `Len(hist[p]) ≤ 1` to finish | blocks run | state constraint in cfg |
| 6 | **P11 false at depth 2.** `Observe(p, poison)` sets signal=floor ⇒ `MandatoryEscalate(p)` true, but priority stays 100. Amendment 3 ("escalation is atomic: detection + enforcement") is false: detection is in `Observe`, enforcement is a *separate* action | Inv violated, 2 states | **core claim false** | either make `Observe` enforce inline, or restate P11 as an action property: every step from a MandatoryEscalate state that isn't an enforcement step is disallowed |
| 7 | **QUARANTINE not terminal for resources.** `ApplyPolicy` has no status guard; on a quarantined principal it sets cpu_limit 0 → 5. Amendment 6 false; P17 and Safety violated | Inv violated, depth 5, trace in run log | **core claim false** | guard `ApplyPolicy` with `status[p] ∉ {"QUARANTINE"}` (and probably SUSPENDED) |
| 8 | **P18 is vacuous.** `CompleteAttestation(p,TRUE) ⇒ cred' = cred` — the action itself conjoins `cred' = cred`. The property checks the action against its own definition. Also unchecked: cfg comments it out, and it is written as an invariant with a primed variable, which TLC rejects | read | overclaimed | state as `[][∀p: CompleteAttestation(p,TRUE) ⇒ cred'[p]=cred[p]]_vars` and check it as a PROPERTY — it will pass trivially; the *real* P18 is "no action other than AdvanceProbation increases cred," which is not written anywhere |
| 9 | **The laundering witness doesn't witness.** `LaunderReputation` is claimed to violate P18. P18 quantifies over `CompleteAttestation` steps; a `LaunderReputation` step is not one, so the implication is vacuously true and no counterexample exists | read (not run — CLAIM by reasoning) | claimed proof artifact is empty | write the real P18 (finding 8); then Launder violates it |
| 10 | **8 of 10 adversary actions are `== FALSE`.** Sybil, collusion, attestation race, SLO gaming, mmap drift, escalation-budget exhaustion, recovery gaming, identity bleach — the named threat model is unmodeled. The "boundary-respecting adversary" is two actions: inject an observation, force a floor | read | the safety claim covers ~20% of the stated threat model | model them or strike them from the header |
| 11 | **No Z2, no hash, no molt.** Every transition is scheduler-automatic. `CredPolicy` weights (80/60/40/20 → 100/70/40/20/10) and the probation ladder are hardcoded constants with no ratification step and no revert. This violates IC-REWARD-01 by construction | read | architecture mismatch | add a `Ratify(hash)` action that gates any weight change; weights become variables with a molt_id |
| 12 | **`Preempt` allows `new_cpu ≤ cpu_limit` but no global CPU bound** despite amendment 5 ("enforces global RAM bound and CPU bound"). `Cores` is the constant that would do it; it's unused (finding 4) | read | claimed, absent | `Sum(alloc_cpu) ≤ Cores × 100` or similar |
| 13 | **Deadlock check.** With `-deadlock` on, TLC reached the invariant violations before any deadlock; deadlock freedom not established | run | unknown | rerun after fixes |

Reproduction: the patched pair `HumanAIOS_Final_v7_1_tlc_patched.{tla,cfg}` runs to the violations above with `java -cp tla2tools.jar tlc2.TLC -workers auto -deadlock <module>`.

## Mapping to our work (what's worth keeping)
| spec concept | our concept | fit |
|---|---|---|
| principal with `cred` | practice / agent with calibration (Brier-derived) | good — cred is the thing LT-1/LT-2 would feed |
| `CredPolicy`: cred → priority → cpu_limit | **REGULATOR**: calibration sets the resource envelope — this is "resource management governed by behavioral calibration" formalized | the best idea in the file; it is LEDGER-ECON's core loop |
| `Preempt` under global RAM bound | envelope + ceiling constants | fits v0.2 resource frame |
| NORMAL → PROBATION → SUSPENDED → QUARANTINE | Tier ladder + "two REVERTs → freeze" (freeze ≈ QUARANTINE terminal) | fits, once finding 7 is fixed |
| P18 "attestation restores eligibility, not trust" | "agreement earns nothing"; only outcomes (AdvanceProbation on positive observations) raise cred | **exactly our value 7**, and the probation ladder is a crude LT curve — keep |
| `hist` append-only | event chain / CHECK valve | fits; needs a bound and a hash |
| `last_obs_signal = floor` | RELIEF valve | fits, but must be atomic (finding 6) |
| `MandatoryEscalate` | halt conditions §F | fits |
| `ForceMandatoryEscalate` | Z2 halt | fits — this is the only Z2-like action, and it is labeled adversarial |
| `Sum`, `Min` | — | fine |
| absent: ratification hash, molt, falsifier, DELUSION-GUARD, record read | — | the whole gate layer is missing |

## What "integration grade" would require (falsifiable list)
1. Parses and runs under TLC in CI (`tla2tools.jar` from github.com is inside our network allowlist — this can be a workflow today).
2. `Inv` holds on the bounded model with P11 restated as an action property and `ApplyPolicy` status-guarded.
3. Real P18 written and checked; `SpecWithLaunder` produces the counterexample it claims.
4. `Ratify(hash)` action gating every weight change; weights as variables.
5. At least the collusion and Sybil adversaries modeled (the two the mesh audit and the market report both flagged as live).
6. Deadlock-free on the bounded model.
7. A `.cfg` that matches the spec's ASSUMEs.
Pin: P(a v7.2 meeting 1–3 and 7 passes TLC within one desktop session) = 0.7. P(4–6) = 0.35 — that is real modeling work.

## Routing
- Lands in `operations/tests/` under quality-assurance's block (it is a gate artifact), LAID.
- IC candidates: IC-TLA-01 (claimed-verified-never-run — IC-031 class); IC-TLA-02 (P11 false: atomic-escalation claim).
- H candidate: H-TLA-01 "cred → envelope regulator (CredPolicy) reproduces the v0.2 resource frame's ordering on the 15-practice pin set." Falsifier: ranking by cred disagrees with ranking by cost-per-kept on > 5 of 15.
- The `CredPolicy` regulator is worth promoting into LEDGER-ECON as the formal statement of the whiteboard sentence. That is the one thing in this file that is ahead of our own docs.
