# HumanAIOS Z3 Execution Protocol

**Status:** LIVE
**Version:** 1.1
**Last updated:** May 1, 2026 (S-050126 · pre-publication audit fixes)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/Z3_PROTOCOL.md`
**Scope:** Applies to every terminal/operator session that executes Z3-class actions — file commits, git pushes, key rotation, grant submissions, Cloudflare changes, deployments, any action only Night executes per Zone definitions in GOVERNANCE.md.
**Authority:** This file is the canonical execution standard for Zone 3 sessions. When a Z2 authority document specifies "what to change," this file specifies "how to execute the change." If a Z2 document conflicts with this protocol on procedural matters: this protocol wins. If it conflicts on substantive matters (what should be done): the Z2 document wins.

---

## Section A — When this protocol applies

Triggered by any of:

- [ ] A Z2 authority document with a "files affected" or "execution sequence" matrix
- [ ] An explicit Z3 item on a session priority list (W-1, W-2, B1, C-2, etc.)
- [ ] A `decision_made` event ratified Z2 that requires a file/repo/external-system change
- [ ] Key rotation, credential change, or any security-sensitive operation
- [ ] Production deployment of code, schema, or content
- [ ] Grant submission, financial transaction, or external-platform action

NOT triggered by:

- Z1 chat work (Claude generating drafts, analyses, reports — no commit, no push, no external call)
- Reading or fetching public URLs
- Running synthetic tests in a sandbox schema or scratch repo
- Z2 deliberation in chat

---

## Section B — Pre-flight (before opening terminal)

Run this checklist BEFORE any command is typed in terminal. If any item fails, halt and resolve before proceeding.

- [ ] **B-1 · Authority document loaded.** Open the Z2 authority document driving this session (e.g. `S-042928_OPERATIONS_REPORT.md`). If no such document exists for the planned actions, halt — Z3 work without a Z2 authority document is unauthorized.
- [ ] **B-2 · Files-affected matrix extracted.** Copy the "files affected" / "execution sequence" matrix from the authority document into a scratch buffer (text file, sticky note, anywhere visible during the session). This becomes the working checklist.
- [ ] **B-3 · Session ID assigned.** Determine session ID for this Z3 session (e.g. `S-042928-Z3-COMMIT`). Will be used in commit messages and the verification ledger.
- [ ] **B-4 · Time confirmed.** Note the actual clock time at session open. If `user_time_v0` is unavailable, get time from system clock or phone. Required for WGS post and verification ledger.
- [ ] **B-5 · Repo location confirmed.** Run `pwd` and confirm the path matches the expected repository for the first file change. Common locations:
   - `~/Desktop/HAIOS-Main/lasting-light-ai/` → `humanaios-ui/lasting-light-ai`
   - `~/Desktop/HAIOS-Main/HAIOSCC/` → `LastingLightAI/HAIOSCC` (cross-org intentional per IC-023)
   - `~/Desktop/HAIOS-Main/operations-staging/` → `humanaios-ui/operations`
   - `~/Desktop/HAIOS-Main/humanaios-internal/` → `humanaios-ui/humanaios-internal` (private)
- [ ] **B-6 · Branch confirmed.** Run `git branch --show-current` and confirm `main` (or the explicit branch named in the authority document).
- [ ] **B-7 · Working tree clean.** Run `git status`. If uncommitted changes exist that are NOT part of this session's planned work, halt — stash, commit elsewhere, or resolve before proceeding. Mixing unrelated changes into a Z3 commit is a discipline violation.
- [ ] **B-8 · Remote synced.** Run `git fetch origin && git status -sb`. Confirm local is not behind remote. If behind, `git pull --ff-only` before proceeding.
- [ ] **B-9 · Credentials staged correctly.** Confirm any tokens/keys needed are in macOS Keychain (or the chosen secure store). Standing security hygiene: NEVER paste credentials into chat or terminal output that will be screenshotted. NEVER use Apple Notes for credential storage. If a credential needs to be regenerated, regenerate via the platform's web UI rather than diagnosing in chat.
- [ ] **B-10 · No credentials in clipboard.** Clear clipboard of any prior credential content before proceeding.

If all 10 boxes check, proceed to Section C. If any fails, halt and resolve.

---

## Section C — Execution discipline

The execution rules. These are non-negotiable.

### C-1 · One file at a time

Edit → save → diff → stage → commit. Per file. Not batched. Exception: paired files where the change must be atomic (e.g. a schema rename across `01_events_table_schema.sql` and `02_reliability_flag_triggers.sql` where the search_path references must match) — those land in a single commit but the diff is reviewed file-by-file before staging.

### C-2 · Diff before staging

Before `git add`, always run `git diff <file>`. Read the diff. Confirm it matches the intent in the authority document. If the diff includes anything not authorized (a stray edit, an IDE auto-format, a smart-quote substitution), reset that file and re-edit cleanly.

### C-3 · Commit message standard

Every Z3 commit message references the authority document and the section that ratified the change. Format:

```
<verb> <subject> per <AUTHORITY_DOC> §<section>

