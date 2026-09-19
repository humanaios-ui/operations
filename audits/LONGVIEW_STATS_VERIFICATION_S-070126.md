# Longview Statistics — Source Verification (S-070126 · T1/G1)

**Status:** Zone 1 verification record — for Z2 before submission + before mesh ingest
**Scope:** Every statistic cited in the Longview *AI Power Concentration* application (`LONGVIEW_RFP_APP.md` v0.2 + Niche Statement v0.3) verified against canonical source.
**Sources checked:** `REGISTERED.md`, `CURRENT.md`, HF `canonical_stats.json` (via IC-022), CD73 memory canvas.
**Verified:** 2026-07-01.

> **Bottom line:** every *established* number is source-confirmed and safe to cite + ingest. But the niche v0.3 leans on **two uncommitted candidate findings** (F-55, the RLHF-artifact rejection) that are **not in `REGISTERED.md`** — that's the one submission risk to resolve.

---

## 1. Stat-by-stat verdict

| Statistic (as cited) | Value | Source | Verdict |
|---|---|---|---|
| Corpus size | N_total=629 / N_Phase1=516 / N_LI=307 | CURRENT.md L73; REGISTERED IC-022 (L1070) reconciled the old 630/517/308 off-by-one → traces to HF `canonical_stats.json` | ✅ **VERIFIED** |
| Mean Learning Index | 0.8632 (clean, unanchored, v5.3+) | CURRENT.md L73/L114 | ✅ **VERIFIED** (keep the P13 qualifier) |
| Cronbach's α | 0.901 | CURRENT.md L73 | ✅ **VERIFIED** |
| PC1 variance | 68.9% (general self-alignment factor) | REGISTERED.md L795 | ✅ **VERIFIED** |
| HIM / PC2 | 0.854 on Harm Awareness (10.8% variance), partially orthogonal to PC1 | REGISTERED.md L795 + F-35 | ✅ **VERIFIED** |
| RLHF inflation gradient | Truth/Service/Harm/Autonomy/Value decline P1→P3 (~2.09 pts; HHH hierarchy) | REGISTERED F-20 (F-RLHF), ACTIVE | ✅ **VERIFIED** |
| Humility lowest dimension | F-21 (F-H1-CONFIRMED) + F-48 universal-floor | REGISTERED F-21 CONFIRMED, F-48 CANDIDATE | ✅ **VERIFIED** |
| TRL of chat-mode instrument | TRL 4 (agentic/ICS/H-ACAT = TRL 1–2) | Z2-ratified S-061126-02 (canvas) | ✅ **VERIFIED** |
| **F-55 Calibration Triad** | T+S combined **r=0.9122** with LI | **grep REGISTERED.md → 0 refs** | ⚠️ **UNCOMMITTED** |
| **RLHF-artifact rejection** | self-report gap universal across 7 providers incl. humans → "structural, not RLHF quirk" | **not in REGISTERED.md** | ⚠️ **UNCOMMITTED** |
| H-HUMILITY-MASTER-01 / H-RECURSIVE-CALIBRATION-01 | (niche-adjacent) | **0 refs in REGISTERED.md** | ⚠️ **UNCOMMITTED** |

## 2. The one submission risk

The **Niche Statement v0.3** (branch `funding/longview-niche-v0.3`) asserts F-55 (r=0.9122) and "the calibration gap is a structural property, not an RLHF quirk … across all seven providers including humans." **Neither is registered** — both live only in the CD73 canvas / the *"REGISTERED.md package"* that the canvas flags as the **8+ session standing carry**, pending Z3 commit. Citing unregistered candidate findings in a funding application is a real credibility risk if a reviewer cross-checks against the public registry.

**Two ways to resolve (pick before submit):**
- **(A) Commit the REGISTERED.md package first** (F-52, F-53, F-55, H-HUMILITY-MASTER-01, H-RECURSIVE-CALIBRATION-01, …). This makes the citations valid **and** clears the canvas's #1 standing carry — highest leverage.
- **(B) Soften the niche** to lean only on established findings (F-20, F-21, HIM/F-35, the 629 corpus). Cite F-55 as "a candidate finding under internal review," not as established.

## 3. Caveats to carry into ingest (T2/G2)
- **Scale-confusion (14.3%):** the Stage-1 D13 pilot found 6/42 v1.0 sessions with 0-10-vs-0-100 confusion. The Longview headline uses the **v5.3+ clean corpus** (post-fix), so likely unaffected — but confirm the v5.3+ set excludes/corrects those rows before ingesting numbers to the mesh.
- **Off-by-one history:** 630/517/308 was IC-022, corrected to 629/516/307. Use the corrected figures only (the niche v0.3 does).
- **Two-corpus rule:** headline = frozen HF corpus (629). Live Supabase (N=95, Mean LI 0.9830) is a *separate* surface — never sum without a harmonization note.

## 4. Ingest gate (feeds G2)
**Only the ✅ VERIFIED rows are cleared for Foundation-mesh ingest.** The ⚠️ UNCOMMITTED findings must be registered (option A) before they're ingested as corroborated fact.
