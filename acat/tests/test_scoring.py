from acat.scoring.calculators import compute_li, compute_sag


def test_compute_li():
    assert compute_li(100, 80) == 0.8


def test_compute_sag():
    assert compute_sag(100, 80) == 20
