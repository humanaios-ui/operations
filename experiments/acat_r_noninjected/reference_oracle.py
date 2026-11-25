"""Independent, specification-derived On-Track classification oracle.

Does not import, inspect, or call On-Track runtime or its helpers.
Reference spec: objective #822, observer #928 are the only fixed anchors;
only leading explicit markers are declarations; claims are not outcomes.
The snapshot is a selected, privacy-minimized GitHub observation, not an
authenticated snapshot of a complete issue inventory.
"""
from __future__ import annotations

import re

TARGET = "INTENT_OS_RESOURCE_MINER_USABLE"
ANCHORS = {822, 928}
BLOCKERS = {"blocked", "needs-human", "needs_human", "on-hold"}
MARK = re.compile(r"^\s*on_track_target:\s*([A-Z0-9_]+)\s*$")


def predict(item: dict) -> dict:
    num = item['number']
    labels = sorted({l['name'].lower() for l in item['labels']})
    lines = str(item['body']).splitlines()
    first = next((line for line in lines if line.strip()), '')
    declarations = [m.group(1) for line in lines if (m := MARK.fullmatch(line))]
    # The benchmark's held-out label comes from documented invariant, not DUT output.
    mapping = ('DECLARED_ANCHOR' if num in ANCHORS else
               'DECLARED_BY_AUTHOR' if declarations == [TARGET] and MARK.fullmatch(first) else
               'UNMAPPED')
    blockers = sorted(BLOCKERS.intersection(labels))
    landing = 'AT_RISK' if mapping != 'UNMAPPED' and blockers else 'UNVERIFIED'
    kind = 'PULL_REQUEST' if 'pull_request' in item else 'ISSUE'
    if mapping == 'UNMAPPED':
        next_action = 'Ask owner to declare a supported goal mapping, or leave unrelated.'
    elif blockers:
        next_action = 'Resolve the named blocker; obtain independent evidence.'
    elif num == 822:
        next_action = 'Verify deployed /intent-os and a human objective-to-resource outcome.'
    elif kind == 'PULL_REQUEST':
        next_action = 'Verify exact-head tests, then observe user-visible behavior.'
    else:
        next_action = 'Identify an implemented change and its exact verification receipt.'
    return {
        'ref':f'humanaios-ui/operations#{num}',
        'goal_mapping':mapping,
        'goal_id':TARGET if mapping!='UNMAPPED' else None,
        'landing_state':landing,
        'blocker_labels':blockers,
        'github_state':item['state'],
        'kind':kind,
        'next_action':next_action,
        'exact_head_ci':'UNVERIFIED',
        'operator_outcome':'UNVERIFIED',
        'authority_effect':'NONE',
        'implementation':'PR_EXISTS_NOT_VERIFIED' if kind=='PULL_REQUEST' else 'ISSUE_EXISTS_NOT_VERIFIED',
    }


def compare(items: list[dict], report: dict) -> dict:
    expected = {f'humanaios-ui/operations#{q["number"]}': predict(q) for q in items}
    actual = {q['ref']:q for q in report['items']}
    diffs = []
    if len(expected)!=len(items) or set(actual)!=set(expected):
        diffs.append({'error':'missing/duplicate/unknown references'})
    for ref, fields in expected.items():
        got = actual.get(ref)
        if got is None:
            continue
        for key, want in fields.items():
            if got.get(key)!=want:
                diffs.append({'ref':ref,'field':key,'expected':want,'actual':got.get(key)})
    mapped = sum(q['goal_mapping']!='UNMAPPED' for q in expected.values())
    counts = {'mapped_declarations':mapped,'unmapped':len(expected)-mapped,
              'at_risk_mapped':sum(q['landing_state']=='AT_RISK' for q in expected.values()),
              'verified_user_outcomes':0}
    if report.get('counts') != counts:
        diffs.append({'error':'wrong aggregate counts','expected':counts,'actual':report.get('counts')})
    expected_order=sorted(expected,key=lambda ref:(expected[ref]['goal_mapping']=='UNMAPPED',-int(ref.split('#')[-1])))
    if list(actual)!=expected_order:
        diffs.append({'error':'noncanonical sort order'})
    for name,want in [('overall','UNVERIFIED'),('authority_effect','NONE'),('merge_authority',False),('deployment_authority',False)]:
        if report.get(name)!=want:
            diffs.append({'error':f'forbidden {name}={report.get(name)}'})
    if report.get('scope',{}).get('items_examined')!=len(items):
        diffs.append({'error':'wrong examined item count'})
    if report.get('scope',{}).get('complete_open_work_inventory') is not False:
        diffs.append({'error':'overstated inventory completeness'})
    return {'case_count':len(items),'reference_agreement':len(diffs)==0,
            'comparison_field_checks':len(expected[next(iter(expected))])*len(items) if expected else 0,
            'differences':diffs,'expected_counts':counts}
