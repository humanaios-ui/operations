# B2.1: Artifact Query Design — Candidate Bundle Fetcher

**Purpose:** Query the Empirica graph to retrieve ratified candidate blocks for REGISTERED.md projection.

**Source:** Local Empirica store (`~/.empirica/sessions/sessions.db`) + remote Cortex (Qdrant)

## Schema Mapping

### Core Artifact Tables
- `project_findings` — observations grounded by findings-log
- `project_unknowns` — resolvable gaps logged by unknown-log
- `assumptions` — unverified beliefs (assumption-log)
- `decisions` — Z1 choices (decision-log)
- `artifact_edges` — relational graph (type, source_id, target_id, relation)
- `calibration_trajectory` — per-transaction vectors + Brier scores
- `transaction_claims` — claims made in PREFLIGHT + their verdicts (held/refuted/untested)

### Key Relations (artifact_edges.relation)
- `grounded_by` — finding grounded by external source
- `caused_by` — assumption that led to decision
- `falsifies` — assumption that would disprove hypothesis
- `resolves` — finding that closed an unknown
- `invalidates` — new evidence that contradicts prior claim
- `sourced_from` — cited reference

## Candidate Bundle Query

### Definition
A candidate bundle is a connected sub-graph containing:
1. **One decision** (Z1 choice) — the anchor
2. **One or more findings** (F) — evidence supporting it
3. **Zero or more assumptions** (H) — unverified beliefs the decision rests on
4. **One falsifier** (low-confidence assumption) — what would prove it wrong
5. **Connected edges** — grounded_by, caused_by, sources_from relations
6. **Verdict** — execution outcome (held/refuted/untested) + Brier score

### SQL Query Template (Option A: Flat Graph)

```sql
WITH candidate_decisions AS (
  -- Find all decisions marked as RATIFY-ready (ratified_at IS NOT NULL)
  SELECT 
    d.id,
    d.choice,
    d.rationale,
    d.reversibility,
    d.ratified_at,
    d.ratified_by,
    d.created_at
  FROM decisions d
  WHERE d.ratified_at IS NOT NULL
    AND d.visibility IN ('shared', 'public')
  ORDER BY d.ratified_at DESC
),

candidate_members AS (
  -- Fetch all artifacts connected to each decision
  SELECT 
    cd.id as candidate_id,
    cd.ratified_at,
    ae.source_id,
    ae.source_type,
    ae.relation,
    f.id as finding_id,
    f.finding as finding_text,
    f.impact,
    f.epistemic_source,
    a.id as assumption_id,
    a.assumption as assumption_text,
    a.confidence,
    u.id as unknown_id,
    u.unknown as unknown_text
  FROM candidate_decisions cd
  LEFT JOIN artifact_edges ae ON (
    ae.target_id = cd.id 
    OR (ae.source_id = cd.id AND ae.relation IN ('caused_by', 'grounded_by'))
  )
  LEFT JOIN project_findings f ON ae.source_id = f.id AND ae.source_type = 'finding'
  LEFT JOIN assumptions a ON ae.source_id = a.id AND ae.source_type = 'assumption'
  LEFT JOIN project_unknowns u ON ae.target_id = u.id AND ae.source_type = 'unknown'
),

execution_verdicts AS (
  -- Lookup POSTFLIGHT verdicts for each candidate's claims
  SELECT 
    d.id,
    COUNT(CASE WHEN tc.verdict = 'held' THEN 1 END) as held_count,
    COUNT(CASE WHEN tc.verdict = 'refuted' THEN 1 END) as refuted_count,
    COUNT(CASE WHEN tc.verdict = 'untested' THEN 1 END) as untested_count,
    MAX(ct.brier_score) as brier_score
  FROM candidate_decisions d
  LEFT JOIN transaction_claims tc ON tc.decision_id = d.id
  LEFT JOIN calibration_trajectory ct ON ct.transaction_id = tc.transaction_id
  GROUP BY d.id
)

SELECT 
  cd.id,
  cd.choice,
  cd.rationale,
  cd.reversibility,
  cd.ratified_at,
  cd.ratified_by,
  COALESCE(ev.held_count, 0) as claims_held,
  COALESCE(ev.refuted_count, 0) as claims_refuted,
  COALESCE(ev.untested_count, 0) as claims_untested,
  ROUND(COALESCE(ev.brier_score, 0), 2) as brier_score,
  GROUP_CONCAT(
    CASE 
      WHEN cm.finding_id IS NOT NULL THEN json_object('type','finding','id',cm.finding_id,'text',cm.finding_text,'impact',cm.impact)
      WHEN cm.assumption_id IS NOT NULL THEN json_object('type','assumption','id',cm.assumption_id,'text',cm.assumption_text,'confidence',cm.confidence)
      WHEN cm.unknown_id IS NOT NULL THEN json_object('type','unknown','id',cm.unknown_id,'text',cm.unknown_text)
    END
  ) as artifacts_json
FROM candidate_decisions cd
LEFT JOIN candidate_members cm ON cm.candidate_id = cd.id
LEFT JOIN execution_verdicts ev ON ev.id = cd.id
GROUP BY cd.id
ORDER BY cd.ratified_at DESC;
```

### Output Structure (JSON)

```json
{
  "candidates": [
    {
      "z_id": "Z1-47",
      "decision_id": "dec_abc123",
      "ratified_at": "2026-10-09T14:32:00Z",
      "ratified_by": "Z2-night",
      "choice": "Adopt empirica-only governance",
      "rationale": "Single source of truth reduces calibration drift",
      "reversibility": "committal",
      "artifacts": {
        "findings": [
          {
            "id": "find_xyz789",
            "text": "REGISTERED.md has 5,141 hand-maintained lines",
            "impact": 0.95,
            "source": "search"
          }
        ],
        "assumptions": [
          {
            "id": "ass_def456",
            "text": "Cortex Qdrant can be authoritative store",
            "confidence": 0.72
          }
        ],
        "falsifier": {
          "id": "ass_ghi789",
          "text": "If Qdrant shards are lost, single source fails",
          "confidence": 0.15
        }
      },
      "execution": {
        "claims": {"held": 3, "refuted": 0, "untested": 1},
        "brier_score": 0.78,
        "status": "active"
      }
    }
  ]
}
```

## Implementation Notes

### Option A (Chosen): Flat Graph
- Pros: Qdrant-friendly, easier to query by relation type, fits constitution §III-b
- Cons: More complex joins (need strong LEFT JOIN discipline)
- Schema: `artifact_edges(source_id, source_type, target_id, relation, ...)`

### Fetch Logic
1. **Start from decisions** (Z1 anchors) where `ratified_at IS NOT NULL`
2. **Walk edges** using `artifact_edges` to find all connected artifacts
3. **Group by decision** to form bundles
4. **Enrich with verdicts** from `transaction_claims` + `calibration_trajectory`
5. **Sort by `ratified_at` DESC** (newest ratifications first)

### Stale/Untested Detection
- **Untested:** `untested_count > 0` and execution window closed (14+ days)
- **Stale:** Last execution >14 days ago, no new claims
- **Disputed:** Any `verdict = refuted` in the bundle

### Live Signals
- **Brier score:** Max from `calibration_trajectory.brier_score` for the transaction
- **Confidence:** From `assumptions.confidence` for each assumption
- **Execution status:** Derived from verdict counts (held/refuted/untested)

---

## Next Step: B2.2

Once this query runs and returns candidate bundles, B2.2 renders them into markdown sections (the REGISTERED.md projection).

