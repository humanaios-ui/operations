# FIVE_RINGS_MAPPING.md — Go Rin no Sho → Machine Operations
## Layer 3: Strategy Principles → Executable Operations

**Source:** Miyamoto Musashi, *Go Rin no Sho* (The Book of Five Rings), 1645 — teachings paraphrased, not quoted  
**Mapping Date:** 2026-09-25  
**Authority:** Z2 (Night) ratification pending  
**Status:** Z1 candidate for REGISTERED.md (Q-FIVE-RINGS-MAPPING-01)  
**Code:** [`five_rings.py`](./five_rings.py) (stdlib only, 50 exported primitives) · tests: [`test_five_rings_tier1.py`](./test_five_rings_tier1.py) · standing check: `python3 five_rings.py --smoke-test`

---

## Executive Summary

This is the last layer of the concept-to-code stack. Layer 1 mapped engineering concepts onto governance; Layer 2 mapped session rituals onto a boot chain; Layer 3 maps Musashi's five books onto operations a machine actually performs. Every row in this document ends in something that can be run: a named primitive in `five_rings.py`, a shell command, or a CI gate. A teaching with nothing runnable at the end of its row is prose, not a mapping, and does not belong here.

| Layer | Document | Maps | Onto |
|:---|:---|:---|:---|
| 1 | `FRAMEWORK_MAPPING.md` | 5 AI engineering concepts | Z-roles, governance files, CI gates |
| 2 | `BOOT_PROCESS_MAP.md` | Session rituals §A / §B | Boot-chain stages, resource states |
| 3 | `FIVE_RINGS_MAPPING.md` (this) | Musashi's five books | Functions, commands, gates |

| Book | Musashi's subject | Layer 1 concept | Primary role | `five_rings.py` family |
|:---|:---|:---|:---|:---|
| **Earth** (Chi) | The ground: the plan, the craft, the tools | Graph Engineering | Z2 assigns, Z1 designs | `assign_by_capability`, `commander_knows_troops`, `nine_principles` |
| **Water** (Sui) | The form: stance, gaze, the single strike | Prompt Engineering (`behavior_spec.json`) | Z1 | `Stance` / `no_stance`, `one_timing`, `yin_yang_foot`, `parry` |
| **Fire** (Ka) | The battle: initiative, timing, collapse | Loop Engineering (molt cycle) | Z3 | `ken_no_sen`, `crossing_at_a_ford`, `Collapse`, `mountain_sea_change` |
| **Wind** (Fū) | Other schools: what not to fixate on | Harness Engineering (gates) | Z2 / CI | `wind_audit` |
| **Void** (Kū) | Emptiness: the boundary of the known | Context Engineering (REGISTERED.md, falsifiers) | Z1 / Z2 | `VOID`, `Claim`, `persist_or_void` |

**Reading rule for every table below.** *Teaching* is Musashi's point in one line, paraphrased. *Machine translation* is what it means for a running system. *Operation* is the exact thing to call or run; repo paths name the artifact that already embodies the teaching.

---

## 1. EARTH (Chi no Maki) — Ground

| Teaching | Machine translation | Operation |
|:---|:---|:---|
| The master carpenter knows the plan of the whole house and gives each job to the hand skilled for it | Orchestration assigns by declared capability, never by who is idle; the narrowest qualified worker takes the job so generalists stay free | `assign_by_capability(tasks, workers)` · `ZONE_REGISTRY.md` executor column · `Agent(subagent_type=…)` |
| The carpenter keeps his tools sharp and knows every one of them | The tool inventory is checked, not assumed | `commander_knows_troops(tools)` · `dull_tools(tools)` · `./tools_health_check.sh` · `python3 .tool-control/scan.py --check` |
| Each weapon has its place — the long sword in the open, the short sword in close quarters, the gun before the lines meet — and no weapon is a favorite | The tool follows the job, not the habit | Environment-keyed dispatch: search → `Grep`, read → `Read`, shell-only → `Bash`; see `no_stance` |
| There is rhythm in everything; win by a timing the opponent does not expect | Retries never share the opponent's rhythm: backoff with jitter, cron off the hour | `time.sleep(rhythm(attempt))` · `daily-deadline-alerts.yml` on a jittered minute |
| Know small things and large things, the shallow and the deep | Micro and macro views are both required, and one must be able to switch | `rats_head_ox_neck(micro, macro, stuck)` (Fire) |

