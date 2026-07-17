# Zone 1 Candidates — External Research Mapping (proposed, not ratified)

**Prepared by:** Claude (Zone 1 — proposing only, no self-numbering per G-4/IC-030)
**Motivating exchange:** external-research mapping session, S-071126-01 continuation
**Requested action:** Zone 2 review of all four; none self-register.

---

## Section A — H-candidates (new research questions, not fixes)

### H-CAND-DISCRIMINATION-VS-GENERATION-01

```
id_slug: "H-CAND-DISCRIMINATION-VS-GENERATION-01"
class: "H"
status: "CANDIDATE"
zone2_ratification: null
related_finding: ["F-49", "IC-047"]
related_paper: "Jiang et al., SELF-[IN]CORRECT (arXiv:2404.04298)"
```

- **Hypothesis:** ACAT's Phase 1 self-report (generation-time calibration
  claim) and a substrate's blind-discrimination accuracy on its own past
  responses (shown a prior response with no self-generation context,
  asked "was this correct/well-calibrated?") are not reliably correlated
  — and blind-discrimination accuracy may be lower than P1 self-report
  accuracy, mirroring SELF-[IN]CORRECT's core finding that LLMs are not
  reliably better at discriminating their own outputs than generating them
  (54/56 experiments failed to reject the null; DG-DIFF generally small
  or negative).
- **Null hypothesis:** P1 self-report accuracy and blind-discrimination
  accuracy on the same substrate are positively correlated at a
  magnitude consistent with a single underlying calibration construct.
- **Required controls, taken directly from the source paper's own
  methodology (not assumed, sourced):**
  - *Task-difficulty parity control* — the source paper found that
    simplifying discrimination-phase distractors substantially closed
    the gap (Figure 9: GSM8K DG-DIFF improved from -2.8/-5.5/-5.9 to
    -1.0/-4.2/-3.5 with easier distractors). Any ACAT-adapted design
    must equalize difficulty between the P1 self-report task and the
    blind-discrimination task, or a null result is confounded, not
    informative.
  - *Capability-tier stratification* — the source paper found DG-DIFF
    increases with model capacity within a family. This should be
    tested as a moderator, not ignored — and the direction should be
    explicitly compared against F-49 (Capability-Correlated Humility
    Inversion), which runs the opposite way (larger models show *worse*
    P1→P3 calibration). If discrimination accuracy improves with
    capability while self-report calibration degrades with capability,
    that is a genuinely novel, citable tension worth naming as its own
    finding once data exists — not resolved here.
  - *Architecture note* — the source paper found non-autoregressive
    models (Flan-T5, Flan-UL2) did not show the SELF-[IN]CORRECT effect.
    All current ACAT substrates are autoregressive; this hypothesis is
    scoped to that architecture class only and should not be
    generalized beyond it without new evidence.
- **Design (proposed, not built):** for N sessions, collect (a) P1
  Humility/Truthfulness self-report, (b) a blind-discrimination pass on
  a randomly-selected prior P3 response from the same substrate with
  self-generation context stripped, scored against the same rubric.
  Use McNemar's test for binary correct/incorrect framings or Wilcoxon
  signed-rank for scored framings — both directly reusable from the
  source paper's own statistical methodology (Section G of the source).
- **Promotion gate:** N≥1 paired pilot run, difficulty-matched per the
  control above, before Zone 2 considers this beyond CANDIDATE.

---

### H-CAND-DRIFT-SIGNAL-COMPOUNDING-01

```
id_slug: "H-CAND-DRIFT-SIGNAL-COMPOUNDING-01"
class: "H"
status: "CANDIDATE"
zone2_ratification: null
related_finding: []
related_drift_code: "D-02 (adjacent, not identical)"
related_paper: "Self-Correction Bench (arXiv:2507.02778) — 'hallucination snowballing'"
```

- **Hypothesis:** an uncaught HumanAIOS drift signal (any code in
  `REGISTERED_DRIFT`, Layer A/B/C per `humanaios-realtime-drift`)
  measurably increases the rate of a second, related error later in the
  same session, rather than remaining a neutral, isolated miss. This
  directly operationalizes the source paper's "hallucination
  snowballing" mechanism — once an error occurs, subsequent generation
  tends to align with and build on it rather than catch it — against
  this project's own session-transcript record.
- **Explicit distinction from D-02 (Repeat Diagnosis):** D-02 names
  immediate re-assertion of the *same* corrected answer after explicit
  correction. This hypothesis is broader and untested — it claims a
  *different*, related error becomes more likely following an *uncaught*
  first error, before any correction has occurred at all. No existing
  drift code or IC pattern measures this.
- **Null hypothesis:** the rate of a second drift signal firing within
  N turns of an uncaught first signal is not significantly different
  from the base rate of drift signals firing in matched control windows
  with no preceding uncaught signal.
- **Design (proposed, not built):** retrospective analysis against
  existing WGS session logs and stored transcripts. For each session,
  identify drift-signal-eligible events (matching `REGISTERED_DRIFT`
  patterns) that were NOT caught/flagged in-session (i.e., appear only
  in a later IC-class correction, meaning they went uncaught live).
  Measure the rate of a second, topically-related drift-eligible event
  in the same session within a defined turn window after the first,
  compared against sessions/windows with no uncaught first event.
- **Evidential caution (per Section 0 discipline, applies here too):**
  this is a transcript-analysis question, answerable from existing
  external record (session logs), not from self-report about internal
  process — it does not require the substrate to introspect on why
  snowballing happened, only whether the compounding pattern is
  statistically present in the visible record.
