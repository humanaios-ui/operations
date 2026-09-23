# Practice: `website`

**Record:** [`practice.yaml`](./practice.yaml) · **Status:** Z1 CANDIDATE, no Z2 hash
**Zone:** none — `PLANNED_REPOS.md` lists `website` as PLANNED (Phase 1 infrastructure, owner
Night). It holds no Zone ID and therefore no published resource cap.
**Resolution class:** **AMBIGUOUS** — read from `ledgers/PRACTICE_RESOLUTION_MAP.md`

## What it owns

The public presentation surface for HumanAIOS research output: registry-generated practice
profiles rendered as hashed claims, and public-facing analytics on that surface.

## What it may not do

- Ratify any claim it renders. Z2 holds that authority.
- Promote. P8 constrains this practice to attraction — URL only, no calls to action.
- Blur canonical source, derived rendering, and generated explanation. Issue #429 §2 requires
  those three to stay distinguishable on any projection surface.

## Why it is blocked

Four tokens (`T-website-01`..`04`), none resolved. The mesh directory for this practice vendors a
copy of another repository under `operations-repo/`, so "the named repo" does not pick out one
tree. Z2 decision **D1** governs.

`T-website-01` calls for 14 practice profiles. This drop covers 3 and does not satisfy it.

## Open question specific to this practice

An in-tree `site/` directory exists in `operations` (`index.html`, `assets/`, `findings/`).
Whether it is this practice's artifact, a separate operations asset, or a vendored copy was not
determined in this session. It is recorded as an `unknowns` entry and as a `cross_references`
edge, not as an ownership claim.
