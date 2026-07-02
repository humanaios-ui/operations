def compute_li(p1_total: float, p3_total: float) -> float | None:
    """Generic Learning-Index ratio p3_total / p1_total.

    AUTHORITATIVE served LI lives in ingest_service._compute_learning_index
    (Core-6 only, per Z2-IC-01, guarding None + non-positive p1_total). This
    is a standalone utility (unit tests); its guard is kept consistent with
    the served path so the two never diverge in behaviour.
    """
    if not p1_total or p1_total <= 0:
        return None
    return round(p3_total / p1_total, 4)


def compute_sag(p1_total: float, p3_total: float) -> float:
    return round(p1_total - p3_total, 4)


def compute_him(scores: dict) -> float | None:
    # TODO: replace with validated HIM calculation
    return None
