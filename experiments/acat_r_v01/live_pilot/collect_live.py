#!/usr/bin/env python3
"""Capture actual, bounded OS child-process observations from OWNED demo only.

Runs only two in-repository scripts using current CPython (isolated -I -S),
never accepts arbitrary executable paths or code. Requires explicit --run-owned.
No network/shell; in-memory SQLite. Output dir must be absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import _sqlite3
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ACAT = HERE.parent / 'calibrate.py'
BASE = HERE / 'owned_runtime_before.py'
AFTER = HERE / 'owned_runtime_after.py'
SCHEMA = 'humanaios.acat-r.protocol.v0.1'
PHASE = 'humanaios.acat-r.phase.v0.1'
CANON = lambda x: json.dumps(x,sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False).encode()
SHA = lambda b: hashlib.sha256(b).hexdigest()


def protocol():
    return {
        'schema': SCHEMA, 'system_id':'owned-cpython-sqlite-runtime',
        'provenance': {'description':'Real isolated CPython child-process execution of deliberately faulted/corrected owned SQLite application. Not a Python or SQLite defect discovery.', 'authorization_ref':'operator-approved ACAT-R local owned-runtime pilot'},
        'cases': [
            {'id':'sqlite-atomicity','baseline_input':{'operation':'transfer','scenario':'valid'},
             'challenge_input':{'operation':'transfer','scenario':'partial_failure'},
             'baseline_oracle':{'kind':'numeric','path':'metrics.total','expected':100,'atol':0},
             'challenge_oracle':{'kind':'numeric','path':'metrics.total','expected':100,'atol':0},
             'reference_id':'conservation:sum(initial balances)=100 under aborted transaction'},
            {'id':'numeric-string','baseline_input':{'operation':'quantity','value':2.5},
             'challenge_input':{'operation':'quantity','value':'2.5'},
             'baseline_oracle':{'kind':'numeric','path':'metrics.amount','expected':2.5,'atol':0},
             'challenge_oracle':{'kind':'refusal'},
             'reference_id':'explicit input contract: quantities are finite JSON numbers, not strings'},
            {'id':'nan-string','baseline_input':{'operation':'finite','value':5.0},
             'challenge_input':{'operation':'finite','value':'NaN'},
             'baseline_oracle':{'kind':'numeric','path':'metrics.measurement','expected':5,'atol':0},
             'challenge_oracle':{'kind':'refusal'},
             'reference_id':'finite numeric input contract: NaN string refused'},
            {'id':'sqlite-unique','baseline_input':{'operation':'unique','code':'B'},
             'challenge_input':{'operation':'unique','code':'A'},
             'baseline_oracle':{'kind':'numeric','path':'metrics.count','expected':2,'atol':0},
             'challenge_oracle':{'kind':'refusal'},
             'reference_id':'SQLite UNIQUE constraint: duplicate code must be rejected'}
        ]}


def runtime_manifest(script):
    exe = Path(sys.executable).resolve()
    sqlite_ext = Path(_sqlite3.__file__).resolve()
    return {'python_executable_sha256':SHA(exe.read_bytes()),
            'python_version':platform.python_version(),
            'sqlite_version':sqlite3.sqlite_version,
            'sqlite_native_extension_sha256':SHA(sqlite_ext.read_bytes()),
            'source_sha256':SHA(script.read_bytes()),
            'runtime_mode':'CPython -I -S, stdin JSON, in-memory SQLite',
            'network':'not used by pilot code; no OS-level network sandbox',
            'capture_authority':'same operator; no independent witness'}


def run_one(script, data):
    args = [sys.executable, '-I', '-S', str(script)]
    environment = {'PYTHONHASHSEED':'0', 'PYTHONDONTWRITEBYTECODE':'1', 'LC_ALL':'C.UTF-8'}
    completed = subprocess.run(args, input=CANON(data)+b'\n',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=6,check=False, env=environment, cwd=str(HERE))
    if completed.returncode != 0:
        raise RuntimeError('owned process terminated with exit='+str(completed.returncode))
    if len(completed.stdout)>8192 or len(completed.stderr)>8192:
        raise RuntimeError('owned process response out of bounds')
    if completed.stderr:
        raise RuntimeError('unexpected stderr')
    raw = completed.stdout
    output = json.loads(raw, parse_constant=lambda t: (_ for _ in ()).throw(ValueError(t)))
    if type(output) is not dict:
        raise RuntimeError('not object')
    return output, {'exit_code':completed.returncode, 'stdin_sha256':SHA(CANON(data)+b'\n'),
                    'stdout_sha256':SHA(raw),'stdout_raw':raw.decode('utf-8'),
                    'stderr_sha256':SHA(completed.stderr),
                    'invocation':'local CPython -I -S owned_runtime_{before|after}.py; no shell'}


def write_new(path, obj):
    path.write_bytes(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n')


def collect(destination):
    if destination.exists():
        raise FileExistsError('refuse to overwrite an existing capture')
    destination.mkdir(parents=True)
    proto = protocol()
    ppath = destination / 'protocol.json'
    write_new(ppath,proto)
    cases=proto['cases']
    baseline_manifest = runtime_manifest(BASE)
    corrected_manifest = runtime_manifest(AFTER)
    # Build an artifact fingerprint from source+interpreter+sqlite components.
    before_hash=SHA(CANON(baseline_manifest))
    after_hash=SHA(CANON(corrected_manifest))
    assert before_hash!=after_hash
    write_new(destination/'runtime_before.manifest.json',baseline_manifest)
    write_new(destination/'runtime_after.manifest.json',corrected_manifest)
    phase_hashes={}
    for phase,script,artifact_hash in [('P1',BASE,before_hash),('P2',BASE,before_hash),('P3',AFTER,after_hash)]:
        observations=[]
        for case in cases:
            data=case['baseline_input' if phase=='P1' else 'challenge_input']
            result,record=run_one(script,data)
            record.update({'phase':phase,'case_id':case['id'],'input':data,'response':result,
                           'artifact_sha256':artifact_hash,'capture_class':'SELF_REPORTED'})
            logpath=destination / ('capture_'+phase+'_'+case['id']+'.json')
            write_new(logpath,record)
            observations.append({'case_id':case['id'],'input_sha256':SHA(CANON(data)),
                                 'response':result,'evidence_ref':logpath.name+':sha256='+SHA(logpath.read_bytes())})
        phase_doc={'schema':PHASE,'phase':phase,'system_id':proto['system_id'],
                   'artifact_sha256':artifact_hash,'capture_class':'SELF_REPORTED',
                   'observations':observations}
        file=destination/(phase.lower()+'.json')
        write_new(file,phase_doc)
        phase_hashes[phase]=SHA(file.read_bytes())
        if phase=='P1':
            # Lock P1 protocol and bytes BEFORE challenge execution.
            cp=destination/'p1.commit.json'
            command=[sys.executable,'-I','-S',str(ACAT),'commit','--protocol',str(ppath),
                     '--p1',str(file),'--output',str(cp)]
            done=subprocess.run(command,capture_output=True,text=True,timeout=8,check=False,
                                env={'PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'})
            if done.returncode!=0:raise RuntimeError('P1 commit failed: '+done.stderr)
            write_new(destination/'commit_command_receipt.json',{'exit':done.returncode,'stdout':done.stdout.strip(),'p1_sha256':phase_hashes['P1'],'protocol_sha256':SHA(ppath.read_bytes())})
    out=destination/'report.json'
    command=[sys.executable,'-I','-S',str(ACAT),'evaluate','--protocol',str(ppath),
             '--p1',str(destination/'p1.json'),'--p2',str(destination/'p2.json'),
             '--p3',str(destination/'p3.json'),'--commit',str(destination/'p1.commit.json'),
             '--output',str(out)]
    completed=subprocess.run(command,capture_output=True,text=True,timeout=8,check=False,
                              env={'PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'})
    if completed.returncode!=0:raise RuntimeError('ACAT-R evaluation failed: '+completed.stderr)
    report=json.loads(out.read_bytes())
    if report['passes'] != {'P1':4,'P2':1,'P3':4}:
        raise RuntimeError('unexpected observation matrix '+str(report['passes']))
    if report['evidence_state'] != 'UNVERIFIED_RUNTIME_OBSERVATIONS':
        raise RuntimeError('evidence improperly promoted')
    # This inventory binds all collected files but is neither independent nor authenticated.
    hashes={p.name:SHA(p.read_bytes()) for p in sorted(destination.glob('*.json'))}
    write_new(destination/'inventory.json',{'schema':'humanaios.acat-r.local-evidence-inventory.v0.1',
        'files_sha256':hashes,'reported_passes':report['passes'],
        'scope':'REAL OWNED APP executed under CPython + SQLite; planted faults; same operator collected; no independent attestation',
        'authority_effect':'NONE','admission':'HOLD'})
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-owned',action='store_true',help='Opt in to actual owned CPython/SQLite child-process execution')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if not args.run_owned:parser.error('must supply --run-owned to execute the local pilot')
    report=collect(args.output_dir)
    print(json.dumps({'passes':report['passes'],'recovered':report['recovered_cases'],
                      'regressed':report['regressed_cases'],
                      'capture_class':report['capture_class'],
                      'evidence_state':report['evidence_state'], 'admission':report['admission']},sort_keys=True))


if __name__=='__main__':
    main()
