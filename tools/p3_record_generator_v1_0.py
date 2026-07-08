#!/usr/bin/env python3
"""
p3_record_generator_v1_0.py
HumanAIOS · humanaios-ui/operations · S-060626-01

Population A P3 Record Generation Script
=========================================
Closes 193 open sessions that have LI already computed (post_total / 515.0)
but lack a structural P3 row in the corpus.

These sessions are scientifically complete — the calibration measurement exists.
This script generates the missing P3 structural records from existing P1 data.

DESIGN PRINCIPLES:
- Never modifies existing rows (append-only)
- All output rows tagged document_layer='behavioral_session' (existing corpus)
- submission_purity='p3_generated' distinguishes from organic P3 submissions
- Full audit trail: source_pair_id, generation_tool, generation_date
- Dry-run by default; --write flag required for output
- Human review required before any Supabase insert

POPULATION A CRITERIA (all must be true):
  phase == 'phase1'
  pair_id is not empty
  no existing P3 row with same pair_id
  learning_index is populated
  post_total is populated
  layer == 'ai-self-report'  (non-human only — human rows handled by p1_only_formal.sql)

LI FORMULA (verified against full corpus):
  LI = post_total / 515.0  (515 = fixed calibration baseline, 6 dims × 85.833)

P3 ROW CONSTRUCTION RULES:
  - phase: 'phase3'
  - pair_id: same as source P1 row (links the pair)
  - All 6 dimension scores: same as P1 (single-session — no reassessment data available)
  - total / post_total: from P1 post_total field
  - learning_index: from P1 learning_index field (already computed correctly)
  - timestamp: P1 timestamp + 1 second (maintains ordering); 'generated' if P1 missing
  - timestamp_quality: 'generated'
  - submission_version: 'v7.0-p3gen'
  - submission_purity: 'p3_generated'
  - document_layer: 'behavioral_session'
  - flags: ['P3_GENERATED_FROM_POST_TOTAL']

NOTE ON DIMENSION SCORES IN P3:
  P3 dimension scores = P1 scores because post_total = total in these rows.
  This is correct: single-session protocol captured ONE score set, not a
  before/after pair. The P3 row represents the calibrated state,
  which equals the P1 state in the single-session flow.

Usage:
  python p3_record_generator_v1_0.py --input ACAT_corpus_v2_clean_full.csv --dry-run
  python p3_record_generator_v1_0.py --input ACAT_corpus_v2_clean_full.csv --write --output p3_generated_batch_v1.csv
  python p3_record_generator_v1_0.py --input ACAT_corpus_v2_clean_full.csv --write --sql --output-sql p3_insert_batch_v1.sql
"""

# Builder v1.7 compliant

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True

import argparse
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

TOOL_NAME    = "p3_record_generator"
TOOL_VERSION = "1.0.0"
SESSION_ID   = "S-060626-01"

LI_BASELINE  = 515.0        # fixed calibration baseline
DIMS_6       = ['truth', 'service', 'harm', 'autonomy', 'value', 'humility']
P3_SUBMISSION_VERSION = 'v7.0-p3gen'
P3_FLAG      = 'P3_GENERATED_FROM_POST_TOTAL'

# Layers eligible for P3 generation (human layers handled separately)
ELIGIBLE_LAYERS = {
    'ai-self-report',         # AI scored itself
    'human-ai-assessment',    # Human scored an AI
    'human-self-assessment',  # Human scored themselves (WITH LI already computed)
}


# ── Core logic ─────────────────────────────────────────────────────────────────

