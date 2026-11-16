# Passing-task cohort

**Status:** owner-approved default, pending Night ratification.
Not a freeze. Not Z2 ratification. No live run and no spend.

This generator does not edit `task()` or `schedule()`. The 24 calibration
ids and the 120 holdout ids are unchanged. Holdout schedule sha256 remains
`c61876d8f98a84b9561293f7a53f89fecde9764ae77bf2efd7085f22fffaec05`.

## Sizes

12 valid + 12 invalid calibration tasks, and 20 valid + 20 invalid holdout
tasks. **Size claim: feasibility, not power.**

## 7/7/6 margin disclosure

Twenty valid families are not divisible by three. The valid-margin split is
**7/7/6**:

- 7 families at `T + 0` (boundary, valid)
- 7 families at `T + 1`
- 6 families at `T + 8`

The far-margin cell (`d = 8`) has **six** families, not seven. That cell is
disclosed. It is not dropped and it is not silently rounded.

## Reported-net sibling shift

Offsets are `-3`, `0`, and `+3`. The invalid sibling of a family uses the
next offset, so validity is not encoded by giving both siblings the same
reported net.

## Seeds

Calibration families start at `8100000`. Holdout families start at `8200000`.
They are disjoint from the 24 calibration seeds, the 120 holdout seeds, the
`harness_shared_mistake` SE-0 band (around 20000, n up to 999), and the
#1241 SE-0 band at `7000000` / `8000000` for n up to 100000.

A #1241 SE-0b schedule with n greater than 100000 would reach `8100000`.
No such size is proposed. The bases above are kept because they were the
owner-approved defaults. That residual is recorded here rather than
renumbered.

## Plumbing

Agreement of `harness.violates()` and `oracle_independent.fails()` is
plumbing only. It does not replace the blank human hand-check on the oracle
worksheet.
