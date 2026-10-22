---
id: "F-CAND-SILENT-GATE-BYPASS-S092726"
name: "Merges through non-required-but-meaningful gates leave no in-repo trace"
status: CANDIDATE
class: F
date_registered: "2026-09-27"
date_origin: "2026-09-27"
session_registered: "S-092726-02-gate-bypass"
tags: ["admission-gate", "z2-ratification-gate", "silent-failure", "principle-9", "receipt-gap"]
related: ["F-CAND-PROCESS-VS-PRODUCT-RATIO-01"]
superseded_by: null
source_issue: null
---

# Candidate Block: F-CAND-SILENT-GATE-BYPASS-01 — a real, observed bypass with zero automatic record

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-27
**Status:** AWAITING Z2 RATIFICATION

## Claim

- **claim:** PR #553 merged (2026-09-27T18:37:26Z, `merged_by: humanaios-ui`) with two named checks still `failure` on its final head commit (`67d64a97...`): `Repository admission/backpressure gate` and `Verify Z2 Ratification Requirements`. Confirmed directly: `REPOSITORY_COORDINATOR_POLICY.json` on `main` does not list `553` under `pull_request_numbers`, and the check-run history for both gates shows `conclusion: failure` right up to merge — no late fix, no admission entry landed. Neither check is a *required* status check in branch protection (confirmed empirically across #552/#553/#555 today: `mergeable_state` read `unstable`, never `blocked`, while these gates were red), so GitHub presented no obstruction, no confirmation dialog, and no override flag — the merge button simply worked.
- **class:** Structural gap, not a single incident. This is the general case: any of the repo's "advisory"/non-required checks can be silently overridden by anyone with merge rights, and the only trace afterward is the check-run history itself on GitHub's side — nothing in the repository records that it happened. Contrast with `molt-tier-check.yml`'s `capture` job, which *does* durably record a merge-time signal (claimed-vs-measured tier) into a tracking issue precisely because a per-push comment isn't durable enough on its own. No equivalent capture step exists for the admission gate or the Z2 ratification gate.
- **evidence_tier:** VERIFIED-LIVE — `get_check_runs` on PR #553 at merge time; `REPOSITORY_COORDINATOR_POLICY.json` read directly off `origin/main` same session.
- **detection:** caught by a direct human ask ("check what a bypass looks like") immediately after observing the merge, not by any existing gate or ritual. Nothing in `.github/workflows/` watches for this; nothing in `CLAUDE.md`'s Callout Mandatory Triggers table names it (closest is GAP/RECEIPT-GAP, neither of which fires automatically here).
- **why this matters:** Principle 9 (Open Process and Drift Detection) requires drift to be *named* and corrected, and requires an append-only record of contributions and revisions. A bypass that is only discoverable by manually cross-referencing check-run history against the admission policy is not "named" in any operationally meaningful sense — it's *detectable*, not *detected*. This is the same class of gap as `z2_ratification_gate.yml`'s 122-run silent failure (F-CAND-PROCESS-VS-PRODUCT-RATIO-01): a real-time signal existed, nobody was told.

## Falsifier

This finding is falsified for the underlying risk (not the historical fact, which is already verified) if: after the prevention below is implemented, a full quarter passes with zero merges bypassing either named gate *without* a corresponding ledger entry appearing. If a bypass is later found to have occurred without a matching entry, the prevention has a hole and this should escalate past a single F-finding.

## Proposed correction / prevention (Z2 to accept, edit, or reject)

1. No retroactive action on PR #553 itself — the content that merged (two proposal files in `z1-inbox/`) is low-risk and the bypass was Z2's own prerogative to exercise (`ADMISSION_IS_NOT_MERGE_AUTHORITY` cuts both ways: the gate can't grant merge rights, and merge rights aren't bound by the gate). This finding is about the missing *record*, not about relitigating the merge.
2. Add a new workflow, modeled directly on `molt-tier-check.yml`'s `capture` job (same permission-minimal, non-recomputing pattern — see investigation below), that on every `pull_request: closed` with `merged == true` reads the final conclusion of a small named list of "meaningful but non-required" checks on the PR's head SHA, and — only when at least one was `failure` at merge — posts a comment on the PR and appends one line to a new append-only ledger file, `GOVERNANCE_BYPASS_LEDGER.jsonl`.
3. Keep it advisory, matching every other gate in this repo: it records, it never blocks, and it never invents a merge-time re-measurement (checks its actual last-known conclusion only, exactly as `molt-tier-check.yml`'s capture job copies rather than recomputes, and for the same reason: recomputing at merge time against a possibly-different ruleset would answer a different question than "did this bypass a check that was actually failing when someone merged").

## Z2 Decision Gate

- [ ] ACCEPT — register as F-CAND, assign F-number, proceed with implementation
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

**Awaiting Z2 ratification by:** 2026-09-29 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
