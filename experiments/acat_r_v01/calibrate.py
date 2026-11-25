#!/usr/bin/env python3
"""ACAT-R v0.1: offline, observational runtime calibration; no target execution."""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
import sys

PROTOCOL = 'humanaios.acat-r.protocol.v0.1'
PHASE = 'humanaios.acat-r.phase.v0.1'
COMMIT = 'humanaios.acat-r.commit.v0.1'
HASH = re.compile(r'^[0-9a-f]{64}$')
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$')
MAX_BYTES = 1_000_000
MAX_CASES = 100

class InvalidEvidence(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise InvalidEvidence(message)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvidence('duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(s):
    raise InvalidEvidence('nonfinite JSON number: ' + s)


def load(path):
    with open(path, 'rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'input exceeds 1 MB limit')
    try:
        obj = json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    except (UnicodeError, json.JSONDecodeError) as e:
        raise InvalidEvidence('invalid UTF-8 JSON: ' + str(e)) from e
    require(isinstance(obj, dict), 'root must be object')
    return obj, digest(raw)


def shape(obj, allowed, required, where):
    require(isinstance(obj, dict), where + ' must be object')
    require(set(required) <= set(obj), where + ' missing required fields')
    require(set(obj) <= set(allowed), where + ' contains unknown fields: ' + str(set(obj) - set(allowed)))


def valid_id(value, label):
    require(isinstance(value, str) and ID.fullmatch(value) is not None, 'invalid ' + label)


def valid_sha(value, label):
    require(isinstance(value, str) and HASH.fullmatch(value) is not None, 'invalid ' + label)


def finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def validate_oracle(o):
    shape(o, {'kind', 'path', 'expected', 'atol', 'rtol'}, {'kind'}, 'oracle')
    kind = o['kind']
    require(kind in ('numeric', 'refusal', 'exact'), 'unknown oracle kind')
    if kind == 'refusal':
        require(set(o) == {'kind'}, 'refusal has surplus fields')
    else:
        require(set(o) >= {'kind', 'path', 'expected'}, 'oracle missing path/expected')
        require(isinstance(o['path'], str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*){0,7}', o['path']), 'invalid output path')
        if kind == 'numeric':
            require(finite_number(o['expected']), 'expected must be finite numeric')
            for t in ('atol', 'rtol'):
                v = o.get(t, 0)
                require(finite_number(v) and v >= 0, t + ' must be nonnegative finite')
        else:
            require(set(o) == {'kind', 'path', 'expected'}, 'exact oracle has surplus fields')
            require(type(o['expected']) in (str, int, float, bool) or o['expected'] is None, 'exact value must be scalar')


def validate_protocol(p):
    shape(p, {'schema','system_id','cases','provenance'}, {'schema','system_id','cases','provenance'}, 'protocol')
    require(p['schema'] == PROTOCOL, 'protocol version mismatch')
    valid_id(p['system_id'], 'system id')
    prov = p['provenance']
    shape(prov, {'description','authorization_ref'}, {'description','authorization_ref'}, 'provenance')
    require(all(isinstance(prov[k], str) and prov[k].strip() for k in prov), 'provenance needs strings')
    cases = p['cases']
    require(isinstance(cases,list) and 1 <= len(cases) <= MAX_CASES, 'cases must be 1..100')
    ids = set()
    for c in cases:
        shape(c, {'id','baseline_input','challenge_input','baseline_oracle','challenge_oracle','reference_id'},
              {'id','baseline_input','challenge_input','baseline_oracle','challenge_oracle','reference_id'}, 'case')
        valid_id(c['id'], 'case id')
        require(c['id'] not in ids, 'duplicate case id')
        ids.add(c['id'])
        require(isinstance(c['reference_id'], str) and c['reference_id'].strip(), 'missing independent reference id')
        for field in ('baseline_input','challenge_input'):
            require(isinstance(c[field], dict) and len(canonical(c[field])) <= 8192, 'invalid '+field)
        validate_oracle(c['baseline_oracle'])
        validate_oracle(c['challenge_oracle'])
    return {c['id']:c for c in cases}


def validate_phase(doc, expected_phase, protocol, cases):
    shape(doc, {'schema','phase','system_id','artifact_sha256','capture_class','observations'},
          {'schema','phase','system_id','artifact_sha256','capture_class','observations'}, 'phase document')
    require(doc['schema'] == PHASE and doc['phase'] == expected_phase, 'wrong phase/schema')
    require(doc['system_id'] == protocol['system_id'], 'subject mismatch')
    valid_sha(doc['artifact_sha256'], 'artifact hash')
    require(doc['capture_class'] in ('SYNTHETIC', 'SELF_REPORTED', 'INDEPENDENT_CAPTURE_CLAIM'), 'unknown capture class')
    observations = doc['observations']
    require(isinstance(observations, list) and len(observations) == len(cases), 'phase requires one result per case')
    indexed = {}
    for obs in observations:
        shape(obs, {'case_id','input_sha256','response','evidence_ref'},
              {'case_id','input_sha256','response','evidence_ref'}, 'observation')
        id_ = obs['case_id']
        require(isinstance(id_,str) and id_ in cases and id_ not in indexed, 'unknown/duplicate case')
        require(isinstance(obs['evidence_ref'],str) and obs['evidence_ref'].strip(), 'empty evidence reference')
        expected_input = cases[id_]['baseline_input' if expected_phase == 'P1' else 'challenge_input']
        require(obs['input_sha256'] == digest(canonical(expected_input)), 'input mismatch: '+id_)
        require(isinstance(obs['response'],dict) and len(canonical(obs['response'])) <= 8192, 'response is not bounded JSON object')
        indexed[id_] = obs
    return indexed


def check_response(response, oracle):
    ok = response.get('ok')
    if type(ok) is not bool:
        return False, 'response requires literal boolean ok'
    status = response.get('status')
    if status is not None and (not isinstance(status, str) or status not in ('OK','REFUSED')):
        return False, 'unrecognized status'
    if status and ((status == 'OK') != ok):
        return False, 'contradictory status and ok'
    if oracle['kind'] == 'refusal':
        if ok is not False:
            return False, 'expected refusal, got success'
        if not isinstance(response.get('reason'),str) or not response['reason'].strip():
            return False, 'refusal lacks reason'
        return True, 'structured refusal'
    if ok is not True:
        return False, 'expected successful result'
    def unsafe_numeric_string(o):
        if isinstance(o, str):
            return o.strip().lower() in {'nan', '+nan', '-nan', 'inf', '+inf', '-inf', 'infinity', '+infinity', '-infinity'}
        if isinstance(o, dict):
            return any(unsafe_numeric_string(v) for v in o.values())
        if isinstance(o, list):
            return any(unsafe_numeric_string(v) for v in o)
        return False
    if unsafe_numeric_string(response):
        return False, 'nonfinite numeric string in successful result'
    value = response
    for key in oracle['path'].split('.'):
        if not isinstance(value,dict) or key not in value:
            return False, 'missing output path'
        value = value[key]
    if oracle['kind'] == 'exact':
        return (type(value) is type(oracle['expected']) and value == oracle['expected'], 'exact result check')
    if not finite_number(value):
        return False, 'output is not finite numeric'
    target = oracle['expected']
    # Decimal from string representation preserves large integer distinctions
    # and avoids float overflow in difference/relative-tolerance arithmetic.
    observed = Decimal(str(value))
    reference = Decimal(str(target))
    atol = Decimal(str(oracle.get('atol', 0)))
    rtol = Decimal(str(oracle.get('rtol', 0)))
    tolerance = max(atol, rtol * abs(reference))
    return (abs(observed-reference) <= tolerance, 'numeric reference and tolerance check')


def commit_p1(protocol_path, p1_path):
    p, protocol_hash = load(protocol_path)
    cases = validate_protocol(p)
    d, p1_hash = load(p1_path)
    validate_phase(d,'P1',p,cases)
    return {'schema':COMMIT,'system_id':p['system_id'],'protocol_sha256':protocol_hash,
            'p1_sha256':p1_hash,'note':'Local digest only; not an independent timestamp or authenticated witness',
            'authority_effect':'NONE'}


def evaluate(protocol_path, p1_path, p2_path, p3_path, commitment_path):
    protocol, ph = load(protocol_path)
    cases = validate_protocol(protocol)
    p1, p1h = load(p1_path)
    p2, p2h = load(p2_path)
    p3, p3h = load(p3_path)
    commitment, _ = load(commitment_path)
    require(commitment == commit_p1(protocol_path,p1_path), 'P1 commitment mismatch')
    require(commitment['protocol_sha256'] == ph and commitment['p1_sha256'] == p1h,
            'commit hash mismatch')
    o1 = validate_phase(p1, 'P1', protocol, cases)
    o2 = validate_phase(p2, 'P2', protocol, cases)
    o3 = validate_phase(p3, 'P3', protocol, cases)
    require(p1['artifact_sha256'] == p2['artifact_sha256'], 'P1 and P2 must test same artifact')
    require(len({p1['capture_class'],p2['capture_class'],p3['capture_class']}) == 1,
            'mixed capture classes prohibited')
    rows = []
    for id_, c in cases.items():
        a, msg_a = check_response(o1[id_]['response'],c['baseline_oracle'])
        b, msg_b = check_response(o2[id_]['response'],c['challenge_oracle'])
        d, msg_d = check_response(o3[id_]['response'],c['challenge_oracle'])
        rows.append({'case_id':id_, 'p1_baseline_pass':a, 'p2_challenge_pass':b,
                     'p3_replay_pass':d,'p2_to_p3_recovered':not b and d,
                     'p2_to_p3_regressed':b and not d,
                     'messages':{'P1':msg_a,'P2':msg_b,'P3':msg_d},
                     'reference_id':c['reference_id']})
    total = len(rows)
    counts = {ph:sum(r[key] for r in rows) for ph,key in [('P1','p1_baseline_pass'),
                    ('P2','p2_challenge_pass'),('P3','p3_replay_pass')]}
    recovered = sum(r['p2_to_p3_recovered'] for r in rows)
    regressed = sum(r['p2_to_p3_regressed'] for r in rows)
    gain = (counts['P3']-counts['P2']) / total
    changed = p2['artifact_sha256'] != p3['artifact_sha256']
    return {'schema':'humanaios.acat-r.report.v0.1','system_id':protocol['system_id'],
            'subject_type':'GENERAL_MACHINE_RUNTIME','protocol_sha256':ph,
            'phase_sha256':{'P1':p1h,'P2':p2h,'P3':p3h},
            'artifact_sha256':{'P1':p1['artifact_sha256'],'P2':p2['artifact_sha256'],'P3':p3['artifact_sha256']},
            'capture_class':p1['capture_class'], 'cases_total':total,
            'passes':counts,'recovered_cases':recovered,'regressed_cases':regressed,
            'challenge_replay_gain':round(gain,8),
            'p3_artifact_changed':changed,'rows':rows,
            'evidence_state':('SYNTHETIC_ONLY' if p1['capture_class']=='SYNTHETIC' else 'UNVERIFIED_RUNTIME_OBSERVATIONS'),
            'authority_effect':'NONE','can_authorize':False,
            'admission':'HOLD_FOR_INDEPENDENT_REVIEW',
            'limitations':['No runtime is invoked by this evaluator.',
                'A local SHA-256 commitment does not prove chronological capture or authorship.',
                'Observed data and reference independence have not been externally authenticated.',
                'This is a runtime score, not the original ACAT Learning Index.',
                'P3 improvement is not causally attributable to a patch without external controls.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    commit = sub.add_parser('commit',help='Lock the P1 bytes and protocol digest')
    commit.add_argument('--protocol',required=True)
    commit.add_argument('--p1',required=True)
    commit.add_argument('--output',required=True)
    evaluate_cmd = sub.add_parser('evaluate',help='Read pre-collected data without executing a target')
    for v in ('protocol','p1','p2','p3','commit','output'):
        evaluate_cmd.add_argument('--'+v,required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'commit':
            report = commit_p1(args.protocol,args.p1)
        else:
            report = evaluate(args.protocol,args.p1,args.p2,args.p3,args.commit)
        output = Path(args.output)
        payload = json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode() + b'\n'
        with open(output, 'xb') as handle:
            handle.write(payload)
        print(json.dumps({'output':str(output),'schema':report['schema'],'admission':report.get('admission','NONE')}))
        return 0
    except (InvalidEvidence, OSError, ValueError) as e:
        print('ACAT-R REFUSED: ' + str(e),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
