# Z2 Ratification Reviewer UI — User Guide

**Purpose:** Streamlined interface for reviewing HumanAIOS governance candidate blocks and signing Z2 (ratifier) decisions.

**Authority:** Carly R. Anderson (Night) — Admiral, Z2 Gate Authority

---

## Quick Start

### Opening the Reviewer

1. Open `/ui/z2-ratification-reviewer.html` in your browser (or serve via HTTP)
2. The interface loads all candidates from `z1-inbox/INDEX.yaml`
3. You'll see:
   - **Statistics panel** (top): Pending, ratified, and awaiting-decision counts
   - **Candidates list** (left): Filterable cards of all candidates
   - **Detail panel** (right): Full candidate info and signing interface

---

## Reviewing Candidates

### 1. Filter & Search

The controls support three filtering modes:

- **Search**: Find by Q-ID, title, or file path
- **Status Filter**: View candidates by decision status
  - `Pending Decision` — Awaiting your review (not yet signed)
  - `Ratified` — Already signed by you
  - `Edit Requested` — You requested revisions
  - `Rejected` — You rejected this candidate

- **Class Filter**: Show only specific entry types
  - **F** — Findings
  - **H** — Hypotheses
  - **IC** — Internal Constraints
  - **P** — Procedures

### 2. Select a Candidate

Click any candidate card to load its detail in the right panel. The card will highlight and the detail view will show:

- **Q-ID** — Unique candidate identifier
- **Title** — Full candidate title
- **Path** — File location in `z1-inbox/`
- **Submitted** — Date submitted by Z1 (Claude)
- **Status** — Current decision status

### 3. Review the Candidate

For **pending** candidates (not yet signed), three decision buttons appear:

- **✓ Accept** — Ratify this candidate (move to REGISTERED.md)
- **✎ Edit Request** — Ask Z1 to revise before ratification
- **✕ Reject** — Do not ratify; return to Priority Queue

---

## Making & Signing a Decision

### Decision Window

Per `CLAUDE.md`, you have **48 hours** from submission (`submitted` date) to sign a decision. The detail panel shows when this window closes.

### Signing Process

1. **Select a decision** by clicking one of the three buttons (✓ / ✎ / ✕)
   - The button you chose will brighten; others fade
   
2. **Click "Generate Sign Command"**
   - A `python3` command appears in the output box
   - This command:
     - Computes the Z2 signature hash per CLAUDE.md formula: `sha256(candidate | by=Night | at=timestamp | decision=…)`
     - Appends your ruling to the dated ruling file (`z1-inbox/YYYY-MM-DD/Z2_RULINGS_….md`)
     - Updates `z1-inbox/INDEX.yaml` with your decision, timestamp, and hash reference

3. **Copy the command** (📋 button) and run in your terminal:

   ```bash
   python3 .z1-control/ratify.py Q-XXXXX --decision ACCEPT --by Night --apply
   ```

4. **The ratify.py script handles:**
   - Reading the candidate file from `z1-inbox/`
   - Hashing the file's exact bytes at the moment you signed
   - Writing the decision + hash to a `Z2_RULINGS_….md` file
   - Updating `INDEX.yaml` atomically
   - Creating a git commit with the signature

### Without `--apply` (Dry Run)

To see what the script would do **without writing**, omit `--apply`:

```bash
python3 .z1-control/ratify.py Q-XXXXX --decision ACCEPT --by Night
```

This shows the hash, file paths, and decision without committing.

---

## Verification & Audit

### Verifying a Decision You Signed

