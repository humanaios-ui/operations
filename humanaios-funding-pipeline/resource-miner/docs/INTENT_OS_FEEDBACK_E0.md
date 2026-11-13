# INTENT-OS feedback processor — first-user E0

**Scope:** Candidate search quality, human feedback and actionable verification. **No new external actor, automatic SEO publication, eligibility decisions, source writes, or changes to the Resource Miner search/rank function.** The feedback surface is purely browser-local unless the user explicitly exports it.

## First observed three-result session

A human user evaluated the local INTENT-OS search and supplied three positive **relevance** judgments. All three are retained, but cannot be collapsed into the same completed / eligible / new-opportunity state.

| Displayed search hit | Human-supplied feedback | Related reference | Correct review action | What is NOT proved |
|---|---|---|---|---|
| GitHub Sponsors | Useful; their sponsor setup is incomplete | Public GitHub sponsor page only; do NOT include the owner's authenticated dashboard URL | `SETUP_INCOMPLETE → COMPLETE_EXISTING_SETUP` | Profile approved, funding received, SEO visibility |
| Apart Lab Fellowship | Interested in the specific **AI Collusion Research Sprint** dated Oct 23–25, 2026 | https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25 | `INTERESTED → VERIFY_DETAILS_AND_DEADLINE` | Fellowship acceptance, sprint registration, submission, current registration state |
| Microsoft for Startups | Already being used for the project's Azure resources (reported by user) | https://www.microsoft.com/en-us/startups | `ALREADY_IN_USE → RECONCILE_EXISTING_RESOURCE` | Actual credit balance, service entitlements, sponsor tier, subscription ownership |

The first-user sample is 3/3 **human-reported relevant hits** in a narrow, self-selected, three-result test. It is **not** an independent precision or recall estimate, not a verification of the three source records, and not proof of resource acquisition. Microsoft already in use should be offered under "controlled resources / existing subscriptions", **not** as a new lead. GitHub Sponsors remains a legitimate human-confirmed lead needing completion. Apart is a separate **sprint linked from a fellowship result**; the link is a human discovery, not a claim that the original resource was a sprint.

**Time-critical Apart warning:** Check current registration status directly before an application. The official page states Oct 23–25 and a submission deadline Oct 25 11:59 PM Anywhere on Earth, but also renders "submission window has closed" before the published event date. Mark registration `UNVERIFIED_CONFLICTING_SOURCE_STATE`, avoid treating website text or the user's interest as successful registration.

## User interaction / feedback boundary

1. The existing search still calls the existing `POST /api/intent`; results, source status, provenance and eligibility warnings remain unchanged.
2. Every result now includes "How did this match land?" with `SETUP_INCOMPLETE`, `INTERESTED`, `ALREADY_IN_USE`, `NOT_RELEVANT`, or `VERIFY_LATER`. An optional related **public** HTTPS reference permits recording a better event or source found by the human.
3. Save explicitly to this browser's `localStorage` under `humanaios.intent_os_feedback.v0.1`; maximum 50 candidate/source pairs. Only title, candidate ID, original source link, optional related public link and feedback state are saved. The original question, emails, authorization credentials, free-text comments and user identity are **not** saved.
4. "Export feedback JSON" downloads a self-contained data file *only upon the user's click*. No server endpoint, tracking pixel, email, DB write or GitHub API action is introduced. Browser localStorage is unencrypted; anyone with this browser profile can read it. Clear feedback deletes this browser's local copy but not past exports. Do not input confidential reference links.
5. A separate offline operator runs `python3 -m resource_miner.intent_feedback --input /path/to/intent-os-feedback.json` to get a bounded deterministic report that marks all feedback `UNVERIFIED_FIRST_PARTY_HUMAN_REPORT`. The SHA-256 digest is unsigned, not independent verification.
6. Reports can later be considered by the existing Evidence Graph / Resource Miner reconciliation process **only after** human review, verified source standing, and a separate authorized PR. This implementation does not update rankings, source files or controlled resource status.

### Reproduce

```sh
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_intent_feedback.py' -v
python3 -m unittest discover -s tests -p 'test_intent_os_bridge.py' -v
python3 -m resource_miner.intent_feedback --input fixtures/intent_os_first_user_feedback_e0.json
python3 app.py --host 127.0.0.1 --port 8766
```

Open `http://127.0.0.1:8766/intent-os`; run a new search, classify candidates and export. This new UI is not in the already-running local server until it uses an updated reviewed commit in the separate `operations-intent-os` worktree. Do **not** `git pull` over the user's original worktree with uncommitted changes.

## SEO: bounded, legitimate follow-up, not automatic promotion

**Good mission alignment:** make it easy for potential supporters to discover clear, truthful public information about HumanAIOS and the official **public** GitHub Sponsors link. A future **separate** human-reviewed SEO proposal can maintain a canonical "Support HumanAIOS" page on humanaios.ai with descriptive title, accurate organization metadata and appropriate structured data, an explicit GitHub Sponsors call-to-action, indexed sitemap/canonical tags, sensible internal navigation, and link-health/currentness checks. Use factual, current statements that distinguish "profile draft/incomplete" from "sponsorship active." Never reproduce authenticated dashboard views, user account URLs, payment information, private GitHub data, or speculative financial benefits.

**Allowed automation:** scheduled link checks, public-page availability, schema linting, broken-link reports, and **draft-only** content proposals for human review. **Not allowed without further authority:** GitHub Sponsors payout setup, sponsor page publishing, posting unsolicited promotional backlinks/comments, creating external accounts, subscriptions, charging funds, editing public production pages, automatically signing up to Apart events. SEO presence can improve discoverability but cannot guarantee traffic, rankings or income.

**Next instrument question:** can a human-feedback classification reduce time spent seeing already-controlled resources as if they were new? Compare a baseline vs feedback-aware display in a future consented controlled test. No ranking change until that result is measured.
