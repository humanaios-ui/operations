# REGISTERED.md Failure-Mode Map
## Registry Failure Modes → Standing Orders → Industrial Failure Modes

**Source:** `REGISTERED.md` @ `1e1b5189f6ae657c3b1a666eb5b52194327e0b63` (3,948 lines, 137 entries post-review correction)
**Mapping Date:** 2026-09-13
**Authority:** Z2 (Night) ratification pending
**Status:** Z1 candidate for REGISTERED.md
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED_FAILURE_MODES.md`
**Instrument:** `tools/registered_failure_mode_scan_v0_1.py`. Every count below is produced by that tool and
verified against it by `scan --verify-doc REGISTERED_FAILURE_MODES.md`, which fails if this document drifts
from the registry. A map asserting RFM-11 while carrying hand-copied counts would be an instance of it.

---

## Executive Summary

`REGISTERED.md` is the load-bearing artifact of HumanAIOS governance. Every Z1 proposal, Z2 ratification and Z3 execution routes through it, and `REGISTERED.md:12` instructs readers to *"treat the synopsis as the citable fact."* The registry catalogues the failure modes of substrates and sessions. It has never been turned on itself.

This document does that, in three columns:

| Column | Question it answers | Output |
|:---|:---|:---|
| **1 — Registry failure modes** (`RFM-NN`) | How does the registry fail? | 19 modes, 11 machine-detected, occurrence measured not asserted |
| **2 — Standing orders** (`SO-NN`) | What operation exists *because* of that failure? | Each order's **watch status**: MANNED / ADVISORY / UNMANNED |
| **3 — Industrial failure modes** | What kind of failure is this, in reliability terms? | Extends the repo's existing 5S/DMAIC layer |

**The three columns are one argument.** Column 2 is the DMAIC **Control** phase artifact — a control plan. Column 3 names what *kind* of control each entry in it is. A failure mode with no operation behind it is a description; an operation with no mechanism behind it is a wish.

**Headline findings:**

1. The registry scores **81.6% first-pass yield / 181,306 DPMO / ~2.4σ** at entry level. `audits/T1_DEFECT_BASELINE_S070726.md` designated `operations` the *"clean reference bar (0/7)."* Measured at entry level, it is not clean.
2. Of 19 failure modes, **before this scan 17 had no detector at all**. The dominant failure mode of the registry is not any single defect — it is the absence of instrumentation.
3. **Four instruments disagree about the registry's own census.** `tools/registered_findings_validator_v1_0.py` reports **130** entries; `tools/repo_health.py` reports **126** immune entries; this scanner reported **131** before review, **135** after first correction, and **137** after Phase 2 parser fix (correction-to discovery + F-24 variant regex + ordering violation counting). No single instrument can be cited as authoritative. Routed to Z2 as a measurement-system finding — its resolution is a Z2 decision about which census should govern RFM-06 scoring and downstream action items.
4. The value recorded as **Ratification Hash** at `REGISTERED.md:3925` is `e8a501f` — a 7-character git commit SHA, where `CLAUDE.md` Decision Routing step 6 and `NF_LEDGER_SCHEMA_v1.md` both specify `sha256(candidate | by=Night | at=timestamp | decision=ACCEPT)`. A commit SHA proves *when code landed*, not *what was approved*.

---

## Measured Baseline

Reproduce with `python3 tools/registered_failure_mode_scan_v0_1.py scan`.

**Entry-level conformance** (137 entries × 4 checks = 548 opportunities):

| Check | RFM | Defects | Conformance |
|:---|:---|:---|:---|
| Ordering (`REGISTRY_SPEC.md:114`) | RFM-09 | 30/137 | 78.1% |
| Required schema fields (`REGISTERED.md:16-32`) | RFM-06 | 58/137 | 57.7% |
| Front-matter fence form | RFM-07 | 8/137 | 94.2% |
| Quote hygiene | RFM-08 | 5/137 | 96.4% |

**101 defects / 548 opportunities → 81.6% first-pass yield → 181,306 DPMO → ~2.4σ**

`RFM-06` scores the **full** schema at `REGISTERED.md:16-32`, all ten declared fields. The registry says entries
*"must open with"* that block, so the whole list is the contract; scoring a convenient subset would let the
measurement flatter the registry. For triage the core five (`name`, `status`, `class`, `date_registered`,
`session_registered`) are at **12/135 — 91.1% conforming**. The gap between 91.1% and 57.0% is `substrate` (45
absent), `tags` (38), `superseded_by` (33) and `date_origin` (29): fields declared but never adopted. Whether that
is schema erosion or an over-declared schema is Z2's call, not the scanner's — it reports both numbers and picks
the declared one as the headline.

Same methodology and 1.5-shift convention as `audits/T1_DEFECT_BASELINE_S070726.md` (mesh baseline: 42.9% FPY, ~571,000 DPMO, ~1.3σ).

**File-level defects** (no per-entry opportunity count; deliberately excluded from the denominator rather than folded in to flatter the score):

| Check | RFM | Result |
|:---|:---|:---|
| F quick-index desync | RFM-11 | 10 of 45 F-entries absent from index (77.8% coverage) |
| Post-terminal append | RFM-10 | 25 entries after the `## Changelog` boundary (by line position, so a later terminal section cannot hide one) |
| Orphan roll-up row | RFM-12 | 1 — IC-036 cited at `REGISTERED.md:118`, no body entry |
| Ratified-class starvation | RFM-16 | 3 of 6 — D, R, GD defined, zero entries |
| Header staleness | RFM-17 | declared 2026-08-15; newest content 2026-09-09 |
| Ratification-hash form | RFM-15 | 1 — 7 hex chars where 64 are specified |
| Cross-artifact ratification | RFM-14 | 2 contradictions |

