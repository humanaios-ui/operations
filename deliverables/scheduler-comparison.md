# Scheduler Comparison — for The Witness Stand

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Decision aid · *verify current pricing/features before you commit — these move.*

**Your needs:** schedule (a) **Substack Notes**, (b) **LinkedIn** (personal + ideally newsletter), (c) **X threads** — all via **official APIs** (ToS-safe), on a solo-operator budget. The long-form Substack *article* is scheduled in Substack's own editor regardless.

---

## The options

| | Substack Notes | LinkedIn | X / threads | Official-API (ToS-safe) | Substack *article* | Notes |
|---|---|---|---|---|---|---|
| **Substack native** | ✅ (schedule + auto-share) | ➖ auto-share on publish only | ➖ auto-share only | ✅ | ✅ **the article scheduler** | Free. Use it for the article + basic auto-share. |
| **Typefully** | ⚠️ limited/none | ✅ | ✅ (thread-native, strong) | ✅ | ❌ | Best for the X thread + LinkedIn text; not Substack. |
| **Buffer** | ❌ | ✅ | ✅ | ✅ | ❌ | Broadest social coverage; no Substack. |
| **Narrareach** | ✅ (Notes via API) | ✅ | ✅ | ✅ (bearer token) | ⚠️ some | The only one claiming **Substack Notes** scheduling. Newer/niche — vet it. |

*(Grounded in current tooling research; feature sets shift — confirm on each site.)*

---

## Recommendation

**Start with the cheapest stack that covers you, add only if needed:**

1. **Substack native** for the biweekly **article** (+ turn on auto-share to X/LinkedIn/Notes). Free, zero setup, ToS-perfect. This alone covers a lot.
2. **Typefully** for the **X thread + LinkedIn** version of each post (its thread composer is the best of the three, official-API, cheap tier). This is where `repurpose.py`'s `x-thread.txt` + `linkedin.md` outputs go.
3. **Only add Narrareach** if scheduling **Substack Notes** in advance becomes a real bottleneck. For now, Notes are cheap to post live (20–30 min/day *is* the growth habit) — don't automate away the one task that most rewards showing up. Vet Narrareach (newer tool, bearer-token model) before trusting it with account access.

**Do not** use any tool that automates LinkedIn *connections/DMs/comments* — official-API *posting* is fine; the rest is a ban risk and off-ethos.

---

## The workflow, end to end
```
post.md (git)
   └─ python3 scripts/repurpose.py post.md
        ├─ substack.md   → paste into Substack editor → Schedule (native)
        ├─ linkedin.md   → Typefully → schedule
        ├─ x-thread.txt  → Typefully → schedule as thread
        └─ notes.txt     → post live 3–5×/week (or Narrareach if you adopt it)
```

**You connect the accounts once (your OAuth); I only ever prepare the content.** Nothing publishes without you.
