# B2 — Organ Coverage (bio_framework)

**Module:** `bio_framework_distributed_v1_2.py` (extension over core v1.2, no core changes).

Adds the two shapes the Phase-3 mapping (§5, §7, §8.2) flagged as having **no clean single-owner model** — the reason "organ coverage" wasn't just enumeration.

## New shape 1 — `DistributedFunction` (the mapping's "big finding")
A Western unified system with **no single Eastern owner**; responsibility is
**broadcast/assembled** across multiple Zang. Implemented for the **nervous
system = Wu Shen**:

| Spirit | Zang (Element) | Facet | Vitality substrate |
|--------|----------------|-------|--------------------|
| Shen | Heart (Fire) | consciousness | `shen` |
| Hun | Liver (Wood) | emotional/ethereal | `blood` |
| Po | Lung (Metal) | corporeal/reflexive | Metal qi |
| Yi | Spleen (Earth) | thought/intellect | Earth qi |
| Zhi | Kidney (Water) | willpower | `jinye` (jing proxy) |

- **`assemble()`** — coherence is a *weighted* mean of the five facet vitalities, with the coordinator (Heart/Shen) weighted heavier ("Heart as emperor"). Each Zang keeps single ownership of its resource; the nervous function is the aggregate — exactly the shared/broadcast partition the mapping described.
- **`broadcast()`** — a system-level signal reaches *all* facet-holders (pub/sub), not one node.
- Validated: losing the **coordinator** (Heart/Shen) hurts coherence more than losing a **peripheral** facet (Zhi) — and no single loss zeroes the system (distributed resilience).

## New shape 2 — `SanJiaoCoordinator` (the full orphan)
San Jiao (Triple Burner): no Zang pair, no anatomical correlate. A **cross-zone
coordinator** over shared fluid (`jinye`) passage across upper/middle/lower
burners — models coordination, not organ ownership. Reports flow status +
`San Jiao fluid stagnation` fail-mode below threshold.

## Coverage status
| Mapping system | Shape | Status |
|----------------|-------|--------|
| 5 Zang (Heart/Lung/Liver/Kidney/Spleen) | Organ / Composite | ✅ v1.0–1.2 |
| Liver-Qi, Wei Qi | CrossCuttingRegulator | ✅ v1.0 |
| Jing-Luo meridians | ChannelGraph | ✅ v1.0 |
| Wu Xing cycles | WuXingEngine + typed Signal | ✅ v1.0 / v1.2 |
| Qi / Jinye / Blood / Shen | ResourcePool | ✅ v1.1 |
| **Nervous system (Wu Shen)** | **DistributedFunction** | ✅ **B2** |
| **San Jiao (Triple Burner)** | **SanJiaoCoordinator** | ✅ **B2** |
| Six Fu (bowels) | paired-component (already solved) | ⏭ trivial — follow their Zang |
| Endocrine / Musculoskeletal / Integumentary | DistributedFunction (same shape as Wu Shen) | ⏭ B2-continuation |

**Tests:** Add `bio_framework_distributed_test_v1_2.py` (currently not in this repo) before reporting results here; same for the B1 signal tests.

## Next (B3)
Register the whole organ mapping as a research build (Z2). Then B4: compare the
derived architecture to grounded runtimes (actor/OTP supervision, k8s control
loops) as a validation input.