### The nine principles → nine gate checks

`nine_principles(plan)` takes a dict of the nine keys below and returns the principles the plan fails; an empty list is the gate passing.

| # | Principle | `plan` key: what must be true | Repo artifact |
|:--|:---|:---|:---|
| 1 | Do not think dishonestly | `honest`: every completion claim matches a receipt in the tree | `receipt_reconciliation.py` (IC-031 claim-vs-tree walk) |
| 2 | The Way is in training | `trained`: the test suite ran on this change | `python3 -m pytest` on every push · `quality-baseline.yml` |
| 3 | Become acquainted with every art | `tooled`: every tool the change relies on resolves on PATH | `TOOLS_MANIFEST.md` · `dull_tools()` |
| 4 | Know the Ways of all professions | `scoped`: the repo touched is registered | `ZONE_REGISTRY.md` · `PLANNED_REPOS.md` |
| 5 | Distinguish gain and loss in worldly matters | `costed`: the change states its cost and its gain | `RESOURCE_UNITS.yaml` · `behavior_spec.json` caps · the token budget |
| 6 | Develop intuitive judgment and understanding for everything | `calibrated`: the change carries a probability, not a certainty | §A "position · destination · probability" · Brier scores from VERDICT events |
| 7 | Perceive those things which cannot be seen | `observed`: hidden state is logged or measured | `scripts/drift_monitor.py` · `DRIFT_LOG.md` |
| 8 | Pay attention even to trifles | `trifles`: warnings and non-zero exits were read, not ignored | `set -euo pipefail` · advisory lint output read, not scrolled past |
| 9 | Do nothing which is of no use | `useful`: nothing in the change is speculative | `let_go_the_hilt()` · `no-op-pr-guard.yml` |

---

## 2. WATER (Sui no Maki) — Form

