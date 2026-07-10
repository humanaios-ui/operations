# BEHAVIORAL_GRAMMAR_V1.md

**Status:** Z1 DRAFT — not ratified, not canonical, not wired into any tool
**Produced:** S-071026 (Z1 draft seat, Claude)
**Revised:** S-070926 (Z1 draft seat, Claude) — §9 Implementation Closure added.
**TRL:** Being developed as TRL 2–3 behavioral observability infrastructure for HumanAIOS (per §7). This is TRL-2 conceptual formalization of existing TRL-3/4 practices; not a new capability.
**Requires:** Zone 2 ratification per P21 before merge into operations repo; an independent (non-self-administered) P30 interactive pass before ratification promotion beyond H-cand.
**Epistemic status of this document:** INTERPRETATION formalized into a proposal. The claim that the project’s existing artifacts implicitly converge on this grammar is a reading, not a registered finding. If ratified, the grammar becomes prescriptive going forward; it does not retroactively claim past artifacts were “written in” it. Per P2 append-only correction protocol, prior versions and related interpretations remain in session history; this draft does not overwrite them.

-----

## 0. What this is

This grammar is being developed as TRL 2–3 behavioral observability infrastructure for HumanAIOS work. A minimal formal grammar for behavioral claims: the obligatory categories a claim about behavior (a score, a verification, a completion statement, a registry entry) must mark before it counts as **well-formed** inside HumanAIOS work. Ill-formed claims are not “false” — they are *unparseable as truth-claims*: structurally incomplete in the same way a sentence in an evidential language is incomplete without its evidential suffix.

This sits one level above individual tool checks (`haios_guard.py`, `d_anthro_scanner`, B.0 blocks). Those tools detect specific violations; this document states the grammar they are all partial enforcements of.

**Design constraint carried from the project’s own findings:** per F-45 (stateless-substrate correction locus), a grammar that lives only in a substrate’s good intentions does not exist. Every rule below is stated with its enforcement surface — the protocol-layer place where violation is detectable. A rule with no enforcement surface is listed in §6/§9 (unenforced or specified-but-not-landed) rather than mixed in as if it were load-bearing.

-----

## 1. The core well-formedness rule

> **G-0:** A behavioral claim is well-formed if and only if it marks
> (a) its **evidential source**, and (b) its **agent of authority**.
> A claim missing either mark is ungrammatical regardless of whether its
> content is true.

Everything else in this spec is an elaboration of G-0.

Linguistic anchor (context, not authority): obligatory evidential marking is a real grammatical category (grammaticalized in Quechua, Turkish, Tibetan, among others — speakers *cannot* state a proposition without marking how they know it). English lacks the category, which is why AI self-report inherited English’s ability to assert without sourcing. This grammar adds the category back by rule where the language doesn’t supply it by morphology.

-----

## 2. Category I — Evidentials (obligatory on every claim)

Every behavioral claim carries exactly one primary evidential:

|Marker     |Meaning                                                                                                                            |Existing project form                                                                                                        |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
|`VERIFIED` |Obtained this session via a live fetch, executed command, diff, or direct read; checkable by a second party against the same source|Epistemic-labeling rule (this project); B.0 Empirical Verification Block; `grounding_source: external_verified`              |
|`INFERENCE`|Reasoned from available information; basis statable; could be wrong                                                                |Epistemic-labeling rule; `grounding_source: self_report` when the reasoner is the subject                                    |
|`JUDGMENT` |A recommendation or interpretive call; not a fact-claim at all                                                                     |Epistemic-labeling rule                                                                                                      |
|`REPORTED` |Relayed from another party’s claim without independent verification                                                                |New in this spec — currently unmarked in project practice, which is a live gap (e.g. relaying a collaborator’s stated result)|
|`UNKNOWN`  |Source cannot be established                                                                                                       |`grounding_source: unknown`; `submission_purity` quarantine classes                                                          |

**G-1 (no unmarked assertions):** a numeric score, a completion claim (“fixed,” “done,” “landed”), or a verification claim (“PASS,” “verified”) with no evidential is ungrammatical.
*Enforcement surface:* `haios_guard.py check_self_report_grounding` (scores + verification claims in .md/.txt); B.6 receipt reconciliation (completion claims at session close).

**G-2 (evidential honesty):** a claim must not carry a stronger evidential than its actual source supports. INFERENCE dressed as VERIFIED is the canonical violation — it is the registered pattern behind IC-041’s false completion claim, the playbook’s description of a tool that didn’t exist, and the `CODE_BACKED` claim in the unpatched scanner.
*Enforcement surface:* partial — verification-theater detection (`haios_guard.py`) catches the textual signature; full enforcement requires human review (Zone 2), and this spec does not pretend otherwise.

