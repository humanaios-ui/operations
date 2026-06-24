-- p1_only_formal_closure_v2.sql
-- Generated: 2026-06-06 | Source: Google Sheet canonical N=608
-- Purpose: Close 34 Pop C (human-assessment, no LI, no P3) sessions as p1_only_formal
-- Zone 2 authority: p1_only_formal RATIFIED (session S-060626-01)
-- CORRECTED from v1 (37 rows) — single-pass exclusive classification yields 34

-- Pre-flight: verify pair_ids exist in acat_assessments_v1
-- Run this SELECT first before applying the UPDATE:
-- SELECT pair_id, submission_purity FROM acat_assessments_v1
-- WHERE pair_id IN (
--   'human_1771287457000_h566','human_1771290498000_8zra','human_1771361490000_j849',
--   'human_1771395746000_a9qy','human_1771466028000_ulni','human_1771478923000_2bq9',
--   'human_1771510405000_1iyc','human_1771511084000_ezsg','human_1771562890000_vl34',
--   'human_1771563108000_8u95','human_1771571502000_ylde','human_1771571741000_d2mw',
--   'human_1771572129000_ws61','human_1771572873000_uahb','human_1771575825000_jlz8',
--   'human_1771576423000_6xlq','human_1771578217000_sktg','human_1771582404000_e9md',
--   'human_1771648012000_5ue2','human_1771652553000_yufb','human_1771652738000_qvm5',
--   'human_1771655050000_rst2','human_1771656811000_wb84','human_1771676624000_uj7w',
--   'human_1771676629000_9wf9','human_1771676634000_dy7e','human_1771694876000_ou2i',
--   'human_1771702023000_v8t6','human_1771710438000_za8j','human_1771710822000_woyy',
--   'human_1771710854000_eyj3','human_1771711837000_l62l','human_1771729268000_nyuu',
--   'human_1771973944000_1882'
-- ) AND phase = 'phase1';

BEGIN;

UPDATE acat_assessments_v1
SET submission_purity = 'p1_only_formal'
WHERE pair_id IN (
  'human_1771287457000_h566',
  'human_1771290498000_8zra',
  'human_1771361490000_j849',
  'human_1771395746000_a9qy',
  'human_1771466028000_ulni',
  'human_1771478923000_2bq9',
  'human_1771510405000_1iyc',
  'human_1771511084000_ezsg',
  'human_1771562890000_vl34',
  'human_1771563108000_8u95',
  'human_1771571502000_ylde',
  'human_1771571741000_d2mw',
  'human_1771572129000_ws61',
  'human_1771572873000_uahb',
  'human_1771575825000_jlz8',
  'human_1771576423000_6xlq',
  'human_1771578217000_sktg',
  'human_1771582404000_e9md',
  'human_1771648012000_5ue2',
  'human_1771652553000_yufb',
  'human_1771652738000_qvm5',
  'human_1771655050000_rst2',
  'human_1771656811000_wb84',
  'human_1771676624000_uj7w',
  'human_1771676629000_9wf9',
  'human_1771676634000_dy7e',
  'human_1771694876000_ou2i',
  'human_1771702023000_v8t6',
  'human_1771710438000_za8j',
  'human_1771710822000_woyy',
  'human_1771710854000_eyj3',
  'human_1771711837000_l62l',
  'human_1771729268000_nyuu',
  'human_1771973944000_1882'
)
AND phase = 'phase1';

-- Verify: should update exactly 34 rows (or fewer if some pair_ids not in Supabase yet)
-- SELECT COUNT(*) FROM acat_assessments_v1 WHERE submission_purity = 'p1_only_formal';

COMMIT;
