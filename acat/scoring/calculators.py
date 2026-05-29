def compute_li(p1_total: float, p3_total: float) -> float | None:
    if not p1_total:
        return None
    return round(p3_total / p1_total, 4)


def compute_sag(p1_total: float, p3_total: float) -> float:
    return round(p1_total - p3_total, 4)


def compute_him(scores: dict) -> float | None:
    # TODO: replace with validated HIM calculation
    return None