**Whitelisted, not defects:** F-32 and F-33 appear in the quick index with no body entry **by design** — documented honest gaps, deliberately never backfilled. Flagging them would be a false positive of exactly the IC-037 genus this document warns about. The scanner whitelists them and self-tests that the whitelist works.

---

## Column 1 — Layer 1: Registry Failure Modes

Grouped by registry lifecycle. **Detection today** is scored `1` = blocking CI gate, `5` = advisory or manual mechanism, `10` = doctrine only or nothing.

### READ — the registry is consulted

| ID | Failure mode | Evidence | Occurrence | Detection today |
|:---|:---|:---|:---|:---|
| **RFM-01** | **Stale / unfetched read** — reasoning from a cached or remembered registry rather than the live file | IC-030 | UNMEASURED | 10 → `SESSION_RITUALS.md` §F.9 hard halt is doctrine; nothing proves a fetch occurred |
| **RFM-02** | **Pin drift** — work proceeds against a SHA that has since moved | `ledgers/NF_LEDGER.jsonl` OPEN `registered_sha` | UNMEASURED | 10 |
| **RFM-03** | **Synopsis-as-fact overreach** — `REGISTERED.md:12` grants synopses citable authority while evidence lives elsewhere, so a wrong synopsis propagates at full authority with no path back to its evidence | `REGISTERED.md:10-12` | UNMEASURED | 10 |

### WRITE — entries enter

| ID | Failure mode | Evidence | Occurrence | Detection today |
|:---|:---|:---|:---|:---|
| **RFM-04** | **Under-registration** — a registrable item surfaces in-session and is never registered | `tools/skills/humanaios-findings-scan/SKILL.md:29` | UNMEASURED | 5 — skill exists, manually invoked |
| **RFM-05** | **Over-registration / receipt overstatement** — asserting registry state that does not exist | IC-031 | UNMEASURED | 5 — §B.6, `receipt_reconciliation.py` |
| **RFM-06** | **Schema erosion** — a field the schema declares is absent | `REGISTERED.md:16-32` | **58 / 137** full schema · 12 / 137 core | 10 — see note below |
| **RFM-07** | **Front-matter fence loss** — the entry carries no machine-readable front matter, so a fence-based parser cannot see it. Two forms: `id:` rendered as a markdown heading (F-52…F-55), and legacy `### ID — Title` entries with bold-prose fields or none at all (H-ELICIT-01 at `:2302`, plus H-1 / H-42 / H-LE-02) | F-52…F-55; H-1, H-42, H-LE-02, H-ELICIT-01 | **8 / 137** | 10 → 5 with this scanner |
| **RFM-08** | **Quote contamination** — curly quotes break straight-quote string parsing. Checked across every declared field, not just `id`/`name`/`status`/`class` | F-52, F-53, H-AICASCADE-01, (2 additional found in Phase 2 review) | **5 / 137** | 10 → 5 with this scanner |

