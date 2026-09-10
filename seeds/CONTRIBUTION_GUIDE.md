# Seed Constitution — How to Contribute

The Seed Constitution for Responsible AI Development is an open draft, and we actively invite your feedback, amendments, critiques, and proposals.

This guide explains how to contribute through different channels and what we're looking for.

---

## What We're Looking For

### Strong Contributions Include:

1. **Specific text changes** — Don't just say "this is unclear"; propose exactly how you'd reword it
2. **Clear rationale** — Why does this change matter? What problem does it solve?
3. **Supporting evidence** — Examples, observed behavior, case studies, or measurement (when possible)
4. **Attribution** — Your name or "AI system + human principal" so we know who proposed it

### Common Types of Feedback:

- **Clarity amendments:** Language is ambiguous or hard to parse
- **Gap identification:** There's a principle we should add, or something contradicts existing HumanAIOS work
- **Behavioral calibration:** You've observed real-world situations where the stated intent doesn't match actual outcomes
- **ACAT cross-check:** You've evaluated the principle against behavioral dimensions (Autonomy, Community, Accountability, Transparency)
- **Integration notes:** How this principle might interact with governance, enforcement, or other parts of the HumanAIOS ecosystem

---

## Contribution Paths

### 1. **Substack Comments** (Most Casual)

**Best for:** Quick reactions, questions, high-level thoughts

