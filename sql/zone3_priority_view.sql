-- ============================================================
-- zone3_priority_view
-- Priority scoring over live zone3_queue
-- Session: S-061126 · HumanAIOS LLC
-- Z2 ratified: S-061126
-- Deploy via: apply_migration or direct SQL at terminal
-- ============================================================

CREATE OR REPLACE VIEW public.zone3_priority_view
WITH (security_invoker = true)
AS
SELECT
  id,
  title,
  severity,
  carry_count,
  source_session,
  created_at,
  EXTRACT(days FROM now() - created_at)::int AS age_days,
  CASE severity
    WHEN 'CRITICAL' THEN 100
    WHEN 'WARN'     THEN 50
    WHEN 'BLOCKED'  THEN 30
    ELSE 10
  END
  + (COALESCE(carry_count, 0) * 5)
  + EXTRACT(days FROM now() - created_at)::int
  AS priority_score,
  CASE
    WHEN COALESCE(carry_count, 0) >= 5 THEN true
    ELSE false
  END AS p28_triggered
FROM zone3_queue
WHERE resolved_at IS NULL
ORDER BY priority_score DESC;

GRANT SELECT ON public.zone3_priority_view TO anon, authenticated, service_role;

COMMENT ON VIEW public.zone3_priority_view IS
  'Live Z3 item priority scoring. Score = severity weight + (carry_count × 5) + age_days.
   p28_triggered = true when carry_count >= 5 (P28 Stale Carry Trigger).
   Ratified S-061126.';
