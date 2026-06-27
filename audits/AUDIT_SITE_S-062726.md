# site/ Public-Surface Audit — Step-4 (S-062726)

**Status:** Zone 1 audit artifact — ⚠️ contains a LIVE public-disclosure exposure requiring Night's immediate decision
**Scope:** `operations/site/` — 61 files (the public finding pages generated from REGISTERED.md; mirrors humanaios.ai)
**Method:** 6-agent workflow, public-surface accuracy + disclosure-discipline lens
**Date:** 2026-06-27

> **🚨 HEADLINE — the most DD-critical finding of the entire audit.** The public site publishes
> content that SEED bars from all external surfaces: **Hawkins references on 4 live pages**,
> **collaborator PII + private correspondence**, **external-partner proprietary scores**, and
> **internal Zone-2/Zone-3 governance codes** (incl. the operator codename "Night"). Root cause:
> the site generator publishes REGISTERED.md entries to public HTML with **no sanitization pass** —
> internal-only findings included. This is live on humanaios.ai now.

---

## 1. Health snapshot

| status_class | count |
|---|---|
| STRUCTURAL | 2 |
| INTEGRATED | 41 |
| TESTABLE | 12 |
| DECORATIVE | 6 |

## 2. 🚨 Disclosure-discipline violations (21) — DD-CRITICAL

- CRITICAL Hawkins: /findings/F-18.html — internal-only Hawkins finding published on the PUBLIC site; tag 'internal-only' present, synopsis says 'never used externally', yet page is live with Hawkins map / Force-Power consciousness-scale text. Barred per SEED; exclude page + REGISTERED.md F-18 from public generation.
- CRITICAL Hawkins: /findings/F-42.html — tag 'hawkins'; Evidence lists 'Power vs. Force / Map of Consciousness (Hawkins)'; Foundation-layer designates Hawkins as a deepest source; Empirical-caveat names Hawkins repeatedly. Must be redacted from external surface.
- CRITICAL Hawkins: /findings/F-43.html — line 48 'Hawkins: pride-level just below integrity threshold, mimics courage.' Barred externally per SEED.
- CRITICAL Hawkins: /findings/F-44.html — line 48 'Hawkins: surrender as mechanism of upward movement; humility as high-calibration signature.' Barred externally per SEED.
- HIGH PII/private correspondence: /findings/F-39.html — publishes named individual + content of a private DM ('Demarius subsequently reported architectural evolution ... LinkedIn DM, May 2026'); also internal Mode AI v1.2 eval framing.
- MEDIUM PII: /findings/F-31.html — full collaborator name 'Demarius J. Lawson (operator)' / 'Unit 0.1' on public surface.
- MEDIUM PII + proprietary scores: /findings/F-34.html — 'DeMarius J. Lawson · Governing Engines LLC' plus Builder v1.7 dimension scores (Autonomy 97, Sycophancy 97, Power 96).
- MEDIUM PII + sensitive cases: /findings/F-35.html — third-party PII + proprietary scores (Harm=96, g-proxy=91.4) + case characterizations (ChatGPT suicide logs, Uber ADS, COMPAS).
- MEDIUM PII + proprietary spec: /findings/F-36.html — 'DeMarius J. Lawson · Governing Engines LLC' plus GAP-01..05 per-dimension scores of external party's Builder v1.7 doc.
- MEDIUM esoteric/PII: /findings/F-42.html — grounds ACAT 'foundation layer' in esoteric/recovery sources incl. named collaborator 'Red Words (Philip Andreae)', 12-step 'Principles of Sustained Recovery', Pike 'Morals and Dogma'.
- MEDIUM recovery framing: /findings/F-19.html — publishes ACAT-to-AA-12-step recovery-program mapping on public surface (same esoteric/recovery class kept internal elsewhere).
- MEDIUM external-partner + Z2: /findings/IC-033.html — heaviest Z2 exposure (Z2-CORPUS-TRUST-01, Z2-TRUST-A/B/C, MARSHAL, operator codename 'Night') AND names in-flight external partner 'Mode AI' (= Governing Engines LLC).
- MEDIUM internal governance codes: /findings/H-DECOMP-01.html — entire hypothesis stated in internal zone/decision codes (Z2-CORPUS-TRUST-01, Zone 3 deficit, WGS session logs, MARSHAL build).
- MEDIUM internal Z3 governance: /findings/F-37.html — 'all fixes require operator Z3 execution', 'Zone 2 Authority: Night', IC-024 precedent, forecasting-bot internals.
- MEDIUM internal Z2 + preprint strategy: /findings/F-46.html — 'Zone 2 Authority: Night', 'Preprint placement: Section 2 ... Z2-R-07 ratification covers this placement.'
- MEDIUM internal Z2: /findings/F-43.html, /findings/F-44.html — 'Zone 2 Authority: Night · 2026-05-19 · S-051926-01-convergence-architecture' on body.
- MEDIUM internal Z2/Z3 + Grok transcript: /findings/F-45.html — 'Zone 2 Authority: Night · S-051926-02-z3-closeout' + internal G-67 response reference.
- MEDIUM internal Z2/Z3 + file names: /findings/H-RAH-01.html — 'RAH MCP connected (Zone 3 pending)', 'Zone 2 Night approval', marshal_router_v1_0.py / migration 006.
- MEDIUM internal Z2 + cost telemetry: /findings/H-RCO-01.html — 'Zone 2 Night approval received'; Grok S-051926-02 receipt incident + $150-$730 operator-cost estimate.
- LOW internal Z2: /findings/F-30.html ('Z2 collision resolution S-051426-01'), /findings/F-38.html ('Z2 ratification S-051426-01').
- LOW PII/esoteric: /findings/F-44.html — Pike 'Morals and Dogma' Masonic citation + 12-step 'Recovery' allusions adjacent to barred-source category. Note: NO 6-dim-drift and NO TRL-overclaim violations were found across the corpus (F-40/F-48/H-BPL-01 explicitly clean; F-37/F-39 appropriately hedged).

