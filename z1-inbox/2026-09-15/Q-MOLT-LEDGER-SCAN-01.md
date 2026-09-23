---
id: "Q-MOLT-LEDGER-SCAN-01"
name: "Molt verification findings scan — the molt lifecycle writes no permanent record, and the anti-cascade rules that would read it are wired nowhere"
status: CANDIDATE
class: MIXED
date_registered: "2026-09-15"
date_origin: "2026-09-15"
session_registered: "S-091526-01-molt-classifier"
zone2_ratification: null
tags: ["molt", "nf-ledger", "anti-cascade", "audit-false-pass", "governance-calibration", "findings-scan"]
related: ["F-64", "IC-041", "IC-050", "H-GOV-01"]
superseded_by: null
source_pr: "humanaios-ui/operations#343"
source_issue: "humanaios-ui/operations#344"
---

# Candidate Block: Q-MOLT-LEDGER-SCAN-01 — molt state exists in `constants.json` and nowhere else

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-15
**Pinned SHA:** `3345688` (main); `REGISTERED.md` blob `5ad15c72ae35456866a36d69e98d846d99c45e1d`
**Time (P22 verified):** 2026-09-15 17:27 CDT / 22:27 UTC via `bash_tool`
**Status:** AWAITING Z2 RATIFICATION

Produced by `humanaios-findings-scan` run standalone during S-091526-01. Scan completeness:
**1 F / 5 IC / 1 H / 5 NM / 1 DUPLICATE from 14 substantive observations.** Every claim below was
executed against the tree at the pinned SHA, not read from documentation.

**Version drift flag:** the findings-scan skill pins `REGISTERED.md` at F-18..F-45, IC to IC-031,
H-RCO-01. Live register is F-18..F-64 (41 F entries) and IC-001..IC-059 (42 IC entries). Taxonomy
and front-matter schema appear unchanged, so the scan proceeded; flagged per the skill's own
"Pinned version" clause.

---

## F-CAND-SELF-EXEMPT-RULE-01 — a path-scoped control that omits its own definition file is silently self-amendable

- **claim:** A governance rule scoped by a path list, whose own definition file is absent from that
  list, can be rewritten by a change that measures below the rule's own detection threshold. Observed
  live: `GATE_PATHS` in `tools/molting_protocol_diff_v1_0.py` omitted that same file, while a source
  comment in it asserted that changing either rule list "is itself a Tier-2 change." The rule and its
  documentation disagreed, and the documentation was the half a reader would trust.
- **class:** F (novel, evidenced, generalizable). Generalizes to every path-scoped control in the
  repository — `CODEOWNERS` path lists, `.doc-control` registry paths, workflow `paths:` filters.
- **evidence_tier:** VERIFIED-LIVE — PR #343; defect present in `d27e480`, corrected in `211459a`;
  review thread `r4017382623`. Post-fix, the check's own comment on #343 lists
  `tools/molting_protocol_diff_v1_0.py -> Tier 2 (matched tools/molting_protocol_diff_v1_0.py)`.
- **detection:** caught by an external review bot after CI was fully green (21 checks, zero failures).
  No gate in this repository would have caught it, because the omission makes the rule agree with
  itself.
- **promotion gate:** confirmed on ≥2 further independent path-scoped controls in this repository that
  omit their own definition file, with the omission shown to permit an undetected self-edit. One
  instance is an anecdote.
- **status:** OPEN.

---

## IC-CAND-TIER-RULE-ABSENT-PATHS-01 — rule targets paths absent from the repository (EXTENSION of IC-041)

- **claim:** The molt-tier handoff spec defined the Tier-2 gate set as `tools/validate.py` and
  `tools/ratify.py`. Neither exists. The gates are `.z1-control/{ratify,validate,render}.py`. Shipped
  verbatim, every change to the Z2 signing path would have measured **Tier 0 by construction**.