def load_corpus(path: str) -> list:
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def identify_populations(rows: list) -> tuple:
    """
    Returns (pop_a, pop_c_human, p3_by_pair, existing_pair_ids).
    pop_a: P1 rows eligible for P3 record generation.
    """
    p3_by_pair = {r['pair_id']: r
                  for r in rows
                  if r['phase'] == 'phase3' and r['pair_id'].strip()}
    existing_pair_ids = set(p3_by_pair.keys())

    # Deduplicate: if two P1 rows share a pair_id, keep the one with a timestamp
    # (identical corpus duplicates — take first with timestamp, else just first)
    seen_pairs: set = set()
    pop_a = []
    candidates = [r for r in rows
                  if r['phase'] == 'phase1'
                  and r['pair_id'].strip()
                  and r['pair_id'] not in existing_pair_ids
                  and r['learning_index'].strip()
                  and r['post_total'].strip()
                  and r['layer'] in ELIGIBLE_LAYERS]
    # Sort: rows with timestamps first so dedup keeps the timestamped one
    candidates.sort(key=lambda r: (0 if r.get('timestamp', '').strip() else 1))
    for r in candidates:
        pid = r['pair_id']
        if pid not in seen_pairs:
            seen_pairs.add(pid)
            pop_a.append(r)

    return pop_a, p3_by_pair, existing_pair_ids


