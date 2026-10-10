from copy import deepcopy
from datetime import datetime
from resource_system.contracts import validate
from resource_system.gateway import require_authority


def _applicable_evidence(resource, evidence):
    """Return every recorded fact that can affect this resource's requirements."""
    requirements = set(resource['requirements'])
    applicable = {}
    for node in evidence:
        if node['predicate'] not in requirements:
            continue
        if node['classification'] != 'GLOBAL' and resource['id'] not in node['resource_ids']:
            continue
        if node['id'] in applicable:
            raise ValueError('duplicate applicable evidence ID')
        applicable[node['id']] = node
    return applicable


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
    applicable = _applicable_evidence(resource, evidence)
    snapshot_ids = set(record['evidence_snapshot'])
    if snapshot_ids != set(applicable):
        raise ValueError('artifact must snapshot all applicable evidence for current requirements')
    blocked = [
        node for node in applicable.values()
        if not node['value'] or node['classification'] in {'CONTRADICTORY', 'DISQUALIFYING'}
    ]
    if blocked:
        raise ValueError('artifact cannot omit or override contradictory, disqualifying, or false evidence')
    snapshot = applicable
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
        if record['prior_artifact_id'] != prior['id']:
            raise ValueError('prior artifact identifier mismatch')
        if prior['resource_id'] != resource['id'] or prior['resource_id'] != record['resource_id']:
            raise ValueError('prior artifact must belong to the same resource')
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