- **class:** audit-false-pass — structurally identical to IC-041 ("CI check targets a path absent from
  the repo; reports PASS by construction"), one layer up: a classification rule rather than a check.
- **evidence_tier:** VERIFIED-LIVE — `ls` on both spec paths fails at the pinned SHA; both
  `.z1-control` paths resolve.
- **detection:** caught pre-merge during implementation; corrected in `d27e480`, which retains the spec
  paths for portability and adds the repo-real ones marked `REPO`.
- **consequence:** none occurred. **Z2 may prefer NM on that basis.** Filed as IC because the defective
  spec is a ratified handoff presumed in use for sibling repos, which is canonical-facing.
- **Fix → Principle P3.**
- **status:** OPEN (disposition IC-vs-NM explicitly deferred to Z2).

---

## IC-CAND-MOLT-LEDGER-ABSENT-01 — the molt lifecycle writes no permanent record

- **claim, limb (a):** The only live molt — `f7a49f667c09f1f6` (Q-RBE-01, ratified Night
  2026-09-13T18:15:00Z, covering `QUEUE_SCORING_MODE` impact→resource and `UNPRICED_ROW_POLICY`
  ALLOWED→REFUSED_TO_START, 28-day window closing 2026-10-11) has **no NF_LEDGER row**, though
  `MOLT_STATE.md` specifies that RATIFIED creates one with `outcome="MEASURING"` and an
  `anti_cascade_check` block. `MOLT_RATIFIED` appears in exactly one file repository-wide:
  `constants.json`.
- **claim, limb (b):** **No molt ledger file exists at all.** `tools/molt_cycle_tier0_v0_1.py` defaults
  to `--molt-ledger molt_events.jsonl`, which is not in the repository, and derives `open_molts` from
  it — reading **0 while a molt is live**. `molt_ledger.py` is a module, not a ledger.
- **class:** record-integrity — state asserted in a working file and absent from the append-only record
  that governs it.
- **evidence_tier:** VERIFIED-LIVE — `ledgers/NF_LEDGER.jsonl` holds 165 rows of types PIN 106 /
  TOKEN 58 / OPEN 1; the keys `molt_id`, `outcome`, `constant` and `anti_cascade_check` appear nowhere
  in the file; `constants.json` is the sole occurrence of `MOLT_RATIFIED`.
- **consequence:** when the window closes on 2026-10-11 there is no ledger row to measure the molt
  against, and no mechanical basis for KEEP or REVERT.
- **Fix → Principle P3.**
- **status:** OPEN.

---

## IC-CAND-ANTICASCADE-UNWIRED-01 — the anti-cascade rules are enforced nowhere (EXTENSION of IC-050)

- **claim:** The five anti-cascade rules exist in two implementations and neither executes.
  Root `z2_ratification_gate.yml` carries jobs `[nf_ledger_hash_chain, anti_cascade_rules,
  falsifier_lint, schema_consistency, gate_decision]` but sits at the repository root, **not** in
  `.github/workflows/`, so GitHub never parses it. The live `.github/workflows/z2_ratification_gate.yml`
  carries `[z2-gate, config-lint]` and no anti-cascade job. `ci_gates.py` implements all five rules and
  is invoked by no workflow.
- **compounding:** both implementations read `open_molt_count` / `outcome == 'MEASURING'` from
  NF_LEDGER. Even once wired they would compute **0** against IC-CAND-MOLT-LEDGER-ABSENT-01 and pass
  vacuously. K=3 is presently a documented rule with no mechanism behind it.
- **class:** blocker-gate-not-enforced (IC-050 sibling), compounded by audit-false-pass (IC-041).
- **evidence_tier:** VERIFIED-LIVE — job lists parsed from both files with PyYAML at the pinned SHA;
  `grep -rn ci_gates .github/workflows/*.yml` returns nothing.
- **Fix → Principle P3.**
- **status:** OPEN.

---

## IC-CAND-MOLTCYCLE-TIER0-BROKEN-01 — a governance tool broken by schema drift, undetected because nothing runs it

- **claim:** `tools/molt_cycle_tier0_v0_1.py` raises `AttributeError: 'str' object has no attribute
  'get'` at line 95 against the current `constants.json`. It iterates `for name, c in consts.items()`
  and calls `c.get("trigger")`, assuming a flat `{name: {...}}` map; the live schema is
  `{$schema, schema_version, description, constants: [...], metadata}`, so the first value it meets is
  a string. Its `--nf` default is also stale (`NF_LEDGER.jsonl`; actual `ledgers/NF_LEDGER.jsonl`).
- **evidence_tier:** VERIFIED-LIVE — reproduced with correct `--nf`/`--events` paths; same traceback.
  Root `molt_cycle.py --read-only --nf ledgers/NF_LEDGER.jsonl` does run and reports 7 constants,
  `nf_resolved: 0`, `brier_overall: null`, and no molt count.
- **detection:** undetected because no workflow invokes it — compounding
  IC-CAND-ANTICASCADE-UNWIRED-01.
- **Fix → Principle P3.**
- **status:** OPEN.

---

## IC-CAND-SEED-INTAKE-LABELS-01 — shipped public intake promises routing that does not exist

- **claim:** `.github/ISSUE_TEMPLATE/seed-amendment.md` is live in `main` and declares
  `labels: ["seed", "amendment"]`. Neither label exists in the repository. Every constitution amendment
  filed through the public path arrives unlabelled.
- **consequence:** currently active and public-facing. The open-process intake that Seed Constitution
  Principle 9 depends on loses its routing silently.
- **evidence_tier:** VERIFIED-LIVE — `get_label` returns not-found for both names; the template is in
  `main` at the pinned SHA.
- **adjacent:** three further labels named by issue #344's spec (`candidate`, `needs-z2-hash`,
  `seed-constitution`) also do not exist. **Five labels total.** This session has no label-creation
  capability, so none were created.
