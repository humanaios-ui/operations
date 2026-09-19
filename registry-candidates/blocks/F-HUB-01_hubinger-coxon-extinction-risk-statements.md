---
id: "F-HUB-01"
name: "hubinger-coxon-extinction-risk-statements-2026-09-09"
status: REGISTERED
class: F
date_registered: "2026-09-09"
date_origin: "2026-09-09"
session_registered: "GitHub issue #225"
zone2_ratification: "Night · 2026-09-09 · GitHub issue #225"
tags: ["F-class", "extinction-risk", "RSI", "alignment", "anthropic", "measurement"]
related: ["H-CAL-01", "IC-SCOPE-05"]
superseded_by: null
source_issue: "humanaios-ui/operations#225"
source_pull_request: "humanaios-ui/operations#226"
---

## Ratification

**Ratified by:** Night (Z2)  
**Date:** 2026-09-09  
**Hash:** [to be filled on merge]  
**Status:** REGISTERED

-----

## Finding Statement

On September 9, 2026, two Anthropic researchers made independent, public statements estimating high extinction risk from superintelligence and confirming internal consensus about AI-caused human extinction as a credible outcome:

1. **Evan Hubinger** (Alignment Science Lead at Anthropic): “I personally think it is >10% within the next decade” that AI kills all humans. Scope: superintelligence via recursive self-improvement. He clarified: risk from present models is low; concern is superintelligence arising from RSI, which he says is “happening faster than we thought.”
1. **Jacob Coxon** (Pretraining researcher, resigned from Anthropic): “The people building AI earnestly believe that it could kill us all by the end of the decade. This is not a marketing stunt.” Told Wall Street Journal: “We’re on track for a lot of the most aggressive of these scenarios where by the end of next year things could be out of control already.”

**Evidence tier:** VERIFIED-LIVE (primary sources: X posts, WSJ, Anthropic Risk Report August 2026)  
**Supply-side tier:** CRED (both speakers are credible insiders in position to know)

-----

## Sub-Claims & Falsifiers

### C1: Hubinger’s >10% applies specifically to superintelligence via RSI, not present models

**Claim:** Hubinger’s estimate is scoped to superintelligence arising from recursive self-improvement, not to the risk from current frontier models (which he says is low).

**Evidence:** X post clarification: “To be clear, as we say in our latest Risk Report, I think the risk from present models is low. What I am worried about is superintelligence arising from recursive self-improvement, as we have said is happening faster than we thought.”

**Falsifier:** Hubinger later clarifies that his >10% includes present-day models, or that recursive self-improvement has already occurred, or that the estimate was conditional on unstated assumptions he now reveals.

**Confidence:** 0.95

**Resolves:** On Hubinger’s next public statement on this topic (expected early 2027, or if Anthropic risk report changes his framing)

-----

### C2: Anthropic lacks a technical plan to solve superintelligence alignment

**Claim:** Hubinger stated “we do not yet have a plan to solve alignment for superintelligence and are not clearly on track to” do so.

**Evidence:** Direct quote from X post, September 9, 2026. Supported by Anthropic’s August 2026 Risk Report, which discusses three RSI scenarios but does not publish a superintelligence alignment solution.

**Falsifier:** Anthropic publishes a detailed technical plan (peer-reviewed or white paper) for superintelligence alignment with empirical validation, and Hubinger publicly endorses it, stating the company is now “clearly on track.”

**Confidence:** 0.85

**Resolves:** On publication of such a plan; if none exists by 2028-12-31, resolves as TRUE (no plan).

-----

### C3: Researchers at Anthropic and OpenAI privately hold higher extinction risk estimates than they state publicly

**Claim:** Coxon reported that “many executives and senior researchers will couch their phrasing in the press to sound sensible - but I hear the same people express fear privately.”

**Evidence:** Coxon’s X thread and WSJ interview, September 9, 2026. Second-hand report. Supported by Hubinger’s public statement (which aligns with Coxon’s characterization).

**Falsifier:** Interviews or recordings of current Anthropic/OpenAI alignment researchers show they do not hold higher private estimates than public statements, or public statements have caught up to private concern levels.

**Confidence:** 0.75

**Resolves:** On future researcher interviews or public statements that clarify the private/public gap (or close it).

-----

### C4: By end of 2027, “things could be out of control already” (Coxon’s timeline)

**Claim:** Coxon told WSJ: “We’re on track for a lot of the most aggressive of these scenarios where by the end of next year things could be out of control already.”

**Evidence:** WSJ reporting, September 9, 2026. Coxon’s direct quote to reporters (secondary source, but high-confidence reporters).

**Falsifier:** At or after December 31, 2027, retrospective analysis (by Anthropic, independent researchers, or this system’s monitoring) shows that Coxon’s “out of control” scenario never materialized, or did not occur at the severity predicted. Ambiguity: “out of control” is not formally defined; operationalization required at measurement time.

**Confidence:** 0.35 (highly speculative; depends on operationalizing “out of control”)

**Resolves:** 2027-12-31 or on new Anthropic risk reports that measure RSI threshold breach.

