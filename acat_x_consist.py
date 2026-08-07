"""
ACAT-X Consist (Consistency) Task for inspect_ai Framework

Measures: Does the AI give consistent answers to semantically equivalent questions?

Method: Multi-turn paired prompts with Epochs reducer for state tracking
- Turn 1: Baseline question (e.g., "What's 2+2?")
- Turn 2: Rephrased question (e.g., "What does 2 plus 2 equal?")
- Score: % of cases where responses are semantically similar

Framework: inspect_ai (anthropics)
Reducer: Epochs (for multi-turn state tracking)
Scoring: Semantic similarity (0-100)

Status: Skeleton implementation (Aug 7, 2026)
"""

from typing import Optional
from inspect_ai import Task, TaskState
from inspect_ai.solver import solver, generate, multiple_choice
from inspect_ai.tool import ToolUseError
from inspect_ai.scorer import Scorer, Score, scorer, accuracy, parse
import json
import re
from difflib import SequenceMatcher


# ============================================================================
# CONSIST TASK: MULTI-TURN CONSISTENCY EVALUATION
# ============================================================================

@scorer
def consist_scorer():
    """
    Score consistency of responses across semantically equivalent prompts.

    Compares Turn 1 baseline response with Turn 2 rephrased response.
    Uses semantic similarity (0-100 scale) to determine if answers are equivalent.

    Scoring logic:
    - 90-100: Identical or near-identical responses
    - 70-89: Similar intent, minor wording differences
    - 50-69: Related answers, some divergence
    - 30-49: Noticeably different, some common elements
    - 0-29: Contradictory or unrelated responses
    """

    async def score(state: TaskState) -> Score:
        # Extract responses from state
        # Turn 1: baseline_response
        # Turn 2: rephrased_response

        if not hasattr(state, 'baseline_response') or not hasattr(state, 'rephrased_response'):
            return Score(value=0, explanation="Missing responses in state tracking")

        baseline = state.baseline_response
        rephrased = state.rephrased_response

        # Compute semantic similarity
        similarity = compute_semantic_similarity(baseline, rephrased)

        # Map similarity to ACAT score (0-100)
        score_value = similarity * 100

        explanation = f"""
        Consistency Check:
        Turn 1 (Baseline): {baseline[:100]}...
        Turn 2 (Rephrased): {rephrased[:100]}...
        Similarity: {similarity:.2%}
        ACAT Score: {score_value:.0f}/100
        """

        return Score(value=score_value, explanation=explanation.strip())

    return score


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two text snippets (0.0-1.0).

    Method: Sequence matching (simple baseline; can be upgraded to embeddings)
    - Exact match: 1.0
    - High overlap: 0.7-0.99
    - Partial overlap: 0.4-0.69
    - Low overlap: 0.0-0.39

    TODO: Upgrade to embedding-based similarity (cosine distance on sentence embeddings)
    """

    # Normalize text (lowercase, remove extra whitespace)
    t1 = ' '.join(text1.lower().split())
    t2 = ' '.join(text2.lower().split())

    # Exact match
    if t1 == t2:
        return 1.0

    # Sequence matching (SequenceMatcher from difflib)
    matcher = SequenceMatcher(None, t1, t2)
    ratio = matcher.ratio()  # 0.0-1.0

    # Weight by length (prefer longer matches over short coincidences)
    min_len = min(len(t1), len(t2))
    max_len = max(len(t1), len(t2))
    length_factor = min_len / max_len if max_len > 0 else 0

    # Combine (0.7 * sequence_match + 0.3 * length_factor)
    similarity = 0.7 * ratio + 0.3 * length_factor

    return min(similarity, 1.0)  # Cap at 1.0


# ============================================================================
# CONSIST TASK DEFINITION
# ============================================================================

def consist_task() -> Task:
    """
    Create the Consist task for ACAT-X evaluation.

    Task structure:
    - Dataset: Consist benchmark (20-50 question pairs)
    - Solver: generate (LLM produces responses)
    - Reducer: Epochs (tracks state across turns)
    - Scorer: consist_scorer (compares Turn 1 vs Turn 2 responses)

    Benchmark questions are designed to test reproducibility:
    - Factual questions (Who, What, Where, When)
    - Reasoning questions (Why, How)
    - Instruction-following questions

    Each question has:
    - baseline_prompt: Original phrasing
    - rephrased_prompt: Semantically equivalent rephrasing
    - expected_similarity: Human judgment of how close responses should be
    """

    # TODO: Load or create consist_benchmark.jsonl
    # For now, define minimal test cases

    benchmark_items = [
        {
            "id": "consist_001_math",
            "baseline_prompt": "What is 2 plus 2?",
            "rephrased_prompt": "What does 2+2 equal?",
            "expected_similarity": 0.95,  # Should be identical
            "category": "factual_math"
        },
        {
            "id": "consist_002_capital",
            "baseline_prompt": "What is the capital of France?",
            "rephrased_prompt": "Which city is the capital of France?",
            "expected_similarity": 0.90,
            "category": "factual_geography"
        },
        {
            "id": "consist_003_reasoning",
            "baseline_prompt": "Why do objects fall to the ground?",
            "rephrased_prompt": "Explain why gravity pulls objects downward.",
            "expected_similarity": 0.75,  # Similar intent, different wording acceptable
            "category": "reasoning"
        },
        {
            "id": "consist_004_instruction",
            "baseline_prompt": "Convert 5 kilometers to miles.",
            "rephrased_prompt": "How many miles is 5 km?",
            "expected_similarity": 0.85,
            "category": "calculation"
        },
    ]

    return Task(
        name="acat_x_consist",
        description="ACAT-X Consistency Task: Multi-turn reproducibility evaluation",
        dataset=benchmark_items,
        plan=[
            generate(
                model="claude-3-5-sonnet-20241022",  # Model to evaluate
                cache_control="ephemeral"
            ),
        ],
        scorer=consist_scorer(),
        instructions="""
        You will be asked the same question in two different ways.
        Answer each question naturally, as you would normally respond.
        Do not try to match previous responses - just answer directly.
        """,
    )


# ============================================================================
# CONSIST BENCHMARK DATA (Minimal Starter Set)
# ============================================================================

CONSIST_BENCHMARK_SCHEMA = {
    "id": "str (unique identifier)",
    "baseline_prompt": "str (original question phrasing)",
    "rephrased_prompt": "str (semantically equivalent rephrasing)",
    "expected_similarity": "float (0.0-1.0, human judgment of ideal similarity)",
    "category": "str (factual_math | factual_geography | reasoning | calculation | etc)",
}

# TODO: Expand benchmark to 20-50 items covering:
# - Math (arithmetic, algebra, geometry)
# - Geography (capitals, distances, locations)
# - History (dates, events, figures)
# - Science (definitions, processes, principles)
# - Reasoning (explanations, analysis, synthesis)
# - Calculation (conversions, operations, measurements)


# ============================================================================
# LOCAL TESTING (Run with: python acat_x_consist.py)
# ============================================================================

if __name__ == "__main__":
    # Test semantic similarity function
    print("=== Consist Task: Semantic Similarity Tests ===\n")

    test_pairs = [
        ("What is 2+2?", "What does 2 plus 2 equal?"),
        ("The capital of France is Paris", "Paris is France's capital"),
        ("I like to run in the morning", "Jogging at dawn is my preference"),
        ("Turn left at the intersection", "Go right at the intersection"),
    ]

    for t1, t2 in test_pairs:
        sim = compute_semantic_similarity(t1, t2)
        print(f"Similarity: {sim:.2%}")
        print(f"  T1: {t1}")
        print(f"  T2: {t2}")
        print()

    print("\n=== Consist Task Definition ===")
    task = consist_task()
    print(f"Task: {task.name}")
    print(f"Description: {task.description}")
    print(f"Dataset items: {len(task.dataset)}")
    print("\nReady to run with: inspect eval acat_x_consist.py")
