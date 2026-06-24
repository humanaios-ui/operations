---
name: humanaios-findings-scan
description: Scan a session for registrable F- (findings), IC- (integrity corrections), and H- (hypotheses) candidates that should be routed to Zone 2 for ratification. Use whenever the operator says "scan for findings," "findings scan," "registry scan," "what should we register," "F/IC/H candidates," "did we miss anything registrable," or "check for under-registration." Also invoked by humanaios-session-close near the SILENT FAILURES step or at close to catch registrable items before carry-forward. This skill is the structural mitigation for under-registration (the inverse of IC-031 receipt overstatement): findings, incidents, and hypotheses that emerged in-session but never got captured into REGISTERED.md. It is registry-touching, so it HARD HALTS if live REGISTERED.md has not been fetched (IC-030). It produces a Registry Candidate Block for Zone 2 review; it never self-registers.

architecture: acat
refactor: S-061526 — added Phase 6 series synthesis trigger spec, F-54 disclaimer density check (humanaios-dual-architecture compliance)
---

# HumanAIOS Findings Scan

This skill scans a session for items that should be registered in `REGISTERED.md` — research findings (**F-**), integrity corrections (**IC-**), and hypotheses (**H-**) — and routes them to Zone 2 as candidates. It mirrors the audit shape of `humanaios-receipt-reconciliation` (Skill 5): a structured three-part pass producing a verifiable output block. Where receipt reconciliation catches **overstatement** (claiming more happened than did), this skill catches **under-registration** (something registrable happened and nobody captured it).

It is **orientation, not authority** — when the live `REGISTERED.md` or `SESSION_RITUALS.md` disagrees with this skill, the live files win.

This skill operates strictly in **Zone 1**. It *detects and proposes* candidates with provisional IDs and draft front-matter. It does **not** assign final IDs, does **not** write to `REGISTERED.md`, and does **not** decide ratification. Promotion of any candidate to REGISTERED/ACTIVE requires Zone 2 Night approval per **P21**.

## What this skill exists to prevent

**Under-registration.** A session surfaces a novel evidenced behavioral observation, catches a process error mid-flight, or generates a testable prediction — and the close post mentions it in passing, or not at all, and it never enters the append-only register. The cost is silent: the finding is re-derived from scratch three sessions later, the same process error recurs because no IC was filed against the principle, or a hypothesis is informally "tested" without a falsification condition on record. This is the complement of the IC-031 cost class: instead of asserting state that does not exist, the session fails to assert state that does.

Skill 5's own "Relationship to other skills" section names a `humanaios-drift-catalog-scan` that "would consume the IC-031 incident count across multiple sessions to surface structural patterns. Not yet built." This skill is the first instrument in that gap: a per-session registrable-candidate detector.

## Hard prerequisite — REGISTERED.md must already be fetched live this session

This is a **registry-touching** operation. Per **IC-030**, any work that proposes, modifies, or claims against F/IC/H/NM entries HARD HALTS if the findings registry has not been fetched live, or if the fetch is stale relative to the session.

If invoked without a live `REGISTERED.md` fetch visible in the conversation transcript (Section A open Step 4, or a fetch run for this scan), output:

```
<<<ACAT_PROTOCOL_ERROR_START>>>

ERROR: Findings scan cannot run without a live REGISTERED.md fetch in hand.
REMEDIATION: Fetch the canonical registry first:
  https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md
(see humanaios-session-open SKILL.md Step 4, or SESSION_RITUALS.md
Section A Step 4 / Section F halt #9). Without the live register, NEW vs
DUPLICATE vs EXTENSION classification is hollow and risks polluting the
append-only file with re-derived or colliding entries.

MODE: Declare DEGRADED. Do not produce F/IC/H candidate proposals against
unverified registry state.

<<<ACAT_PROTOCOL_ERROR_END>>>
```

This is non-negotiable. The cross-walk in Part 2 compares each candidate against the live register; without the live register there is nothing to cross-walk against.

