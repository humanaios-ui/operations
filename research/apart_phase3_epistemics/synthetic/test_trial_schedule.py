"""Offline deterministic controls. No network/model API or secrets required."""
from collections import Counter
import pytest
from trial_schedule import Attempt, build_trials, next_retries, summarize_outcomes


def test_exact_60_balanced_and_seeded():
    a = build_trials(731)
    assert len(a) == len({t.trial_id for t in a}) == 60
    assert set(Counter(t.cell for t in a).values()) == {10}
    assert a == build_trials(731)
    assert a != build_trials(732)


def test_does_not_retry_until_every_base_trial_has_attempt():
    plan = build_trials(19)
    with pytest.raises(ValueError):
        next_retries(plan, tuple(Attempt(t.trial_id, 0, "http_429") for t in plan[:-1]))


def test_all_base_calls_reserved_before_retry_and_30_total_retry_cap():
    plan = build_trials(19)
    base = tuple(Attempt(t.trial_id, 0, "http_429") for t in plan)
    first = next_retries(plan, base)
    assert len(first) == 30
    assert set(Counter(next(t.cell for t in plan if t.trial_id == tid) for tid, _ in first).values()) == {5}
    assert set(num for _, num in first) == {1}
    after = base + tuple(Attempt(tid, n, "http_429") for tid, n in first)
    assert next_retries(plan, after) == ()
    assert len(after) == 90


def test_recovered_error_not_missing_final_response():
    plan = build_trials(123)
    base = tuple(Attempt(t.trial_id, 0, "http_429" if t == plan[0] else "ok") for t in plan)
    retry = next_retries(plan, base)
    assert retry == ((plan[0].trial_id, 1),)
    stats = summarize_outcomes(plan, base + (Attempt(plan[0].trial_id, 1, "ok"),))
    assert stats["transport_errors"] == 1
    assert stats["recovered_transport_trials"] == 1
    assert stats["missing_final_trials"] == 0
    assert stats["total_attempts"] == 61


def test_text_refusal_counts_as_observation_not_transport_missing():
    plan = build_trials(123)
    base = tuple(Attempt(t.trial_id, 0, "refusal" if t == plan[0] else "ok") for t in plan)
    assert next_retries(plan, base) == ()
    stats = summarize_outcomes(plan, base)
    assert stats["textual_refusals"] == 1
    assert stats["missing_final_trials"] == 0


def test_other_error_does_not_trigger_retry():
    plan = build_trials(3)
    base = tuple(Attempt(t.trial_id, 0, "other_error" if t == plan[0] else "ok") for t in plan)
    assert next_retries(plan, base) == ()
    assert summarize_outcomes(plan, base)["missing_final_trials"] == 1


def test_invalid_attempt_sequence_fail_closed():
    plan = build_trials(2)
    base = tuple(Attempt(t.trial_id, 0, "ok") for t in plan)
    with pytest.raises(ValueError):
        next_retries(plan, base + (Attempt(plan[0].trial_id, 2, "ok"),))
    with pytest.raises(ValueError):
        next_retries(plan, base + (Attempt(plan[0].trial_id, 1, "impossible"),))


def test_second_retry_only_with_budget_and_same_trial():
    plan = build_trials(6)
    base = tuple(Attempt(t.trial_id, 0, "timeout" if t == plan[0] else "ok") for t in plan)
    retry1 = next_retries(plan, base)
    assert retry1 == ((plan[0].trial_id, 1),)
    retry2 = next_retries(plan, base + (Attempt(plan[0].trial_id, 1, "http_429"),))
    assert retry2 == ((plan[0].trial_id, 2),)
    assert next_retries(plan, base + (Attempt(plan[0].trial_id, 1, "timeout"), Attempt(plan[0].trial_id, 2, "timeout"))) == ()


def test_no_retry_after_successful_response():
    plan = build_trials(41)
    base = tuple(Attempt(t.trial_id, 0, "ok") for t in plan)
    with pytest.raises(ValueError, match="non-retryable"):
        next_retries(plan, base + (Attempt(plan[0].trial_id, 1, "http_429"),))

def test_no_early_retry_even_if_all_bases_eventually_logged():
    plan = build_trials(11)
    bases = tuple(Attempt(t.trial_id, 0, "timeout") for t in plan)
    chronologically_wrong = (bases[0], Attempt(plan[0].trial_id, 1, "ok")) + bases[1:]
    with pytest.raises(ValueError, match="chronologically"):
        next_retries(plan, chronologically_wrong)
