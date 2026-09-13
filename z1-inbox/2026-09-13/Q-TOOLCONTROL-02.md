# Candidate Block: Q-TOOLCONTROL-02 — Category Vocabulary & Backlog Clearance

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `1619e8b` (main, after PR #304)
**Branch:** `claude/tool-manifest-doc-registry-344ako`
**Phase:** 1 (control infrastructure — second pass)
**Status:** AWAITING Z2 RATIFICATION
**Follows:** Q-TOOLCONTROL-01 (merged as PR #304; still awaiting Z2 ratification)

---

## §A Position · Destination · Probability

**Position:** PR #304 landed the tool manifest and closed the doc-control drift holes. It
deliberately did **not** clean the corpus it exposed: 86 of 136 tools uncategorized, six more
carrying one-off category labels nobody chose deliberately, and 24 with no Builder v1.7 markers.
The operator directed that the backlog be cleared.

**Destination:** a closed category vocabulary, every tool placed in it, and the corresponding
gate rule promoted from advisory to blocking — so the backlog cannot refill.

**Probability:** **75%** that the `unclassified` count is still zero in 60 days. Held below 90%
because the rule now blocks: a contributor adding a tool must pick a category or the PR fails,
and the usual response to that friction is to widen the vocabulary rather than think. The
falsifier below tests exactly that.

---

## What was done

### 1 · A controlled category vocabulary (16 terms)

Defined in `CATEGORIES` in `.tool-control/scan.py`, with a one-line meaning for each. The
organizing rule: **a category says what a tool does to the system, not what subject it
concerns.** "ACAT" is a subject; `audit_tool` is a role. That distinction is what made the 86
classifiable at all — most of them are *about* ACAT, which is why nobody had labelled them.

`audit_tool` · `validation_tool` · `diagnostic_tool` · `security_gate_tool` · `governance_tool` ·
`calibration_tool` · `orchestrator_tool` · `pipeline_tool` · `connector_tool` ·
`infrastructure_tool` · `analytics_tool` · `research_tool` · `monitoring_tool` ·
`reporting_tool` · `dependency` · `template_tool`

`calibration_tool` was added rather than forced into `diagnostic_tool`: 14 tools
(`ci_predict_*`, `smag_*`, `nf_ledger*`, `lifecycle_predict`, `dimension_attribution`,
`scg_scorer`) pin and resolve predictions against outcomes. In a repository whose subject is
behavioural calibration, collapsing that into "diagnostics" would have hidden the largest
coherent family in the corpus.

### 2 · All 86 classified, and six one-offs normalized

Every assignment was made from the tool's module docstring, not its filename. Resulting spread:

| | | | |
|---|---|---|---|
| audit_tool 19 | infrastructure_tool 17 | calibration_tool 16 | validation_tool 14 |
| diagnostic_tool 13 | connector_tool 11 | security_gate_tool 10 | research_tool 9 |
| orchestrator_tool 6 | reporting_tool 5 | dependency 5 | pipeline_tool 4 |
| monitoring_tool 3 | governance_tool 2 | template_tool 2 | analytics_tool 1 |

Six tools declared labels outside any convention (`governance`, `site`, `discovery`,
`dispatch` ×2, `template`). Their `TOOL_CATEGORY` constants were normalized in source, so the
file and the manifest agree literally rather than through an alias. `CATEGORY_ALIASES` still maps
the old spellings, so an un-normalized file lands on a real category instead of failing the gate
for a name nobody chose.

### 3 · The gate ratchets

`unclassified`, and any category outside the vocabulary, are now **merge-blocking errors** — not
warnings. The rule was promoted only after its count reached zero, which is the principle worth
registering:

> **A finding is promoted to blocking only once its count reaches zero.** Shipping a rule the
> corpus already violates produces a gate everyone learns to route around.

A new tool with no `TOOL_CATEGORY` registers as `unclassified` and fails CI. That is the
mechanism by which the backlog stays cleared, and it is the friction the probability above
discounts.

### 4 · One vocabulary, not two

`tools/tool_scaffolder_v1_0.py` carried its own `TOOL_TYPES` list — seven entries, one of which
(`scaffolder_tool`) is in no vocabulary anywhere. A scaffolder that offers a category the gate
rejects generates tools that cannot land. It now reads `CATEGORIES` from the control system, with
a literal fallback for running outside a checkout. This is the same "one definition, not two that
disagree" rule applied in PR #304 to the tool/not-a-tool boundary.

### 5 · Five agents' Builder markers

`tools/agents/*_v1.py` already had `TOOL_NAME`, `TOOL_VERSION`, main guards and real
`run_smoke_test()` functions — they lacked only the declarative header line. Adding it states
something already true. All five still pass their own smoke tests.

**The other 19 were left alone deliberately.** Sixteen lack `TOOL_NAME`/`TOOL_VERSION`/a smoke
test outright. Writing sixteen stub smoke tests would turn the number green without testing
anything — gaming a metric I introduced two commits ago. Real smoke tests require understanding
each tool and belong in per-tool work, not in a registry pass.

---

## Registrable item surfaced

**`builder-lint`'s pass rate is computed over a self-selected corpus.**

`_is_builder_corpus_member` in `tools/builder_compliance_scanner_v1.0.py` admits a file only if
it **already contains** the string `Builder v1.7 compliant`. A tool that omits the header
entirely is therefore not counted as failing — it is not counted at all.

Verified directly: adding a header line to five agents moved the scanner from **111/112 (99.1%)**
to **116/117 (99.2%)** — the denominator rose by exactly five while the pass rate barely moved.
The five files that had been invisible became visible by opting in.

This is why 99.1% compliance coexisted with 24 registered tools carrying no markers, and it means
the gate's `≥ 0.90` threshold cannot detect the failure mode it most needs to: a tool that simply
never declares itself. **F candidate.** The manifest's `builder_markers` field covers the whole
registry and is the surface that *can* see an omission; the two numbers are not redundant, and my
own README in PR #304 understated this as "the corpora differ". Corrected there.

A secondary observation, not registered: `_is_directory_scan_target` excludes `/agents/`, but the
check runs against a scan-root-relative path with no leading slash, so the exclusion does not fire
under `--path tools/`. It happens to work in this change's favour. Not fixed here — it is that
tool's own bug and out of this pass's scope.

---

## §Review round — Copilot, 12 findings, all correct

Two were my own **subject-over-role** errors, i.e. exactly the mistake this vocabulary's
organizing rule exists to prevent, made while applying that rule:

| Tool | I assigned | What it does | Now |
|---|---|---|---|
| `governance_fetcher.py` | `governance_tool` | Fetches `GOVERNANCE.md` from GitHub raw, exposes MCP resources, local fallback. Operates no registry. | `connector_tool` |
| `agents/rentahuman_validation_bot_v1.py` | `validation_tool` | Recruits validators, tracks feedback, generates cohort reports and testimonials. Validates nothing. | `reporting_tool` |

I categorized both on a word in their name — "governance", "validation" — which is the failure
the rule names in its first sentence. `tool_scaffolder_v1_0.py` was a third: it is the literal
example in `template_tool`'s definition yet sat in `infrastructure_tool`, inherited from the old
`tools/README.md` table.

The most consequential finding was structural: **`extract()` discarded any declared category not
already in `CATEGORIES`**, so `build()` fell back to the curated value. A tool could set
`TOOL_CATEGORY = "made_up_thing"` and both `scan --check` and the new blocking rule would pass —
the rule was enforceable only against the manifest, not against the source of truth that outranks
it. Declarations are now preserved whenever they are identifier-shaped (template placeholders like
`{tool_type}` are still discarded, naming no category at all), so the validator gets to reject
them. Verified by declaring a junk category in a real tool and watching the gate fail.

The rest: the scaffolder's docstring still advertised the removed `scaffolder_tool` and the old
seven-type list; its `except Exception` would have silently restored the stale list on any
failure, recreating the very drift the indirection removes; `validate.py` let falsy-but-present
categories (`0`, `False`, `[]`) through; `tool-manifest.yml`'s header comment still described
categories as advisory at 93-of-143; the README misexplained the builder-lint rate change as
denominator-only when both terms rose; and its claim that all six one-off labels were normalized
in source was false — `meta_validator_tool` is docstring prose, not a declared constant.

---

## Falsifier

**Claim:** a closed vocabulary plus a blocking rule keeps every tool categorized, without the
vocabulary degrading into a synonym list.

**FALSE if:**

- A tool can be merged to `main` with `category: unclassified` or a category outside `CATEGORIES`, OR
- `CATEGORIES` grows past **20 entries** within 60 days, OR any added term is a synonym of an
  existing one rather than a distinct role, OR
- `infrastructure_tool` + `diagnostic_tool` combined exceed **35 of 137 (26%)**, up from today's
  30 of 137 (22%) — the two catch-all categories, whose growth is the tell that classification
  has become a formality, OR
- The `unclassified` rule is reverted to advisory to unblock a PR.

**Success criterion:** 60 days on `main` with zero `unclassified`, no reversion of the rule, and
`CATEGORIES` unchanged or grown only by a role genuinely absent today.

---

## Honest limitations, named

- **Categories were assigned from docstrings, not from reading each tool's behaviour.** A
  docstring that misdescribes its tool produces a wrong category that the gate will happily pass.
  Coverage is enforced; correctness is not.
- **The boundaries are judgment calls and some are arguable.** `audit_tool` vs `validation_tool`
  turns on "reports findings" vs "pass/fail", and several tools do both;
  `infrastructure_tool` (18) absorbed routers, hooks, servers and archive utilities that share
  little beyond not fitting elsewhere. These are the entries most worth a second opinion.
- **19 tools still carry no Builder markers**, and the registry now records that honestly rather
  than fixing it cosmetically.
- **Nothing changed status or gained an owner.** Of 137 tools, 136 are `status: draft` and one
  (`HAIOS-TOOL-012`, an archived analyzer) is `archived`; none has an `owner`. Both fields are the
  owner's acts under the rule this system already enforces, and 136 of them is a real queue that
  this pass does not touch.
- **The `pending_ratification` Zone 2 item is unchanged** — still `HAIOS-TOOL-088`, still awaiting
  the Z2 decision requested in Q-TOOLCONTROL-01.

---

## Deliverables

| File | Change |
|---|---|
| `.tool-control/scan.py` | `CATEGORIES` vocabulary + `CATEGORY_ALIASES`; declared categories normalized on read |
| `.tool-control/validate.py` | Rule 9 — category in vocabulary, `unclassified` blocks; smoke tests |
| `.tool-control/render.py` | Vocabulary table in the index; category titles |
| `.tool-control/README.md` | Vocabulary, ratchet principle, corrected builder-lint note |
| `tools-manifest.yaml` | 86 categories assigned; 0 unclassified |
| `TOOLS_MANIFEST.md` | Regenerated |
| `tools/{governance_fetcher, registry_site_generator_v1_0, repo_discovery_v1_0, slack_notifier, supabase_logger, tool_template}.py` | `TOOL_CATEGORY` normalized to the vocabulary |
| `tools/tool_scaffolder_v1_0.py` | Reads `CATEGORIES` instead of its own list |
| `tools/agents/*_v1.py` (5) | Builder v1.7 header + `TOOL_CATEGORY`; smoke tests still pass |
| `z1-inbox/2026-09-13/Q-TOOLCONTROL-02.md` | This block |

No tool's behaviour changed. Both gates green; all four self-tests pass; `repo_health` 100/100;
`builder-lint` 116/117 (99.2%), above its 0.90 threshold.

---

## Z2 Review Checklist

- [ ] The 16-term vocabulary is accepted, and `calibration_tool` is accepted as a distinct role
      rather than a subdivision of `diagnostic_tool`
- [ ] The ratchet principle is accepted as policy: a finding becomes blocking only at zero
- [ ] Normalizing six tools' `TOOL_CATEGORY` constants in source is accepted (behaviour unchanged)
- [ ] The `builder-lint` self-selected-corpus finding is routed — the `≥ 0.90` gate cannot see a
      tool that never declares itself
- [ ] Leaving 19 tools without Builder markers is accepted, rather than stub smoke tests
- [ ] Status and owner for 136 tools remain open owner work, deliberately untouched here
- [ ] Q-TOOLCONTROL-01's four items are still open and unaffected by this pass

---

## Summary

The backlog is cleared: 86 tools categorized, six one-off labels normalized, zero `unclassified`,
and the rule promoted from warning to blocking so it cannot refill. The scaffolder no longer
offers categories the gate rejects.

Clearing it surfaced one thing worth registering: the existing `builder-lint` gate reports 99.1%
over a corpus that only admits files already claiming compliance, so it cannot see a tool that
never opted in — which is precisely the failure the manifest was built to catch.

What was not done is named rather than papered over: 19 tools still lack Builder markers, and all
136 still lack a status and an owner.

**Ratification requested.**
