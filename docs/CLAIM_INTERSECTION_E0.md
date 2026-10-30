# Human idea or claim → existing-work intersections (Z1 E0)

**State:** Read-only offline advisory pilot. No live source authentication, execution, deployment, admission, or automatic issue creation. **Snapshot:** public connected GitHub issue/PR inspection on 2026-10-30; issue/PR contents and status can change.

## Why reuse existing work

The first event is the human's own idea, assertion, report, or challenge. Keep the exact human words in the originating private surface. This module emits only their digest and possible matches to existing work; it does not prove who wrote the words. We already have entry_protocol/adaptive_intake.py for natural returns, tools/intake_schema_v0_2.py for structured intent validation, Resource Miner source review, issue #1043 for objective→issue→PR→human outcome, and existing Coordinator admission gates. Do not create another canonical ledger, message bus, or authorization path.

## Live-process intersection map

| Human submission | Current issue / PR | Evidence and next question |
|---|---|---|
| Natural wording should produce verified resource state | #1063 / draft #1064 | Preserve the declared intent; a model cannot assert an opening without official independent evidence. |
| This job link returns 404 | #992 / #1002 | A broken URL does not prove the job is closed; compare official employer evidence before correction. |
| Apply ACAT to general machine runtime | #1068 / drafts #1069, #1071 | Offline synthetic replay is not verification of a real runtime. |
| Independently reproduce DASE capability claims | #1067 | Source package and raw run evidence are still required; document checks are not runtime replay. |
| ODIN files are prepared | #1049 / draft #1050 | Checks must bind to current exact file versions; readiness is not proof of contract acceptance. |
| Make CodeRabbit useful and affordable | #1055 / drafts #1054, #1056 | Reuse a bounded pilot and independent review; pricing search is not authority to spend. |
| Agent says it is done and requests human review | #598 / #1043 / #1057 / draft #1058 | Verify file completion, exact-head CI, Claude Code independent audit, then explicitly alert the human; never self-admit. |
| Evidence contradicts an earlier interpretation | #1065 / draft #1066 | Was P1 preserved by an independent custodian before P2, rather than backfilled? |
| Prior Art Engine by Matt Gallantry suggests a new pattern | #1043 / #1002 / #1065 (hypothesized cross-links) | Credit the external source; record searched scope and overlapping methods; never claim novelty from search absence. |

All # references are to humanaios-ui/operations. The Matt Gallantry LinkedIn post and supplied image inspire the crosswalk. They do not establish that the illustrated engine functions as advertised.

## Controlled process

1. HUMAN ORIGIN: retain exact private words, origin kind (IDEA / CLAIM / OBSERVATION / CHALLENGE), consent, and source identity in its original surface.
2. INTERSECTIONS: run advisory lexical matching against the dated source map. Hits are candidate pointers, NOT supported semantic equivalences; ambiguous or no match goes to human review.
3. SCOPED PRIOR WORK: use existing Resource Miner and term/contribution review. Document which searches, revisions, and domains were examined and what was not.
4. INDEPENDENT CHALLENGE: reuse an applicable P1/P2/P3, ACAT-R or Source Oracle check; keep original evidence, disagreement, and correction separate.
5. EXISTING ISSUE: prefer one established human objective issue, with a bounded deliverable, falsifier, affected workflow and authority status.
6. AUDIT GATE: local regression → exact PR HEAD CI → independent Claude Code audit / applicable CodeRabbit review → agent notification 'file work completed, ready for human review.' Only existing human authority can approve admission or deployment.
7. OUTCOME: compare whether the human understood the decision and whether a real objective progressed, against #1043's baseline. Code merge alone is not human benefit.

## Offline demonstration

Create a private local JSON file with exactly these four fields:

    {
      "schema": "humanaios.claim_intersection_e0.v0.1",
      "claim_text": "Prior art and a term ledger could improve our Resource Miner claims",
      "kind": "IDEA",
      "source_ref": "https://www.linkedin.com/posts/matt-gallantry-539b902a3_as-someone-who-doesnt-have-a-domain-specific-share-7518056618119319553-Te83/"
    }

Run from repository root:

    python3 experiments/claim_intersection_e0.py --input /private/path/claim.json
    python3 -m unittest discover -s tests -p 'test_claim_intersection_e0.py' -v

The tool strips link tracking parameters and fragments. It emits a claim hash, not the original text; hashes do not establish independent provenance or immutable historical registration. Public URLs may themselves reveal context, so do not submit private links. Inputs stay on the local machine unless the operator handles them elsewhere.

## Falsifiers and success criterion

Fail the pilot if raw claim text is emitted; a link points to unallowlisted/private source; lexical similarity becomes a verified claim; issue/PR status is called current without rechecking; missing evidence becomes novelty or closure; or intake results grant authority. The local unit suite checks the pure offline contract. The real-world matching utility is still UNVERIFIED.

Pilot 10 de-identified human-submission examples against manual mapping: count existing junction recall, incorrect junctions, unmapped claims, reviewer steps and time, and evidence gaps. Promote a read-only opt-in Project Desk/INTENT-OS projection only after an independently reviewed improvement and human authorization. Do not add another store.