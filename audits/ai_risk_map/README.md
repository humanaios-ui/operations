# AI Risk Map v1.3 — bounded HumanAIOS control crosswalk (Z1 observation)

**Status:** CANDIDATE / NOT ADMITTED. **Authority effect:** NONE. 
**Primary HumanAIOS scope:** `humanaios-ui/operations`, existing Resource Miner `/api/intent` → INTENT-OS public objective preview; named governance / CI components only where individually inspected. **Not a company-wide audit.**

## Source, provenance and license

Evan Wheeler, *AI Risk Map v1.3* (2026), © Evan Wheeler, CC BY-SA 4.0.
Immutable source: https://github.com/wheels344i-gte/ai-risk-map/blob/v1.3/AI-Risk-Map.csv
GitHub source **blob SHA**: `01a7c3ad7d5bfd52b11f6b29bd6a753b97553af5`.
Full wording, citations, scope exclusions and change log remain with the source publisher; the local JSON stores a thin ID/domain/category index, **not** a copied control framework.
This crosswalk is an adaptation/compilation distributed under CC BY-SA 4.0. Its HumanAIOS implementation observations are separately identified.
Treat AI Risk Map as a taxonomy of candidate *risk factors*, not controls, risk assessments, likelihoods, probabilities, or authority.

Source v1.3 has **196 active IDs** among 197 rows; `AIRM-171` is retired. Unique active categories: **55**. Domains: **12**.

| Risk owner domain | Active factors | Risk owner domain | Active factors |
| --- | ---: | --- | ---: |
| AI Governance & Accountability | 19 | Strategy & Value Realization | 12 |
| Data & Privacy | 19 | Model Development & Performance | 16 |
| Security & Adversarial Threats | 23 | Safety, Ethics & Responsible AI | 18 |
| Operations & Resilience | 22 | Legal, Regulatory & Compliance | 14 |
| Third-Party & Model Supply Chain | 15 | Workforce, Human & Societal | 14 |
| Financial & Resource | 8 | Autonomy & Delegated Action (Agentic AI) | 16 |

## Coverage: source indexed versus actual control review

The JSON contains **all 196 active factor IDs**; it compares only **24 individual factors** with code and control surfaces actually inspected in this pilot.

| Scoped result | Factors | Meaning |
| --- | ---: | --- |
| `SCOPED_CONTROL` | 6 | Named code boundary observed; live/protected effectiveness not yet established |
| `PARTIAL_CONTROL` | 13 | Some evidence relevant; not a complete risk mitigation |
| `OBSERVED_GAP` | 2 | Narrow missing or non-enforcing condition directly observable in reviewed code |
| `NOT_APPLICABLE_SCOPED` | 3 | Not triggered by this specific stateless, no-agent-execution path; wider system remains unassessed |
| `UNREVIEWED` | 172 | **Unknown, not unprotected**; not evidence of missing controls |

**No row means APPROVED, RISK_ACCEPTED or PRODUCTION_SAFE.** `observed_effectiveness=UNVERIFIED` throughout because actual protected CI and real behavior were not independently checked when authored.

### Scenarios supported by code observations

**AIRM-174 / AIRM-186 / AIRM-077 — unauthorized action from opportunity text.** The existing `resource_miner/intent_os.py` output has `"authority": "NONE"` and `"execution": "DISABLED"`. It ranks public discovery candidates; it does not assess eligibility or apply for them. This is a code-supported *scoped* guard, not evidence that every HumanAIOS agent is incapable of execution.

**AIRM-035 — stale opportunity.** The same module filters expired deadlines and warns that currentness is unverified. A past date filter is *not* primary-source verification. Coverage remains partial.

**AIRM-075 — text/URL injection into browser.** The existing `intent-os.html` sets human-visible text through `textContent`; the backend `_public_https` rejects unsafe URL forms. This does not replace independent adversarial/browser tests.

**AIRM-085 / AIRM-039 — private information.** Public names are allowlisted by string. A string `source_name` is not a signed origin assertion nor a per-user permission check. No private account retrieval should be added through this preview without a separate authorized connector boundary.

