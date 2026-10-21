"""Single-writer append ledger. Vault values never enter this store."""
import json
from copy import deepcopy
from pathlib import Path
from resource_system.artifacts import validate_artifact_traceability
from resource_system.contracts import validate

KINDS = {'resource', 'resource_value', 'evidence', 'claim', 'activity', 'artifact', 'authorization', 'trust_rule'}

class StateStore:
    def __init__(self, path):
        self.path = Path(path)

    def events(self):
        if not self.path.exists():
            return []
        records = [json.loads(line) for line in self.path.read_text().splitlines()]
        for sequence, event in enumerate(records, 1):
            if set(event) != {'sequence', 'kind', 'record'} or event['sequence'] != sequence or event['kind'] not in KINDS:
                raise ValueError('invalid ledger envelope')
            validate(event['kind'], event['record'])
        return records

    def append(self, kind, record, now=None):
        if kind not in KINDS:
            raise ValueError('unsupported ledger kind')
        validate(kind, record)
        events = self.events()
        if kind not in {'resource', 'resource_value'} and any(e['kind'] == kind and e['record']['id'] == record['id'] for e in events):
            raise ValueError('immutable record ID already exists')
        if kind == 'artifact':
            resources = {
                event['record']['id']: event['record']
                for event in events
                if event['kind'] == 'resource'
            }
            resource = resources.get(record['resource_id'])
            if not resource:
                raise ValueError('artifact resource must be recorded')
            evidence = [event['record'] for event in events if event['kind'] == 'evidence']
            authorizations = [event['record'] for event in events if event['kind'] == 'authorization']
            artifacts = {
                event['record']['id']: event['record']
                for event in events
                if event['kind'] == 'artifact'
            }
            prior = artifacts.get(record['prior_artifact_id']) if record['prior_artifact_id'] else None
            if record['prior_artifact_id'] and not prior:
                raise ValueError('prior artifact must be recorded')
            validate_artifact_traceability(
                record,
                resource,
                evidence,
                authorizations,
                now,
                prior,
            )
        event = {'sequence': len(events) + 1, 'kind': kind, 'record': deepcopy(record)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + '\n')
        return event

    def latest(self, kind):
        """Resource/value snapshots may evolve; prior events remain intact."""
        return {event['record']['id']: event['record'] for event in self.events() if event['kind'] == kind}
