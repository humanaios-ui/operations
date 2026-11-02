#!/usr/bin/env python3
"""ACAT-R non-injected workload: actual existing On-Track Reflex v0.1 subprocess.

Offline, real GitHub-sourced metadata; no faults injected into code or input;
reference oracle is a separate implementation with no DUT imports.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from reference_oracle import compare

BLOB_SHA1='25bcb7d1be105d4e7869f9b918436eac430e2709'
SOURCE_REL='humanaios-funding-pipeline/resource-miner/resource_miner/on_track_reflex.py'
SHA_REPO='52aa7c0ed70f6e24ec050d0d56788a791e5f78f7'
EXPECTED_ITEMS=24


def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def json_bytes(obj)->bytes:
    return (json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')


def load_fixture(path:Path)->dict:
    raw=path.read_bytes()
    if len(raw)>100_000:raise ValueError('fixture oversized')
    doc=json.loads(raw)
    if doc.get('schema')!='acat-r.external-workload-input.v0.1':raise ValueError('schema')
    if doc.get('repository')!='humanaios-ui/operations':raise ValueError('repository')
    if doc.get('original_source_sha')!=SHA_REPO or doc.get('original_module_git_blob_sha1')!=BLOB_SHA1:
        raise ValueError('unrecognized upstream reference')
    arr=doc['items']
    if len(arr)!=EXPECTED_ITEMS or len({x['number'] for x in arr})!=EXPECTED_ITEMS:
        raise ValueError('sample set size/unique')
    if {x['number'] for x in arr}.issuperset({822,928}) is False:raise ValueError('missing anchors')
    for x in arr:
        if set(x)-{'number','title','state','body','labels','pull_request'}:
            raise ValueError('extraneous snapshot data')
        if x['state'] not in ('open','closed') or type(x['number']) is not int:
            raise ValueError('invalid real snapshot item')
    return doc


def run_actual(source:Path, items:list[dict], temp:Path, phase:str):
    input_path=temp/(phase+'_input.json')
    output_path=temp/(phase+'_output.json')
    input_path.write_bytes(json_bytes(items))
    argv=[sys.executable,'-I',str(source.resolve()),'--input',str(input_path), '--json-out',str(output_path),
          '--execution-event','OFFLINE_FIXTURE','--execution-sha',SHA_REPO]
    finished=subprocess.run(argv,capture_output=True,text=True,timeout=25,check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if finished.returncode!=0 or not output_path.exists():
        raise RuntimeError('existing runtime failed '+phase+': '+finished.stderr[-600:])
    if finished.stdout.strip():raise ValueError('unexpected stdout')
    raw=output_path.read_bytes()
    report=json.loads(raw)
    reference=compare(items,report)
    return {'phase':phase,'process_exit_code':finished.returncode,'input_sha256':digest(input_path.read_bytes()),
            'output_sha256':digest(raw),'report_snapshot_sha256':report['snapshot_sha256'],
            'reference':reference,'report':report}


def run(source:Path,fixture:Path)->dict:
    src=source.read_bytes()
    if git_blob_sha1(src)!=BLOB_SHA1:
        raise RuntimeError('existing runtime source changed; pin/consent required')
    doc=load_fixture(fixture)
    items=doc['items']
    baseline=items[:8]
    # Explicitly commit source, protocol, and P1 input bytes BEFORE any challenge is run.
    p1_commit={'source_git_blob_sha1':BLOB_SHA1,'source_sha256':digest(src),
               'snapshot_sha256':digest(fixture.read_bytes()),'P1_input_sha256':digest(json_bytes(baseline)),
               'scope':'Z1 research receipt; not an authenticated independent witness'}
    with tempfile.TemporaryDirectory(prefix='acat-r-existing-') as tempstr:
        temp=Path(tempstr)
        commit_path=temp/'P1.commit.json'
        with commit_path.open('xb') as f:f.write(json_bytes(p1_commit))
        p1=run_actual(source,baseline,temp,'P1')
        p2=run_actual(source,items,temp,'P2')
        p3=run_actual(source,items,temp,'P3')
        if p1['input_sha256']!=p1_commit['P1_input_sha256']:raise RuntimeError('P1 changed after commitment')
        if p2['input_sha256']!=p3['input_sha256']:raise RuntimeError('P2/P3 did not use identical input bytes')
        if p2['output_sha256']!=p3['output_sha256']:raise RuntimeError('unchanged P3 replay output differed')
    success=all(p['reference']['reference_agreement'] for p in (p1,p2,p3))
    return {'schema':'humanaios.acat-r.noninjected-workload-proof.v0.1',
      'subject':'EXISTING_HUMANAIOS_ON_TRACK_REFLEX_V01','source_repository_commit':SHA_REPO,
      'original_source_git_blob_sha1':BLOB_SHA1,'original_source_sha256':digest(src),
      'git_source_ref':'https://github.com/humanaios-ui/operations/blob/'+SHA_REPO+'/'+SOURCE_REL,
      'runtime':{'python':platform.python_version(),'platform':platform.platform(),
                 'actual_child_processes':3,'DUT_modified':False,'faults_injected':False},
      'source_snapshot_sha256':digest(fixture.read_bytes()),'sampling':'GITHUB_CONNECTOR_DERIVED_MINIMIZED_SNAPSHOT_NOT_COMPLETE_OR_SIGNED',
      'p1_commit':p1_commit,
      'phases':[{k:v for k,v in p.items() if k!='report'} for p in (p1,p2,p3)],
      'P1_P2_P3_reference_agreement':success,'P2_P3_deterministic_replay':p2['output_sha256']==p3['output_sha256'],
      'recovered_cases':0,'regressed_cases':0,'challenge_replay_gain':0.0,
      'status':'CONTRACT_CONFORMANCE_PASS' if success else 'REFERENCE_DISAGREEMENT',
      'limitations':['P2 is workload expansion, not injected failure. P3 is unchanged exact replay, not a correction.',
        'This tests observed correctness relative to a separately written contract oracle, not a validated metrological calibration instrument.',
        'Source snapshot is sampled connected GitHub metadata, not full raw issue evidence or independently signed.',
        'Reference agreement does not prove live deployment, correct third-party source claims, human outcomes or authorization.',
        'Oracle is separately implemented by the same investigator; no blinded independent human review has occurred.'],
      'evidence_state':'CONNECTED_SOURCE_SNAPSHOT_UNAUTHENTICATED','authority_effect':'NONE','can_authorize':False,
      'admission':'HOLD','production_ready':False}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        report=run(args.source,args.fixture)
        with args.output.open('xb') as f:f.write(json_bytes(report))
        print(json.dumps({'status':report['status'],'phase_cases':[(x['phase'],x['reference']['case_count']) for x in report['phases']],
                          'same_replay':report['P2_P3_deterministic_replay'],'admission':report['admission']}))
        return 0 if report['P1_P2_P3_reference_agreement'] else 1
    except (OSError,TypeError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        print('ACAT-R noninjected REFUSED: '+str(e),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