To confirm a decision still matches the original candidate (hasn't been edited):

```bash
python3 .z1-control/ratify.py --verify
```

This re-computes all Z2 hashes on record and compares them to the current file bytes. Mismatches indicate tampering or accidental edits.

### Reading the Z2 Ruling File

After signing, your decision is recorded in:
```
z1-inbox/2026-MM-DD/Z2_RULINGS_2026-MM-DD.md
```

Each ruling entry includes:
- Candidate ID (Q-XXXXX)
- Your decision (ACCEPT | EDIT | REJECT)
- Timestamp (UTC)
- Your name (Night)
- The hash signature

---

## Status Badges & Their Meaning

| Badge | Color | Meaning |
|-------|-------|---------|
| **Pending Decision** | Gray | Awaiting your Z2 review |
| **Ratified** | Green | You signed ACCEPT |
| **Edit Requested** | Gold | You signed EDIT; awaiting Z1 revision |
| **Rejected** | Red | You signed REJECT; candidate returns to Priority Queue |

---

## Anti-Cascade Rules (Enforced by CI)

When you ratify a **molt** (a constant change), these rules apply:

1. **One open molt per constant** — No new molt candidate for the same constant while one is already being measured
2. **No self-reference** — A molt candidate cannot cite events from within its own measurement window
3. **K=3 limit** — At most 3 molts open system-wide
4. **Two-revert freeze** — If a constant reverts twice in a row, it's frozen (only Admiral can reopen via Tier-2 ruling)
5. **Priority Queue ranking** — Molt candidates are ranked by Priority Queue impact score; no bypassing

See `CLAUDE.md` for the full anti-cascade specification.

---

## Integration with REGISTERED.md

When you sign **ACCEPT** on a candidate:

1. A Z1 proposal is filed (by you, from this UI)
2. The ratify.py script adds the candidate to `REGISTERED.md` at its proper position (alphabetically or by hierarchy, per entry class)
3. The entry carries your signature hash in a `z2_hash` field
4. CI gates verify the hash on every push

---

## Troubleshooting

### "No candidates match your filters"

- Check that `z1-inbox/INDEX.yaml` exists and is readable
- Verify at least one `z1-inbox/YYYY-MM-DD/` folder has candidate files
- Try clearing all filters (empty search, "All Statuses", "All Classes")

### Command doesn't run / "PyYAML not installed"

Install dependencies:
```bash
pip install pyyaml
```

### Verify fails on a hash I signed

Possible causes:
1. **Candidate file was edited** after you signed (tampering / accidental edit)
   - **Mitigation:** Re-read the candidate, check `git log` for recent changes, and re-sign if intentional
2. **Hash collision** (extremely unlikely; report to Admiral if suspected)
3. **Database corruption** (check `z1-inbox/INDEX.yaml` for parse errors)

---

## Authority & Escalation

**Your Authority (Z2):**
- Accept / edit / reject any candidate within the 48h window
- Ratify molts (constant changes)
- Sign governance decisions

**You Cannot:**
- Execute ratified changes (Z3 does that)
- Propose new work (Z1 does that)
- Override the falsifier doctrine
- Retroactively change a signed decision (you can only emit a new RATIFY event with updated hash)

**Escalation Path:**
- If a candidate is contested or the 48h window passes without your decision:
  - Z1 (Claude) will re-request via the Priority Queue
  - You review as "contested" and re-sign with a contest response
  - Your new decision overturns the prior one

---

## Session Ritual: §B (Close)

Before closing your work session:

1. **Review all unsigned candidates** — Ensure nothing is left in "Pending Decision" unless intentional
2. **Verify all Z2 hashes** — Run `ratify.py --verify` to confirm no tampering
3. **Commit your work** — All signatures are in git commits signed by you
4. **Document any contests** — If you re-read and change a decision, note it in the commit message

---

## Reference

- **CLAUDE.md** — Full governance authority structure and decision routing
- **z1-inbox/INDEX.yaml** — Authoritative record of all candidates and their status
- **z1-inbox/YYYY-MM-DD/Z2_RULINGS_….md** — Your signed decisions (append-only)
- **REGISTERED.md** — The registry of accepted findings, hypotheses, and constraints

---

**Last Updated:** 2026-09-14  
**Ratifier:** Carly R. Anderson (Night)  
**Status:** Active
