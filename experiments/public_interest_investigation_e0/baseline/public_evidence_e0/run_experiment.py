"""Retrospective, non-independent three-arm replay; all arms use same frozen notes."""
import json, pathlib
from resource_miner.public_evidence import discover, load_frozen, to_planning_requirements
ROOT=pathlib.Path(__file__).resolve().parent

def run():
    blob=(ROOT/'fixtures/case.json').read_bytes(); sha=(ROOT/'fixtures/case.sha256').read_text().strip()
    case=load_frozen(blob,sha)
    # A: human-readable conventional research replay. Explicit author-coded result,
    # not a blinded investigator or an independent replicate. Give A credit for all
    # nine named records visible in the same input rather than handicap it.
    a={'candidate_ids':['ER-001','ER-002','ER-003','ER-004','ER-005','ER-006','ER-007','ER-008','ER-009'],
       'required_ids':['ER-009'],'conflict':'UNRESOLVED','exposure':'UNKNOWN','authority':'NONE',
       'method':'author-coded conventional reconstruction from frozen notes; not a separate agent'}
    mined=discover(blob,sha)
    b={'candidate_ids':[r['id'] for r in mined['candidates']],
       'required_ids':[r['id'] for r in mined['candidates'] if r['state']=='REQUIRED'],
       'conflict':'NOT_EVALUATED','exposure':'NOT_EVALUATED','authority':mined['authority_effect'],
       'method':'executed bounded adapter on manually annotated frozen notes'}
    # C: explicit human-authored Witness-style disposition. Not existing Witness code.
    c={**b,'conflict':'UNRESOLVED','exposure':'UNKNOWN',
       'method':'executed adapter plus author-authored Witness-style challenge; no independent runtime',
       'challenge_sources':['ARMY','IPR'],'verification_tasks':['Obtain public or lawfully releasable decision records','Compare agency rationale with underlying records','Obtain validated environmental results and independent scientific review'],
       'planning_requirements':to_planning_requirements(mined)}
    return {'input_sha256':sha,'as_of':case['as_of'],'A':a,'B':b,'C':c,'adapter_receipt':mined,'independence':'NONE','production':'HOLD'}

if __name__=='__main__': print(json.dumps(run(),indent=2,ensure_ascii=False))
