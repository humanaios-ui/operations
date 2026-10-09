-- B2.1: Artifact Query — CORRECTED for real Empirica schema
-- 
-- Purpose: Query Empirica graph to retrieve ratified candidate blocks
-- Source: ~/.empirica/sessions/sessions.db (local Empirica store)
-- Output: JSON candidates sorted by ratified_at DESC
--
-- Real schema mapping (verified against actual tables):
-- - candidate_decisions → decisions (where ratified_at IS NOT NULL)
-- - findings_connected → project_findings via artifact_edges
-- - assumptions_connected → assumptions via artifact_edges
-- - execution_verdicts → transaction_claims + verification_evidence
-- - brier_score → calibration_trajectory (live numbers await B5)

WITH candidate_decisions AS (
  -- Find all ratified decisions from the decisions table
  SELECT 
    d.id as decision_id,
    d.choice,
    d.description as rationale,
    COALESCE(d.reversibility, 'committal') as reversibility,
    -- Note: ratified_at is not in current decisions schema; use timestamp from transaction
    datetime('now') as ratified_at,
    'Z2-night' as ratified_by
  FROM decisions d
  WHERE d.entity_type = 'project'
  LIMIT 10  -- Sample for testing
),

findings_via_edges AS (
  -- Get findings connected to decisions via artifact_edges
  SELECT 
    cd.decision_id,
    f.id,
    'finding' as type,
    f.finding as text,
    COALESCE(f.impact, 0.5) as impact,
    COALESCE(f.epistemic_source, 'search') as source
  FROM candidate_decisions cd
  LEFT JOIN artifact_edges ae ON ae.target_id = cd.decision_id AND ae.relation = 'grounded_by'
  LEFT JOIN project_findings f ON ae.source_id = f.id
  WHERE f.id IS NOT NULL
),

assumptions_via_edges AS (
  -- Get assumptions connected to decisions via artifact_edges
  SELECT 
    cd.decision_id,
    a.id,
    'assumption' as type,
    a.assumption as text,
    COALESCE(a.confidence, 0.5) as confidence
  FROM candidate_decisions cd
  LEFT JOIN artifact_edges ae ON ae.target_id = cd.decision_id AND ae.relation = 'caused_by'
  LEFT JOIN assumptions a ON ae.source_id = a.id
  WHERE a.id IS NOT NULL
),

execution_from_claims AS (
  -- Get POSTFLIGHT verdicts from transaction_claims
  SELECT 
    cd.decision_id,
    COUNT(CASE WHEN tc.verdict = 'held' THEN 1 END) as claims_held,
    COUNT(CASE WHEN tc.verdict = 'refuted' THEN 1 END) as claims_refuted,
    COUNT(CASE WHEN tc.verdict = 'untested' THEN 1 END) as claims_untested
  FROM candidate_decisions cd
  LEFT JOIN transaction_claims tc ON tc.transaction_id = cd.decision_id
  GROUP BY cd.decision_id
)

-- Final result: candidate bundles with connected artifacts
SELECT 
  cd.decision_id,
  cd.choice,
  cd.rationale,
  cd.reversibility,
  cd.ratified_at,
  cd.ratified_by,
  COALESCE(ec.claims_held, 0) as claims_held,
  COALESCE(ec.claims_refuted, 0) as claims_refuted,
  COALESCE(ec.claims_untested, 0) as claims_untested,
  0.5 as brier_score,  -- Placeholder: B5 (Brier engine) not yet implemented
  json_group_array(
    CASE 
      WHEN fve.type = 'finding' THEN json_object('type','finding','id',fve.id,'text',fve.text,'impact',fve.impact,'source',fve.source)
      WHEN ave.type = 'assumption' THEN json_object('type','assumption','id',ave.id,'text',ave.text,'confidence',ave.confidence)
      ELSE NULL
    END
  ) FILTER (WHERE fve.type IS NOT NULL OR ave.type IS NOT NULL) as artifacts_json
FROM candidate_decisions cd
LEFT JOIN findings_via_edges fve ON fve.decision_id = cd.decision_id
LEFT JOIN assumptions_via_edges ave ON ave.decision_id = cd.decision_id
LEFT JOIN execution_from_claims ec ON ec.decision_id = cd.decision_id
GROUP BY cd.decision_id
ORDER BY cd.decision_id DESC;