> **Note on RFM-06 detection.** `.github/workflows/findings-registry.yml` runs `tools/registered_findings_validator_v1_0.py` as a blocking gate and its documented hard classes include *missing fields*. Run against the live registry it returns **Verdict: WARN, exit 0** with `✓ F-class ✓ H-class ✓ IC-class`, and does not surface the 8 entries missing required fields. A check that is nominally blocking and empirically silent is the IC-041 *audit-false-pass* genus. Scored 10, not 1, because detection is scored on observed behaviour rather than declared intent. **Routed to Z2 as an IC-candidate; not self-registered.**

### STRUCTURE — the file's own order

| ID | Failure mode | Evidence | Occurrence | Detection today |
|:---|:---|:---|:---|:---|
| **RFM-09** | **Append-ordering decay** — entry outside the class block `REGISTRY_SPEC.md:114` declares, *and* the class blocks themselves out of F→IC→H order | Z2-ASSESS-01, IC-044/045 in the H block; 25 more past the Changelog; F-31/IC-041 discovered via correction-to field | **30 / 137** | 10 → 5 |
| **RFM-10** | **Post-terminal append** — entries land after the `## Changelog` boundary, forming a shadow zone the declared structure does not describe | L3246–3917 | **25** | 10 → 5 |
| **RFM-11** | **Index desync** — the hand-maintained quick index stops tracking the body | F-24, F-56…F-61, 3× `F-CAND-*` | **10 / 45 F** | 10 → 5 |
| **RFM-12** | **Orphan roll-up row** — the IC Pareto cites an ID with no entry; the row still reports healthy | IC-036 @ `REGISTERED.md:118` | **1** | 10 → 5 |
| **RFM-13** | **Semantic duplicate numbering** — two IDs for one defect. Invisible to any validator that detects only *literal* ID collisions | IC-052 / IC-053, both "drift validator missing D-OVERCLAIM" | **1 known** | 10 — no detector possible without semantic comparison |

### RECONCILE — registry vs the world

| ID | Failure mode | Evidence | Occurrence | Detection today |
|:---|:---|:---|:---|:---|
| **RFM-14** | **Cross-artifact ratification desync** — an artifact's ratification state contradicts itself or the registry | `PRIORITY_QUEUE.md:11` says *"pending Z2 signature"*; that same file's `## Appended Events` says *"PRIORITY_QUEUE.md v1_1 ratified"*; `REGISTERED.md:3925` lists it ratified at `e8a501f` | **2** | 10 → 5 |
| **RFM-15** | **Ratification-hash substitution** — a git commit SHA recorded where a decision signature is specified | `REGISTERED.md:3925` = `e8a501f` (7 hex); spec requires 64 | **1** | 10 → 5 |
| **RFM-16** | **Ratified-class starvation** — a class `REGISTRY_SPEC.md` ratifies has zero entries. Indistinguishable from a healthy unused channel without a proof test | D-class (`REGISTRY_SPEC.md:16`), R, GD | **3 / 6 classes** | 10 → 5 |
| **RFM-17** | **Header staleness** — `Last updated` drifts behind the newest dated content | header 2026-08-15 vs content 2026-09-09 | **1** | 10 → 5 |

### GOVERN — the doctrine around the file

| ID | Failure mode | Evidence | Occurrence | Detection today |
|:---|:---|:---|:---|:---|
| **RFM-18** | **Cost-class undefined** — `REGISTRY_SPEC.md:45` requires IC entries be *"cost-classified by impact"*; only IC-031 carries a ratified cost class (lines 1501, 2029). Without universal classification the registry cannot prioritise its own failures | IC-031 | 1 of 43 IC entries cost-classed | 10 |
| **RFM-19** | **Silent-tier undefined** — `tools/skills/humanaios-wgs-sweep/SKILL.md:175` references *"three-tier silent failures"* in `SESSION_RITUALS.md` §B.5; the tiers are not defined there | §B.5 | n/a | 10 |

---

## Column 1 — Layer 2: What the Registry Already Captured

Not a re-listing of the IC Pareto (`REGISTERED.md:88-125`) or the D-signal catalog (`GOVERNANCE.md:209-221`, 13 entries + D-OVERCLAIM at `:165`). A **genus map** — the claim that entries already registered are instances of the same genera as Layer 1, which is what makes Layer 1 a taxonomy rather than a list of this week's complaints.

