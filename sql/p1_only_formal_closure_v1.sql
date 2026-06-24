-- ============================================================
-- p1_only_formal_closure_v1.sql
-- HumanAIOS · humanaios-ui/operations · S-060626-01
--
-- Population C Formal Closure
-- Zone 2 ratification: Night · 2026-06-06 · S-060626-01
--   Designation: p1_only_formal
--   Scope: 37 human-layer sessions (human-self-assessment / human-ai-assessment)
--          with no LI, no post_total, and no existing P3 row.
--          Original respondents uncontactable (anonymity rate ~92%).
--          These rows contribute valid P1 dimension data and are retained in
--          corpus aggregates. They are formally closed as single-phase entries.
--
-- WHAT THIS DOES:
--   Updates submission_purity to 'p1_only_formal' on 37 P1 rows.
--   Removes them from the open-session count without destroying any data.
--   Does NOT delete rows. Does NOT change dimension scores or LI.
--   Does NOT affect corpus aggregate statistics (document_layer unchanged).
--
-- PRE-FLIGHT (run before applying):
--   SELECT COUNT(*) FROM acat_assessments_v1
--   WHERE submission_purity = 'p1_only_formal';
--   Expected: 0
--
--   SELECT COUNT(*) FROM acat_assessments_v1
--   WHERE pair_id IN (<pair_ids below>)
--   AND phase = 'phase1';
--   Expected: 37
--
-- POST-FLIGHT (run after applying):
--   SELECT submission_purity, COUNT(*) FROM acat_assessments_v1
--   WHERE pair_id IN (<pair_ids below>)
--   GROUP BY submission_purity;
--   Expected: p1_only_formal | 37
--
-- ROLLBACK (if needed):
--   UPDATE acat_assessments_v1
--   SET submission_purity = 'unknown'
--   WHERE submission_purity = 'p1_only_formal'
--   AND pair_id IN (<pair_ids below>);
-- ============================================================

BEGIN;

UPDATE acat_assessments_v1
SET
    submission_purity = 'p1_only_formal',
    metadata_raw = jsonb_set(
        COALESCE(metadata_raw::jsonb, '{}'::jsonb),
        '{p1_only_formal}',
        jsonb_build_object(
            'ratification', 'Night · 2026-06-06 · S-060626-01',
            'reason', 'human-layer session: original respondent uncontactable or anonymous; no P3 completion possible at scale',
            'applied_at', now()::text,
            'applied_by', 'p1_only_formal_closure_v1.sql'
        )
    )::text
WHERE
    phase = 'phase1'
    AND pair_id IN (
        'anthropic_1771971434000_e4uf',
        'google_1772670072000_w9ov',
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
        'human_1771973944000_1882',
        'openai_1773346051000_oe1f'
    );

-- Verify row count updated (should be 37)
-- SELECT COUNT(*) FROM acat_assessments_v1
-- WHERE submission_purity = 'p1_only_formal';

COMMIT;
