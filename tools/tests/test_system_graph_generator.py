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
