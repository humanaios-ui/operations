#!/usr/bin/env python3
"""Read-only Codebase Atlas bridges to Evidence, Session, SCVC and Coordinator.

Git HEAD is the source of the fixed, public, tracked-path inputs. A bridge is
an observation/provenance view, never an authority or runtime-dependency edge.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

SCHEMA = "humanaios.codebase-atlas.bridges.v0.1"
SOURCES = {
    "evidence": ("EVIDENCE_GRAPH.json",),
    "session": ("chat_graph/source/humanaios_cross_chat_knowledge_graph.v0.1.json",
                "chat_graph/evidence/github_hydration_2026-10-02.json",
                "chat_graph/schema/longitudinal_graph.schema.json"),
    "scvc": ("tools/state_continuity_verification_v0_1.py",
             "schemas/validated_learning_record_v1.schema.json",
             "experiments/scvc_v02/trusted_witness.py"),
    "coordinator": ("REPOSITORY_COORDINATOR_POLICY.json",
                    "tools/repository_coordinator_state_v1_1.py"),
}
PATH_RE = re.compile(r"^[A-Za-z0-9._/\-]{1,250}$")
MAX_BYTES = 1_000_000
MAX_BINDINGS = 1500


def _load_head_file(repo: Path, path: str, tracked: set[str]) -> tuple[bytes, str] | None:
    """Read exactly HEAD:path; never read checkout, symlinks, or arbitrary paths."""
    if path not in tracked or not PATH_RE.fullmatch(path) or '..' in PurePosixPath(path).parts:
        return None
    result = subprocess.run(["git", "-C", str(repo), "show", "HEAD:" + path],
                            capture_output=True, timeout=30, check=True)
    if len(result.stdout) > MAX_BYTES:
        raise ValueError(f"oversize pinned source: {path}")
    return result.stdout, sha256(result.stdout).hexdigest()


def project(repo: Path, atlas: dict, tracked: list[str], component_of_path) -> dict:
    """Create four projections; preserve provenance, time and authority boundaries.

    component_of_path is the Atlas config mapper, not a governance decision.
    Historical session observations remain historical even at a newer HEAD.
    """
    if (atlas.get('authority_effect') != 'NONE' or atlas.get('merge_authority') is not False
            or not re.fullmatch(r'[a-f0-9]{40}', str(atlas.get('head_sha', '')))):
        raise ValueError('Atlas identity/authority boundary invalid')
    paths = set(tracked)
    entries = []
    datasets = {}
    bykind = {}
    for kind, filenames in SOURCES.items():
        bykind[kind] = []
        for path in filenames:
            pinned = _load_head_file(repo, path, paths)
            if pinned is None:
                bykind[kind].append({'path': path, 'status': 'NOT_OBSERVED'})
                continue
            payload, digest = pinned
            record = {'path': path, 'sha256': digest, 'head_sha': atlas['head_sha'],
                      'status': 'PINNED_SOURCE_OBSERVED', 'component_id': component_of_path(path)}
            bykind[kind].append(record)
            if path.endswith('.json'):
                try:
                    datasets[path] = json.loads(payload)
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise ValueError(f'invalid pinned JSON: {path}') from exc
            entries.append(record)
    bindings = []
    def attach(kind, path, relation, reference, *, evidence_state='STRUCTURAL_ONLY', source_time=None):
        if (not isinstance(path, str) or path not in paths or len(bindings) >= MAX_BINDINGS
                or not PATH_RE.fullmatch(path)):
            return False
        cid = component_of_path(path)
        if not cid:
            return False
        bindings.append({'graph': kind, 'path': path, 'component_id': cid,
                         'relation': relation, 'source_ref': reference,
                         'epistemic_state': evidence_state,
                         'source_time': source_time,
                         'authority_effect': 'NONE'})
        return True

    e = datasets.get('EVIDENCE_GRAPH.json')
    if e is not None:
        if (not isinstance(e, dict) or not isinstance(e.get('nodes'), list)
                or not isinstance(e.get('edges'), list)):
            raise ValueError('malformed Evidence Graph source')
        # Exact filename uniqueness is necessary: fuzzy/ambiguous labels NEVER bind.
        names = Counter(PurePosixPath(p).name for p in paths)
        index = {PurePosixPath(p).name: p for p in paths if names[PurePosixPath(p).name] == 1}
        for node in e['nodes'][:500]:
            if not isinstance(node, dict) or not isinstance(node.get('id'), str):
                raise ValueError('bad Evidence Graph node')
            label = node.get('label')
            candidate = (label if label in paths else index.get(label)) if isinstance(label, str) else None
            if candidate:
                attach('evidence', candidate, 'EVIDENCE_NODE_LABEL_MATCH',
                       'EVIDENCE_GRAPH.json#' + node['id'], evidence_state='DECLARED_NOT_VERIFIED')

    source_file = SOURCES['session'][0]
    s = datasets.get(source_file)
    overlay = datasets.get(SOURCES['session'][1])
    historical = None
    if s is not None:
        if (not isinstance(s, dict) or not isinstance(s.get('nodes'), list)
                or not isinstance(s.get('edges'), list)):
            raise ValueError('malformed Session Graph source')
        for node in s['nodes'][:500]:
            if not isinstance(node, dict):
                raise ValueError('bad Session Graph node')
            path = node.get('label')
            if isinstance(path, str) and path in paths:
                attach('session', path, 'CHAT_SYNTHESIS_EXACT_PATH',
                       source_file + '#' + str(node.get('id', 'unknown')),
                       evidence_state='CHAT_DERIVED', source_time=s.get('generated_date'))
        historical = {'source_generated_on': s.get('generated_date'), 'overlay_observed_on': None,
                      'overlay_commit_sha': None, 'same_as_atlas_head': False}
    if overlay is not None:
        if not isinstance(overlay, dict) or overlay.get('authority_effect') != 'NONE':
            raise ValueError('Session overlay attempts to assert authority')
        snap = overlay.get('repository_snapshot') or {}
        if not isinstance(snap, dict):
            raise ValueError('invalid Session overlay snapshot')
        historical = historical or {}
        historical.update({'overlay_observed_on': overlay.get('observed_on'),
                           'overlay_commit_sha': snap.get('commit_sha'),
                           'same_as_atlas_head': snap.get('commit_sha') == atlas['head_sha']})

    # SCVC reference files are present as interfaces, NOT as continuity proof.
    for path in SOURCES['scvc']:
        if any(row['path'] == path and row['status'] == 'PINNED_SOURCE_OBSERVED' for row in bykind['scvc']):
            attach('scvc', path, 'SCVC_INTERFACE_PRESENT', path,
                   evidence_state='NO_CONTINUITY_ATTESTATION')

    policy = datasets.get('REPOSITORY_COORDINATOR_POLICY.json')
    coordinator_state = 'NOT_ESTABLISHED'
    if policy is not None:
        if not isinstance(policy, dict) or not isinstance(policy.get('invariants'), list):
            raise ValueError('malformed Coordinator policy')
        state = policy.get('state', {})
        if (not isinstance(state, dict) or state.get('merge_authority') is not False
                or policy.get('evaluation_admission', {}).get('merge_authority') is not False):
            raise ValueError('Coordinator policy violates advisory boundary')
        control_paths = policy.get('control_plane', {}).get('paths')
        if not isinstance(control_paths, list):
            raise ValueError('missing Coordinator control plane')
        for path in control_paths[:200]:
            if isinstance(path, str):
                attach('coordinator', path, 'CONTROL_PLANE_POLICY_REFERENCE',
                       'REPOSITORY_COORDINATOR_POLICY.json#control_plane.paths',
                       evidence_state='POLICY_DECLARED_NOT_ADMITTED')
        coordinator_state = 'STATE_BRANCH_NOT_READ'

    views = {}
    for kind in SOURCES:
        source_count = sum(item['status'] == 'PINNED_SOURCE_OBSERVED' for item in bykind[kind])
        views[kind] = {'sources': bykind[kind], 'present': source_count,
                       'expected': len(SOURCES[kind]),
                       'bindings': sum(1 for b in bindings if b['graph'] == kind),
                       'state': 'SOURCE_BOUND' if source_count == len(SOURCES[kind]) else 'INCOMPLETE_SOURCE',
                       'verification': 'NOT_ESTABLISHED'}
    views['session']['historical_observation'] = historical
    views['scvc']['continuity_status'] = 'NOT_ESTABLISHED'
    views['coordinator']['admission_status'] = coordinator_state
    views['coordinator']['state_branch_verified'] = False
    return {'schema': SCHEMA, 'head_sha': atlas['head_sha'],
            'snapshot': atlas['snapshot'], 'worktree_clean': atlas['worktree_clean'],
            'authority_effect': 'NONE', 'merge_authority': False,
            'can_authorize': False, 'authenticated': False,
            'relationships_are_advisory': True,
            'time_model': 'SOURCE_VALID_TIME_SEPARATE_FROM_HEAD_OBSERVATION',
            'sources': entries, 'views': views,
            'bindings': sorted(bindings, key=lambda b:(b['graph'], b['component_id'], b['path'], b['source_ref'])),
            'limitations': ['No evidence assertion is an implementation proof.',
                            'Historical session snapshots are not current HEAD evidence.',
                            'SCVC continuity is not established without independent witness.',
                            'Coordinator state-branch admission is not read or modified.',
                            'Reference/binding is not authorization or execution.']}
