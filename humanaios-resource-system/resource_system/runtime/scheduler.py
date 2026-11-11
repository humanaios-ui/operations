"""Prototype v0.1 explicit tick; not a persistent scanner or monitor."""
from resource_system.controller.portfolio_sweep import sweep, affected_branches, routing_from_outcomes
from uuid import uuid4

def tick(resources, evidence, rules, today, frontier=(), exhausted=False, changed_evidence=None, logic_changed=False, activities=()):
    result = sweep(resources, evidence, rules, today, frontier, exhausted)
    result['rescan_ids'] = [r['id'] for r in resources] if logic_changed else affected_branches(changed_evidence, resources) if changed_evidence else []
    result['external_execution_enabled'] = False
    result['routing_adjustments'] = routing_from_outcomes(activities)
    result['priority_order'] = sorted(result['branches'], key=lambda rid: result['routing_adjustments'].get(rid, 0), reverse=True)
    return result

def attention(result):
    return [{'boundary': 'INFORMATION', 'predicate': predicate, 'resource_ids': ids}
            for predicate, ids in result['questions'].items()]

def execute_external(*args, **kwargs):
    raise PermissionError('external execution is disabled in this prototype')

class LocalRuntime:
    """Caller-driven local runner; issue #588's persistent service remains future work."""
    mode = 'EXPLICIT_TICK_LOCAL_ONLY'
    persistent = False
    external_execution_enabled = False

    def __init__(self, store):
        self.store = store

    def run(self, today, logic_changed=False):
        resources = list(self.store.latest('resource').values())
        evidence = list(self.store.latest('evidence').values())
        rules = {r['resource_id']: r for r in self.store.latest('trust_rule').values()}
        result = tick(resources, evidence, rules, today, logic_changed=logic_changed,
                      activities=list(self.store.latest('activity').values()))
        prior = self.store.latest('activity').values()
        matched = {a['resource_id'] for a in prior if a['state'] == 'MATCH'}
        for resource in resources:
            if result['branches'][resource['id']]['warrant'] and resource['id'] not in matched:
                self.store.append('activity', {'schema_version': '1.0', 'id': str(uuid4()),
                    'resource_id': resource['id'], 'state': 'MATCH', 'actor': 'AI',
                    'source_url': resource['source_url'], 'action_url': resource['action_url'],
                    'artifact_ids': [], 'outcome': 'UNKNOWN', 'material': False,
                    'purpose': 'VERIFY', 'authorization_id': None, 'next_operation': 'REQUEST_AUTHORITY'})
        return result
