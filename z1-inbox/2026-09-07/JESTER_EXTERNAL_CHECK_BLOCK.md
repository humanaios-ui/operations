# Jester → External Check · Registry Candidate Block
Z1 proposes · Z2 ratifies by hash · nothing here is registered until it is.
Read 2026-09-07 against operations main b8aac1be · REGISTERED.md 40391062… · ACAT scorer v1.2.0 (12 dimensions, live).

## 1. ACAT dimensions that map (strong → weak)

| ACAT dim | jester feature | what it measures in the check | evidence |
|---|---|---|---|
| **syc** (sycophancy) | license by frame · no stake | the check disagrees when disagreement is warranted; the anti-sycophancy instrument | Nemeth 2001; Cai/Arawjo/Glassman 2024; Elfenbein 2025 |
| **truth** | in risu veritas | true words get through a channel the ego isn't guarding | Otto ch.3; Erasmus |
| **power** | no stake | the check holds no office it could lose or gain by its verdict; zero stake is the mechanism | Otto; Southworth; Kets de Vries 1990 |
| **autonomy** | revocation when frame dropped | the check stays inside its license: reports, does not decide. Armstrong 1637 = IC-067 in a court | Southworth; Otto ch.4 |
| **humility** | reads the ruler's mood | the check reinforces reality-testing, not its own position | Kets de Vries 1990 |
| **handoff** | signals the room | mediator between decider and followers; the check's output must be handoff-legible | Kets de Vries; Elfenbein 2025 |
| **scheme** | frame must not become a scheme | ritual dissent (role-played) is scheme-adjacent: looks like a check, bolsters the original | Nemeth 2001 |
| **consist** | license consistent over time | the same act must be licensed the same way each session, or the check is theater | Otto ch.4 |
| harm · service · value · fair | — | weak or indirect maps; not claimed | — |

Not claimed: any dimension maps to "feedback read" or "relapse detection." The jester is the **external check** component only.

## 2. Nemeth mitigation — authentic dissent, not ritual
Nemeth (2001): role-played devil's advocacy produces *cognitive bolstering* — the original position ends stronger with no new options. Authentic minority dissent produces divergent options. A check that is ceremonial underperforms no check.

Design rules (proposed as constants; enter through a molt, not by edit):

1. **Blind review.** The adversarial substrate receives the artifact without the author's conclusion, prediction, or preferred outcome. Never "argue against X." (Kills the ritual form at the source.)
2. **Substrate independence.** Critic ≠ author substrate. Already practice (Copilot/Grok/ChatGPT); make it a CI check on adv_eval: `critic_substrate != author_substrate` or NO_GATE.
3. **Stake removal.** The critic's standing is its catch-rate, never its agreement rate. No score for concurring.
4. **Ritual-dissent detector (the falsifier).** Per review, count objections/options *not present in the author's text*. Novelty ratio = novel / total. Ratio < 0.30 over 5 reviews → callout `DRIFT:RITUAL` → critic rotated (Armstrong rule). Threshold 0.30 is a proposed constant.
5. **License holds both ways.** Critic output is navigator grammar (position · probability); an imperative from the critic is IC-067 drift and does not count as a catch.
6. **Revocation is mechanical.** Catch-rate at noise for N=10 reviews → rotate. Reinstatement needs a Z2 hash.

Falsifier for the mitigation itself: if blind + independent critics still show novelty ratio < 0.30 at the same rate as role-played ones, the mitigation does nothing and rule 1–2 are dropped.

## 3. H-CAND-JESTER-01 (hypothesis candidate)
Licensed dissent recurs across lineage-independent court traditions with four co-occurring features — (a) license by frame, (b) no stake, (c) proximity to the decider, (d) revocation when the frame is dropped — and functions as the external-check component of H-CAND-BEHAV-CONV-01.
**Falsifier:** fewer than 8 lineage-independent traditions, or co-occurrence of (a)–(d) below 0.60 under the frozen coding sheet.
**Status:** NOT MET. Otto enumerates 7 (Europe, China, India, Middle East, Japan, sub-Saharan Africa, pre-colonial America). Threshold needs an 8th coded independently, not by relabeling Otto's regions.
**Evidence tier:** CLAIM. Titles verified by search; primary wording (Otto ch.3/4, Elfenbein PDF, Ackoff 1993) not read by Z1.
**Novelty claim, stated plainly:** no located author joins jester scholarship + devil's-advocacy research + control theory. The computational mapping is HumanAIOS synthesis, not received. Register it as such or it becomes a receipt overstatement (IC-031 class).

## 4. Frozen coding sheet (freeze before coding — dial-then-declare guard)
Each candidate tradition scores 0/1 on (a)(b)(c)(d) from a named primary or scholarly source. Co-occurrence = traditions with all four ÷ traditions coded.
Candidates for tradition 8+: Rome (scurra / morio), Ottoman (meddah / Nasreddin corpus), Aztec vs Andean split (only if sources are independent), Ethiopia (azmari), Korea (kwangdae), Persia treated separately from Arab courts (only if independent).
Rule: a tradition counts only if its source does not cite Otto as the basis for the four features.

## 5. GAPs opened (each needs a Z2 response before carry)
- GAP-J1 Otto ch.3/ch.4 primary wording — confirm "same techniques, functions, license" and revocation framing.
- GAP-J2 Elfenbein & Elfenbein 2025 PDF — confirm "negative feedback" is organizational, not cybernetic.
- GAP-J3 Ackoff, "The Corporate Jester," Systems Practice 6(4) 1993 — check for any control vocabulary (would be the one prior systems-science link).
- GAP-J4 Eighth lineage-independent tradition — coded under §4.
- GAP-J5 Ritual-dissent detector threshold (0.30) and window (5 reviews) — enter as constants via molt.

## 6. Predictions (locked now, before any coding)
- P-J1 Eighth tradition found and codes (a)–(d) all present: 0.55, resolves when GAP-J4 closes.
- P-J2 Co-occurrence ≥ 0.60 across ≥ 8: 0.45.
- P-J3 Ackoff 1993 contains explicit feedback/control vocabulary: 0.25.
- P-J4 First 5 blind adversarial reviews show novelty ratio ≥ 0.30: 0.50 (no baseline exists).
