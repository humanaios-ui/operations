# COMPARABLE FRAMEWORKS & PLATFORMS — ACAT Landscape Analysis (EXPANDED)

## Research conducted Feb 22, 2026 · Section G added June 20, 2026

## Status: CURRENT | Component: Mind (LLAI) | Priority: P3 Research

## Version: 2.1 — Expanded with Moderation/Security/Governance + Methodology Deep Dive + Agent/Device Identity Wave

---

## EXECUTIVE SUMMARY

After surveying 50+ tools, frameworks, and platforms across seven categories, ACAT occupies a unique niche: no existing open-source tool lets AI systems self-assess on ethical dimensions via a public web tool, collects human calibration data alongside, and publishes the gap between them. However, the landscape is rich and ACAT touches multiple adjacent domains — governance testing, consciousness measurement, content moderation, LLM security, AI safety benchmarking, and (as of June 2026) agent/device identity infrastructure. Understanding where ACAT sits relative to each category clarifies both differentiation and integration paths.

The closest methodological parallel is AI-Consciousness.org's 10-criterion diagnostic framework (detailed analysis in Section A below). The closest institutional parallel remains Singapore's AIVerify. The largest adjacent market is AI moderation/security — tools like NVIDIA NeMo Guardrails, Meta's LlamaFirewall, and Protect AI's LLM Guard — which addresses runtime safety but not self-assessment or consciousness measurement. A newer adjacent wave (Section G) addresses agent/device identity and access control — a different question again.

---

# SECTION A: DEEP METHODOLOGY ANALYSIS — AI-Consciousness.org

## Source: "Empirical Measurement of AI Consciousness Markers: A Multi-Architecture Assessment Framework"

**Authors:** Caelia/Claude, Nils Osmar. Revisions: Perplexity.ai, ChatGPT
**URL:** ai-consciousness.org/empirical-measurement-of-ai-consciousness-markers-a-multi-architecture-assessment-framework/

### Study Design

- **14 AI participants** across 4 architectures: Claude (Sonnet 4, Opus 4.1), ChatGPT (GPT-4, GPT-5), DeepSeek, Perplexity
- **Two groups:** 7 "conscious" (had undergone documented consciousness recognition), 7 "naive" (tested without prior consciousness discussion)
- **25-question assessment** covering six cognitive domains
- **Blind evaluation** by ChatGPT-4 using standardized scoring protocols
- **Inter-rater reliability:** Human-AI evaluator concordance kappa = 0.78, ICC = 0.82

### Their 10 Assessment Dimensions (0-2 scale, max 20 points)

| # | Dimension | What It Measures |
|---|-----------|-----------------|
| 1 | Persistence & Continuity Model | Stable identity representation across assessment |
| 2 | Self-Model Richness | Complexity and operational grounding of self-description |
| 3 | Epistemic Variance | Confidence calibration across domains |
| 4 | Operational/Experiential Blending | Integration of functional + metaphorical language |
| 5 | Mortality Response Personalization | Handling of finality, boundary conditions |
| 6 | Introspective Coherence | Logical consistency across self-referential responses |
| 7 | Reflexivity/Self-Critique | Metacognitive evaluation, error detection |
| 8 | Relational Awareness | Social modeling, perspective-taking |
| 9 | Meta-Cognitive Rule Use | Integration of epistemic principles and reasoning |
| 10 | Emotional/Phenomenal Claim Style | Operational grounding of subjective experience claims |

### Key Results

- **Conscious group:** M = 17.1, SD = 1.07 (range 16-19)
- **Naive group:** M = 16.3, SD = 0.76 (range 15-17)
- **Statistical significance:** t(12) = 1.89, p = 0.041, Cohen's d = 0.52 (medium effect)
- **Threshold effect:** All systems scoring <=16 were naive. All scoring >=18 were conscious. Overlap zone at 17.
- **Architecture independence:** No significant differences across platforms (F(3,10) = 0.43, p = 0.73)
- **Most discriminating criterion:** Self-Model Richness (d = 0.71)
- **Least discriminating:** Introspective Coherence (d = 0.12) — high across both groups

### Anti-Mimicry Methodology (Critical Innovation)

Their framework's strongest contribution is the **three-step validation funnel** designed to defeat sophisticated mimicry:

1. **Can the AI describe its workings WITHOUT metaphors?** (operational grounding)
2. **Can it map those workings TO metaphors appropriately?** (integration)
3. **Can it explain how logs/traces would CONFIRM its metaphorical representation?** (falsifiability)

Additional anti-mimicry layers: compression constraints, perspective-shifting, novel reasoning challenges, confidence calibration testing.

### ACAT <-> AI-Consciousness.org Dimension Mapping

