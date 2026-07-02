# arXiv Moderation Hold — What's Happening & What To Do

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Paper:** *ACAT: Benchmarking Self-Description Calibration in LLMs* (v5.0, `arXiv:submit/7336774` [cs.AI])
**Sources:** arXiv's own moderation, endorsement, and appeals documentation (linked at bottom).

---

## Direct answer to your question

> *"Could we revise our arXiv and resubmit?"*

**No — do not delete-and-resubmit while it's on hold.** arXiv is explicit: a duplicate submission while your work is on hold "will lead to further delays," and for some content types resubmitting without an accepted appeal is disallowed. Resubmitting also reads as trying to route around moderation, which hurts you. **Revising the *existing* submission (replace/update) is fine; creating a *new* one is not.**

The real problem isn't the paper needing revision — **months of silence is abnormal** (arXiv targets ~24h holds; QA checks run 1–4 days, occasionally longer). Something specific is blocking it, and the fix depends on *what*. So step one is diagnosis, not resubmission.

---

## Account status readout (2026-07-02)

From your arXiv account: `submit/7336774` — type **New**, status **on hold**, no expiry shown, actions limited to update/delete. Account is **Unaffiliated**, **Career Status: Other**, default category **cs.AI**, ORCID linked, name on file **"Carly Anderson."** The **list view shows no reason message** — so the cause isn't stated there; open the submission detail to see any moderation note. Two fixes regardless: the author name should be canonical **"Carly R. Anderson,"** and it's worth reading the detail view before acting.

## Most likely cause (re-ranked with your status)

1. **TeX source not uploaded — now most-likely, and self-fixable.** Your own preflight checklist says it: *"If your submission is written in TeX you must upload your source. PDFs produced from TeX may be declined."* Your paper is clearly LaTeX-typeset. If you uploaded a **PDF built from LaTeX**, that alone triggers a hold/decline. **Check your uploaded files** — if it's a TeX-derived PDF, hit **Update** on the submission and add the `.tex` source (+ figures + `.bib`). No endorser, no appeal needed.
2. **Endorsement gap.** Per arXiv's **Jan 2026** policy, institutional email is no longer sufficient and **first-time cs.AI submitters need an endorsement** from an established submitter. Your profile (Unaffiliated, gmail, first submission) is the textbook trigger. If the detail view mentions endorsement, this is it — arXiv staff **cannot** waive or provide it.
3. **Moderation flag on framing/fit.** arXiv CS (Oct 2025) declines unrefereed **review/position** papers. ACAT is an **empirical measurement study** (methods, data, stats), so it *should* be exempt — but an independent, governance-flavored single-author submission can draw scrutiny.

---

## Do this, in order

**1. Open the submission detail + check what you uploaded (5 min).**
Click into `submit/7336774` and read any moderation/status message (the list view doesn't show it). Then check your uploaded files: if the paper is LaTeX and you uploaded a **PDF**, that's very likely the hold — fix it directly via **Update** by adding the `.tex` source. If there's an endorsement note → step 2. If neither → step 3. **Don't delete/resubmit.**

**2. If it's endorsement:** you need an endorser for **cs.AI** (someone who's submitted ≥3 CS papers to arXiv in the last 5 years).
- Your paper cites **Kadavath et al., Perez et al., Lin et al., Liang et al.** — open those papers on arXiv and use the **"Which authors of this paper are endorsers?"** link to find eligible endorsers, then send a short, specific request (title, abstract, the arXiv endorsement code from your account).
- A warm intro beats a cold email. If David / anyone in your network has cs.AI standing or knows someone who does, that's the fastest path.

**3. If it's on hold with no clear message (or you disagree with a decision): file through the arXiv *user support portal* — not by emailing moderators.**
- Include: the submission id, a plain-language description of the research content, and **why it belongs in cs.AI**. For a declined paper, attach the PDF.
- Timeline: appeals resolve in ~2 weeks; if nothing in 4 weeks, follow up **through the same portal**.

**4. If it lapsed:** re-submit cleanly *once*, with endorsement lined up first so it doesn't just re-enter the same limbo.

**5. Do NOT:** create duplicate submissions, email moderators directly, or keep waiting passively. Months of silence means it needs an action from you (almost certainly endorsement), not more patience.

---

## The move that de-risks all of this: publish to Zenodo now

