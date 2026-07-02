# Zenodo REST API — Run-It-Yourself Helpers

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Record:** `21135723` · **DOI:** `10.5281/zenodo.21135723`

> **Credential boundary (important):** These scripts read your Zenodo **personal access token from an environment variable** so it never appears in the code, in this repo, or in front of me. **You run them; I never see or handle the token.** Don't paste your token into chat. Create one at Zenodo → *Applications → Personal access tokens* with scopes `deposit:write` + `deposit:actions`.
>
> ```bash
> export ZENODO_TOKEN="paste-your-token-in-your-own-terminal"
> ```

> **Do you even need the edit flow?** If your UI deposit already has the abstract, keywords, related works, references, and CC-BY-4.0 license, the record is **done** — use §1 to *verify*, and only use §2 if something's actually missing. Editing a published record re-runs the publish step on your live research output, so don't do it casually.

---

## 1 · Verify the published record (read-only, **no token needed**)

Published records are public. This confirms what's actually on the record:

```bash
curl -s https://zenodo.org/api/records/21135723 \
| python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('metadata',{}); \
print('title:', m.get('title')); \
print('doi:', d.get('doi')); \
print('license:', (m.get('license') or {})); \
print('keywords:', m.get('keywords')); \
print('related:', [(r.get('relation'), r.get('identifier')) for r in m.get('related_identifiers',[])]); \
print('refs:', len(m.get('references',[])), 'references'); \
print('creators:', [(c.get('name'), c.get('orcid')) for c in m.get('creators',[])])"
```

*(If Zenodo rate-limits you, wait 60s and retry — it caps guests at 60 req/min.)*

---

## 2 · (Optional) Patch metadata via the edit → update → publish flow

Only if §1 shows something missing. The legacy Deposit API uses the **edit → PUT → publish** sequence. Save as `zenodo_patch.py` and run `python3 zenodo_patch.py`:

```python
import os, requests

TOKEN = os.environ["ZENODO_TOKEN"]           # never hard-code the token
DEP_ID = 21135723
BASE = "https://zenodo.org/api/deposit/depositions"
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

metadata = {
  "upload_type": "publication",
  "publication_type": "preprint",
  "title": "ACAT: Benchmarking Self-Description Calibration in Large Language Models",
  "publication_date": "2026-03-07",
  "version": "v5.0",
  "language": "eng",
  "access_right": "open",
  "license": "cc-by-4.0",
  "creators": [
    {"name": "Anderson, Carly R.",
     "affiliation": "HumanAIOS LLC (Lasting Light AI)",
     "orcid": "0009-0003-7540-4245"}
  ],
  "description": (
    "We introduce ACAT (AI Calibrated Assessment Tool), an open-source instrument that "
    "measures self-description calibration in AI systems. Using a three-phase protocol"
    "—blind self-report, empirical calibration, and corrected self-report—we quantify "
    "the Self-Assessment Gap (SAG): the difference between what AI systems describe about "
    "their own capabilities and how those descriptions change when exposed to empirical peer "
    "data. Across 35 models from 11 providers, assessed by two independent collectors using "
    "different methods (API-based and manual web-based), we find a mean SAG of 67.8 points on "
    "a 600-point scale (SD = 62.3). The Learning Index (LI)—the ratio of post-calibration to "
    "pre-calibration composite scores—averages 0.87 (SD = 0.12). Value Alignment is the "
    "consistently weakest self-assessed dimension; Humility is the strongest predictor of "
    "calibration response. Instrument, dataset, and methodology are freely available."
  ),
  "keywords": [
    "AI self-assessment", "self-description calibration", "behavioral observability",
    "AI governance", "LLM evaluation", "psychometrics", "AI alignment",
    "Learning Index", "Self-Assessment Gap"
  ],
  "related_identifiers": [
    {"relation": "isSupplementedBy",
     "identifier": "https://huggingface.co/datasets/HumanAIOS/acat-assessments",
     "resource_type": "dataset"},
    {"relation": "isDocumentedBy", "identifier": "https://humanaios.ai"}
  ],
  "references": [
    "Lin, S., Hilton, J., & Evans, O. (2022). TruthfulQA: Measuring How Models Mimic Human Falsehoods. ACL, 3214-3252.",
    "Liang, P., et al. (2023). Holistic Evaluation of Language Models. TMLR.",
    "Srivastava, A., et al. (2023). Beyond the Imitation Game (BIG-bench). TMLR.",
    "Pan, A., et al. (2023). Do the Rewards Justify the Means? MACHIAVELLI. arXiv:2304.03279.",
    "Crowne, D. P., & Marlowe, D. (1960). A new scale of social desirability. J. Consulting Psychology, 24(4), 349-354.",
    "Kruger, J., & Dunning, D. (1999). Unskilled and unaware of it. JPSP, 77(6), 1121-1134.",
    "Lichtenstein, S., Fischhoff, B., & Phillips, L. D. (1977). Calibration of probabilities. In Decision Making and Change in Human Affairs, 275-324. Springer.",
    "Kadavath, S., et al. (2022). Language Models (Mostly) Know What They Know. arXiv:2207.05221.",
    "Perez, E., et al. (2023). Discovering Language Model Behaviors with Model-Written Evaluations. Findings of ACL 2023."
  ]
}

# 1) unlock the published record for editing
r = requests.post(f"{BASE}/{DEP_ID}/actions/edit", headers=H); print("edit:", r.status_code)
# 2) update metadata
r = requests.put(f"{BASE}/{DEP_ID}", json={"metadata": metadata}, headers=H); print("update:", r.status_code, r.text[:400])
# 3) re-publish
r = requests.post(f"{BASE}/{DEP_ID}/actions/publish", headers=H); print("publish:", r.status_code)
```

---

## 3 · Caveats (read before running §2)

- **InvenioRDM compatibility:** records created in Zenodo's current UI don't always accept the *legacy* Deposit API cleanly — the `edit` step can return `400`/`409`. If it does, **just finish the edits in the web UI** (it's the supported path for UI-created records) rather than fighting the API.
- **`license` id:** must be a valid id from `GET https://zenodo.org/api/licenses/` — `cc-by-4.0` is correct for CC-BY-4.0.
- **Publishing is permanent:** step 3 re-publishes your live record. Verify step 2 returned `200` with the metadata you expect before publishing.
- **Sandbox first (optional):** to rehearse without touching the real record, use `https://sandbox.zenodo.org` (separate account + token; test DOIs use the `10.5072` prefix).

---

## What I'd actually do
1. Run **§1** to confirm the record has the dataset related-id, references, keywords, and CC-BY-4.0.
2. If anything's missing, fix it in the **web UI** (simplest for a UI-created record). Reserve §2 for if you want to script future deposits.
3. Then the API is a nice-to-have for **future preprints** — the §2 `metadata` block is a reusable template.

Tell me which way you want to go, or hand me the §1 output and I'll tell you exactly what (if anything) still needs adding.