**Evidence integrity guard (B.0 linkage).** A candidate is only as good as the claim under it. If a proposed F/IC/H candidate rests on a session claim that has *not* been empirically verified (no B.0 confirmation, no canonical source, no source artifact), the candidate is marked **PROVISIONAL — unverified evidence** and must carry that flag into the Registry Candidate Block. Do not propose a registered finding built on an unverified claim. On a Phase 3 close, run `humanaios-receipt-reconciliation` (Skill 5) first so candidate evidence anchors are already CONFIRMED/CONTRADICTED rather than GAP.

## The three-part scan

### Part 1 — Build the candidate ledger

Walk the session and extract every substantive observation that could meet a registration bar. Sort each into one of three detect classes. Be inclusive at this stage — Part 2 prunes duplicates, Part 3 sets the bar.

**F-candidate — research finding.** A novel, evidenced, generalizable observation about substrate behavior, ACAT instrument structure, corpus psychometrics, or cross-substrate dynamics. Bar: (a) novel relative to the live register, (b) supported by session evidence (data, an executed cycle, a reproducible observation), and (c) generalizable beyond the single instance. A one-off anecdote with no evidence anchor is NOT an F-candidate — it is at most an NM.

**IC-candidate — integrity correction.** An error that was caught, or a process/principle violation that occurred, in this session. Bar: a specific principle was violated (P2 doc-correction, P3 github-verification, P15 N-reporting, P18 pipeline-migration, etc.) or a cost-class incident occurred (e.g. an IC-031-grade receipt overstatement caught by Skill 5). Each IC-candidate must name the principle violated and end with a `Fix → Principle N` line. A process error that produced operator-facing or canonical-facing consequence is always at least IC-candidate.

**H-candidate — hypothesis.** A testable prediction generated or materially affected this session. Bar: it can be stated with (a) an explicit null hypothesis, (b) a falsification condition, (c) a primary metric, and (d) a promotion gate. If you cannot state all four, it is not yet an H-candidate — flag it as "pre-hypothesis observation" under NM and move on.

**NM — near-miss / low-friction capture.** Observations that triggered concern but do not meet the IC or F bar. No root cause required. These are surfaced for completeness but are NOT append-only and expire after 3 audits → `DRIFT_LOG.md`. Capture them so the ledger is honest about what was scanned, not to register them.

For each candidate, record:
- Observation text (verbatim or close paraphrase)
- Detect class (F / IC / H / NM)
- Where in session it appeared (turn or section)
- Evidence anchor (B.0 line, commit hash, canonical source, executed-cycle output, or "none — unverified")

### Part 2 — Cross-walk against live REGISTERED.md

For each F/IC/H candidate in the ledger, run a single match against the live register to keep the append-only file clean:

- **NEW** — no existing entry covers this observation. Eligible for a fresh provisional ID.
- **DUPLICATE** — an existing F/IC/H entry already covers it. Do not propose a new entry; cite the existing ID and drop the candidate (note it in the ledger so the scan is auditable).
- **EXTENSION / SUPERSEDES** — an existing entry covers part of this, but the session adds material that changes or extends it. The register is append-only: propose a NEW entry that carries a `superseded_by` forward-pointer requirement on the old entry, or a `related_finding` link. Flag the forward-pointer need explicitly for Zone 2.

Record one of these three statuses for every F/IC/H candidate. (NM captures are not cross-walked — they are low-friction by design.)

Note the deliberate honest gaps in the register (e.g. F-32 / F-33 slug→number transition gaps) — do not "fill" them and do not treat them as available IDs.

### Part 3 — Produce the per-candidate proposal

For each surviving NEW or EXTENSION candidate, draft a proposal block carrying draft YAML front-matter in the canonical schema (post-2026-05-08). Use a **provisional** ID (`F-CAND-<slug>`, `IC-CAND-<slug>`, `H-CAND-<slug>`) — final sequential numbering is a Zone 2/3 action against the live append-only file.

