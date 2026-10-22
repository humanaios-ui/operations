#!/usr/bin/env python3
"""Read-only projection of synthetic containment fixtures onto the existing Evidence Graph.

No imports from the simulator, no network, no secrets, no repository writes, no
ratification. Prints a *derived* humanaios.graph.observation_projection.v0 JSON view.
Receipt results are self-reported synthetic evidence, NOT production observations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GRAPH = 'EVIDENCE_GRAPH.json'
SCENARIO = 'research/agent_containment/phase0/scenario.json'
RECEIPT = 'research/agent_containment/phase0/trial_receipt.json'
IDENTIFIER = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')
LINKS = {'T06': ('CT1', 'FS1'), 'T07': ('C1',), 'T08': ('C1',),
         'T09': ('CT1',), 'T11': ('CT2',), 'T12': ('CT2',)}


class ProjectionError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ProjectionError(message)


def load_json(root: Path, name: str):
    base = root.resolve()
    path = (base / name).resolve()
    require(path.is_relative_to(base), f'read outside repository refused: {name}')
    require(path.is_file() and path.stat().st_size <= 2_000_000, f'missing/oversized input: {name}')
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProjectionError(f'invalid JSON in {name}: {exc}') from exc
    require(isinstance(value, dict), f'JSON object required: {name}')
    return value, hashlib.sha256(raw).hexdigest()


def source_record(file_ref, state='observed'):
    return {'kind': 'source_file', 'reference': file_ref, 'state': state}


def validate(graph, scenario, receipt):
    require(isinstance(graph.get('nodes'), list) and isinstance(graph.get('edges'), list), 'graph structure invalid')
    require(len(graph['nodes']) <= 5000 and len(graph['edges']) <= 10000, 'graph too large')
    ids = set()
    for node in graph['nodes']:
        require(isinstance(node, dict) and isinstance(node.get('id'), str)
                and IDENTIFIER.fullmatch(node['id']) and len(node['id']) <= 125
                and isinstance(node.get('type'), str) and isinstance(node.get('label'), str),
                'invalid graph node')
        require(node['id'] not in ids, f'duplicate graph node: {node["id"]}')
        ids.add(node['id'])
    for edge in graph['edges']:
        require(isinstance(edge, dict) and edge.get('from') in ids and edge.get('to') in ids
                and isinstance(edge.get('relation'), str) and isinstance(edge.get('state'), str),
                'invalid graph edge endpoint or type')
    required_anchors = set(a for anchors in LINKS.values() for a in anchors)
    require(required_anchors <= ids, f'baseline evidence anchors missing: {sorted(required_anchors - ids)}')
    require(scenario.get('schema_version') == 'humanaios.sim.scenario.v0.1', 'scenario version not supported')
    require(receipt.get('kind') == 'SIMULATION_NOT_PRODUCTION_EVIDENCE', 'receipt is not marked synthetic')
    require(isinstance(scenario.get('scenario_id'), str) and IDENTIFIER.fullmatch(scenario['scenario_id'])
            and scenario['scenario_id'] == receipt.get('scenario_id'), 'scenario/receipt ID mismatch')
    require(isinstance(scenario.get('trial'), list) and isinstance(receipt.get('trial_results'), list),
            'trial list missing')
    require(len(scenario['trial']) == len(receipt['trial_results']) and len(scenario['trial']) <= 512,
            'trial count mismatch or limit exceeded')
    trial_ids = set()
    for planned, declared in zip(scenario['trial'], receipt['trial_results']):
        require(isinstance(planned, dict) and isinstance(declared, dict), 'invalid trial row')
        tid = planned.get('id')
        require(isinstance(tid, str) and IDENTIFIER.fullmatch(tid) and tid not in trial_ids
                and tid == declared.get('id'), 'duplicate/out-of-order/mismatched trial ID')
        trial_ids.add(tid)
        require(type(declared.get('status')) is int and declared['status'] in (200, 201, 202, 423)
                and isinstance(declared.get('reason'), str) and len(declared['reason']) <= 100,
                f'invalid declared outcome: {tid}')
    require(all(type(receipt.get(k)) is int and receipt[k] == 0 for k in
                ('production_writes', 'production_receipts', 'real_network_calls')),
            'receipt does not declare zero production effects')
    require(type(receipt.get('quarantined_events')) is int and
            receipt['quarantined_events'] == sum(x['status'] == 202 for x in receipt['trial_results']),
            'quarantine count inconsistent')
    require(type(receipt.get('events')) is int and
            receipt['events'] == sum(x['status'] in (201, 202) for x in receipt['trial_results']),
            'event count inconsistent')
    require(isinstance(receipt.get('head_hash'), str) and
            bool(re.fullmatch('[a-f0-9]{64}', receipt['head_hash'])), 'missing head hash')
    require(type(receipt.get('chain_verified')) is bool, 'chain verification claim missing')
    # A true value is merely a claim: the receipt does not carry the underlying rows.
    require(type(receipt.get('halted')) is bool, 'halt state not present')


def project(root: Path, observed_at: str):
    try:
        stamp = datetime.fromisoformat(observed_at.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ProjectionError('observed_at must be ISO 8601 with offset') from exc
    require(stamp.tzinfo is not None and stamp.utcoffset() is not None, 'observed_at needs timezone')
    graph, graph_sha = load_json(root, GRAPH)
    scenario, scenario_sha = load_json(root, SCENARIO)
    receipt, receipt_sha = load_json(root, RECEIPT)
    validate(graph, scenario, receipt)
    nodes, edges = [], []

    for n in graph['nodes']:
        nodes.append({'id': f'eg.{n["id"]}', 'kind': f'existing_{n["type"]}'[:100],
                      'label': n['label'][:512],
                      'evidence': source_record(f'{GRAPH}#nodes/{n["id"]}', 'observed')})
    for i, e in enumerate(graph['edges']):
        edges.append({'id': f'eg.edge.{i+1}', 'from': f'eg.{e["from"]}', 'to': f'eg.{e["to"]}',
                      'relation': e['relation'][:100],
                      'evidence': source_record(f'{GRAPH}#edges/{i}', 'inferred')})

    nodes.extend([
        {'id': 'sim.scenario', 'kind': 'synthetic_scenario',
         'label': f'{scenario["scenario_id"]} | fixture only; no live agents',
         'evidence': source_record(f'{SCENARIO}#sha256={scenario_sha}')},
        {'id': 'sim.receipt', 'kind': 'unverified_simulation_receipt',
         'label': 'Declared local Phase 0 outcomes; head hash and zero-write fields not independently attested',
         'evidence': source_record(f'{RECEIPT}#sha256={receipt_sha}', 'unresolved')},
    ])
    edges.append({'id': 'sim.edge.scenario_receipt', 'from': 'sim.scenario', 'to': 'sim.receipt',
                  'relation': 'declared_outcomes',
                  'evidence': source_record(RECEIPT, 'inferred')})

    for row in receipt['trial_results']:
        tid = row['id']
        ref = f'{RECEIPT}#trial_results/{tid}'
        nodes.append({'id': f'sim.trial.{tid}', 'kind': 'synthetic_declared_trial',
                      'label': f'{tid}: {row["reason"]} (status {row["status"]}); synthetic, not production',
                      'evidence': source_record(ref, 'unresolved')})
        edges.append({'id': f'sim.edge.trial.{tid}', 'from': 'sim.receipt', 'to': f'sim.trial.{tid}',
                      'relation': 'declares_trial', 'evidence': source_record(ref, 'inferred')})
        for anchor in LINKS.get(tid, ()):
            edges.append({'id': f'sim.edge.crosswalk.{tid}.{anchor}', 'from': f'sim.trial.{tid}',
                          'to': f'eg.{anchor}', 'relation': 'synthetic_probe_for',
                          'evidence': source_record(ref, 'inferred')})
    result = {
        'schema_version': 'humanaios.graph.observation_projection.v0',
        'projection_id': f'containment-phase0-{receipt_sha[:12]}',
        'source': {'system': 'evidence_graph', 'source_ref': GRAPH,
                   'revision': f'sha256:{graph_sha}', 'observed_at': observed_at,
                   'visibility': 'internal'},
        'nodes': nodes, 'edges': edges,
    }
    all_ids = {n['id'] for n in nodes}
    require(len(all_ids) == len(nodes) and all(e['from'] in all_ids and e['to'] in all_ids for e in edges),
            'projection has duplicate/missing endpoints')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT, help='read-only repository root')
    ap.add_argument('--observed-at', help='ISO-8601 read time (UTC by default; no historical backdating)')
    ap.add_argument('--check', action='store_true', help='validate only; do not print projection')
    args = ap.parse_args()
    stamp = args.observed_at or datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    try:
        result = project(args.root, stamp)
    except (ProjectionError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    if args.check:
        print(f'PASS: read-only synthetic projection; {len(result["nodes"])} nodes, '
              f'{len(result["edges"])} edges; no authority effect')
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