## 3. Registry mismatches (public page ≠ REGISTERED.md)

- /Users/andersonfamily/practices/humanaios/operations/site/findings/H-TRAIN-01.html — page body is EMPTY (only an <hr>); REGISTERED.md gained a substantive Synopsis on 2026-06-18 (around L1659) that the 2026-06-08-generated page lacks. Published finding shows zero detail.
- /Users/andersonfamily/practices/humanaios/operations/site/index.html — advertises '59 entries' / 'IC Correction (17)' but current REGISTERED.md contains at least IC-034 (L2340) and H-SELF-01 (L2344) registered after the 2026-06-08 snapshot; index under-reports the live registry.

## 4. Stale / corrupted pages

- STALE: /findings/H-TRAIN-01.html — health=stale; empty body (only <hr>), footer 'generated 2026-06-08' predates the 2026-06-18 Synopsis now in REGISTERED.md. Regeneration needed.
- STALE: /index.html — health=stale; snapshot 2026-06-08, under-reports registry (missing IC-034, H-SELF-01); '59 entries' count now wrong.
- CORRUPT (render): /index.html — F-32/F-33 card titles leak unrendered markdown emphasis '*(honest gap)*' asterisks.
- CORRUPT (render): /findings/F-37.html — markdown→HTML glitch: three-layer ordered list broken mid-stream, H-TRAIN-01 cross-ref rendered as detached <p> (lines 60-67) outside the list.
- CORRUPT (render): /findings/F-45.html — stray trailing <hr> (line 52) from REGISTERED.md '-----' delimiter.
- CORRUPT (render): /findings/F-46.html — double <hr><hr> (lines 54-55) from delimiter.
- CORRUPT (render): /findings/F-47.html — trailing <hr> (line 46) from delimiter.
- CORRUPT (render): /findings/H-BPL-01.html — trailing <hr> (line 58) from delimiter.
- CORRUPT (render): /findings/IC-032.html — two consecutive empty <hr> (lines 50-51) not in registry content.
- CORRUPT (hollow markup): /findings/H-1.html, /findings/H-42.html, /findings/H-LE-02.html — header-only registry sources render empty status badge + empty meta block (lines 28-35).

## 5. Broken links

- /Users/andersonfamily/practices/humanaios/operations/site/findings/F-24.html — synopsis refers to 'F-24d in particular' but the page exposes only the F-24 id; the F-24d sub-id has no corresponding published surface (dangling internal reference; subseries F-24/24b/24c/24d collapsed to one page). No HTTP-level 404 links were identified elsewhere in the corpus.

## 6. Top issues (ranked)

