"""Acquired restricted value is neither cash nor realized gain."""
from datetime import date
from resource_system.contracts import validate

class Inventory:
    def __init__(self, resource, value):
        validate('resource', resource)
        validate('resource_value', value)
        if resource['state'] != 'ACQUIRED' or value['resource_id'] != resource['id']:
            raise ValueError('acquisition receipt and matching value required')
        self.resource, self.value = resource.copy(), value.copy()
        self.allocations, self.consumed, self.gains = {}, 0, []

    def allocate(self, workload, amount, today):
        if date.fromisoformat(today) >= date.fromisoformat(self.value['expires_on']):
            raise ValueError('resource expired')
        if workload not in self.value['allowed_workloads'] or amount <= 0 or sum(self.allocations.values()) + self.consumed + amount > self.value['usable_value']:
            raise ValueError('invalid or excessive allocation')
        self.allocations[workload] = self.allocations.get(workload, 0) + amount

    def consume(self, workload, amount, today):
        if date.fromisoformat(today) >= date.fromisoformat(self.value['expires_on']) or amount <= 0 or amount > self.allocations.get(workload, 0):
            raise ValueError('invalid consumption')
        self.allocations[workload] -= amount
        self.consumed += amount

    def conversion(self, target_resource, realized_value, observation):
        validate('evidence', observation)
        evidence_id = observation['id']
        if not observation['value'] or observation['classification'] in {'DISQUALIFYING', 'CONTRADICTORY'} or target_resource not in observation['resource_ids']:
            raise ValueError('supporting downstream observation required')
        if self.consumed <= 0 or realized_value < 0 or not evidence_id or target_resource == self.resource['id']:
            raise ValueError('observed downstream evidence required')
        if any(g['evidence_id'] == evidence_id for g in self.gains):
            raise ValueError('conversion evidence already recorded')
        edge = {'source': self.resource['id'], 'target': target_resource, 'evidence_id': evidence_id, 'realized_value': realized_value}
        self.gains.append(edge)
        self.value['realized_value'] += realized_value
        return edge

    def lifecycle(self, today):
        return 'EXPIRED' if date.fromisoformat(today) >= date.fromisoformat(self.value['expires_on']) else 'ACTIVE'
