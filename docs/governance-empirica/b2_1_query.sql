-- B2.1: Artifact Query — Fetch Candidate Bundles for REGISTERED.md
-- 
-- Purpose: Query Empirica graph to retrieve ratified candidate blocks
-- Source: ~/.empirica/sessions/sessions.db (local Empirica store)
-- Output: JSON candidates sorted by ratified_at DESC

WITH candidate_decisions AS (
  -- Find all decisions marked as RATIFY-ready
  SELECT 
    d.id,
    d.choice,
    d.rationale,
    d.reversibility,
    d.entity_id as decision_id
  FROM decisions d
  WHERE d.entity_type = 'project'
    AND (d.id LIKE '%ratif%' OR d.choice LIKE '%ratif%' OR 1=1)  -- All decisions (no ratified_at field yet)
  ORDER BY d.id DESC
  LIMIT 10  -- Sample: fetch latest 10 for testing
),

findings_connected AS (
  -- Get findings connected to decisions
  SELECT 
    cd.decision_id,
    'finding' as type,
    pf.id,
    pf.finding as text,
    COALESCE(pf.impact, 0.5) as impact,
    COALESCE(pf.epistemic_source, 'search') as source
  FROM candidate_decisions cd
  LEFT JOIN project_findings pf ON pf.id LIKE '%' || cd.id || '%' OR 1=0
  WHERE pf.id IS NOT NULL
),

assumptions_connected AS (
  -- Get assumptions (including falsifiers: low confidence)
  SELECT 
    cd.decision_id,
    'assumption' as type,
    a.id,
    a.assumption as text,
    COALESCE(a.confidence, 0.5) as confidence
  FROM candidate_decisions cd
  LEFT JOIN assumptions a ON a.id LIKE '%' || cd.id || '%' OR 1=0
  WHERE a.id IS NOT NULL
),

execution_verdicts AS (
  -- Lookup POSTFLIGHT verdicts for each candidate's claims
  SELECT 
    cd.decision_id,
    COUNT(CASE WHEN tc.verdict = 'held' THEN 1 END) as claims_held,
    COUNT(CASE WHEN tc.verdict = 'refuted' THEN 1 END) as claims_refuted,
    COUNT(CASE WHEN tc.verdict = 'untested' THEN 1 END) as claims_untested,
    ROUND(MAX(ct.brier_score), 2) as brier_score
  FROM candidate_decisions cd
  LEFT JOIN transaction_claims tc ON tc.decision_id = cd.id
  LEFT JOIN calibration_trajectory ct ON ct.transaction_id = tc.transaction_id
  GROUP BY cd.decision_id
)

-- Final result: candidate bundles with connected artifacts
SELECT 
  cd.decision_id,
  cd.choice,
  cd.rationale,
  cd.reversibility,
  DATETIME('now') as ratified_at,
  'Z2' as ratified_by,
  COALESCE(ev.claims_held, 0) as claims_held,
  COALESCE(ev.claims_refuted, 0) as claims_refuted,
  COALESCE(ev.claims_untested, 0) as claims_untested,
  COALESCE(ev.brier_score, 0.5) as brier_score,
  json_group_array(
    CASE 
      WHEN fc.type = 'finding' THEN json_object('type','finding','id',fc.id,'text',fc.text,'impact',fc.impact,'source',fc.source)
      WHEN ac.type = 'assumption' THEN json_object('type','assumption','id',ac.id,'text',ac.text,'confidence',ac.confidence)
      ELSE NULL
    END
  ) FILTER (WHERE fc.type IS NOT NULL OR ac.type IS NOT NULL) as artifacts_json
FROM candidate_decisions cd
LEFT JOIN findings_connected fc ON fc.decision_id = cd.decision_id
LEFT JOIN assumptions_connected ac ON ac.decision_id = cd.decision_id
LEFT JOIN execution_verdicts ev ON ev.decision_id = cd.decision_id
GROUP BY cd.decision_id
ORDER BY cd.id DESC;
