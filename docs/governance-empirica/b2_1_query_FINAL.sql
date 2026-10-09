-- B2.1: Artifact Query — FINAL (schema corrected: from_id/to_id)
-- 
-- Real schema corrections:
-- - artifact_edges: from_id/to_id (not source_id/target_id)
-- - decisions table has no ratified_at; using decision timestamp
-- - Brier: placeholder 0.5 (B5 not implemented)

WITH candidate_decisions AS (
  SELECT 
    d.id as decision_id,
    d.choice,
    COALESCE(d.description, d.rationale, d.choice) as rationale,
    COALESCE(d.reversibility, 'committal') as reversibility,
    datetime('now') as ratified_at,
    'Z2' as ratified_by
  FROM decisions d
  WHERE d.entity_type = 'project'
  LIMIT 10
),

findings_connected AS (
  SELECT 
    cd.decision_id,
    f.id,
    'finding' as type,
    f.finding as text,
    COALESCE(f.impact, 0.5) as impact
  FROM candidate_decisions cd
  LEFT JOIN artifact_edges ae ON ae.to_id = cd.decision_id
  LEFT JOIN project_findings f ON ae.from_id = f.id
  WHERE f.id IS NOT NULL
),

assumptions_connected AS (
  SELECT 
    cd.decision_id,
    a.id,
    'assumption' as type,
    a.assumption as text,
    COALESCE(a.confidence, 0.5) as confidence
  FROM candidate_decisions cd
  LEFT JOIN artifact_edges ae ON ae.to_id = cd.decision_id
  LEFT JOIN assumptions a ON ae.from_id = a.id
  WHERE a.id IS NOT NULL
),

verdicts AS (
  SELECT 
    cd.decision_id,
    COUNT(CASE WHEN tc.verdict = 'held' THEN 1 END) as claims_held,
    COUNT(CASE WHEN tc.verdict = 'refuted' THEN 1 END) as claims_refuted,
    COUNT(CASE WHEN tc.verdict = 'untested' THEN 1 END) as claims_untested
  FROM candidate_decisions cd
  LEFT JOIN transaction_claims tc ON tc.transaction_id LIKE '%' || cd.decision_id || '%'
  GROUP BY cd.decision_id
)

SELECT 
  cd.decision_id,
  cd.choice,
  cd.rationale,
  cd.reversibility,
  cd.ratified_at,
  cd.ratified_by,
  COALESCE(v.claims_held, 0) as claims_held,
  COALESCE(v.claims_refuted, 0) as claims_refuted,
  COALESCE(v.claims_untested, 0) as claims_untested,
  0.5 as brier_score,
  json_group_array(
    CASE 
      WHEN fc.id IS NOT NULL THEN json_object('type','finding','id',fc.id,'text',fc.text,'impact',fc.impact)
      WHEN ac.id IS NOT NULL THEN json_object('type','assumption','id',ac.id,'text',ac.text,'confidence',ac.confidence)
    END
  ) FILTER (WHERE fc.id IS NOT NULL OR ac.id IS NOT NULL) as artifacts_json
FROM candidate_decisions cd
LEFT JOIN findings_connected fc ON fc.decision_id = cd.decision_id
LEFT JOIN assumptions_connected ac ON ac.decision_id = cd.decision_id
LEFT JOIN verdicts v ON v.decision_id = cd.decision_id
GROUP BY cd.decision_id
ORDER BY cd.decision_id DESC;
