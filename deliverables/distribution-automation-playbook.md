# Distribution & Automation Playbook — The Witness Stand

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready

---

## The honest answer first (what to automate, what not to)

Your question has three parts, and they are *not* equally automatable — and one of them you shouldn't automate at all:

| You said | Verdict | Why |
|---|---|---|
| **Publish articles to Substack** | ✅ Semi-automate (schedule) | Native scheduler + limited [Substack Developer API](https://support.substack.com/hc/en-us/articles/45099095296916-Substack-Developer-API). ToS-clean. |
| **Cross-post to LinkedIn / X** | ✅ Automate via **official-API** schedulers | Buffer / Typefully / Narrareach post through LinkedIn's + X's sanctioned APIs. Safe. |
| **"Communication through LinkedIn"** (auto-connect / auto-DM / auto-comment) | ❌ **Do not** | Against LinkedIn ToS → restrictions or bans ([ConnectSafely 2026](https://connectsafely.ai/articles/is-linkedin-automation-safe-tos-scraping-guide-2026)). And it's the definition of *promotion*, which your P8 (Tradition 11) forbids. |
| **Recommendations outreach** | ❌ Keep human | It's relational. Automating it defeats the purpose and reads as spam. |

**The principle, and it happens to be your governance:** automate the *mechanics* (formatting, scheduling, posting sanctioned content); keep the *relationships* human. "Manifest, don't promote" and "no CTAs" map exactly onto *scheduled distribution of substance + human relationship-building* — never bots reaching into people's inboxes.

**My boundary as your agent:** I don't post, connect, or DM on your behalf — that needs your account access and per-action approval, which I don't take. I build the pipeline, the drafts, the scheduled content, the Notes bank, the target list, and the templates. **You (or a scheduler you've connected) hit publish.**

---

## The system (human-in-the-loop, four layers)

### 1 · Content pipeline — git is the source of truth
Posts live in this repo as markdown (like `witness-stand-post-1.md`) → you review → they publish. Version-controlled, guardrail-checked, canonical stats/links baked in.

**One source → three channels.** From each post I produce: (a) the Substack article, (b) a LinkedIn version (LinkedIn's native *newsletter* article is indexable + reaches your network), (c) an X thread, (d) 2–3 Notes. *I can build a small `repurpose.py` that turns one markdown post into all four formats — that's legitimate automation I can write for you.*

### 2 · Publishing (ToS-safe scheduling)
- **Substack article:** write/paste in the editor → **Schedule** for the cadence slot. Turn on Substack's native auto-share to X + LinkedIn + Notes on publish (free, built-in).
- **LinkedIn + X:** a scheduler on **official APIs** — **Typefully** or **Buffer** (X + LinkedIn), or **Narrareach** if you want Substack **Notes** scheduling too. You connect the accounts once (your OAuth); I hand you the pre-written, pre-timed content.
- **Avoid:** unofficial/"reverse-engineered" Substack API tools and any LinkedIn auto-connect/DM tool. Ban risk + ToS + off-ethos.

### 3 · Notes cadence — the actual growth engine
Evidence: Notes + Recommendations drive ~40% of Substack growth under 10K subs; 20–30 min/day of Notes drove the *majority* of subscribers for many. So Notes aren't a side task — they're the engine.

**Cadence:** 3–5 Notes/week, biweekly long post. A repeatable **Notes bank** seeded from REGISTERED.md:
| Format | Example seed |
|---|---|
| One finding, plainly | "A model's confidence in its own honesty isn't calibrated to anything. Shown peer data, 35 systems revised down ~13%." |
| A correction (the flex) | "We filed an integrity correction on our own instrument today. Here's what we got wrong and why we left the pointer." |
| A chart | one dimension's gap, captioned |
| A question | "If a system can't witness its own behavior, what exactly is it reporting when it says it's 'sure'?" |
| A quiet link | one line + the DOI, no CTA |

*I can generate a starter bank of ~15 Notes from your registry so you're never staring at a blank box.*

### 4 · Recommendations — human, and the highest-leverage relationship move
One recommendation from a 5K+ peer newsletter = 50–200 subs, and it's Tradition-11-clean (you're *recommended into* the niche, not broadcasting). **Reality:** recs work best **peer-to-peer** — a brand-new newsletter asking a giant rarely gets reciprocated. So: recommend *first*, engage genuinely, and target a **mix of peer-tier and a few aspirational** publications.

---

## Recommendations target list (AI-safety / eval / governance)

Master directory to mine: **[LessWrong — Top AI safety newsletters](https://www.lesswrong.com/posts/vxSGDLGRtfcf6FWBg/top-ai-safety-newsletters-books-podcasts-etc-new-aisafety)**. Ranked by fit for *your* niche (behavioral eval / calibration / governance):

| Tier | Publication | Why it fits | Move |
|---|---|---|---|
| **Best fit** | **[AI Safety at the Frontier](https://aisafetyfrontier.substack.com/)** | Research-forward, paper highlights — your exact readership | Recommend it; comment substantively on a paper post |
| Best fit | **[The EU AI Act Newsletter](https://artificialintelligenceact.substack.com/)** | Governance/accountability audience overlaps your funder track | Recommend; offer the Witness-Problem angle on auditability |
| Anchor | **[AI Safety Newsletter / ML Safety (CAIS)](https://newsletter.safe.ai/)** | The field's hub (Hendrycks/CAIS) | Engage/cite; aspirational rec, not a cold ask |
| Anchor | **Import AI (Jack Clark)** | Broad reach, research-literate | Cite in your posts; long-game |
| Peer | **Responsible AI Weekly**, **AI Safety Events & Training** | Peer-tier, reciprocal-friendly | Recommend first → likely reciprocal |
| Verify | **Zvi — "Don't Worry About the Vase"**, **Joe Carlsmith**, **Liron Shapira** | Well-known adjacent voices | Confirm current handles before outreach |

*Strategy: recommend 4–6 peer/best-fit pubs from your account now (recommending costs nothing and seeds reciprocity), engage in comments/Notes weekly, and let a few aspirational ones come from being genuinely useful in the niche.*

**Recommendation-request note (Tradition-11 clean, paste + personalize):**
> Hi [name] — I read [specific post] and [one genuine, specific reaction]. I write *The Witness Stand*, on measuring the gap between what AI systems say about themselves and how they behave (open instrument + dataset). I've added your newsletter to my Recommendations. No obligation at all to reciprocate — mostly wanted to say the work resonates. — Carly

*(No ask-for-ask, no hype. The recommendation is given, not traded. That's the ethos and it also works better.)*

---

## The operating rhythm (biweekly)
| Day | Action | Tool |
|---|---|---|
| Mon | 1 Note (a finding) | scheduler / manual |
| Tue (biweekly) | **Publish the post** + auto-share | Substack scheduler |
| Wed | 1 Note (the post's key chart) | scheduler |
| Thu | Engage: comment on 2 peer newsletters | manual (human) |
| Fri | 1 Note (a correction / question) | scheduler |
| Monthly | Review metrics; send 1–2 rec notes | manual (human) |

**Metrics that matter:** Recommendations received (leading indicator), inside-Substack vs external referral split, Notes→sub conversion, and *quality* of inbound (researchers citing, funders reaching out) — the attraction test.

---

## What I can build for you next (just say which)
1. **`repurpose.py`** — one markdown post → Substack + LinkedIn-newsletter + X-thread + Notes drafts. Legit, ToS-clean automation.
2. **Notes bank** — ~15 ready Notes drawn from REGISTERED.md, guardrail-checked.
3. **Recommendations tracker** — a small table (target, tier, recommended-them?, status) to run the human outreach against.
4. **Scheduler decision** — a 3-way compare (Typefully / Buffer / Narrareach) against your exact needs (Notes scheduling? LinkedIn newsletter? budget?).

**One boundary to restate:** connecting the accounts and pressing publish/connect stays with you. I prepare; you authorize. That keeps you ToS-safe, ban-safe, and Tradition-11-clean.
