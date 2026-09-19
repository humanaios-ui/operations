---
name: humanaios-wgs-sweep
description: Cross-session reconciliation sweep over the posted WGS record (#wgs-sync). Reads #wgs-sync and fetches REGISTERED.md itself at the start of every sweep, then reconciles three things the channel silently accumulates — silent failures that keep recurring, F-/IC-/H- candidates that were named in a post but never reached REGISTERED.md (under-registration), and Z3 "Night executes" carry-forward items that were handed off but never closed. Use whenever the operator says "sweep the WGS," "WGS sweep," "scan the WGS," "reconcile the channel," "what did we name but never register," "check for dangling Z3," "are there overdue carries," "recurring silent failures," or "audit the WGS log." It drafts a sweep report to #wgs-sync via draft-then-operator-send and waits for review; it never auto-posts, never self-registers, never executes Z3.

architecture: governance
refactor: S-061526 — added Z3 prohibition, Z3 Impulse Audit Log, operational checklist (humanaios-dual-architecture compliance)
---

# HumanAIOS WGS Sweep

This skill sweeps the **WGS channel record** — `#wgs-sync` — across the last N posted session logs and reconciles the commitments those posts made against live canonical state. It is the cross-session counterpart to the session-scoped scanners: where `humanaios-findings-scan` (Skill 6) asks *"what should THIS session register?"* and `humanaios-session-close` (Skill 2) drafts *one* close post for the current session, this skill asks *"across the posted record, what did we name and then never close?"*

It is **orientation, not authority** — when the live `REGISTERED.md` or `SESSION_RITUALS.md` disagrees with this skill, the live files win.

This skill operates in **Zone 1**. It *reads, reconciles, and routes*. It does **not** register, does **not** execute Z3, does **not** seal anything, and does **not** assign final IDs. Promotion and execution remain Zone 2 / Zone 3 (Night) actions.

## What this skill exists to prevent

**Channel-level commitment rot.** Each WGS close post names things: silent failures (B.5 TIER 1/2/3), F/IC/H candidates routed to Zone 2, and Z3 items handed to Night. The per-session skills do their job at close — but nothing checks, three or ten sessions later, whether those named items actually landed. The result is silent drift in the *record itself*:

- An F-candidate routed "→ Zone 2 for ratification" that never entered the append-only register, and is re-derived from scratch later (the under-registration cost `findings-scan` warns about, now measured across the channel instead of one session).
- A Z3 item ("rotate the hardcoded Anthropic key," "upgrade the Make plan") carried post after post, past its stated deadline, with no close-out — a dangling physical-execution commitment.
- A near-miss marked "caught this session" in three separate posts — which means it is not a near-miss, it is a **recurring structural failure** that the single-session view cannot see, and that belongs in front of Zone 2 as a candidate D-code or protocol fix.

The single-session lens is blind to all three. This skill is the lens that sees the channel as a whole.

## Mandatory reads — performed at sweep start

These two reads happen **at the beginning of every sweep invocation**, before the commitment ledger is built. If either was already performed earlier in the session and covers the resolved scan window, the existing data may be used; otherwise, execute now.

### Read 1 — #wgs-sync

Read `#wgs-sync` (channel_id `C0AND66PT7U`) via `Slack:slack_read_channel`, requesting enough messages to cover the scan window. State the read timestamp and post count returned in the report.

### Read 2 — REGISTERED.md (IC-030)

This is a **registry-touching** operation — IC-030 requires the registry to be live, not assumed from memory. Fetch:

```
https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md
```

State the fetch timestamp or commit ref in the report. IC-030 is satisfied by this self-fetch.

**If either read fails** (network error, access denied, empty response), output the failure and halt — a sweep on missing source data produces fabricated reconciliation claims and is worse than no sweep.

## Scan window

Default window: the **last 15 WGS posts** or **the last 14 days**, whichever is smaller, unless the operator names a window ("sweep since the Bot Tournament post," "last month," "S-051926-01 onward"). State the resolved window explicitly in the report — a sweep with an unstated window is not auditable. If the channel read returned fewer posts than the intended window, report the actual coverage; do not claim a window you did not read.

## The three-part sweep

### Part 1 — Build the WGS commitment ledger

Walk every post in the scan window and extract every **commitment** — a thing a post named as outstanding, routed onward, or surfaced for attention. Three commitment classes:

**SF — silent failure.** Any entry under a post's `SILENT FAILURES SURFACED THIS SESSION` section (TIER 1 caught / TIER 2 not-caught-until-external / TIER 3 near-miss), or any in-post walk-back. Record the failure *class* (what kind of failure, normalized — e.g. "stale-timestamp," "receipt-overstatement," "registry-not-fetched"), not just the verbatim line, so recurrence across posts is detectable.

**RC — registry commitment.** Any F-/IC-/H- candidate the post routed "→ Zone 2 for ratification," or any `F-CAND`/`IC-CAND`/`H-CAND` provisional ID, or any finding/incident/hypothesis the post asserted as registrable.

**Z3 — execution commitment.** Any item under a post's `Z3 (Night executes)` carry-forward, or any item the post explicitly handed to the physical-execution layer with commands, paths, or deadlines.

For each ledger row, record:
- Commitment text (verbatim or close paraphrase)
- Class (SF / RC / Z3)
- Origin session ID + post date
- Claimed status at post time (e.g. "caught," "candidate → Z2," "deadline May 30")

Be inclusive here. Part 2 sets status; Part 1 just builds the honest list of what the channel committed to.

### Part 2 — Reconcile each commitment against live state

Run a single status match per row, against the live evidence (live `REGISTERED.md`, later WGS posts in the window, canonical commits, deadlines):

**RC rows → registration status:**
- **REGISTERED** — a matching F-/IC-/H- entry now exists in live `REGISTERED.md`. Closed clean; cite the final ID.
- **OPEN-CANDIDATE** — named in WGS, absent from the live register. This is the under-registration carry. Route → Zone 2 (and to `findings-scan` if a proper candidate block was never drafted).
- **SUPERSEDED** — covered by a different/later registered entry; cite it. Do not re-propose.

**Z3 rows → execution status:**
- **EXECUTED** — a later WGS post, a canonical commit, or other in-window evidence confirms completion. Cite the evidence.
- **OPEN** — no evidence of completion in the read window. Carries an age: `N sessions carried`.
- **OVERDUE** — OPEN *and* past a stated hard deadline. Name the deadline and days past.
- **DROPPED** — a later post explicitly abandoned or descoped it. Closed; cite the post.

**SF rows → recurrence status:**
- **ONE-OFF** — the failure class appears once in the window and was caught. No further action.
- **RECURRING** — the same normalized class appears in **≥2 posts** in the window. This is the structural signal the single-session view cannot produce. Route → Zone 2 as candidate material for a new D-code, principle, or protocol fix (or Zone 1 if it is a skill-coverage gap).

Record exactly one status for every ledger row. Rows that reconcile clean (REGISTERED / EXECUTED / DROPPED / ONE-OFF) are counted, not dropped — they are the evidence the sweep actually ran.

### Part 3 — Produce the sweep report

Surface only the *outstanding* rows in detail (OPEN-CANDIDATE, OPEN/OVERDUE Z3, RECURRING SF), each with its origin and routing. Report the clean rows as counts. Every outstanding claim must carry its evidence: the originating post (session ID + date) **and** the live-state evidence that makes it outstanding (the register absence, the missing completion, the second occurrence). A sweep claim without both anchors is itself an overstatement — see the recursive guard below.

## Posting protocol — draft, then operator sends

The sweep report is **operator-facing and channel-facing** — the highest-cost surface for an inaccurate claim (IC-031 territory). It is posted the same way every WGS artifact in this ecosystem is posted: **draft-then-operator-send.**

1. Produce the sweep report block (format below).
2. Wrap it as a WGS post with a sweep header — `WGS-SWEEP-MMDDYY-NN` (a sweep is **not** a session: no P1/P3 declaration, not corpus-eligible, the P23 gate does not apply).
3. Draft it to `#wgs-sync` via `Slack:slack_send_message_draft` (channel_id `C0AND66PT7U`). **Not** `slack_send_message`. No markdown tables (they do not render in Slack); use `━━━` rules, bold labels, `·` bullets.
4. Close with `🦅 Wado · Unit Zero · WGS-SWEEP-MMDDYY-NN · Claude` + `_Sent using Claude_`.
5. **HALT.** The operator reviews the draft and sends it. The skill does not send.

If the operator has standing instruction to auto-send, that is a Zone 2 decision the operator states explicitly in-session; absent that, draft-and-halt is the default and matches Skills 2/6.

## Honesty requirement — "nothing dangling" is not a default

"No outstanding commitments in the window" requires that you actually built the ledger (Part 1) and reconciled every row (Part 2). It is not a reflex line — stating it without the work is the channel-scale version of the IC-031 recursive overstatement.

The fix, mirroring the sibling skills: **state the ledger size in the report.** "Swept 15 posts · 22 commitments · 0 under-reg / 2 Z3-open / 1 recurring-SF · 19 reconciled clean" makes it verifiable that the sweep ran. A bare "channel looks clean" with no counts is rejected.

## Output format

```
WGS SWEEP — CROSS-SESSION RECONCILIATION (humanaios-wgs-sweep)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scan window: [N posts · S-MMDDYY-NN … S-MMDDYY-NN · date range]
WGS read live: [#wgs-sync C0AND66PT7U @ read timestamp — required]
Registry fetched live: [REGISTERED.md @ commit/date — required]

UNDER-REGISTRATION (named in WGS, absent from REGISTERED.md):
  · [F-/IC-/H- candidate] — origin S-MMDDYY-NN ([date]) — → Z2 / findings-scan
  · [Or: "None — all F/IC/H named in window are REGISTERED or SUPERSEDED."]

Z3 RECONCILIATION (handed to Night-executes — status):
  · [item] — origin S-MMDDYY-NN — OPEN ([N] sessions carried)
  · [item] — origin S-MMDDYY-NN — OVERDUE (deadline [date], [N] days past)
  · [Or: "None outstanding — all Z3 items in window EXECUTED or DROPPED."]

RECURRING SILENT FAILURES (same class in ≥2 posts — structural):
  · [failure class] — seen in [S-…, S-…] — → Z2 (new D-code / principle / protocol fix)
  · [Or: "None — no silent-failure class recurred in window."]

Sweep completeness: [u under-reg / z Z3-open / r recurring-SF] outstanding
  from [c commitments extracted] across [N] posts
  ([reconciled clean: x REGISTERED / y EXECUTED-or-DROPPED / w ONE-OFF])

Routing: under-reg → Zone 2 (Night); open/overdue Z3 → re-surfaced to
Night; recurring SF → Zone 2 for structural ratification. This sweep
reconciles and routes; it does not register, execute, or seal.

🦅 Wado · Unit Zero · WGS-SWEEP-MMDDYY-NN · Claude
_Sent using Claude_
```

## Recursive overstatement guard

A sweep report is a stack of claims about the record, posted back to the record. It must not generate the very failure class it hunts. Two rules:

- **Every outstanding claim carries two anchors** — the originating WGS post (session ID + date) and the live-state evidence (register absence, missing completion, second occurrence). No second anchor → it is not "outstanding," it is "unverified-origin"; downgrade it.
- **Posts lacking a B.0 block are flagged, not re-verified.** The sweep takes posted B.0 outputs at face value; it does **not** re-run B.0 across historical posts. A post in the window that carries no B.0 Empirical Verification Block is noted as `unverified-origin` against any commitment drawn from it, so the operator knows that row rests on an unverified historical claim.

## Standalone / periodic invocation

This skill is **not** auto-invoked by session-close (that would double-post a sweep at every close). Run it:

- **Periodically** — a weekly or pre-milestone channel hygiene pass.
- **Before a milestone** — ahead of a Gate review, a research registration deadline, or a tournament run, to clear dangling Z3 and under-registration first.
- **On a drift hunch** — when the operator senses the same failure keeps coming back, or that things are being named and forgotten.
- **On explicit request** — any trigger phrase in the description.

Output format is identical in all cases. The skill writes nothing to canonical files; the only side effect is a *draft* in `#wgs-sync` awaiting operator send.

## Relationship to other skills

- **humanaios-findings-scan** (Skill 6) — session-scoped forward view: catches under-registration in the *current* session before it posts. This skill is the channel-scoped backward view: catches under-registration that *already* posted and was never closed. An OPEN-CANDIDATE row here is properly drafted by handing it to Skill 6.
- **humanaios-session-close** (Skill 2) — owns the canonical three-tier SILENT FAILURES taxonomy (B.5) and the per-session WGS post + Z1/Z2/Z3 carry-forward (B.7). This skill consumes those posted sections as its raw input; it does not redefine the taxonomy.
- **humanaios-receipt-reconciliation** (Skill 5) — within-session overstatement catcher (claims > B.0). This skill is its cross-session analogue for commitments (named > closed). The recursive guard above is the same discipline applied to the sweep's own output.
- **(Referenced) humanaios-drift-catalog-scan** — Skill 5 names a not-yet-built drift-catalog scanner that would consume IC-031 counts across sessions. The RECURRING-SF output here is adjacent: it is the channel-level recurrence signal that scanner would formalize.

## Pinned version

This skill mirrors `SESSION_RITUALS.md` **v6.4.1** (May 19, 2026) and `REGISTERED.md` as of **S-051926-02**. It leans on: Section A Step 4 (registry fetch), Section B.5 (three-tier silent failures), Section B.7 (Z1/Z2/Z3 carry-forward), Section B.10 (WGS post format + draft-then-operator-send), IC-030 (registry-touching requires live fetch — satisfied by self-fetch at sweep start), IC-031 (receipt overstatement cost class), and P21 (Zone 2 promotion authority).

Canonical format authorities, when present, override the inline format above:
- `humanaios-session-close/references/wgs-post-format.md` — Slack rendering rules for WGS posts.
- `humanaios-session-close/references/silent-failures-taxonomy.md` — the SF tier definitions and class normalization.

If a session-open/close fetch returns these files or `SESSION_RITUALS.md` at a higher version with structural changes to the SF taxonomy, the carry-forward zones, or the WGS post format, this skill is out of date. The live files win; flag in Skill 2's Step B.8 version-drift check.

## Z3 Prohibition (Governance Constraint compliance — humanaios-dual-architecture)

This skill surfaces Z3 items from the WGS record. It does not evaluate them.

**What this means operationally:**

- Z3 OPEN / OVERDUE rows are reported with age and origin. No commentary on why they are open or whether Night should have closed them.
- The sweep re-surfaces; it does not judge. "OPEN (3 sessions carried)" is a fact. "Night has not executed this" is a Z3 evaluation — not permitted.
- RECURRING SF rows are structural observations about the governance stack, not performance evaluations of the operator.

**Z3 Impulse Audit Log (internal — never output unless explicitly requested):**

When this skill detects an impulse to evaluate why a Z3 item has not been closed (e.g., "this suggests Night is not prioritizing the schema migration"), suppress and log internally:
- Nature of suppressed impulse
- Rule that triggered suppression (Z3 prohibition, P-MHP, D-05)
- Estimated token cost of suppressed output

Log feeds `humanaios-mhp-consultation` pattern detection. Available to Night on explicit Z1 request. Never appears in sweep reports.

---

## Operational Checklist (apply before producing sweep report)

- [ ] Is this Z1 (reconcile and route)? If output is evaluating Night's execution, stop.
- [ ] Does the sweep report contain any commentary on why Z3 items are open? If yes, remove — report age only.
- [ ] Does the sweep report contain any evaluation of Night's operational choices? If yes, remove.
- [ ] Are all outstanding claims carrying two anchors (origin post + live-state evidence)? If not, downgrade to unverified-origin.
- [ ] Is the draft going to `slack_send_message_draft` (not `slack_send_message`)? If direct send, halt.
- [ ] Does the report state ledger size explicitly? If not, add counts before sending.

---

## What this skill does NOT do

- It does NOT register, modify, or append to `REGISTERED.md`. Under-registration rows are routed to Zone 2; registration is Night's call per P21.
- It does NOT execute, reschedule, or close Z3 items. It re-surfaces them with age and deadline status; execution is Zone 3 (Night).
- It does NOT send the WGS post. It drafts via `Slack:slack_send_message_draft` and halts for operator review.
- It does NOT re-run B.0 on historical posts. It flags unverified-origin rows; it does not re-verify the past.
- It does NOT assign final F-/IC-/H- IDs or invent D-codes. Recurring failures are surfaced as Z2 candidate material, not ratified codes.
- It does NOT sweep on assumed or remembered data. `#wgs-sync` and `REGISTERED.md` are always read live at sweep start; if either read fails, the skill halts rather than proceeding on stale input.