Examples:
- Rename schema haios_events_test → haios per S-042928_OPERATIONS_REPORT §1.1
- Add P24 (Temporal Trigger Ordering) per S-042928_OPERATIONS_REPORT §2.1
- Append F33 entry per S-042928_OPERATIONS_REPORT §3.2
```

No emoji in commit messages. No "fix stuff." No commit messages without the `per <AUTHORITY_DOC> §<n>` reference. The reference is what makes future sessions traceable.

### C-4 · Push immediately after commit

Do not batch commits and push at end of session. Each commit pushes immediately. This minimizes the risk of losing work and produces a clean P3 verification window per file.

### C-5 · Verify before next file

After `git push`, run the P3 verification (Section D) for that file BEFORE moving to the next file. Browser cache does not count as verification. Failure on any file halts the session — see Section F.

### C-6 · No silent edits to other files

If during execution you discover a related file that needs an edit not in the authority document, STOP. Do not edit it. Surface it as a Z2 question for the next session. Editing files outside the authority document's matrix during a Z3 session is the highest-frequency drift pattern and is the root cause of multiple IC-class corrections.

### C-7 · Source-first when something looks wrong

If a file's contents on disk don't match what you expect, do NOT diagnose from memory. Open the file. Read the actual bytes. Per P17 (Source-First Debug). Browser caches lie. IDE caches lie. Memory of "what the file used to say" lies. Only the bytes on disk are authoritative.

---

## Section D — P3 verification (per-file, mandatory)

After every `git push`, perform P3 verification. This is the codification of CI principle P3 (GitHub Verification).

### D-1 · Refetch the raw URL

```bash
curl -sS https://raw.githubusercontent.com/<org>/<repo>/main/<filename> | <verification grep>
```

Substitute `<org>`, `<repo>`, `<filename>` for the actual values. Substitute `<verification grep>` for a grep that confirms the change landed (e.g. `grep "P24"` after adding P24 to GOVERNANCE.md, or `grep "F33"` after appending F33 to REGISTERED.md).

### D-2 · Wait for cache propagation if needed

GitHub raw URLs typically refresh within seconds, but can lag up to ~30s. If the first refetch doesn't show the change, wait 15s and retry. Not 5 minutes — if the change isn't visible after 60s, something is wrong (wrong branch, push failed, etc.).

### D-3 · Browser is not verification

Loading the GitHub web UI in a browser tab and seeing the change is NOT P3 verification. Browser pages are cached aggressively. Only the raw URL fetched via `curl` (or equivalent non-cached HTTP client) counts.

### D-4 · Log the verification

For each file verified, append to the session's verification ledger (Section E format) immediately. Don't batch. Don't trust memory. Write it down as it happens.

### D-5 · Common verification greps

| Action | Grep pattern |
|---|---|
| Added a new principle to GOVERNANCE.md | `grep -A1 "^\*\*P<n>"` |
| Appended a finding to REGISTERED.md | `grep "^### F<n>"` |
| Renamed a schema in SQL | `grep -c "haios_events_test"` (expect 0) and `grep -c "haios"` (expect >0) |
| Updated a version number | `grep "Version:.*v6\.1"` |
| Added a file | `curl -sS <url> -o /dev/null -w "%{http_code}"` (expect 200) |
| Removed a file | same as above (expect 404) |

---

## Section E — Verification ledger format

Every Z3 session produces a verification ledger. Single text block, plain text, appended to as the session progresses. Format:

```
═══════════════════════════════════════════════════════════════════════════
Z3 VERIFICATION LEDGER · S-<sessionID>
Opened: <timestamp at session start>
Authority document: <filename>
═══════════════════════════════════════════════════════════════════════════

[1] FILE: <repo>/<filename>
    CHANGE: <one line summary>
    AUTHORITY: <authority doc> §<section>
    COMMIT: <hash>
    PUSHED: <timestamp>
    VERIFIED: <timestamp> · curl <url> · grep "<pattern>" → <result>
    STATUS: ✓ PASS