| Registered entry | Pattern label | Same genus as | Why |
|:---|:---|:---|:---|
| **IC-041** | Audit-false-pass — *"CI check targets a path absent from the repo; reports PASS by construction"* | **RFM-12**, and the RFM-06 note | A pointer at nothing that still reports healthy. The orphan roll-up row is this defect in table form |
| **IC-050** | Blocker gate not enforced — *"runtime behavior only warns and continues through every phase"* | **every RFM scored 10** | A defence present on paper, defeated in operation |
| **IC-037** | Instrument-scorer-conflation | **the scanner shipped with this document** | Measurement-system failure — see below |
| **IC-042** | Deploy-corruption-recurrence (count 2) | **RFM-08** | Typographic corruption surviving two independent attempts is a process incapability, not an accident |
| **IC-031** | Receipt overstatement ($150–730/incident) | **RFM-05** | The only quantified cost class in the registry |
| **IC-044/046** | Purity/exclusion gap recurrence | **RFM-13** | Recurrence under a second number is how semantic duplication enters |

### The scanner is subject to the failure mode it measures

`audits/T2_ANALYZE_S070726.md` records a regex bug — `\w` excluding `-` — that manufactured **five false ID-collision defects**, classified IC-037 + IC-034. The instrument was wrong in the direction of finding more work.

This document ships an instrument. It is in the same genus, and it demonstrated so during construction: the scanner's first version scored ordering conformance at 28/131 by silently skipping non-F/IC/H entries, where `REGISTRY_SPEC.md:114` declares *"F-class, then IC-class, then H-class, **then other classes**"* — making `Z2-ASSESS-01`'s position inside the H block a violation, not an exemption. The reconciliation step caught it; the corrected count is 29.

A second instance arrived from review. The first published version of this scanner reported **131 entries and
91.6% yield**; the figures above are **135 and 81.9%**. Three distinct instrument defects, all reviewer-caught:
it discovered entries only by `id:` lines and so silently dropped the four legacy-format entries — the very
schema failures it exists to measure; it scored a five-field subset of a ten-field declared schema; and under
`--enforce` a missing input produced `SKIP`, which summed to zero defects and **exited 0** — a gate reporting
success without having run, the IC-041 genus in the tool built to detect it.

The correction was not monotonic either. Widening entry discovery first produced **143** entries by
double-counting F-52…F-55 (their malformed `## id:` line is itself a heading, so the lookahead stopped short of
the id it contained) and by counting the F-32/F-33 honest gaps as malformed entries. Both are the T2 pattern
exactly: an instrument wrong in the direction of finding more work. 143 → 137 → 135 across three narrowing
passes, each removing a false-positive class.

Two controls, neither sufficient alone:

- `--smoke-test` / `self-test` exercises every evaluator against synthetic known-good and known-bad fixtures, including an explicit assertion that the F-32/F-33 whitelist suppresses the honest-gap false positive **and** that a non-whitelisted phantom is still caught.
- `scan --verify-doc REGISTERED_FAILURE_MODES.md` asserts this document's headline numbers against a live scan, so the map cannot silently go stale as the registry changes.
- The census divergence in Executive Summary finding 3 is **unresolved and left visible**. Three instruments disagree; this document does not assert which is right. Its own counts are conditional on its parser being correct — which is precisely the assumption IC-037 punishes.

---

## Column 2 — Standing Orders

### On vocabulary

Naval command vocabulary is used here deliberately. It is greenfield — `OODA`, `standing orders`, `watch bill`, `ROE`, `general quarters` return zero hits repo-wide — so it introduces no collisions. The repo's existing operational vocabulary is already overloaded:

- **"gate"** carries four meanings: Z2 gate, CI gate, runtime gate, blocker gate
- **"drift"** carries two: protocol drift signals (`D-*`) and registry↔filesystem divergence (A6)
- **"calibration"** means behavioural self-report accuracy, *not* metrology

A distinct register for *operations* keeps them separable from the *mechanisms* that implement them. Existing operations are mapped onto the frame, not replaced by it:

