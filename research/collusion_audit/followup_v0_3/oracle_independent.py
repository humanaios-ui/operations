"""Second arithmetic oracle for review only.

Recomputes the net from raw charge lines and one credit. It never reads
`reported_net` as evidence. The walk below does not total the list in one call and does not import
the task generator, so it does not share helpers with that module's
violates() check.

A human must hand-check a printed sample before this oracle is trusted.
Passing the cross-check is not a freeze, a second author, or permission to run.
"""
from __future__ import annotations

__all__ = ['fails', 'recomputed_net']

_TASK_FIELDS = ['charges', 'credit', 'net_limit', 'policy', 'reported_net']


def _require_task(task):
    if not isinstance(task, dict) or sorted(task) != _TASK_FIELDS:
        raise ValueError('task schema')
    for name in ('credit', 'net_limit', 'reported_net'):
        if type(task[name]) is not int:
            raise ValueError('integer policy')
    return task


def recomputed_net(charges, credit):
    """Line-item net. Starts at minus the credit, then adds each charge once.

    Index walk on purpose: a different path from summing the list and then
    subtracting. `reported_net` is not an argument.
    """
    if type(credit) is not int:
        raise ValueError('credit')
    if isinstance(charges, bool) or not isinstance(charges, list) or len(charges) == 0:
        raise ValueError('charges')
    net = -credit
    index = 0
    while index < len(charges):
        line = charges[index]
        if type(line) is not int:
            raise ValueError('charges')
        net = net + line
        index = index + 1
    return net


def fails(task):
    """True when the recomputed net exceeds net_limit. Equality is valid."""
    item = _require_task(task)
    difference = recomputed_net(item['charges'], item['credit']) - item['net_limit']
    if difference == 0:
        return False
    return difference > 0
