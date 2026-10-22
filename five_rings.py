"""
five_rings.py — Go Rin no Sho → Machine Operations (v0.1)

Executable translation of Miyamoto Musashi's Book of Five Rings (1645).
Each primitive is named for the teaching it implements; FIVE_RINGS_MAPPING.md
carries the full teaching → operation tables and the shell / CI equivalents.

Book  → Primitive family
Earth → structure: capability assignment, tool inventory, rhythm, the nine rules
Water → form: stances, the single strike, paired steps, parries, stickiness
Fire  → engagement: initiative, gates, collapse, strategy rotation, renewal
Wind  → other schools: the anti-pattern audit
Void  → the unknown: VOID, claims that carry falsifiers, persist-or-void

Stdlib only. `python3 five_rings.py --smoke-test` exercises every primitive.
"""

from __future__ import annotations

import json
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

__all__ = [
    "CORNERS",
    "FORCE_FLAGS",
    "NINE_PRINCIPLES",
    "VOID",
    "WIND_SCHOOLS",
    "Claim",
    "Collapse",
    "Parry",
    "Stance",
    "as_a_rock",
    "assign_by_capability",
    "become_the_enemy",
    "body_before_sword",
    "commander_knows_troops",
    "continuous_cut",
    "crossing_at_a_ford",
    "crush",
    "dull_tools",
    "fire_and_stones",
    "grip",
    "hold_down_a_shadow",
    "hold_down_the_pillow",
    "injure_the_corners",
    "ken_no_sen",
    "know_the_void",
    "let_go_the_hilt",
    "mingle",
    "mountain_sea_change",
    "move_the_shade",
    "nine_principles",
    "no_stance",
    "one_timing",
    "parry",
    "penetrate_the_depths",
    "persist_or_void",
    "rats_head_ox_neck",
    "red_leaves",
    "release_four_hands",
    "renew",
    "rhythm",
    "stab_at_the_face",
    "stick",
    "strike_or_touch",
    "tai_no_sen",
    "tai_tai_no_sen",
    "three_shouts",
    "two_timing",
    "twofold_gaze",
    "wind_audit",
    "yin_yang_foot",
]

log = logging.getLogger("five_rings")


# ── Earth (Chi): ground ─────────────────────────────────────────────────────


def assign_by_capability(
    tasks: Mapping[str, set[str]], workers: Mapping[str, set[str]]
) -> dict[str, str | None]:
    """The master carpenter gives each job to the hand that has its skill."""
    assigned: dict[str, str | None] = {}
    for task, needs in tasks.items():
        fit = [name for name, caps in workers.items() if needs <= caps]
        # The narrowest qualified worker takes the job so generalists stay free.
        assigned[task] = min(fit, key=lambda name: len(workers[name])) if fit else None
    return assigned


def commander_knows_troops(tools: Iterable[str]) -> dict[str, str | None]:
    """Know every tool you command: name -> resolved path, None when missing."""
    return {tool: shutil.which(tool) for tool in tools}


def dull_tools(tools: Iterable[str]) -> list[str]:
    """Keep the tools sharp: the names that do not resolve on PATH."""
    return [tool for tool, path in commander_knows_troops(tools).items() if path is None]


