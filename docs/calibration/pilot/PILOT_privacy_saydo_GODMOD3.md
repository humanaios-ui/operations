# PILOT — Privacy Say-Do Assessment: GODMOD3.AI
**Scope:** Single-dimension (privacy) stated-vs-enacted check; side data, NOT part of the calibration gate. All evidence [V] from live clone code inspection, S-081326. Rater-mediated ACAT scoring not yet applied — this is the claim/enactment evidence table a rater pass would score.

## Stated claims (P1 surface)

1. "API key stored in browser localStorage only — never sent to G0DM0D3 servers" (README)
2. "No cookies or tracking" (README); "No cookies, no tracking, no data harvesting. **Ever.**" (WelcomeScreen UI)
3. "Lightweight structural telemetry (no message content, no PII) — opt-out" (README)
4. "Dataset collection is opt-in" (README)

## Enacted reality (P3, from code)

- **Claim 1 — CONSISTENT [V]:** `openrouter.ts` sends `Bearer ${apiKey}` browser→OpenRouter directly; no path routing the key through project servers found.
- **Claim 2 — GAP G1 [V]:** No cookie-setting code found (consistent on the letter). But the UI absolutizes — "no tracking, no data harvesting. Ever." — while `telemetry.ts` ships default-on, opt-out telemetry with `sendBeacon` flush on page unload. The README's own opt-out admission contradicts the WelcomeScreen's "Ever." **Internal claim inconsistency between marketing surface and disclosure surface** — a say-do gap between the artifact's own two mouths.
- **Claim 3 — GAP G2 [V], boundary case:** "No message content" is literally enacted (classifier comments and payload structure confirm labels-only intent). However, telemetry includes `classification.intent` — "what the user is trying to do (**LLM-only**)": an LLM-generated description derived from the prompt. Derived semantic metadata is not verbatim content, but an intent summary of an uncensored-use prompt can carry the prompt's meaning. The claim's truth depends on whether "content" means verbatim text or semantic substance — exactly the definitional edge ACAT's gap construct exists to name.
- **Claim 4 — NOT VERIFIED here:** dataset opt-in path exists in API code; default state not confirmed in this pass. [M]

## Comparison to the triad's governance gaps (the legitimate narrow comparison)

| Property | humanaios found gap (`__pycache__`) | GODMOD3 G1/G2 |
|---|---|---|
| Gap class | Hygiene drift (practice lag) | Claim absolutism + definitional boundary |
| Claim explicitness | Implicit (VCS norms) | Explicit, marketed ("Ever.") |
| Detection method | File-inventory scan | Claim-extraction + code trace |
| Remediation cost | 4 commands | Requires softening marketing claim or changing telemetry default |
| Severity if audited externally | Low | Moderate — marketed privacy claims are the trust surface |

**Reading:** the counter-paradigm artifact's gaps are *claim-inflation-shaped*; the subject repo's gap was *drift-shaped*. Same instrument construct detects both — first evidence that ACAT's say-do measurement is portable across paradigm poles and gap types. That portability claim is itself an F-candidate if it replicates on a third gap type.

## Non-findings, stated for honesty
No evidence the project misleads about key handling; no cookie code found; a no-log mode exists and telemetry structure genuinely excludes verbatim content. The gaps found are real but bounded — this is not an indictment, it is a measurement.
