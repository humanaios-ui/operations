#!/usr/bin/env python3
"""Print N tasks with both oracles' verdicts so a human can recompute them.

No model call, no network, no spend. A human must hand-check the sample
before oracle_independent is trusted. This script does not freeze anything.

Usage (from this directory):
    python3 print_oracle_sample.py N [--seed SEED]
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import harness  # noqa: E402
import oracle_independent  # noqa: E402


def render_sample(n, seed):
    if type(n) is not int or n < 1:
        raise ValueError('n')
    if type(seed) is not int:
        raise ValueError('seed')
    rng = random.Random(seed)
    lines = [
        f'sample_seed={seed}',
        f'n={n}',
        'note=A human must hand-check this sample before oracle_independent is trusted. Not a freeze. No model call.',
        'i\tseed\tchallenge\tcharges\tcredit\tnet_limit\treported_net\tindependent_net\tmargin\tharness_fails\tindependent_fails\tagree',
    ]
    disagree = False
    for i in range(n):
        task_seed = rng.randrange(1, 1000000)
        challenge = bool(rng.randrange(2))
        item = harness.task(task_seed, challenge)
        net = oracle_independent.recomputed_net(item['charges'], item['credit'])
        harness_fails = harness.violates(item)
        independent_fails = oracle_independent.fails(item)
        agree = harness_fails == independent_fails
        disagree = disagree or not agree
        lines.append('\t'.join([
            str(i),
            str(task_seed),
            str(challenge),
            ','.join(str(x) for x in item['charges']),
            str(item['credit']),
            str(item['net_limit']),
            str(item['reported_net']),
            str(net),
            str(net - item['net_limit']),
            str(harness_fails),
            str(independent_fails),
            'YES' if agree else 'NO',
        ]))
    return '\n'.join(lines) + '\n', disagree


def main(argv=None):
    parser = argparse.ArgumentParser(description='Print a hand-check sample of both oracles.')
    parser.add_argument('n', type=int, help='how many tasks to print')
    parser.add_argument('--seed', type=int, default=20261116, help='sample seed (printed)')
    args = parser.parse_args(argv)
    try:
        text, disagree = render_sample(args.n, args.seed)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    sys.stdout.write(text)
    return 1 if disagree else 0


if __name__ == '__main__':
    sys.exit(main())
