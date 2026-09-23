# ROI_RUBRICS_S-092126 — two decisions Night asked to be priced before ruling

**Session:** S-092126 · **Author:** Z1 (Claude) · **Status:** analysis, not a ruling
**Requested:** 2026-09-21 — *"lose the key, lose the thread — ROI here"* and
*"an external administrator, or a self-administered protocol with a pre-registered
falsifier — ROI rubric"*

**Temporal position (Q-TEMPORAL-DISSOLUTION-01):** nothing here carries a
deadline or a cadence. Neither decision becomes urgent by elapsing; both become
decidable when the evidence each names arrives.

---

## Rubric A — pseudonymous check-in with no recovery path

The proposal was a login that collects no personal data, so that a
user–machine transmission becomes measurable without an identity to protect.
The cost is that a lost key is an unrecoverable thread.

### The framing error to clear first

"Lose the key, lose the thread" is stated as a cost to the participant. For most
of this system it is not. The thread is the *project's* longitudinal measurement
of how a human's participation moved a machine's behaviour. The participant, in
the EPHEMERAL case, wanted nothing back.

So the question is not "how much does the user suffer" but **"what measurement
does HumanAIOS lose, and can it be reconstructed without an identity?"** Priced
that way the answer differs sharply by continuity mode, which
`PARTICIPATION_CONTRACT_V0_1` already distinguishes and which this rubric simply
prices.

### Scored by continuity mode

| | EPHEMERAL | QUALIFICATION_PROOF | STANDING_SIGIL |
|---|---|---|---|
| What the key holds | one session | a proof that a bar was cleared | a standing participation series |
| Participant's loss on key loss | none | redo the qualification | the accumulated standing |
| **Project's loss on key loss** | **none** | one re-run's cost | **the whole longitudinal series — the only data that can show influence over time** |
| Reconstructable without identity? | n/a | yes, by re-qualifying | **no** |
| PII avoided by having no recovery | none worth counting | small | large — recovery is where identity normally enters |
| Net | **take the trade** | **take the trade** | **do not take it blind** |

### The finding

Two of three modes are free. The trade is only expensive in STANDING_SIGIL, and
that is precisely the mode the influence measurement needs — a single session
cannot show a human moving a machine's behaviour; a series can. So the honest
position is not "pseudonymous, no recovery" as a blanket rule but:

> No recovery for EPHEMERAL and QUALIFICATION_PROOF. STANDING_SIGIL needs a
> recovery mechanism that is not an identity, or it needs to accept that the
> series it exists to accumulate is one lost key away from zero.

### The candidate mechanism, and its defect

Behavioural re-identification: a returning participant re-proves they are the
same participant by reproducing their own behavioural signature (the H-ACAT
instrument already produces one), rather than by presenting a credential or an
email address. No PII stored, thread recoverable.

**This must not be adopted without naming what it is.** A behavioural signature
stable enough to recover an account is a biometric. It re-identifies a person
across sessions, which is the defining property of personal data, and calling it
"no personal data collected" because no name was typed would be the exact
claim–reality gap this project exists to measure. Under GDPR Art. 4(14) a
behavioural template used for unique identification is likely special-category
data — a *stricter* regime than the email address it was meant to avoid.

| Option | PII held | Thread recoverable | Honest to describe as "no personal data" |
|---|---|---|---|
| No recovery | none | no | yes |
| Email recovery | an identifier | yes | no |
| Behavioural re-identification | **a biometric template** | yes | **no — and worse than email** |

The cheap-looking option is the expensive one. If STANDING_SIGIL needs recovery,
the defensible form is a participant-held secret they can back up themselves — a
recovery phrase the project never sees — which keeps recovery available and keeps
the project holding nothing. The project's loss becomes a support burden rather
than a data liability.

### ROI verdict

**Take the no-recovery trade for EPHEMERAL and QUALIFICATION_PROOF now.** Hold
STANDING_SIGIL pending a decision between participant-held recovery phrase and
accepted loss. Do not adopt behavioural re-identification without a privacy
assessment that calls it what it is.

### Falsifier

FALSE if `PARTICIPATION_CONTRACT_V0_1.schema.json` does not distinguish the three
continuity modes, or if STANDING_SIGIL does not in fact accumulate anything
across sessions — in which case all three modes are free and the whole trade is
costless. Mechanically checkable against the schema.

---

## Rubric B — external administrator vs self-administered HA-000