**AIRM-007 — separation of duties.** The default-branch admission-gate and SCVC witness are observed. Neither workflow by itself is a global proof that every agent action has independent human authorization.

### Observed gaps (do not silently promote into claims of total exposure)

**G1 / AIRM-084: secrets workflow does not block on gitleaks.**
- **Observed:** `.github/workflows/security-gates.yml` has `continue-on-error: true` immediately under `gitleaks/gitleaks-action@v3`. A gitleaks failure alone cannot fail that job via that step.
- **Scope:** the specific gitleaks step; dependency scanning and other checks have separate semantics.
- **Failure test:** insert a synthetic secret-canary fixture in an isolated test branch and verify the protected secret-scanning check actually blocks; **never commit a real credential**.
- **Action:** separately inspect gitleaks licensing/rate limits/reliability and human security-gate policy; on approval, remove `continue-on-error` and verify exact-head protected CI. Do not remove the rest of security gates or waive admission.
- **Current remedy:** NOT APPLIED; would change protected CI behavior without verified readiness.

**G2 / AIRM-109: public objective receipt is an unsigned digest, not an authenticated decision/authorization audit.**
- **Observed:** `resource_miner/intent_os.py` explicitly marks `receipt_kind=UNSIGNED_INPUT_AND_SELECTION_DIGEST_NOT_AN_ATTESTATION`; the inspected `app.py` intent path returns the read-only response without an authenticated per-action audit record.
- **Scope:** this **read-only preview** only. No consequential action exists on this route, so this is a **conditional execution-readiness gap**, not evidence of a harmful logged-out action or current duty to retain private prompts.
- **Failure test:** if a future agent attempts to execute/claim using only that digest, it must be denied; a reviewer should not be able to present digest as authenticated authorization.
- **Action:** keep `execution=DISABLED`. If any consequential action is proposed, use the existing governed authorization/witness infrastructure; review privacy/retention and signed evidence before enabling. **Do not add an unneeded logging database now.**

### Open questions — not observed gaps

Source labels can be forged by an upstream component, but no public exploitation path or unauthorized private-data leak was established from the reviewed code. Model-provider diligence, comprehensive agent inventory, customer disclosure, finance forecasting, and production reliability remain `UNREVIEWED` where the evidence is missing. Do not interpret absence of mapped evidence as absence of protection. The taxonomy does not support numerical risk scores.

## Minimal implementation / how to reproduce

Data: `audits/ai_risk_map/SCOPED_CROSSWALK_V0_1.json`. It records stable source factor IDs, owners/categories, scoped mapping state and exact existing file/needle evidence. It does **not** activate a risk engine, network fetch, model, agent or UI endpoint. The public `/api/intent` path and its authorization semantics are unchanged.

Local structural test:

```sh
python3 -m pytest tests/test_ai_risk_map_crosswalk.py -q
```

Existing protected `quality-baseline.yml` already runs suites enumerated in `.tool-control/baseline_tests.yaml`; the new regression is listed there. It verifies count/IDs/categories, on-disk evidence anchors, tracked gaps and no-execution semantics. It does **not** prove operational mitigation. `security-gates.yml` remains unchanged.

## Admission and decision

1. Human reviews the two observed conditions and confirms whether mitigation is required now.
2. Verify these tests and existing protected CI on **this PR head**, plus independent CodeRabbit review.
3. Obtain required authenticated human approval and repository admission **separately**. No agent comment or crosswalk row constitutes admission.
4. Only after review, consider surfacing relevant scoped risk observations in INTENT-OS; never display `UNREVIEWED` as an identified flaw or `SCOPED_CONTROL` as a guarantee.
5. Extend factor review **only on evidence** from actual repository control code and tests, following the existing read-only graph translation work. No parallel risk register or authority service is authorized.

**Stop rule:** If this crosswalk does not help catch a real failure, reduce ungrounded risk claims, or speed a human decision, remove the extra apparatus.