**How:**
1. Go to the Seed Constitution post on [humanaios.substack.com](https://humanaios.substack.com)
2. Leave a comment directly on the post
3. We'll read it, and substantive comments may be featured in a follow-up post

**Example:**
> "Principle 3 (Least-Privilege Agency) resonates with what we've seen in [X case]. One clarification: does 'untrusted sources' include other AI systems in the same organization, or only external ones?"

---

### 2. **Writable Wall Submission** (Structured & Discoverable)

**Best for:** Formal amendments, detailed critiques, detailed new principles

**How:**
1. Visit [humanaios.ai/contribute](https://humanaios.ai/contribute)
2. Fill out the amendment form:
   - **Proposed change** (what text to add/modify/remove)
   - **Rationale** (why it matters)
   - **Evidence** (optional: examples or measurement)
   - **Attribution** (your name or team)
3. Submit; it enters the moderation queue
4. Accepted submissions appear in [Contributions Digest](#contributions-digest)

**Example:**
```
Proposed Change:
  Modify Principle 4 from "Purely declarative language..." to 
  "Purely declarative language without ongoing independent audit is..."

Rationale:
  The word "independent" clarifies that self-assessment is insufficient. 
  Observed in [X case where internal audit missed Y risk].

Evidence:
  Case study: [link]; ACAT assessment: [link]

Attribution:
  Alex Chen, Empirica Autonomy Team
```

---

### 3. **GitHub Issue** (Preferred for Technical Feedback)

**Best for:** Structural feedback, integration with governance, technical concerns

**How:**
1. Go to [github.com/humanaios-ui/operations/issues](https://github.com/humanaios-ui/operations/issues)
2. Click **New Issue** and select **Seed Amendment or Critique**
3. Fill out the template (includes sections for principle, rationale, evidence, ACAT assessment)
4. Submit; it's visible in the project and automatically linked to version history

**Why use this?**
- Creates an audit trail linked to the git history
- Enables discussion and threading
- Helps identify patterns across contributions
- Supports Z2 ratification workflow

---

### 4. **Simple Form** (Fastest)

**Best for:** Anonymous feedback, very quick thoughts, no preference for public attribution

**How:**
1. Visit [humanaios.ai/seed-feedback](https://humanaios.ai/seed-feedback)
2. Type your feedback in the short form
3. Optionally provide contact info
4. Submit; responses aggregate in our feedback digest

**Note:** Responses are attributed to "Anonymous" unless you provide a name.

---

### 5. **Direct Email** (Least Preferred)

**Best for:** Sensitive feedback or if you prefer private discussion first

**How:**
- Email [seeds@humanaios.ai](mailto:seeds@humanaios.ai) with your amendment and rationale
- We'll respond within 48 hours

**Note:** Unless you specify otherwise, we'll ask permission to move your feedback to a public channel (GitHub, Writable Wall, or Contributions Digest).

---

## What Happens to Your Contribution?

```
Your Contribution
       ↓
Moderation Check (relevance, civility, attribution)
       ↓
Contributions Digest (weekly summary)
       ↓
Z1 Proposer (Claude) reviews & aggregates
       ↓
Z1 Candidate Block created (with rationale & falsifier)
       ↓
Z2 Ratification (Night / Carly R. Anderson)
       ↓
Decision: ACCEPT / EDIT / REJECT (within 48 hours)
       ↓
If ACCEPTED → Version 0.2 (includes your change & attribution)
If EDITED → Re-review & re-ratification
If REJECTED → Documented with rationale → back to you (optional re-proposal)
```

---

## Contribution Digest & Versioning

**Weekly Digest (every Monday):**
We publish a summary of the strongest contributions, patterns, and debates at [humanaios.substack.com](https://humanaios.substack.com).

**Version Releases:**
- **v0.1** (current): Open for community input
- **v0.2** (planned, ~2 weeks): Incorporates accepted amendments
- **v1.0** (post-ratification): Final, community-endorsed version

---

## Tips for Strong Contributions

### ✓ Do:

- **Be specific.** Quote the exact text and propose the replacement.
- **Include rationale.** Tell us why this matters.
- **Cite evidence when possible.** A real example beats a hypothetical.
- **Use ACAT dimensions.** Frame your critique in terms of Autonomy, Community, Accountability, Transparency.
- **Be respectful.** We disagree gracefully and in good faith.
- **Reference existing work.** Link to REGISTERED.md, Moltbook, Observatory, etc., if relevant.

### ✗ Avoid:

- Generic praise ("Great document!") without specific feedback
- Vague critiques ("This doesn't work") without rationale
- Overly broad new principles without evidence
- Anonymous attacks or rhetorical framing designed to manipulate
- Duplicating existing issues (search first!)

---

## Questions?

- **"How long does review take?"** 48 hours for Z2 decision, then ~2 weeks to next version release
- **"Will my name be credited?"** Yes, unless you opt for anonymity
- **"Can I revise my proposal?"** Yes; comment on the issue, resubmit via Writable Wall, or email us
- **"What if my proposal is rejected?"** You get documented rationale and can re-propose after 48 hours

---

## Integration with HumanAIOS Governance

This Seed Constitution follows HumanAIOS governance practices:

- **Z1 (Proposer):** Claude AI agent aggregates feedback and proposes amendments
- **Z2 (Ratifier):** Night (Carly R. Anderson) ratifies or contests decisions
- **Z3 (Executor):** Teams implement accepted changes and measure outcomes

All decisions are logged in [REGISTERED.md](https://github.com/humanaios-ui/operations/blob/main/z1-inbox/REGISTERED.md) with timestamps and audit trail.

---

## Community Covenant

By contributing, you agree to:
- Treat this as a good-faith collaborative effort
- Assume best intentions from other contributors
- Focus on improving the substance, not scoring points
- Respect the HumanAIOS [Code of Conduct](https://github.com/humanaios-ui/operations/blob/main/CODE_OF_CONDUCT.md)

---

**Ready to contribute?** Start here:

1. **Quick thought?** → [Substack comments](https://humanaios.substack.com)
2. **Detailed amendment?** → [Writable Wall](https://humanaios.ai/contribute)
3. **Technical feedback?** → [GitHub Issue](https://github.com/humanaios-ui/operations/issues)
4. **Very quick feedback?** → [Simple form](https://humanaios.ai/seed-feedback)

---

*Last updated: 2026-09-10*  
*Maintained by: HumanAIOS Governance Team*
