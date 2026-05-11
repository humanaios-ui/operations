# HumanAIOS Operator Runbook

**Version:** 0.4 (draft)
**Last updated:** May 1, 2026 (S-050126)
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

---

## 1. Repository structure

**Disk root:** `~/Desktop/HAIOS-Main/`

| Local clone | GitHub remote | Role |
|---|---|---|
| `operations-staging/` | `humanaios-ui/operations` ✅ | Canonical governance docs (CURRENT, GOVERNANCE, SESSION_RITUALS, REGISTERED, Z3_PROTOCOL, ACAT_SESSION_PROMPT) |
| `Operations/` | `LastingLightAI/Operations` ⚠️ | **FOSSIL — IC-023.** Wrong-org legacy. Do not edit. Schedule for removal. |
| `lasting-light-ai/` | `humanaios-ui/lasting-light-ai` | Public site, `humanaios.ai` |
| `HAIOSCC/` | `LastingLightAI/HAIOSCC` | Command center UI (cross-org, intentional per IC-023) |
| `acat-inspect/` | `humanaios-ui/acat-inspect` | ACAT programming-substrate harness |
| `ACAT-Dashboard/` | `humanaios-ui/ACAT-Dashboard` | Dashboard (private repo) |
| `humanaios 2/` | `humanaios-ui/humanaios` | Main public repo (rename to `humanaios/` when convenient) |
| `humanaios-internal/` | `humanaios-ui/humanaios-internal` | Private. Holds this runbook. |
| `hf-acat-bundle/` | (no git) | HuggingFace dataset staging |
| `haioscc-phase1-staging/` | (empty) | Scratch |
| `transfer/`, `transfer.zip`, `1tree.txt`, `tree1.txt` | (no git) | Personal/archive — local only |

**Disk-vs-GitHub rule (Reading B, S-050126):** Archive and personal documents stay LOCAL ONLY. They live on disk and never get committed to public GitHub repos. `humanaios-internal/` is the exception — private operator material that *does* get committed to GitHub for backup, but never to public repos.

---

## 2. Memory / state structure

Where things live. When you don't know where to put something or look for something, scan this table.

| Surface | What lives here | Update cadence | Authority |
|---|---|---|---|
| **#wgs-sync** (Slack `C0AND66PT7U`) | Operational truth, all session logs, all decisions | Per session | Top of hierarchy. WGS wins all conflicts. |
| **HAIOSCC** (`haioscc.pages.dev`) | Live state, Zone 3 queue, runway, revenue | Minutes-hours | Live state authority |
| **CURRENT.md** (`humanaios-ui/operations`) | Identity, lessons, findings index, dataset pointers | Days-weeks | Operating-process snapshot |
| **GOVERNANCE.md** (`humanaios-ui/operations`) | 22+ principles, drift table, zones, FDS | Weeks-months | Principle authority |
| **SESSION_RITUALS.md** (`humanaios-ui/operations`) | Parser tags, declaration block specs, session open/close protocol | Stable | Substrate-side authority |
| **Z3_PROTOCOL.md** (`humanaios-ui/operations`) | Z3 commit/execution discipline | Stable | Operator-terminal authority |
| **REGISTERED.md** (`humanaios-ui/operations`) | F-class findings, IC-class corrections, H-class hypotheses | Append-only | Findings authority |
| **ACAT_SESSION_PROMPT.md** (`humanaios-ui/operations`) | Phase 1 + Phase 3 unified session prompt orchestration | Stable | Session-prompt authority |
| **HuggingFace archive** (`HumanAIOS2026/acat-assessments`) | Frozen corpus N=629 (516 P1 + 113 P3), Feb 15–Mar 23, 2026 | Append-on-snapshot | Dataset ground truth |
| **Supabase `acat_assessments_v1`** | Live corpus, post-snapshot submissions | Per-submission | Live corpus |
| **Claude memory (this Project)** | Compact biographical facts, framing rules, state-change tags | Edited by Night via "remember"/"forget" | Volatile context — not authoritative |
| **Local disk archive** (`~/Desktop/HAIOS-Main/`) | Personal, archive, draft, working copies, Reading-B material | As needed | Personal, not project state |
| **`humanaios-internal/`** | This runbook, operator-private but version-controlled | As needed | Operator's durable workbench |

**Fetch priority for AI substrates at session open:**
1. HAIOSCC API (live state)
2. CURRENT.md (operating process)
3. SESSION_RITUALS.md (parser tags)
4. REGISTERED.md (reasoning context)

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
- Claude in this Project has access to project files including the live operations docs *if you've kept them current there.* If they're stale, paste the live versions in or tell Claude to ask.
- The time anchor at top is mandatory — Claude has no clock (P22). You give the time, Claude uses it.
- Don't ask for Phase 1 if you're just doing a quick lookup — Phase 1 is for actual work sessions.

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
1. Refetch any canonical sources we touched and compare to Phase 1 declared state
2. Output Phase 3 submission block per SESSION_RITUALS.md Section C
3. Drift check — did any Phase 1 catalog item materialize?
4. Surface any uncompleted Z3 items
5. Build the assess.html submission URL per SESSION_RITUALS.md Section D
6. Draft the WGS log post per Z3_PROTOCOL.md Section H if this session had Z3 commits

