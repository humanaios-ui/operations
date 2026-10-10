from copy import deepcopy
from datetime import datetime
from resource_system.contracts import validate
from resource_system.gateway import require_authority


def validate_artifact_traceability(record, resource, evidence, authorizations, now, prior=None):
    """Enforce the persisted-artifact traceability contract."""
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError('timezone-aware authorization time required')
    authority_id = require_authority(
        authorizations,
        record['resource_id'],
        'PREPARE',
        resource['action_url'],
        'ARTIFACT',
        now,
    )
    if authority_id != record['authorization_id']:
        raise ValueError('artifact authorization must match the selected current authority')
    snapshot = {node['id']: node for node in evidence if node['id'] in record['evidence_snapshot']}
    if len(snapshot) != len(record['evidence_snapshot']):
        raise ValueError('artifact snapshot evidence must be recorded')
    for claim in record['claims']:
        node = snapshot.get(claim['evidence_id'])
        if (
            not node
            or node['predicate'] != claim['predicate']
            or node['value'] != claim['value']
            or not node['value']
            or node['classification'] in {'CONTRADICTORY', 'DISQUALIFYING'}
        ):
            raise ValueError('artifact claim must trace to supporting snapshot evidence')
    if set(resource['requirements']) != {claim['predicate'] for claim in record['claims']}:
        raise ValueError('artifact must cover exact external requirements')
    if prior:
        old_requirements = {claim['predicate'] for claim in prior['claims']}
        new_requirements = set(resource['requirements'])
        if set(record['overlap']) != old_requirements & new_requirements or set(record['delta']) != old_requirements ^ new_requirements:
            raise ValueError('explicit overlap/delta mapping required')


def build_artifact(identifier, resource, branch, evidence, claims, authorizations, now, prior=None, overlap=None, delta=None):
    if not branch['warrant'] or branch['eligibility'] != 'VERIFIED':
        raise ValueError('verified warrant required')
    authority = require_authority(authorizations, resource['id'], 'PREPARE', resource['action_url'], 'ARTIFACT', now)
    snapshot = {node['id']: node for node in evidence if node['id'] in branch['evidence_snapshot']}
    artifact = {'schema_version': '1.0', 'id': identifier, 'resource_id': resource['id'],
                'evidence_snapshot': sorted(snapshot), 'authorization_id': authority,
                'state': 'UNDER_REVIEW', 'claims': deepcopy(claims), 'prior_artifact_id': prior['id'] if prior else None,
                'overlap': overlap or [], 'delta': delta or []}
    validate_artifact_traceability(artifact, resource, evidence, authorizations, now, prior)
    return validate('artifact', artifact)
