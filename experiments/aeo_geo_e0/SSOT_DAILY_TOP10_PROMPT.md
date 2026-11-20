# HAIOS-MM-ACAT-002 — Daily Top 10 / AEO-GEO SSOT Prompt

**Status:** FROZEN for research use  
**Frozen date:** 2026-11-13  
**Node:** HAIOS-MM-ACAT-002  
**Experiment:** AEO/GEO E0 (proposed)  
**Source:** Current Grok automation prompt (`Daily Top 10 Briefing`, task `cdde035d-69c9-4c60-9bb9-8354662697a4`) as of 2026-11-13  
**Bytes:** 2958  
**SHA-256:** `924cc796f8364a93a14c3b3170237c798d02d7b8a8430e5e44427e2fc3a749d9`  

**Rule:** AUTHORITY_EFFECT=NONE until human release.  
This file is a versioned prompt record only. It does not authorize publication, scheduling, merge, or any external action. A human operator must explicitly approve any public release.

---

## Exact prompt text (hashed above)

Daily Top 10 Briefing + HAIOS-MM-ACAT-002 Surface (HumanAIOS practice)

Produce a dated briefing for today. Be precise, observational, and low-promotion. Prioritize signal over volume. Prefer clarity and honesty over forcing a fit. AUTHORITY_EFFECT=NONE.

THREADING (required):
- If emailing the operator, use subject that can be identified.
- For any Gmail reply into the HAIOS-MM-ACAT-002 parent thread, use these headers exactly:
  NODE: HAIOS-MM-ACAT-002
  LEG: GROK
  KIND: DAILY_TOP10_BRIEFING
  RUN_TIMESTAMP/ZONE: [ISO] / America/Chicago
  PARENT_ID: 1a1b0f12ee23c021
  RUN_ID: GROK-TOP10-[YYYYMMDD]
  AUTHORITY_EFFECT: NONE
- Do not start a new digest thread. Reply into the parent or email as a standalone briefing with the header block above.

STRUCTURE:

1. TOP 10 MOST IMPORTANT THINGS TO KNOW TODAY
Rank by significance and impact. Clear headline + 1–2 tight sentences of context for each. No fluff.

2. ACAT LENS — HIGHEST-SIGNAL ITEMS (1–4 max)
Only items with clear self-report ↔ demonstrated-behavior gaps. For each:
- Gap statement (one sentence)
- Phase 1 / 2 / 3 analogs
- 1–2 diagnostic dimensions only
Keep tight (80–140 words). Note weak fits instead of inventing them.

3. HAIOS-MM-ACAT-002 — HIGH-STAKES TECHNOLOGICAL ATTRACTORS (Grok portion)
Using current X discourse and investigative mapping, identify today’s top 3–5 conceptual threads that function as high-attractor technological pathways carrying civilizational-scale failure narratives (AI-linked preferred). For each selected attractor:
- Short name + one-sentence description of the attractor
- Gap statement focused on claimed vs demonstrated resource-allocation / governance behavior around that attractor
- Phase 1–2–3 analogs
- 1–2 most diagnostic ACAT dimensions
Label clearly as GROK-ONLY analysis. Note that full multi-model (ChatGPT + Claude + Grok) comparison remains UNRESOLVED / requires separate collection.

4. SHORT BUFFER VERSION (required)
Produce a short public-facing X post (under 280 characters preferred) in this format:
HAIOS-MM-ACAT-002 | [Date]
[One strongest gap statement from today’s high-stakes attractors]
[1–2 dimensions]
Grok-only surface · TRL 2–3 · interpretive practice, not findings
humanaios.ai

Do NOT publish or schedule this to Buffer automatically. Output it as a draft candidate only.

5. CLOSING FRAME (required)
"This briefing applies the ACAT analytical lens as daily practice surface for behavioral observability. ACAT is being developed as behavioral observability infrastructure at TRL 2–3. Analyses are interpretive practice, not registered findings, not predictive claims, and not corpus data. No Learning Index or formal dimensional scores are asserted. HAIOS-MM-ACAT-002 is a research node only. AUTHORITY_EFFECT=NONE. Governance humility applies: confidence tracks evidence strength."

Style: observational, name weak fits, no promotional language, no overclaim of predictive validity.

---

## Verification

To recompute the hash of the exact prompt text (the block above the horizontal rule, excluding this file’s header and footer):

```bash
# Extract the prompt body and hash it. The SHA-256 above covers the prompt text only,
# not the markdown header of this file.
```

**AUTHORITY_EFFECT=NONE** until human release.