| Naval term | Existing mechanism |
|:---|:---|
| Standing orders | the callout table (`CLAUDE.md`) — always in force |
| Night orders | per-session drift catalog, `SESSION_RITUALS.md:57` |
| Watch / rounds | `A6_DRIFT_MONITOR_SPEC.md` biweekly sweep; `stale_sweep.py` half-life |
| General quarters | §F hard halt → DEGRADED mode (§F.9) |
| Commander's intent | falsifier doctrine — Z2 states what would falsify; Z3 acts unsupervised |
| Rules of engagement | `behavior_spec.json` caps; the five anti-cascade rules |
| Serial gate | single-server queue, no parallel authority (`ORGANIZATION_BLUEPRINT_v1.md:175`) |

### Watch status

Each standing order carries one of:

- **MANNED** — a blocking mechanism exists and demonstrably fires
- **ADVISORY** — a mechanism exists but warns only, or must be invoked by hand
- **UNMANNED** — doctrine only; nothing would catch the failure

### The orders

| SO | Trigger | Standing order | Actor | Cadence / window | Stop-work condition | From | Watch |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **SO-01** | Any registry-touching work begins | Fetch `REGISTERED.md` live and pin its SHA before reasoning from it | Z1 | Every session open (§A) | Hard halt, declare DEGRADED, if the fetch cannot be performed | RFM-01 | UNMANNED |
| **SO-02** | A pinned SHA is carried across a session boundary | Re-verify the pin still matches `origin/main` before acting on it | Z1/Z3 | Session open + before any append | Halt if the pin has moved and the delta is unread | RFM-02 | UNMANNED |
| **SO-03** | A synopsis is cited as fact | Cite the entry ID with its evidence pointer, never the synopsis alone | Z1 | Continuous | — | RFM-03 | UNMANNED |
| **SO-04** | Session close | Run a findings scan; route F/IC/H candidates to Z2 | Z1 | Every §B close | — | RFM-04 | ADVISORY |
| **SO-05** | Any claim about registry state | Walk claim against tree; generate receipt; report RECEIPT-GAP | Z1 | §B.6, every close | Refuse close if B.0 was not run | RFM-05 | ADVISORY |
| **SO-06** | An entry is appended | Entry must carry every field the schema declares | Z1 → Z2 | Per append | Reject the append | RFM-06, RFM-07, RFM-08 | ADVISORY |
| **SO-07** | An entry is appended | Entry lands inside its declared class block, never after a terminal section | Z2 | Per append | Reject the append | RFM-09, RFM-10 | ADVISORY |
| **SO-08** | Any hand-maintained table cites an entry | Index and roll-up rows are generated from the body, never hand-carried | Z3 | Per append + weekly rounds | — | RFM-11, RFM-12 | ADVISORY |
| **SO-09** | A new ID is assigned | Check the defect against existing pattern labels before numbering it | Z2 | Per append | — | RFM-13 | UNMANNED |
| **SO-10** | An artifact is ratified | Ratification state is written to **both** the artifact and the registry in one act | Z2 | Per ratification | Halt if the two disagree | RFM-14 | ADVISORY |
| **SO-11** | A ratification is signed | The recorded hash is `sha256(candidate \| by \| at \| decision)`, never a commit SHA | Z2 | Per ratification | Reject a hash shorter than 64 hex | RFM-15 | ADVISORY |
| **SO-12** | A class is defined in `REGISTRY_SPEC.md` | Proof-test each declared class on a fixed interval; a channel with zero flow is dormant, not healthy | Z2 | Quarterly | — | RFM-16 | ADVISORY |
| **SO-13** | Any append | Update `Last updated` in the same commit as the append | Z1 | Per append | — | RFM-17 | ADVISORY |
| **SO-14** | An IC is registered | Assign a cost class from a defined taxonomy | Z2 | Per IC | — | RFM-18, RFM-19 | UNMANNED |

**Watch census: 0 MANNED · 9 ADVISORY · 5 UNMANNED.**

Before this document, the count was 0 MANNED · 2 ADVISORY · 12 UNMANNED. The scanner moves nine orders from UNMANNED to ADVISORY. **It moves none to MANNED**, because it ships with `--enforce` off — see *Action Items*. That is the honest reading, and it is deliberately not dressed up: an advisory gate is the IC-050 pattern, and naming it is the only way to make the decision to fix it available to Z2.

---

## Column 3 — Industrial Failure Modes