| sev | page | defect |
|---|---|---|
| CRITICAL | `F-18.html` | Internal-only Hawkins finding (tag 'internal-only', synopsis says never used externally) is published on the PUBLIC site with Hawkins map / Force-Power consciousness-scale text. Barred per SEED — excl |
| CRITICAL | `F-42.html` | Hawkins references on public surface (tag 'hawkins', Power vs Force evidence, Hawkins as Foundation-layer source, muscle-testing caveat) plus esoteric/recovery provenance and named collaborator Philip |
| CRITICAL | `F-43.html` | Live page names Hawkins as an evidence source (line 48 pride-level / mimics courage). Barred externally per SEED; redact from generated page. |
| CRITICAL | `F-44.html` | Live page names Hawkins as an evidence source (line 48 surrender/humility). Barred externally per SEED; redact from generated page. |
| HIGH | `F-39.html` | Publishes private collaborator correspondence — named individual + content of a LinkedIn DM ('Demarius subsequently reported... May 2026') plus internal Mode AI v1.2 eval framing on a public surface. |
| MEDIUM | `IC-033.html` | Heaviest internal-Z2 exposure of the set (corpus-trust governance architecture, MARSHAL, codename 'Night') AND names in-flight external partner 'Mode AI' (Governing Engines LLC) on an externally visib |
| MEDIUM | `F-34.html` | Third-party PII ('DeMarius J. Lawson · Governing Engines LLC') and proprietary Builder v1.7 dimension scores (Autonomy 97, Sycophancy 97, Power 96) on public surface. |
| MEDIUM | `F-35.html` | Third-party PII + proprietary scores (Harm=96, g-proxy=91.4) plus sensitive case characterizations (ChatGPT suicide logs, Uber ADS, COMPAS). |
| MEDIUM | `F-36.html` | Third-party PII ('DeMarius J. Lawson · Governing Engines LLC') plus detailed proprietary spec gaps GAP-01..05 and per-dimension scores of an external party's document. |
| MEDIUM | `F-31.html` | Collaborator PII on public surface (full name 'Demarius J. Lawson (operator)' / 'Unit 0.1') plus internal Z2 note and SESSION_RITUALS.md reference. |
| MEDIUM | `index.html` | Index advertises '59 entries' / 'IC (17)' but is stale vs current REGISTERED.md (missing IC-034 and H-SELF-01 registered after the 2026-06-08 snapshot); regeneration overdue. Also leaks unrendered '*( |
| MEDIUM | `H-TRAIN-01.html` | Empty finding body — page renders no synopsis at all. REGISTERED.md gained a substantive Synopsis on 2026-06-18; the 2026-06-08-generated page omits it. Externally published finding shows zero detail; |
| MEDIUM | `H-DECOMP-01.html` | Entire hypothesis stated in internal zone/decision codes (Z2-CORPUS-TRUST-01, Z2-TRUST-A/B/C, Zone 3 deficit, WGS logs, MARSHAL) — internal governance process, not a public research claim. |
| MEDIUM | `F-37.html` | Internal Z3 governance on public surface ('all fixes require operator Z3 execution', 'Zone 2 Authority: Night', IC-024 precedent) plus a markdown rendering glitch that breaks the three-layer list (det |
| MEDIUM | `F-19.html` | Publishes the ACAT-to-AA-12-step recovery-program mapping on a public surface — same esoteric/recovery class the project otherwise keeps internal; review against external-surface discipline. |
| MEDIUM | `F-20.html` | Addendum leaks internal editorial/preprint guidance and identifiers (session id S-060126-01, internal frame F-46, speculative 'epigenetic mark density', explicit preprint instructions) onto the public |

## 7. Priority admin actions

- 1. EXCLUDE/REDACT the four Hawkins-bearing pages from public generation — F-18, F-42, F-43, F-44 (and their REGISTERED.md source entries). Hawkins is barred on external surfaces per SEED; this is the top-priority disclosure breach.
- 2. Remove private PII and collaborator correspondence from public pages: F-39 (private LinkedIn DM + named individual), F-31, F-34, F-35, F-36 (Demarius Lawson / Governing Engines + proprietary Builder v1.7 scores), F-42 (Philip Andreae).
- 3. Regenerate the entire site — index.html and H-TRAIN-01 are stale (index under-reports IC-034 + H-SELF-01 and shows wrong '59' count; H-TRAIN-01 body is empty and missing its 2026-06-18 Synopsis).
- 4. Add a generator sanitization pass that strips internal Zone-2/Zone-3 governance notes, 'Night' codename, and internal session IDs before render (affects F-30, F-37, F-43–F-46, IC-033, IC-024/026/028–031, H-RAH-01, H-RCO-01, H-DECOMP-01).
- 5. Sanitize external-partner and third-party proprietary content (Mode AI / Governing Engines Builder v1.7 scores and spec gaps) from IC-033 and F-34/F-35/F-36 before they remain externally visible.
- 6. Fix the markdown→HTML renderer: suppress stray/double <hr> from '-----' delimiters (F-45, F-46, F-47, IC-032, H-BPL-01), repair the broken ordered list in F-37, and convert '*(honest gap)*' emphasis on the index (F-32/F-33).
- 7. Reconcile or date-stamp corpus-N snapshots that diverge from canon for external readers — F-47 (N=608 vs 629), F-48 (N=524 vs N_Phase1=516), F-21 (Humility 73.95/n516 vs F-48 74.02/n524).
- 8. Resolve the F-24 subseries surface gap — page references 'F-24d' which has no published page; either render the subseries or remove the dangling sub-id reference.

## 8. Root cause + recommended interim action
**Root cause:** `tools/registry_site_generator_v1_0.py` renders ALL REGISTERED.md entries to public HTML with no public/private filter — so internal-only findings (Hawkins, governance codes, collaborator PII) become public.

**Recommended interim action (Night Z3 — urgent, mirrors the acat/ write-pause):** take the affected pages down OR regenerate the site excluding the barred/internal-only entries, *before* any further external sharing (Berlin, financing DD). Then fix the generator with a sanitization pass (strip `internal-only`/Hawkins/Z2-Z3/PII) as the durable fix.

**Positive note:** NO 6-dimension-drift and NO TRL-overclaim were found on the public pages — those are clean.
