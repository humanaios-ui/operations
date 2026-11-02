#!/usr/bin/env python3
"""Re-derive checks from raw local receipts and REPLAY owned code in new child processes.

Same-operator replay, not third-party independent attestation. Does not accept
an executable path; only hashes and runs two fixed repository-owned files.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
import sys

import collect_live as pilot
sys.path.insert(0,str(pilot.HERE.parent))
import calibrate as acat


def verify(folder):
    protocol=folder/'protocol.json'
    p, _=acat.load(protocol)
    acat.validate_protocol(p)
    if p != pilot.protocol():
        raise ValueError('protocol differs from code-owned frozen reference contract')
    manifest_before=acat.load(folder/'runtime_before.manifest.json')[0]
    manifest_after=acat.load(folder/'runtime_after.manifest.json')[0]
    if manifest_before != pilot.runtime_manifest(pilot.BASE):
        raise ValueError('baseline binary/source manifest mismatch')
    if manifest_after != pilot.runtime_manifest(pilot.AFTER):
        raise ValueError('corrected binary/source manifest mismatch')
    for phase,source,manifest in [('P1',pilot.BASE,manifest_before),('P2',pilot.BASE,manifest_before),('P3',pilot.AFTER,manifest_after)]:
        doc=acat.load(folder/(phase.lower()+'.json'))[0]
        case_map=acat.validate_phase(doc,phase,p,acat.validate_protocol(p))
        if doc['capture_class'] != 'SELF_REPORTED':raise ValueError('capture label drift')
        if doc['artifact_sha256']!=pilot.SHA(pilot.CANON(manifest)):
            raise ValueError('phase artifact hash mismatch')
        for case in p['cases']:
            id=case['id']
            reference=case_map[id]['evidence_ref']
            path_name, hash_claim=reference.split(':sha256=')
            if path_name != 'capture_'+phase+'_'+id+'.json' or '/' in path_name:
                raise ValueError('invalid receipt reference')
            raw_path=folder/path_name
            if pilot.SHA(raw_path.read_bytes()) != hash_claim:
                raise ValueError('raw receipt mismatch '+path_name)
            record=acat.load(raw_path)[0]
            expected_input=case['baseline_input' if phase=='P1' else 'challenge_input']
            if record['input'] != expected_input or record['response'] != case_map[id]['response']:
                raise ValueError('raw data does not match phase observation')
            if record['exit_code'] != 0 or record['artifact_sha256'] != doc['artifact_sha256']:
                raise ValueError('execution receipt inconsistency')
            if record['stdout_sha256'] != pilot.SHA(record['stdout_raw'].encode()):
                raise ValueError('stdout digest mismatch')
            if json.loads(record['stdout_raw']) != record['response']:
                raise ValueError('stdout content mismatch')
            result, _=pilot.run_one(source,expected_input)
            if result != record['response']:
                raise ValueError('fresh process replay disagreement '+phase+'/'+id)
    result=acat.evaluate(str(protocol),str(folder/'p1.json'),str(folder/'p2.json'),
                         str(folder/'p3.json'),str(folder/'p1.commit.json'))
    if result!=acat.load(folder/'report.json')[0]:
        raise ValueError('scoring report changed')
    return {'status':'SAME_OPERATOR_REPLAY_PASS','fresh_processes':12,
            'passes':result['passes'],'evidence_state':result['evidence_state'],
            'admission':result['admission']}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--replay-owned',action='store_true')
    ap.add_argument('--evidence-dir',required=True,type=Path)
    args=ap.parse_args()
    if not args.replay_owned:ap.error('explicit --replay-owned required')
    try:
        output=verify(args.evidence_dir)
        print(json.dumps(output,sort_keys=True))
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print('REPLAY REFUSED: '+str(exc),file=sys.stderr)
        sys.exit(2)