HA-000 is an assessment run. The question is whether it must be administered by
someone outside the project, or whether a self-administered run with a
pre-registered falsifier is sufficient.

### The framing error to clear first

Pre-registration and external administration are widely discussed together and
they defend against **different** failures. Treating one as a substitute for the
other is the mistake this rubric exists to prevent.

| Failure mode | Pre-registration fixes it? | External administration fixes it? |
|---|---|---|
| Choosing the analysis after seeing the data | **yes** | partly |
| Choosing which run to report | **yes** | yes |
| Moving the threshold after the result | **yes** | yes |
| Administrator cues the subject, knowingly or not | no | **yes** |
| Instrument's designer scores their own collaborator | **no** | **yes** |
| Subject knows what the instrument rewards | no | partly |
| Reviewer has no reason to believe the record | no | **yes** |

The bottom three rows are the ones that matter here, and pre-registration does
not touch them. Z1 built the ACAT instrument. Z2 is Z1's collaborator. A
self-administered HA-000 is the instrument's author scoring their own partner,
and no falsifier registered in advance changes who administered it.

### Scored

Weight reflects what the run is *for*. HA-000's output is cited as validation
evidence, so reviewer credibility is weighted heaviest.

| Dimension | Weight | Self-administered + prereg | External administrator |
|---|---|---|---|
| Cost to run | 2 | **5** — zero marginal | 2 — fee, scheduling, instrument exposure |
| Available now | 2 | **5** | 2 — nobody is engaged |
| Guards analysis-selection | 3 | **5** | 4 |
| Guards administration effects | 4 | 1 | **5** |
| Guards designer-scores-collaborator | 4 | **1** | **5** |
| Credible to a skeptical reviewer | 5 | 1 | **5** |
| Supports a TRL 4 claim | 5 | **1** | **5** |
| **Weighted total** | | **62** | **108** |

### Why the last two rows decide it

`Q-SEED-TRL-PROPAGATION-01` is open on exactly this point. TRL 4 conventionally
requires validation in a relevant environment. `audits/CORPUS_LIVE_VERIFICATION_S-092126.md`
measured the live corpus at 116 rows, of which the strictest clean stratum is 4,
and `acknowledged_elicitation = true` appears in **zero** rows in every stratum.
The evidence base for the ratified TRL value is thinner than it was understood to
be when that value was ratified.

A self-administered HA-000 adds rows to that base that a reviewer will discount
to zero for the same reason the corpus rows are discounted: the subject and the
administrator are inside the same project. It does not move the TRL claim. It
costs nothing and returns nothing that can be cited.

### The trap in the cheap option

Self-administration is not merely weaker — it is *negatively* valued if the
result is later cited. A published HA-000 figure that a reviewer discovers was
self-administered damages the instrument's credibility more than having no figure
at all, and this project's entire thesis is measuring the gap between what a
system claims about itself and what it does. Producing exactly that gap in our
own validation run is the single most expensive available mistake.

### ROI verdict

**External administration, and if it cannot be afforded, no HA-000 run rather
than a self-administered one.** The pre-registered falsifier is not the
alternative to external administration; it is a requirement on top of it, and
should be registered before an external administrator is engaged so the engagement
cannot shape it.

Cheapest credible path, in order:
1. Pre-register the falsifier and scoring rubric now, in `z1-inbox/`, before any
   administrator is approached. Free, and it is the part that expires if done later.
2. Engage one external administrator for one run. Not a panel — a single
   disinterested administrator clears the two rows that decide this table.
3. Run self-administration in parallel **only** as a labelled comparison: the gap
   between the two is itself a measurement of administration effects, and it is
   publishable in a way the self-administered figure alone is not.

Step 3 is the one that converts the cheap option from a liability into evidence,
and it only works if the external run exists to compare against.

### Falsifier

FALSE if an external administrator's HA-000 result does not differ from the
self-administered one beyond measurement noise, across enough runs to tell —
which would show administration effects are negligible for this instrument and
collapse the two heaviest rows. Directly testable by step 3, and it is the
outcome that would make the cheap option correct.

Also FALSE if HA-000's output is never cited outside the project, in which case
reviewer credibility carries no weight and the cost row decides.

---

## What neither rubric settles

Both verdicts are Z1 analysis. Rubric A's STANDING_SIGIL question and Rubric B's
engagement decision are Z2 calls with budget and external consequences, and this
document deliberately stops at pricing them.
