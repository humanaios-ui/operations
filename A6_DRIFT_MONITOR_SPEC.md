---
doc_id: HAIOS-OPS-007
title: A6 Drift Monitor Specification
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-08-15
retention: permanent
---

# A6: Drift Monitor Specification

**Timeline:** Aug 19+, 2026 (deferred after A4-A5 complete)  
**Owner:** mesh-support + autonomy (empirica loop integration)  
**Goal:** Catch divergence between registry + filesystem in real-time (or near-real-time).

---

## The Problem A6 Solves

The S070126 audit was a one-time cleanup (T0-T3). Without a **standing monitor**, divergence re-accumulates silently:

| Event | Without A6 | With A6 |
|-------|-----------|---------|
| A doc is edited out-of-band in `_inbox/` | Invisible for 6+ months | Detected in next biweekly scan |
| A doc's external link dies | Invisible for 6+ months | Detected in next scan, issue filed |
| A doc is moved/deleted without registry update | Invisible for 6+ months | Detected, registry updated |
| A doc passes `review_due` without approval | Owner doesn't know | Escalation issue filed to CODEOWNERS |

A6 **makes the audit a sensor, not a periodic event.**

---

## Drift Monitor Algorithm

**Runs biweekly (every 14 days) on a schedule:**

### Phase 1: Scan All Repos
1. Clone/fetch all 5 repos
2. For each document in `registry.yaml`:
   - **File check:** Does canonical file exist at canonical_path in canonical_repo?
   - **Content check:** Compare hash(file) vs. hash(last_known) from registry
   - **Metadata check:** Last git commit date vs. registry's recorded date
   - **Approval check:** If `review_due < today`, flag as stale

3. For each `_inbox_files*/`:
   - **Unregistered files:** Are there new files not in registry?
   - **Orphans:** Are there files that were supposed to be moved to canonical but still sit in inbox?

### Phase 2: Diff Against Last Run
- Compare scan results to previous biweekly scan
- **Novel drift:** Issues that appeared since last scan (only report new findings, not recurring ones)
- **Resolved drift:** Issues that were already there last time (suppress repeat noise)

### Phase 3: Emit Report + Issues

**Report format:**
```
Drift Monitor Run — 2026-08-19
Repos scanned: 5
Documents checked: 67
Novel issues: 3

ISSUES:
1. HAIOS-RES-005 (REGISTERED.md) — last commit 2026-06-24, now 2026-08-19 (56 days old, outside review_due)
   → Action: Owner @humanaios-ui/operations review for staleness, re-approve or mark superseded

2. HAIOS-WEB-002 (lumina-tide-pool.html) — external link broke (lychee: 404 https://example.com/old-path)
   → Action: Check if resource moved; update link or mark document stale

3. inbox_files2/MYSTERY_REPORT.html — unregistered, 12KB, inbox-only (not in any repo)
   → Action: Gate 4 needed: classify, assign doc_id, merge into canonical or exclude

RESOLVED (from last run):
- HAIOS-COLLAB-003 (Berlin_Advisory.html) → merged inbox → repo 2026-07-15, re-approved ✅
```

**GitHub issues auto-created:**
- One issue per area (owner: CODEOWNERS group)
- Title: "Document drift detected: [area] ([count] issues)"
- Body: Links to docs, recommended actions
- Label: `document-control/drift`
- Auto-close if resolved in next scan

---

## Drift Categories (What Gets Flagged)

| Drift Type | Detection | Action |
|-----------|-----------|--------|
| **Link rot** | External URL returns 4xx/5xx | Fix link / mark doc stale / check if resource moved |
| **Stale doc** | `review_due < today` + `status==approved` | Owner re-reviews + re-approves (or supersede) |
| **Missing file** | Registry says canonical path exists, but file is gone | Find + restore, or mark `superseded` |
| **Diverged copy** | Inbox copy exists after being "moved" to canonical | Move to archive or reconcile upstream |
| **Unregistered** | File in `_inbox_files*/` not in registry | Classify + register (gate 4) or exclude |
| **Orphaned binary** | Binary file listed in registry but excluded from CI | Update schema to skip or re-classify |
| **Registry mismatch** | Registry says `canonical_repo=X`, but file is in repo Y | Update registry or move file |

---

## Implementation Layers

### Layer 1: Script (`operations/scripts/drift_monitor.py`)
- Scans all repos
- Compares against last-run state (cached in `.doc-control/drift_state.json`)
- Emits report + diffs
- Runs locally (manual `python3 drift_monitor.py`) or via GitHub Actions

### Layer 2: Empirica Loop Hook (Optional)
- Integrate with autonomy's empirica loop (See `/empirica-constitution`)
- Hook: `cortex_finding_log` emits findings from drift report
- Auto-promotion: findings with confidence ≥ 0.8 → cross-org visibility (empirica-foundation practices can see humanaios doc health)

### Layer 3: GitHub Actions Workflow
- Scheduled: `cron: "0 2 * * 1"` (2 AM every Monday)
- Runs drift_monitor.py
- Creates issues for novel drift
- Posts summary to Slack (optional)

---

## Success Criteria (End of A6)

- ✅ Drift monitor script written + tested on historical registry
- ✅ GitHub workflow active (`.github/workflows/drift-monitor.yml`)
- ✅ First run complete: zero false positives, all issues traced to root cause
- ✅ Issues auto-created + auto-closed when resolved
- ✅ Area owners responsive to drift alerts (turnaround ≤ 5 business days)
- ✅ Mean time-to-detect drift < 1 monitor cycle (14 days max)

---

## Monitoring the Monitor

A6 itself needs health checks:

| Metric | Target | Check |
|--------|--------|-------|
| Scan time | < 5 min (all 5 repos) | GitHub Actions log |
| False positive rate | < 5% | Triage issues, count "non-actionable" |
| Detection latency | < 14 days | Compare issue date vs. actual divergence date (git blame) |
| MTTR (mean time to resolve) | < 5 business days | GitHub issue close date vs. open date |

If a metric misses target, review A6 configuration (e.g., is lychee too strict? Are review_due thresholds realistic?).

---

## Phase 6: Transition to "Continuous Control"

Once A6 runs stable for 2+ cycles, Phase 6 (ratchet) promotes advisory checks to errors:
- Vale warnings → errors (prose style enforced)
- External link checks → errors (not just warnings)
- Cross-repo control uniform (all 5 repos use same standards)

By this point, divergence is caught at commit time (CI) + between commits (drift monitor). The S070126 scenario (71 diverged pairs hidden for months) becomes structurally impossible.

---

## Runbook: Responding to Drift Issues

**When you receive a `document-control/drift` issue:**

1. **Read the issue:** What drift was detected? Which doc? Why?
2. **Classify the action:**
   - **Link rot:** Can you fix it? Update link in canonical + re-approve. Can't fix? Mark doc `superseded`.
   - **Stale doc:** Review current content. Still accurate? Re-approve. Obsolete? Mark `superseded`.
   - **Missing file:** Check git log. Was it deleted intentionally? Mark `superseded`. Accident? Restore from history.
   - **Unregistered file:** Run intake pipeline gate 4 (register + place). Or exclude if it's config/code.
3. **Action:** Make the fix (edit doc, update registry, etc.)
4. **Confirm in issue:** Comment "Fixed via PR #XYZ" → issue auto-closes next scan if resolved
