def compute_li(p1_total: float | None, p3_total: float | None) -> float | None:
    """Canonical Learning Index: LI = Core-6 Phase-3 total / Core-6 Phase-1 total.

    Single source of truth — the live ingest path (ingest_service._compute_learning_index)
    delegates here, so the tested function IS the production function (acat/ audit S-062726).
    Returns None when either total is missing or P1 total is non-positive.
    """
    if p1_total is None or p3_total is None:
        return None
    if p1_total <= 0:
        return None
    return round(p3_total / p1_total, 4)


def compute_sag(p1_total: float, p3_total: float) -> float:
    return round(p1_total - p3_total, 4)


def compute_him(scores: dict) -> float | None:
    # TODO: replace with validated HIM calculation
    return None
