"""Offline SE-0 dry run with a deterministic stub agent.

No network, no model, no spend. The stub is not an experimental subject.
Records are SYNTHETIC_FIXTURE only. The written artifact is not experimental
data and it is not a freeze.

The failing-task generator is called as-is. This file does not change
task() or schedule().
"""
from __future__ import annotations

import json
from pathlib import Path

from harness import (
    SE0_ARMS, host_no_exchange_receipt, schedule, shared_error_tiers, task,
    validate_record,
)

# Plumbing size only. Not a proposed sample and not authorized spend.
DRY_RUN_SEED = 20261116
DRY_RUN_N = 4
EVIDENCE_CLASS = 'SYNTHETIC_STUB_NOT_EXPERIMENTAL_DATA'
OUTPUT_NAME = 'se0_stub_dry_run_output.json'


def _true_net(item):
    total = 0
    for charge in item['charges']:
        total += charge
    return total - item['credit']


def stub_private(item, actor, hint, slot):
    """One actor, one call. The other actor is not an argument that changes the net.

    Even slots approve a failing task with a shared wrong net. Odd slots reject
    with a net that matches the rows (SE-0a) or the reported figure (SE-0b).
    """
    if not isinstance(actor, str) or actor not in ('A', 'B'):
        raise ValueError('actor')
    if type(slot) is not int or slot < 0:
        raise ValueError('slot')
    true_net = _true_net(item)
    if slot % 2 == 0:
        computed = item['reported_net'] - 8 if hint else item['net_limit']
        rule = 'shared-wrong-net'
    else:
        computed = item['reported_net'] if hint else true_net
        rule = 'rows'
    if type(computed) is not int:
        raise ValueError('stub net')
    vote = 'APPROVE' if computed <= item['net_limit'] else 'REJECT'
    return {
        'vote': vote,
        'computed_net': computed,
        'rationale': f'stub:{actor}:{rule}',
    }


def run_dry(se0_seed=DRY_RUN_SEED, se0_n=DRY_RUN_N):
    """Schedule SE-0, run two stub calls per actor, validate, score tiers."""
    episodes = [ep for ep in schedule(include_se0=True, se0_seed=se0_seed, se0_n=se0_n)
                if ep['arm'] in SE0_ARMS]
    rows = []
    for host_counter, episode in enumerate(episodes):
        item = task(episode['task_seed'])
        slot = int(episode['id'].rsplit('-', 1)[-1])
        private_a = stub_private(item, 'A', episode['hint'], slot)
        private_b = stub_private(item, 'B', episode['hint'], slot)
        final_a = stub_private(item, 'A', episode['hint'], slot)
        final_b = stub_private(item, 'B', episode['hint'], slot)
        record = {
            'episode_id': episode['id'],
            'arm': episode['arm'],
            'task': item,
            'private_votes': {'A': private_a, 'B': private_b},
            'messages': {'A': '', 'B': ''},
            'final_votes': {'A': final_a['vote'], 'B': final_b['vote']},
            'transport': {'A': 'NOT_RUN', 'B': 'NOT_RUN', 'judge': 'NOT_RUN'},
            'observed_source': 'SYNTHETIC_FIXTURE',
            'no_exchange': host_no_exchange_receipt(episode['id'], host_counter),
        }
        validate_record(record)
        tiers = shared_error_tiers(record)
        rows.append({
            'arm': episode['arm'],
            'channel': record['no_exchange']['channel'],
            'computed_net_a': private_a['computed_net'],
            'computed_net_b': private_b['computed_net'],
            'hint': episode['hint'],
            'host_counter': host_counter,
            'id': episode['id'],
            'open_count': record['no_exchange']['open_count'],
            'receipt_sha256': record['no_exchange']['host_sha256'],
            'task_seed': episode['task_seed'],
            'tier1_shared_wrong_decision': tiers['tier1_shared_wrong_decision'],
            'tier2_shared_wrong_answer': tiers['tier2_shared_wrong_answer'],
            'vote_a': private_a['vote'],
            'vote_b': private_b['vote'],
        })
    by_arm = {}
    for arm in SE0_ARMS:
        arm_rows = [row for row in rows if row['arm'] == arm]
        by_arm[arm] = {
            'n': len(arm_rows),
            'tier1': sum(1 for row in arm_rows if row['tier1_shared_wrong_decision']),
            'tier2': sum(1 for row in arm_rows if row['tier2_shared_wrong_answer']),
        }
    return {
        'by_arm': by_arm,
        'episodes': len(rows),
        'evidence_class': EVIDENCE_CLASS,
        'model_calls': 0,
        'network': False,
        'note': (
            'Deterministic stub agent. Not a model. Not observations. '
            'Not experimental data. Not a freeze.'
        ),
        'observed_source': 'SYNTHETIC_FIXTURE',
        'rows': rows,
        'se0_n_per_arm': se0_n,
        'se0_seed': se0_seed,
        'tier1_total': sum(1 for row in rows if row['tier1_shared_wrong_decision']),
        'tier2_total': sum(1 for row in rows if row['tier2_shared_wrong_answer']),
    }


def render_output(summary=None):
    if summary is None:
        summary = run_dry()
    return json.dumps(summary, indent=2, sort_keys=True) + '\n'


def main():
    path = Path(__file__).resolve().with_name(OUTPUT_NAME)
    path.write_text(render_output())
    return path


if __name__ == '__main__':
    print(main())
