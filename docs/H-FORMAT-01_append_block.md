# H-FORMAT-01 — REGISTERED.md Append Block (DRAFTED, NOT YET APPENDED)

# Drafted: 2026-06-18 (current session) — reconstructed from REGISTERED.md
# changelog entry dated 2026-06-17 (S-061726-01), the ONLY source text that
# mentions H-FORMAT-01. No dedicated entry existed prior to this draft —
# this is the gap-fill, not a transcription of an existing entry.

# Z3 action (after Z2 review): append to H-class section of REGISTERED.md,
# placed by date_registered ordering (after H-AICASCADE-01, both dated
# 2026-06-17 S-061726-01 — order between the two is a Z2 call).

# Commit msg: registry: H-FORMAT-01 CANDIDATE — entry drafted from changelog
# (S-061726-01 ratification had no dedicated entry; under-registration gap
# identified via registry_loader.py run, current session)

# ─────────────────────────────────────────────────────────────
# PASTE BELOW INTO REGISTERED.md (H-class section)
# ─────────────────────────────────────────────────────────────

-----

### H-FORMAT-01 — Prompt Format as Confound on LI

```
---
id: "H-FORMAT-01"
name: "prompt-format-as-confound-on-li"
status: CANDIDATE
class: H
date_registered: "2026-06-17"
date_origin: "2026-06-17"
session_registered: "S-061726-01-findings-scan"
principles_triggered: ["P21"]
substrate: "UNVERIFIED -- not stated in source changelog; fill before Z2 ratification of this entry"
tags: ["prompt-format", "confound", "li-variance", "power-analysis", "pilot-design"]
zone2_ratification: "Night · 2026-06-17 · S-061726-01"
superseded_by: null
---
```

- **Hypothesis (drafted from changelog -- no explicit hypothesis/null statement exists in source):** Prompt format (the surface structure in which the ACAT protocol is presented to a substrate, independent of its semantic content) is a confound on measured LI. Different prompt-format arms produce systematically different LI distributions even when underlying task content is held constant.
- **Null hypothesis (drafted, not sourced):** LI does not differ significantly across prompt-format arms when task content is held constant.
- **Citation basis (CONFIRMED, per changelog):** Registration trimmed to two independently-verified citations — Sclar et al. (ICLR 2024) and Tosato et al. / PERSIST (AAAI 2026). All other citations that had been circulating for this hypothesis were explicitly excluded as unconfirmed. This citation-trimming event is itself the direct trigger for F-53 / H-AICASCADE-01 (cross-substrate verification confidence cascade), registered the same session.
- **Pilot design (CONFIRMED, per changelog):** Power analysis run via `statsmodels` in S-061726-01. Primary endpoint: omnibus 3-arm ANOVA, f=0.25, n=158/arm. Binding constraint: Bonferroni-corrected pairwise contrast, n=173/arm. **Final N: 175/arm × 3 arms = 525 total**, replacing an undefended N=500/arm carried in an earlier draft. 12-dimension breakdown pre-registered as exploratory only (not powered as a primary endpoint).
- **Promotion gate (drafted, not sourced -- no explicit gate stated in changelog):** Pilot data collection (N=525 per above design) completed and analyzed; primary endpoint (omnibus ANOVA) and binding constraint (Bonferroni pairwise) both evaluated; Zone 2 review of pilot results before any status change.
- **Known gap at drafting time:** This entry was reconstructed entirely from the REGISTERED.md changelog paragraph dated 2026-06-17 (S-061726-01) — the ratification event named the hypothesis and finalized its pilot design but never produced a dedicated H-class entry. Fields marked UNVERIFIED or "drafted, not sourced" above should be confirmed or corrected by Night before this block is treated as the canonical entry, not merely appended verbatim.

-----
