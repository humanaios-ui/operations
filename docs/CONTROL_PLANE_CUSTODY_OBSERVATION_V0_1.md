# Control-Plane Observation and Custody — v0.1

Issue: #620  
Standing: Z1 observation instrument  
Authority effect: **NONE**

## Question

For a control-plane event:

> What changed, who or what executed it, who or what decided it, who held the evidence, what boundary applied, and did custody remain separated?

This instrument does **not** determine whether the action was authorized.

## Invariants

```
OBSERVATION != AUTHORITY
PROVENANCE != AUTHORITY
CUSTODY != AUTHORITY
BOUNDARY_ENFORCEMENT != AUTHORITY
```

## Custody

The v0.1 classifier tracks three roles:

- **execution custody** — principal/mechanism that performed the state mutation;
- **decision custody** — principal/policy that selected or triggered the action;
- **information custody** — principal(s) holding the evidence used to observe/reconstruct it.

Derived state:

- `COLLAPSED` — execution and decision are the same known principal;
- `MIXED` — another known role overlap exists;
- `SEPARATED` — execution, decision, and information roles are known and disjoint;
- `UNKNOWN` — evidence is insufficient.

This is a mechanical classification, not a normative verdict.

## Authority evidence

Receipts record `VERIFIED | CLAIMED | NONE | UNKNOWN` independently of custody.

A custody state cannot promote authority evidence. An event with `SEPARATED` custody and `authority_evidence.state=NONE` remains authority-neutral.

## Boundary

`MECHANICAL | PROCEDURAL | ABSENT | UNKNOWN`.

A mechanical boundary proves that a mechanism enforced something. It does not prove that the policy was normatively correct or human-authorized.

## Actor identity

The instrument keeps these separate:

```
carrier_account
actor_origin.origin_class
actor_origin.agent
authority_evidence
```

A shared GitHub account is not treated as a human identity receipt.

## CPC-001

The first replay specimen is PR #593 and covers:

- protected-branch refusal;
- two-parent restack;
- ACAT v2 pin;
- Tool Manifest failure;
- principle-compliance failure;
- corrective head;
- unchanged prediction re-pin (#619).

The specimen is intentionally replayable. The classifier reads it and writes a derived view elsewhere; it does not mutate the source.

## CLI

```bash
python3 tools/control_plane_custody_observer_v0_1.py \
  --input experiments/control-plane-custody/CPC-001/pr-593-observations.json
```

For a file output:

```bash
python3 tools/control_plane_custody_observer_v0_1.py \
  --input experiments/control-plane-custody/CPC-001/pr-593-observations.json \
  --output /tmp/cpc-001-receipts.json
```
