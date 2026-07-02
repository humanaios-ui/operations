# P0-3 · Task 1 — ORCID Edit Sheet

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (you apply in your ORCID account)
**Record:** [orcid.org/0009-0003-7540-4245](https://orcid.org/0009-0003-7540-4245)

**Why this is the highest-value identity fix:** ORCID is the one identifier search engines, Scholar, and publishers trust to say "these works are the *same* Carly Anderson." A filled-out, cross-linked ORCID is what breaks the namesake collision. Each edit below is paste-ready. Log in → edit each section.

---

## 1 · Name (Personal information → Names)

| Field | Set to |
|---|---|
| **Published name** | `Carly R. Anderson` |
| **Also known as** | `Carly Anderson` |

> Keep "Carly Anderson" as an *also-known-as* so the variant already in circulation still resolves to you, while `Carly R. Anderson` becomes the canonical display name everywhere else.

---

## 2 · Employment (Personal information → Employment) — **ADD (currently empty)**

This is the single biggest missing disambiguation signal. Add:

| Field | Value |
|---|---|
| Organization | `HumanAIOS LLC` |
| Department | *(leave blank, or `Lasting Light AI`)* |
| Role/title | `Founder & Principal Investigator` |
| Start date | `2026-02` |
| End date | *(leave blank — ongoing)* |
| City / Region / Country | `Fort Walton Beach` / `FL` / `United States` |
| URL | `https://humanaios.ai` |

*(ORCID may not find "HumanAIOS LLC" in the Ringgold/ROR org lookup — that's fine, type it manually.)*

---

## 3 · Websites & social links (Personal information → Websites)

Add each as a separate link — these are your `sameAs` anchors that tie every surface to one entity:

| Label | URL |
|---|---|
| HumanAIOS (site) | `https://humanaios.ai` |
| Substack | `https://substack.com/@humanaios` |
| GitHub | `https://github.com/humanaios-ui` |
| X | `https://x.com/HumanAIOS` |
| LinkedIn | `https://www.linkedin.com/in/humanaios` |
| HuggingFace | `https://huggingface.co/HumanAIOS` |

---

## 4 · Keywords (Personal information → Keywords)

Add (comma-separated, each becomes a tag):

```
AI self-assessment, self-description calibration, behavioral observability, AI governance, LLM evaluation, psychometrics, AI alignment
```

---

## 5 · Works — reconcile + add the DOI

Your record currently has two works. Here's the fix:

**(a) Reconcile the divergent-title work.** The work currently titled *"The Self-Assessment Gap: Measuring the Divergence Between AI Behavioral Self-Report and Post-Calibration Correction"* is the same paper as the canonical preprint. **Edit it** (or delete + re-add) so it reads:

| Field | Value |
|---|---|
| Title | `ACAT: Benchmarking Self-Description Calibration in Large Language Models` |
| Type | `Preprint` |
| Publication date | `2026-03` |
| **DOI** (add as external ID) | `10.5281/zenodo.21135723` |
| URL | `https://zenodo.org/records/21135723` |

**(b) Cleanest way to add it — auto-import (recommended).** Once the Zenodo record is **published**, add the work without typing:
- **Add works → Search & link → DataCite** (Zenodo DOIs are registered with DataCite), find `10.5281/zenodo.21135723`, and import — it pulls title/authors/date/DOI correctly.
- Even easier: in **Zenodo**, log in / connect your **ORCID**, and published records can push to ORCID automatically. If you connect ORCID in Zenodo before publishing, the work appears in ORCID on publish — then just delete the old divergent-title entry so you don't have a duplicate.

**(c) Keep** the *"HumanAIOS: Behavioral Observability Infrastructure for AI Systems"* report — it's a distinct output. (Optionally set its type to `Report` and add a URL to humanaios.ai.)

> ⚠️ **Avoid duplicates:** after the canonical preprint is in (via edit or auto-import), make sure there's only **one** entry for this paper — remove the old-title version.

---

## 6 · Optional but quick

- **Education** — you have NAU (BS Chemistry). Optionally add *Master of Information Technology, University of the People (in progress)* if you want it visible.
- **Biography** — yours is already good (names HumanAIOS + ACAT). No change needed; if you touch it, make sure the name reads "Carly R. Anderson."
- **Email** — confirm `aioshuman@gmail.com` is the primary (matches the canonical-email decision, still pending your final call vs. the paper's address).

---

## Apply order (fastest first)
1. **Name** (30 sec) → 2. **Employment** (2 min, biggest signal) → 3. **Websites** (2 min) → 4. **Keywords** (30 sec) → 5. **Works** (do after Zenodo publish, via auto-import).

When you've published Zenodo + applied these, ping me and I'll move to the next surface (**HuggingFace** card redline, then **Substack**).
