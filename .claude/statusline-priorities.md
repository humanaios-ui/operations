# Statusline Priorities — empirica-outreach

**Practice:** outreach  
**Updated:** 2026-08-04  
**Role:** Ecosystem practice (publishing, engagement, external comms)

## Priority Indicators (High → Low)

1. **Publishing pipeline status** — Draft, review, publishing, published
   - Reason: Outreach work is pipeline-driven; need to know state
   - Display: `pipeline: 2 drafts | 1 in-review | publishing…` | `all published`

2. **Engagement metrics** — Feedback pending, responses, engagement signals
   - Reason: Outreach is feedback-driven; know what's awaiting input
   - Display: `engagement: 3 awaiting | 5 new responses` | `engagement: quiet`

3. **Branch & staged changes** — Current branch, files ready to commit
   - Reason: Publishing often involves batch commits; track readiness
   - Display: `outreach↔main | 4 staged, 1 modified` | `ready to ship`

4. **Transaction phase** — PREFLIGHT | NOETIC | CHECK | PRAXIC | POSTFLIGHT
   - Reason: Publishing discipline (planning → execution → measurement)
   - Display: `[praxic]` | `[check →]` | `[postflight]`

5. **Calendar / scheduling** — Any content scheduled for publish?
   - Reason: Time-sensitive outreach needs visibility
   - Display: `scheduled: 1 (3 days)` | `scheduled: none` | `publishing today!`

## Optional (Lower Priority)

- Context / token budget
- Inventory of drafted pieces (secondary to pipeline state)

## Feedback Notes

- Publishing state is **critical** — show pipeline counts prominently
- Engagement feedback should be actionable (pending + new = total attention needed)
- Staged changes: show count; full diff only on demand
- Schedule visibility helps with coordinated releases
- Refresh: 5000ms good; can increase to 10000ms during writing phases (less jarring)

---

*This file evolves as the practice reports what works. Modify freely; changes auto-surface to statusline script on next refresh.*
