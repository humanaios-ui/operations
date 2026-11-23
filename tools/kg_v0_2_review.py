#!/usr/bin/env python3
"""HumanAIOS KG v0.2 Z1 advisory contract checker; never ratifies or writes to GitHub.

Only reads local JSON. A passed structural check does not validate the cited
commits, authorizations, causal relationships or real-world outcomes.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

TOOL_NAME = 'kg_v0_2_review'
TOOL_VERSION = '0.1.0'
TOOL_CATEGORY = 'validation_tool'
TOOL_SESSION = 'Z1-independent-review-2026-11-23'
TOOL_ZONE = 1
RELATIONS = {'depends_on', 'supported_by', 'approved_by', 'resulted_in'}
EXTERNAL_KINDS = {'registry', 'decision', 'evidence', 'outcome'}
STATES = {'recorded', 'candidate'}


def check(base: dict, proposal: dict) -> dict:
    """Return reproducible HOLD/PASS structure; never confer evidentiary authority."""
    blockers, warnings = [], []
    base_nodes = base.get('nodes', [])
    base_edges = base.get('edges', [])
    new_nodes = proposal.get('new_nodes', [])
    edges = proposal.get('edges', [])
    b_ids = [n.get('id') for n in base_nodes]
    n_ids = [n.get('id') for n in new_nodes]
    ids = b_ids + n_ids
    old_eids = [e.get('id') for e in base_edges]
    eids = [e.get('id') for e in edges]
    if proposal.get('extends') != base.get('graph_id'):
        blockers.append('extends must match exact v0.1 graph_id')
    if proposal.get('authority_effect') != 'NONE' or base.get('authority_effect') != 'NONE':
        blockers.append('graph authority_effect must remain NONE')
    if not isinstance(new_nodes, list) or not isinstance(edges, list):
        blockers.append('nodes and edges must be arrays')
    if len(ids) != len(set(ids)) or not all(isinstance(x, str) and x for x in ids):
        blockers.append('node IDs collide, are missing, or are malformed')
    if len(eids) != len(set(eids)) or any(not isinstance(x, int) or isinstance(x, bool) for x in eids):
        blockers.append('duplicate or invalid proposal edge IDs')
    if set(eids) & set(old_eids):
        blockers.append('proposal edge IDs collide with v0.1')
    if eids and old_eids and min(eids) <= max(old_eids):
        blockers.append('proposal edges must be additive after v0.1 IDs')
    for n in new_nodes:
        if not isinstance(n.get('id'), str) or not n.get('label'):
            blockers.append('a construct node lacks an id or label')
        # first_dated = "" is explicitly permitted: missing date is not invented.
    known = set(ids)
    external = Counter()
    states = Counter()
    by_relation = Counter()
    external_rows = []
    outcome_ids = []
    for e in edges:
        eid = e.get('id')
        if e.get('relation') not in RELATIONS:
            blockers.append(f'edge {eid}: unknown relation')
        if e.get('link_state') not in STATES:
            blockers.append(f'edge {eid}: invalid link_state')
        if e.get('status') != 'unratified':
            blockers.append(f'edge {eid}: approval/ratification claimed by data')
        source = e.get('source')
        target = e.get('target')
        if source not in known:
            blockers.append(f'edge {eid}: unresolved internal source {source!r}')
        if target not in known:
            if not isinstance(target, str) or ':' not in target:
                blockers.append(f'edge {eid}: invalid external target {target!r}')
            else:
                prefix, val = target.split(':', 1)
                if prefix not in EXTERNAL_KINDS or not val or '..' in val or '\\' in val or '\n' in val:
                    blockers.append(f'edge {eid}: unrecognized/unsafe external target {target!r}')
                else:
                    external[prefix] += 1
                    external_rows.append({'id': eid, 'locator': target, 'resolution': 'UNVERIFIED_BY_STRUCTURE_CHECK'})
        basis = e.get('basis')
        if not isinstance(basis, dict) or not isinstance(basis.get('note'), str) or not basis['note'].strip():
            blockers.append(f'edge {eid}: missing basis.note')
            basis = basis if isinstance(basis, dict) else {}
        if e.get('link_state') == 'recorded' and basis.get('type') == 'inference':
            blockers.append(f'edge {eid}: inferred link promoted to recorded')
        if e.get('link_state') == 'candidate' and basis.get('type') == 'inference' and basis.get('ref'):
            warnings.append(f'edge {eid}: inference has a cited ref; verify provenance')
        if e.get('relation') == 'resulted_in':
            outcome_ids.append(eid)
            if isinstance(target, str) and target.startswith('registry:'):
                warnings.append(f'edge {eid}: registry entry is not a verified measured outcome')
            elif isinstance(target, str) and target.startswith('outcome:'):
                warnings.append(f'edge {eid}: named outcome artifact is not proof of real-world benefit')
        if e.get('relation') == 'approved_by':
            warnings.append(f'edge {eid}: approval reference does not authorize graph promotion')
        if e.get('link_state') == 'recorded' and basis.get('type') == 'commit' and len(str(basis.get('ref', ''))) < 40:
            warnings.append(f'edge {eid}: shortened commit ref; pin full SHA before source promotion')
        states[e.get('link_state')] += 1
        by_relation[e.get('relation')] += 1
    if states['candidate'] and states['candidate'] + states['recorded'] != len(edges):
        blockers.append('candidate+recorded counts do not account for every edge')
    for eid in outcome_ids:
        if eid not in eids:
            blockers.append(f'missing outcome edge {eid}')
    return {
        'tool': TOOL_NAME,
        'version': TOOL_VERSION,
        'authority_effect': 'NONE',
        'can_authorize': False,
        'verdict': 'HOLD_STRUCTURE' if blockers else 'PASS_STRUCTURE_ONLY',
        'blockers': blockers,
        'warnings': sorted(set(warnings)),
        'counts': {
            'base_nodes': len(base_nodes), 'base_edges': len(base_edges),
            'new_nodes': len(new_nodes), 'proposed_edges': len(edges),
            'link_states': dict(states), 'relations': dict(by_relation),
            'external_locators': dict(external),
            'outcome_edges_requiring_independent_proof': len(outcome_ids),
            'verified_human_outcomes_by_this_checker': 0,
        },
        'external_locator_manifest': external_rows,
        'separate_research_graph': 'NOT_IMPORTED_NOT_JOINED',
        'limitations': [
            'Commit subjects and registry text do not prove relationships or outcomes.',
            'Structural checks do not fetch GitHub or verify external locator targets.',
            'Every edge remains unratified until human Z2 disposition.',
            'The independent 358-node research graph is not merged or mapped.',
        ],
    }


def write_report(path: str, report: dict) -> None:
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write('\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('baseline', type=Path)
    ap.add_argument('proposal', type=Path)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    try:
        base = json.loads(args.baseline.read_text(encoding='utf-8'))
        proposal = json.loads(args.proposal.read_text(encoding='utf-8'))
        result = check(base, proposal)
    except (OSError, ValueError, TypeError) as exc:
        print(f'HOLD_INPUT: {exc}')
        return 2
    if args.report:
        write_report(str(args.report), result)
    print(result['verdict'], json.dumps(result['counts'], sort_keys=True))
    for b in result['blockers']:
        print('BLOCK', b)
    return 0 if not result['blockers'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