- **Fix → Principle P3.**
- **status:** OPEN.

---

## H-CAND-MOLT-TIER-UNDERCLAIM-01 — authors under-claim molt tier when the tier is self-declared

- **null:** an author's `molt_tier_claimed` equals the path-measured tier; self-declaration is unbiased.
- **falsification:** >5% of PRs over a rolling 30-day window show `measured − claimed > 1`. Directional
  by design — a two-level over-claim is not a trip, because over-claiming costs caution while
  under-claiming is how a gate change merges labelled "not a molt."
- **primary metric:** under-claim rate = (PRs with `measured − claimed > 1`) / (total PRs), from the
  classifier's gap records.
- **promotion gate:** ≥30 PRs measured through `.github/workflows/molt-tier-check.yml` before the rate
  is read as signal; at that point the check is promoted from advisory to blocking, or the falsifier
  stands.
- **dependency:** conditional on PR #343 merging — the falsifier exists only in that diff.
- **status:** OPEN.

---

## DUPLICATE — cited, not proposed

`nf_resolved: 0`; 165 NF_LEDGER rows of types PIN 106 / TOKEN 58 / OPEN 1, no RESOLVE of any kind →
covered exactly by **F-64** (*Assurance Is Accumulating; Evidence Is Not*, ratified Night ·
2026-09-13 · Q-RBE-01 acceptance). Same counts, same file. Not re-proposed.

Worth Z2's attention: F-64 and molt `f7a49f667c09f1f6` were ratified in the **same Z2 act**. That act
registered the finding and wrote no ledger row for the molt — which is
IC-CAND-MOLT-LEDGER-ABSENT-01 observed at its moment of origin.

---

## NM low-friction captures (expire after 3 audits → `DRIFT_LOG.md`)

1. `constants.json` `metadata.acceptance_gate` still reads "constants: 3 … when all 3 constants have
   molt_id"; there are 7, two carrying molt_ids. Both molted constants' `notes` still read as though
   unsigned ("inert until Z2 signs", "Held at `ALLOWED` until then") while their values show the molt
   applied. Stale prose — and the direct cause of the open-molt-count ambiguity this scan resolved.
2. Two live intake channels for constitution amendments (public issue template vs. the `z1-inbox`
   class proposed in #344). AMBIGUITY, not a finding — routed to #344 for Z2 to name the canonical one.
3. `tools/molting_protocol_diff_v1_0.py` sat in the tool manifest with a `run()` body that was a `TODO`
   returning nothing, under a `purpose` string describing behavior it never had. Manifest
   `status: draft` was honest about maturity; only the purpose string was aspirational. Below the IC bar
   on that basis. Corrected in #343.
4. `ui/Z2_RATIFICATION_GUIDE.md` documents a Class Filter (F/H/IC/P) the shipped reviewer does not
   implement. Already tracked as gap 5 on issue #344.
5. GitHub's legacy commit-status API returns `"pending"` with zero statuses on this repository (it uses
   check runs). Tooling quirk, no governance consequence; noted so a future session does not misread CI.

