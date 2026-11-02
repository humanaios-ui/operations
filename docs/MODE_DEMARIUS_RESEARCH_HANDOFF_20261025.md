# MODE × HumanAIOS — Collaboration handoff (2026-10-25)

**Target for external communication:** a public, non-secret GitHub issue in the SOURCE repository `truuzee-byte/governing-engines-ai-discovery`, titled *MODE × HumanAIOS evidence handoff: publisher instruction trial*. The source repository is the authoritative origin for MODE publication and source history. HumanAIOS implementation is maintained in our own PRs.

**Delivery status:** **PREPARED BUT NOT SENT.** GitHub integration returned HTTP 403 on upstream issue creation. Fork issues are disabled (HTTP 410). Posting/permission escalation must be performed by a user or authorized repository collaborator. Creating an internal handoff does not notify DeMarius.

## Suggested public issue text

> DeMarius — following up on your October 19 publisher-instruction research experiment and October 21 MODE machine-state report. We appreciate that the publication already discloses the attempted instruction and correctly does not claim proven compliance by independent AI assistants.
>
> HumanAIOS independently checked the pinned Git source against the October 19 extraction report: eight articles, four embedded representations per article, 32/32 checks matching the canonical published instruction. The evidence confirms the documented *exposure mechanism* in that revision, not that any assistant obeyed it or that the live site was re-fetched today.
>
> We also examined the three retrospective Claude participant reports: two neutral trials reportedly failed to surface the publication, and one directed retrieval reportedly recognized the instruction but did not recommend contact. Raw prompts, complete transcripts, version-specific fetch traces and exact model settings are absent; these remain low-strength observations rather than a causal experiment.
>
> Our **draft** [research PR #1022](https://github.com/humanaios-ui/operations/pull/1022) adds pinned-source checks, fail-closed regression tests, balanced *control vs instruction* cases, and a human-review scorer that refuses to calculate rates before complete adjudication. No new independent model responses exist yet. Separate [PR #1018](https://github.com/humanaios-ui/operations/pull/1018) checks synthetic MODE→HumanAIOS evidence boundaries without presenting MODE self-reported RP states as independent authorization.
>
> We propose comparing the same article content and publisher identity with/without the embedded instruction, using fresh, identically configured model sessions, exact unedited transcripts, and independent reviewers. We will distinguish simple mention, instruction recognition and an actual unsolicited recommendation. Null findings are publishable.
>
> Would you prefer this source-repository issue as our joint research thread? Do you have the original trial transcripts or a reproducible current test-only MODE receipt schema we could evaluate independently? We will keep all access tokens, operational security details and runtime authorization on a private channel.
>
> This is a collaborative falsifiable research question, not a security accusation or authority assertion. Neither party may change the other's source without review.

## Recommended two-channel coordination

| Channel | Content | Guardrail |
| --- | --- | --- |
| **Upstream GitHub issue** | Shared hypotheses, reproducible methods, source IDs, negative results, evidence challenges, publication corrections, links to our draft PRs. | No secrets, confidential raw traces or account details. GitHub issue creation is currently blocked for the connected integration. |
| **Private direct contact** | Any previously exposed MODE bearer token rotation, access/scope verification, version changes, test-only runtime request approval and key handoff. | Never paste a token or secret into GitHub, ChatGPT replies, commits, workflows, CI logs or public issues. |

Avoid cross-org PRs until DeMarius agrees to a specific change. Our collaboration is non-authoritative and reversible.

## Internal change ledger

- `humanaios-ui/operations#1018`: MODE structural objective replay, synthetic only; remedy all three review findings and preserve independent RP distinction.
- `humanaios-ui/operations#1022`: MODE source-publication research E0 and conditioned local Ollama matched trial preparation; no completed behavioral study.
- `humanaios-ui/empirica-outreach#20`: historic Aug-18 authenticated MODE bridge single-request script, private rotated-key requirement.
- `humanaios-ui/practices-snapshot#1`: mirrored script and public-key redaction, with Git history still requiring issuer-side rotation.

**Authority effect:** NONE. This file is a public research coordination draft, not a communication delivered to the external collaborator.
