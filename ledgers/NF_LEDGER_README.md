# NF_LEDGER v0.1 — mesh Phase 2 pins (built 2026-09-08, Z1)

Source: PHASE2_PLAN_v0_1.md §3 (LAID; not on main). Main pinned at `efcfcb5`; REGISTERED.md sha `40391062…069029` (IC-030 read 2026-09-08).

| file | sha256 |
|---|---|
| tools/nf_ledger_v0_1.py | 3db6cbb741c4b1c9d58460612384b9b0ff78b928268475b992d9fa1768a958d4 |
| ledgers/mesh_pins_090826.json | 7e4b0f8b06ed5a0218e453d522f04ee2567b26d27debd32ba874cc2faa8b50e9 |
| ledgers/NF_LEDGER.jsonl (165 events) | b68a6fb8de43fef1c1824847f85ee2116a60b80a00f511bd56d8f02121f87a47 · head `9f0bd7e0…6eff3` |

## Counts (reported, not rounded)
- Tokens: **58** = 37 practice-dated + 21 Z1-proposed dates (`PENDING_Z2_DATE`). 2 of the 37 are HumanAIOS additions (Admiral approval Sep 6; first intake batch Sep 19).
- The plan header said "31 dated"; §3 enumerates 37. Count inconsistency in Z1's own document. Logged; candidate IC.
- Pins: 75 Z1 (58 token-level + 15 practice-level + 2 plan-level) · 16 practice self-pins (OA carries two, DISPUTED) · 15 Z2 slots, **all empty**.
- Scoreable now: 48 Z1 pins + 10 practice pins (OA counts twice). The other 21 tokens and 6 practice pins are VOID until Z2 dates or strikes them.

## Mechanical rules in the tool (re-tested at landing: 6/6 refusals, tamper detected)
p outside [0,1] refused · resolve without `--source` refused · resolve on undated token refused · date on Z1-proposed token needs `--by Z2 --hash` · double-resolve refused · any edited line breaks `verify`.

## Owed by Z2 before Sep 12 (in unblock order)
1. Ratification hash for this build (or edits).
2. 15 priors → `P2-<practice>:Z2` pins (currently null; without them LT-2 has no input).
3. Dates for the 21 `PENDING_Z2_DATE` tokens, or `STRIKE`.
4. Resolution of the two tokens already past date: T-empirica-outreach-01 (Admiral approval, Sep 6) and T-grok-crossref-01 (recovery restart, Sep 8) — resolver needs a tree read source.

## Landing receipt (Z1, 2026-09-08, this PR)
- All three file shas re-verified against the draft receipt; spec → ledger round-trip is byte-identical.
- Two corrections to the draft receipt, both receipt-only (IC-031 class, no ledger change): draft listed head `e0efe9aa…` — actual head of the file whose sha it also listed is `9f0bd7e0…`; draft said 9 scoreable practice pins — projection gives 10 (OA's two DISPUTED pins both count).
- Draft said "0/40 unchanged". Operated count at landing is **3/40** (cycles 1–3, z1-inbox/2026-09-08). NF_LEDGER does not add to it: these are pins, not cycles; the first NF resolution with a tree-read source is what counts.
- OPERATED here: verify, status, score (undefined at N=0, reported), 6/6 refusals on a scratch copy. LAID: Oct 4 resolver run; Merkle inclusion of `ledgers/` in the root; Z2's 15 priors.