---

## Proposed preventions (Z2 to accept, edit or reject — none built here)

Each changes a gate, a ritual or a ledger, which are Z2's, not Z1's.

**(1) Wire the anti-cascade job.** Move or re-create root `z2_ratification_gate.yml`'s
`anti_cascade_rules` job into `.github/workflows/`, advisory first. Advisory matters here: against an
empty molt ledger it will report 0 open molts, and the value of the first runs is that the emptiness
becomes *visible* rather than passing silently.

**(2) Give the molt lifecycle a ledger.** Either create `molt_events.jsonl` and have ratification
append a `MOLT` event, or re-point `tools/molt_cycle_tier0_v0_1.py` at NF_LEDGER and extend the NF
event schema with the molt event types. Z2 picks which — the two ledgers have different hash chains and
this decides where molt state lives permanently. Backfill `f7a49f667c09f1f6` either way, so the
2026-10-11 window close has something to measure.

**(3) Repair `molt_cycle_tier0_v0_1.py` against the current `constants.json` schema** and add it to the
`quality-baseline` pytest list, so schema drift breaks a test rather than lying dormant.

**(4) Resolution as a standing ritual step — see the appendix below.** This is the one with the widest
blast radius and the one this block most wants a ruling on.

**(5) Create the five missing labels** (`seed`, `amendment`, `candidate`, `needs-z2-hash`,
`seed-constitution`). The first two are already promised to the public by a template in `main`.

---

## Appendix — mending `nf_resolved: 0`

F-64 registers the gap; it does not say how to close it. Three facts, all executed at the pinned SHA:

- **The tooling already exists.** `tools/nf_ledger_v0_1.py` has a full `resolve` subcommand:
  `resolve <ledger.jsonl> <token_id> YES|NO --by <who> --source <tree read sha / path>`. It already
  enforces the discipline that matters — *"resolution is by tree read: the RESOLVE event must carry a
  `source` (sha or path); no source → refused"* — and refuses to resolve a token still in
  `PENDING_Z2_DATE`. `score` computes Brier per predictor over RESOLVED pins only. **This is unrun
  tooling, not missing tooling.**
- **~~48 Z1 pins are scoreable right now.~~ CORRECTED 2026-09-16 (P2, in place): 7 were ripe, not 48.**
  The earlier figure misread the tool. `scoreable-now` is computed as `p["scoreable"] and p["p"] is not
  None` — "the pin is well-formed and its token carries a Z2 date." It says **nothing** about whether
  the measurement window has closed. The binding rule is the spec's own resolver in
  `ledgers/mesh_pins_090826.json`: *"tree read of the named repo at date+3 (UTC); missing file = NO;
  final read 2026-10-04."* At 2026-09-16 that made **7** tokens ripe and 51 not yet (earliest
  2026-09-18). Resolving the other 51 would have been scoring predictions before their windows closed —
  manufacturing the exact data this block warns against. The error is left visible rather than
  silently overwritten; it is itself an instance of reading a tool's column name instead of its
  definition.
- **21 tokens are blocked on Z2, not on Z1.** They sit in `PENDING_Z2_DATE` and cannot be resolved until
  a `date` event signed by Z2 lands. That is a genuine ratifier dependency and it is the mechanism
  F-62 (*Ratification Attention Is the Binding Constraint*) predicts.

**Does it need to be a regular part of our methods? Yes, and there is currently no hook anywhere.**
`SESSION_RITUALS.md` contains no reference to `NF_LEDGER`, `resolve`, or `brier` — the close ritual
(§B.0 empirical verification, §B.6 receipt reconciliation, findings scan, handoff) never touches the
calibration ledger. The register accumulates forecasts and the ritual never spends them.

The structural point is that resolution is only cheap **at the window close**. A pin resolved six months
late needs the tree state of six months ago reconstructed; resolved on time it is one `git show`. Every
session that does not resolve raises the cost of every future resolution — which is exactly how 75 pins
reached zero resolutions without anyone deciding to let that happen.