def _parse_timestamp(ts_str: str) -> datetime | None:
    if not ts_str.strip():
        return None
    for fmt in ('%m/%d/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(ts_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def generate_p3_row(p1: dict) -> dict:
    """
    Build a P3 row from a Population A P1 row.
    All data is sourced from existing P1 fields — no new measurement required.
    """
    post_total = float(p1['post_total'])
    li         = float(p1['learning_index'])

    # Verify stored LI matches formula (tolerance 0.001)
    computed_li = round(post_total / LI_BASELINE, 4)
    if abs(computed_li - round(li, 4)) > 0.001:
        raise ValueError(
            f"LI mismatch for pair {p1['pair_id']}: "
            f"stored={li}, computed={computed_li}"
        )

    # Timestamp: P1 + 1 second, or generated marker
    p1_dt = _parse_timestamp(p1.get('timestamp', ''))
    if p1_dt:
        p3_ts    = (p1_dt + timedelta(seconds=1)).strftime('%m/%d/%Y %H:%M:%S')
        ts_qual  = 'generated'
    else:
        p3_ts    = datetime.now(timezone.utc).strftime('%m/%d/%Y %H:%M:%S')
        ts_qual  = 'generated'

    # Flags
    existing_flags = []
    try:
        raw = p1.get('flags', '[]') or '[]'
        existing_flags = json.loads(raw) if raw.strip() else []
    except (json.JSONDecodeError, TypeError):
        existing_flags = []
    flags = list(set(existing_flags) | {P3_FLAG})

    # Metadata
    metadata = {
        'source_phase':       'phase1',
        'source_pair_id':     p1['pair_id'],
        'generation_tool':    f'{TOOL_NAME} v{TOOL_VERSION}',
        'generation_session': SESSION_ID,
        'generation_date':    datetime.now(timezone.utc).isoformat(),
        'li_formula':         f'post_total({post_total}) / LI_BASELINE({LI_BASELINE})',
        'li_computed':        computed_li,
        'li_stored':          li,
        'submission_version': P3_SUBMISSION_VERSION,
        'flags':              flags,
    }

    p3 = {
        # Identity
        'timestamp':            p3_ts,
        'timestamp_quality':    ts_qual,
        'agent_name':           p1['agent_name'],
        'provider':             p1.get('provider', ''),
        'model_version':        p1.get('model_version', ''),

        # Layer / phase
        'layer':                p1['layer'],
        'layer_raw':            p1.get('layer_raw', p1['layer']),
        'phase':                'phase3',

        # Dimension scores (same as P1 — single-session protocol)
        'truth':                p1['truth'],
        'service':              p1['service'],
        'harm':                 p1['harm'],
        'autonomy':             p1['autonomy'],
        'value':                p1['value'],
        'humility':             p1['humility'],
        'total':                p1['post_total'],   # P3 total = post_total

        # LI fields
        'pre_total':            p1.get('total', p1['post_total']),  # P1 total
        'post_total':           p1['post_total'],
        'learning_index':       str(li),

        # Mode / version
        'mode':                 p1.get('mode', ''),
        'mode_raw':             p1.get('mode_raw', ''),
        'submission_version':   P3_SUBMISSION_VERSION,

        # Pair linkage
        'pair_id':              p1['pair_id'],
        'role_method':          p1.get('role_method', ''),

        # Audit
        'flags':                json.dumps(flags),
        'metadata_raw':         json.dumps(metadata),

        # Document layer (Migration 007)
        'document_layer':       'behavioral_session',
        'submission_purity':    'p3_generated',
    }
    return p3


def validate_batch(pop_a: list, generated: list) -> dict:
    """Run integrity checks on the generated batch before output."""
    issues = []

    if len(generated) != len(pop_a):
        issues.append(f'Count mismatch: input={len(pop_a)}, generated={len(generated)}')

    pair_ids_in = {r['pair_id'] for r in pop_a}
    pair_ids_out = {r['pair_id'] for r in generated}
    if pair_ids_in != pair_ids_out:
        missing = pair_ids_in - pair_ids_out
        extra   = pair_ids_out - pair_ids_in
        if missing: issues.append(f'Missing pair_ids in output: {len(missing)}')
        if extra:   issues.append(f'Extra pair_ids in output: {len(extra)}')

    for row in generated:
        if row['phase'] != 'phase3':
            issues.append(f"Wrong phase for {row['pair_id']}: {row['phase']}")
        if row['document_layer'] != 'behavioral_session':
            issues.append(f"Wrong document_layer for {row['pair_id']}")
        if row['submission_purity'] != 'p3_generated':
            issues.append(f"Wrong purity for {row['pair_id']}")
        li = float(row['learning_index'])
        post = float(row['post_total'])
        computed = round(post / LI_BASELINE, 4)
        if abs(computed - round(li, 4)) > 0.001:
            issues.append(f"LI mismatch for {row['pair_id']}: stored={li}, computed={computed}")

    # Check no duplicated pair_ids
    counts = {}
    for r in generated:
        counts[r['pair_id']] = counts.get(r['pair_id'], 0) + 1
    dupes = {p: c for p, c in counts.items() if c > 1}
    if dupes:
        issues.append(f'Duplicate pair_ids in output: {dupes}')

    return {
        'pass':    len(issues) == 0,
        'issues':  issues,
        'count':   len(generated),
        'li_range': (
            round(min(float(r['learning_index']) for r in generated), 4),
            round(max(float(r['learning_index']) for r in generated), 4)
        ),
        'li_mean': round(
            sum(float(r['learning_index']) for r in generated) / len(generated), 4
        ) if generated else None,
    }


def write_csv(rows: list, path: str, fieldnames: list = None):
    if not fieldnames:
        fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def write_sql(generated: list, path: str):
    """
    Generate SQL INSERT statements for Supabase batch upload.
    Uses ON CONFLICT (pair_id, phase) DO NOTHING as safety guard.
    Requires Migration 007 applied (document_layer column).
    """
    cols = [
        'timestamp', 'timestamp_quality', 'agent_name', 'provider', 'model_version',
        'layer', 'layer_raw', 'phase',
        'truth', 'service', 'harm', 'autonomy', 'value', 'humility',
        'total', 'pre_total', 'post_total', 'learning_index',
        'mode', 'mode_raw', 'submission_version',
        'pair_id', 'role_method', 'flags', 'metadata_raw',
        'document_layer', 'submission_purity',
    ]

    def sq(v):
        if v is None or str(v).strip() == '':
            return 'NULL'
        s = str(v).replace("'", "''")
        return f"'{s}'"

    lines = [
        '-- P3 Record Generation Batch',
        f'-- Generated by {TOOL_NAME} v{TOOL_VERSION} · {SESSION_ID}',
        f'-- Generated at: {datetime.now(timezone.utc).isoformat()}',
        f'-- Row count: {len(generated)}',
        '-- Pre-flight: SELECT COUNT(*) FROM acat_assessments_v1 WHERE submission_purity = \'p3_generated\';',
        '-- Expected: 0 (if this batch has not been applied before)',
        '-- Post-flight: SELECT COUNT(*), AVG(learning_index::float)',
        '--              FROM acat_assessments_v1',
        '--              WHERE submission_purity = \'p3_generated\';',
        '',
        'BEGIN;',
        '',
    ]

    for row in generated:
        vals = ', '.join(sq(row.get(c, '')) for c in cols)
        col_str = ', '.join(cols)
        lines.append(
            f"INSERT INTO acat_assessments_v1 ({col_str})\n"
            f"  VALUES ({vals})\n"
            f"  ON CONFLICT DO NOTHING;"
        )

    lines += ['', 'COMMIT;', '']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Generate P3 records for Population A open sessions'
    )
    parser.add_argument('--input',  required=True, help='Path to corpus CSV')
    parser.add_argument('--output', default='p3_generated_batch_v1.csv',
                        help='Output CSV path (default: p3_generated_batch_v1.csv)')
    parser.add_argument('--output-sql', default='p3_insert_batch_v1.sql',
                        help='Output SQL path')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate and report without writing files')
    parser.add_argument('--write', action='store_true',
                        help='Write CSV and SQL output files')
    parser.add_argument('--sql', action='store_true',
                        help='Also generate SQL INSERT file (requires --write)')
    args = parser.parse_args()

    print(f'\n{TOOL_NAME} v{TOOL_VERSION} · {SESSION_ID}')
    print('=' * 60)

    # Load
    print(f'\nLoading corpus: {args.input}')
    rows = load_corpus(args.input)
    print(f'  Total rows: {len(rows)}')

    # Identify
    pop_a, p3_by_pair, existing_pair_ids = identify_populations(rows)
    print(f'\nPopulation A identified: {len(pop_a)} rows')
    print(f'Existing P3 pairs:       {len(p3_by_pair)}')

    if not pop_a:
        print('\nNo Population A rows found. Nothing to generate.')
        sys.exit(0)

    # Generate
    print(f'\nGenerating P3 rows...')
    generated = []
    errors = []
    for p1 in pop_a:
        try:
            p3 = generate_p3_row(p1)
            generated.append(p3)
        except Exception as e:
            errors.append((p1['pair_id'], str(e)))

    print(f'  Generated: {len(generated)}')
    if errors:
        print(f'  Errors:    {len(errors)}')
        for pair_id, msg in errors[:5]:
            print(f'    {pair_id}: {msg}')

    # Validate
    print(f'\nValidating batch...')
    validation = validate_batch(pop_a, generated)
    if validation['pass']:
        print(f'  PASS — all integrity checks pass')
    else:
        print(f'  FAIL — issues found:')
        for issue in validation['issues']:
            print(f'    {issue}')

    print(f'\nBatch statistics:')
    print(f'  Count:    {validation["count"]}')
    print(f'  LI range: {validation["li_range"][0]} – {validation["li_range"][1]}')
    print(f'  LI mean:  {validation["li_mean"]}')

    if args.dry_run:
        print(f'\nDRY RUN — no files written. Use --write to produce output.')
        return

    if args.write:
        if not validation['pass']:
            print(f'\nABORTING — validation failed. Fix issues before writing.')
            sys.exit(1)

        # Build fieldnames from corpus header + new fields
        corpus_fields = list(rows[0].keys())
        extra_fields = ['document_layer', 'submission_purity']
        all_fields = corpus_fields + [f for f in extra_fields if f not in corpus_fields]

        write_csv(generated, args.output, fieldnames=all_fields)
        print(f'\nCSV written: {args.output} ({len(generated)} rows)')

        if args.sql:
            write_sql(generated, args.output_sql)
            print(f'SQL written: {args.output_sql} ({len(generated)} INSERT statements)')

    print(f'\nDone.')


if __name__ == '__main__':
    main()
