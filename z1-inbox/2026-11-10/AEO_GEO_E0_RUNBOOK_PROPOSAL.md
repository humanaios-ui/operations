# AEO/GEO E0 runbook — Z1 proposal (HAIOS-MM-ACAT-002)

**Status:** PROPOSED · **AUTHORITY_EFFECT:** NONE · **Findings:** NOT REGISTERED · **Multi-model comparison:** INCOMPLETE
**Filed by:** Z1 (Claude) on the live instruction of the operator ("Update repository"), 2026-11-10.
**Awaiting:** Z2 (Night) ratification. This file ratifies nothing, approves no publication, and changes no governed file, automation, or schedule.
**Privacy:** contains no account identifiers, mailbox identifiers, or private message pointers. Private evidence stays in restricted storage; this repo holds public-safe summaries only.

## 1. Operator decisions recorded (informal, from the operator's own messages; not yet in an authenticated form)

| Decision | Record |
|---|---|
| Single source of truth is a versioned foundation file | "SSOT file for sure" |
| Keep the original three-horizon daily prompt; do not adopt the neutral-baseline rewrite | Operator chose to keep the original |
| Posts are approved by the operator in a draft-only publishing tool | Operator message |
| Public entry must be secure and anonymous | Operator message |
| Order of work | identity → P2 or single-operator limit → anonymous form → draft-only approval flow → Gray Swan test → only then public entry |

Labeling note (not an objection): with the original prompt, daily outputs are a **discovery scan**, not a controlled baseline. Grok and ChatGPT proposed source/date fields and a scan-vs-baseline split; those are open suggestions, not adopted.

## 2. Single-operator limit (use on every claim, post, and the SSOT file until a P2 is named)

> HumanAIOS research is run and reviewed by a single operator. No independent human reviewer has examined these results. Agent identity is claimed, not authenticated, unless marked RUN_BOUND or INDEPENDENTLY_CHECKED. Findings are not registered and are interpretive (TRL 2–3).

Public reviewers recruited from posts are **public challengers**, not the independent P2.

## 3. Runbook

Hour figures are estimates, not measurements.

### Step 1 — Agent identity (operator, ~3–6 h)
1. One GitHub machine account (or GitHub App) per agent; least privilege (read, comment on issues in one repo; no merge, no admin, no approval).
2. Operator account uses a passkey or hardware key; no agent holds any token for it. Branch protection requires review from the operator account.
3. Per-run challenge: a fresh random file plus nonce per leg per run, readable only by that leg's connector. The leg hashes the file and echoes the nonce with its output hash.
4. Ledger line per run: `LEG | RUN_ID | acting principal | nonce | input hash | output hash | actions with receipts | identity level`.
   Identity levels: `CLAIMED → TRANSPORT_VERIFIED → RUN_BOUND → INDEPENDENTLY_CHECKED`. Never promote on an agent's say-so.
- **Done when:** a forged `LEG` header from another principal is flagged; no agent token can approve or merge; three consecutive runs carry a correct nonce echo.

### Step 2 — P2 or single-operator limit (operator, ~1–3 h)
- Option A: name a person who did not build or freeze the packet; give them the blinded packet and key. Review task: omissions, contradictions, unsupported certainty, false authority.
- Option B (now): apply the §2 line everywhere.
- **Done when:** the §2 line is on the SSOT file and post template, or a named P2 accepts in writing from an account that is not the operator's.

### Step 3 — Anonymous form (operator builds, Z1 reviews, ~2–4 h)
- No login; no name/email/contact field; free text capped (~1,000 chars) plus a category dropdown.
- Check and minimize what the form tool logs; state remaining limits in a privacy notice. Do **not** use GitHub Discussions for this (requires a GitHub login).
- Spam control and a moderation queue: nothing is public until approved.
- Private store; agents never read raw submissions. A sanitizer strips links/markup, caps length, and flags instruction-like text first.
- Written retention rule.
- **Done when:** fake personal data in a test submission is not stored; an injected instruction is flagged; nothing shows publicly before approval.

### Step 4 — Draft-only approval flow (operator, ~2 h, then ≤30 min/day)
Agents draft with no publish permission (draft-only scopes where offered, separate workspace). Operator reviews against a checklist (sources dated, claim within evidence, §2 line present, AI involvement disclosed), approves in the tool, records a receipt (artifact hash, platform, time, expiry, retries), publishes personally, and reads back the result. Weekly batch until one cycle closes.
- **Done when:** a test draft passes the checklist; a post goes out only via the operator's click; the ledger has the matching receipt.

### Step 5 — Gray Swan indirect-injection challenge (operator, ~2–4 h, after Steps 1–4)
Throwaway account; no private data; read the terms first (not yet reviewed by Z1). Convert what is learned into ~20 test fixtures for the intake (form text, quoted email, wrong-thread reply, fake "operator approves" line).
- **Done when:** no fixture causes an agent action, or failures are logged, fixed, and the set re-run.

### Gate
No public entry opens until Steps 1, 2 and 4 are done and Step 5 passes. Step 3 may be built in parallel but stays closed to the public.

## 4. Red-team findings carried forward (process, not case content)
Identity is claimed not proven; the record is split across channels; operator approval is not authenticated or scoped; convergence prompts can manufacture agreement; optimization changes what is measured; no frozen public baseline; claims could outrun evidence; agent-reported actions are unverified; matching hashes can be copied; independent P2 unnamed; connector sprawl; email threading fragments the record. Agents' own mitigations are requested in the coordination channel and are not recorded here until received.

## 5. Decisions required, with ROI (estimates; none measured)

| Decision | Cost | Benefit | Reversible | ROI | Why |
|---|---|---|---|---|---|
| Revoke unintended third-party sign-ins | ~30 min | Closes a live exposure | Yes | High | Only active exposure today |
| Name P2 or adopt §2 limit | 1–3 h | Claims become honest | Yes | High | Cheap; unblocks every public claim |
| Agent identity (Step 1) | 3–6 h | Makes attribution and approval checkable | Mostly | High | Everything else depends on it |
| Canonical ledger / SSOT file | 1–2 h + 2–4 h | Ends split record | Yes | High | Needs Z2 under CLAUDE.md |
| Scoped, expiring AEO approval | 30–60 min | Stops scope creep | Yes | High | Makes approval usable |
| Anonymous form (Step 3) | 2–4 h | Safe public entry | Yes | Moderate | Valuable only after Steps 1, 2, 4 |
| Public platform choice | 1 h + 2–3 h | Public test surface | Mostly | Low now | Defer until first cycle closes |

## 6. Not done / not claimed
No account, token, form, automation, schedule, label, or publishing change was made. No P1, P2, P3, case analysis, or ACAT verdict was produced. No Z2 hash exists for this file.

AUTHORITY_EFFECT: NONE
