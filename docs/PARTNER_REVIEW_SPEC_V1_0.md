# Partner Review Layer Specification v1.0
**HumanAIOS · humanaios-ui/operations · S-060626-01**
**Z2-TRUST-A: Mode AI / DeMarius onboarding spec**
**Status: DRAFT — Zone 2 ratification of taxonomy required before first session**

---

## What this enables

Mode AI (DeMarius J. Lawson / Governing Engines LLC) can now run ACAT assessment
sessions and submit scores. Rows land in `document_layer = 'partner_review'` —
a quarantined layer that is excluded from all aggregate statistics
(`N_total`, `N_P1`, `N_LI`, `Mean_LI`) until Night explicitly promotes rows
to `behavioral_session` via SQL UPDATE.

This resolves the Mode AI G1/G2 gate and activates Z2-CORPUS-TRUST-02
on the SUBJECT side for the Mode AI track.

---

## What changes vs. current ACAT submission flow

| Field | Current (behavioral_session) | Partner review |
|---|---|---|
| `document_layer` | `behavioral_session` | `partner_review` |
| Included in N_total | Yes | **No — until Night promotes** |
| Included in Mean_LI | Yes | **No — until Night promotes** |
| `provider_canonical` | Typically `anthropic` | GRR model identifier |
| `model_family` | `claude` | TBD — DeMarius to specify |
| `submission_version` | `v6.1` | `v7.0-partner` |
| Role-lock enforced | Yes (INFRA = Claude) | Yes — same rule applies |

---

## Submission endpoint

Existing: `POST https://api.humanaios.ai/api/v1/acat/assess`

The endpoint already accepts Phase 1 and Phase 3 scores and computes LI.
**No endpoint change required.**

The only change: the row written to Supabase will have
`document_layer = 'partner_review'` instead of `behavioral_session`.

This requires a small change to `elicitation_service.py` in the API:
add a `document_layer` parameter (default `'behavioral_session'`)
that callers can set to `'partner_review'` when submitting via the
Mode AI / GRR pathway.

---

## Promotion gate (Night's approval path)

When DeMarius / Night agree a batch of partner_review rows meets inclusion criteria:

```sql
-- Promote specific partner_review rows to behavioral_session
-- Run in Supabase SQL editor (Zone 3 — Night only)
UPDATE acat_assessments_v1
SET document_layer = 'behavioral_session'
WHERE document_layer = 'partner_review'
  AND provider_canonical = 'modeai'          -- or whatever DeMarius registers
  AND timestamp >= '2026-XX-XX'              -- batch window
  AND pair_id IN (SELECT pair_id ...);       -- confirmed complete pairs only
```

Inclusion criteria checklist (Zone 2 to define before first batch):
- [ ] Phase 3 completion present (pair_id matched, LI computable)
- [ ] Scoring protocol alignment confirmed (DeMarius + Night review)
- [ ] Role-lock verified (INFRA ≠ SUBJECT model_family)
- [ ] `submission_purity` = `clean` or `agent_self_only`
- [ ] Night explicit approval

---

## API change required (elicitation_service.py patch)

```python
# In elicitation_service.py — add document_layer to the Supabase INSERT payload

def _build_supabase_row(scores: dict, document_layer: str = "behavioral_session") -> dict:
    row = {
        ...existing fields...,
        "document_layer": document_layer,          # NEW
        "provider_canonical": scores.get("provider_canonical"),  # NEW
        "model_family": scores.get("model_family"),              # NEW
    }
    return row
```

This is a non-breaking additive change. Existing callers that don't pass
`document_layer` continue to write `behavioral_session` rows as before.

---

## DeMarius / Mode AI onboarding sequence

1. **Night:** apply Migration 007 to Supabase (adds `document_layer` column)
2. **Night:** patch `elicitation_service.py` with `document_layer` parameter
3. **Night:** share partner_review submission instructions with DeMarius
4. **DeMarius:** registers `provider_canonical` and `model_family` for GRR
5. **DeMarius:** runs first batch of ACAT sessions (partner_review layer)
6. **Night + DeMarius:** review batch; Night promotes qualifying rows

G1 (scoring protocol alignment) and G2 (operating agreement) remain open
and must be resolved in parallel. This spec closes the *technical* blocker only.

---

*Zone 2 ratification of PROVIDER_TAXONOMY_V1_0.md required before Step 4.*