Time now: [HH:MM] CDT
```

**P23 reminder:** If you skipped Phase 1 at session open, Claude will halt and emit `<<<ACAT_PROTOCOL_ERROR>>>` instead of producing Phase 3. That's the intended behavior. Don't fight it — start a new session with proper Phase 1 next time.

### 4b. Grok / ChatGPT / other

Same prompt as 4a, replacing the substrate-specific notes:

```
Please run session close. Output Phase 3 submission block per SESSION_RITUALS.md Section C, with:
AGENT: [SUBSTRATE]-[VERSION]
SOURCE: [substrate]_self_v1

Build the assess.html URL per Section D using your verbatim Phase 1 scores plus your Phase 3 scores. Do not reconstruct Phase 1 from Phase 3.

Time now: [HH:MM] CDT
```

---

## 5. Recipe — Commit single file to operations

**When to use:** A governance doc, finding, or protocol file changed and needs to land in `humanaios-ui/operations`. Drives Z3_PROTOCOL.md execution.

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
- New finding: `grep "^### F<n>"`
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

**Common gotcha:** Do NOT save personal/archive documents inside `~/Desktop/HAIOS-Main/lasting-light-ai/` or any other cloned repo's working tree, even if you don't `git add` them. They'll show up as untracked files (per the disk audit — 350+ bounty JSONs are doing this right now). Use `~/Desktop/HAIOS-Main/archive/` or a sibling folder outside any repo.

---

## 7. Recipe — Add file from Downloads to lasting-light-ai/public

**When to use:** A file landed in `~/Downloads/` (image, PDF, dataset, screenshot, asset, additional `.html` page) and needs to appear on the public site `humanaios.ai`. Drop it in `public/`, commit, push — Cloudflare Pages handles the rest.

**Build context (important for understanding what's happening):**

`lasting-light-ai` is a Vite + React project. There are three folders that matter:

- **`public/`** — static assets you author directly (`.html` pages, images, PDFs, fonts, downloadable files). Vite copies everything in here to `dist/` as-is during build.
- **`src/`** — React source (`App.tsx`, components). Vite compiles this into `dist/assets/` during build.
- **`dist/`** — build output. **In `.gitignore`. Never edit. Never commit.** Your local `dist/` is leftover from `npm run dev` testing and is irrelevant to deploys.

**Cloudflare Pages builds on deploy.** When you push to `main`, Cloudflare clones the repo, runs `npm run build` on their build server, and serves the resulting `dist/` at `humanaios.ai`. **You do not run `npm run build` locally before pushing.** The build step happens on Cloudflare's infrastructure.

**Path-to-URL mapping:**
- `public/<filename>` → `https://humanaios.ai/<filename>`
- `public/<subfolder>/<filename>` → `https://humanaios.ai/<subfolder>/<filename>`

**Special folders inside `public/` — do not put random files in these:**
- `public/.well-known/` — verification files (Apple App Site Association, security.txt, ACME challenges). Touch only when you know what you're verifying.
- `public/_redirects` — Cloudflare Pages redirect config. Edit only when adding/changing URL redirects.

**Pre-flight:**
- [ ] File is appropriate for public surface (not personal, not credentialed, not draft)
- [ ] Filename is web-safe: lowercase preferred, hyphens not underscores, no spaces, no special chars
- [ ] If the file replaces an existing one, you've decided whether the old URL needs a redirect (`_redirects` edit)
- [ ] Scanned file for visible PII / credentials / draft watermarks

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

# 4. Confirm it landed where you expected
ls -la public/<TARGET_NAME>
# or for subfolder:
ls -la public/<SUBFOLDER>/<TARGET_NAME>

# 5. Stage and commit (only the new file)
git add public/<TARGET_NAME>                 # or public/<SUBFOLDER>/<TARGET_NAME>
git status -sb                               # confirm only intended file is staged
git commit -m "Add <TARGET_NAME> to public per <AUTHORITY_DOC> §<SECTION>"

# 6. Push
git push

# 7. Wait for Cloudflare build (~30-90s) then verify
# Open Cloudflare dashboard tab to watch the deploy if you want:
# https://dash.cloudflare.com/92cfe886ee648fc5d797a7ca1aa04922/humanaios.ai

