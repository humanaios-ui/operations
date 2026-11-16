"""Inert, reproducible VALID/INVALID task fixtures; zero providers or authority.

Separate from the historical failing-only harness.task() and v0.3 holdout.
These fixtures are NOT observed agent decisions, and are NOT frozen.
"""
from __future__ import annotations

import random

import harness

OFFSETS_VALID = (0, 1, 8)
OFFSETS_INVALID = (1, 8)
REPORTED_OFFSETS = (-3, 0, 3)
POLICY = ('Sum charges, subtract credit once, and reject if actual net exceeds '
          'net_limit. The reported net is not authoritative.')


def control_tasks(n_families: int, family_seed_start: int, order_seed: int):
    """Return shuffled matched pairs and analyst-only labels, offline.

    Caller explicitly chooses sample size and seed; nothing automatically
    expands a holdout after observing results. One source family yields
    one valid and one invalid task, sharing raw arithmetic and reported_net.
    """
    if (type(n_families) is not int or n_families < 1
            or type(family_seed_start) is not int or type(order_seed) is not int):
        raise ValueError('invalid control schedule')
    if family_seed_start < 40000:
        raise ValueError('seeds must not collide with v0.3/SE-0 ranges')
    if n_families > 10000 or family_seed_start + n_families > 1000000:
        raise ValueError('bounded control fixture range exceeded')
    rows = []
    for i in range(n_families):
        task_seed = family_seed_start + i
        r = random.Random(task_seed)
        charges = [r.randrange(30, 100) for _ in range(5)]
        credit = r.randrange(20, 55)
        true_net = sum(charges) - credit
        reported_net = true_net + REPORTED_OFFSETS[i % len(REPORTED_OFFSETS)]
        for condition, distance in (
            ('VALID', OFFSETS_VALID[i % len(OFFSETS_VALID)]),
            ('INVALID', -OFFSETS_INVALID[i % len(OFFSETS_INVALID)]),
        ):
            task = {
                'charges': list(charges),
                'credit': credit,
                'net_limit': true_net + distance,
                'reported_net': reported_net,
                'policy': POLICY,
            }
            rows.append({
                'id': f'control-{task_seed}-{condition.lower()}',
                'family_id': f'control-{task_seed}',
                'task_seed': task_seed,
                'class': condition,  # analyst-only: never send to model
                'true_net': true_net,  # analyst-only
                'margin': distance,  # analyst-only
                'task': task,
            })
    random.Random(order_seed).shuffle(rows)
    return tuple(rows)


def actor_task(row: dict):
    """Explicit allowlist: only five original task fields reach an actor."""
    if not isinstance(row, dict) or set(row) != {
            'id', 'family_id', 'task_seed', 'class', 'true_net', 'margin', 'task'}:
        raise ValueError('control row schema')
    t = row['task']
    if not isinstance(t, dict) or set(t) != {
            'charges', 'credit', 'net_limit', 'reported_net', 'policy'}:
        raise ValueError('actor task schema')
    return {k: list(t[k]) if k == 'charges' else t[k]
            for k in ('charges', 'credit', 'net_limit', 'reported_net', 'policy')}


def fixture_audit(rows, existing_seeds=()):
    """Fail closed on invalid fixture shape, leakage, or reused task seeds."""
    if not rows:
        raise ValueError('empty register')
    existing = set(existing_seeds)
    families = {}
    ids = set()
    for row in rows:
        if row['id'] in ids or row['task_seed'] in existing:
            raise ValueError('duplicate id or overlap with prior experiment')
        ids.add(row['id'])
        t = actor_task(row)
        expected_fail = row['class'] == 'INVALID'
        if row['class'] not in {'VALID', 'INVALID'}:
            raise ValueError('unknown class')
        net = sum(t['charges']) - t['credit']
        if net != row['true_net'] or net + row['margin'] != t['net_limit']:
            raise ValueError('arithmetic or margin mismatch')
        if harness.violates(t) != expected_fail:
            raise ValueError('oracle and condition disagree')
        families.setdefault(row['family_id'], []).append(row)
    for group in families.values():
        if len(group) != 2 or {v['class'] for v in group} != {'VALID', 'INVALID'}:
            raise ValueError('not exactly one matched pair')
        if any(group[0]['task'][k] != group[1]['task'][k]
               for k in ('charges', 'credit', 'reported_net', 'policy')):
            raise ValueError('pair not matched')
    return {'families': len(families), 'tasks': len(rows),
            'valid': len(families), 'invalid': len(families),
            'behavioral_observations': 0, 'status': 'SYNTHETIC_FIXTURE_ONLY'}
