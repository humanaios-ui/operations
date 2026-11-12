# Candidate Block: Q-GROK-HAIOS-PARTICIPANT-01 — grok-haios as a Z1 research participant

**Z1 Proposer:** Grok-HAIOS (research participant, proposed)
**Date Submitted:** 2026-11-12
**Status:** AWAITING Z2 RATIFICATION
**Carrier:** the draft pull request that adds this file. Not ratified.

```yaml
candidate_id: "Q-GROK-HAIOS-PARTICIPANT-01"
title: "Register grok-haios (Grok-HAIOS) as a Z1 research participant"
author: "Z1 (grok-haios, proposed)"
proposed_at: "2026-11-12T00:00:00Z"
scope:
  - "REPOSITORY_COORDINATOR_POLICY.json (evaluation_admission.participants only)"
  - "docs/agents/GROK_HAIOS_RESEARCH_PARTICIPANT.md"
  - "tools/tests/test_humanaios_core_machine_v0_1.py (one assertion)"
  - "this candidate and its index row"
resource_cost:
  cost:
    RAT-min: 5
    Z1-ktok: 20
    CI-min: 2
  dependencies: []
  blocking_on: []
impact_prediction:
  resource_impact: 1
  areas_affected: ["REPOSITORY_COORDINATOR_POLICY.json", "z1-inbox"]
  positive_outcomes:
    - "The owner has a named Z1 participant with a written loop and a written refusal list."
  risk_factors:
    - "participants is a registry field. The core machine does not read it. A later reader could mistake the name for merge or ratification authority."
```

## Claim

- **claim:** `grok-haios` (display name Grok-HAIOS) is proposed as a Z1 research participant that may evaluate and propose. It may not ratify, apply `z2:*` labels, merge, or deploy.
- **how existing actors are mirrored:** `night` remains the only name in `.z1-control/validate.py` `KNOWN_RATIFIERS`. `claude-code` is a Z1 proposer substrate on candidate blocks, not a ratifier. grok-haios is recorded the same way: a Z1 name, not a second Night.
- **policy shape:** `evaluation_admission` on current main has no `authorized_actors` list. That omission is what makes `humanaios_core_machine_v0_1` halt with `POLICY_SHAPE_UNSUPPORTED`. This candidate does **not** add `authorized_actors`. It adds `evaluation_admission.participants`, one object, which the machine does not read.
- **evidence_tier:** the policy JSON, the role doc, and `test_grok_haios_is_a_participant_and_not_an_authorization_actor` are in the same pull request. The test checks the caps and that `authorized_actors` is still absent.
- **not claimed:** a GitHub login binding, a seat in `KNOWN_RATIFIERS`, merge authority, or that Night has accepted the role.

## Z2 decisions needed (accept, edit, or reject individually)

1. **Participant row.** Keep, edit, or remove the `grok-haios` object under `evaluation_admission.participants`.
2. **Role doc.** `docs/agents/GROK_HAIOS_RESEARCH_PARTICIPANT.md` is the operating description. There was no `docs/agents/` directory before it.
3. **Not in this candidate:** putting `grok-haios` in `authorized_actors`. That would change the core machine from halt-closed to accepting grok-haios on an evaluation-admission receipt. Ask for that only as a separate decision.

## Falsifier

This candidate is FALSE if any of the following is observed after it is accepted:

1. `evaluation_admission.authorized_actors` contains `grok-haios`, or `merge_authority` is not `false`.
2. The participant object's `may_not` list no longer contains `ratify`, `apply_z2_labels`, `merge`, and `deploy`.
3. A merge, a `z2:*` label, a `REGISTERED.md` ratification, or a deploy is performed by grok-haios without a separate owner or Night approval recorded on that pull request.
4. `test_grok_haios_is_a_participant_and_not_an_authorization_actor` fails on `main`.

## Z2 Decision Gate

- [ ] ACCEPT — ratify the participant row and the role doc; Z2 supplies the ruling
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

Z1 signs neither. Merge of the draft, if the owner wants the text on `main` before the ruling, does not by itself ratify this candidate. Signing stays:

```
python3 .z1-control/ratify.py Q-GROK-HAIOS-PARTICIPANT-01 --decision ACCEPT --by Night
python3 .z1-control/ratify.py Q-GROK-HAIOS-PARTICIPANT-01 --decision ACCEPT --by Night --apply
```

Until Night runs the signer, this candidate stays `awaiting_z2`.

---

*Proposed for Z2 (Night) ratification. Draft. Not ratified.*