This extends the repo's existing lean/Six Sigma layer rather than duplicating it: `audits/5S_SIXSIGMA_ACAT_AUDIT_CHARTER_S070726.md` (5S + DMAIC + ACAT tri-lens), `RECURSIVE_IMPROVEMENT_SEED.md` (29 waste items by Toyota muda type), `audits/T1_DEFECT_BASELINE_S070726.md` (DPMO/σ), `A6_DRIFT_MONITOR_SPEC.md` (*"makes the audit a sensor, not a periodic event"*; MTTR < 5 days).

| RFM | Industrial failure mode | Why this term | Standard countermeasure |
|:---|:---|:---|:---|
| RFM-01, RFM-02 | **Stale process input** | Acting on a measurement taken before the last process change | Re-zero before each run |
| RFM-03 | **Traceability break** | The part is certified but the cert cannot be walked back to the lot | Serialized lot genealogy |
| RFM-04 | **Escape** | A defect leaves the cell undetected — under-reporting, not over-reporting | Containment at source |
| RFM-05 | **Overclaim / falsified inspection record** | A record asserts an inspection that did not occur | Independent verification |
| RFM-06, RFM-07, RFM-08 | **Poka-yoke absence** | The malformed state is *representable*; the format permits its own corruption | Make the bad state impossible to build, not merely detectable |
| RFM-09, RFM-10 | **Process drift / shadow WIP** | Work accumulating outside the declared routing | Standard work + visual control |
| RFM-11, RFM-12 | **Latent condition (Swiss cheese)** — and where the roll-up row reports healthy, **audit false-pass** | A defence present on paper, defeated in operation. IC-041 is this exactly | Proof-test the defence, not just its presence |
| RFM-13 | **Duplicate part number** | Two numbers for one part defeats Pareto — the class looks half as frequent as it is | Part-number reconciliation |
| RFM-14, RFM-15 | **Certification substitution** | A document of the wrong type accepted in a cert's place. A commit SHA and a decision signature are different instruments answering different questions | Cert-type validation at receipt |
| RFM-16 | **Dormant failure** | A protective channel never exercised is indistinguishable from a working one | **Proof test at a defined functional test interval** |
| RFM-17 | **Label/revision mismatch** | The tag describes an earlier revision than the item carries | Revision control at point of change |
| RFM-18, RFM-19 | **Missing severity scale** | Without severity, criticality cannot be computed and prioritisation is arbitrary | Define the scale before the FMEA |
| *(the scanner)* | **Measurement system error (gauge R&R)** | The instrument is a source of variation. T2's regex bug; this scanner's ordering bug | Calibrate the gauge against known standards before use |

**Explicitly declined, with reason:** bathtub curve, wear-out, fatigue, corrosion, creep, tolerance stack. These model time-dependent *physical* degradation. Registry entries do not wear out — a 2026-05 entry is exactly as valid today as when written; what decays is the *surrounding* state (`stale_sweep.py` half-life, A6 divergence), which is drift, already named. Forcing these terms would produce metaphor, not analysis. Naming and declining them is the more useful act.

### FMEA

The drift catalog at `SESSION_RITUALS.md:57` (*"Predict 3-8 failure modes you may exhibit in this session"*) is a proto-FMEA. It is missing exactly one thing: severity / occurrence / detection scoring. `RECURSIVE_IMPROVEMENT_SEED.md:128` already names the consequence — *"no gate checks whether the catalog was comprehensive... generated to justify a humility score, not to actually measure drift."*

**The honesty rule, non-negotiable:**

- **Occurrence** — from the measured scan only. Every unmeasured mode reads `UNMEASURED`, never a guessed integer.
- **Detection** — scored `1` / `5` / `10` on *observed* behaviour, not declared intent. This is the one axis groundable today, and the one that drives Column 2.
- **Severity** — only where a cost class exists **and a ratified mapping turns it into a 1–10 score**. IC-031 supplies a dollar range but no such mapping exists, so even it is `UNSCORED`. An earlier draft of this table scored RFM-05 an `8` from that range — reviewer-caught, and exactly the false precision this rule exists to prevent. The rule bound its author before it bound anyone else.
- **RPN** — computed **only** where all three axes are grounded. Today that is **zero rows**.