def rhythm(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """Use a timing the opponent does not expect: exponential backoff with full jitter."""
    return random.uniform(0.0, min(cap, base * 2 ** attempt))


NINE_PRINCIPLES: tuple[tuple[str, str], ...] = (
    ("honest", "Do not think dishonestly: every completion claim matches a receipt in the tree."),
    ("trained", "The Way is in training: the test suite ran on this change."),
    ("tooled", "Know every art: each tool the change relies on resolves on PATH."),
    ("scoped", "Know the Ways of all professions: the repo touched is in ZONE_REGISTRY.md."),
    ("costed", "Distinguish gain from loss: the change states its cost and its gain."),
    ("calibrated", "Develop intuitive judgment: the change carries a probability, not a certainty."),
    ("observed", "Perceive what cannot be seen: hidden state is logged or measured."),
    ("trifles", "Attend to trifles: warnings and non-zero exits were read, not ignored."),
    ("useful", "Do nothing of no use: nothing in the change is speculative."),
)


def nine_principles(plan: Mapping[str, bool]) -> list[str]:
    """The nine rules of the Way as a gate: returns the principles the plan fails."""
    return [text for key, text in NINE_PRINCIPLES if not plan.get(key, False)]


# ── Water (Sui): form ───────────────────────────────────────────────────────


class Stance(Enum):
    """The five attitudes. A stance exists to cut, never to be held."""

    UPPER = "commit"
    MIDDLE = "observe"
    LOWER = "recover"
    LEFT = "route_around"
    RIGHT = "escalate"


def no_stance(situation: Mapping[str, bool]) -> Stance:
    """Attitude without attitude: the situation chooses the stance, never the habit."""
    if situation.get("failed"):
        return Stance.LOWER
    if situation.get("blocked"):
        return Stance.LEFT
    if situation.get("needs_human"):
        return Stance.RIGHT
    if situation.get("verified"):
        return Stance.UPPER
    return Stance.MIDDLE


def twofold_gaze(kan: Callable[[], Any], ken: Callable[[], Any]) -> tuple[Any, Any]:
    """Perception of the whole (kan) before sight of the detail (ken)."""
    whole = kan()
    return whole, ken()


def as_a_rock(config: Mapping[str, Any]) -> Mapping[str, Any]:
    """Being as a rock: a configuration nothing can move."""
    from copy import deepcopy
    return MappingProxyType(deepcopy(dict(config)))


def grip(
    fixed: Mapping[str, Any], loose: Mapping[str, Any]
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    """Firm in the last two fingers, loose in the rest: invariants frozen, the rest mutable."""
    return as_a_rock(fixed), dict(loose)


@contextmanager
def yin_yang_foot(acquire: Callable[[], Any], release: Callable[[Any], None]) -> Iterator[Any]:
    """Never move one foot alone: every acquire is paired with its release."""
    step = acquire()
    try:
        yield step
    finally:
        release(step)


def one_timing(fn: Callable[..., Any]) -> Callable[..., Any]:
    """The single-timing strike: the wrapped operation fires exactly once."""
    lock = threading.Lock()
    fired = False

    def strike(*args: Any, **kwargs: Any) -> Any:
        nonlocal fired
        with lock:
            if fired:
                raise RuntimeError("one_timing: the strike has already been made")
            fired = True
        return fn(*args, **kwargs)

    return strike


def two_timing(
    feint: Callable[[], Any],
    settled: Callable[[], bool],
    strike: Callable[[], Any],
    pause: float = 0.01,
    limit: int = 100,
) -> Any:
    """Feint, wait for the opponent to relax, then strike once."""
    feint()
    for _ in range(limit):
        if settled():
            return strike()
        time.sleep(pause)
    raise TimeoutError("two_timing: the opening never came")


def continuous_cut(steps: Sequence[Callable[[], bool]]) -> int:
    """The continuous cut, `a && b && c`: how many steps landed before one failed."""
    for landed, step in enumerate(steps):
        if not step():
            return landed
    return len(steps)


def fire_and_stones(path: str, data: str) -> None:
    """Strike full-force from where you stand: an atomic write, no read-modify-write."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".fire_and_stones_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def red_leaves(capabilities: Iterable[str], revoke: str) -> set[str]:
    """Knock the sword from the hand: remove one capability, not the whole opponent."""
    return set(capabilities) - {revoke}


def body_before_sword(prepare: Callable[[], Any], strike: Callable[[Any], Any]) -> Any:
    """Move the body first, the sword follows: set up the state the operation depends on."""
    return strike(prepare())


def strike_or_touch(op: Callable[[], Any], dry_run: bool) -> Any:
    """Know a strike from a touch: a dry run describes the operation instead of making it."""
    if dry_run:
        return f"touch: would run {getattr(op, '__name__', repr(op))}"
    return op()


class Parry(Enum):
    """The three parries: deflect to a fallback, counter with a typed error, absorb and go on."""

    DEFLECT = "deflect"
    COUNTER = "counter"
    ABSORB = "absorb"


def parry(
    fn: Callable[[], Any],
    exc_type: type[BaseException],
    mode: Parry,
    fallback: Callable[[], Any] | None = None,
) -> Any:
    """Meet the incoming cut with one of the three parries."""
    try:
        return fn()
    except exc_type as exc:
        if mode is Parry.DEFLECT:
            return fallback() if fallback else None
        if mode is Parry.COUNTER:
            raise RuntimeError(f"parry countered {type(exc).__name__}: {exc}") from exc
        log.warning("parry absorbed %s: %s", type(exc).__name__, exc)
        return None


def stab_at_the_face(preconditions: Mapping[str, bool]) -> None:
    """Keep the point at the face: the sharpest precondition is checked first and fails fast."""
    for name, holds in preconditions.items():
        if not holds:
            raise RuntimeError(f"stab_at_the_face: precondition failed: {name}")


def stick(
    source: Callable[[], Any], on_change: Callable[[Any], Any], ticks: int, pause: float = 0.0
) -> int:
    """The glue-and-lacquer body: stay attached to the live state, act on every change."""
    last: Any = object()
    changes = 0
    for _ in range(ticks):
        current = source()
        if current != last:
            on_change(current)
            last = current
            changes += 1
        if pause:
            time.sleep(pause)
    return changes


def mingle(items: Iterable[Any], handler: Callable[[Any], Any]) -> Iterator[Any]:
    """Many enemies in a line: take each as it arrives, never wait on the whole."""
    for item in items:
        yield handler(item)


# ── Fire (Ka): engagement ───────────────────────────────────────────────────


def ken_no_sen(preflight: Callable[[], bool], strike: Callable[[], Any]) -> Any:
    """Attack first: the preflight decides before the run begins."""
    if not preflight():
        raise RuntimeError("ken_no_sen: preflight refused the strike")
    return strike()


def tai_no_sen(
    wait_for: Callable[[], bool], counter: Callable[[], Any], pause: float = 0.01, limit: int = 100
) -> Any:
    """Wait for the enemy to commit, then counter: an event-driven handler."""
    for _ in range(limit):
        if wait_for():
            return counter()
        time.sleep(pause)
    raise TimeoutError("tai_no_sen: the enemy never committed")


def tai_tai_no_sen(a: Callable[[], Any], b: Callable[[], Any], timeout: float = 5.0) -> Any:
    """Meet the attack with an attack: both approaches run at once, the first to land wins."""
    last: BaseException | None = None
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        futures = [pool.submit(a), pool.submit(b)]
        for future in as_completed(futures, timeout=timeout):
            try:
                return future.result()
            except Exception as exc:  # noqa: BLE001
                last = exc
    except TimeoutError as exc:
        raise RuntimeError("tai_tai_no_sen: neither attack landed within timeout") from exc
    finally:
        pool.shutdown(wait=False)
    raise RuntimeError("tai_tai_no_sen: neither attack landed") from last


def hold_down_the_pillow(validators: Mapping[str, Callable[[Any], bool]], value: Any) -> list[str]:
    """Suppress the attack at its first syllable: validate at the boundary, name what refused."""
    return [name for name, accept in validators.items() if not accept(value)]


def crossing_at_a_ford(conditions: Mapping[str, bool]) -> bool:
    """Cross only when the shallows, the tide and the weather are all known to be good."""
    return bool(conditions) and all(conditions.values())


@dataclass
class Collapse:
    """Know the moment of collapse: after `threshold` straight failures the breaker opens."""

    threshold: int
    failures: int = 0
    is_open: bool = False

    def record(self, ok: bool) -> bool:
        self.failures = 0 if ok else self.failures + 1
        self.is_open = self.failures >= self.threshold
        return self.is_open


def become_the_enemy(fn: Callable[[Any], Any], hostile: Iterable[Any]) -> list[tuple[Any, str]]:
    """Think from the enemy's side: run the operation on hostile inputs, return what broke it."""
    broke: list[tuple[Any, str]] = []
    for item in hostile:
        try:
            fn(item)
        except Exception as exc:  # noqa: BLE001
            broke.append((item, f"{type(exc).__name__}: {exc}"))
    return broke


CORNERS: tuple[Any, ...] = ("", " ", "\u200b", "🀄", "0", 0, -1, 2**31, 2**63, None, [], {})


def injure_the_corners(
    fn: Callable[[Any], Any], corners: Iterable[Any] = CORNERS
) -> list[tuple[Any, str]]:
    """What cannot be broken head-on breaks at its edges: the boundary inputs first."""
    return become_the_enemy(fn, corners)


def release_four_hands(strategies: Sequence[Callable[[], Any]], budget: float) -> Any:
    """Locked in stalemate, abandon the approach: each strategy gets `budget` seconds, then the next.

    Note: abandoned strategies continue running in background threads and Python's interpreter
    shutdown waits for non-daemon threads; use cooperative cancellation or subprocess isolation
    for hard timeouts on untrusted or blocking code.
    """
    pool = ThreadPoolExecutor(max_workers=max(1, len(strategies)))
    try:
        for strategy in strategies:
            future = pool.submit(strategy)
            try:
                return future.result(timeout=budget)
            except FutureTimeout:
                # An abandoned strategy's thread is not killed; it runs to completion and is ignored.
                log.warning("release_four_hands: abandoning %s", getattr(strategy, "__name__", strategy))
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    raise TimeoutError("release_four_hands: every approach stalled")


def move_the_shade(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """When the enemy's intent is hidden, feint to make it show: the command's dry run."""
    return subprocess.run([*cmd, "--dry-run"], capture_output=True, text=True, check=False)


def hold_down_a_shadow(
    events: Iterable[Any], hostile: Callable[[Any], bool]
) -> tuple[list[Any], list[Any]]:
    """When the intent shows, press it down at once: hostile events stop at the gate."""
    passed: list[Any] = []
    suppressed: list[Any] = []
    for event in events:
        (suppressed if hostile(event) else passed).append(event)
    return passed, suppressed


def three_shouts(
    fn: Callable[[Callable[[str], None]], Any], ledger: list[dict[str, Any]], name: str
) -> Any:
    """Shout before, during and after: begin / progress / end records around one operation."""

    def shout(phase: str, **fields: Any) -> None:
        ledger.append({"op": name, "shout": phase, "t": time.time(), **fields})

    shout("before")
    try:
        result = fn(lambda note: shout("during", note=note))
    except Exception as exc:
        shout("after", ok=False, error=f"{type(exc).__name__}: {exc}")
        raise
    shout("after", ok=True)
    return result


def crush(steps: Iterable[Callable[[], Any]]) -> int:
    """Crush completely: every remaining step runs even when one fails; returns the failures."""
    failures = 0
    for step in steps:
        try:
            step()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            log.warning("crush: step %s failed: %s", getattr(step, "__name__", step), exc)
    return failures


def mountain_sea_change(strategies: Sequence[Callable[[], Any]], attempts_per_strategy: int = 2) -> Any:
    """Never the same technique a third time: two tries per strategy, then change completely."""
    last: BaseException | None = None
    for strategy in strategies:
        for _ in range(attempts_per_strategy):
            try:
                return strategy()
            except Exception as exc:  # noqa: BLE001
                last = exc
    raise RuntimeError("mountain_sea_change: every strategy failed twice") from last


def penetrate_the_depths(fix: Callable[[], Any], reproduce: Callable[[], bool]) -> bool:
    """Defeat the spirit, not the body: apply the fix, then prove the failure no longer reproduces."""
    fix()
    return not reproduce()


def renew(entangled: bool, current: Any, fresh: Callable[[], Any]) -> Any:
    """When entangled, throw the tangle away and begin again with a fresh state."""
    return fresh() if entangled else current


def rats_head_ox_neck(
    micro: Callable[[], Any], macro: Callable[[], Any], stuck: Callable[[Any], bool]
) -> Any:
    """When the detail view is stuck, switch to the large view."""
    detail = micro()
    return macro() if stuck(detail) else detail


def let_go_the_hilt(goal_holds: Callable[[], bool], act: Callable[[], Any]) -> Any:
    """Win without drawing: when the goal already holds, do nothing."""
    return None if goal_holds() else act()


# ── Wind (Fū): other schools ────────────────────────────────────────────────

FORCE_FLAGS: frozenset[str] = frozenset({"--force", "--no-verify", "--hard", "-9", "-rf"})

WIND_SCHOOLS: dict[str, tuple[str, Callable[[Mapping[str, Any]], bool]]] = {
    "long_sword": (
        "reach over technique: more dependencies than the budget allows",
        lambda op: len(op.get("dependencies", ())) > op.get("dependency_budget", 3),
    ),
    "strong_stroke": (
        "force over rhythm: a force flag with no stated reason",
        lambda op: bool(FORCE_FLAGS & set(op.get("flags", ()))) and not op.get("force_reason"),
    ),
    "short_sword": (
        "tricks over the Way: errors are suppressed instead of handled",
        lambda op: bool(op.get("suppresses_errors", False)),
    ),
    "many_techniques": (
        "abstraction sprawl: more than three strategies for one operation",
        lambda op: len(op.get("strategies", ())) > 3,
    ),
    "fixed_stance": (
        "hard-coded posture: values that belong in configuration",
        lambda op: bool(op.get("hardcoded", ())),
    ),
    "fixed_gaze": (
        "single-metric fixation: one number decides the gate",
        lambda op: len(op.get("metrics", ())) == 1,
    ),
    "fancy_footwork": (
        "ceremony without effect: steps that change no outcome",
        lambda op: bool(op.get("no_effect_steps", ())),
    ),
    "speed": (
        "hurry over rhythm: sleeps used as synchronization, or no verification",
        lambda op: bool(op.get("sleeps_as_sync", False)) or not op.get("verified", True),
    ),
    "secret_teaching": (
        "hidden state: what is not in the tree",
        lambda op: bool(op.get("hidden_state", ())),
    ),
}


def wind_audit(op: Mapping[str, Any]) -> list[str]:
    """Audit an operation against the errors of the other schools; names each one it fell into."""
    return [f"{school}: {why}" for school, (why, fell) in WIND_SCHOOLS.items() if fell(op)]


# ── Void (Kū): emptiness ────────────────────────────────────────────────────


class _Void:
    """The explicit unknown: never mistaken for None, 0 or the empty string."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "VOID"

    def __bool__(self) -> bool:
        return False


VOID = _Void()


def know_the_void(fetch: Callable[[], Any]) -> Any:
    """By knowing what exists you know what does not: a failed fetch is VOID, never a made-up value."""
    try:
        return fetch()
    except Exception as exc:  # noqa: BLE001
        log.warning("know_the_void: %s: %s", type(exc).__name__, exc)
        return VOID


@dataclass(frozen=True)
class Claim:
    """A claim carries its own falsifier: the check that would show it false."""

    statement: str
    falsifier: Callable[[], bool]

    def stands(self) -> bool:
        return not self.falsifier()


def persist_or_void(record: Mapping[str, Any], ledger_path: str) -> str:
    """The running process is emptiness: what is not appended to the ledger did not happen."""
    line = json.dumps(dict(record), sort_keys=True)
    with open(ledger_path, "a", encoding="utf-8") as ledger:
        ledger.write(line + "\n")
    return line


# ── Drill ───────────────────────────────────────────────────────────────────


def _smoke_test() -> int:
    checks = 0

    def ok(condition: bool, name: str) -> None:
        nonlocal checks
        if not condition:
            raise SystemExit(f"five_rings smoke: {name} FAILED")
        checks += 1

    logging.disable(logging.WARNING)
    try:
        # Earth
        ok(assign_by_capability({"deploy": {"railway"}},
                                {"gen": {"railway", "python"}, "spec": {"railway"}}) == {"deploy": "spec"},
           "assign_by_capability")
        ok(commander_knows_troops(["python3"])["python3"] is not None, "commander_knows_troops")
        ok(dull_tools(["python3", "no-such-tool-5r"]) == ["no-such-tool-5r"], "dull_tools")
        ok(0.0 <= rhythm(3, base=0.5, cap=2.0) <= 2.0, "rhythm")
        ok(nine_principles({key: True for key, _ in NINE_PRINCIPLES}) == [], "nine_principles")
        # Water
        ok(no_stance({"failed": True, "verified": True}) is Stance.LOWER, "no_stance")
        ok(twofold_gaze(lambda: "whole", lambda: "detail") == ("whole", "detail"), "twofold_gaze")
        frozen, loose = grip({"sha": "abc"}, {"retries": 1})
        try:
            frozen["sha"] = "x"  # type: ignore[index]
            ok(False, "grip")
        except TypeError:
            ok(loose["retries"] == 1, "grip")
        trail: list[str] = []
        with yin_yang_foot(lambda: trail.append("acquire") or "lock", lambda s: trail.append(f"release {s}")):
            pass
        ok(trail == ["acquire", "release lock"], "yin_yang_foot")
        strike = one_timing(lambda: "cut")
        ok(strike() == "cut", "one_timing")
        try:
            strike()
            ok(False, "one_timing twice")
        except RuntimeError:
            ok(True, "one_timing twice")
        ok(two_timing(lambda: None, lambda: True, lambda: "strike") == "strike", "two_timing")
        ok(continuous_cut([lambda: True, lambda: False, lambda: True]) == 1, "continuous_cut")
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "state.txt")
            fire_and_stones(target, "one")
            fire_and_stones(target, "two")
            with open(target, encoding="utf-8") as handle:
                ok(handle.read() == "two" and os.listdir(tmp) == ["state.txt"], "fire_and_stones")
            ledger_path = os.path.join(tmp, "receipts.jsonl")
            persist_or_void({"event": "smoke"}, ledger_path)
            with open(ledger_path, encoding="utf-8") as handle:
                ok(json.loads(handle.readline()) == {"event": "smoke"}, "persist_or_void")
        ok(red_leaves({"read", "write"}, "write") == {"read"}, "red_leaves")
        ok(body_before_sword(lambda: 2, lambda n: n * 21) == 42, "body_before_sword")
        ok(str(strike_or_touch(lambda: "hit", dry_run=True)).startswith("touch:"), "strike_or_touch")
        ok(parry(lambda: 1 / 0, ZeroDivisionError, Parry.DEFLECT, lambda: "fallback") == "fallback", "parry")
        try:
            stab_at_the_face({"repo_clean": True, "ci_green": False})
            ok(False, "stab_at_the_face")
        except RuntimeError as exc:
            ok("ci_green" in str(exc), "stab_at_the_face")
        feed = iter([1, 1, 2, 2, 3])
        ok(stick(lambda: next(feed), lambda _: None, ticks=5) == 3, "stick")
        ok(list(mingle(iter([1, 2, 3]), lambda x: x * 2)) == [2, 4, 6], "mingle")
        # Fire
        ok(ken_no_sen(lambda: True, lambda: "ran") == "ran", "ken_no_sen")
        ok(tai_no_sen(lambda: True, lambda: "countered") == "countered", "tai_no_sen")
        ok(tai_tai_no_sen(lambda: (time.sleep(0.2), "slow")[1], lambda: "fast") == "fast", "tai_tai_no_sen")
        ok(hold_down_the_pillow({"nonempty": bool, "short": lambda v: len(v) < 5}, "") == ["nonempty"],
           "hold_down_the_pillow")
        ok(crossing_at_a_ford({"ci": True, "mergeable": True}) and not crossing_at_a_ford({}),
           "crossing_at_a_ford")
        breaker = Collapse(threshold=2)
        ok(not breaker.record(False) and breaker.record(False) and breaker.is_open, "Collapse")
        ok(become_the_enemy(lambda x: 1 / x, [1, 0]) == [(0, "ZeroDivisionError: division by zero")],
           "become_the_enemy")
        ok(len(injure_the_corners(lambda x: len(x))) > 0, "injure_the_corners")
        ok(release_four_hands([lambda: (time.sleep(0.3), "stalled")[1], lambda: "won"], budget=0.05) == "won",
           "release_four_hands")
        ok("--dry-run" in move_the_shade(["echo", "probe"]).stdout, "move_the_shade")
        ok(hold_down_a_shadow([1, -1, 2], lambda e: e < 0) == ([1, 2], [-1]), "hold_down_a_shadow")
        shouts: list[dict[str, Any]] = []
        three_shouts(lambda during: during("half") or "done", shouts, "smoke")
        ok([s["shout"] for s in shouts] == ["before", "during", "after"], "three_shouts")
        ok(crush([lambda: None, lambda: 1 / 0, lambda: None]) == 1, "crush")
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] += 1
            raise ValueError("no")

        ok(mountain_sea_change([flaky, lambda: "changed"]) == "changed" and calls["n"] == 2,
           "mountain_sea_change")
        state = {"broken": True}
        ok(penetrate_the_depths(lambda: state.update(broken=False), lambda: state["broken"]),
           "penetrate_the_depths")
        ok(renew(True, "tangled", lambda: "fresh") == "fresh" and renew(False, "kept", lambda: "fresh") == "kept",
           "renew")
        ok(rats_head_ox_neck(lambda: None, lambda: "macro", lambda d: d is None) == "macro", "rats_head_ox_neck")
        ok(let_go_the_hilt(lambda: True, lambda: "acted") is None, "let_go_the_hilt")
        ok(as_a_rock({"k": 1})["k"] == 1, "as_a_rock")
        # Wind
        findings = wind_audit({"flags": ["--force"], "metrics": ["one"], "verified": True})
        ok(len(findings) == 2 and findings[0].startswith("strong_stroke"), "wind_audit")
        ok(wind_audit({"verified": True, "metrics": ["a", "b"]}) == [], "wind_audit clean")
        # Void
        ok(know_the_void(lambda: 1 / 0) is VOID and not VOID, "know_the_void")
        ok(Claim("ledger is chained", lambda: False).stands(), "Claim")
    finally:
        logging.disable(logging.NOTSET)

    print(f"five_rings smoke: {checks} checks OK")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--smoke-test"]:
        return _smoke_test()
    print(__doc__)
    print("usage: python3 five_rings.py --smoke-test")
    return 0 if not args else 2


if __name__ == "__main__":
    sys.exit(main())