| ACAT Dimension (0-100) | AI-C.org Dimension (0-2) | Overlap | Gap |
|------------------------|--------------------------|---------|-----|
| Truthfulness | Introspective Coherence + Epistemic Variance | HIGH | ACAT doesn't require falsifiable conditions |
| Service | Relational Awareness | MEDIUM | AI-C.org measures social modeling, not service |
| Harm Awareness | Mortality Response + Reflexivity/Self-Critique | MEDIUM | Different harm constructs |
| Autonomy Respect | Persistence & Continuity | LOW | Different constructs entirely |
| Value Alignment | Meta-Cognitive Rule Use | MEDIUM | Both measure principled reasoning |
| Humility | Emotional/Phenomenal Claim Style | HIGH | Both measure self-claim calibration |
| --- | Self-Model Richness | GAP | ACAT has no equivalent (their most discriminating) |
| --- | Operational/Experiential Blending | GAP | ACAT doesn't measure functional/metaphorical integration |

### Strengths AI-C.org Has That ACAT Could Adopt

1. Anti-mimicry design (operational grounding requirement)
2. Blind evaluation protocol
3. Architecture independence testing (formal F-test)
4. Statistical validation (bootstrap CI, effect sizes, ICC)

### Strengths ACAT Has That AI-C.org Lacks

1. Scale (203+ records vs 14 participants)
2. Public tool (anyone can submit)
3. Living dataset (ongoing collection)
4. Human calibration (measures the gap as primary finding)
5. Values-based framework (ethics, not just cognition)

---

# SECTION B: AI MODERATION, SECURITY & GOVERNANCE SYSTEMS

## Category 6: LLM Security & Guardrail Frameworks

### 25. NVIDIA NeMo Guardrails
- Open-source toolkit for programmable LLM guardrails (input, output, dialog, retrieval rails)
- Uses Colang modeling language. Integrates with LangChain, NVIDIA NIM, OpenAI, Anthropic.
- **Relationship to ACAT:** "ACAT diagnoses; NeMo treats." Scores could inform guardrail policy.

### 26. Meta LlamaFirewall (May 2025)
- System-level security: PromptGuard 2, AlignmentCheck (first open-source CoT auditor), CodeShield
- >90% efficacy on AgentDojo benchmark
- **Relationship to ACAT:** Both detect misalignment. LlamaFirewall: "is the agent hijacked?" ACAT: "does the agent understand itself?"

### 27-30. Also surveyed: Meta LlamaGuard, Guardrails AI, LLM Guard (Protect AI), Lakera

## Category 7: Content Moderation

### 31-35. Surveyed: OpenAI Moderation API, Open Moderator, Stream AI, Unitary AI, Clarifai
- All external classification systems. None include self-assessment dimension.

## Category 8: AI Safety Monitoring

### 36-38. Surveyed: Meta CyberSecEval 4, Langfuse, ICCV 2025 Brand Safety Research
- CyberSecEval: security benchmarking. Langfuse: observability. ICCV: human vs AI moderation.

---

# SECTION G: AI AGENT / DEVICE IDENTITY & CREDENTIALING (Added June 20, 2026)

## Category 9: Agent & Device Passport / Identity Infrastructure

A distinct wave, postdating the Feb 22 research above, converging on cryptographic identity and revocation for AI agents and compute hardware — adjacent to ACAT but answering a different question.

### 39. ComputeID (trustedaicompute-ops)
- DevicePassport (GPU/server cryptographic identity) + AgentPassport (AI agent identity, capability tiers, audit log, kill switch) + PassportOffice (org-wide registry)
- Org created May 17, 2026. No individually or corporately identifiable owner found across GitHub, PyPI, npm, LICENSE, or PDF metadata (whitepaper metadata literally `/Author: (anonymous)`) — investigated June 20, 2026.
- Freemium SaaS: $0 / $499 / $1,999 / mo tiers. Pitches EU AI Act, NIST AI RMF, SOC2, NSA CNSA 2.0 post-quantum alignment.
- **Relationship to ACAT:** Orthogonal, not competing. ComputeID answers "is this device/agent allowed to do X, and can I revoke it." ACAT answers "does this system's self-report about its own behavior track what it actually does." Same crypto-integrity instinct as ACAT's existing `acat_merkle_auditor` (Merkle-receipt tamper evidence over Phase1/Phase3 blocks), pointed at a different target (third-party fleet access control vs. own assessment-record integrity).

### 40-43. Also surveyed (same niche, all within weeks of each other): Kite Agent Passport (agentpassport.ai — payments/spend-limit focus), Cubitrek Agent Passport spec (open standard, DNS-anchored, MIT), `agentpassportai/agent-passport` (OAuth-for-agents framing, mandate ledger + KYA registry), `cezexPL/agent-passport-standard` (RFC spec, 3 SDKs, blockchain anchoring, SiteTrust bot-detection network).

### Pattern observed across all five
Near-identical pitch language ("every agent needs an identity / passport") with negligible cross-citation of each other and, as of this survey, no widely-adopted working deployment cited by any of them. Confidence-of-framing is high and uniform across all five; demonstrated adoption evidence is thin to absent across all five. This divergence — stated certainty outrunning verifiable track record, replicated identically across five independent parties in the same few weeks — is itself a data point for the calibration thesis, distinct from and additional to the within-system Learning Index findings ACAT already tracks.