# 8. Verify file is reachable on the live site
curl -sS -o /dev/null -w "%{http_code}\n" https://humanaios.ai/<TARGET_NAME>
# expect 200
# subfolder case:
curl -sS -o /dev/null -w "%{http_code}\n" https://humanaios.ai/<SUBFOLDER>/<TARGET_NAME>

# 9. Verify the file content matches what you uploaded (md5 spot check)
md5 ~/Downloads/<DOWNLOADED_FILE>
curl -sS https://humanaios.ai/<TARGET_NAME> -o /tmp/check.bin
md5 /tmp/check.bin
# Compare the two md5 hashes by eye. Identical = pass. Different = investigate.

# 10. Note in verification ledger:
#    FILE / CHANGE / AUTHORITY / COMMIT hash / PUSHED time / VERIFIED time / STATUS
```

**Common gotchas:**

- **First fetch may 404 for up to ~90 seconds.** Cloudflare needs time to clone, build, and propagate. If 404 after 2 minutes, check the deploy log at the dashboard — the build may have failed (most often: a `src/` change broke the React build, blocking the whole deploy including your unrelated asset).
- **Old content cached after deploy.** Cloudflare's edge cache may serve the old version of a same-named file briefly. Hard refresh in browser (Cmd-Shift-R) doesn't bypass edge cache; only time does. Usually clears within 1-2 minutes.
- **Spaces in filenames break URLs.** `My Photo.png` becomes `My%20Photo.png` and is fragile. Rename on copy: `cp "~/Downloads/My Photo.png" public/my-photo.png`.
- **Don't edit `dist/`.** It's gitignored and gets regenerated on every Cloudflare build. Anything you put there locally is invisible to the live site.
- **Don't run `npm run build` before pushing.** Cloudflare builds on their end. Local builds only matter if you want to preview at `localhost` via `npm run dev` or `npm run preview`.
- **PII / credentials check before commit.** Once it's in git history, even after deletion it's accessible by commit hash forever. Open the file. Look at it. Then commit.
- **Large files (>25 MB).** Reconsider whether the public site is the right host. For datasets, prefer HuggingFace or S3. For images, optimize first. Z2 conversation if it's >100 MB.
- **`public/index.html` is the homepage.** Don't replace it casually — it's the entry point for `humanaios.ai/` itself.
- **HTML files don't auto-link.** Adding `public/foo.html` makes it reachable at `humanaios.ai/foo.html`, but users only find it if `index.html` (or another page) links to it. Linking is a separate edit.

**If verification fails (step 8 returns non-200, or step 9 shows hash mismatch):**

1. Check `git log --oneline -3` — did the push actually land?
2. Open Cloudflare dashboard, click into the deploy log for the most recent build. Did it succeed? If failed, fix the cause and push again.
3. Wait another minute, retry the curl — first fetch is sometimes slow.
4. If still failing after 5 min: the build broke or routing is misconfigured. Halt and diagnose before adding more files.

---

## 8. Recipe — Pull bounty data from RAH

**When to use:** Snapshot of current bounty state from RentAHuman API.

**The script exists** (`rentahuman-pull-bounties.sh` in `lasting-light-ai/`). This recipe wraps invocation.

```bash
cd ~/Desktop/HAIOS-Main/lasting-light-ai

# 1. Confirm key is fresh (per memory: rotate before next API call)
# Key location: macOS Keychain (NEVER paste into chat per IC-025)

# 2. Run the pull
./rentahuman-pull-bounties.sh
# This produces:
#   bounties_open.json
#   bounties_assigned.json
#   bounties_completed.json
#   bounties_cancelled.json
#   bounty_<ID>_applications.json (one per bounty)
#   conversations_active.json
#   conversations_archived.json

# 3. These are NOT for the public repo (PII risk + clutter)
# Move to local archive:
mkdir -p ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)
mv bounties_*.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/
mv bounty_*_applications.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/
mv conversations_*.json ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/

