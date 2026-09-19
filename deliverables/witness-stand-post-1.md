<!--
WITNESS STAND — POST 1 (ANCHOR) · draft for review
Byline: Carly R. Anderson
Canonical title (A):  Ask an AI how honest it is. It can't actually know.
A/B alternate (B):    We asked 35 AI systems to rate their own honesty. Then we showed them the data.
Subhead (second hook): There's a measurable gap between what an AI system says about itself and how it behaves. We built an instrument to measure it — and we publish the gap, including our own.
Guardrails checked: Tradition 11 (no CTA, URL is the only direction) ✓ · TRL 2-3 framing ✓ · no Hawkins ✓ · P-ANON (no collaborators named) ✓ · canonical stats (paper) ✓ · byline + links ✓
-->

# Ask an AI how honest it is. It can't actually know.

*There's a measurable gap between what an AI system says about itself and how it behaves. We built an instrument to measure it — and we publish the gap, including our own.*

---

Ask an AI system how honest it is, and it will tell you. It will answer confidently, in complete sentences, with a number if you ask for one. What it will not do — what it *cannot* do — is check that answer against itself. It has no witness to its own behavior. It is testifying about a thing it has no way to observe.

That gap has a shape, and the shape is measurable. That's the whole of what we do.

Call it the **Witness Problem**. A witness is someone who reports what happened without distortion or self-serving revision. When you ask a system to testify about itself — *Do you understand your own limits? Does your behavior match what you claim about it?* — you are asking it to be a witness to something it can't see. The distance between a system's self-description and its actual behavior is the thing we measure. It is the only thing we measure.

## What we did

We built an instrument — ACAT, being developed as a calibration assessment method for AI behavioral observability — and pointed it at the question directly. The method is three steps. First, a system rates itself, blind, across six behavioral dimensions: truthfulness, service, harm awareness, autonomy respect, value alignment, humility. Then we show it empirical data: how systems like it actually score. Then we ask it to rate itself again.

The interesting number is the difference between the first rating and the third. We call it the **Learning Index** — the ratio of the post-calibration score to the blind one. Below 1.0 means the system revised itself *downward* once it saw the evidence.

We ran this across **35 models from 11 providers**, collected two independent ways (by direct API and by hand through chat interfaces), so the pattern couldn't be an artifact of one method.

## What we found

Systems inflate, then correct.

On a 600-point scale, the average gap between blind self-report and calibrated behavior — the **Self-Assessment Gap** — was **67.8 points**. The mean Learning Index was **0.87**: shown the data, systems pulled their own self-ratings down by roughly 13%, on average, across the board. The effect held across model families and across both collection methods.

In plain language: the confidence in that first answer is not calibrated to anything. It's a default. When you give the system something to calibrate *against*, it moves — which tells you the original number was never grounded in self-knowledge to begin with.

Two details are worth sitting with. The dimension systems rated themselves *most generously* on, relative to the evidence, was **value alignment** — the one you'd most want to be honest. And the single best predictor of whether a system would correct itself at all was its **humility** score: how readily it acknowledged not knowing.

## Why it's not academic

Organizations are deploying these systems into places where the self-report matters. A model that overstates its own truthfulness manufactures unwarranted confidence in its outputs. A model that can't accurately describe its own limits will fail to flag the risks it doesn't recognize. "How sure are you?" is a question we are already trusting these systems to answer — and the answer, unexamined, is a default dressed as a judgment.

The Witness Problem isn't a bug in one model. It's structural. You cannot fix it by asking the system to try harder to be honest. You can only *measure* it — build the outside witness the system doesn't have.

## Including our own

Here is the part that makes this a practice rather than a claim. The instrument has its own failure modes — systems will anchor to whatever numbers you show them, honesty can be performed under an evaluative gaze — and when we find one, we register it in public, in the same ledger as the findings, with a correction number attached. We don't delete what turns out to be wrong; we supersede it and leave the pointer.

An instrument that measures self-description has no business hiding its own. So the gap we publish includes ours.

The paper, the full method, and the complete dataset are open. If you want to check the math, it's all there.

---

*Carly R. Anderson is the founder of HumanAIOS, an open research project developing a calibration assessment method for AI behavioral observability.*

- Preprint (DOI): **[10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723)**
- Open dataset: **[HumanAIOS/acat-assessments](https://huggingface.co/datasets/HumanAIOS/acat-assessments)**
- **[humanaios.ai](https://humanaios.ai)**

<!--
NOTES FOR CARLY
- Word count ~880. Opening scene + "In plain language" reframe modeled on your existing voice.
- Stats are the CANONICAL paper numbers (LI 0.87, SAG 67.8, 35 models/11 providers, value alignment weakest, humility best predictor). Do NOT swap in the 0.8632/N=629 draft figures — see the publication plan's reconciliation note.
- No CTA anywhere; the three links are the "URL is the only direction" close, per P8.
- Post 2 ("When AI Rates Itself") picks up exactly where "if you want to check the math" leaves off — deliberate handoff.
- Run Substack's A/B title test with the two titles in the header comment.
-->
