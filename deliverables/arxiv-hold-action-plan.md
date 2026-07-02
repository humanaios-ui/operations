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

## Most likely cause (ranked)

1. **Endorsement gap — most probable.** As of arXiv's **Jan 2026** policy, an institutional email is no longer sufficient credibility, and **first-time submitters to a category (cs.AI) need an endorsement** from an established submitter. You're an independent researcher (ORCID `0009-…`, gmail) with no prior cs.AI submissions — this is the textbook trigger. A submission can sit unresolved when it's waiting on endorsement. **arXiv staff cannot waive or provide the endorsement.**
2. **Moderation flag on framing/fit.** arXiv CS tightened practice (Oct 2025) and now declines unrefereed **review/position** papers. ACAT is an **empirical measurement study**, so it *should* be exempt — but a single-author, governance-flavored, independent submission can draw extra scrutiny. Framing it unambiguously as empirical research (methods, data, stats — which it has) matters.
3. **The submission lapsed.** Incomplete/held submissions can be removed after periods of inactivity. After months, it's worth confirming it still exists in your account at all.

---

## Do this, in order

**1. Check the actual status first (5 min).**
Log into your arXiv account → look at the submission's **status + any status messages**. arXiv posts the reason there. This single check tells you which of the three causes you're in. Don't act before you read it.

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

## Sources
- [arXiv — Content Moderation](https://info.arxiv.org/help/moderation/index.html)
- [arXiv — Appealing a moderation decision](https://info.arxiv.org/help/moderation/appeals.html)
- [arXiv — Endorsement](https://info.arxiv.org/help/endorsement.html) · [Updated endorsement policy (Jan 2026)](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/)
- [arXiv — Submission status](https://info.arxiv.org/help/submit_status.html)
- [arXiv — Licenses](https://info.arxiv.org/help/license/index.html)
- [arXiv CS practice for review/position papers (Oct 2025)](https://blog.arxiv.org/2025/10/31/attention-authors-updated-practice-for-review-articles-and-position-papers-in-arxiv-cs-category/)
