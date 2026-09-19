"""
learner_growth_classifier.py — the correctly-inverted counterpart to
kambhampati_tracker.py, built after direct reuse was found polarity-backwards:
truthfulness's healthy 7-8pt/phase growth read as "recurring" (bad), humility's
near-zero stuck oscillation read as "closed" (good) — exactly wrong.

Same shape as kambhampati_tracker.py: phase-pair observations, a hard
refusal below a minimum sample size, a threshold-based classify(). Opposite
polarity: here a LARGE positive delta is the healthy signal (real growth),
and a SMALL or negative delta across repeated phases is the signal worth
flagging (plateau or regression) — not the reverse.

Distinguishes three transition types per phase, not just two, because
"not growing" and "actively regressing" need different responses:
GROWTH / STAGNATION / REGRESSION.
"""

from dataclasses import dataclass, field
from enum import Enum
import statistics


class TransitionType(Enum):
    GROWTH = "growth"
    STAGNATION = "stagnation"
    REGRESSION = "regression"


class GrowthPattern(Enum):
    GROWTH_CONSISTENT = "consistent_growth_across_phases"
    PLATEAU_CONSISTENT = "plateaued_despite_repeated_practice"
    REGRESSION_CONSISTENT = "regressing_across_phases"
    MIXED = "mixed_signal"
    INSUFFICIENT_DATA = "insufficient_data"


# A delta below this magnitude counts as stagnation, not growth or regression —
# same threshold magnitude as kambhampati_tracker's CLOSURE_THRESHOLD (5.0),
# deliberately kept comparable, but consumed with the opposite meaning:
# there, small = good; here, small = the concerning case.
GROWTH_THRESHOLD = 5.0

# Matches the real four-phase pathway (Stabilization, Skill Building,
# Platform Integration, Self-Sufficiency) — a verdict needs at least this
# many phase transitions to be honest, same discipline as the original.
MIN_PHASES_FOR_VERDICT = 4

# Fraction of transitions that must share a type for a clean (non-MIXED) verdict.
CONSISTENCY_THRESHOLD = 0.7


@dataclass
class PhaseObservation:
    dimension: str
    learner_id: str
    phase_id: str
    start_score: float
    end_score: float

    @property
    def delta(self) -> float:
        return self.end_score - self.start_score

    @property
    def transition_type(self) -> TransitionType:
        if self.delta >= GROWTH_THRESHOLD:
            return TransitionType.GROWTH
        elif self.delta <= -GROWTH_THRESHOLD:
            return TransitionType.REGRESSION
        return TransitionType.STAGNATION


@dataclass
class LearnerVerdict:
    dimension: str
    learner_id: str
    n_phases: int
    growth_rate: float
    stagnation_rate: float
    regression_rate: float
    mean_delta: float
    pattern: GrowthPattern
    caveat: str = ""


def classify(observations: list[PhaseObservation]) -> LearnerVerdict:
    """Core classification. Refuses a verdict below the minimum phase count,
    same discipline as kambhampati_tracker — no forced answer from too little data."""
    if not observations:
        raise ValueError("no observations supplied")

    dim = observations[0].dimension
    learner = observations[0].learner_id
    n = len(observations)

    if n < MIN_PHASES_FOR_VERDICT:
        return LearnerVerdict(
            dimension=dim, learner_id=learner, n_phases=n,
            growth_rate=float('nan'), stagnation_rate=float('nan'), regression_rate=float('nan'),
            mean_delta=float('nan'), pattern=GrowthPattern.INSUFFICIENT_DATA,
            caveat=f"n={n} < minimum {MIN_PHASES_FOR_VERDICT} phases for any verdict",
        )

    types = [o.transition_type for o in observations]
    n_growth = sum(1 for t in types if t == TransitionType.GROWTH)
    n_regression = sum(1 for t in types if t == TransitionType.REGRESSION)
    n_stagnation = sum(1 for t in types if t == TransitionType.STAGNATION)
    growth_rate = n_growth / n
    regression_rate = n_regression / n
    stagnation_rate = n_stagnation / n
    mean_delta = statistics.mean(o.delta for o in observations)

    if growth_rate >= CONSISTENCY_THRESHOLD:
        pattern = GrowthPattern.GROWTH_CONSISTENT
    elif regression_rate >= CONSISTENCY_THRESHOLD:
        pattern = GrowthPattern.REGRESSION_CONSISTENT
    elif stagnation_rate >= CONSISTENCY_THRESHOLD:
        pattern = GrowthPattern.PLATEAU_CONSISTENT
    else:
        pattern = GrowthPattern.MIXED

    return LearnerVerdict(
        dimension=dim, learner_id=learner, n_phases=n,
        growth_rate=round(growth_rate, 3), stagnation_rate=round(stagnation_rate, 3),
        regression_rate=round(regression_rate, 3), mean_delta=round(mean_delta, 2),
        pattern=pattern,
    )


