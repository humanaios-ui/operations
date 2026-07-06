"""Inter-rater agreement — Cohen's kappa (Stage-1 validity layer, S-070626).

Makes validity a first-class, computed output instead of a `None` stub. This is the
measurement of the instrument's own trustworthiness: how much two raters (human vs
human, or machine vs human) agree on an AI's dimension scores. Per the POC plan, a
calibration claim must ship with this number, or it doesn't ship.

Pure Python (no numpy/sklearn) to stay within the minimal service footprint.

Scores are 0-100 ordinal, so the default is QUADRATIC-WEIGHTED kappa over binned bands
(near-miss disagreements penalised less than far ones). Unweighted kappa is available
for genuinely categorical labels.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

DEFAULT_BANDS = 5  # 0-100 -> 5 bands of 20 (ordinal categories for kappa)


def _bin(score: float, bands: int = DEFAULT_BANDS) -> int:
    """Map a 0-100 score to a band index in [0, bands-1]."""
    if score is None:
        raise ValueError("cannot bin a None score")
    s = max(0.0, min(100.0, float(score)))
    idx = int(s / (100.0 / bands))
    return min(idx, bands - 1)


def cohens_kappa(labels_a: Sequence[int], labels_b: Sequence[int]) -> float:
    """Unweighted Cohen's kappa for two paired sequences of categorical labels.

    kappa = (po - pe) / (1 - pe). Returns 1.0 when raters are in perfect agreement
    and chance agreement is degenerate (pe == 1), 0.0 when there is no signal.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("rater sequences must be equal length")
    n = len(labels_a)
    if n == 0:
        raise ValueError("no items to score")

    categories = set(labels_a) | set(labels_b)
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    pe = 0.0
    for c in categories:
        pa = sum(1 for a in labels_a if a == c) / n
        pb = sum(1 for b in labels_b if b == c) / n
        pe += pa * pb

    if pe == 1.0:
        return 1.0  # both raters gave one constant label and agreed
    return round((po - pe) / (1.0 - pe), 4)


def quadratic_weighted_kappa(
    ratings_a: Sequence[int], ratings_b: Sequence[int], bands: int = DEFAULT_BANDS
) -> float:
    """Quadratic-weighted kappa over ordinal band indices in [0, bands-1].

    Disagreement weight d_ij = ((i-j)/(bands-1))^2 — adjacent bands cost little, far
    bands cost most. kappa = 1 - sum(d*O) / sum(d*E).
    """
    if len(ratings_a) != len(ratings_b):
        raise ValueError("rater sequences must be equal length")
    n = len(ratings_a)
    if n == 0:
        raise ValueError("no items to score")
    if bands < 2:
        raise ValueError("need >= 2 bands for weighted kappa")

    # observed matrix O and marginals
    O = [[0 for _ in range(bands)] for _ in range(bands)]
    hist_a = [0] * bands
    hist_b = [0] * bands
    for a, b in zip(ratings_a, ratings_b):
        O[a][b] += 1
        hist_a[a] += 1
        hist_b[b] += 1

    denom = (bands - 1) ** 2
    num = 0.0  # sum d_ij * O_ij
    den = 0.0  # sum d_ij * E_ij
    for i in range(bands):
        for j in range(bands):
            d = ((i - j) ** 2) / denom
            e_ij = (hist_a[i] * hist_b[j]) / n
            num += d * O[i][j]
            den += d * e_ij

    if den == 0.0:
        return 1.0  # no expected disagreement -> perfect
    return round(1.0 - num / den, 4)


def compute_inter_rater_agreement(
    scores_a: Dict[str, float],
    scores_b: Dict[str, float],
    weighted: bool = True,
    bands: int = DEFAULT_BANDS,
) -> dict:
    """Agreement between two raters' dimension-score dicts (e.g. machine vs human,
    or human A vs human B). Compares the shared dimensions, binning 0-100 scores into
    ordinal bands, and returns the (weighted) Cohen's kappa.

    Backwards-compatible with the previous `(machine_scores, human_scores)` call.
    """
    shared = sorted(
        k for k in scores_a.keys() & scores_b.keys()
        if scores_a[k] is not None and scores_b[k] is not None
    )
    if len(shared) < 2:
        return {
            "metric": "cohens_kappa",
            "value": None,
            "status": "insufficient_overlap",
            "n_items": len(shared),
            "weighted": weighted,
        }

    a = [_bin(scores_a[k], bands) for k in shared]
    b = [_bin(scores_b[k], bands) for k in shared]
    value = quadratic_weighted_kappa(a, b, bands) if weighted else cohens_kappa(a, b)

    return {
        "metric": "cohens_kappa",
        "value": value,
        "status": "computed",
        "n_items": len(shared),
        "weighted": weighted,
        "bands": bands,
        "dimensions": shared,
    }
