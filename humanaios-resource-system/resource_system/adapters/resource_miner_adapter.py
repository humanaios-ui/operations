"""Compose the existing handoff, carrying only selected claim-safe fields."""
import importlib.util
from pathlib import Path

def load_handoff_module(relative):
    path = Path(__file__).resolve().parents[3] / 'humanaios-funding-pipeline' / relative
    spec = importlib.util.spec_from_file_location('handoff_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def ingest(candidate):
    handoff = load_handoff_module('resource-miner/resource_miner/entitlement_handoff.py').build_entitlement_handoff(candidate)
    resource = handoff['resource']
    return {'schema_version': '1.0', 'id': resource['resource_id'],
            'source_url': resource['primary_source_url'] or resource['source_url'] or resource['canonical_url'],
            'eligibility': 'UNASSESSED', 'state': 'DISCOVERED',
            'resource_types': resource['resource_types'], 'requirements': [],
            'action_url': resource['canonical_url'], 'source_handoff_id': handoff['handoff_id']}
