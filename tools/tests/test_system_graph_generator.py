"""Guards for system_graph_generator.py: valid, fresh, and minimal feedback set."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import system_graph_generator as sgg  # noqa: E402


def _built():
    gen = sgg.SystemGraphGenerator()
    gen.build_phase2_graph()
    return gen


def test_generator_output_is_valid():
    v = _built().validate_graph()
    assert v['valid'], v['errors']


def test_committed_graph_matches_generator():
    assert sgg.check(os.path.join(ROOT, 'system_graph.json')) == []


def test_new_forward_cycle_is_detected():
    gen = _built()
    gen.add_edge(sgg.Edge('CIG', 'Z2', 'control_flow', 'bogus back edge'))
    assert not gen.validate_graph()['valid']


def test_feedback_set_is_minimal():
    gen = _built()
    fb = [e for e in gen.edges if e.feedback]
    assert fb
    for e in fb:
        e.feedback = False
        assert not gen.validate_graph()['valid'], 'feedback edge not needed: %s->%s' % (e.source, e.target)
        e.feedback = True


def test_check_flags_age(tmp_path):
    d = sgg.build_graph_dict()
    d['generated_at'] = '2020-01-01T00:00:00'
    p = tmp_path / 'g.json'
    p.write_text(json.dumps(d))
    assert any('days old' in x for x in sgg.check(str(p), max_age_days=30))


def test_every_orphan_has_a_note():
    """A node with no edges is allowed only when it says why."""
    gen = _built()
    touched = set()
    for e in gen.edges:
        touched.add(e.source)
        touched.add(e.target)
    bare = [i for i, n in gen.nodes.items() if i not in touched and not n.notes.strip()]
    assert bare == [], 'orphan nodes without notes: %s' % bare


def test_output_is_deterministic_across_hash_seeds():
    """--check compares generator output to the committed file, so output must not depend on set order."""
    import subprocess
    outs = set()
    for seed in ('1', '2', '3'):
        r = subprocess.run(
            [sys.executable, '-c',
             "import json,system_graph_generator as g;"
             "d=g.build_graph_dict();d.pop('generated_at');print(json.dumps(d,sort_keys=True))"],
            cwd=ROOT, env={**os.environ, 'PYTHONHASHSEED': seed},
            capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr
        outs.add(r.stdout)
    assert len(outs) == 1


def _write_variant(tmp_path, mutate):
    d = sgg.build_graph_dict()
    mutate(d)
    p = tmp_path / 'g.json'
    p.write_text(json.dumps(d))
    return str(p)


def test_check_rejects_missing_timestamp_without_age_limit(tmp_path):
    """The PR gate runs without --max-age-days; a graph with no usable timestamp must still fail."""
    path = _write_variant(tmp_path, lambda d: d.pop('generated_at'))
    assert any('generated_at' in x for x in sgg.check(path))


def test_check_rejects_malformed_timestamp_without_age_limit(tmp_path):
    path = _write_variant(tmp_path, lambda d: d.update(generated_at='not-a-date'))
    assert any('generated_at' in x for x in sgg.check(path))


def test_removed_edges_stay_removed():
    """Edges dropped after review because no file supports them."""
    pairs = {(e.source, e.target) for e in _built().edges}
    for bad in [('CIP', 'NF'), ('VER', 'GNER'), ('VER', 'MODE'), ('ACAT', 'HIAE'), ('ACAT', 'ACATR'), ('TDG', 'CIG')]:
        assert bad not in pairs, bad