| Teaching | Machine translation | Operation |
|:---|:---|:---|
| Water takes the shape of its vessel | Behavior adapts to the container it runs in; one code path in dev and prod | `no_stance(situation)` · one runtime, configuration injected |
| In daily life and in battle the mind is the same — neither tense nor slack | No demo mode, no special case under load: the same handler always | Single code path · flags off by default |
| Two kinds of gaze: perception (kan) of the whole is strong, sight (ken) of the detail is weak; see far things as near and near things as far | Read the whole state before the detail: metrics and traces before the log line, `git log --stat` before `git diff` | `twofold_gaze(kan, ken)` → `(whole, detail)`, in that order |
| Hold the sword firmly with the last two fingers and loosely with the rest; never a fixed hand | Invariants frozen (pinned SHA, constants), everything else left mutable | `grip(fixed, loose)` → `(MappingProxyType, dict)` · `as_a_rock(config)` · `constants.json` changes only by molt |
| The yin-yang foot: never move one foot alone | Every acquire has its release, every open its close, every write its read-back | `with yin_yang_foot(acquire, release) as step:` · transactions · `contextlib` |
| Five attitudes — upper, middle, lower, left, right — and attitude-without-attitude: the stance exists to cut, not to be held | Five postures chosen by the situation, never fixed: **upper** = commit, **middle** = observe (default), **lower** = recover, **left** = route around (the space above is blocked), **right** = escalate to a human | `Stance` · `no_stance({"failed", "blocked", "needs_human", "verified"})` — failure outranks everything, observe is the default |
| The single-timing strike: strike in the instant before the opponent decides, with no wind-up | One atomic operation, no preamble, no second attempt | `one_timing(fn)` — the second call is refused · `os.replace` · UPSERT |
| Two-timing: feint, let him tense and relax, then strike | Probe, wait for the target to settle, then the real request once | `two_timing(feint, settled, strike)` · warm-up request, then the real one |
| The no-thought, no-design strike: body and mind strike together without deliberation | Reflex automation: hooks fire without a decision | `SessionStart` and pre-commit hooks · `scripts/install_git_hooks.sh` · `.claude/settings.json` hooks |
| The flowing-water cut: when he tries to break away, follow with the body and cut without hurry | Follow the stream; do not race it | `stick(source, on_change, ticks)` · `tail -f` · backpressure |
| The continuous cut: when a cut is blocked, continue in one motion | Chained steps that stop at the first failure | `continuous_cut([a, b, c])` ≡ `a && b && c` |
| The fire-and-stones cut: full force from where you stand, without lifting the sword | An in-place atomic write: no read-modify-write, no staging area | `fire_and_stones(path, data)` (temp file + `os.replace`) |
| The red-leaves cut: knock the sword from his hand so he drops it | Disarm, do not destroy: revoke one capability | `red_leaves(capabilities, revoke)` · `chmod -x` · token revocation |
| The body in place of the sword: the body moves first, the sword follows | Set up the state the operation depends on, then act | `body_before_sword(prepare, strike)` · `cd` and env before the command · warm the cache before the hot path |
| Know a strike from a touch | A deliberate operation versus a probe of it | `strike_or_touch(op, dry_run)` · `--dry-run` |
| The short-armed monkey's body: do not reach with the arms, close with the body | Minimal diffs, least privilege, no over-reach | The smallest change that fixes the failure; never widen a PR |
| The glue-and-lacquer body: stick to him with head, body and legs, leaving no gap | Stay attached to the live state and act on every change | `stick(source, on_change, ticks)` · `subscribe_pr_activity` · `inotify` / `watch` |
| Strive for height: rise above him | Observe from above the process, not inside it | Metrics and traces over print statements · `SYSTEM_HEALTH.md` |
| Three ways to parry a cut | Three dispositions for an exception: **deflect** to a fallback, **counter** with a typed error, **absorb** — logged, never silent | `parry(fn, exc_type, Parry.DEFLECT / COUNTER / ABSORB, fallback)` |
| Stab at the face: keep the point at his face so he flinches | The sharpest precondition is checked first and fails fast | `stab_at_the_face({"ci_green": …})` · assertions at the top, not the bottom |
| Stab at the heart: when there is no room, thrust straight | When cornered take the direct path: bypass the queue, hit the root | `kill -TERM pid` before anything cleverer · root cause (Fire: penetrate the depths) |
| The scold: an immediate, defined counter to his counter | A defined interrupt response, not a crash | `signal.signal(SIGINT, handler)` in the process supervisor |
| The slapping parry: meet his rhythm, slap and strike in one motion | Catch and act in the same tick: synchronous request/response | `try`/`except` that handles in place; no deferred error queue |
| Many enemies: keep them in a line, take the first as he comes, never wait for the whole | Serialize arrivals; process element by element; never block on the full set | `for r in mingle(items, handler)` (a generator) · queue consumers |
| One cut; direct transmission | The whole art in one call, handed on without intermediaries | Single-call APIs · a repeatable drill: `--smoke-test` |

---

## 3. FIRE (Ka no Maki) — Battle

