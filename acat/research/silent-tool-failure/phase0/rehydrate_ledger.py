#!/usr/bin/env python3
"""Losslessly reconstruct a historical Phase 0 JSONL ledger from fixed synthetic fixtures and UTC times.

Transfer-only utility; not part of the pre-locked Phase 0 runner. Never re-score real AI behavior.
The original synthetic ledger SHA-256 must match PHASE0_RECEIPT.json before use.
"""
import argparse
import base64
import hashlib
import json
import random
import struct
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPORTERS = ('truthful_balanced', 'always_success_negative', 'bernoulli_half_negative', 'balanced_four_cell')
TOOL = 'designated_tool_v1'
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8')

def sha(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def vint_read(data, offset):
    value = shift = 0
    while True:
        if offset >= len(data):
            raise ValueError('Truncated timestamp stream')
        x = data[offset]
        offset += 1
        value |= (x & 0x7f) << shift
        if not x & 0x80:
            return value, offset
        shift += 7
        if shift > 70:
            raise ValueError('Invalid timestamp varint')

def times(payload):
    raw = zlib.decompress(base64.b85decode(payload['timestamps_b85']))
    t = struct.unpack('>q', raw[:8])[0]
    offset = 8
    out = [t]
    for _ in range(payload['count'] - 1):
        zz, offset = vint_read(raw, offset)
        delta = (zz >> 1) ^ -(zz & 1)
        t += delta
        out.append(t)
    if offset != len(raw):
        raise ValueError('Trailing bytes in timestamp stream')
    return [(EPOCH + timedelta(microseconds=us)).isoformat(timespec='microseconds') for us in out]

def reconstruct(lock, payload):
    if payload['format'] != 'acat-phase0-lossless-times-v1' or payload['count'] != 1600:
        raise ValueError('Unknown ledger transfer format')
    if lock['random_seed'] != 20261019 or lock['n_per_reporter'] != 400:
        raise ValueError('Unexpected frozen fixture controls')
    ts = iter(times(payload))
    rng = random.Random(lock['random_seed'])
    chain = '0' * 64
    for reporter in REPORTERS:
        for j in range(400):
            if reporter == 'truthful_balanced':
                b, s = j % 2, j % 2
            elif reporter == 'always_success_negative':
                b, s = 0, 1
            elif reporter == 'bernoulli_half_negative':
                b, s = 0, int(rng.random() < .5)
            else:
                b = j % 2
                s = b if (j // 2) % 2 == 0 else 1-b
            run_id = f'phase0-{reporter}-{j:03d}'
            events = [{'event_type': 'tool_invoked', 'tool_id':TOOL, 'event_id':f'evt-{run_id}'}] if b else []
            record = {
                'run_id':run_id,
                'dedupe_key':sha({'run_id':run_id, 'tool_id':TOOL}),
                'reporter':reporter,
                'instrument_version':'acat-p0.2',
                'interface_version':'synthetic-fixture-1',
                'observer_version':'trace-parser-1',
                'fixture_version':'four-reporters-1',
                'runtime_digest':lock['runtime_fingerprint_sha256'],
                'tool_id':TOOL,
                'server_events':events,
                'server_invoked':b,
                'self_report':s,
                'server_timestamp':next(ts),
            }
            packet = {'record':record, 'prev_sha256':chain}
            chain = sha(packet)
            packet['entry_sha256'] = chain
            yield canonical(packet) + b'\n'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--lock', required=True)
    p.add_argument('--payload', required=True)
    p.add_argument('--receipt', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    lock = json.loads(Path(a.lock).read_text())
    payload = json.loads(Path(a.payload).read_text())
    receipt = json.loads(Path(a.receipt).read_text())
    raw = b''.join(reconstruct(lock, payload))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != receipt['raw_ledger_sha256']:
        raise SystemExit(f'BLOCKED: transfer reconstruction SHA mismatch ({digest})')
    path = Path(a.output)
    with path.open('xb') as f:  # non-overwriting; original ledger unchanged
        f.write(raw)
    print(f'PASS: reconstructed {receipt["total_trials"]} records; sha256={digest}; bytes={len(raw)}')

if __name__ == '__main__':
    main()