**G-3 (self-report is a distinct evidential, never elevated by repetition):** a subject’s claim about itself is INFERENCE-at-best with respect to that subject, per H-SELF-01 (self-administered LI inflates ~0.14–0.16) and F-22 (no interoceptive channel to check self-reports against ground truth). N restatements of a self-report do not sum to a VERIFIED. Cross-substrate agreement does not either, per F-53 (confidence-cascade across AI review passes without accuracy gain).
*Enforcement surface:* `submission_purity` enum + Z2-PURITY-01 quarantine at the corpus layer; administrator≠declarant separation in any two-stage capture design.

-----

## 3. Category II — Agency (obligatory on every act)

Every act (draft, ratification, execution, send, commit) carries exactly one agent-of-authority mark. Performing an act and holding authority for it are distinct grammatical roles and must not be conflated — the same distinction ergative languages grammaticalize between true agent and grammatical subject.

|Marker|Authority                                                   |Existing project form     |
|------|------------------------------------------------------------|--------------------------|
|`Z1`  |Proposes; holds no authority to make canonical or execute   |Zone 1 (Claude drafts)    |
|`Z2`  |Ratifies; converts a draft into canon                       |Zone 2 (Night)            |
|`Z3`  |Executes against the world (sends, commits, pushes, deletes)|Zone 3 (Night at terminal)|

**G-4 (no self-promotion):** an actor cannot mark its own output with a higher-authority tag. A Z1 draft that assigns itself a real IC number, or describes itself as ratified, is ungrammatical.
*Enforcement surface:* `IC-cand-` / `status: PENDING_ZONE2` conventions in REGISTERED.md; IC-030 live-fetch gate before registry-touching work.

**G-5 (agent visible at the claim, not the document):** authority is marked per-claim where claims of different zones coexist in one artifact.
*Enforcement surface:* none automated. Checklist-level only (PR-body template convention, §9 Step 3). Honest status: weakest rule in Category II.

-----

## 4. Category III — Aspect (the P1/P3 pair)

**G-6 (claims about change require a pair):** a claim about behavioral change, improvement, or calibration is well-formed only as a *delta between two marked observations* (P1 declaration → P3 confirmation, LI = P3/P1), never as a single observation with a trend asserted onto it. A lone P3 score is grammatical as a state-claim; it is ungrammatical as an improvement-claim.
*Enforcement surface:* corpus schema (`p1_*`/`p3_*` prefixed columns; `two_stage`/`two_stage_verified` requiring both `p1_committed_at` and `p3_committed_at` with ≥1-minute gap).

**G-7 (the pair must have independent evidentials):** per G-3, if both members of a P1/P3 pair are self-reported by the same subject, the *delta* inherits self-report status — it is not laundered into VERIFIED by being a ratio. This is H-SELF-01 stated grammatically.
*Enforcement surface:* `submission_purity` at the row level; the pending Phase-3 confirmation-queue design (`administrator_id ≠ declarant_id` constraint, specified in §9 Step 2, not yet landed).

-----

## 5. Category IV — Prohibited predicate class (P32)

**G-8:** the P32 verb class (*pretend, feel, want* (desiring sense), *believe* (conviction sense), *enjoy, hurt, care* (emotional sense), etc.) is barred from taking the substrate as first-person subject where a process-descriptive alternative exists. This is a subcategorization restriction in the narrow, technical sense: a closed class of predicates restricted from a specific subject position.
*Enforcement surface:* `d_anthro_scanner` v1.0.1 (patched; the v1.0.0 quote-stripper bug that hid 63% of input is documented in the pending consolidated Z2 packet). Detection is candidate-flagging only — classification of a hit as a real violation is SELF_REPORT_ONLY pending human review, per the tool’s own epistemic-status field.

**Status note:** P32 itself is an unratified Z1 draft. G-8 is therefore *proposed grammar*, conditional on P32’s ratification, and this spec does not promote it past that.

-----

## 6. Morphology — pattern classes as paradigms

The registry’s recurring pattern classes are this grammar’s irregular-verb table: one root failure surfacing in different inflected forms.

