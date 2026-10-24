"""Z1 qualification of a frozen live-inspected PR: no GitHub calls, no source writes.

Run from a full HumanAIOS Resource Miner checkout to recompute the initial broker
projection. The fixture's metadata is a research readback copied from a separate
connected GitHub source lookup, NOT a cryptographically authenticated attestation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

from resource_miner.independent_readback import board_html, qualify, systems_report
from resource_miner.internal_repository_broker import project


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,help='An OUTSIDE-THE-REPOSITORY output directory')
    args=parser.parse_args(argv)
    here=Path(__file__).resolve().parents[1] / 'tests' / 'fixtures' / 'internal_readback'
    files={name:here/name for name in ('snapshot.json','initial_broker_projection.json','github_readback_pr987.json','challenge_corrections_pr987.json')}
    before={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
    get=lambda key:json.loads(files[key].read_text(encoding='utf-8'))
    snapshot=get('snapshot.json')
    original=get('initial_broker_projection.json')
    generated=project(snapshot)
    if original != generated:
        raise ValueError('broker projection diverges from frozen evidence; do not silently rebase')
    result=qualify(snapshot,generated,get('github_readback_pr987.json'),get('challenge_corrections_pr987.json'))
    output=Path(args.output).resolve()
    # Work remains outside repo, never mutate source files or fixtures.
    repo_root = Path(__file__).resolve().parents[3]
    if output == repo_root or repo_root in output.parents:
        raise ValueError('output must be outside repository worktree')
    output.mkdir(parents=True,exist_ok=True)
    (output/'board.html').write_text(board_html(result),encoding='utf-8')
    (output/'report.txt').write_text(systems_report(result),encoding='utf-8')
    (output/'qualification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    after={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
    if before!=after:
        raise RuntimeError('source fixture unexpectedly mutated')
    print(json.dumps({'status':'QUALIFICATION_COMPLETED_NON_AUTHORITATIVE','inputs_unchanged':True,
          'input_sha256':before,'source_head':result['source_head_sha'],
          'disputed_claims':[k for k,v in result['derived_claims'].items() if v['state']=='CONTRADICTED'],
          'corrections':len(result['correction_events']),'authority_effect':'NONE',
          'output_dir':str(output)},sort_keys=True,indent=2))
    return 0


if __name__=='__main__':
    sys.exit(main())