def compute_li(p1_total: float, p3_total: float) -> float | None:
    if not p1_total:
        return None
    return round(p3_total / p1_total, 4)


def compute_sag(p1_total: float, p3_total: float) -> float:
    return round(p1_total - p3_total, 4)


def compute_him(scores: dict) -> float | None:
    """Humility Index Metric — DELIBERATELY DEFERRED (S-070626), not a silent TODO.

    We do not ship an unvalidated humility metric: inventing a formula the corpus
    can't yet validate would be the exact overclaim ACAT exists to detect. HIM stays
    None until a definition is ratified (Z2) AND checkable against the human-grounded
    verified corpus the POC produces. Callers surface this as
    him_status="deferred_pending_validation" so the None is labeled, never mistaken
    for a computed 0. See ACAT_POC_PLAN Stage 1.
    """
    return None
