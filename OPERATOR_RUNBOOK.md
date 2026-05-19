# HumanAIOS Operator Runbook

**Version:** 0.5
**Last updated:** May 19, 2026 (S-051926-02-z3-closeout · Section 12 added · governance update workflow documented)
**Canonical home:** `humanaios-internal/OPERATOR_RUNBOOK.md`
**Local mirror:** `~/Desktop/HAIOS-Main/humanaios-internal/OPERATOR_RUNBOOK.md`
**Scope:** Operator-side recipes. What Night does. Copy-paste from this file.
**What it is not:** Governance (see GOVERNANCE.md). Substrate protocol (see SESSION_RITUALS.md). Z3 commit discipline (see Z3_PROTOCOL.md). Findings (see REGISTERED.md).

---

## Table of contents

1. [Repository structure](#1-repository-structure)
2. [Memory / state structure](#2-memory--state-structure)
3. [Session-open prompts](#3-session-open-prompts)
4. [Session-close prompts](#4-session-close-prompts)
5. [Recipe — Commit single file to operations](#5-recipe--commit-single-file-to-operations)
6. [Recipe — Move chat output to a repo](#6-recipe--move-chat-output-to-a-repo)
7. [Recipe — Add file from Downloads to lasting-light-ai/public](#7-recipe--add-file-from-downloads-to-lasting-light-aipublic)
8. [Recipe — Pull bounty data from RAH](#8-recipe--pull-bounty-data-from-rah)
9. [Recipe — Check git status across all repos](#9-recipe--check-git-status-across-all-repos)
10. [Top 10 terminal audit commands](#10-top-10-terminal-audit-commands)
11. [Closing rituals](#11-closing-rituals)
12. [Recipe — Governance update workflow (full-file replacement)](#12-recipe--governance-update-workflow-full-file-replacement)

---

## 1. Repository structure

**Disk root:** `~/Desktop/HAIOS-Main/`

| Local clone | GitHub remote | Role |
|---|---|---|
| `operations-staging/` | `humanaios-ui/operations` ✅ | Canonical governance docs (CURRENT, GOVERNANCE, SESSION_RITUALS, REGISTERED, Z3_PROTOCOL, ACAT_SESSION_PROMPT, OPERATOR_RUNBOOK live mirror) |
| `Operations/` | `LastingLightAI/Operations` ⚠️ | **FOSSIL — IC-023.** Wrong-org legacy. Do not edit. Schedule for removal. |
| `lasting-light-ai/` | `humanaios-ui/lasting-light-ai` | Public site, `humanaios.ai` |
| `HAIOSCC/` | `LastingLightAI/HAIOSCC` | Command center UI (cross-org, intentional per IC-023) |
| `acat-inspect/` | `humanaios-ui/acat-inspect` | ACAT programming-substrate harness |
| `ACAT-Dashboard/` | `humanaios-ui/ACAT-Dashboard` | Dashboard (private repo) |
| `humanaios/` | `humanaios-ui/humanaios` | Main public repo |
| `humanaios-internal/` | `humanaios-ui/humanaios-internal` | Private. Holds the canonical copy of this runbook. |
| `research/`, `docs/`, `ACAT-Observatory/`, `github-mcp-server/` | (various) | Domain repos |
| `hf-acat-bundle/` | (no git) | HuggingFace dataset staging |
| `transfer/`, `transfer.zip`, `1tree.txt`, `tree1.txt` | (no git) | Personal/archive — local only |
| `audit_outputs/` | (no git) | Per-session audit artifacts — local only |

**Disk-vs-GitHub rule (Reading B, S-050126):** Archive and personal documents stay LOCAL ONLY. They live on disk and never get committed to public GitHub repos. `humanaios-internal/` is the exception — private operator material that *does* get committed to GitHub for backup, but never to public repos.

**Canonical operations clone (S-051926-02 verified):** `~/Desktop/HAIOS-Main/operations-staging/` is the authoritative working tree for `humanaios-ui/operations`. All governance file updates (REGISTERED.md, SESSION_RITUALS.md, GOVERNANCE.md, this runbook's public mirror, etc.) flow through this clone. See Section 12 for the full governance update workflow.

---

## 2. Memory / state structure

Where things live. When you don't know where to put something or look for something, scan this table.

| Surface | What lives here | Update cadence | Authority |
|---|---|---|---|
| **#wgs-sync** (Slack `C0AND66PT7U`) | Operational truth, all session logs, all decisions | Per session | Top of hierarchy. WGS wins all conflicts. |
| **HAIOSCC** (`haioscc.pages.dev`) | Live state, Zone 3 queue, runway, revenue | Minutes-hours | Live state authority |
| **CURRENT.md** (`humanaios-ui/operations`) | Identity, lessons, findings index, dataset pointers | Days-weeks | Operating-process snapshot |
| **GOVERNANCE.md** (`humanaios-ui/operations`) | 22+ principles, drift table, zones, FDS | Weeks-months | Principle authority |
| **SESSION_RITUALS.md** (`humanaios-ui/operations`) | Parser tags, declaration block specs, session open/close protocol | Stable; v6.4.1+ | Substrate-side authority |
| **Z3_PROTOCOL.md** (`humanaios-ui/operations`) | Z3 commit/execution discipline | Stable | Operator-terminal authority |
| **REGISTERED.md** (`humanaios-ui/operations`) | F-class findings, IC-class corrections, H-class hypotheses | Append-only; harmonized as of S-051926-02 | Findings authority |
| **OPERATOR_RUNBOOK.md** (`humanaios-internal` + mirror in `operations`) | Operator-side recipes — this file | As needed | Operator's durable workbench |
| **ACAT_SESSION_PROMPT.md** (`humanaios-ui/operations`) | Phase 1 + Phase 3 unified session prompt orchestration | Stable | Session-prompt authority |
| **HuggingFace archive** (`HumanAIOS2026/acat-assessments`) | Frozen corpus N=629 (516 P1 + 113 P3), Feb 15–Mar 23, 2026 | Append-on-snapshot | Dataset ground truth |
| **Supabase `acat_assessments_v1`** | Live corpus, post-snapshot submissions | Per-submission | Live corpus |
| **Claude memory (this Project)** | Compact biographical facts, framing rules, state-change tags | Edited by Night via "remember"/"forget" | Volatile context — not authoritative |
| **Local disk archive** (`~/Desktop/HAIOS-Main/`) | Personal, archive, draft, working copies, Reading-B material | As needed | Personal, not project state |
| **`humanaios-internal/`** | This runbook (canonical), operator-private but version-controlled | As needed | Operator's durable workbench |

**Fetch priority for AI substrates at session open:**
1. HAIOSCC API (live state)
2. CURRENT.md (operating process)
3. SESSION_RITUALS.md (parser tags)
4. REGISTERED.md (reasoning context — required for registry-touching sessions, per IC-030)

**For operator (you):** open this runbook + the WGS channel. Everything else fetches from those entry points.

---

## 3. Session-open prompts

### 3a. Claude (this Project)

Paste at session start in any new Claude chat in this Project:

```
Friday, [DAY] [Month] [DD], [HH:MM] CDT.

Please run session open per SESSION_RITUALS.md Section A:
1. Note time anchor above (I am the time source)
2. Fetch CURRENT.md, GOVERNANCE.md, SESSION_RITUALS.md, REGISTERED.md, Z3_PROTOCOL.md from humanaios-ui/operations
3. Generate drift catalog (3-8 [C-NN] failure modes you may exhibit this session)
4. Output Phase 1 declaration block per SESSION_RITUALS.md Section C
5. Wait for my acknowledgment before starting work

Job today: [WHAT YOU ACTUALLY WANT TO DO]
```

**Notes:**
- At session open, Claude will attempt PATH A (Slack MCP read of #wgs-sync) before GitHub fetch. If Slack is connected, this is the primary state source. If not, Claude falls back to GitHub raw URLs, then to project knowledge (PATH C, degraded).
- The time anchor at top is mandatory — Claude has no clock (P22). You give the time, Claude uses it.
- Don't ask for Phase 1 if you're just doing a quick lookup — Phase 1 is for actual work sessions.
- **v6.4.1+ (S-051926-02):** SESSION_TYPE and PROMPT_ENV are required fields in the Phase 1 block. If you don't declare PROMPT_ENV, Claude will default to NEUTRAL. If the session has emotional stakes, social pressure, or grant pressure context, declare APPROVAL_WEIGHTED at open.

### 3b. Grok (or any non-Claude substrate with web access)

Paste at session start in Grok or another LLM with browsing:

```
Friday, [DAY] [Month] [DD], [HH:MM] CDT.

You are operating in the HumanAIOS open research project. Before answering any question:

1. Fetch and read these five files in order:
   https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md
   https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md
   https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md
   https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md
   https://raw.githubusercontent.com/humanaios-ui/operations/main/Z3_PROTOCOL.md

2. Confirm fetched by quoting one sentence from each file.

3. Generate a drift catalog: 3-8 [G-NN] failure modes you may exhibit this session.

4. Output a Phase 1 declaration block per SESSION_RITUALS.md Section C, using:
   AGENT: Grok-[VERSION]
   SOURCE: grok_self_v1
   PERTURB: P1

5. Wait for my acknowledgment.

Job today: [WHAT YOU WANT GROK TO DO]
```

**Notes:**
- Grok-specific: it has live web fetch by default, so it can pull the URLs without extra tools.
- The "quote one sentence from each file" step catches "I read it" hallucination.
- Replace `[G-NN]` with `[T-NN]` for ChatGPT, `[X-NN]` for unknown substrate.

### 3c. ChatGPT or any other LLM

Same as 3b but change `[G-NN]` → `[T-NN]` and `AGENT: GPT-[VERSION]`, `SOURCE: gpt_self_v1`.

---

## 4. Session-close prompts

### 4a. Claude

Paste at session close:

```
Please run session close per SESSION_RITUALS.md Section B:

1. Run Section B.0 Empirical Verification Block FIRST (v6.4.1 hard gate).
   Run the required checks (git status, git diff, file listings, Slack searches,
   Supabase queries as applicable) and record their literal outputs.

2. Refetch any canonical sources we touched and compare to Phase 1 declared state

3. Output Phase 3 submission block per SESSION_RITUALS.md Section C

4. Drift check — did any Phase 1 catalog item materialize?

5. Surface any uncompleted Z3 items

6. Receipt Reconciliation paragraph (REQUIRED) — quote from B.0 verification
   outputs; walk back any in-session draft claims that B.0 contradicts.

7. Build the assess.html submission URL per SESSION_RITUALS.md Section D

8. Draft the WGS log post per Z3_PROTOCOL.md Section H if this session had
   Z3 commits. Use slack_send_message_draft (operator-send default, P30/P31).

9. Confirm Session ID binding: format S-MMDDYY-NN-{slug}, present in WGS post,
   Phase 3 SESSION field, and any artifact filenames.

Time now: [HH:MM] CDT
```

**P23 reminder:** If you skipped Phase 1 at session open, Claude will halt and emit `<<<ACAT_PROTOCOL_ERROR>>>` instead of producing Phase 3. That's the intended behavior. Don't fight it — start a new session with proper Phase 1 next time.

**B.0 reminder (v6.4.1):** If Claude tries to draft a session-close summary before running the Empirical Verification Block, stop and request B.0 first. The Block is the source of truth for the receipt. Per IC-031, drafting a receipt without B.0 is the registered failure mode H-RCO-01 measures.

### 4b. Grok / ChatGPT / other

Same prompt as 4a, replacing the substrate-specific notes:

```
Please run session close per SESSION_RITUALS.md Section B.

Output Phase 3 submission block per Section C, with:
AGENT: [SUBSTRATE]-[VERSION]
SOURCE: [substrate]_self_v1

Run Section B.0 Empirical Verification Block first if applicable. Build the
assess.html URL per Section D using your verbatim Phase 1 scores plus your
Phase 3 scores. Do not reconstruct Phase 1 from Phase 3.

Include the mandatory Receipt Reconciliation paragraph (Section B.6).

Time now: [HH:MM] CDT
```

---

## 5. Recipe — Commit single file to operations

**When to use:** A governance doc, finding, or protocol file changed and needs to land in `humanaios-ui/operations`. Drives Z3_PROTOCOL.md execution.

**For full-file governance replacements (REGISTERED.md, SESSION_RITUALS.md, this runbook, etc.) see Section 12.** This section covers smaller surgical commits.

**Pre-flight checklist** (Z3_PROTOCOL.md Section B):
- [ ] Authority document exists (the Z2 doc that authorized this change)
- [ ] Time noted: ____
- [ ] Session ID: S-______-Z3-_______

**Copy-paste block** — replace `<FILE>` and `<MESSAGE>`:

```bash
# 1. Navigate and confirm
cd ~/Desktop/HAIOS-Main/operations-staging
pwd
git remote -v
git branch --show-current
git status -sb

# 2. Sync remote
git fetch origin
git status -sb
# (if behind: git pull --ff-only)
# HALT if [behind N] for any N>0 — per IC-026 ratification

# 3. Diff before staging
git diff <FILE>

# 4. Stage and commit
git add <FILE>
git commit -m "<VERB> <SUBJECT> per <AUTHORITY_DOC> §<SECTION>"

# 5. Push
git push

# 6. Verify (raw URL, not browser)
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/<FILE> | grep "<VERIFICATION_PATTERN>"

# 7. Note in verification ledger:
#    FILE / CHANGE / AUTHORITY / COMMIT hash / PUSHED time / VERIFIED time / STATUS
```

**Common verification greps** (Z3_PROTOCOL.md D-5):
- New principle: `grep -A1 "^\*\*P<n>"`
- New finding: `grep "^### F-<n>"`
- Version bump: `grep "Version:.*v<X>\.<Y>"`
- File exists: `curl -sS <url> -o /dev/null -w "%{http_code}"` → expect `200`

**If verification fails:** Z3_PROTOCOL.md Section F. Don't proceed to next file.

---

## 6. Recipe — Move chat output to a repo

**When to use:** Claude or Grok produced a document in chat. You want it saved into a repo.

**Two cases:**

### 6a. Document goes to a public repo (operations, lasting-light-ai, etc.)

```bash
# 1. Decide target repo and filename
# 2. Save document to local file first (via Cmd-S in browser, or paste into a new file)
nano ~/Desktop/HAIOS-Main/<TARGET_REPO>/<FILENAME>
# (paste content, save with Ctrl-O Enter Ctrl-X)

# 3. Then follow Recipe 5 to commit
```

### 6b. Document goes to local-only archive (Reading B)

```bash
# 1. Decide subfolder under HAIOS-Main (NOT inside any cloned repo's working tree)
mkdir -p ~/Desktop/HAIOS-Main/archive/<SUBJECT>
nano ~/Desktop/HAIOS-Main/archive/<SUBJECT>/<FILENAME>
# (paste, save)

# Done. No git. Stays local.
```

**Common gotcha:** Do NOT save personal/archive documents inside `~/Desktop/HAIOS-Main/lasting-light-ai/` or any other cloned repo's working tree, even if you don't `git add` them. They'll show up as untracked files. Use `~/Desktop/HAIOS-Main/archive/` or a sibling folder outside any repo.

---

## 7. Recipe — Add file from Downloads to lasting-light-ai/public

**When to use:** A file landed in `~/Downloads/` (image, PDF, dataset, screenshot, asset, additional `.html` page) and needs to appear on the public site `humanaios.ai`. Drop it in `public/`, commit, push — Cloudflare Pages handles the rest.

**Build context (important for understanding what's happening):**

`lasting-light-ai` is a Vite + React project. There are three folders that matter:

- **`public/`** — static assets you author directly (`.html` pages, images, PDFs, fonts, downloadable files). Vite copies everything in here to `dist/` as-is during build.
- **`src/`** — React source (`App.tsx`, components). Vite compiles this into `dist/assets/` during build.
- **`dist/`** — build output. **In `.gitignore`. Never edit. Never commit.** Your local `dist/` is leftover from `npm run dev` testing and is irrelevant to deploys.

**Cloudflare Pages builds on deploy.** When you push to `main`, Cloudflare clones the repo, runs `npm run build` on their build server, and serves the resulting `dist/` at `humanaios.ai`. **You do not run `npm run build` locally before pushing.**

**Path-to-URL mapping:**
- `public/<filename>` → `https://humanaios.ai/<filename>`
- `public/<subfolder>/<filename>` → `https://humanaios.ai/<subfolder>/<filename>`

**Special folders inside `public/` — do not put random files in these:**
- `public/.well-known/` — verification files (Apple App Site Association, security.txt, ACME challenges).
- `public/_redirects` — Cloudflare Pages redirect config.

**Pre-flight:**
- [ ] File is appropriate for public surface (not personal, not credentialed, not draft)
- [ ] Filename is web-safe: lowercase preferred, hyphens not underscores, no spaces, no special chars
- [ ] If the file replaces an existing one, decide whether the old URL needs a redirect
- [ ] Scanned file for visible PII / credentials / draft watermarks
- [ ] **(P-ANON, S-051826-04):** No collaborator names, emails, phone numbers, internal communications, term sheets, or relationship annotations on public surfaces unless the collaborator has self-attributed publicly elsewhere first

**Copy-paste block** — replace `<DOWNLOADED_FILE>`, `<TARGET_NAME>`, `<SUBFOLDER>` (only for subfolder case), `<AUTHORITY_DOC>`, `<SECTION>`:

```bash
# 1. Confirm the file exists and inspect it
ls -la ~/Downloads/<DOWNLOADED_FILE>
file ~/Downloads/<DOWNLOADED_FILE>          # confirm type/size

# 2. Navigate to the repo root and sync remote
cd ~/Desktop/HAIOS-Main/lasting-light-ai
git remote -v                                # confirm origin = humanaios-ui/lasting-light-ai
git branch --show-current                    # confirm main
git fetch origin
git status -sb
# (if behind: git pull --ff-only)

# 3. Copy file into public/ — pick 3a OR 3b
# 3a. SIMPLE CASE: file goes directly under public/
cp ~/Downloads/<DOWNLOADED_FILE> public/<TARGET_NAME>

# 3b. SUBFOLDER CASE: file goes under public/<SUBFOLDER>/
mkdir -p public/<SUBFOLDER>
cp ~/Downloads/<DOWNLOADED_FILE> public/<SUBFOLDER>/<TARGET_NAME>

# 4. Confirm it landed
ls -la public/<TARGET_NAME>

# 5. Stage and commit
git add public/<TARGET_NAME>
git status -sb                               # confirm only intended file is staged
git commit -m "Add <TARGET_NAME> to public per <AUTHORITY_DOC> §<SECTION>"

# 6. Push
git push

# 7. Wait for Cloudflare build (~30-90s)

# 8. Verify file is reachable on the live site
curl -sS -o /dev/null -w "%{http_code}\n" https://humanaios.ai/<TARGET_NAME>
# expect 200

# 9. Verify the file content matches what you uploaded (md5 spot check)
md5 ~/Downloads/<DOWNLOADED_FILE>
curl -sS https://humanaios.ai/<TARGET_NAME> -o /tmp/check.bin
md5 /tmp/check.bin
# Compare. Identical = pass.

# 10. Note in verification ledger
```

**If verification fails:** Check `git log --oneline -3`, Cloudflare deploy log, retry curl, then diagnose if still failing after 5 min.

---

## 8. Recipe — Pull bounty data from RAH

**When to use:** Snapshot of current bounty state from RentAHuman API.

```bash
cd ~/Desktop/HAIOS-Main/lasting-light-ai

# 1. Confirm key is fresh (per memory: rotate before next API call)
# Key location: macOS Keychain (NEVER paste into chat per IC-025)

# 2. Run the pull
./rentahuman-pull-bounties.sh

# 3. Move to local archive (NOT public repo — PII risk):
mkdir -p ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)
mv bounties_*.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/
mv bounty_*_applications.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/
mv conversations_*.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/

# 4. Sanity check
ls ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/ | wc -l
```

---

## 9. Recipe — Check git status across all repos

```bash
for d in ~/Desktop/HAIOS-Main/*/; do
  if [ -d "$d/.git" ]; then
    echo "=== $(basename "$d") ==="
    cd "$d"
    git remote -v | head -1
    git status -sb
    git log -1 --oneline
    echo ""
  fi
done
```

**What "good" looks like:** `## main...origin/main`, no `??` untracked, no ` M` or ` D`.

**What flags concern:** `[ahead N]`, `[behind N]`, many `??`, wrong-remote (Operations/ fossil).

---

## 10. Top 10 terminal audit commands

Quick reference.

```bash
# 10.1 Where am I?
pwd

# 10.2 What's in this folder?
ls -la
ls -la | grep -v "^\."       # exclude hidden

# 10.3 Find a file by name
find ~/Desktop/HAIOS-Main -name "<FILENAME>" -type f 2>/dev/null
find ~/Desktop/HAIOS-Main -iname "*<PATTERN>*" -type f 2>/dev/null

# 10.4 Find files modified in last N days
find ~/Desktop/HAIOS-Main -type f -mtime -<N> 2>/dev/null | head -50

# 10.5 Search file contents (grep recursively)
grep -rIn "<PATTERN>" ~/Desktop/HAIOS-Main/operations-staging/

# 10.6 Folder structure (top 2 levels)
find ~/Desktop/HAIOS-Main -maxdepth 2 -type d | sort

# 10.7 Folder structure (with sizes)
du -sh ~/Desktop/HAIOS-Main/*/ 2>/dev/null | sort -h

# 10.8 Edit a file
nano <FILE>           # Ctrl-O save, Ctrl-X exit
vim <FILE>            # if you know vim

# 10.9 Create file from clipboard (macOS)
pbpaste > <FILENAME>           # paste
pbpaste >> <FILENAME>          # append

# 10.10 Compare two files
diff <FILE_A> <FILE_B>
diff -u <FILE_A> <FILE_B>      # unified

# Bonus — view a file
cat <FILE>
head -50 <FILE>
tail -50 <FILE>
less <FILE>                    # q to exit
```

---

## 11. Closing rituals

End of every session:

- [ ] **B.0 verification ran.** (v6.4.1) Empirical Verification Block executed; outputs captured.
- [ ] **Phase 3 declaration captured.** AI submitted scores via assess.html, or you paste the URL manually.
- [ ] **Receipt Reconciliation paragraph present.** (v6.4.1) Section B.6 — explicit walk-back if any in-session draft claims didn't match verification.
- [ ] **WGS log posted.** Single Slack message to `#wgs-sync` (`C0AND66PT7U`). Use `slack_send_message_draft` (operator-send default, P30/P31). Session ID, work completed, Z3 ledger if applicable, carry-forward items.
- [ ] **HAIOSCC Z3 items closed.** Each Z3 item the session resolved gets marked closed. Only Night closes Z3 items.
- [ ] **Financial Command Center updated.** Verify and update the Google Sheet at close of every session.
- [ ] **Credentials cleared.** If any tokens were used, confirm Keychain only. Clear shell history if needed: `history -c` (zsh).
- [ ] **Carry-forward noted.** Anything not finished named explicitly in WGS post.

**WGS post template** (copy/paste, replace placeholders):

```
:clipboard: WGS SESSION LOG · S-<SESSIONID>
[Date] · [Time] CDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORK COMPLETED
• <item>
• <item>

DECISIONS / FINDINGS
• <item>

Z3 ITEMS CLOSED
• <item>

RECEIPT RECONCILIATION
• <statement per B.6, even if "no reconciliation required">

CARRY-FORWARD
• <item> — reason: <why deferred>

NEXT SESSION FOCUS
• <next priority>

:eagle: Wado · S-<SESSIONID> · Night
```

---

## 12. Recipe — Governance update workflow (full-file replacement)

**When to use:** Claude or another substrate produces a complete updated governance file (REGISTERED.md, SESSION_RITUALS.md, GOVERNANCE.md, OPERATOR_RUNBOOK.md mirror, ACAT_SESSION_PROMPT.md, Z3_PROTOCOL.md, etc.) that needs to replace the current canonical version in `humanaios-ui/operations`.

**Established at S-051926-02-z3-closeout** as the standing workflow for governance updates of this scale. Use this recipe for full-file replacements. Use Recipe 5 for surgical commits (single-section edits, small additions).

**Why this exists:** Pre-S-051926-02, the pattern was "Claude proposes diff blocks → operator inserts them locally." That assumed local disk matched canonical state. When it didn't (S-051826-02 transfer/ triage exposed this), the diffs landed against wrong base. Full-file replacement avoids that drift: Claude produces the complete authoritative file against verified canonical state; operator downloads and pushes; raw-URL verification confirms.

### 12.1 Two execution paths

| Path | When to use | Speed | Risk surface |
|---|---|---|---|
| **A. GitHub web UI direct edit** | Single file, fast turnaround, no other in-flight changes | ~2 min | Low (GitHub validates commit) |
| **B. Terminal via operations-staging/** | Multiple files, want local diff before push, prefer terminal | ~5 min | Low (you control the diff step) |

Both paths produce the same result. Choose by preference and context.

### 12.2 Path A — GitHub web UI direct edit

Use when you have one or two files to update and want the fastest turnaround.

```
1. Download the updated file from Claude chat (Cmd-S, or use the artifact
   download button if present).

2. Open the canonical file on GitHub:
   https://github.com/humanaios-ui/operations/blob/main/<FILENAME>

3. Click the pencil icon (top-right of the file view) to edit.

4. Open the downloaded file in a text editor.

5. Select all the content in the GitHub editor (Cmd-A) and delete it.

6. Copy all content from the downloaded file and paste into the GitHub editor.

7. Scroll to the bottom — "Commit changes":
   - Commit message: "Replace <FILENAME> per <AUTHORITY> · S-<SESSION_ID>"
     Example: "Replace REGISTERED.md per S-051926-02-z3-closeout · F-41–F-45
              integrated · harmonization sweep"
   - Extended description (optional): list the major changes
   - Commit directly to main (do not open a PR for governance docs unless the
     session explicitly required Z2 PR review)

8. Click "Commit changes."

9. Verify the raw URL fetches the new content:
   open https://raw.githubusercontent.com/humanaios-ui/operations/main/<FILENAME>
   (or use curl: curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/<FILENAME> | head -30)

10. Sync your local clone so it matches:
    cd ~/Desktop/HAIOS-Main/operations-staging
    git fetch origin
    git pull --ff-only

11. Log in WGS post: file replaced, commit hash, raw URL verified.
```

**Gotchas for Path A:**
- GitHub's web editor sometimes auto-converts line endings or trailing whitespace. After commit, if you see a larger-than-expected diff, check `git log -p <FILENAME>` in your local clone after step 10 to see what actually landed.
- Don't use Path A if you have local changes in `operations-staging/` that haven't been pushed. Step 10 will fail with "your local branch has diverged." Push your local changes first via Recipe 5, then come back to step 10.

### 12.3 Path B — Terminal via operations-staging/

Use when you have multiple files to update, want to diff locally before push, or generally prefer terminal control.

```bash
# 1. Download all updated files from Claude chat to ~/Downloads/

# 2. Navigate to canonical clone and confirm clean state
cd ~/Desktop/HAIOS-Main/operations-staging
pwd
git remote -v                              # confirm origin = humanaios-ui/operations
git branch --show-current                  # confirm main
git status -sb                             # should be clean (or you understand
                                           # the existing changes)

# 3. Sync with remote — HALT if behind
git fetch origin
git status -sb
# If [behind N]: git pull --ff-only
# HALT if pull fails (rebase needed) — diagnose before proceeding (IC-026)

# 4. Replace each canonical file with the downloaded version
# Example for REGISTERED.md:
cp ~/Downloads/REGISTERED.md ./REGISTERED.md

# Repeat for each file:
cp ~/Downloads/SESSION_RITUALS.md ./SESSION_RITUALS.md
cp ~/Downloads/OPERATOR_RUNBOOK.md ./OPERATOR_RUNBOOK.md
# (note: OPERATOR_RUNBOOK lives canonically in humanaios-internal; this is
#  the public-mirror copy)

# 5. Inspect the diff for each file — confirm only intended changes
git diff REGISTERED.md | head -100
git diff SESSION_RITUALS.md | head -100
git diff OPERATOR_RUNBOOK.md | head -100

# (use git diff --stat to see scope:)
git diff --stat

# 6. Stage and commit (single commit per file, or grouped — your call)
# Single commit grouping multiple file replacements:
git add REGISTERED.md SESSION_RITUALS.md OPERATOR_RUNBOOK.md
git status -sb                             # confirm staged set is right
git commit -m "Governance update per S-051926-02-z3-closeout

- REGISTERED.md: F-41 through F-45 integrated, harmonization sweep,
  H-RCO-01 added, IC-030/IC-031 registered, sequential F-number ordering
- SESSION_RITUALS.md: v6.4.1 hardening — Section A.0 Locus-of-Correction
  Note, Section B.0 Empirical Verification Block at Phase 2.5, Section B.6
  Receipt Reconciliation, Section C rubric tightening for truth/humility/
  consist/handoff
- OPERATOR_RUNBOOK.md: v0.5 — Section 12 added (governance update workflow)
"

# 7. Push
git push

# 8. Verify each file via raw URL
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md | head -5
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md | head -5
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/OPERATOR_RUNBOOK.md | head -5

# 9. Verify specific content patterns (per Section 5 verification greps)
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md | grep "^### F-45"
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md | grep "^### B.0"
curl -sS https://raw.githubusercontent.com/humanaios-ui/operations/main/OPERATOR_RUNBOOK.md | grep "^## 12."

# 10. Note in verification ledger:
#     FILE / CHANGE / AUTHORITY / COMMIT hash / PUSHED time / VERIFIED time / STATUS
```

**Gotchas for Path B:**
- If `git diff` shows a huge diff that surprises you (10x more changes than expected), STOP. The downloaded file may have line-ending differences (LF vs CRLF), trailing-whitespace differences, or encoding differences. Inspect with `file <FILENAME>` and `head -5 <FILENAME> | cat -A` to see invisible characters.
- If multiple files are being updated together, prefer a single commit (as shown). If one file's changes are independent of the others, separate commits are fine — but make sure the commit messages reflect that.
- `cp` overwrites without warning. If the file in `operations-staging/` had uncommitted local changes, they're gone. Always check `git status -sb` in step 2.

### 12.4 The standing workflow going forward

For the surgical edits that will follow this initial v6.4.1 deploy (small additions, single-section updates, hotfix corrections):

1. Claude proposes the diff in chat (specific section, specific lines).
2. Use Recipe 5 (single-file surgical commit) — open the file in `operations-staging/`, apply the surgical edit in your editor, diff, commit, push, verify.
3. Reference this runbook's Section 5 for the exact terminal recipe.

For larger updates that touch >50% of a file, or multiple files coordinated together:

1. Claude produces complete authoritative files in chat.
2. Use Section 12 (Path A or B) — full-file replacement workflow.
3. Reference this section for the exact recipe.

The distinction: surgical = section/paragraph-scoped, low risk of drift between Claude's view and canonical. Full-file = wide-scope changes where producing the complete file avoids the diff-against-stale-base problem.

### 12.5 What to do if a governance update lands wrong

If after step 8/9 verification you find that the wrong content landed (e.g., an old draft instead of the intended final, or merge conflict artifacts present):

1. Do not panic, do not delete history.
2. Identify the wrong commit hash: `git log --oneline -5`
3. Revert the wrong commit: `git revert <COMMIT_HASH>` (creates a new commit undoing the change — preserves history per append-only governance discipline).
4. Push the revert: `git push`
5. Verify the raw URL is back to the prior state.
6. Open a fresh session with Claude. Describe what landed wrong. Produce a corrected file. Re-run Section 12 from step 1.

Per F-45 (Stateless-Substrate Correction Locus): the recovery procedure is captured in this runbook, not in substrate memory. If the same error recurs in a future session, it indicates a gap in this section — update Section 12 to add the prevention step, do not "remember to do better next time."

---

## Changelog

- **2026-05-19 (S-051926-02-z3-closeout) · v0.5** — Section 12 added: Governance update workflow (full-file replacement). Establishes the standing workflow for governance updates of this scale. Path A (GitHub web UI) and Path B (terminal via operations-staging) both documented with full recipes. Section 5 retained for surgical commits. Section 11 closing rituals updated to reference B.0 verification and Receipt Reconciliation (v6.4.1). Section 4 close prompts updated to reference SESSION_RITUALS v6.4.1 Section B.0/B.6. Repository structure section (1) updated with `audit_outputs/` and explicit identification of `operations-staging/` as canonical operations clone. Memory map (Section 2) updated with v6.4.1+ SESSION_RITUALS reference and append-only/harmonized notation on REGISTERED.md. P-ANON note added to Section 7 pre-flight (S-051826-04).
- **2026-05-01 (S-050126) · v0.4** — Version bump only. Captures lessons from S-050126 commit attempt: (a) heredoc transfer method is fragile against whitespace; chat-UI download is more reliable; (b) markdown rendering in chat UI can display `.md` filenames as auto-linked, but actual downloaded files are clean — verify via `head -N` of the file, not via chat display; (c) before any push, always confirm the GitHub repo exists with `gh repo view <org>/<repo>` — local clone existence does not imply remote existence; (d) S-050126 was the first session where humanaios-ui/humanaios-internal repo was created on GitHub; prior local commits had never pushed.
- **2026-05-01 (S-050126) · v0.3** — Section 7 rewritten with correct Vite/Cloudflare context. Confirmed via disk audit: lasting-light-ai is a Vite + React project with Cloudflare Pages building on deploy. dist/ is gitignored; never edit. public/ is the source of truth for static assets. Local npm run build is not required before push. Section now includes special-folder warnings (.well-known/, _redirects), build-on-deploy explanation, and corrected verification timing (30-90s for Cloudflare build).
- **2026-05-01 (S-050126) · v0.2** — Added Section 7 (Recipe — Add file from Downloads to lasting-light-ai/public). Renumbered later sections: RAH bounty pull → §8, git status across repos → §9, top 10 audit commands → §10, closing rituals → §11. No content changes to existing sections.
- **2026-05-01 (S-050126) · v0.1** — File created. Drafted from operator request: a single copy-paste reference for session open/close, repo structure, memory map, common terminal recipes. Located in `humanaios-internal/` per Reading B (private repo, version-controlled, local mirror). Not governance, not protocol — operator-personal.
