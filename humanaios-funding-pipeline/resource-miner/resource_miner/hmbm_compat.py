"""HMBM URA passive compatibility projection. No execution."""

from datetime import datetime


def project(observation, cutoff, frozen_assets):
    if observation['asset_id'] not in frozen_assets:
        raise ValueError('non-frozen asset')
    if observation.get('authorization_effect') != 'NONE':
        raise ValueError('authority denied')
    cutoff_time = datetime.fromisoformat(cutoff.replace('Z', '+00:00'))
    available_time = datetime.fromisoformat(observation['available_at'].replace('Z', '+00:00'))
    valid = bool(observation.get('availability_proof')) and available_time <= cutoff_time
    return {'evaluation_state': 'ELIGIBLE_FOR_HMBM_EVALUATION' if valid else 'MISSING_DATA', 'authorization_effect': 'NONE', 'dhp_state_effect': 'NONE'}
