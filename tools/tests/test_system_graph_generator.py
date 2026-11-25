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


def _load_renderer():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'system_graph_render', os.path.join(ROOT, 'tools', 'system_graph_render_v1_0.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_render_marks_feedback_edges_and_titles_causality():
    """A reader of the rendered page must be able to tell loop-closing edges from forward edges."""
    g = sgg.build_graph_dict()
    text = _load_renderer().render(g, source_path='system_graph.json', source_sha256='0' * 64, commit='test')
    assert '| from | to | label | feedback |' in text
    rows = [ln for ln in text.splitlines() if ln.startswith('| `') and ln.rstrip().endswith('| yes |')]
    assert len(rows) == sum(1 for e in g['edges'] if e.get('feedback'))
    assert any(ln.rstrip().endswith('| no |') for ln in text.splitlines())
    assert '### Causality (' in text


def _count_tests(*relpaths):
    import re
    n = 0
    for rel in relpaths:
        with open(os.path.join(ROOT, rel)) as f:
            n += len(re.findall(r'^def test_', f.read(), re.M))
    return n


def test_declared_test_counts_match_the_files():
    """The `tests` field on SG and SGF is a claim; keep it equal to the suites it names."""
    nodes = sgg.build_graph_dict()['nodes']
    gen = 'tools/tests/test_system_graph_generator.py'
    lint = 'tools/tests/test_graph_capture_lint.py'
    assert nodes['SG']['tests'] == _count_tests(gen)
    assert nodes['SGF']['tests'] == _count_tests(gen, lint)


def test_batch_one_edges_keep_their_evidence():
    """Each batch-one edge rests on a line in a file. If that line goes (or is commented out), the edge must be revisited.

    This reads text; it does not show that the line executes.
    """
    pairs = {(e.source, e.target) for e in _built().edges}
    evidence = {
        ('GNER', 'ACATR'): ('experiments/acat_r_comparison/study.py', 'from gner_verify_e1 import reconcile'),
        ('TDG', 'IGV'): ('tools/intent_graph_v1_0.py', 'from tests.test_temporal_dissolution_gate import is_risky'),
        ('CPGA', 'CUST'): ('tools/tests/test_control_plane_github_adapter_v0_1.py', 'observer.normalize_observation('),
    }
    for edge, (rel, needle) in evidence.items():
        assert edge in pairs, edge
        with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
            live = [ln for ln in f.read().splitlines() if not ln.lstrip().startswith('#')]
        assert any(needle in ln for ln in live), (
            '%s no longer has a non-comment line containing %r; revisit edge %s' % (rel, needle, edge))