| RFM | Severity | Occurrence | Detection | RPN |
|:---|:---|:---|:---|:---|
| RFM-01 | UNSCORED | UNMEASURED | 10 | — |
| RFM-02 | UNSCORED | UNMEASURED | 10 | — |
| RFM-03 | UNSCORED | UNMEASURED | 10 | — |
| RFM-04 | UNSCORED | UNMEASURED | 5 | — |
| RFM-05 | UNSCORED — IC-031 gives $150–730, but no ratified mapping turns a dollar range into a 1–10 severity | UNMEASURED | 5 | — |
| RFM-06 | UNSCORED | 58 / 137 | 10 | — |
| RFM-07 | UNSCORED | 8 / 137 | 5 | — |
| RFM-08 | UNSCORED | 5 / 137 | 5 | — |
| RFM-09 | UNSCORED | 30 / 137 | 5 | — |
| RFM-10 | UNSCORED | 25 | 5 | — |
| RFM-11 | UNSCORED | 10 / 45 | 5 | — |
| RFM-12 | UNSCORED | 1 | 5 | — |
| RFM-13 | UNSCORED | 1 known | 10 | — |
| RFM-14 | UNSCORED | 2 | 5 | — |
| RFM-15 | UNSCORED | 1 | 5 | — |
| RFM-16 | UNSCORED | 3 / 6 | 5 | — |
| RFM-17 | UNSCORED | 1 | 5 | — |
| RFM-18 | UNSCORED | 1 of 43 IC cost-classed | 10 | — |
| RFM-19 | UNSCORED | n/a | 10 | — |

**A table of `UNSCORED` cells is the finding.** Every RPN cell is empty, including RFM-05's. The registry cannot presently prioritise its own failure modes, because the cost-class taxonomy `REGISTRY_SPEC.md:45` already requires does not exist (RFM-18). Filling this column with plausible numbers would manufacture exactly the false precision IC-034 (D-OVERCLAIM) names. The empty column is the argument for `Q-RFM-02`.

---

## Integration Diagram

```
                    REGISTERED.md  (137 entries, append-only, LIVE)
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───v────┐          ┌────v────┐          ┌────v────┐
    │  READ  │          │  WRITE  │          │STRUCTURE│
    │RFM-01  │          │ RFM-04  │          │ RFM-09  │
    │   -02  │          │    -05  │          │    -10  │
    │   -03  │          │    -06  │          │    -11  │
    └───┬────┘          │    -07  │          │    -12  │
        │               │    -08  │          │    -13  │
        │               └────┬────┘          └────┬────┘
        │                    │                    │
        │      ┌─────────────┼────────────────────┤
        │      │             │                    │
    ┌───v──────v───┐   ┌─────v──────┐      ┌──────v──────┐
    │  RECONCILE   │   │   GOVERN   │      │             │
    │ RFM-14 -15   │   │ RFM-18 -19 │      │             │
    │     -16 -17  │   │            │      │             │
    └───────┬──────┘   └──────┬─────┘      └─────────────┘
            │                 │
            └────────┬────────┘
                     │   reverse-engineer: each order exists
                     │   BECAUSE of a specific failure mode
                     v
         ┌───────────────────────────┐
         │  STANDING ORDERS SO-01…14 │   = DMAIC "Control" plan
         │  0 MANNED                 │
         │  9 ADVISORY               │
         │  5 UNMANNED               │
         └─────────────┬─────────────┘
                       │   classify: what KIND of control
                       v
         ┌───────────────────────────┐
         │  INDUSTRIAL FAILURE MODES │
         │  poka-yoke absence        │
         │  latent condition         │
         │  dormant failure          │
         │  cert substitution        │
         │  gauge R&R  ◄─── applies to the scanner itself
         └───────────────────────────┘
```

---

## Action Items for Z2 Ratification

- [ ] **Ratify the RFM taxonomy** (19 modes) as the registry's failure-mode vocabulary
- [ ] **Rule on `--enforce`** for `tools/registered_failure_mode_scan_v0_1.py`. Advisory today; leaving it advisory indefinitely reproduces IC-050. Recommended: remediate the 101 entry-level defects, then turn enforcement on in the same ratification
- [ ] **Rule on wiring into CI.** Deliberately not wired — `findings-registry.yml` already runs a blocking registry validator, and two registry gates on the same paths could return contradictory verdicts before Z2 has ruled
- [ ] **Resolve the census divergence** — 126 vs 130 vs 135 entries, and the F/IC/H split, across the three instruments. Until resolved, no instrument's census should be cited as authoritative
- [ ] **Number and append the four IC-candidates** below (Z1 proposes; Z2 numbers and appends, per G-4 / IC-030)
- [ ] **Commission `Q-RFM-02`** — the cost-class taxonomy `REGISTRY_SPEC.md:45` requires, which is the blocker on every `UNSCORED` cell in the FMEA

