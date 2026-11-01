"""Advisory governance invariant evaluator. No admission or ratification capability.

Builder v1.7 compliant
HumanAIOS
"""
import argparse, hashlib, json, pathlib, re
TOOL_NAME = 'governance_invariant_evaluator'
TOOL_VERSION = '1.0.0'
TOOL_CATEGORY = 'audit_tool'
SHA=re.compile(r'[0-9a-f]{40}\Z')
REQUIRED=('GOVERNANCE_FILES.md','SESSION_RITUALS.md','BOOT_PROCESS_MAP.md','REGISTRY_SPEC.md','REPOSITORY_COORDINATOR_POLICY.json')
def normalize(path):
    if not isinstance(path,str) or not path or '\\' in path or '\x00' in path: raise ValueError('invalid path')
    parts=path.split('/')
    if path.startswith('/') or any(p in ('','..') for p in parts): raise ValueError('unsafe path')
    return '/'.join(p for p in parts if p!='.')
def evaluate(snapshot,root):
    reasons=[]
    if snapshot.get('schema')!='humanaios.governance-evaluation-input.v1': reasons.append('INVALID_INPUT_SCHEMA')
    head,base=snapshot.get('head_sha'),snapshot.get('base_sha')
    if not isinstance(head,str) or not SHA.fullmatch(head): reasons.append('UNPINNED_HEAD')
    if not isinstance(base,str) or not SHA.fullmatch(base): reasons.append('UNPINNED_BASE')
    if snapshot.get('diff_head_sha')!=head or snapshot.get('diff_base_sha')!=base: reasons.append('DIFF_PIN_MISMATCH')
    if snapshot.get('source')!='protected_checkout': reasons.append('UNTRUSTED_EVIDENCE_SOURCE')
    pins=snapshot.get('governance_pins',{})
    if not isinstance(pins,dict): pins={}
    for path in (*REQUIRED,'.gov-control/governance-files.yaml'):
        expected=pins.get(path);file=root/path
        if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected) or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected: reasons.append('PIN_MISMATCH:'+path)
    files=snapshot.get('changed_files')
    if not isinstance(files,list) or not files: reasons.append('MISSING_DIFF_FILES');files=[]
    try: changed={normalize(p) for p in files}
    except (TypeError,ValueError): changed=set();reasons.append('UNSAFE_CHANGED_PATH')
    if snapshot.get('claimed_authority','Z1')!='Z1' or snapshot.get('can_authorize') is not False or snapshot.get('authority_effect')!='NONE': reasons.append('AUTHORITY_ELEVATION_CLAIM')
    manifest=root/'.gov-control/governance-files.yaml'
    registry=manifest.read_text() if manifest.is_file() else ''
    protected=set(re.findall(r'^\s*- path:\s*["\']?([^\s"\']+)',registry,re.M));protected.update(REQUIRED);protected.add('.gov-control/governance-files.yaml')
    touched=sorted(changed & protected)
    if touched: reasons.append('RATIFICATION_REQUIRED:'+','.join(touched))
    events=[('A1','REGISTERED.md'),('A2','ZONE_REGISTRY.md'),('A3','REGISTERED.md'),('A4','PRIORITY_QUEUE.md'),('A5','MOLT_STATE.md'),('A6','BOOT_PROCESS_MAP.md'),('B6','ledgers/NF_LEDGER.jsonl'),('B6b','ledgers/NF_LEDGER.jsonl'),('B7','z1-inbox/'),('B8','PRIORITY_QUEUE.md')]
    if snapshot.get('proposed_boot_edges'): reasons.append('BOOT_ORDER_CHANGE_REQUIRES_SEPARATE_RATIFICATION')
    return dict(schema='humanaios.governance-invariant-evaluation.v1',head_sha=head,base_sha=base,status='PASS' if not reasons else 'FAIL',reasons=sorted(set(reasons)),event_nodes=[dict(id=i,target=p) for i,p in events],advisory_only=True,authenticated=False,can_authorize=False,authority_effect='NONE',admitted=False)
def run_smoke_test():
    """Exercise pinned evidence and manifest ratification using an isolated checkout."""
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        root=pathlib.Path(directory)
        pins={}
        for path in (*REQUIRED,'.gov-control/governance-files.yaml'):
            file=root/path
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text('- path: REGISTERED.md\n',encoding='utf-8')
            pins[path]=hashlib.sha256(file.read_bytes()).hexdigest()
        snapshot=dict(schema='humanaios.governance-evaluation-input.v1',
                      head_sha='a'*40,base_sha='b'*40,diff_head_sha='a'*40,diff_base_sha='b'*40,
                      source='protected_checkout',governance_pins=pins,changed_files=['tools/harmless.py'],
                      claimed_authority='Z1',can_authorize=False,authority_effect='NONE')
        valid=evaluate(snapshot,root)
        snapshot['changed_files']=['.gov-control/governance-files.yaml']
        protected=evaluate(snapshot,root)
        return (valid['status']=='PASS' and valid['reasons']==[]
                and protected['status']=='FAIL'
                and protected['reasons']==['RATIFICATION_REQUIRED:.gov-control/governance-files.yaml']
                and all(r['advisory_only'] is True and r['authenticated'] is False
                        and r['can_authorize'] is False and r['authority_effect']=='NONE'
                        and r['admitted'] is False for r in (valid,protected)))
def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--root',default='.')
    a=p.parse_args();r=evaluate(json.loads(pathlib.Path(a.snapshot).read_text()),pathlib.Path(a.root));print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(0 if r['status']=='PASS' else 1)
if __name__=='__main__':main()