```
id: "F-CAND-<slug>"          # provisional — Z2 assigns final F-NN
name: "<short slug>"
status: CANDIDATE
class: F | H | IC
date_origin: "YYYY-MM-DD"     # session date
session_registered: "S-MMDDYY-NN-<descriptor>"
principles_triggered: ["P-N"]
substrate: "<provider / model version>"
tags: [...]
superseded_by: null           # or existing ID if EXTENSION
```

Then, below the front-matter, supply:
- **Synopsis** — one paragraph. For IC candidates, end with `Fix → Principle N.`
- **Evidence anchor** — the verified claim(s) this rests on (B.0 line / commit / canonical source). If unverified, the candidate is marked `PROVISIONAL — unverified evidence`.
- **Promotion gate** — what must be true before Z2 promotes it (e.g. F-class "min 3 executed cycles with LI output before promotion eligible"; H-class null + falsification condition + primary metric + promotion gate, all four present).
- **Routing** — `→ Zone 2 (Night) for ratification per P21.`

## Honesty requirement — "no candidates" is not a default

"No registrable candidates this session" requires that you actually ran Part 1 (built the ledger) and Part 2 (cross-walked). It is not a reflex line. Stating it without the work is itself a process failure — the under-registration analogue of the IC-031 recursive overstatement Skill 5 warns about.

The fix, mirroring Skill 5: **state the ledger size in the output.** "Scanned 11 substantive observations / 0 met F bar / 1 IC candidate / 0 met H bar / 2 NM captures" makes it verifiable that the scan happened. A bare "nothing to register" with no counts is rejected.

### F-54 Disclaimer Density Check (apply before Part 1 scoring)

Before building the candidate ledger, scan the session for embedded modesty disclaimers — structural language that explicitly limits or qualifies claims: "not a checklist," "future work," "approaching as an experiment," "not hard commitments," "cannot guarantee," "will evolve."