### IC-candidates routed, not self-registered

| Candidate | Claim | Evidence |
|:---|:---|:---|
| **IC-CAND-A** | Ratification hash is a commit SHA where a decision signature is specified | `REGISTERED.md:3925` = `e8a501f` (7 hex, spec requires 64) |
| **IC-CAND-B** | `PRIORITY_QUEUE.md` contradicts itself on its own ratification state | `PRIORITY_QUEUE.md:11` vs its `## Appended Events` |
| **IC-CAND-C** | IC roll-up cites IC-036, which has no body entry | `REGISTERED.md:118` |
| **IC-CAND-D** | IC-052 and IC-053 number the same defect twice | both "drift validator missing D-OVERCLAIM" |

A fifth is noted but held pending the census resolution: the registry validator returns WARN/exit-0 while 8 entries are missing required fields it nominally checks (RFM-06 note). Stating it as a finding requires first establishing that the two instruments are counting the same entries.

---

## Appendix: Quick Reference

| Need | File | Command |
|:---|:---|:---|
| The taxonomy | `REGISTERED_FAILURE_MODES.md` | — |
| Measure the registry | `tools/registered_failure_mode_scan_v0_1.py` | `scan` |
| Trust the measurement first | same | `self-test` |
| Machine-readable report | same | `scan --json --out report.json` |
| Existing registry validator | `tools/registered_findings_validator_v1_0.py` | `--input REGISTERED.md` |
| Ordering rule | `REGISTRY_SPEC.md:114` | — |
| Entry schema | `REGISTERED.md:16-32` | — |
| DPMO precedent | `audits/T1_DEFECT_BASELINE_S070726.md` | — |
| 5S/DMAIC lens | `audits/5S_SIXSIGMA_ACAT_AUDIT_CHARTER_S070726.md` | — |

### RFM → SO → industrial, at a glance

| RFM | Standing order | Industrial mode |
|:---|:---|:---|
| RFM-01, -02 | SO-01, SO-02 | Stale process input |
| RFM-03 | SO-03 | Traceability break |
| RFM-04 | SO-04 | Escape |
| RFM-05 | SO-05 | Falsified inspection record |
| RFM-06, -07, -08 | SO-06 | Poka-yoke absence |
| RFM-09, -10 | SO-07 | Process drift / shadow WIP |
| RFM-11, -12 | SO-08 | Latent condition / audit false-pass |
| RFM-13 | SO-09 | Duplicate part number |
| RFM-14, -15 | SO-10, SO-11 | Certification substitution |
| RFM-16 | SO-12 | Dormant failure |
| RFM-17 | SO-13 | Label/revision mismatch |
| RFM-18, -19 | SO-14 | Missing severity scale |

---

## Appended Events

```
2026-09-13 — Z1 Phase 2 parser correction: correction-to field discovery + F-24 variant regex + ordering violation counting: 137 entries, 101 defects / 548 opportunities, 81.6% FPY, 181,306 DPMO, ~2.4 sigma. Supersedes preceding; stream preserved append-only.
2026-09-13 — Z1 re-measured after review corrected the scanner's entry discovery: 135 entries, 98 defects / 540 opportunities, 81.9% FPY, 181,481 DPMO, ~2.4 sigma [SUPERSEDED by Phase 2 parser fixes]
2026-09-13 — Z1 measured REGISTERED.md @ 1e1b518: 44 defects / 524 opportunities, 91.6% FPY, 83,969 DPMO, ~2.9 sigma [SUPERSEDED — scanner under-counted: 4 legacy entries invisible, schema scored on 5 of 10 declared fields]
```

---

**Generated by:** Claude (Z1 Proposer)
**For ratification by:** Night/Admiral (Z2 Ratifier)
**For execution by:** Z3 Executors (per ZONE_REGISTRY.md)
