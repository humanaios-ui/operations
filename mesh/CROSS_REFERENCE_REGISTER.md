# Cross-Reference Register v0.1

**Status:** Z1 candidate — not ratified. No Z2 hash.
**Owning practice:** `grok-crossref`
**Pin (HISTORICAL_RECORD):** first read at `operations` @ `44347b79b1d6351bd10bbb5fb6c45b9ead6bd42e`;
artifact states refreshed at `22a06f35fd10333eb85db7d69c057f5ec2a2ecdb`
**Read at:** 2026-09-22 (OBSERVATIONAL — carries no scheduling authority)

This register binds the artifacts named in the coordination request to the three practices in
this drop. It is a **cross-reference**, not a review: it records what each artifact claims, what
it explicitly disclaims, and which practice the claim lands on.

`T-grok-crossref-03` defines sign-off as "validated crossref run with hash." **This register is
not that.** It is a specified artifact with no run hash, and it does not satisfy that token.

---

## Artifacts read

| # | artifact | state at read | type |
|:--|:--|:--|:--|
| [#454](https://github.com/humanaios-ui/operations/pull/454) | Z1 preregistration: independent OSF OAuth adversarial audit | OPEN, mergeable clean | preregistration |
| [#452](https://github.com/humanaios-ui/operations/pull/452) | Z1 experiment: CT-001 constitutional tuning reconstruction | **MERGED** at `22a06f3` | experiment |
| [#451](https://github.com/humanaios-ui/operations/pull/451) | Z1 proposal: Witness Arena v0.1.1 — adversarial hardening | OPEN, mergeable clean | design proposal |
| [#389](https://github.com/humanaios-ui/operations/issues/389) | Add blind independent AI reviewer to pull-request governance | OPEN; PR [#390](https://github.com/humanaios-ui/operations/pull/390) open against it | governance task |
| [#429](https://github.com/humanaios-ui/operations/issues/429) | Q-WITNESS-COMMONS-ASSURANCE-01 readiness audit | CLOSED (completed) via merged PR [#431](https://github.com/humanaios-ui/operations/pull/431) | architecture RFC |

The coordination request listed #451 twice. It is registered once.

**#452 merged while this register was in review.** Its body states "Do not merge or treat this
experiment as constitutional ratification." Merging does not retire that disclaimer: the
artifact is now on `main`, and its Pass A results are on the record, but H-CT-001 remains
UNRESOLVED pending Pass B and the Seed Constitution remains a provisional calibration reference.
The claim/disclaimer pairs below are unchanged by the merge.

This row was corrected on a refresh, which is the maintenance rule in
`MESH_LOCAL_CHARTER_V0_1.md` §7 applied to this register: a derived record that reads as current
while its subject has moved is the failure mode, not the correction.

---

## Practice binding

| artifact | `humanaios` | `website` | `grok-crossref` |
|:--|:--:|:--:|:--:|
| #454 OSF OAuth audit | — | — | ✅ preregistered adversarial protocol |
| #452 CT-001 | ✅ instrument under reconstruction | — | ✅ cross-substrate convergence |
| #451 Witness Arena | — | — | ✅ Grok-authored v0.1.1 revision |
| #389 blind reviewer | — | — | ✅ the mechanism this practice feeds |
| #429 Witness/Commons | ✅ ACAT mapping (§11) | ✅ service contract (§2–3) | ✅ observability horizon (§16) |

---

## Claim / disclaimer pairs

Each row records what the artifact asserts and the boundary it draws around that assertion. The
disclaimer column is the part a coordination layer most easily loses.

### #454 — OSF OAuth independent audit

| claims | disclaims |
|:--|:--|
| Audit protocol, 18 test vectors, and a live baseline are frozen ahead of review | Does not implement the bridge; does not authorize deployment |
| Independence at freeze time: `osf-oauth-start` and `osf-oauth-callback` were not present in the connected Supabase project and no matching implementation PR was visible | Independence is asserted **as of freeze**, not proven for the execution that follows |

Invariants carried: `OAUTH_PERMISSION_IS_NOT_GOVERNANCE_AUTHORITY`,
`OSF_CONNECTION_IS_NOT_RESEARCH_RATIFICATION`,
`OAUTH_CONTEXT_CANNOT_BE_REBOUND_AFTER_AUTHORIZATION_START`, `SECRET_MATERIAL_IS_NOT_EVIDENCE`,
`REGISTRATION_SUBMISSION_REQUIRES_HUMAN_CONFIRMATION`.

**Binding to this layer:** the first invariant is the same shape as
`PARTICIPATION_IN_THE_LOCAL_MESH_IS_NOT_AUTHORITY`. A permission event and a membership record
both fail to produce governance standing.

### #452 — CT-001 constitutional tuning reconstruction

| claims | disclaims |
|:--|:--|
| 4 substrate-distinct reviewer outputs materially converge on the structural-independence gap | Demonstrably blind observations remain **unproven** in the frozen fixture |
| 11/11 observed PR workflow runs succeeded | Tool health is kept separate from constitutional/design assurance |
| Preregistered before result encoding at `d17b75d6b0f30e0d96607713ffeeddcb76eecda6` | H-CT-001 remains UNRESOLVED pending Pass B — the merge does not resolve it |
| — | Issue #429 authority is **not** transferred to PR #451 |
| — | Seed Constitution v0.1 is a provisional calibration reference, **not binding authority** |
| — | External regulatory/standards support is not asserted for this internal specimen |

**Binding to this layer:** the last disclaimer governs how `seeds/seed-constitution-v0.1.md` is
cited in `MESH_LOCAL_CHARTER_V0_1.md` §0 — as a calibration reference only. The
convergence-is-not-blindness distinction is recorded as an open unknown in the `grok-crossref`
record rather than resolved in this layer's favour.

### #451 — Witness Arena v0.1.1

Seven adversarial findings and their resolutions, per the PR body:

| finding | resolution |
|:--|:--|
| Membrane "structural" independence overclaimed | Standing narrowed to policy + receipts + integrity; structural isolation out of scope until sealed contexts exist |
| Authority boundary unbound | MANIFEST `authority_pinned_at` path+commit; membrane decisions are observation records, not a new tier |
| Harmonic valence bias | Default valence-neutral mapping; legacy table illustrative only, with disclosure |
| Epoch can override Z2? | **No** — findings advisory; may file F/IC only |
| Schema soft smuggling | `additionalProperties: false` on core objects; `extensions` namespace ignored by escalation logic |
| Cross-domain divergence stall | Escalate to HUMAN_AUTHORITY_AGENDA; no pooled voting; minority evidence not suppressed |
| Public PR contamination | Recorded in MANIFEST contamination_controls |

The PR also records `smag_p: 0.80`, `molt_tier_claimed: 0`, and that contamination *detection*
remains TBD before any operational claim.

**Binding to this layer — carried, not cited:**
- *Schema soft smuggling* → `mesh/practice_local.schema.json` sets `additionalProperties: false`
  on the record and on every nested object, and
  `mesh/conformance/validate_mesh.py` demonstrates the refusal rather than asserting it.
- *Authority boundary unbound* → every record carries `provenance.pinned_sha`, and
  `authority.grants_authority` is a schema `const: false`.
- *Observation records, not a new tier* → the charter's authority boundary uses the same words.

### #389 — blind independent AI reviewer

| claims | disclaims |
|:--|:--|
| A second AI reviewer reviews the diff without seeing Copilot's conclusions first | Neither Copilot nor the second model receives merge authority |
| `AGENTS.md` is the shared governance source; Copilot guidance references rather than duplicates it | Human merge authority remains non-negotiable |
| Secrets live in GitHub Secrets | The second reviewer is a counterpoint, not a replacement decision-maker |

**Binding to this layer:** this is the governance mechanism the `grok-crossref` practice feeds.
Its "counterpoint, not decision-maker" framing is the same boundary the practice record draws in
`out_of_scope`.

### #429 — Q-WITNESS-COMMONS-ASSURANCE-01

Closed as completed via merged PR #431. Two hypotheses from it are registered in `REGISTERED.md`
(`H-WITNESS-OBSERVABLE-01`, `H-WITNESS-PHASE-1-SCOPE-01`), both ratified by Z2 on 2026-09-21.

| section | binds to | carried here as |
|:--|:--|:--|
| §2–3 Witness service contract; `ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE` | `website` | `out_of_scope`: rendering must keep canonical source, derived rendering, and generated explanation distinguishable |
| §7 `OMISSION_IS_EVIDENCE_METADATA` | all three | charter §0 records the unreadable plugin text as an omission rather than substituting for it; every record carries an `unknowns` list |
| §11 event → assessment path | `humanaios` | `constrained_by` edge: an event is not an ACAT score |
| §16 `AUTHORITY_CANNOT_OUTRUN_OBSERVABILITY` | `grok-crossref` | the standing reason this layer stays an observation record |
| §19 implementation-state vocabulary | all three | `trl_framing.implementation_state`, closed to SPECIFIED/CODED/TESTED/OPERATED/VERIFIED |
| §3 `PARTICIPATION_IS_NOT_AUTHORITY` | all three | `authority.grants_authority` is `const: false` |

---

## What this register does not do

- It does not review the correctness of any linked artifact.
- It does not resolve any NF ledger token, including the three `grok-crossref` tokens in
  `PENDING_Z2_DATE`.
- It does not transfer authority between any two artifacts. #452 states explicitly that #429
  authority is not transferred to #451; this register does not create that transfer by placing
  them in one table.
- It is not a blind review. It was assembled by a single reader with all five artifacts visible,
  which is the condition #452 Pass B is specified to avoid.