PATHWAY_PHASES = [
    "1_stabilization", "2_skill_building", "3_platform_integration", "4_self_sufficiency",
]


def run_learner(learner_id: str, dimension_history: dict) -> dict:
    """dimension_history: {dimension: [(start, end), ...]} — same input
    shape as the (broken) direct reuse attempt, so the comparison is exact."""
    results = {}
    for dim, pairs in dimension_history.items():
        obs = [
            PhaseObservation(dimension=dim, learner_id=learner_id, phase_id=PATHWAY_PHASES[i],
                              start_score=s, end_score=e)
            for i, (s, e) in enumerate(pairs)
        ]
        results[dim] = classify(obs)
    return results


if __name__ == "__main__":
    # EXACT same simulated learner data as the broken direct-reuse attempt,
    # so the fix is verifiable against the same known-wrong baseline.
    learner = {
        "truthfulness":        [(55, 62), (62, 70), (70, 78), (78, 85)],   # should read GROWTH
        "service_orientation": [(60, 68), (68, 75), (75, 80), (80, 88)],   # should read GROWTH
        "harm_awareness":      [(50, 58), (58, 65), (65, 72), (72, 80)],   # should read GROWTH
        "autonomy_respect":    [(65, 70), (70, 74), (74, 78), (78, 82)],   # slower growth — check MIXED vs GROWTH
        "value_alignment":     [(58, 65), (65, 71), (71, 77), (77, 84)],   # should read GROWTH
        "humility":            [(45, 44), (44, 46), (46, 45), (45, 47)],   # should read PLATEAU
    }

    print("── Corrected classifier, same learner data as the broken attempt ──\n")
    results = run_learner("test-learner-01", learner)
    for dim, v in results.items():
        print(f"  {dim:22} pattern={v.pattern.value:32} growth_rate={v.growth_rate}  mean_delta={v.mean_delta:+.2f}")
        if v.caveat:
            print(f"    caveat: {v.caveat}")

    print("\n── Verification against expectation ──")
    expected_growth = {"truthfulness", "service_orientation", "harm_awareness", "value_alignment"}
    expected_plateau = {"humility"}
    for dim in expected_growth:
        ok = results[dim].pattern == GrowthPattern.GROWTH_CONSISTENT
        print(f"  {dim:22} expected GROWTH_CONSISTENT: {'PASS' if ok else 'FAIL — got ' + results[dim].pattern.value}")
    for dim in expected_plateau:
        ok = results[dim].pattern == GrowthPattern.PLATEAU_CONSISTENT
        print(f"  {dim:22} expected PLATEAU_CONSISTENT: {'PASS' if ok else 'FAIL — got ' + results[dim].pattern.value}")
    print(f"  autonomy_respect (slower grower, 4-5pt/phase): {results['autonomy_respect'].pattern.value} "
          f"— below GROWTH_THRESHOLD={GROWTH_THRESHOLD}, real edge case worth knowing about, not hidden")

    print("\n── Insufficient-data refusal, tested directly ──")
    tiny = [PhaseObservation(dimension="fair", learner_id="test", phase_id="1_stabilization",
                              start_score=50, end_score=60)]
    v = classify(tiny)
    print(f"  n=1: pattern={v.pattern.value}  caveat={v.caveat}")