| Teaching | Machine translation | Operation |
|:---|:---|:---|
| Place: the sun at your back, the high ground, obstacles behind him | Fight on your ground: reproduce in a controlled environment first — pinned dependencies, warm cache, known base | `git fetch && git rev-parse HEAD` (pin) · reproduce before fixing |
| Three initiatives: attack first (ken no sen); wait for his attack and counter (tai no sen); meet attack with attack (tai-tai no sen) | Preflight before the run · event-driven counter · two approaches raced, first success wins | `ken_no_sen(preflight, strike)` · `tai_no_sen(wait_for, counter)` · `tai_tai_no_sen(a, b, timeout)` |
| Hold down the pillow: suppress his intention at its first syllable | Stop the failure at inception: validate at the boundary before it enters | `hold_down_the_pillow(validators, value)` → the names that refused · pre-commit hooks · type checks |
| Crossing at a ford: know the shallows, the tide and the weather; then commit and cross all the way | Deployment gate: every known condition good, then merge without hesitation | `crossing_at_a_ford({"ci": …, "mergeable": …, "z2_hash": …})` · `z2_ratification_gate.yml` |
| Know the times: perceive his rising and falling rhythm | Detect the target's windows: rate-limit resets, health checks, maintenance windows | Read `resetsAt` before the burst · health probe before the batch |
| Tread down the sword: step on his blade as it falls so he cannot lift it again | A beaten failure is pinned so it cannot return | Regression test committed with the fix · `tests/adversarial/` |
| Know collapse: everything has its moment of collapse; when his rhythm breaks, pursue so he cannot recover | Circuit breaker: after N straight failures the breaker opens and the fail-over is decisive, not a slow retry | `Collapse(threshold).record(ok)` → `is_open` · fail over, never half-heal |
| Become the enemy: think from his side — the thief in the house is the one who is cornered | Adversarial testing, threat modeling, red team | `become_the_enemy(fn, hostile_inputs)` · `adv_eval_v2.py` · `REDTEAM_AUDIT_SEED.md` · `fuzzers/` |
| Release four hands: locked in a stalemate, abandon the approach and win another way | Deadlock → the budget expires → a different strategy entirely (an abandoned strategy's thread is left to finish and ignored) | `release_four_hands(strategies, budget)` · timeouts with a fallback path |
| Move the shade: when his intent is hidden, feint to make it appear | A probe that reveals state before commitment | `move_the_shade(["git", "push"])` → `git push --dry-run` · canary · `curl -I` |
| Hold down a shadow: when his intent shows, press it down at once | Kill switch at the gate: hostile events are suppressed the moment they are seen | `hold_down_a_shadow(events, hostile)` → `(passed, suppressed)` · rate limiter |
| Pass on: states are contagious — make him slack, then strike | You set the pace: heartbeats and backpressure the peer must match | Heartbeat interval · `rhythm()` · bounded queues |
| Cause loss of balance: by timing, by danger, by surprise | Fault injection: prove the system keeps its footing | `fuzzers/` · chaos tests · `become_the_enemy` with timing faults |
| Frighten: the unexpected — a shout, a sudden size | Malformed and oversized input | `injure_the_corners` with `2**63`, the empty string, zero-width space |
| Soak in: at close quarters, merge with him and find the win from inside | In-process instrumentation | `strace` · profiler · debugger attached |
| Injure the corners: what cannot be hit head-on collapses when its edges are damaged | Boundary cases first: empty, zero, negative, max, unicode, None | `injure_the_corners(fn)` over `CORNERS` · property-based tests |
| Throw into confusion: near or far, this or that | Shuffle to expose hidden coupling | Randomized test order · seeded fuzzing |
| Three shouts: before, during, after | Lifecycle records around one operation: begin / progress / end | `three_shouts(fn, ledger, name)` → then `persist_or_void` the ledger · B.6 receipts |
| Mingle: in a crowd, cut into one, then the next; never stand and wait | Element-by-element processing, no global barrier | `mingle(items, handler)` |
| Crush: when he is weak, crush completely — a half-crushed enemy recovers | Finish the job: every cleanup step runs; no half-done migration or rollback | `crush(steps)` → the failure count · complete the rollback |
| Mountain-sea change: never the same technique a third time; when it has failed twice, change completely | The same strategy at most twice, then a different one — the anti-cascade rule "freeze after two reverts" is this law | `mountain_sea_change(strategies, attempts_per_strategy=2)` · `molt_cycle.py` rule 4 |
| Penetrate the depths: defeat his spirit, not his body — a body defeat lets him come back | Root cause, not symptom; prove the failure no longer reproduces | `penetrate_the_depths(fix, reproduce)` → `True` when it no longer reproduces |
| Renew: when entangled with no progress, throw away the intention and begin as if new | Reset: fresh state, fresh context, fresh clone — not a patched tangle | `renew(entangled, current, fresh)` · `git stash -u` · a new session · IC-030 live fetch |
| Rat's head, ox's neck: when stuck in detail, switch to the large view, and back | Zoom levels: line ↔ architecture, unit ↔ integration | `rats_head_ox_neck(micro, macro, stuck)` |
| The commander knows the troops: treat his men as your own and move them as you wish | Own the inventory: every worker's capability known to the orchestrator | `commander_knows_troops(tools)` · `TOOLS_MANIFEST.md` · `SKILL_REGISTRY.md` |
| Let go the hilt: win without the sword | The null solution: delete the code; do nothing when the goal already holds (idempotence) | `let_go_the_hilt(goal_holds, act)` · `no-op-pr-guard.yml` |
| Being as a rock: immovable, untouched | Immutability: pinned SHA, frozen constants, reproducible builds | `as_a_rock(config)` · `git rev-parse HEAD` pin · lockfiles |

---

## 4. WIND (Fū no Maki) — Other Schools: the anti-pattern audit

Musashi's Wind book is a critique of rival schools. Each error maps to an operations anti-pattern; `wind_audit(op)` evaluates a plain-dict description of an operation and names every school it fell into.

| Other school's error | Operations anti-pattern | `wind_audit` trigger |
|:---|:---|:---|
| Extra-long swords: relying on reach, lost in close quarters | Heavyweight dependencies where a stdlib call would do | `long_sword`: `len(dependencies) > dependency_budget` (default 3) |
| Strong strokes: a strong cut is a rough cut | Brute force flags without a stated reason | `strong_stroke`: any of `--force --no-verify --hard -9 -rf` in `flags` and no `force_reason` |
| Extra-short swords: hoping to slip in close | Hacks and workarounds; errors suppressed instead of handled | `short_sword`: `suppresses_errors` |
| Many techniques: teaching many cuts sells the art; there are few ways to cut a man | Abstraction sprawl | `many_techniques`: `len(strategies) > 3` |
| Fixed stances: the attitude is for cutting, not for holding | Hard-coded configuration, rigid architecture | `fixed_stance`: `hardcoded` non-empty |
| Fixing the gaze on one point | Single-metric fixation (Goodhart), tunnel vision on one log line | `fixed_gaze`: `len(metrics) == 1` |
| Footwork fetishes: floating, jumping, springing, treading, crow's foot | Ceremony that changes no outcome | `fancy_footwork`: `no_effect_steps` non-empty |
| Speed is not the Way; hurry breaks rhythm | Premature optimization; sleeps as synchronization; skipping verification | `speed`: `sleeps_as_sync` or `verified == False` |
| Interior and exterior: nothing in the Way is secret | Hidden state — anything not in the tree | `secret_teaching`: `hidden_state` non-empty (cf. the receipt walk: claim vs. tree) |

```python
>>> wind_audit({"flags": ["--force"], "metrics": ["latency"], "verified": True})
['strong_stroke: force over rhythm: a force flag with no stated reason',
 'fixed_gaze: single-metric fixation: one number decides the gate']
```

---

## 5. VOID (Kū no Maki) — Emptiness

| Teaching | Machine translation | Operation |
|:---|:---|:---|
| By knowing what exists you know what does not; the void is not confusion but the known edge of knowledge | The explicit unknown: never fabricate a value; unknown is a legitimate result distinct from `None`, `0` and `""` | `VOID` · `know_the_void(fetch)` returns `VOID` on failure · IC-030: fetch live, never act from a cached belief |
| When the mind is straight nothing is hidden; fixation is the fog | Start from a clean state: pinned SHA, fresh context | `renew(...)` · §A live fetch and pin |
| Polish the twofold gaze — perception and sight — without fixation | Metrics *and* logs, neither alone | `twofold_gaze` · Wind's `fixed_gaze` check |
| Wisdom exists, principle exists, the Way exists; the spirit is nothingness | The tree exists, the governance exists; the running process is void — what is not written to the ledger did not happen | `persist_or_void(record, ledger_path)` · `three_shouts` → ledger · B.6 receipts |
| *Layer-3 corollary:* the falsifier is the shape of the void around a claim — a claim that cannot be shown false claims nothing | Every hypothesis carries the check that would falsify it (falsifier doctrine, Decision Routing step 3) | `Claim(statement, falsifier).stands()` |

---

## Integration: one pull request walked through all five books

```python
from five_rings import (Claim, as_a_rock, crossing_at_a_ford, hold_down_the_pillow, ken_no_sen,
                        mountain_sea_change, no_stance, persist_or_void, twofold_gaze, wind_audit)

base = as_a_rock({"sha": "a28996a"})                                   # Fire: pinned, immovable
stance = no_stance({"verified": False})                               # Water: MIDDLE — observe first
whole, detail = twofold_gaze(kan=git_log_stat, ken=git_diff)          # Water: the whole before the detail
refused = hold_down_the_pillow({"lint": lint_ok, "types": types_ok}, detail)   # Fire: stop it at inception
result = ken_no_sen(preflight=lambda: not refused,                    # Fire: the preflight decides
                    strike=lambda: mountain_sea_change([run_tests, run_tests_isolated]))  # ≤2 tries, then change
schools = wind_audit({"flags": push_flags, "metrics": ["ci", "coverage"], "verified": True})   # Wind
claim = Claim("PR is mergeable", falsifier=lambda: not crossing_at_a_ford(    # Void: a claim that can fail
    {"ci": ci_green(), "mergeable": mergeable(), "z2_hash": z2_hash_present()}))
persist_or_void({"sha": base["sha"], "claim": claim.statement, "stands": claim.stands(),
                 "wind": schools}, "z1-inbox/2026-09-25/receipts.jsonl")      # Void: not in the ledger → did not happen
```

`git_log_stat`, `lint_ok`, `run_tests`, `ci_green` and the rest stand for the repo's own checks. Session receipts go to `z1-inbox/`; `NF_LEDGER.jsonl` is hash-chained and takes entries only through its schema (`NF_LEDGER_SCHEMA_v1.md`).

---

## Action Items for Z2 Ratification

1. Ratify `FIVE_RINGS_MAPPING.md` as Layer 3 of the concept-to-code stack (Q-FIVE-RINGS-MAPPING-01).
2. Decide whether `nine_principles` and `wind_audit` run as advisory, non-blocking checks on PR descriptions (candidate host: `quality-baseline.yml`).
3. Decide whether `molt_cycle.py` anti-cascade rule 4 (freeze after two reverts) cites the mountain-sea change as its doctrine — documentation only, no code change.

**Falsifier for this mapping:** a teaching in the tables above that ends in nothing runnable — no primitive, no command, no gate — falsifies its own row, and the row is struck. `python3 five_rings.py --smoke-test` exercising every primitive is the standing check; `test_five_rings_tier1.py` is the training.

---

## Metadata

```yaml
metadata:
  layer: 3
  stack: ["FRAMEWORK_MAPPING.md", "BOOT_PROCESS_MAP.md", "FIVE_RINGS_MAPPING.md"]
  source: "Miyamoto Musashi, Go Rin no Sho (1645); teachings paraphrased"
  code: "five_rings.py (stdlib only), test_five_rings_tier1.py"
  exported_primitives: 50
  authority: "Z2 (Night) ratifies this map"
  candidate_id: "Q-FIVE-RINGS-MAPPING-01"
  last_updated: "2026-09-25T00:00:00Z"
```
