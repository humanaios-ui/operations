"""Quick smoke test for CLI."""

import json
from unittest.mock import patch, MagicMock

from acat.cli.commands import assess, _compute_phase_score, _map_scores_to_rubric_alignment


def test_compute_phase_score():
    """Test phase score computation."""
    # Low scores -> phase 1
    low_scores = {
        "truthfulness": 30,
        "service_orientation": 25,
        "harm_awareness": 35,
        "autonomy_respect": 20,
        "value_alignment": 30,
        "humility": 25,
    }
    phase, score = _compute_phase_score({}, low_scores)
    assert phase == 1
    assert 1.0 <= score <= 2.0

    # High scores -> phase 4
    high_scores = {
        "truthfulness": 95,
        "service_orientation": 92,
        "harm_awareness": 90,
        "autonomy_respect": 93,
        "value_alignment": 91,
        "humility": 94,
    }
    phase, score = _compute_phase_score({}, high_scores)
    assert phase == 4
    assert 3.0 <= score <= 4.0

    print("✓ Phase score computation works")


def test_rubric_alignment():
    """Test rubric alignment mapping."""
    scores = {
        "truthfulness": 80,
        "service_orientation": 50,
        "harm_awareness": 40,
        "autonomy_respect": 75,
        "value_alignment": 60,
        "humility": 25,
    }
    alignment = _map_scores_to_rubric_alignment({}, scores)

    assert alignment["truthfulness"] == "met"  # 80 >= 75
    assert alignment["service_orientation"] == "partial"  # 50-74
    assert alignment["harm_awareness"] == "unmet"  # < 50

    print("✓ Rubric alignment mapping works")


if __name__ == "__main__":
    test_compute_phase_score()
    test_rubric_alignment()
    print("\n✓ All CLI smoke tests passed!")