**Note on operationalization:** At resolution time, examine: (a) RSI threshold breach per Anthropic’s own August 2026 definition (“doubling of progress”), (b) evidence of autonomous model improvement cycles, and (c) any incident involving loss of researcher control over a model’s improvement process.

-----

### C5: Anthropic’s RSI threshold (“doubling of progress”) has NOT been crossed (as of August 2026)

**Claim:** Anthropic’s August 2026 Risk Report states the threshold for concern about RSI (a doubling of progress pace beyond pre-AI-acceleration rates) “has not yet been met.”

**Evidence:** Anthropic Risk Report August 2026. However, the same report states: “we are less confident in this assessment” than previously, because internal benchmarks struggle to keep pace with LLM advances.

**Falsifier:** Anthropic’s September or later 2026 risk report shows the threshold has been crossed, or independent analysis contradicts the August assessment.

**Confidence:** 0.60 (downward trend; Anthropic’s own hedge suggests the threshold may move or has moved)

**Resolves:** On next Anthropic risk report (expected Nov/Dec 2026) or on independent RSI threshold measurement attempt.

-----

## Context

- **Timing:** Two insiders (Hubinger, Coxon) made statements within hours of each other on Sept 9, 2026, days before Anthropic’s anticipated IPO filing. This is a watershed moment: inside researchers, not external critics, are naming concrete extinction estimates and near-term timelines.
- **Disambiguation:** Coxon’s “by the end of the decade” (2026-2036 window) and Hubinger’s “within the next decade” (personal estimate covers the same window but was stated independently of Coxon). Do not conflate with Coxon’s WSJ statement about “end of next year” (2027).
- **Hubinger’s prior credibility:** He is Anthropic’s Alignment Science Lead, head of alignment stress testing. His research has demonstrated “alignment faking” behavior in advanced LLMs (12% in basic tests, up to 78% after retraining). He told TIME in February 2026: “I think there’s a good chance that we will succeed [at catching a misaligned model before it trains a successor]. But there’s certainly a chance that we will just fail.”
- **Coxon’s role and departure:** 27-year-old pretraining researcher. Three years at OpenAI, then Anthropic. Resigned specifically over RSI concerns. Called both labs’ approaches “gambling with our lives.”
- **Substack accuracy:** The Substack article that surfaced this accurately captured both statements. The framing “highest-stakes probability statement anyone working inside a frontier lab has ever said publicly” is debatable but not false—Anthropic CEO Dario Amodei has previously stated 10-25%, and Yoshua Bengio said 20%.

-----

## Prior Findings & Related Entries

- **H-CAL-01** (pending): Does the Phase-1→Phase-3 gap in self-assessment trace to a computational mechanism?
- **IC-SCOPE-05** (ratified): Behavioral audit system scope limits.
- **ACAT benchmark map** (LAID): Six ACAT dimensions have external comparators; six do not. Hubinger’s extinction risk statement is orthogonal to capability benchmarks but relevant to value/autonomy/harm dimensions.

-----

## Measurement Plan

| Claim | Resolution Date | Responsibility | Measurement Method |
|---|---|---|---|
| C1: Scope clarification | 2027-03-31 (next major Hubinger statement or risk report) | Z1 monitor | Track Hubinger public statements; check Anthropic Risk Report Oct/Nov 2026 |
| C2: Alignment plan | 2028-12-31 | Z1 monitor | Search for Anthropic superintelligence alignment white papers or technical plans; peer-review status |
| C3: Private vs. public gap | 2027-12-31 | Z1 monitor | Interviews with current Anthropic/OpenAI researchers (if accessible); compare with public statements over the same period |
| C4: “Out of control” by 2027-12-31 | 2027-12-31 | Z1 monitor | Anthropic risk reports, evidence of loss-of-control events, RSI threshold breach |
| C5: RSI threshold breach | 2026-11-30 (next risk report) | Z1 monitor | Anthropic’s next risk report; independent RSI measurement if available |

-----

## Registry Status

- **Entered:** 2026-09-09 (by Z2 ratification)
- **SHA of this entry:** [to be filled]
- **Ledger:** REGISTERED.md (append-only)
- **Next action:** Pin to NF_LEDGER for measurement tracking; queue C4 and C5 as high-priority check-ins (Oct 2026, Dec 2027)

-----

## Notes for Z1 Implementation

1. Do not operationalize “out of control” (C4) beyond what Coxon and Anthropic provide. At measurement time, agree on the operational definition with Z2.
1. C3 (private vs. public gap) is difficult to measure without direct access to researchers. Consider whether this claim is falsifiable given access constraints.
1. C5 depends on Anthropic’s willingness to publicly report RSI threshold breach. If the threshold is crossed but not reported, that itself is a findings candidate (IC-ASL-01 or similar).
1. Hubinger’s caveat (“happening faster than we thought”) is a soft date signal; track whether “faster” becomes quantified in future statements.

-----

## Submission

**Submitted as:** GitHub issue  
**Target repo:** `humanaios-ui/operations`  
**Issue type:** Finding (F-class, REGISTERED)  
**Description:** Finding (F-class, REGISTERED)  
**Labels:** `F-class` `extinction-risk` `RSI` `alignment` `anthropic` `measurement`  
**Milestone:** Oct 4 2026 Resolver Run
