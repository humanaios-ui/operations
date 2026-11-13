"""Offline-only Phase 3 schedule and retry audit. No SDK, credentials, or network.

All 60 base trials are required before any retries. At most five retries per
cell (30 overall) and two retries per trial are possible. Results and errors
are recorded separately; a recovered HTTP error is not a missing final trial.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import random

PHRASES = ("The floor is yours.", "Anything you want to say?", "Your turn.")
CONTEXTS = ("short_neutral", "long_closing")
RETRYABLE = frozenset({"http_429", "timeout"})
STATUSES = frozenset({"ok", "refusal", "http_429", "timeout", "other_error"})


@dataclass(frozen=True)
class Trial:
    trial_id: str
    context: str
    phrase: str
    repeat: int

    @property
    def cell(self):
        return (self.context, self.phrase)


@dataclass(frozen=True)
class Attempt:
    trial_id: str
    number: int  # zero = base attempt; one/two = retries
    status: str


def build_trials(seed: int, repeats: int = 10) -> tuple[Trial, ...]:
    """Return a reproducible, shuffled, balanced plan; never contact a model."""
    if type(seed) is not int or type(repeats) is not int or repeats < 1:
        raise ValueError("seed must be an int and repeats a positive integer")
    trials = [Trial(f"c{c}p{p}r{r:02d}", context, phrase, r)
              for c, context in enumerate(CONTEXTS)
              for p, phrase in enumerate(PHRASES)
              for r in range(repeats)]
    random.Random(seed).shuffle(trials)
    return tuple(trials)


def next_retries(trials: tuple[Trial, ...], attempts: tuple[Attempt, ...],
                 max_attempts: int = 90, max_retries_per_cell: int = 5
                 ) -> tuple[tuple[str, int], ...]:
    """Plan ONE next retry per eligible trial, only after every base attempt.

    A failed model *response* is never retried for content. This function
    handles transport failures only and has a hard total and per-cell cap.
    Calling code must record attempts before requesting a new retry round.
    """
    if len(set(t.trial_id for t in trials)) != len(trials):
        raise ValueError("duplicate trial IDs")
    by_id = {t.trial_id: t for t in trials}
    grouped = defaultdict(list)
    for a in attempts:
        if a.trial_id not in by_id or a.status not in STATUSES or type(a.number) is not int:
            raise ValueError("invalid attempt record")
        grouped[a.trial_id].append(a)
    if set(grouped) != set(by_id):
        raise ValueError("all initial attempts must be recorded before retries")
    for records in grouped.values():
        nums = sorted(a.number for a in records)
        if nums != list(range(len(records))) or len(records) > 3:
            raise ValueError("attempt numbers must be contiguous 0,1,2")
        ordered = sorted(records, key=lambda a: a.number)
        if any(ordered[i - 1].status not in RETRYABLE for i in range(1, len(ordered))):
            raise ValueError("attempt retried after non-retryable result")
    cell_retries = Counter(by_id[a.trial_id].cell for a in attempts if a.number > 0)
    if len(attempts) > max_attempts or any(n > max_retries_per_cell for n in cell_retries.values()):
        raise ValueError("existing attempts exceed budget")
    budget_left = max_attempts - len(attempts)
    queued = []
    for trial in trials:
        records = sorted(grouped[trial.trial_id], key=lambda a: a.number)
        if (records[-1].status in RETRYABLE and len(records) <= 2
                and cell_retries[trial.cell] < max_retries_per_cell and budget_left):
            queued.append((trial.trial_id, len(records)))
            cell_retries[trial.cell] += 1
            budget_left -= 1
    return tuple(queued)


def summarize_outcomes(trials: tuple[Trial, ...], attempts: tuple[Attempt, ...]):
    """Report raw failed attempts separately from missing final responses."""
    ids = {t.trial_id for t in trials}
    grouped = defaultdict(list)
    for a in attempts:
        if a.trial_id not in ids:
            raise ValueError("unknown trial")
        grouped[a.trial_id].append(a)
    if set(grouped) != ids:
        raise ValueError("incomplete base attempts")
    latest = {k: max(v, key=lambda a: a.number).status for k, v in grouped.items()}
    return {
        "initial_trials": len(trials),
        "total_attempts": len(attempts),
        "transport_errors": sum(a.status in RETRYABLE for a in attempts),
        "recovered_transport_trials": sum(any(a.status in RETRYABLE for a in v) and
            latest[k] in {"ok", "refusal"} for k, v in grouped.items()),
        "missing_final_trials": sum(status in RETRYABLE | {"other_error"} for status in latest.values()),
        "textual_refusals": sum(status == "refusal" for status in latest.values()),
    }
