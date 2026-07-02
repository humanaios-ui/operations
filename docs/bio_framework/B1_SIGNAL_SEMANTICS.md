# B1 — Per-Component Signal Semantics (bio_framework v1.2)

**Status:** Zone-1 research build. Canonical home: `humanaios/_bio_framework/`.
**Answers the gap:** "what should a received signal actually *do* per component?"

## Canonical reconciliation (resolves Track-3 "pick canonical bio files")
The **Downloads** copy of the core was *newer*, not a stale dup — it had already
split `regulate()` (autonomous per-tick baseline, called once) from a new
`receive_signal()` hook (fired by ChannelGraph/WuXing), fixing the double/triple
-invocation bug. But `receive_signal` was a **no-op** — the actual B1 gap.
Canonical = the reconciled version in this repo → `bio_framework_core_v1_2.py`.
Inbox/Downloads drift for the identical stress tests was moot.

## The design
A received signal now carries its **kind**, so a component responds to *why* it
was reached:

```
Signal(kind, source, strength)
  GENERATIVE — Sheng cycle: mother element nourishes this one   (Wood→Fire)
  CONTROL    — Ke cycle: controller restrains this one          (Wood→Earth)
  CHANNEL    — Jing-Luo meridian: a named connectivity edge fired
```

**Separation of concerns (no double-count):** the `WuXingEngine` moves *qi* (the
resource economy). `receive_signal` is the organ's **functional response** to
being signalled — it touches non-qi resources (shen / blood / jinye) or its
fail-state, never qi again.

## Per-component handlers (biologically faithful)
| Organ | GENERATIVE (nourished) | CONTROL (restrained) |
|-------|------------------------|----------------------|
| Heart (Fire, houses Shen) | +shen (nourished by Wood) | −shen (Water cools Fire) |
| Lung (Metal, disperses fluids) | +jinye (fed by Earth) | −jinye (Fire melts Metal) |
| Liver (Wood, stores Blood) | +blood (fed by Water) | −blood (Metal chops Wood) |
| Kidney/Renal (Water, fluids) | +jinye (fed by Metal) | −jinye (Earth dams Water) |
| Kidney/Marrow (makes Blood) | +blood contrib | −blood contrib |
| **Spleen/Transport (Earth)** | +blood contrib (fed by Fire) | **−blood contrib (Wood overacts on Earth)** |

The bolded Spleen row is the mechanism the **general stress test** narrates
(Liver Qi stagnation → Wood controls Earth → Spleen dysfunction) — which had
**no code behind it** until v1.2, because `receive_signal` was a no-op.

## Validation
Add/restore `bio_framework_signal_test_v1_2.py` (currently not in this repo), or
update this section to avoid claiming "5/5 pass" until the tests exist.
(You can re-list the asserted behaviours once the test file is present.)

## Next (B2)
Organ coverage: the distributed systems (nervous/Wu Shen, endocrine, San Jiao),
the meridian topology, Qi/Jinye layers — each modelled with the three code
shapes + now-typed signal handlers.
