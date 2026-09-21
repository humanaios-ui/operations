# Q-GATE-PATHS-TEST-LOGIC-01 — a gate's logic measures Tier 0 while its wrapper measures Tier 2

**Type:** IC · Tier 2 (proposes editing `GATE_PATHS`) · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Approved for filing by:** Night, 2026-09-21 ("I approve to add to Z2")
**Origin:** the molt-tier over-claim on PR #436.

---

## The finding

`tools/molting_protocol_diff_v1_0.py` lists `.github/workflows/` in `GATE_PATHS`
but not `tests/test_temporal_dissolution_gate.py`.

That test file **is** the temporal-dissolution merge gate. The workflow
`.github/workflows/temporal-dissolution-gate.yml` is a wrapper that sets
`TEMPORAL_SCAN_ENFORCE=1` and runs it. The refusal logic — which surfaces are
scanned, which patterns are prohibited, which paths are exempt — lives entirely in
the test module.

So under the published rule:

| Change | Measured tier |
|---|---|
| Edit the workflow wrapper (env var, trigger, runner) | **2** |
| Edit which merges the gate refuses | **0** |

PR #436 changed what that gate refuses — added `MOLT_STATE.md` to the scanned
surfaces, added two exemptions, extended `RISK_PATTERNS` with the `*_days`
duration forms — and measured Tier 0, "not a molt".

## Precedent

This exact gap has been patched twice before, and the file records why. From its
own `# REPO:` comments:

> the ratification and validation gates live under `.z1-control/` here, not
> `tools/`. The spec's `tools/validate.py` and `tools/ratify.py` do not exist in
> this repository, so without these two entries every change to the Z2 signing
> path would have measured Tier 0.

and

> The rule must be able to see edits to itself.

The same reasoning applies: a gate whose logic lives in `tests/` is invisible to
the classifier, so every change to what it refuses measures as not-a-molt.

## Why Z1 did not simply add the path

Three reasons, and the third is the one that mattered:

1. Editing `tools/molting_protocol_diff_v1_0.py` is itself Tier 2 by that file's
   own rule.
2. It changes tier measurement for every future PR, not just this one.
3. **Adding it inside the PR whose own over-claim it would retroactively vindicate
   is self-serving.** Z1 claimed Tier 2, the classifier measured 0, and the claim
   was wrong because Z1's local verification ran against a stale `main`. Fixing the
   rule so the wrong claim becomes right — in the same diff, unprompted — is not a
   correction, it is laundering. Filed for Z2 instead.

## Proposal

Add to `GATE_PATHS`:

```python
    # Q-GATE-PATHS-TEST-LOGIC-01. The temporal-dissolution gate's refusal logic
    # lives here; .github/workflows/temporal-dissolution-gate.yml only wraps it.
    # Without this entry, changing what the gate refuses measures Tier 0.
    "tests/test_temporal_dissolution_gate.py",
```

Z2 may prefer the broader rule — *any* test module invoked by a workflow as a
merge gate — but that is harder to state mechanically and Z1 does not recommend
guessing at it. A named path matches how the two prior gaps were patched.

## What this does not fix

The molt-tier snapshot for PR #436 is already recorded as `OVER_CLAIM`, gap −2,
`accuracy_impact: LOW`, and should stay that way. The ledger is measuring Z1's
claim accuracy; retroactively re-measuring a closed row against a changed rule
would destroy exactly the signal it exists to collect. The rule change applies
forward.

## Falsifier

FALSE if `tests/test_temporal_dissolution_gate.py` is not the enforcement logic of
a merge gate — i.e. if `.github/workflows/temporal-dissolution-gate.yml` does not
invoke it, or invokes it non-blockingly. Checkable by reading the workflow.

Also FALSE if adding the path causes a PR that touches only that file's
*self-tests* (not its rules) to measure Tier 2 and thereby demand a registry entry
and ADV run for a no-op change. Z1 judges this acceptable — over-claiming costs
caution, under-claiming is how a gate change merges labelled "not a molt" — but it
is a real cost and Z2 should price it.

## Evidence

- `tools/molting_protocol_diff_v1_0.py` — `GATE_PATHS`, and the two `# REPO:` notes
- `.github/workflows/temporal-dissolution-gate.yml` — the wrapper
- `tests/test_temporal_dissolution_gate.py` — `CONTROL_EXACT`, `EXEMPT_PATHS`, `RISK_PATTERNS`
- PR #436 molt-tier snapshot: `{"molt_tier_claimed": 2, "molt_tier_measured": 0, "gap": -2, "verdict": "OVER_CLAIM"}`

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```

---

## Z2 Ruling

**Decision:** ACCEPT — stated by Night (Z2/Admiral) in session, 2026-09-21.
**Recorded by:** Claude (Z1), as transcription. Z1 did not make this call.
**Signature:** none on this file. Per `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`,
the hash echo is retired and **the merge of this candidate's pull request is the
act of ratification** — the merger and the merge date are the signature's `by`
and `at`, recomputable by `.z1-control/ratify.py --verify` over the bytes as
merged. The index entry stays `awaiting_z2` until that merge, because Z1
recording a terminal status would be the self-grant `.z1-control/validate.py`
rule 6 refuses.

Single-member override applies: with one board member, Night reviews, approves
and merges her own ruling PR, recorded as an override per that ruling's `review`
row.
