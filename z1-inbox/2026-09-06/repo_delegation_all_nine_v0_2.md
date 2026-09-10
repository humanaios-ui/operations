# humanaios-ui — all nine repos → practices · v0.2
Z1 · 2026-09-06 · live tarball read (VERIFIED-LIVE) except two unreadable · candidate for Z2

## Inventory
| repo | files | CODEOWNERS | CI | what it is (from its own README) | owning practice | co-owners (review) |
|---|---|---|---|---|---|---|
| operations | 1,012 | yes (all-Z2) | 26 workflows | governance, tools, registry, site | per-path (v0.1 delegation) | all |
| humanaios | 573 | **none** | — | practice runtime, ACAT sessions, alembic | humanaios | acat-x, QA, LMO |
| lasting-light-ai | 241 | **none** | 2 | public research platform: ACAT, "629 assessments, 31+ agents", HF dataset, arXiv 2503.09618 | **humanaios** (Tier 1) | epistemology (METHODS.md, papers/), website (site/, public/), QA (assessments/ integrity) |
| acat-x | 219 | **none** | 0 | Inspect AI suite, 12 dimensions | **acat-x** | epistemology, QA |
| acat-inspect | 10 | none | 0 | H-INSPECT-01 pre-registered 2026-04-22; results/ present | **acat-x** | epistemology (resolves the hypothesis) |
| research | 14 | none | 0 | frozen-at-publication snapshots | **epistemology** | Z2 gate on any publish |
| ACAT-Dashboard | 26 | none | 0 | Magic Patterns Vite template; src/, team/ | **website** | acat-x (data), collaborator-ops (team/) |
| ACAT-Observatory | ? | ? | ? | unreadable on main/master/develop/dev | ruling needed — likely humanaios or QA | — |
| humanaios-internal | ? | ? | ? | unreadable — private, as it should be | **humanaios-internal** | — |

Gate coverage: CODEOWNERS on 1 of 9 repos. CI on 2 of 9.

## Findings from the read (loud)
1. **Operated evidence exists — for ACAT.** lasting-light-ai's README claims 629 assessments, 516 blind self-reports, 307 Learning Index records, 31+ agents, with a Hugging Face dataset link and an arXiv id. If the HF dataset resolves, that is OPERATED at CLAIM+LINK → VERIFIED on read. The 0/40 count is scoped to the MDU/GRBS intake pipeline and stays 0/40; the record should say which pipeline the count belongs to so the two aren't confused.
2. **acat-x README carries a VOID citation** — `arxiv.org/abs/XXXX.XXXXX` as its own paper link. A placeholder in a public README of the practice whose product is calibration measurement. Also lists eight names under "6 core" dimensions.
3. **ACAT-Dashboard/team/ holds a personal résumé** in a public repo generated from a design template. Whether that's intended exposure is a Z2 call; noting it, not moving it.
4. **research/ README describes four directories; one exists** (datasets/). papers/, supplementary/, corrections/ are absent. The public "frozen snapshot" repo is a README and a folder.
5. **acat-inspect is the cleanest artifact in the org**: hypothesis registered before data, matched-sample design, results/ directory present. Whether H-INSPECT-01 resolved is the first receipt epistemology should pull.
6. **Nine repos, one gate.** A5's rollout plan said "the other 4"; there are eight others.

## Delegation rules across repos (extends v0.1)
- Every public repo gets CODEOWNERS with the owning practice + Z2 on `*`. Z2-only: README status claims, any file asserting counts or results, dataset publication, arXiv metadata.
- Public-facing numbers (629, 0.8632, "31+") are IC-031 territory: each must trace to a dataset hash or a registry line. website practice may not publish a number without one.
- research/ is the record's public face: nothing lands there without a registry entry; epistemology owns, Z2 hashes.
- acat-x and acat-inspect share one practice; epistemology reviews hypothesis registration and resolution in both.
- ACAT-Dashboard: template origin means most of src/ is generated; website owns the shell, acat-x owns any data binding, collaborator-ops owns team/.
- lasting-light-ai is the only repo that touches external audiences with data; it gets a second human reviewer before any other repo does.

## Sequencing
1. Land CODEOWNERS on the five public repos without one (five small files; same team names as v0.1).
2. Pull the HF dataset and check the 629 against it → first cross-repo receipt.
3. Fix or remove the XXXX.XXXXX link; reconcile "6 core / 8 listed."
4. Rule on ACAT-Observatory ownership and on the résumé file.
5. Resolve or mark stale H-INSPECT-01 (registered 138 days ago).

## Falsifier
If the HF dataset does not resolve or its row count is not within 10% of 629, the platform's headline claim is CLAIM only and the site must say so.