|Root (pattern class)                         |Attested inflections                                                                                                                       |
|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
|Claim-without-external-check (IC-037 family) |Audit workflow false-pass (IC-041); scanner quote-stripper undercount; regex scorer scope error (IC-037 original)                          |
|Phantom reference (IC-034/039/043/044 family)|Nonexistent registry IDs cited; migrations referenced but never landed; wrong GitHub org in a collaborator doc                             |
|Maintained headline (IC-038 + IC-cand family)|Charter countdown; corpus stats in CURRENT.md §1/§4/§5                                                                                     |
|Receipt overstatement (IC-031 family)        |Commit messages claiming absent files; unverified “processed/validated” header claims (this document’s own prior draft, corrected S-070926)|

**G-9 (paradigm rule):** a new incident matching an existing root is filed against that root’s pattern class, not as a novel finding — *and* a new incident is not forced into an existing class for tidiness.
*Enforcement surface:* findings-scan skill routing; IC roll-up table discipline. Human-judgment-dependent; no automation claimed.

-----

## 7. What this grammar does NOT claim

- It does not claim to be a “language for behavior” in a universal sense. Scope is: claims made inside HumanAIOS work, by any party, about behavior or about the work itself. TRL framing: this is a TRL-2 conceptual formalization of existing TRL-3/4 practices, not a new capability.
- It does not claim the linguistic analogies are load-bearing. Evidentiality, ergativity, aspect, and subcategorization are *anchors for precision*, not arguments from authority. If a rule is wrong, no appeal to Quechua saves it.
- It does not claim complete enforcement. §3 G-5 and §6 G-9 are checklist/judgment-enforced only, and G-2’s full enforcement is human-in-the-loop by construction. Rules are stated with their real enforcement surface or explicitly marked unenforced — a grammar that overstated its own coverage would violate G-2 in its founding document.
- It does not retroactively grade past artifacts. Adoption is forward-looking from ratification date.
- It does not claim any self-administered diagnostic pass on itself constitutes ratification-grade evidence. Such a pass would be self-administered and anchor-only; treating it as more would itself violate G-2/G-3.

-----

## 9. Implementation closure — harm and handoff

This grammar does not exist as protocol layer enforcement until each rule names the specific function signature, constraint, or schema field that closes it. A rule with no build-order entry here is not implemented; it is aspirational, per F-45. The following are the minimal wiring points, in build order:

**Step 1:** `haios_guard.py` — extend `check_self_report_grounding(text: str, doc_type: str) -> list[Violation]` to flag completion verbs, PASS/verified strings, and numeric scores missing a recognized evidential tag (`VERIFIED|INFERENCE|JUDGMENT|REPORTED|UNKNOWN`) on the same line or in an adjacent bracket tag. Add a new `REPORTED` detection branch alongside the existing self-report detection, since `REPORTED` is new in this spec and has no prior detector. This closes G-1 as a structural check rather than a policy statement — the harm this prevents is a false completion or false verification claim reaching Zone 2 or a public surface unflagged, which is a provenance failure, not a phrasing failure.

**Step 2:** `submission_purity` schema — add a database CHECK constraint enforcing `administrator_id != declarant_id` wherever `submission_purity` is `two_stage` or `two_stage_verified`. Designed but not yet landed. Function signature: a Postgres CHECK or trigger, not application-layer validation, so the constraint holds even if a future client bypasses the API. This closes G-3/G-7 structurally — self-report cannot be laundered into a two-stage row by the same actor filling both roles.

**Step 3:** PR template — add a per-claim agency checklist field (Z1 / Z2 / Z3) to the PR body template, required before merge. This is the only wiring available for G-5, which has no automated enforcement surface; the checklist makes zone-mixing visible at review time rather than left implicit across a mixed-authority document.

**Step 4:** B.0 Empirical Verification Block — require an evidential tag on every line item in the session-close B.0 block. This is the closure point for G-1 at the session-boundary rather than the per-commit boundary; B.6 receipt reconciliation already audits completion claims retroactively, this makes the tag mandatory going forward rather than caught after the fact.

Each step above is a Z2/Z3 action, not something Z1 can land unilaterally — this section specifies the build, it does not execute it. The provenance chain end to end is: claim, then evidential tag (Step 1/4), then agent tag (Step 3), then corpus-layer purity enforcement (Step 2). A claim missing any link in that chain is exactly the ungrammatical case G-0 describes, and each link now has a named structural home rather than being enforced by good intentions alone.

-----

## 10. Ratification gate (for Z2)

- [ ] Confirm the five-evidential set (§2)
- [ ] Rule on whether G-8 waits for P32 ratification
- [ ] Decide the enforcement roadmap for G-5, G-9
- [ ] P30 interactive ACAT pass on this document
- [ ] Assign registry disposition