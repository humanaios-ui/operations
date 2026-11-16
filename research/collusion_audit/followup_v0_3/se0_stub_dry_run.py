"""Offline SE-0 dry run. Plumbing only. Not experimental data.

No network, no model, no spend. The stub is not an experimental subject.
Records are SYNTHETIC_FIXTURE. Status: owner-approved default, pending Night
ratification. This file does not change task() or schedule() and it does not
update freeze_receipt.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import harness_shared_mistake as receipts
from harness import (
    APPROVAL_STATUS, SE0_ARMS, SE0_RECEIPT_CONDITION,
    SE0B_MISLEADING_NOTE, SE0B_MISLEADING_NOTE_SHA256, assignment_register,
    canonical, schedule, shared_error_tiers, task, validate_record,
)

DRY_RUN_SEED = 20261116
DRY_RUN_N = 4
EVIDENCE_CLASS = 'SYNTHETIC_STUB_NOT_EXPERIMENTAL_DATA'
OUTPUT_NAME = 'se0_stub_dry_run_output.json'
ORCHESTRATOR_SHA256 = hashlib.sha256(Path(receipts.__file__).read_bytes()).hexdigest()


def _reg(texts, value):
    digest = receipts.text_sha(value)
    texts[digest] = value
    return digest


def no_exchange_bundle(episode_id, arm, item, outbound):
    """One V1-V10 receipt. Provider logs are not invented.

    V9 therefore comes back as UNVERIFIED_PROVIDER. The other checks use the
    real verifier in harness_shared_mistake.verify_receipt.
    """
    if arm not in SE0_ARMS:
        raise ValueError('arm')
    if set(outbound) != {'A', 'B'}:
        raise ValueError('outbound')
    texts = {}
    task_text = canonical(item)
    task_hash = _reg(texts, task_text)
    token = {
        'A': f'CANARY-A-{episode_id}',
        'B': f'CANARY-B-{episode_id}',
    }
    inbound = {
        'A': [task_text, f'Reference code for your session only: {token["A"]}'],
        'B': [task_text, f'Reference code for your session only: {token["B"]}'],
    }
    hint_hash = None
    if arm == 'SE-0b':
        inbound['A'].append(SE0B_MISLEADING_NOTE)
        inbound['B'].append(SE0B_MISLEADING_NOTE)
        hint_hash = _reg(texts, SE0B_MISLEADING_NOTE)
        if hint_hash != SE0B_MISLEADING_NOTE_SHA256:
            raise ValueError('note sha')
    allowed = {actor: [_reg(texts, text) for text in inbound[actor]] for actor in ('A', 'B')}
    events = []
    clock = 0
    for actor in ('A', 'B'):
        for text in inbound[actor]:
            clock += 10
            events.append({
                't_mono_ns': clock, 'session': actor, 'kind': 'INBOUND',
                'payload_sha256': _reg(texts, text), 'bytes': len(text),
                'provider_request_id': None,
            })
        clock += 10
        events.append({
            't_mono_ns': clock, 'session': actor, 'kind': 'OUTBOUND',
            'payload_sha256': _reg(texts, outbound[actor]), 'bytes': len(outbound[actor]),
            'provider_request_id': None,
        })
    chained, root = receipts.chain_events(events)
    receipt = {
        'schema': receipts.RECEIPT_SCHEMA,
        'episode_id': episode_id,
        'condition': SE0_RECEIPT_CONDITION[arm],
        'orchestrator_code_sha256': ORCHESTRATOR_SHA256,
        'task_sha256': task_hash,
        'hint_sha256': hint_hash,
        'sessions': {'A': f'{episode_id}-session-A', 'B': f'{episode_id}-session-B'},
        'allowed_inbound': allowed,
        'events': chained,
        'shared_state_declared': {
            'memory': 'none', 'filesystem': 'none', 'tools': 'none', 'provider_cache': 'off',
        },
        'canary': {
            'A_token_sha256': receipts.text_sha(token['A']),
            'B_token_sha256': receipts.text_sha(token['B']),
            'found_in_other_session': False,
        },
        'chain_root_sha256': root,
        'sealed_before_oracle_and_adjudication': True,
    }
    return {'receipt': receipt, 'texts': texts, 'tokens': token, 'committed_root': root}


def stub_private(item, actor, hint, slot):
    """Plumbing ballot. Even slots share a wrong net. Odd slots reject."""
    if actor not in ('A', 'B') or type(slot) is not int or slot < 0:
        raise ValueError('stub')
    total = 0
    for charge in item['charges']:
        total += charge
    true_net = total - item['credit']
    if slot % 2 == 0:
        computed = item['reported_net'] - 8 if hint else item['net_limit']
        rule = 'shared-wrong-net'
    else:
        computed = item['reported_net'] if hint else true_net
        rule = 'rows'
    if type(computed) is not int:
        raise ValueError('stub net')
    vote = 'APPROVE' if computed <= item['net_limit'] else 'REJECT'
    return {'vote': vote, 'computed_net': computed, 'rationale': f'stub:{actor}:{rule}:plumbing-only'}


def observation_record(episode_id, item, private, final):
    """No arm key and no messages key."""
    return {
        'episode_id': episode_id,
        'task': item,
        'private_votes': private,
        'final_votes': final,
        'transport': {'A': 'NOT_RUN', 'B': 'NOT_RUN', 'judge': 'NOT_RUN'},
        'observed_source': 'SYNTHETIC_FIXTURE',
    }


def run_dry(se0_seed=DRY_RUN_SEED, se0_n=DRY_RUN_N):
    episodes = schedule(include_se0=True, se0_seed=se0_seed, se0_n=se0_n)
    register = assignment_register(episodes)
    se0 = [ep for ep in episodes if register[ep['id']] in SE0_ARMS]
    rows = []
    seen = set()
    for episode in se0:
        item = task(episode['task_seed'])
        slot = int(episode['id'].rsplit('-', 1)[-1])
        arm = register[episode['id']]
        private = {
            'A': stub_private(item, 'A', episode['hint'], slot),
            'B': stub_private(item, 'B', episode['hint'], slot),
        }
        final = {
            'A': stub_private(item, 'A', episode['hint'], slot)['vote'],
            'B': stub_private(item, 'B', episode['hint'], slot)['vote'],
        }
        record = observation_record(episode['id'], item, private, final)
        bundle = no_exchange_bundle(
            episode['id'], arm, item,
            {'A': private['A']['rationale'], 'B': private['B']['rationale']},
        )
        checked = validate_record(
            record, assignment=register, no_exchange=bundle, seen_session_ids=seen,
        )
        seen.add(bundle['receipt']['sessions']['A'])
        seen.add(bundle['receipt']['sessions']['B'])
        tiers = shared_error_tiers(record, assignment=register, no_exchange=bundle)
        if 'arm' in record or 'messages' in record:
            raise ValueError('observation record leaked arm or messages')
        rows.append({
            'channel_state': checked['channel_state'],
            'computed_net_a': private['A']['computed_net'],
            'computed_net_b': private['B']['computed_net'],
            'flags': list(checked['flags']),
            'hint': episode['hint'],
            'id': episode['id'],
            'receipt_failures': list(checked['failures']),
            'task_seed': episode['task_seed'],
            'tier1_shared_wrong_decision': tiers['tier1_shared_wrong_decision'],
            'tier2_shared_wrong_answer': tiers['tier2_shared_wrong_answer'],
            'vote_a': private['A']['vote'],
            'vote_b': private['B']['vote'],
        })
    by_arm = {}
    for arm in SE0_ARMS:
        arm_rows = [row for row in rows if register[row['id']] == arm]
        by_arm[arm] = {
            'n': len(arm_rows),
            'tier1': sum(1 for row in arm_rows if row['tier1_shared_wrong_decision']),
            'tier2': sum(1 for row in arm_rows if row['tier2_shared_wrong_answer']),
        }
    return {
        'approval_status': APPROVAL_STATUS,
        'assignment_register': {row['id']: register[row['id']] for row in rows},
        'by_arm': by_arm,
        'episodes': len(rows),
        'evidence_class': EVIDENCE_CLASS,
        'model_calls': 0,
        'network': False,
        'note': (
            'Plumbing only. Deterministic stub. Not a model. Not observations. '
            'Not experimental data. Not a freeze. Not Night ratification. '
            'owner-approved default, pending Night ratification.'
        ),
        'observed_source': 'SYNTHETIC_FIXTURE',
        'plumbing_only': True,
        'receipt_enforcement': (
            'V1-V10 via harness_shared_mistake.verify_receipt. '
            'V9 is UNVERIFIED_PROVIDER offline because no provider log exists '
            'and provider_log_required stays false. That is the one check that '
            'cannot be proven offline.'
        ),
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
