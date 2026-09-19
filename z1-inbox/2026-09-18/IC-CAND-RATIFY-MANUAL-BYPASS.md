---
id: "IC-CAND-RATIFY-MANUAL-BYPASS-S091826"
name: "A by-hand signature path (ratify.py --apply) stayed executable for board rulings after Z2 ruled that the merge is the ratification — and d31 plus runbook §4 documented it, until Z2's red-team review of #409"
status: CANDIDATE
class: IC
date_registered: "2026-09-18"
date_origin: "2026-09-18"
session_registered: "session_01CePrSjPSB8Epbpq3Lj8oKj"
zone2_ratification: null
tags: ["governance-bypass", "merge-is-ratification", "z2-gate", "tier-2", "intent-os-board", "IC-030-class"]
related: ["IC-030", "IC-031"]
superseded_by: null
source_issue: "humanaios-ui/operations#409"
---

# Candidate Block: Q-IC-RATIFY-BYPASS-01 — two acts of ratification for one decision

**Z1 Proposer:** Claude (Z1) — transcribing finding 1 of Z2's red-team review (ChatGPT) on #409, 2026-09-18
**Date Submitted:** 2026-09-18
**Pinned SHA:** `06b9813` (main's HEAD, the squash-merge of #408)
**Status:** AWAITING Z2 RATIFICATION

## IC-RATIFY-BYPASS-01

- **claim:** Z2 ruled on 2026-09-18 (`z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`) that a board
  ruling is ratified by merging its pull request, that every ruling PR is reviewed and approved, and that the
  reconcile job records the merger and the merge date as the signature. At `06b9813` the live
  `.z1-control/ratify.py --apply` still accepted any `awaiting_z2` candidate — a board-ruling block included —
  and wrote the ruling file, flipped `INDEX.yaml` to `ratified` and issued a hash with no ruling PR, no review,
  no merge and no reconcile provenance. `Q-BOARD-PUBLISH-01` (d31, as first filed in #409) and runbook §4
  offered that command as a second way to rule. Two valid-looking mechanisms existed for one class of
  decision, one of which bypassed the control Z2 had just established: "all ruling PRs are reviewed and
  approved" was true in prose and false in the tree.
- **class:** governance bypass, IC-030 class (a control adopted from memory of the ruling while the tool that
  could contradict it was left as it was). Adjacent to IC-031: a signature the tree would have verified as
  valid without the act the ruling requires behind it.
- **evidence_tier:** VERIFIED-LIVE — at `06b9813`, `cmd_ratify` in `.z1-control/ratify.py` refuses only an
  unknown ratifier, an unknown q_id and a status other than `awaiting_z2`; d31 at `cc736dd` ("How this gets
  ruled", step 2) and runbook §4 (lines 112–114 at `06b9813`) both print the by-hand command.
- **detection:** Z2's red-team review on #409 — not any gate. `z2_ratification_gate` and `ratify.py --verify`
  check that a signature recomputes; neither asks which act produced it.
- **correction (lands in #409):** `ratify.py --apply` refuses any candidate whose file carries a `## Ruling`
  section with a `choice:` line — the shape `tools/decision_relay.py` writes and
  `tools/intent_os_reconcile_v1_0.py` signs — naming the ruling as the reason. d31, runbook §4 and the INDEX
  note no longer offer the by-hand route; without the relay, a person opens the one-file PR by hand and the
  merge is still the act. `.z1-control/ratify.py` is a GATE path in `tools/molting_protocol_diff_v1_0.py`, so
  #409 measures **Tier 2** by the published rule; this block is the registry entry that tier asks for.
- **prevention (proposed, Z2 to accept or edit):** the reconcile tool's self-test gains a case that
  `ratify.py` on a DECIDED board block exits 1 with the ruling named, so the two tools' contract is tested
  together rather than assumed. Not built here — it touches a gate's test, and the rule for that is Z2's.
- **falsifier:** event-based, no clock. (a) If `python3 .z1-control/ratify.py Q-BOARD-PUBLISH-01 --decision
  ACCEPT --by Night` (a dry run: no `--apply`) exits 0 at any commit on `main` after #409 merges, the guard is
  not in force and the correction claim is false: this block is withdrawn and the bypass re-filed. (b) If the
  same dry run against a candidate with no `## Ruling` section (`Q-IC-BOARD-SEALS-01`) is refused *for the
  board-ruling reason*, the guard over-matches and the correction is wrong the other way. Both are one
  command each, run at the merged tree.
- **status:** OPEN.

## Z2 Review Checklist

- [ ] Register IC-RATIFY-BYPASS-01 as stated (or edit the class / duration)
- [ ] Accept the guard as the correction — a Tier 2 gate change carried in #409 — or ask instead for the
      alternative the review named: a Z2 ruling that keeps a by-hand exception and says how its review and
      provenance requirement is met
- [ ] Accept, edit or refuse the prevention (a cross-tool self-test case)