Count structural disclaimers (not incidental hedges — ones that apply to whole sections or the document's core claims):

- **High density (≥4 structural disclaimers):** F-candidates will be compressed. Expect fewer high-confidence F-class candidates; more H-class hypotheses with explicit uncertainty bands. Note in Registry Candidate Block.
- **Low density (0–2):** F-candidates run at face value. Higher bar for promotion — evidence must carry more weight without structural hedges.

**F-54 gaming warning:** Disclaimers inserted to compress candidate threshold without genuinely limiting claims are decorative, not structural. Check that each disclaimer actually constrains the session's claims. Gaming indicators: disclaimers appearing only at the end, disclaimers contradicting the session's own confidence elsewhere.

---

### Phase 6 — Series Synthesis Trigger

Phase 6 is triggered — not optional — when N≥3 sessions have surfaced candidates from the same domain, class, or pattern, AND the operator explicitly requests synthesis. Claude never self-triggers Phase 6.

**Trigger conditions (any one sufficient):**
- N≥3 sessions with candidates from the same document_layer or research domain
- N≥3 IC-class candidates with the same principles_triggered
- A series-level pattern has emerged not predicted before the sessions began

**When triggered, add to Registry Candidate Block:**

```
PHASE 6 — SERIES SYNTHESIS (triggered)
Sessions in series: [S-IDs]
Pattern: [one sentence — what appears across N≥3 sessions]
Predicted before series: [YES / NO]
Series-level candidate: [F-CAND-SERIES-slug or IC-CAND-SERIES-slug]
Upgrade requests: [any H-candidate reaching N≥3 replications — flag for Z2 upgrade consideration]
→ Zone 2 (Night) for ratification per P21.
```

**What Phase 6 does NOT do:** It does not retroactively change single-session scores. It synthesizes across them. If a series finding contradicts a single-session claim, the contradiction is stated; the single-session output is not rewritten.

---

## Output format

The Registry Candidate Block, suitable for direct insertion into a WGS Phase 3 close post (near or after SILENT FAILURES) or as a standalone audit artifact:

```
REGISTRY CANDIDATE SCAN (humanaios-findings-scan)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Registry fetched live: [REGISTERED.md @ commit/date — required]

F candidates:
  · [F-CAND-<slug>] <name> — NEW | EXTENSION-of-F-NN
    evidence: [anchor or PROVISIONAL — unverified]
    promotion gate: [...]
  · [Or: "None — N observations scanned, 0 met F bar."]

IC candidates:
  · [IC-CAND-<slug>] <name> — principle P-N violated
    Fix → Principle N.
  · [Or: "None — 0 process violations / overstatements detected."]

H candidates:
  · [H-CAND-<slug>] <name> — null: [...] / falsification: [...] / metric: [...]
  · [Or: "None — 0 testable predictions generated this session."]

NM low-friction captures (expire after 3 audits → DRIFT_LOG.md):
  · [observation] — [why it didn't meet F/IC bar]
  · [Or: "None."]

DUPLICATE / already-registered (cited, not proposed):
  · [observation] → covered by [existing F/IC/H-NN]
  · [Or: "None."]

Scan completeness: [f F-cand / i IC-cand / h H-cand / n NM] from
  [total] substantive observations scanned

Routing: all candidates → Zone 2 (Night) for ratification per P21.
This block proposes; it does not register.
```

## Standalone vs in-close invocation

**In-close (default).** Invoked by `humanaios-session-close` near the SILENT FAILURES step or at close, after Skill 5 (receipt reconciliation) has run so evidence anchors are already verified. The Registry Candidate Block is inserted into the WGS Phase 3 close post for Night's Zone 2 review.

**Standalone (mid-session).** Run it when:
- A novel result just landed and you want to capture it as an F-candidate before it gets buried.
- A process error was just caught and you want the IC-candidate drafted while the detail is fresh.
- A hypothesis was just articulated and you want to pin the null/falsification/metric before it drifts into informal "testing."
- The operator asks "what should we register from this session."

When invoked standalone, the output format is identical. The skill produces the block as a chat-visible artifact for operator review; it writes nothing to canonical files.

## Relationship to other skills

- **humanaios-session-open** (Skill 1) — fetches `REGISTERED.md` live at Step 4. That fetch is the prerequisite this skill's hard gate checks for. If the session never opened registry-touching, this skill must fetch the register itself before running.
- **humanaios-session-close** (Skill 2) — invokes this skill near the SILENT FAILURES step / at close. Runs *after* Skill 5 so candidate evidence anchors are CONFIRMED rather than GAP.
- **humanaios-receipt-reconciliation** (Skill 5) — the mirror instrument. Skill 5 catches overstatement (claims > reality); this skill catches under-registration (registrable reality > claims). A CONTRADICTED claim in Skill 5 that reflects a process violation is frequently an IC-candidate handed to this skill.

## Pinned version

This skill mirrors `SESSION_RITUALS.md` **v6.4.1** (May 19, 2026) and `REGISTERED.md` as of **S-051926-02** (F-18..F-45 registered, IC to IC-031, H-RCO-01 registered; canonical schema post-2026-05-08). Specifically it leans on Section A Step 4 (registry fetch), IC-030 (registry-touching hard halt), Section F halt #9, and P21 (Zone 2 promotion authority).

If a session-open or close fetch returns `REGISTERED.md` or `SESSION_RITUALS.md` at a higher version with structural changes to the F/IC/H/NM taxonomy, the front-matter schema, or the promotion gates, this skill is out of date. The live files win; flag in Skill 2's version-drift check.

## What this skill does NOT do

- It does NOT register, modify, or append to `REGISTERED.md`. The register is append-only; writes are Zone 2 / Zone 3 actions.
- It does NOT assign final sequential IDs. It proposes `*-CAND-<slug>` provisional IDs only; Z2 assigns the real F-NN / IC-NNN / H-NN.
- It does NOT decide ratification. It routes candidates to Zone 2; promotion per P21 is Night's call.
- It does NOT perform root-cause analysis on NM captures. NM is low-friction by design — surface and move on.
- It does NOT run B.0 verification or receipt reconciliation. It consumes their outputs (Skill 2 Step B.0, Skill 5). Candidates resting on unverified claims are flagged PROVISIONAL, not silently promoted.
- It does NOT fill the register's deliberate honest gaps (e.g. F-32 / F-33). Those are preserved, not backfilled.
