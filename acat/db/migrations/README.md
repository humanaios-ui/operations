## Pre-migration checklist for CHECK constraints on existing columns

Before adding any `CHECK` constraint to a column that already has data:

1. Run `SELECT DISTINCT <column> FROM public.<table> WHERE <column> IS NOT NULL ORDER BY 1;`
2. Compare all distinct values against your proposed enum.
3. Any value not in the enum must be either:
   a. Added to the enum (if semantically valid), or
   b. Backfilled/normalized before the constraint is applied.
4. Document the inspection result in a comment at the top of the migration file.

Failure to do step 1–3 is the IC-032 pattern.
