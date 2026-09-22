# Practice: `grok-crossref`

**Record:** [`practice.yaml`](./practice.yaml) · **Status:** Z1 CANDIDATE, no Z2 hash
**Aliases:** "grock-cross-ref", "grok cross-ref" — operator prose only; the canonical token in
`ledgers/NF_LEDGER.jsonl` is `grok-crossref` and is used in every machine-readable field.
**Zone:** none — no row in `ZONE_REGISTRY.md`, no entry in `PLANNED_REPOS.md`
**Resolution class:** **UNAMBIGUOUS** — the one practice in this drop that is not blocked

## What it owns

Cross-reference runs that bind a claim to the artifacts carrying it, adversarial
cross-examination of Z1 proposals authored by a different substrate, and the register at
[`../../CROSS_REFERENCE_REGISTER.md`](../../CROSS_REFERENCE_REGISTER.md).

## What it may not do

- Ratify what it cross-examines, or approve any pull request it reviews.
- Treat substrate diversity as independence. PR #452 Pass A records that demonstrably blind
  observations remain unproven in the frozen fixture. Four distinct substrates converging is
  convergence, not blindness.

## Token state

| token | title | state |
|:--|:--|:--|
| `T-grok-crossref-01` | Recovery restart | resolved |
| `T-grok-crossref-02` | Validation run | resolved |
| `T-grok-crossref-03` | Sign-off = validated crossref run with hash | resolved |
| `T-grok-crossref-04` | KG optimization | `PENDING_Z2_DATE` |
| `T-grok-crossref-05` | Accuracy benchmark | `PENDING_Z2_DATE` |
| `T-grok-crossref-06` | Theme detection | `PENDING_Z2_DATE` |

The three pending tokens carry `date_source: Z1_PROPOSED`. Z2 has not dated them. Whether they
receive dates or lapse is not a Z1 decision.

## What this drop is not

`T-grok-crossref-03` defines sign-off as a validated crossref run **with a hash**. The register
produced here carries no run hash and does not satisfy that token. No ledger row is written.