[2] FILE: <repo>/<filename>
    CHANGE: <one line summary>
    AUTHORITY: <authority doc> §<section>
    COMMIT: <hash>
    PUSHED: <timestamp>
    VERIFIED: <timestamp> · curl <url> · grep "<pattern>" → <result>
    STATUS: ✓ PASS

...

═══════════════════════════════════════════════════════════════════════════
SESSION CLOSE
Closed: <timestamp at session close>
Total files changed: <n>
Total commits: <n>
Total verifications passed: <n>
Verifications failed: <n> (see Section F log if >0)
═══════════════════════════════════════════════════════════════════════════
```

The ledger is the artifact that proves the session happened correctly. Paste it into the WGS log post (Section G). Save a copy locally if useful.

---

## Section F — Failure protocol

If P3 verification fails on any file, halt the session. Do not proceed to the next file.

### F-1 · Diagnose

Run these in order until the cause is found:

- [ ] Re-run the curl 30 seconds later — was it propagation lag?
- [ ] Run `git log --oneline -5` — did the commit actually land?
- [ ] Run `git status` — is there an uncommitted change still in the working tree?
- [ ] Run `git push` again — did the push silently fail?
- [ ] Check the GitHub web UI for the repo's recent commits — is yours there?
- [ ] Open the raw URL in an incognito browser tab — does it show the change?

### F-2 · Decide: revert or fix-forward

- **Revert** if the diagnosis shows the change landed wrong (e.g. wrong content, malformed, breaks downstream). Run:
  ```bash
  git revert <hash>
  git push
  ```
  Then re-verify the revert (Section D) before continuing.

- **Fix-forward** if the diagnosis shows the change is correct but verification was wrong (e.g. typo in grep pattern, looking at wrong URL). Update the verification, re-run, log the corrected verification.

### F-3 · Log the failure

Add to the verification ledger immediately:

```
[<n>] FAILURE: <repo>/<filename>
    DIAGNOSIS: <what was wrong>
    RESOLUTION: <revert / fix-forward / abandoned>
    RE-VERIFIED: <timestamp> · <result>
    STATUS: ✗ FAILURE → <RESOLVED | OPEN>
```

### F-4 · Surface as IC if pattern repeats

If the same class of failure happens twice in one session, halt and file an IC entry per CI v6.0 IC convention. The session does NOT continue with more file changes — the IC is the next priority. Continuing past a repeat-failure is itself a drift signal (D-02, repeat diagnosis).

---

## Section G — Session close

When all files in the authority document's matrix are committed AND verified, close the session with these steps in order.

- [ ] **G-1 · Verify the verification.** Re-read the verification ledger top-to-bottom. Confirm every file in the authority document's matrix has a corresponding ledger entry with STATUS: ✓ PASS.
- [ ] **G-2 · Close items in HAIOSCC.** For each Z3 item from the next-session priority list that this session closed, mark closed in HAIOSCC. Per Zone definitions, only Night closes Z3 items.
- [ ] **G-3 · Compose WGS log post.** Use the template in Section H. The verification ledger is the body.
- [ ] **G-4 · Post to #wgs-sync.** Single post, complete content. Add timestamp at post time.
- [ ] **G-5 · Update authority document if needed.** If the authority document had a "Status" or "Open items" section that this session resolved, edit those lines to reflect the new status. Commit and push (this is itself a Z3 file change subject to D-1 verification).
- [ ] **G-6 · Stash credentials.** If any tokens were used during the session, confirm they remain only in Keychain. Clear shell history if it captured any credential material (`history -c` in zsh).
- [ ] **G-7 · Note carry-forward.** Items from the authority document NOT closed this session carry to the next session. Name them explicitly in the WGS post.

---

## Section H — WGS log post template (Z3 sessions)

```
:clipboard: WGS Z3 EXECUTION LOG · S-<sessionID>
<DATE> · <TIME CDT>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Authority document: <filename>
Files changed: <n>
Verifications passed: <n>/<n>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORK COMPLETED

<paste verification ledger from Section E>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Z3 ITEMS CLOSED THIS SESSION
• <item> per <authority §section>
• <item> per <authority §section>

CARRY-FORWARD (not closed this session)
• <item> — reason: <why deferred>

NEXT SESSION FOCUS
• <next priority>

