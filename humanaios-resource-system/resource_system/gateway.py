"""Ephemeral vault; exact disclosure needs explicit scoped human authority."""
from datetime import datetime, timezone
from uuid import uuid4
from resource_system.contracts import validate

def require_authority(authorizations, resource_id, purpose, recipient, operation, now):
    if now.tzinfo is None:
        raise ValueError('timezone-aware time required')
    for auth in reversed(authorizations):
        validate('authorization', auth)
        if (auth['resource_id'], auth['purpose'], auth['recipient'], auth['operation']) == (resource_id, purpose, recipient, operation):
            if auth['state'] == 'GRANTED' and auth['human_authorized'] and datetime.fromisoformat(auth['expires_at'].replace('Z', '+00:00')) > now:
                return auth['id']
            break
    raise PermissionError('explicit current scoped human authorization required')

class ClaimGateway:
    def __init__(self):
        self._vault = {}

    def put(self, reference, raw_value):
        self._vault[reference] = raw_value

    def claim(self, claim_id, predicate, value, evidence_id):
        return validate('claim', {'schema_version': '1.0', 'id': claim_id, 'predicate': predicate,
                                 'value': value, 'evidence_id': evidence_id})

    def disclose(self, reference, resource_id, purpose, recipient, authorizations, store, now=None):
        now = now or datetime.now(timezone.utc)
        auth_id = require_authority(authorizations, resource_id, purpose, recipient, 'DISCLOSE', now)
        value = self._vault[reference]
        # Receipt is persisted before returning a sensitive value; never records it.
        store.append('activity', {'schema_version': '1.0', 'id': str(uuid4()), 'resource_id': resource_id,
                     'state': 'DISCLOSURE', 'actor': 'HUMAN', 'source_url': 'urn:local:vault',
                     'action_url': recipient, 'artifact_ids': [], 'outcome': 'UNKNOWN', 'material': False,
                     'purpose': purpose, 'authorization_id': auth_id, 'next_operation': 'CHECK_IN'})
        return value