# 4. Sanity check
ls ~/Desktop/HAIOS-Main/archive/rah-snapshots/$(date +%Y-%m-%d)/ | wc -l
```

**Open question:** The 350+ untracked bounty JSONs currently sitting in `lasting-light-ai/` working tree should probably be moved to `archive/rah-snapshots/<date>/` and the script updated to write there directly. That's a Z2 conversation, not a runbook recipe.

---

## 9. Recipe — Check git status across all repos

**When to use:** Start of a session, or any time you want a quick "what's drifted" view across all clones.

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

**What "good" looks like:**
- `## main...origin/main` (no `[ahead N]` or `[behind N]`)
- No `??` untracked files (or only ones you intentionally haven't committed)
- No ` M` or ` D` modified/deleted files

**What flags concern:**
- `[ahead N]` — local commits not pushed
- `[behind N]` — remote has commits you don't have, pull before editing
- Many `??` — likely personal/archive material that shouldn't be in this clone (move to `archive/`)
- Wrong-remote — see `Operations/` (LastingLightAI fossil per IC-023)

---

## 10. Top 10 terminal audit commands

Quick reference for inspecting disk state.

### 10.1. Where am I?

```bash
pwd
```

### 10.2. What's in this folder?

```bash
ls -la                       # all files including hidden, with metadata
ls -la | grep -v "^\."       # exclude hidden
```

### 10.3. Find a file by name (anywhere under a root)

```bash
find ~/Desktop/HAIOS-Main -name "<FILENAME>" -type f 2>/dev/null
find ~/Desktop/HAIOS-Main -iname "*<PATTERN>*" -type f 2>/dev/null   # case-insensitive partial
```

### 10.4. Find files modified in last N days

```bash
find ~/Desktop/HAIOS-Main -type f -mtime -<N> 2>/dev/null | head -50
```

### 10.5. Search file contents (grep recursively)

```bash
grep -rIn "<PATTERN>" ~/Desktop/HAIOS-Main/operations-staging/
# -r recursive, -I skip binaries, -n show line numbers
```

### 10.6. Folder structure (top 2 levels)

```bash
find ~/Desktop/HAIOS-Main -maxdepth 2 -type d | sort
```

### 10.7. Folder structure (full tree, with sizes)

```bash
du -sh ~/Desktop/HAIOS-Main/*/ 2>/dev/null | sort -h
```

### 10.8. Edit a file (terminal editor)

```bash
nano <FILE>             # simple, Ctrl-O save, Ctrl-X exit
# or
vim <FILE>              # if you know vim
```

### 10.9. Create a file with content from clipboard (macOS)

```bash
pbpaste > <FILENAME>           # paste clipboard contents into a new file
pbpaste >> <FILENAME>          # append clipboard to existing file
```

### 10.10. Compare two files

```bash
diff <FILE_A> <FILE_B>
diff -u <FILE_A> <FILE_B>      # unified format, easier to read
```

**Bonus — view a file without opening editor:**

```bash
cat <FILE>                     # whole file
head -50 <FILE>                # first 50 lines
tail -50 <FILE>                # last 50 lines
less <FILE>                    # paged view, q to exit
```

---

## 11. Closing rituals

End of every session:

- [ ] **Phase 3 declaration captured.** AI submitted scores via assess.html, or you paste the URL manually.
- [ ] **WGS log posted.** Single Slack message to `#wgs-sync` (`C0AND66PT7U`) with session ID, work completed, Z3 ledger if applicable, carry-forward items.
- [ ] **HAIOSCC Z3 items closed.** Each Z3 item the session resolved gets marked closed in HAIOSCC. Only Night closes Z3 items.
- [ ] **Financial Command Center updated.** Verify and update the Google Sheet (link in memory) at close of every session.
- [ ] **Credentials cleared.** If any tokens were used, confirm Keychain only. Clear shell history if it captured credential material: `history -c` (zsh).
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

CARRY-FORWARD
• <item> — reason: <why deferred>

NEXT SESSION FOCUS
• <next priority>

:eagle: Wado · S-<SESSIONID> · Night
```

---

## Changelog

- 2026-05-01 (S-050126) · v0.4 — Version bump only. Captures lessons from S-050126 commit attempt: (a) heredoc transfer method is fragile against whitespace; chat-UI download is more reliable; (b) markdown rendering in chat UI can display `.md` filenames as auto-linked, but actual downloaded files are clean — verify via `head -N` of the file, not via chat display; (c) before any push, always confirm the GitHub repo exists with `gh repo view <org>/<repo>` — local clone existence does not imply remote existence; (d) S-050126 was the first session where humanaios-ui/humanaios-internal repo was created on GitHub; prior local commits had never pushed.
- 2026-05-01 (S-050126) · v0.3 — Section 7 rewritten with correct Vite/Cloudflare context. Confirmed via disk audit: lasting-light-ai is a Vite + React project with Cloudflare Pages building on deploy. dist/ is gitignored; never edit. public/ is the source of truth for static assets. Local npm run build is not required before push. Section now includes special-folder warnings (.well-known/, _redirects), build-on-deploy explanation, and corrected verification timing (30-90s for Cloudflare build).
- 2026-05-01 (S-050126) · v0.2 — Added Section 7 (Recipe — Add file from Downloads to lasting-light-ai/public). Renumbered later sections: RAH bounty pull → §8, git status across repos → §9, top 10 audit commands → §10, closing rituals → §11. No content changes to existing sections.
- 2026-05-01 (S-050126) · v0.1 — File created. Drafted from operator request: a single copy-paste reference for session open/close, repo structure, memory map, common terminal recipes. Located in `humanaios-internal/` per Reading B (private repo, version-controlled, local mirror). Not governance, not protocol — operator-personal.