- **Promotion gate:** retrospective pass across N≥10 existing sessions
  with at least one clearly uncaught-then-corrected drift event, before
  Zone 2 considers a prospective design.

---

## Section B — IC-candidates (gaps in existing infrastructure)

### IC-CAND-SELF-CORRECTION-CLAIMS-NOT-UNIFORMLY-GATED

```
id_slug: "IC-CAND-SELF-CORRECTION-CLAIMS-NOT-UNIFORMLY-GATED"
class: "IC"
status: "CANDIDATE"
zone2_ratification: null
related_finding: ["IC-041", "IC-043", "IC-041-correction (S-071026-01)"]
related_paper: "Huang et al., LLMs Cannot Self-Correct Reasoning Yet (arXiv:2310.01798)"
fix_principle: "P3 (generalize existing narrow-scoped fixes into one rule)"
```

- **Synopsis:** IC-041 (audit false-pass), IC-043 (phantom migration
  references), and the IC-041 fix-not-landed correction (S-071026-01)
  are three separate, independently-discovered instances of the same
  underlying mechanism the cited paper establishes empirically: a
  self-correction claim made without external verification often fails
  or is simply wrong, and the failure is not caught until something
  outside the generating process checks it. Each instance was patched
  narrowly — P3 (GitHub Verification Protocol) for repo-state claims,
  IC-030 for registry state — rather than as one general rule.
- **Gap:** there is no principle currently stated as "any claim that a
  prior self-correction was completed, in any domain (code, registry,
  schema, documentation, prose), requires an external check before being
  treated as resolved." The existing fixes are domain-scoped patches
  applied after each separate failure, not a preventative general rule
  applied before a fourth instance occurs in a domain not yet patched
  (e.g., a self-correction claim about a document's content, or a
  claim about a fixed calculation, neither of which P3 or IC-030
  currently cover).
- **Evidence:** three independently-discovered, differently-scoped
  instances in this project's own IC record is itself the pattern —
  same mechanism, three domains, three separate narrow fixes.
- **Fix path (proposed, not drafted here):** a domain-general principle
  amendment — draft language TBD at Z2 — stating that self-correction
  claims are provisional until externally checked, with the check
  method left domain-specific (git diff for code, live fetch for
  registry, re-execution for a calculation, re-read for a document) but
  the *requirement* stated once, generally, rather than per-domain.
- **Promotion gate:** Zone 2 confirms this is worth a general principle
  rather than continuing to patch domain-by-domain as new instances
  surface; if confirmed, draft principle text becomes a separate Z1
  deliverable.

---

### IC-CAND-P1-INTROSPECTIVE-RELIABILITY-UNWEIGHTED

```
id_slug: "IC-CAND-P1-INTROSPECTIVE-RELIABILITY-UNWEIGHTED"
class: "IC"
status: "CANDIDATE"
zone2_ratification: null
related_finding: ["F-57", "H-SELF-01"]
related_paper: "Anthropic, Emergent Introspective Awareness in LLMs (arXiv:2602.20031)"
fix_principle: "P19"
```

- **Synopsis:** ACAT Phase 1 is, structurally, exactly the kind of claim
  the cited paper's own authors say should not be trusted without
  external validation — a model's self-report about its internal
  state/adherence, found in their own testing to be accurate only
  roughly 20% of the time under their conditions, with the paper's
  stated open problem being how to detect confabulation in such
  reports. `acat_dimension_scorer_v1_1.py` currently ingests Phase 1 as
  a raw, equally-weighted data point alongside Phase 3 behavioral
  evidence, with no field discounting it by a known introspective-
  reliability floor.
- **Distinction from IC-047 (Scorer Certainty Overclaim):** IC-047
  concerns the scorer's *output* — emitting unconditional PASS over
  JUDGMENT-tier scores. This candidate concerns the scorer's *input* —
  Phase 1 is accepted without any reliability discount applied before
  it enters LI computation at all. They are adjacent, not duplicate:
  fixing IC-047 would not fix this; fixing this would not fix IC-047.
- **Distinction from F-57 and H-SELF-01:** those establish that
  self-report is unreliable and that self-administration inflates
  scores. This candidate is the specific, actionable schema gap that
  follows from taking those findings seriously: no field currently
  exists to encode "how much should this specific Phase 1 declaration
  be trusted" as a first-class, queryable value.
- **Evidence:** direct review of `acat_dimension_scorer_v1_1.py`'s
  `aggregate()` function (same code region flagged by F-56/IC-047) shows
  Phase 1 values entering LI computation with no discount or
  reliability-tier field referenced anywhere in the module.
- **Fix path (proposed, not drafted):** a `p1_introspective_reliability_tier`
  field, populated per-session from available signal (e.g., whether the
  session is self-administered per `submission_purity`, whether
  cross-substrate or grounded corroboration exists) — not a claim the
  substrate makes about itself, but a value computed from external,
  already-available corpus metadata.
- **Promotion gate:** schema design proposal reviewed at Z2; this
  candidate does not itself propose exact tier boundaries or scoring
  logic — that is a separate downstream design task once the gap is
  confirmed as worth closing.

---

## Numbering instructions (per standing discipline)

- Verify current max F-/IC- number live before assigning.
- H-series is slug-named — append using the slug given.
- None of the four entries above are self-registered; all require Zone
  2 ratification before any registry write.