**Proposed §B addition (Z2's call, not built):** a `B.7 — Ledger Resolution` step, after B.6:

```
B.7 Ledger Resolution
  1. python3 tools/nf_ledger_v0_1.py status ledgers/NF_LEDGER.jsonl
  2. For every token DATED with a date now past and state != RESOLVED:
       read the tree; resolve YES/NO with --source pinning the sha or path read.
       Cannot determine from a tree read → leave unresolved and raise it as a
       RECEIPT-GAP; do not guess. An unresolved pin is honest, a guessed one is not.
  3. python3 tools/nf_ledger_v0_1.py score ledgers/NF_LEDGER.jsonl
       Brier undefined is a reportable state, not a failure to hide.
  4. Tokens in PENDING_Z2_DATE are a Z2 queue item, not a Z1 blocker — carry the
       count into the handoff so the ratifier dependency stays visible.
```

Paired with it, a **backlog pass**: the 48 scoreable-now Z1 pins resolved in one sitting, as its own
work order priced in the constraint unit. It is the single action that would move `nf_resolved` off
zero and give F-64 its first evidence.

Deliberately **not** proposed: auto-resolution. A pin resolved by a script that infers the outcome from
anything other than a tree read manufactures calibration data, which is worse than having none — it is
IC-031's cost class pointed at the calibration programme itself.

### Executed — 2026-09-16, first resolution pass in the ledger's history

Seven ripe tokens resolved **NO** by tree read of `empirica-practice-mesh` @
`f2d37a87ec8da924de4c15319528e8e236b02aa2`, each RESOLVE carrying that sha plus the practice path as
its `source`:

| token | due | read-at | p | outcome |
|:--|:--|:--|:--|:--|
| `T-empirica-outreach-01` | 2026-09-06 | 09-09 | 0.6 | NO |
| `T-grok-crossref-01` | 2026-09-08 | 09-11 | 0.5 | NO |
| `T-grok-crossref-02` | 2026-09-10 | 09-13 | 0.45 | NO |
| `T-empirica-foundation-evaluator-01` | 2026-09-12 | 09-15 | 0.4 | NO |
| `T-empirica-outreach-02` | 2026-09-12 | 09-15 | 0.4 | NO |
| `T-grok-crossref-03` | 2026-09-12 | 09-15 | 0.4 | NO |
| `T-opportunity-aggregator-01` | 2026-09-12 | 09-15 | 0.4 | NO |

**Basis for every NO:** each of those four practice directories contains exactly one file,
`.empirica/project.yaml`, added 2026-09-11 in commit `48fb0a1`. Across all 12 commits of the repository's
history, `git log --diff-filter=AD` shows no deliverable was ever added under them and none was deleted.
The named artifacts never existed. Per the spec, missing file = NO.

**Measured effect:**

| metric | before | after |
|:--|:--|:--|
| `nf_resolved` | 0 | 7 |
| `brier_overall` | null | 0.2075 |
| `stocks.EVID-row` | 0 | 7 |
| `stocks.CAL-pt` | 0 | 7 |

Chain verified intact at 172 events. **F-64's falsifier is NOT tripped** — its condition was "any
sourced RESOLVE event in the tree that `resource_census_v0_1.py` fails to count," and the census counts
all seven as MEASURED. F-64 now has its first evidence, and Z1's Brier of 0.208 sits below the 0.25
coin-flip baseline.

**What the run surfaced that drafting did not:**

1. **"The named repo" is under-specified.** The practices are not repositories — no `empirica-outreach`
   or `grok-crossref` repo exists. They are directories inside `empirica-practice-mesh` (Z-007). That
   reading is recorded in each RESOLVE's `source` so it is auditable; if Z2 reads "the named repo"
   differently, the correction path is a DISPUTE event, not an edit.
2. **Resolution needs cross-repo read access**, which the operations session scope does not cover. It
   worked only because the repository is public and the git proxy serves anonymous reads. A private
   practice repo would have blocked the pass outright.
3. **The cost is front-loaded, not per-pin.** The reads themselves were seconds. Nearly all the effort
   went to locating the resolver rule and mapping practice → repo. That is the load-bearing input for
   §B.7: a per-session resolution step is cheap **only once the resolver mapping is written down**.
   Proposing §B.7 without first recording that mapping would ship a ritual whose real cost nobody
   has measured.
4. **A delivery signal, not just a calibration one.** Seven of seven practice deliverables due on or
   before 2026-09-12 do not exist. That is a mesh-execution finding in its own right and is not what
   this block was scanning for; flagged for Z2 rather than folded into an existing candidate.

Still blocked, unchanged: 21 tokens in `PENDING_Z2_DATE` cannot be resolved until a Z2-signed `date`
event lands. 30 tokens remain DATED with windows still open (earliest ripe 2026-09-18).

---

## Z2 Review Checklist

- [ ] Register or reject `F-CAND-SELF-EXEMPT-RULE-01` (promotion gate: 2 further instances)
- [ ] Rule on `IC-CAND-TIER-RULE-ABSENT-PATHS-01` — IC (EXTENSION of IC-041) or NM (caught pre-merge)
- [ ] Register or reject `IC-CAND-MOLT-LEDGER-ABSENT-01` (both limbs)
- [ ] Register or reject `IC-CAND-ANTICASCADE-UNWIRED-01` (EXTENSION of IC-050)
- [ ] Register or reject `IC-CAND-MOLTCYCLE-TIER0-BROKEN-01`
- [ ] Register or reject `IC-CAND-SEED-INTAKE-LABELS-01`
- [ ] Register or reject `H-CAND-MOLT-TIER-UNDERCLAIM-01` (conditional on #343 merging)
- [ ] Accept / edit / reject preventions (1)–(5), including the §B.7 ritual addition
- [ ] **H-GOV-01 forward-pointer:** all five IC candidates trigger P3 and share one shape — the
      principle existed and was documented, the mechanism was absent or unwired. That is limb (a) of
      H-GOV-01's promotion gate verbatim. Its `evidence_basis` currently reads `IC-024 through IC-038`;
      if these ratify it wants extending. Not proposed as an edit — the register is append-only and the
      forward-pointer is Z2's to write.
- [ ] Confirm `open_molt_count: 1` = molt `f7a49f667c09f1f6` (Q-RBE-01), **not** PR #342, and that
      #343 may proceed as the second of K=3

## Falsifier

Per candidate, each independently falsifiable against the tree at the pinned SHA:

- `F-CAND-SELF-EXEMPT-RULE-01` — falsified if no second path-scoped control in this repository omits
  its own definition file, making the observation a one-off implementation slip rather than a class.
- `IC-CAND-TIER-RULE-ABSENT-PATHS-01` — falsified if `tools/validate.py` or `tools/ratify.py` resolves
  on disk at `3345688`.
- `IC-CAND-MOLT-LEDGER-ABSENT-01` — falsified if any row in `ledgers/NF_LEDGER.jsonl` carries
  `molt_id` or `outcome`, or if any molt ledger file exists anywhere in the tree.
- `IC-CAND-ANTICASCADE-UNWIRED-01` — falsified if `.github/workflows/z2_ratification_gate.yml` parses
  to a job set containing `anti_cascade_rules`, or if any workflow invokes `ci_gates.py`.
- `IC-CAND-MOLTCYCLE-TIER0-BROKEN-01` — falsified if `python3 tools/molt_cycle_tier0_v0_1.py
  --read-only --nf ledgers/NF_LEDGER.jsonl` exits 0 against `constants.json` at this SHA.
- `IC-CAND-SEED-INTAKE-LABELS-01` — falsified if either `seed` or `amendment` resolves as a repository
  label.
- `H-CAND-MOLT-TIER-UNDERCLAIM-01` — falsified by ≥30 measured PRs with an under-claim rate at or
  below 5%.
- **Appendix** — ~~falsified if `nf_ledger_v0_1.py status` reports zero scoreable-now pins…~~
  **Superseded by execution, 2026-09-16.** The claim was tested by running the pass rather than
  arguing it. 7 ripe tokens were resolved by tree read; `nf_resolved` moved 0 → 7 and `brier_overall`
  null → 0.2075. The appendix's substantive claim — that the tooling exists and the work is Z1's, not
  Z2's — held. Its *number* did not. See "Executed" below.
