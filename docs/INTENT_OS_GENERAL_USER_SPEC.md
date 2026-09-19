# Intent-OS for a general user — tone, connectors, and the data line
Z1 draft 2026-09-08 · hypothetical prototyping scope · nothing here is ratified

## 1. Tone: project-supplied lexicon
Board renders from project data; add a `lexicon` block. Renderer substitutes on display.

| internal term | HumanAIOS lexicon | general default |
|---|---|---|
| Z1 / Z2 / Z3 | Z1 / Z2 / Z3 | proposer / owner / lands |
| ratify by hash | ratify by hash | confirm with the fingerprint |
| operated cycle | operated cycle | real run (not a rehearsal) |
| IC-030 live read | IC-030 | check against the live source |
| falsifier | falsifier | what would prove this wrong |
| DRIFT / GAP / STALE | same | off-course / missing / out of date |

Rule: the engine never changes; only words do. A project without a lexicon gets the general default.

## 2. Connectors without holding credentials
- OAuth per service; scopes read-only wherever the research need allows.
- Tokens live on the user's side: their own relay (decision_relay.py pattern) or a broker that stores one encrypted blob per tagline and cannot read it.
- The board holds no secret. It asks the relay; the relay asks the service; only derived events return.
- Needed per user: relay or broker slot, key store, revocation path, scope manifest, consent record keyed to the tagline.

## 3. The data line — three readings, no preference encoded
A. Extract everything; call it personal data; carry consent, lawful basis, retention, deletion, DPA.
B. Collect none; extract derived behavior on the user's side; only features leave.  ← Z1 reads as incumbent
C. Hybrid: raw local, features central, raw deleted on schedule; hardest to audit.

"No personal information" is only true under B. Under A or C the claim fails a read.

## 4. Feature set that leaves the device under B (behavioral outputs, never content)
decision latency (question posted → option picked) · reversal rate · echo-hash time · forecast vs outcome (Brier) ·
step state transitions per day · deadline hit/miss · external-review novelty ratio · DRIFT count in assistant output ·
connector call counts by type (no payloads) · session length and cadence.
Excluded by construction: names, emails, message bodies, file contents, repo names, calendar titles, IPs.
Identity: tagline only; tagline ↔ person mapping never leaves the user's device.

## 5. Falsifier for B
If a behavioral finding cannot be reproduced from the feature set alone and requires reading content, B is insufficient for that finding; record it as a GAP, do not widen collection silently.

## 6. Hash link — correction to §3B (Z2 raised it; Z1 had overstated the loss)
Every feature leaving the relay carries `content_ref = HMAC-SHA256(user_key, canonical(content))`.
- user_key is generated at intake, held on the user's device, never transmitted; the tagline maps to it only there.
- HMAC, not bare sha: short content is dictionary-guessable; keying closes that and prevents cross-user linkage.
- What the record holds: fingerprint + features. What it cannot do: recover content. What it can do:
  (i) prove a feature came from a specific unseen artifact (the crossing left a record);
  (ii) verify a later voluntary disclosure — user shows the artifact, relay recomputes, match = same artifact;
  (iii) detect the same artifact recurring across sessions.
- Corrected cost line: content cannot be read without the user; it can always be verified.
- Not chosen: encrypted content held centrally with a user key. It is technically sound but is the "secret stash"; under it the claim "we hold no personal information" fails a read.
- Falsifier for §6: a content_ref that verifies against two different artifacts (collision or canonicalisation bug) → GAP, ref scheme reopened.
