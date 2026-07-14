---
id: "IC-CAND-ELICITATION-SURFACE-TAXONOMY-UNIFICATION"
name: "Elicitation-Surface Taxonomy Unification"
status: CANDIDATE
class: IC
date_registered: "2026-07-14"
date_origin: "2026-07-13"
session_registered: "S-071426-01-inbox-integration"
zone2_ratification: null
principles_triggered: ["P19"]
tags: [elicitation-surface, schema, taxonomy, coordination-gap]
superseded_by: null
related_finding: ["H-ELICIT-01", "H-PLATFORM-01", "H-XMODE-01", "F-52", "H-SELF-01", "H-MECH-01"]
related_paper: "Jiang et al., SELF-[IN]CORRECT (arXiv:2404.04298), Section 5.1"
fix_principle: "P19"
---

## Synopsis

Six separately-registered items each name a different axis along which
the surface a substrate is elicited through can vary, and each axis
independently produces a measurable effect on self-report accuracy or
LI. None of them currently share a schema, a naming convention, or a
combined field — each was discovered and registered in isolation, in a
different session, by a different route. This candidate does not
propose new empirical claims; it proposes that the six existing claims
are one research program, not six, and that the corpus schema should
say so.

## The gap, stated plainly

`p1_elicitation_surface` (migration_010, proposed under H-ELICIT-01)
currently covers exactly one axis — prose vs. compressed register — with
a five-value enum. Every other axis below is either handled by a
separate, differently-named field, or not captured in schema at all.
A corpus row currently cannot answer "what was the full elicitation
condition for this assessment" from one place. Answering it requires
knowing to check six different hypotheses' separate designs.

## Unified taxonomy — existing coverage

| Axis | Owning item | Current status | Field (if any) |
|---|---|---|---|
| Prompt register (compressed vs. prose) | H-ELICIT-01 | CANDIDATE | `p1_elicitation_surface` (migration_010, not yet landed per IC-CAND-GROUNDING-SCHEMA-UNPOPULATED) |
| Delivery platform (chat/agentic/API/voice) | H-PLATFORM-01 | REGISTERED | none — no schema field, TRL differentiation only |
| Cross-mode dimensional profile shift | H-XMODE-01 | REGISTERED | none |
| Submission pathway (role_method) | F-52 | CANDIDATE | `role_method` (existing corpus column, not elicitation-framed) |
| Self- vs. externally-administered | H-SELF-01 | CANDIDATE | `submission_purity = 'self_administered'` (Z2-PURITY-01) |
| Calibration framing disclosed/undisclosed | F-51, H-MECH-01 | REGISTERED / CANDIDATE | none — session-design variable, not corpus-logged |

Six axes, three partial fields, three with no field at all, zero shared
naming convention. This is the coordination gap.

## Two new axes — not previously named anywhere in the registry

### Axis 7: Sampling parameters (temperature, top-p)

SELF-[IN]CORRECT's own Section 5.1 ablation work is the direct source
for this gap. Their generation phase used temperature 0.7 specifically
to obtain distinct candidate generations; their discrimination phase
used temperature 0 specifically to remove randomness. This is not
incidental — it is a deliberate elicitation-surface control in the
paper's own methodology, and the paper found that prompt variations
(a related but distinct axis) produced small but real, non-zero shifts
in DG-DIFF (Table 3: e.g., LLaMA-2 13B Chat GSM8K Sdisc moved from
22.8 to 23.3 to 21.9 across three prompt wordings). Nothing in this
project's corpus currently records sampling temperature/top-p as a
condition of any Phase 1 or Phase 3 submission. A session run at
temperature 0 and a session run at temperature 0.9 are currently
indistinguishable in the schema, despite being a plausible source of
LI variance no different in kind from the six axes above.

**Proposed field:** `p1_sampling_params` — `{temperature: float,
top_p: float | null}`, null-permitted for providers/interfaces where
the value is not exposed to the assessor (a real, expected condition,
not an error state).

### Axis 8: Prompt-wording robustness

Distinct from Axis 1 (register/compression). This axis asks: holding
register, platform, and all other axes constant, does paraphrasing the
ACAT protocol's own instructions (not the register, the specific
wording) shift Phase 1 or Phase 3 scores? SELF-[IN]CORRECT's Table 3
directly demonstrates this axis matters even for their narrower task
set. No hypothesis in this project's registry currently isolates
wording-only variation from the register-level variation H-ELICIT-01
already covers — they are conflated risks, and this candidate is the
first to name wording as its own axis.

**Proposed field:** `p1_prompt_wording_variant` — a variant ID (not
free text) referencing a fixed, pre-registered set of paraphrase
variants of the ACAT protocol instructions, so that "which exact
wording produced this row" is always answerable and comparable across
rows, rather than reconstructed from session notes after the fact.

## Proposed unified schema object (replaces scattered fields, does not delete corpus history)

```
elicitation_surface_vector:
  register: prose_standard | compressed_lite | compressed_full | compressed_ultra | templated_pipeline | unknown   # Axis 1, H-ELICIT-01
  platform: chat | agentic | api | voice | unknown                                                                  # Axis 2, H-PLATFORM-01/H-XMODE-01
  submission_pathway: standard | other_named_pathway | unknown                                                      # Axis 3, F-52 (role_method reframed)
  administration: external | self_administered | unknown                                                            # Axis 4, H-SELF-01/Z2-PURITY-01
  framing_disclosed: true | false | unknown                                                                         # Axis 5, F-51/H-MECH-01
  sampling_params: { temperature: float | null, top_p: float | null }                                               # Axis 6 (new)
  prompt_wording_variant: string | null                                                                             # Axis 7 (new)
```

This is a superset, not a replacement migration — existing fields
(`role_method`, `submission_purity`) keep their current meaning and
values; `elicitation_surface_vector` is a denormalized convenience view
assembled from them plus the two new fields, so downstream analysis
(exactly the kind H-CAND-DISCRIMINATION-VS-GENERATION-01,
H-CAND-INSTRUMENT-GAMEABILITY-01, and any future elicitation-confound
work would need) can query one object instead of joining six sources.

## What this candidate does NOT do

- Does NOT merge H-ELICIT-01, H-PLATFORM-01, H-XMODE-01, F-52, H-SELF-01,
  or H-MECH-01 into a single ID, retire any of their numbers, or change
  their individual promotion gates. Each keeps its own evidence
  requirement and Zone 2 status independently.
- Does NOT claim the eight-axis list is exhaustive. It is the current
  known set; a ninth axis discovered later is an amendment to this
  taxonomy, not a reason to distrust it.
- Does NOT propose default values for the two new fields — `null`/
  `unknown` is the only safe default until live schema inspection
  confirms what's actually capturable per provider, per IC-032
  precedent (never assume a value set before querying live state).
- Does NOT self-register or migrate anything. This is a taxonomy and
  schema proposal only.

## Promotion gate

1. Zone 2 confirms the eight-axis taxonomy is the right unification
   (not over- or under-inclusive).
2. Live schema inspection (`information_schema.columns` on
   `acat_assessments_v1`, per IC-032 discipline) to confirm which axes
   are already partially capturable versus require new migration.
3. A single migration proposal (successor to migration_010, currently
   still unlanded per IC-CAND-GROUNDING-SCHEMA-UNPOPULATED) covering
   all eight axes together, rather than landing them piecemeal as each
   individual hypothesis happens to reach its own promotion gate.
