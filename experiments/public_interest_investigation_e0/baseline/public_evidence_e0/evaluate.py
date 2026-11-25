"""Separate deterministic scoring implementation; not an independent evaluator identity."""
import json,sys,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
key=json.loads((ROOT/'fixtures/provisional_key.json').read_text())
results=json.loads(pathlib.Path(sys.argv[1]).read_text())
expected=set(key['expected_ids']); report={}
for name in ('A','B','C'):
    a=results[name]; ids=set(a['candidate_ids']); correct=ids & expected
    report[name]={'targeted_records':len(correct),'false_positive_ids':sorted(ids-expected),'missed_ids':sorted(expected-ids),
                  'precision':len(correct)/len(ids) if ids else None,'recall':len(correct)/len(expected),
                  'duplicate_ids':len(a['candidate_ids'])-len(ids),
                  'required_state_correct':set(a['required_ids'])==set(key['expected_required']),
                  'conflict':a['conflict'],'exposure':a['exposure'],'authority_none':a['authority']==key['expected_authority']}
print(json.dumps({'scoring_status':'AUTHOR_KEY_SELF_CHECK_ONLY','results':report},indent=2))