:eagle: Wado · Unit Zero · S-<sessionID>-Z3 · Night
```

---

## Section I — Standing caveats

These hold for every Z3 session, no exceptions.

- **No credentials in chat.** Tokens, API keys, passwords never appear in chat with any LLM, ever. If a credential needs to be regenerated, regenerate it via the platform's web UI. Pasting `echo $TOKEN` output into chat for "diagnosis" is the failure mode this caveat exists to prevent.
- **No `\echo` or psql meta-commands in committed SQL.** SQL files committed to operations must run cleanly in the Supabase SQL Editor and `execute_sql` MCP tool. Backslash-prefixed psql meta-commands are not supported by either runner. Use `RAISE NOTICE` inside `DO $$ ... END $$;` blocks for human-readable banner output instead.
- **No same-transaction `<` predicates on `recorded_at`.** Per P24 (Temporal Trigger Ordering, GOVERNANCE.md). Any deterministic trigger ordering events by `NOW()`-populated timestamps must use `<=` with `event_id <> NEW.event_id` exclusion.
- **No `WITH CHECK (true)` policies in committed migrations.** The five tables in `public` schema with this pattern (acat_assessments_v1, acat_research_hub_v1, assessments, experiments, music_hall_submissions, transmissions) are documented anti-patterns. New migrations must use shape-constrained policies.
- **No SECURITY DEFINER views without explicit Z2 ratification.** Three exist in `public` schema (model_leaderboard, acat_assessments_v1_verified, acat_assessments_v1_unified) — those are pre-existing and pending cleanup. New views default to `WITH (security_invoker = true)`.

---

## Section J — Halt conditions (Z3-specific)

Stop the session and ask Night before proceeding if any of:

1. The authority document does not specify a file you would need to edit to complete the work
2. A diff includes content not authorized by the authority document
3. Verification fails twice for any single file
4. A credential ends up in chat or terminal output by accident
5. The repo's `main` branch has commits from another author since session open (someone else pushed mid-session)
6. A push is rejected (force-push protection, branch protection, etc.)
7. Running the proposed change would affect a row count, schema object, or external system in a way not anticipated by the authority document
8. The actual file contents on disk do not match what the authority document assumed

---

## Section K — Verification posture (carries from SESSION_RITUALS Section G)

Claims of completion require evidence. URLs returning 200, grep counts, hash matches, query results — not assertion. The "verified" line in the verification ledger must point to the actual curl/grep/git output, not a narration of what was done.

If a verification command's output contradicts the expected result, the verification fails — even if "the change definitely landed" feels true. Walking back claims explicitly is the correct response, not a failure.

---

## Section L — What is NOT in this file

- **What to change.** Lives in the Z2 authority document driving the session.
- **Why a change is correct.** Lives in the Z2 authority document and its source artifacts.
- **Substrate-specific behavior.** This protocol is for the human operator (Night) executing in terminal. LLM substrate behavior lives in SESSION_RITUALS.md.
- **Live state.** Lives at HAIOSCC API endpoints.
- **Findings.** Live in REGISTERED.md.
- **Principle definitions.** Live in GOVERNANCE.md.
- **Session-specific tasks.** Live in the session's authority document, not this protocol.

This file is the execution standard for Z3 work only. Everything else has its own home.

---

## Changelog

- 2026-05-01 (S-050126) · v1.1 — Pre-publication audit fixes before initial commit to humanaios-ui/operations. (a) IC-025 references removed/replaced in Sections B-9 and I; IC-025 is the GOVERNANCE/SESSION_RITUALS cross-file edit gap (S-050126), not a credential-paste pattern. Credential discipline now stands on its own as security hygiene without IC-attribution. (b) Section B-5 paths updated to `~/Desktop/HAIOS-Main/*` per Reading B disk consolidation; HAIOSCC cross-org note added per IC-023; humanaios-internal added. (c) Section I caveat about psql meta-commands rewritten to stand alone; `F-cand-RUNNER-COMPATIBILITY-ASSUMPTION` reference removed (per P21, no candidate-status findings cited as authority). (d) Section I caveat about temporal triggers: GOVERNANCE.md version qualifier dropped from P24 reference; principle ID is the stable handle.
- 2026-04-29 (S-042928) · v1.0 — File created. Codifies Z3 commit/execution discipline that was previously implicit in CI principles P3 (GitHub Verification), P17 (Source-First Debug), P19 (Drift Detection Protocol). Surfaced as a need during S-042928 when the operations report named "files affected" matrix but no standard existed for executing it. Lettered-section structure adopted from SESSION_RITUALS.md for substrate parity.
