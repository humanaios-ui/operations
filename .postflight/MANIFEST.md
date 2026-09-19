# POSTFLIGHT Data Navigation Guide

**Purpose:** You have a question. This guide tells you which file answers it.

**Status:** Holographic efficiency layer — 7 sessions aggregated into queryable master + individual session files

---

## Quick Navigation

### Vector Trends & Patterns
**→ `INDEX.yaml` → `vector_trends` section**
- All 13 epistemic vectors with trends across 7 sessions
- Interpretation of what each trend means

### Decisions Due for Review
**→ `INDEX.yaml` → `decisions_timeline.decisions_due_for_review_within_30_days`**
- Pre-sorted by urgency
- Shows which decisions need review soon

### What's Blocking Progress?
**→ `INDEX.yaml` → `goals_health.top_blocker`**
- Critical blockers affecting multiple goals
- How many goals each blocker affects

### Mesh Coordination Health
**→ `INDEX.yaml` → `mesh_health.practice_responsiveness`**
- Response time per practice
- Reliability score
- Status (EXCELLENT/GOOD/NEEDS_ATTENTION)

### Complete Session Details
**→ `.postflight/YYYY-MM-DD/session.yaml`**
- All artifacts (findings, unknowns, assumptions, dead-ends)
- Complete goal progress
- Mesh communication details
- Decision context

---

## Files Structure

```
.postflight/
├── INDEX.yaml                   ← Master: See all patterns
├── MANIFEST.md                  ← This file
├── YYYY-MM-DD/session.yaml      ← One file per session date
└── _rollups/                    ← Weekly aggregations (coming)
```

---

## Reading Pattern

1. **Quick answer?** → Read INDEX.yaml (1 minute)
2. **Need session detail?** → Read specific session.yaml (2-5 minutes)
3. **Trend analysis?** → Read vector_trends in INDEX.yaml (5 minutes)

---

For more guidance, see the full POSTFLIGHT_MANIFEST.md in the documentation.