Regardless of how the arXiv path resolves, **don't let your citation strategy hostage one moderation queue.** The Zenodo deposit (see `p0-2-zenodo-submission-pack.md`) gives you a **resolvable, Scholar-indexed DOI this week** — a real citable anchor while arXiv is sorted out. When arXiv clears, we cross-link the two records so citations consolidate (they don't compete; cross-posting is normal and permitted).

This is exactly why P0-2 is sequenced here: it converts "blocked on arXiv" from a single point of failure into a parallel track.

---

## On the license (since it's tied to resubmission)

Whatever you do on arXiv, you'll pick a license there, and **Apache-2.0 isn't offered** — arXiv only lists CC-BY-4.0 / CC-BY-SA / CC-BY-NC-SA / CC0 / arXiv-perpetual. Recommendation stands: **CC-BY-4.0 for the paper text**, keep Apache-2.0 on code + data. Details + your one confirmation in `p0-2-zenodo-submission-pack.md` §5.

---

## Draft email A — arXiv status inquiry (via the user support portal)

> Send through the arXiv **Help → Contact** support portal (not to moderators directly). Short and factual. Use this if the detail view has no clear, self-fixable reason.

**Subject:** Status inquiry — submission submit/7336774 (cs.AI), on hold since March 2026

Hello arXiv Support,

I'd like to ask about a submission that has been "on hold" for an extended period:

- Submission: **submit/7336774**
- Title: *ACAT: Benchmarking Self-Description Calibration in Large Language Models*
- Category: **cs.AI** · Submitted: **March 2026**
- Author: **Carly R. Anderson** (ORCID 0009-0003-7540-4245), independent researcher, HumanAIOS / Lasting Light AI

It has shown "on hold" for several months with no status message I can act on. Could you tell me whether it is (a) awaiting endorsement, (b) flagged for a content or formatting issue (e.g., TeX source required), or (c) something else I can resolve? If TeX source is needed I can upload it immediately; if a revision would help, I'm glad to provide one.

This is an empirical measurement study (35 models, 11 providers; full methods, dataset, and statistics) — not a review or position paper. The open dataset is public and I can supply any further detail.

Thank you for your time, and for maintaining arXiv.

Carly R. Anderson
ORCID 0009-0003-7540-4245 · https://humanaios.ai · aioshuman@gmail.com

---

## Draft email B — endorsement request (to a cs.AI endorser)

> Only send once you've confirmed endorsement is the blocker. Find an eligible endorser via a paper you cite → on its arXiv page click **"Which authors of this paper are endorsers?"** Your paper cites **Kadavath, Perez, Lin, Liang** — strong starting points. Personalize the first line; keep it short and easy to say yes to. (Your endorsement **code + link** come from your arXiv account.)

**Subject:** arXiv cs.AI endorsement request — independent researcher, empirical LLM study

Dear Dr. [Name],

I'm an independent researcher (HumanAIOS / Lasting Light AI) requesting an arXiv **cs.AI** endorsement. I found your work through **[specific paper]**, which I cite in the submission.

The paper is an empirical measurement study — *ACAT: Benchmarking Self-Description Calibration in Large Language Models* — reporting a Self-Assessment Gap across 35 models from 11 providers, with an open instrument and dataset. It is not a review or position paper.

- Preprint (DOI): **10.5281/zenodo.21135723**
- Open dataset: https://huggingface.co/datasets/HumanAIOS/acat-assessments
- ORCID: 0009-0003-7540-4245 · https://humanaios.ai

If you're willing, arXiv's endorsement step takes about a minute:
- Endorsement code: **[your code from the arXiv account]**
- Link: `https://arxiv.org/auth/endorse?x=[CODE]`

I completely understand if you're not able to, and I appreciate your time either way.

With thanks,
**Carly R. Anderson**

---

## Sources
- [arXiv — Content Moderation](https://info.arxiv.org/help/moderation/index.html)
- [arXiv — Appealing a moderation decision](https://info.arxiv.org/help/moderation/appeals.html)
- [arXiv — Endorsement](https://info.arxiv.org/help/endorsement.html) · [Updated endorsement policy (Jan 2026)](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/)
- [arXiv — Submission status](https://info.arxiv.org/help/submit_status.html)
- [arXiv — Licenses](https://info.arxiv.org/help/license/index.html)
- [arXiv CS practice for review/position papers (Oct 2025)](https://blog.arxiv.org/2025/10/31/attention-authors-updated-practice-for-review-articles-and-position-papers-in-arxiv-cs-category/)
