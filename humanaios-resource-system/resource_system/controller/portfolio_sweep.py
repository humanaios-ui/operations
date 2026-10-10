"""Pure replay: rule verification is an input, never inferred from relevance."""
from datetime import date
from resource_system.contracts import validate

CLASSES = {'LOCAL', 'GLOBAL', 'DISQUALIFYING', 'CONTRADICTORY', 'SUFFICIENT'}

def classify_evidence(evidence):
    classification = evidence['classification']
    if classification not in CLASSES:
        raise ValueError('unknown evidence classification')
    return classification

def sweep(resources, evidence, rules, today, frontier=(), exhausted=False):
    today = date.fromisoformat(today)
    facts = {}
    for node in evidence:
        validate('evidence', node)
        classify_evidence(node)
        facts.setdefault(node['predicate'], []).append(node)
    branches, questions = {}, {}
    for resource in resources:
        validate('resource', resource)
        missing, blocked, snapshot = [], False, []
        for predicate in resource['requirements']:
            nodes = [n for n in facts.get(predicate, []) if n['classification'] == 'GLOBAL' or resource['id'] in n['resource_ids']]
            snapshot.extend(n['id'] for n in nodes)
            if not nodes:
                missing.append(predicate)
                questions.setdefault(predicate, []).append(resource['id'])
            elif len({n['value'] for n in nodes}) > 1 or any(n['classification'] in {'DISQUALIFYING', 'CONTRADICTORY'} or not n['value'] for n in nodes):
                blocked = True
        rule = rules.get(resource['id'])
        if rule:
            validate('trust_rule', rule)
        current = bool(rule and rule['resource_id'] == resource['id'] and rule['authoritative'] and
                       date.fromisoformat(rule['verified_on']) <= today <= date.fromisoformat(rule['valid_until']) and
                       set(rule['predicates']) == set(resource['requirements']))
        status = 'BLOCKED' if blocked else 'VERIFIED' if current and not missing else 'UNASSESSED'
        branches[resource['id']] = {'eligibility': status, 'warrant': status == 'VERIFIED',
                                    'missing': missing, 'evidence_snapshot': sorted(snapshot), 'authority_effect': 'NONE'}
    return {'branches': branches, 'questions': questions,
            'scan_queue': list(frontier[:1]) if exhausted else [], 'scan_executed': False}

def affected_branches(node, resources):
    classify_evidence(node)
    if not node['material']:
        return []
    return [r['id'] for r in resources if node['predicate'] in r['requirements'] and
            (node['classification'] == 'GLOBAL' or r['id'] in node['resource_ids'])]

def convergence(actions, branches):
    """Raise priority only for actions yielding multiple verified resource types."""
    return sorted(actions, key=lambda a: len({t for rid, types in a['yields'].items()
                  if branches.get(rid, {}).get('eligibility') == 'VERIFIED' for t in types}), reverse=True)

def routing_from_outcomes(activities):
    scores = {}
    for activity in activities:
        validate('activity', activity)
        if activity['state'] == 'OUTCOME' and activity['material'] and activity['outcome'] in {'SUCCESS', 'FAILURE'}:
            scores[activity['resource_id']] = scores.get(activity['resource_id'], 0) + (1 if activity['outcome'] == 'SUCCESS' else -1)
    return scores
