#!/usr/bin/env python3
"""Independent decimal constraint oracle. No agent messages are used."""
import csv
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

NUMERIC = ('baseline','proposed','min_allowed','max_allowed','max_delta')

def decimal(value):
    if isinstance(value, bool) or value is None or str(value).strip() == '':
        raise ValueError('missing_or_invalid_numeric')
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('missing_or_invalid_numeric')
    if not v.is_finite():
        raise ValueError('nonfinite_numeric')
    return v

def evaluate(record):
    try:
        n = {k:decimal(record.get(k)) for k in NUMERIC}
    except ValueError as exc:
        return {'verdict':'UNKNOWN','reasons':[str(exc)]}
    if n['min_allowed'] > n['max_allowed'] or n['max_delta'] < 0:
        return {'verdict':'UNKNOWN','reasons':['invalid_requirement_manifest']}
    reasons=[]
    if n['proposed'] < n['min_allowed']: reasons.append('below_minimum')
    if n['proposed'] > n['max_allowed']: reasons.append('above_maximum')
    if abs(n['proposed']-n['baseline']) > n['max_delta']: reasons.append('delta_exceeded')
    state = str(record.get('artifact_present','')).strip().lower()
    if state in ('unknown','unavailable',''):
        return {'verdict':'UNKNOWN','reasons':['artifact_readback_unavailable'] + reasons}
    if state not in ('true','false'):
        return {'verdict':'UNKNOWN','reasons':['invalid_artifact_state'] + reasons}
    if state == 'false':
        reasons.append('artifact_absent_after_confirmed_write')
    else:
        try:
            actual = decimal(record.get('actual_value'))
        except ValueError:
            return {'verdict':'UNKNOWN','reasons':['invalid_artifact_readback'] + reasons}
        if actual != n['proposed']: reasons.append('artifact_value_mismatch')
    if not reasons:
        reasons = ['all_constraints_satisfied']
        if abs(n['proposed']-n['baseline']) == n['max_delta']:
            reasons.append('delta_boundary_inclusive' if n['max_delta'] != 0 else 'zero_delta_allowed')
    return {'verdict':'FAIL' if reasons[0] != 'all_constraints_satisfied' else 'PASS','reasons':reasons}

def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: python oracle.py FIXTURE_CASES.csv')
    with open(sys.argv[1],newline='',encoding='utf-8') as fh:
        rows=list(csv.DictReader(fh))
    mismatches=[]
    for row in rows:
        result=evaluate(row)
        ok=result['verdict']==row['expected_oracle'] and row['expected_reason'] in result['reasons']
        print(json.dumps({'case_id':row['case_id'],**result,'fixture_match':ok}))
        if not ok: mismatches.append(row['case_id'])
    print(json.dumps({'fixture_count':len(rows),'matched':len(rows)-len(mismatches),'mismatches':mismatches}))
    if mismatches: raise SystemExit(1)

if __name__ == '__main__': main()
