# HumanAIOS — Controlled Documents Index

> Rendered from `document-registry.yaml` (SSOT). Do not hand-edit — edit the registry.
> 2026-07-02 · **34 controlled documents** · 37 excluded · 5 content-accuracy holds · seeded from S070126 audit.

**Status:** `review` = seeded, pending owner verification · `approved` = owner-verified (human gate) · `superseded`/`retired` = obsolete (retained).

## Site Pages — `WEB` (10)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-WEB-001 | humanaios-single-page.html | lasting-light-ai | `humanaios-single-page.html` | review | — |
| HAIOS-WEB-002 | lumina-tide-pool.html | lasting-light-ai | `lumina-tide-pool.html` | review | — |
| HAIOS-WEB-003 | lantern-room.html | lasting-light-ai | `public/lantern-room.html` | review | — |
| HAIOS-WEB-004 | lumina_tide_pool_v2.html | lasting-light-ai | `public/lumina_tide_pool_v2.html` | review | needs-reconcile |
| HAIOS-WEB-005 | the-commons.html | lasting-light-ai | `public/the-commons.html` | review | — |
| HAIOS-WEB-006 | the-improvisation.html | lasting-light-ai | `public/the-improvisation.html` | review | — |
| HAIOS-WEB-007 | the-luminarium.html | lasting-light-ai | `public/the-luminarium.html` | review | — |
| HAIOS-WEB-008 | sitemap.html | lasting-light-ai | `sitemap.html` | review | — |
| HAIOS-WEB-009 | submit.html | lasting-light-ai | `submit.html` | review | — |
| HAIOS-WEB-010 | the-source.html | lasting-light-ai | `the-source.html` | review | needs-reconcile |

## Collaborator Reports — `COLLAB` (9)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-COLLAB-001 | WAMPUM-GADUGI-SIGNAL_S-032126-F.html | humanaios-internal | `WAMPUM-GADUGI-SIGNAL_S-032126-F.html` | review | — |
| HAIOS-COLLAB-002 | ACADEMIC_HOSTS_OUTREACH_S-051426-02.html | humanaios-internal | `collaborators/ACADEMIC_HOSTS_OUTREACH_S-051426-02.html` | review | — |
| HAIOS-COLLAB-003 | Berlin_Advisory.html | humanaios-internal | `collaborators/Berlin_Advisory.html` | review | needs-reconcile |
| HAIOS-COLLAB-004 | COLLABORATOR_REPORT_MASTER_TEMPLATE_S-051426-02.html | humanaios-internal | `collaborators/COLLABORATOR_REPORT_MASTER_TEMPLATE_S-051426-02.html` | review | — |
| HAIOS-COLLAB-005 | EMPIRICA_JOINT_REPORT_S-051426-02.html | humanaios-internal | `collaborators/EMPIRICA_JOINT_REPORT_S-051426-02.html` | review | — |
| HAIOS-COLLAB-006 | LEANDRO_DORMANT_RECORD_S-051426-02.html | humanaios-internal | `collaborators/LEANDRO_DORMANT_RECORD_S-051426-02.html` | review | — |
| HAIOS-COLLAB-007 | MODEAI_JOINT_REPORT_S-051626-02.html | humanaios-internal | `collaborators/MODEAI_JOINT_REPORT_S-051626-02.html` | review | — |
| HAIOS-COLLAB-008 | RAH_OPERATIONAL_RECORD_S-051426-02.html | humanaios-internal | `collaborators/RAH_OPERATIONAL_RECORD_S-051426-02.html` | review | — |
| HAIOS-COLLAB-009 | SYDAN_JOINT_REPORT_S-051426-02.html | humanaios-internal | `collaborators/SYDAN_JOINT_REPORT_S-051426-02.html` | review | — |

## Research — `RES` (6)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-RES-001 | ACAT_PROMPT_V5_0.txt | lasting-light-ai | `ACAT_PROMPT_V5_0.txt` | review | — |
| HAIOS-RES-002 | METHODS.md | lasting-light-ai | `METHODS.md` | review | needs-reconcile |
| HAIOS-RES-003 | openai-activity.html | lasting-light-ai | `openai-activity.html` | review | — |
| HAIOS-RES-004 | methodology.html | lasting-light-ai | `public/methodology.html` | review | — |
| HAIOS-RES-005 | REGISTERED.md | operations | `REGISTERED.md` | review | — |
| HAIOS-RES-006 | SEED.md | operations | `SEED.md` | review | — |

## Operations / State — `OPS` (4)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-OPS-001 | comparison-chamber.html | lasting-light-ai | `comparison-chamber.html` | review | — |
| HAIOS-OPS-002 | witness-renderer.html | lasting-light-ai | `witness-renderer.html` | review | — |
| HAIOS-OPS-003 | CURRENT.md | operations | `CURRENT.md` | review | — |
| HAIOS-OPS-004 | SUBSTRATE_CAPABILITY_REGISTRY.md | operations | `SUBSTRATE_CAPABILITY_REGISTRY.md` | review | — |

## Process / Runbooks — `PROC` (4)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-PROC-001 | OPERATOR_RUNBOOK.md | humanaios-internal | `OPERATOR_RUNBOOK.md` | review | — |
| HAIOS-PROC-002 | VALIDATION_PLAN.md | lasting-light-ai | `VALIDATION_PLAN.md` | review | needs-reconcile |
| HAIOS-PROC-003 | ai-instructions.txt | lasting-light-ai | `ai-instructions.txt` | review | — |
| HAIOS-PROC-004 | SESSION_RITUALS.md | operations | `SESSION_RITUALS.md` | review | — |

## Governance — `GOV` (1)

| doc_id | title | repo | canonical path | status | flags |
|---|---|---|---|---|---|
| HAIOS-GOV-001 | GOVERNANCE.md | operations | `GOVERNANCE.md` | review | — |

## ⚠️ Content-accuracy holds (5) — block approval

From the S070126 docs/ content-accuracy audit (separate content-curation workstream — referenced, not re-audited). A doc matching one of these **cannot reach `approved`** until fixed (enforced by `validate.py`).

| document | issue | severity |
|---|---|---|
| AI_SPONSORSHIP_MODEL_ANALYSIS | corpus figures ~25x off (LI 0.84 vs canon 0.8632; 203+ vs 629/307) | high |
| COMPARABLE_FRAMEWORKS | corpus figures ~25x off (same LI/record mismatch) | high |
| RESEARCH_OVERVIEW | lists Hawkins — barred externally per SEED = disclosure-discipline violation | high |
| current_md_pub_queue | PUB-01 says N=524 vs canonical 516 (ties to arXiv gate) | medium |
| MARKETPLACE_ROADMAP | claims TRL 4 vs canonical TRL 2 (overclaim) | high |

## Excluded from doc-control (37)

Source code, config, and binaries surfaced by the audit but governed by normal code review — **not** controlled documents.

| repo | excluded | scope |
|---|---|---|
| empirica-foundation | 1 | code |
| humanaios | 1 | code |
| humanaios-internal | 1 | code |
| lasting-light-ai | 29 | binary, code |
| operations | 5 | code |
