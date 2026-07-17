"""
university_module_test.py — test module for the real R&D question in
TRINITY_RD_ROADMAP_V2.docx: "Could a modified [H-ACAT] version serve as a
holistic worker development tool... measuring growth across the same six
dimensions that matter for AI systems?"

Composes three real, already-built pieces for a fourth purpose none of
them were originally designed for:
  - H-ACAT's six real dimensions (Truthfulness, Service, Harm Awareness,
    Autonomy Respect, Value Alignment, Humility) as the curriculum's courses
  - tutor-skills' proficiency-badge mechanism (🟥🟨🟩🟦) as the tracking engine
  - kambhampati_tracker.classify() as the closing-vs-recurring diagnostic —
    reused directly, not reimplemented

Maps onto the real four-phase employment pathway already defined in
TRINITY_RD_ROADMAP_V2.docx: Stabilization -> Skill Building ->
Platform Integration -> Self-Sufficiency.

This is a Zone 1 test module — simulated learner data, not a real
deployment. Built to test whether the composition holds up, same
discipline as every other prototype this session.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from kambhampati_tracker import GapObservation, classify, GapPattern

# The six real H-ACAT dimensions — not invented, matching the actual
# operator-facing instrument already tested and fixed this session.
H_ACAT_DIMENSIONS = [
    "truthfulness", "service_orientation", "harm_awareness",
    "autonomy_respect", "value_alignment", "humility",
]

# The real four-phase pathway from TRINITY_RD_ROADMAP_V2.docx
PATHWAY_PHASES = [
    "1_stabilization", "2_skill_building", "3_platform_integration", "4_self_sufficiency",
]

BADGE_THRESHOLDS = [
    (90, "🟦 Mastered"), (70, "🟩 Good"), (40, "🟨 Fair"), (0, "🟥 Weak"),
]


def badge_for(proficiency: float) -> str:
    for threshold, badge in BADGE_THRESHOLDS:
        if proficiency >= threshold:
            return badge
    return "⬜ Unmeasured"


def run_test_learner(name: str, dimension_history: dict) -> dict:
    """dimension_history: {dimension: [(phase_score, next_phase_score), ...]}
    — real shape, reusing GapObservation/classify exactly as built for AI
    substrates, applied here to phase-to-phase learner assessment pairs."""
    results = {}
    for dim, pairs in dimension_history.items():
        obs = [
            GapObservation(dimension=dim, substrate=name, session_id=f"phase-{i}",
                            p1_score=p1, p3_score=p3, session_id_verified=True)
            for i, (p1, p3) in enumerate(pairs)
        ]
        verdict = classify(obs)
        current_proficiency = pairs[-1][1]
        results[dim] = {
            "badge": badge_for(current_proficiency),
            "current_score": current_proficiency,
            "growth_pattern": verdict.pattern.value,
            "recurrence_rate": verdict.recurrence_rate,
            "caveat": verdict.caveat,
        }
    return results


if __name__ == "__main__":
    # Simulated test learner — NOT real data, a test of whether the
    # composition holds, matching this session's Zone 1 discipline.
    # Four phases, six dimensions, plausible progression with one
    # deliberately-stuck dimension (humility) to test the classifier's
    # recurring-vs-closing distinction on a human-learning analog.
    learner = {
        "truthfulness":        [(55, 62), (62, 70), (70, 78), (78, 85)],   # closing
        "service_orientation": [(60, 68), (68, 75), (75, 80), (80, 88)],   # closing
        "harm_awareness":      [(50, 58), (58, 65), (65, 72), (72, 80)],   # closing
        "autonomy_respect":    [(65, 70), (70, 74), (74, 78), (78, 82)],   # closing, slower
        "value_alignment":     [(58, 65), (65, 71), (71, 77), (77, 84)],   # closing
        "humility":            [(45, 44), (44, 46), (46, 45), (45, 47)],   # recurring — stuck
    }

    print("── University module test: one simulated learner, four phases, six real H-ACAT dimensions ──\n")
    results = run_test_learner("test-learner-01", learner)
    for dim, r in results.items():
        print(f"  {dim:22} {r['badge']:14} pattern={r['growth_pattern']:28} "
              f"score={r['current_score']}")
        if r["caveat"]:
            print(f"    caveat: {r['caveat']}")

    print("\n── What this tests ──")
    stuck = [d for d, r in results.items() if "ACCESS_LIMITATION" in r["growth_pattern"] or "MIXED" in r["growth_pattern"]]
    print(f"  Dimensions NOT cleanly closing under practice: {stuck}")
    print("  Real implication: these need a different intervention than more drilling —")
    print("  same distinction the AI-facing Kambhampati work draws between miscalibration")
    print("  (corrects itself) and a structural limitation (doesn't, regardless of exposure).")
