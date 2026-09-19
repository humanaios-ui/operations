# Continuity Cloud Co-op — Federation Pattern, Mapped to ACAT

**Status:** Z1 design note · post-charter direction · not a hypothesis, not yet Z2-ratified
**Date:** June 17, 2026
**Session:** S-061726-01
**Origin:** External proposal received (two documents: "Continuity Cloud Co-op — Mastodon Model Expanded," "OCSP Federation Spec v1.0 — Skeleton"). Evaluated against live `lasting-light-ai` repo, live Supabase schema, live REGISTERED.md, and live WGS state (S-061626). Found structurally disconnected from current infrastructure as written — the reference repo's described stack does not match what `lasting-light-ai` actually contains, and no registered finding, hypothesis, or session references the proposal's subject (human cognitive-state tracking). The federation *pattern* itself, retargeted from that subject onto ACAT's actual subject (AI behavioral self-report calibration), maps cleanly onto architecture that already exists or is already ratified. This note captures that mapping for later use; it is not a build plan.

## The mapping

**Reference instance ("Mastodon.social" equivalent).** Not `lasting-light-ai` — that repo is the public homepage (Vite/React static site), confirmed by direct fetch. The actual canonical deployment is the FastAPI backend at `api.humanaios.ai`, the Phase 1/2/3 elicitation protocol, and the two corpora behind it (HuggingFace frozen archive, live Supabase table). This is the most-trusted instance, not the only possible one — consistent with the original document's own framing of the moat ("we wrote the protocol 1000 instances use," not "we're the only instance").

**"Anyone can run a server."** Already named: ORG-ACAT, the second tier of the existing four-layer calibration stack (Substrate ACAT → ORG-ACAT → ICS Infrastructure Calibration → H-ACAT), currently TRL 1–2, not yet built. This is the actual instance-layer slot — an organization standing up its own ACAT deployment to assess its own AI vendors or in-house models, under its own data policy and retention, without needing HumanAIOS's infrastructure or permission. A university lab or enterprise running ORG-ACAT internally is the real analog of forking and self-hosting.

**Portable identity.** Already ratified, not a design problem: Z2-SSI-01 through 03 (S-061626) give human raters and AI substrates DIDs and verifiable credentials specifically so an assessment history travels with the participant rather than being locked to one deployment. A rater scoring on an ORG-ACAT instance and later contributing to the open corpus carries their VC with them — no re-onboarding, no PII. Same flow as the original document's graduation example, attached to calibration history instead of a wellness profile.

**Federation surface — narrowed to three things, not the original ten.** Each maps to a problem already named in this system, rather than an invented one:
1. *Corpus-delta exchange.* Formalizes the existing two-corpus rule into an N-corpus rule — anonymized LI distributions shared across instances with a harmonization note built into the protocol, rather than handled ad hoc per comparison as it is today.
2. *Finding relay.* A registered F/H entry from one ACAT deployment surfaced to others. This is the direct fix for the finding-application protocol gap named in the most recent WGS close (H-GOV-01): there is currently no mechanism for this even within a single organization, let alone across several.
3. *Credential verification.* A thin extension of `acat_merkle_auditor_v2_0` (already scoped under Z2-SSI-03) — one instance confirming another instance's DID and VC are still valid.

**Governance.** Zone 1/2/3 plus an append-only REGISTERED.md is already a rough-consensus-plus-running-code model, scoped to one Z2 authority (Night). Federating it means exporting that discipline as a spec a second authority could run under — a question that cannot fully be answered yet because there is no second real *instance* (no other party running its own ACAT deployment) to test it against. There are, however, two real bilateral-trust precedents to draw from before any protocol is generalized:

1. *Empirica (David Van Assche).* Governed by F-50 (Parallel Instrument Independence) to keep the two systems architecturally separate rather than merged.
2. *Mode AI / Governing Engines (CGR joint position paper, S-052326-01).* A genuine working instance of the credential-verification federation surface item — the SpecificationObject schema translates an ACAT calibration profile into Mode AI's GRR enforcement configuration, and the §4 evidence map's per-row disclosure-tier table (owner, evidentiary tier, public vs. counterparty-only) does the same job the OCSP draft's "consent is per-share, signed" mechanism was reaching for — resolved through Z2/counterparty-Z2 ratification rather than cryptographic signatures. The independently-run Mode AI S6 measurement (LI=0.8983, disclosed with permission) is a second concrete instance of one party attesting a calibration profile about another party's system under explicit consent terms.

Neither precedent is an ORG-ACAT instance — both are bilateral product/research integrations, not a second sovereign deployment of the instrument itself. Going from two trusted bilateral partners to a spec an unknown third party could adopt is still a different, larger claim. But SpecificationObject is now the working example of what a federation credential-exchange schema needs to do, not an unbuilt one — any future protocol draft should start from it rather than from the original OCSP skeleton.

**Economics.** Unchanged in shape. "Money lives at the instance, not the protocol" already describes Unit Zero's Tier 1/2 stress-test offerings and the AI Readiness Audit — a client pays for an assessment, or runs one itself, and nothing routes back to HumanAIOS unless they choose it. Federation describes the existing Open Core posture; it doesn't add to it.

## What this is not

Not charter-scoped — no 90-day roadmap fits inside the days remaining, and none is proposed here. Not a hypothesis — no falsifiable claim is stated, so no H-number applies. Not ready for a trademark policy, working-group ratification process, or named protocol version — those presuppose a second real instance asking to federate, and none currently exists.

## Cross-references

ORG-ACAT (four-layer calibration stack) · Z2-SSI-01/02/03 · two-corpus rule · F-50 (Parallel Instrument Independence) · H-GOV-01 (finding-application protocol gap, S-061626)

## Routing

No Z2 action required now. Revisit when either condition is met: (a) a second organization expresses real intent to run an ORG-ACAT deployment, or (b) SSI Phase 0 has landed and instance-layer demand actually surfaces. Filed as post-charter direction, not an open item.