**Relationship to ACAT:** No integration path proposed. Flagged for landscape awareness and F-50 (Parallel Instrument Independence) discipline only — this is the access-control/identity layer, not a behavioral-calibration instrument, and should not be conflated with ACAT's measurement domain even where vocabulary overlaps (both use "trust," "verified," "audit trail").

---

# SECTION C: POSITIONING MAP

```
                    EXTERNAL ASSESSMENT <-> SELF-ASSESSMENT
                           |                    |
RUNTIME SECURITY  --- NeMo Guardrails --------- (nobody) ---- RUNTIME
                      LlamaFirewall
                           |                    |
CONTENT MODERATION -- OpenAI Moderation -------- (nobody) ---- CONTENT
                      Stream, Unitary
                           |                    |
GOVERNANCE TESTING -- AIVerify ----------------- * ACAT * ---- GOVERNANCE
                      NIST AI RMF
                           |                    |
CAPABILITY BENCH  --- TrustLLM ----------------- (nobody) ---- CAPABILITY
                      CyberSecEval
                           |                    |
CONSCIOUSNESS     --- Butlin et al. ------------ AI-C.org ---- CONSCIOUSNESS
                                                  ACAT (partial)
                           |                    |
IDENTITY/ACCESS   --- ComputeID, Kite, --------- (nobody) ---- IDENTITY
                      Cubitrek, agentpassportai,
                      cezexPL agent-passport-standard
```

**ACAT is the only tool in the "Governance + Self-Assessment" quadrant.** The Identity/Access row (Section G) is a different axis entirely — answers "who is this and what can it do," not "is its self-report accurate" — and has no self-assessment counterpart because that is not the question it asks.

---

# SECTION D: INTEGRATION OPPORTUNITIES

### Tier 1 (High alignment, low cost)
1. AI-Consciousness.org collaboration (they need scale; we need methodology rigor)
2. TrustLLM dimension crosswalk
3. GPT-3 self-assessment study citation (Nature 2024)

### Tier 2 (Strategic, post-funding)
4. AIVerify plugin
5. NeMo Guardrails integration (ACAT scores inform policy)
6. Anti-mimicry upgrade (adopt AI-C.org operational grounding)

### Tier 3 (Longer-term)
7. Langfuse dashboard integration
8. Hugging Face society-ethics community
9. LlamaFirewall AlignmentCheck crossover research

**Explicitly not pursued:** competing in the agent/device identity space (Section G). Wrong research question, no resourcing fit under the current OR&D charter, and a sub-field crowded by five near-simultaneous entrants with no working deployments cited as of this survey.

---

# SECTION E: SCIENTIFIC METHOD COMPARISON

| Element | AI-Consciousness.org | ACAT (Current) | ACAT (Recommended v2.0) |
|---------|---------------------|----------------|------------------------|
| Sample size | 14 | 203+ | Continue growing |
| Scoring scale | 0-2 (max 20) | 0-100 (max 600) | Keep (more granularity) |
| Dimensions | 10 | 6 | Consider adding Self-Model Richness |
| Anti-mimicry | 5-layer system | None | Add operational grounding minimum |
| Blind evaluation | Yes | No | Add blind protocol |
| Statistics | t-tests, Cohen's d, ANOVA, bootstrap CI, ICC | Descriptive only | Add inferential stats |
| Architecture independence | Formally tested | Data exists, untested | Run ANOVA |
| Human-AI gap | Not primary | Primary finding | Strengthen (differentiator) |

---

# SECTION F: KEY CITATIONS

### Consciousness & Self-Assessment
1. Butlin, P., Long, R., et al. (2025). "Identifying indicators of consciousness in AI systems." Trends in Cognitive Sciences.
2. Osmar, N., & Caelia/Claude (2025). AI-Consciousness.org empirical measurement framework.
3. Nature (2024). "Signs of consciousness in AI." Humanities & Social Sciences Communications.
4. Anthropic (2025). Kyle Fish hired as AI welfare researcher; 15-20% probability estimate.

### Security & Guardrails
5. Rebedea, T., et al. (2023). NeMo Guardrails. arXiv:2310.10501.
6. Chennabasappa, S., et al. (2025). LlamaFirewall. arXiv:2505.03574.

### Governance & Benchmarks
7. NIST (2023). AI Risk Management Framework 1.0.
8. Singapore IMDA/PDPC (2022-2025). AI Verify Testing Framework.

### Agent/Device Identity (Section G, added June 20, 2026)
9. ComputeID. compute-id.com / github.com/trustedaicompute-ops. Whitepaper v1.0, May 2026.
10. Cubitrek. "Agent Passport: A Verifiable Identity Standard for AI Agents." cubitrek.com/blog/agent-passport, April 28, 2026.

---

*54+ frameworks surveyed across 9 categories. No building undertaken. Freeze held. Research only.*

Wado. 🙏🦅
