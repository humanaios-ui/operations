# Z1 Inbox — Conversion Index

Rendered from `z1-inbox/INDEX.yaml` (SSOT). **Do not hand-edit — edit the index** and run `python3 .z1-control/render.py`. CI runs `--check`, so the two cannot disagree.

A **candidate** asks Z2 for a decision. A **record** reports, receipts or hands off and asks for nothing. Z2's routine window is **2 days** from submission (CLAUDE.md); `decision_due` is derived from that, not hand-set. Signing is **Night** — `.z1-control/validate.py` refuses any other signature.

**137 candidates** — ⏳ awaiting Z2 3 · ✅ ratified 124 · ⤴️ superseded 2 · ↩️ withdrawn 8 · **97 records**

## Awaiting Z2 (3)

Earliest due first. Anything dated before today is past the window — `.z1-control/validate.py` flags those on every run, and CLAUDE.md routes a closed window to Admiral re-read.

| decision due | candidate | what it asks | block |
|---|---|---|---|
| 2026-09-15 | **Q-DOCREVIEW-01** | The 39 overdue document reviews — lifecycle, not re-dating | `z1-inbox/2026-09-13/Q-DOCREVIEW-01.md` |
| 2026-09-15 | **Q-DOCREVIEW-02** | Findings from the first real document review pass (11 reviewed, 28 unreachable) | `z1-inbox/2026-09-13/Q-DOCREVIEW-02.md` |
| 2026-09-16 | **Q-BOOT-FINDINGS-SCAN-01** | Registry candidate block — post-merge findings scan over Q-BOOT-STATE-MACHINE-01, cross-walked against a live REGISTERED.md fetch | `z1-inbox/2026-09-14/Q-BOOT-FINDINGS-SCAN-01.md` |

## Decided (124)

| decision | candidate | signed by | on | ruling |
|---|---|---|---|---|
| ✅ ratified | **Q-CYCLE3-FALSIFY-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`cycle-3-falsification-approved-20260908` |
| ✅ ratified | **Q-JESTER-CHECK-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-WITCH-CASCADE-01** | Night | 2026-09-08 | `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md`<br>`h-cand-batch-ratified-20260908` |
| ✅ ratified | **Q-INTENTOS-LAUNCH-01** | Night | 2026-09-14 | `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md`<br>`9a2a469be2cbbe1d559b78d0b0fd41d286c21d0313bc61482b906b474f5d3309` |
| ✅ ratified | **Q-INTENTOS-TEST-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`eb568ab4a65efbae21927c646b18be459a0c8de8353d59fe8b4cc451f3ed36ae` |
| ✅ ratified | **Q-MERGE-SCOPE-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`f04b05d31dad3138c47b3875b2104776b3f4a80a65c5d1a376ec50f867dac53a` |
| ✅ ratified | **Q-MOLT-LEDGER-SCAN-01** | Night | 2026-09-16 | `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md`<br>`44276df7c921d87cc388922155eace549f1f57b71134f65422d9be1770859eb2` |
| ✅ ratified | **Q-BOARD-RULING-02** | Night | 2026-09-18 | `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md`<br>`b80131eba24815480dfd83630cfbdd69672fb017bf4e264e081a9a05326f3c6a` |
| ✅ ratified | **Q-BOARD-RULING-14** | Night | 2026-09-18 | `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md`<br>`27c98b653cefe16826fe3b2b76fcfdc822cb87b00a5ce81dc7c256112a7f51eb` |
| ✅ ratified | **Q-BOARD-RULING-03** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`d9205f80f381b99b49f2cd336494e6f313be2688698c06094ed15e4f8514b09c` |
| ✅ ratified | **Q-BOARD-RULING-05** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`b1aeacc4d76a2f5b00e1705376376d051069e46bc2d41391bb15156edb45f2a3` |
| ✅ ratified | **Q-BOARD-RULING-06** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`8eaf5ba86242368b13e3418cbfc327c5149febed788ba2037b134d364a5f832e` |
| ✅ ratified | **Q-BOARD-RULING-07** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`c16c68fc6d746960957e073b4eaaad595f0a8fa768e5f936680902a10814cb3a` |
| ✅ ratified | **Q-BOARD-RULING-08** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`13872d43cf874c4191afdaa49e9c497f15fabfb5a009b0156892a253838d3a35` |
| ✅ ratified | **Q-BOARD-RULING-09** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`0223e63774de313e12b4c2fb48c13605a174caf62ad01d0e3b380fe5c484f4dd` |
| ✅ ratified | **Q-BOARD-RULING-10** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`7c4cebf936c8a4f5769a6569e8a7df0459243dc74bab9915922b4e3e0a69521d` |
| ✅ ratified | **Q-BOARD-RULING-11** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`9851a3b0752090a0b2da32e0a601bf9b49afb3d8c9e302d215e17f15a976ce81` |
| ✅ ratified | **Q-BOARD-RULING-12** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`5b4b235054a9c853be1711b42debd8ab84b003571cca742d60b8d5a478f0f48b` |
| ✅ ratified | **Q-BOARD-RULING-13** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`fa83e8cad90de5979c733e1135369a540a10c164a56c1a05e0da77db8e8dceb6` |
| ✅ ratified | **Q-BOARD-RULING-15** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`9a74fa65d8997015b091773db6f595d6210207a474973c59dd508ca5bd07b7ad` |
| ✅ ratified | **Q-BOARD-RULING-16** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`4222c6c47c77b78f75528559d98ada6358da07dba025a4ea28c533e2152cf531` |
| ✅ ratified | **Q-IC-RATIFY-BYPASS-01** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`e55cc0066e99e6b5ce8a785a1212fd874b5a9ce62c6191a3a4a9702e4cde5ac6` |
| ✅ ratified | **Q-INTENT-OS-WITNESS-LEDGER-01** | Night | 2026-09-19 | `z1-inbox/2026-11-20/Q-INTENT-OS-WITNESS-LEDGER-01-INDEX-RECONCILE.md`<br>`PENDING_NIGHT_REPIN` |
| ✅ ratified | **Q-INTENTOS-BUS-01** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`1ecb7427980c61ac9e10762b93ddee184578181586978f2025559f30da953dd5` |
| ✅ ratified | **Q-INTENTOS-PAGES-GATE-01** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`7295313ceefa43cb87bd44d802ef18c0987d296a0f63ce1c89e1feb76e7d3d7d` |
| ✅ ratified | **Q-INTENTOS-REFRESH-01** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`72af1d74b1e8a35bb7516a05f0032bc45c64e1f967affc4713d5ec27f5fcde4e` |
| ✅ ratified | **Q-PHASE-2-BOARD-MOLT-01** | Night | 2026-09-19 | `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md`<br>`6d6e757732b1f68177467acf9707e5bdf94bcdd8edad97affb36342560fab154` |
| ✅ ratified | **Q-DEFERRAL-RULE-01** | Night | 2026-09-21 | `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md`<br>`d94a4559f1fff11a21077661bd732345c846c7b5c4a3da82f03f0f80b24df7ea` |
| ✅ ratified | **Q-EXTERNAL-JESTER-01** | Night | 2026-09-21 | `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md`<br>`2c45665f54592dce809f5d9fa968fd9fbf47a00aa77941ab57adca69ac25a3bc` |
| ✅ ratified | **Q-GATE-PATHS-TEST-LOGIC-01** | Night | 2026-09-21 | `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md`<br>`9b1f182e3f0b584fe5091808668da927acbf82751e1f3f7b85c0f07cd9a8a1a9` |
| ✅ ratified | **Q-INTENT-GRAPH-01** | Night | 2026-09-21 | `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md`<br>`13c8cf5517180412b4ff60cc2ecdf980150acb22f06f15a8208ee67d6f4d2346` |
| ✅ ratified | **Q-MOLT-TEMPORAL-PURITY-01** | Night | 2026-09-21 | `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md`<br>`ba3072e06803b9b0576b57b554ff9f1e3086e596bc5d444e5a1b0a1ca082497a` |
| ✅ ratified | **Q-A11-ORDERING-INERT-01** | Night | 2026-09-22 | `z1-inbox/2026-09-22/Z2_RULINGS_2026-09-22.md`<br>`10314a8eac5114e3fb217f75543b14b159bcdb9effcee372d52bc544962b7bb5` |
| ✅ ratified | **Q-GOVDRIFT-01** | Night | 2026-09-22 | `z1-inbox/2026-09-22/Z2_RULINGS_2026-09-22.md`<br>`7c341213752905a5201c179ef78789cca4f534e66d0b9d7eb3dedcfd9566e0be` |
| ✅ ratified | **Q-P19-GATE-INERT-01** | Night | 2026-09-22 | `z1-inbox/2026-09-22/Z2_RULINGS_2026-09-22.md`<br>`3c3e1cdb30dcc955586d562a23bf8f585bf4799175263a787f4c54b5d602fcd4` |
| ✅ ratified | **Q-ACCOUNT-HUB-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`3232238159e82308cecff220d3a3d0c847c27c4fbb7dbb830b44c59c31c10162` |
| ✅ ratified | **Q-BUZZ-COLLAB-EVAL-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`3a1c238fd5a25421df599453b6fafea2962dff6ebb57a0ad6c81ba7cf95da07c` |
| ✅ ratified | **Q-SA-WINDOW-DESIGN-E-PLUS-A-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`9a3d54e6c9967cdb02192fcc4b9fabfd1334445674e583b434d6da983155d8c7` |
| ✅ ratified | **Q-SMAG-Z3-TASK-SEQUENCING-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`b450d4c75dc5979b7c351771700678968046bd95f2a6e871e5f512cb48f709bb` |
| ✅ ratified | **Q-TOOL-MANIFEST-DRIFT-PREVENTION-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`bbbeb3de3fead9065a0f02c6471ddeb04c6348c209a6cec460d8e064b799e369` |
| ✅ ratified | **Q-Z2-BLOCK-UNFILLABLE-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`a9b01819691f950c3d569fcd9f93487b344c0c15279973cae7f9c1c85d95777b` |
| ✅ ratified | **Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`f9e514b7d2b8ba30cfbce5eff9ed08f9d87d3a647fc21c022ce82cff0d4936bf` |
| ✅ ratified | **Q-Z2RATIF-MECH-32** | Night | 2026-09-23 | `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md`<br>`5701d6fab8331640e5c2f4a4d0b9ae7d825a4506d32fab6feb6955471bd06771` |
| ✅ ratified | **Q-MAIL-EVIDENCE-LEDGER-01** | Night | 2026-09-24 | `z1-inbox/2026-09-24/Z2_RULINGS_2026-09-24.md`<br>`d52a583d659c4230b1456042193748e2c4ec1d32c3aaf395e000aabfe6f40f78` |
| ✅ ratified | **Q-CRB-COMPILE-01** | Night | 2026-09-25 | `z1-inbox/2026-09-25/Z2_RULINGS_2026-09-25.md`<br>`3973ae36b2d6d7cc5d4d0568e9ab10b4b00d59718d2c04dc80140aa44fa322b5` |
| ✅ ratified | **Q-ACAT-DISTRIBUTION-PLAYS-01** | Night | 2026-09-27 | `z1-inbox/2026-09-27/Z2_RULINGS_2026-09-27.md`<br>`8a554118303f61dc18de2f3ee8e60361c7f96b92074363dd5727f65924ff8a6f` |
| ✅ ratified | **Q-GATE-BYPASS-LEDGER-01** | Night | 2026-09-28 | `z1-inbox/2026-09-28/Z2_RULINGS_2026-09-28.md`<br>`12f72d426b18fe37a9514d038e62f77726547337b3b58350d2ffeb77a912fe85` |
| ✅ ratified | **Q-WITNESS-LEDGER-TIER0-EXTENSION-01** | Night | 2026-09-28 | `z1-inbox/2026-09-28/Z2_RULINGS_2026-09-28.md`<br>`9fe935bd180c75631d1c34d9de09dc9eed5b695e80ee25880f2b361a38d2b21f` |
| ✅ ratified | **Q-588-CONVERGENCE-MATRIX-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`8e85e6a2a3664928f33e470f42864829a1c3b55e173a53667ffebf413a0d04e7` |
| ✅ ratified | **Q-GRAPH-CAPTURE-LINT-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`d77a50d5b3df37e7918f7987ac27cdfa9066788e1631163b263d8b8443a2ad2d` |
| ✅ ratified | **Q-PHASE-2B-TELEMETRY-IC-032-PREVENTION-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`3778f919299fb9186c2ad50154c594016b02dc31ae5211cbfd3fc1b81bb2862c` |
| ✅ ratified | **Q-RBE-OPS-TIER-RANKING-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`156a0c91c2393fa911d05bf695d2fe32bfeeca55c1a0fead9ef86729e3fa3044` |
| ✅ ratified | **Q-TIER-ASSIGNMENT-BATCH-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`e38243ad6c1d0fc1615e6b78ab4bf6ccb10697993871f45af04e231c97f92ee5` |
| ✅ ratified | **Q-Z3-EXECUTOR-ASSIGNMENT-BATCH-01** | Night | 2026-10-01 | `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md`<br>`e66e267b7505cb6037d4fe458539e60590f71cc9352c78e8896509b462a5a0d8` |
| ✅ ratified | **Q-REGISTRY-STRUCTURAL-REPAIR-PLAN-01** | Night | 2026-10-09 | `z1-inbox/2026-10-09/Z2_RULINGS_2026-10-09.md`<br>`ad373723fa2107868dd7a78f4b34c5eb7fa2255e132b556530777d78cc47b66c` |
| ✅ ratified | **Q-SYSTEM-GRAPH-TEMPORAL-01** | Night | 2026-10-09 | `z1-inbox/2026-10-09/Z2_RULINGS_2026-10-09.md`<br>`e2a875a2dacba854001df61fd25b37450acf21b589211e8d1cad1e374aebc383` |
| ✅ ratified | **Q-HCM-CORE-MACHINE-01** | Night | 2026-10-14 | `z1-inbox/2026-10-14/Z2_RULINGS_2026-10-14.md`<br>`9d31eeb4bb7eebd2732d3dfe09e4bf46f01e71a67f4e1b30d6894042e336e1bd` |
| ✅ ratified | **Q-MULTI-AGENT-QUEUE-PLAN-01** | Night | 2026-10-15 | `z1-inbox/2026-10-15/Z2_RULINGS_2026-10-15.md`<br>`a04cd27e6b9621a02afce42960575db8c93fa5f7f055fc34c9f8d23def653573` |
| ✅ ratified | **Q-LEDGER-GROUNDING-STUB-01** | Night | 2026-10-21 | `z1-inbox/2026-10-21/Z2_RULINGS_2026-10-21.md`<br>`8537eca961308aa4e93c0cdacb0cd412f90c0afd7e40ba8dcdcdb7ef96195b6c` |
| ✅ ratified | **Q-MESH-LOCAL-COORDINATION-01** | Night | 2026-10-21 | `z1-inbox/2026-10-21/Z2_RULINGS_2026-10-21.md`<br>`2c62341e03c880942e71b2b1b3f6ea85fc99feac0f032b665adb9048f4eae926` |
| ✅ ratified | **Q-QUEUE-SWEEP-PIN-SPEC-01** | Night | 2026-10-21 | `z1-inbox/2026-10-21/Z2_RULINGS_2026-10-21.md`<br>`3823b1ed565652db123cfa2f519c72fe5ae13c194085ff539b7596c782793dc4` |
| ✅ ratified | **Q-EXTERNAL-ADVISORY-INTAKE-01** | Night | 2026-10-22 | `z1-inbox/2026-10-22/Z2_RULINGS_2026-10-22.md`<br>`563369ff69f95601304340707395bd03ba07b8571c09e5cd19430589bf5e782a` |
| ✅ ratified | **Q-HOST-INVENTORY-01** | Night | 2026-10-22 | `z1-inbox/2026-10-22/Z2_RULINGS_2026-10-22.md`<br>`cb1dd413aa869909056e414eea6dcf5cb4df21098385c7f956046e247a6ff9a9` |
| ✅ ratified | **Q-REPO-GRAPH-LOOKUP-01** | Night | 2026-10-22 | `z1-inbox/2026-10-22/Q-REPO-GRAPH-LOOKUP-01-RE-RATIFICATION.md`<br>`3d9fd60e45ad381233420f6086dcfee37da3b44d657c6ba6986ea9286d63e800` |
| ✅ ratified | **Q-WITNESS-DATA-PLANE-01** | Night | 2026-10-22 | `z1-inbox/2026-10-22/Z2_RULINGS_2026-10-22.md`<br>`03d05d10ca71eab7e459b4f178f7c380a52d1dc9c812cf419f9774533df9f9bc` |
| ✅ ratified | **Q-PRINCIPLES-CROSSWALK-01** | Night | 2026-10-24 | `z1-inbox/2026-10-24/Z2_RULINGS_2026-10-24.md`<br>`9f2d417c443bc510feb04389e0acd5b7ae4da54238b35147da89f320d3676af5` |
| ✅ ratified | **Q-HIAE-001-ASSIGNMENT-RECEIPTS-01** | Night | 2026-10-31 | `z1-inbox/2026-10-31/Z2_RULINGS_2026-10-31.md`<br>`462f6a9c2487c31add6dfcdda2c6ce861cfbb9345877ba49307299e8cbe014e0` |
| ✅ ratified | **Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01** | Night | 2026-10-31 | `z1-inbox/2026-10-31/Z2_RULINGS_2026-10-31.md`<br>`ce40510fa97b6df060aa5cdc4fc12809dd80dfe282a2a17f93d2169513788c83` |
| ✅ ratified | **Q-ZONE-Z011-RESEARCH-CAP-01** | Night | 2026-10-31 | `z1-inbox/2026-10-31/Z2_RULINGS_2026-10-31.md`<br>`a33a0e63d9f7a3709ba96e2cea0e69a143bf9103732840a26cfd8b6d4d6a2b57` |
| ✅ ratified | **Q-ISSUE-TRIAGE-CONVENTION-01** | Night | 2026-11-02 | `z1-inbox/2026-11-02/Z2_RULINGS_2026-11-02.md`<br>`b42c53ce8f0721a7c81fe7c09ce3abf0b19026c9dad18b923d3391533767daf7` |
| ✅ ratified | **Q-GOVERNING-ENGINES-HIDDEN-INSTRUCTION-01** | Night | 2026-11-04 | `z1-inbox/2026-11-04/Z2_RULINGS_2026-11-04.md`<br>`3aafdddd10203649ae3638002efeb5956cc771670cc37e6aa5bbd9320fedcf99` |
| ✅ ratified | **Q-PR956-GOVERNANCE-ADMISSION-01** | Night | 2026-11-04 | `z1-inbox/2026-11-04/Z2_RULINGS_2026-11-04.md`<br>`fb3392dac95d3518b3704be189827c5666a230ff8b4e111ba7806a5d8ae9525b` |
| ✅ ratified | **Q-GRAPH-ORPHANS-B1-01** | Night | 2026-11-11 | `z1-inbox/2026-11-11/Z2_RULINGS_2026-11-11.md`<br>`0f1ebdbcb2fd823a439390d02c952d522e90a2503860d32dca2dfdbbbb97dbb0` |
| ✅ ratified | **Q-SYSTEM-GRAPH-REGEN-01** | Night | 2026-11-11 | `z1-inbox/2026-11-11/Z2_RULINGS_2026-11-11.md`<br>`308fb698a1fb1dc569e4bf6ebe1fe8b413b2ae3d8fe32dd79601a2efd0a0cbbc` |
| ✅ ratified | **Q-PILLOW-PYSEC-2026-4363-WAIVER-01** | Night | 2026-11-12 | `z1-inbox/2026-11-12/Z2_RULINGS_2026-11-12.md`<br>`c10a2884f19ff4eb32501d2eddd99a582395d0a6669d25067d92cd09334772fa` |
| ✅ ratified | **Q-RATIFY-STALE-NOTE-01** | Night | 2026-11-13 | `z1-inbox/2026-11-13/Z2_RULINGS_2026-11-13.md`<br>`73c7b805fa6a1eea3da0afda823818fbd340377aa0a5953886fe5ef666dc402a` |
| ✅ ratified | **Q-ACAT-BENCHMARK-01** | Night | 2026-11-14 | `z1-inbox/2026-11-14/Z2_RULINGS_2026-11-14.md`<br>`4e08fe3fa0c8883d0bf16ba691745dc916ebda34cecbe1409dec44a5e1441cbd` |
| ✅ ratified | **Q-PILLOW-TIFF-ADVISORIES-WAIVER-01** | Night | 2026-11-14 | `z1-inbox/2026-11-14/Z2_RULINGS_2026-11-14.md`<br>`710ef85dd69c5d23e999891d9fc8dea3361225e888af1b3d7354435e9eb044e4` |
| ✅ ratified | **Q-GRAPH-CONVERGENCE-01** | Night | 2026-11-15 | `z1-inbox/2026-11-15/Z2_RULINGS_2026-11-15.md`<br>`7104e43ec6dd90b8cffe0f273f828f8b44c900a7aebdc53e78425cd6b4f51302` |
| ✅ ratified | **Q-NF-ADAPTER-01** | Night | 2026-11-15 | `z1-inbox/2026-11-15/Z2_RULINGS_2026-11-15.md`<br>`f43ec3e32c572024e7754b1284ffead8bd339600921ea45fa5982b5f5e908dd1` |
| ✅ ratified | **Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01** | Night | 2026-11-15 | `z1-inbox/2026-11-15/Z2_RULINGS_2026-11-15.md`<br>`334a7fa9d7b2c1dde4812a3940b74a5ce4f386c470a7e2c93931bc72d636972c` |
| ✅ ratified | **Q-DATA-SSOT-REGENERATION-01** | Night | 2026-11-16 | `z1-inbox/2026-11-16/Z2_RULINGS_2026-11-16.md`<br>`842bc245987d30da8fcc74f6bea421c3c87fbf9c7d57c23a40ca52b8e692470a` |
| ✅ ratified | **Q-PROCESS-PRODUCT-RATIO-01** | Night | 2026-11-16 | `z1-inbox/2026-11-16/Z2_RULINGS_2026-11-16.md`<br>`a9023076184b1351f6716b61bc1784e7921b63d17458f8447808f5d55e01e6ee` |
| ✅ ratified | **Q-SEED-TRL-PROPAGATION-01** | Night | 2026-11-16 | `z1-inbox/2026-11-16/Z2_RULINGS_2026-11-16.md`<br>`2f5333da42c63793f95c564f121dfd279c1c82c4638bb84ee527911247ef25a5` |
| ✅ ratified | **Q-SHARED-MISTAKE-CONTROLS-01** | Night | 2026-11-16 | `z1-inbox/2026-11-16/Z2_RULINGS_2026-11-16.md`<br>`58f5653daa33d5674ef463d1649d6acc98c5b4668437c3c7907452c6e139181a` |
| ✅ ratified | **Q-AGENT-CHECKIN-CALIBRATION-01** | Night | 2026-11-19 | `z1-inbox/2026-11-19/Z2_RULINGS_2026-11-19.md`<br>`9029baf16e6415ee1cab97558f8b1582945b38106049e40fc9136645b8b12744` |
| ✅ ratified | **Q-CORPUS-STATS-RECONCILE-01** | Night | 2026-11-19 | `z1-inbox/2026-11-19/Z2_RULINGS_2026-11-19.md`<br>`5197f46860d8847540e4b03814bf7b17759d030f13739be2c9fb657f7e1851f7` |
| ✅ ratified | **Q-REFERENT-DECAY-01** | Night | 2026-11-19 | `z1-inbox/2026-11-19/Z2_RULINGS_2026-11-19.md`<br>`7392a2e7cd2b715de74573d614b805721dcf91633186ec19afb36809fe25a899` |
| ✅ ratified | **Q-SWARM-TRUSTED-HOST-V2-1-PREFLIGHT-01** | Night | 2026-11-19 | `z1-inbox/2026-11-19/Z2_RULINGS_2026-11-19.md`<br>`99d4e259366031dd6c15de5259a52a6ca4d2dacab8a676d2acec3219ad0fe2cc` |
| ✅ ratified | **Q-ADMISSION-GRAPH-TIER2-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`9fb2af9c602b1cacf34adc5080c5f0c51edfe421554c26de7a7e537b4972221a` |
| ✅ ratified | **Q-ADMISSION-RULING-GRAPH-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`3f5cac40f77f8970dc424cef998f2a713a267c4c2c696e512e48334c82b90b79` |
| ✅ ratified | **Q-AGENT-CHECKIN-HA000-LEDGER-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`9849e2ea88025a5102cca16ed75f063253793e12834faca8fe00117e07445ed7` |
| ✅ ratified | **Q-CORPUS-STATS-FOLLOWON-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`73f7b84c73e9c0827d2bed86ee730daa1dfe9eb243f55eef26c91465f15a5476` |
| ✅ ratified | **Q-PROJECT-DESK-BRIDGE-ADMISSION-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`a37b75a823ef1a1572454b55d6c307b3c545c46e2db3ece71bc101888ffa9759` |
| ✅ ratified | **Q-REFERENT-DECAY-FOLLOWON-01** | Night | 2026-11-20 | `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md`<br>`6d7a31980ce273e2fb3984c10ddb2a70d55c96ea0cc4bb60f017e25e8c1af14b` |
| ✅ ratified | **Q-CATCH-BIG-TALK-RULES-01** | Night | 2026-11-25 | `z1-inbox/2026-11-25/Z2_RULINGS_2026-11-25.md`<br>`00a7bc0a4129b5f085d57bf7e3f4ec67172e363bade4dc77e12e62c5e328e2c8` |
| ✅ ratified | **Q-DIGEST-COORD-LAYER-01** | Night | 2026-11-25 | `z1-inbox/2026-11-25/Z2_RULINGS_2026-11-25.md`<br>`570ffe296b88c049446206fe5c5d7ff9e7cbece382be97442606915fa1cdee29` |
| ✅ ratified | **Q-REPO-GRAPH-SORT-01** | Night | 2026-11-25 | `z1-inbox/2026-11-25/Z2_RULINGS_2026-11-25.md`<br>`50d27729d923587ef8e433fd826d901b22dba58a826a9bfb2efed79f48cd8efa` |
| ✅ ratified | **Q-AGENT-WORKFLOWS-01** | Night | 2026-11-26 | `z1-inbox/2026-11-26/Z2_RULINGS_2026-11-26.md`<br>`c3ad71ad4a60226a26a2208d19f27422b5da1ffe9e9a3abc17672fa2dadcee17` |
| ✅ ratified | **Q-BOARD-PUBLISH-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`ce3c38fe981eca2abe82fe915b80865858ae579cb9fb6f1efc16e050669019dc` |
| ✅ ratified | **Q-BOARD-RULING-20** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`5b8f04529aa5e1fc4c20a429589a58a8552c8e9bb20687425457baa46996e065` |
| ✅ ratified | **Q-BOARD-RULING-21** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`9b091779c91ba670c4f2b171f2af5397d5037d78729987355e45bfc2262680fd` |
| ✅ ratified | **Q-BOARD-RULING-22** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`6c37f2be204b92a9c8e3a10ecf715fe245f753b7f58dd9cf5359e2950ba9de6f` |
| ✅ ratified | **Q-BOARD-RULING-23** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`c8ae8edeaae0e48d7f5056d6017097c056b315e03579a1b77a69cec1462e13ab` |
| ✅ ratified | **Q-BOARD-RULING-24** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`748605dc84ab8ae60a1f800877a9e42a54a5fd78a3ef4c963796aabd0521990e` |
| ✅ ratified | **Q-BOARD-RULING-25** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`74f23f0a3ce492a171606f2c96ac0e0943a90f753c69a4e259daafaa31e6c023` |
| ✅ ratified | **Q-BOARD-RULING-26** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`6209b0f5acb5816442a891c6115d82cdea5763d420e2f2b6f12a8c722e182cd6` |
| ✅ ratified | **Q-BOARD-RULING-27** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`86724008145b91802f079394de6a79903408da72ead6c1c162a6fae05c21ca47` |
| ✅ ratified | **Q-BOARD-RULING-28** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`0f03b08144b9e40e2964fe95b120e7710b7a49e24143a93660ca0ce64ec801f5` |
| ✅ ratified | **Q-BOARD-RULING-29** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`d85004fd44dbb8797c8afd91c3a4101506cffe2a629fc6ed336587c4814d4503` |
| ✅ ratified | **Q-BOARD-RULING-30** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`c565584f818c1528e3c511a0c8af851c5e4bfe875237999e76126bded3ccd27d` |
| ✅ ratified | **Q-BOARD-RULING-32** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`17267ddbe840bff8ceeff42df5541cff76d18208b37b3c7e56c46f20c3460905` |
| ✅ ratified | **Q-BOARD-RULING-33** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`0e984b38cadaaedef7e80710b85ada27715c4246b232afacf02cfee647118f5a` |
| ✅ ratified | **Q-FRAMEWORK-MAPPING-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`0be243df58618a069ee0a0c45883c370102ab70e6216b23f3784249a13d43d1f` |
| ✅ ratified | **Q-GOVGATE-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`0e25254978a1e7e0d22713e79b359546a0273a76565b60e440a0f0d95956639f` |
| ✅ ratified | **Q-IC-BOARD-SEALS-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`39dde9d3b2211e917e80e3763e3579053b6685427d0b6ec3d479309b864b37c9` |
| ✅ ratified | **Q-RBE-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`5864af2eda189b5ec158c2fd6f68e479b233de2dd1a82f56d16b97c726fc2aac` |
| ✅ ratified | **Q-REGISTRY-AUDIT-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`ff4ef521607d3d8c50569ba82470cd6e2c92c01d0c51e45fe5669c08e9b6498b` |
| ✅ ratified | **Q-REGISTRY-AUDIT-02** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`61c626549b7725ffff300cac30851d1a6527013f860b1cced2f04700c8ec60f0` |
| ✅ ratified | **Q-RFM-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`85fdf7a4b6d6a2b6c3a11f77608a09aaa3f41a6a79913659dd5388247660408a` |
| ✅ ratified | **Q-STALE-QUEUE-SORT-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`3432b0cb326b50b0ab6ea895c2d247c2b3ec84415dc410531757ed9a37ff9810` |
| ✅ ratified | **Q-TOOLCONTROL-01** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`9ddb53605ea1992d4f0cb83af1f8061b692ba13697305659f62b92de420f1192` |
| ✅ ratified | **Q-TOOLCONTROL-02** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`7ef3a9b5e40900cf6e051f030636b1aa02bd69acc6a204893d76a65e33c3609f` |
| ✅ ratified | **Q-TOOLCONTROL-03** | Night | 2026-11-28 | `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md`<br>`8823989d1b0113972849ac9dceb5ffdc139c397812c6e8dee50c8574118d2a8c` |

## Closed without a Z2 decision (10)

Withdrawn or superseded by the proposer. No Z2 ruling was issued, so these carry no signature — they are not decisions.

| state | candidate | what it asked | block |
|---|---|---|---|
| ↩️ withdrawn | **Q-ADVREVIEW-CALIB-01** | Adversarial review as a PR-gated calibration node | `z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md` |
| ↩️ withdrawn | **Q-BOOT-STATE-MACHINE-01** | Adversarial review of the boot state machine prototype — 17 findings mapped to the 12 ACAT dimensions, plus a corrected implementation | `z1-inbox/2026-09-14/Q-BOOT-STATE-MACHINE-01-ADVERSARIAL-REVIEW.md` |
| ↩️ withdrawn | **Q-CGBG-BASELINE-01** | Adversarial review: CGBG-MARKET-BASELINE-001 (Evidence-Linked Market Observation v0.1) | `z1-inbox/2026-09-13/Q-CGBG-BASELINE-01.md` |
| ↩️ withdrawn | **Q-CGBG-PILOT-01** | Adversarial review: CGBG Pilot Offer (AI Research Capacity) | `z1-inbox/2026-09-13/Q-CGBG-PILOT-01.md` |
| ↩️ withdrawn | **Q-DOC-LIFECYCLE-01** | docs/ lifecycle — disposition for 108 files | `z1-inbox/2026-09-08/DOC_LIFECYCLE_CANDIDATE_BLOCK.md` |
| ↩️ withdrawn | **Q-FRAMEWORK-MAPPING-INTEGRATION-01** | Framework Mapping governance integration across 31 repos | `z1-inbox/2026-09-10/FRAMEWORK_MAPPING_FOLLOWUP.md` |
| ⤴️ superseded | **Q-NF-SCHEMA-01** | Unify NF_LEDGER schema | `z1-inbox/2026-09-10/Q-NF-SCHEMA-01-CANDIDATE.md` |
| ↩️ withdrawn | **Q-PHASE1-2-ROLLOUT-01** | Framework Mapping Phase 1–3 rollout plan | `z1-inbox/2026-09-11/PHASE_1_2_ROLLOUT_PLAN.md` |
| ↩️ withdrawn | **Q-REGISTRY-AUDIT-03** | ZONE_REGISTRY.md reconciliation — implement + deploy CI gate | `z1-inbox/2026-09-13/Q-REGISTRY-AUDIT-03.md` |
| ⤴️ superseded | **Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01** | Research→Governance→Operations Loop + Automated Repository Auditor — three tools: research_to_candidates.py, apply_findings.py, repository_auditor.py (Tier 2 molt) | `z1-inbox/2026-09-19/Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01.md` |

## ⚠️ Falsifier waivers (4) — open for Z2

A candidate with no falsifier. The waiver is the candidate's own claim that it predicts nothing, recorded so it cannot pass silently. Accepting or refusing it is Z2's act.

| candidate | stated reason |
|---|---|
| **Q-FRAMEWORK-MAPPING-01** | the block declares itself Type H, 'no falsifier required — reference architecture'. Recorded as the candidate's own claim, not as an accepted exemption: Z2 accepts or refuses it. |
| **Q-PHASE-2-CI-CONSOLIDATION-ROADMAP-01** | As filed, this candidate presents four strategic options (A-D) for Z2 to prioritize rather than a single falsifiable prediction, and contains no explicit '## Falsifier' heading or falsifier: field. Recorded as the gap, not as an accepted exemption: Z2 accepts or refuses the waiver, or requires a falsifier scoped to whichever option(s) it selects. |
| **Q-SA-WINDOW-DESIGN-E-PLUS-A-01** | As filed, this candidate makes falsifiable claims but contains no explicit ## Falsifier or falsifier: field. Indexed to expose the omission; Z2 must either require an explicit falsifier or consciously accept the waiver before ratification. |
| **Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01** | As filed, this document records a human Z2 decision and implementation authorization but contains no explicit ## Falsifier or falsifier: field. Indexed as awaiting canonical signature so the decision cannot be treated as mechanically ratified by prose alone. |

## Open questions for Z2 (9)

Every unticked item from the `## Z2 Review Checklist` of each candidate still awaiting a decision. Answer them in the block itself — ticking a box here does nothing, because this file is generated.

### Q-DOCREVIEW-01 (9)

`z1-inbox/2026-09-13/Q-DOCREVIEW-01.md`

- [ ] **Decision A — the backlog.** A1 pull queue / A2 retire first / A3 accept as-is. Z1 recommends **A2 then A1**. The staggered-schedule option is withdrawn: it invented an end date, which is the error this correction names.
- [ ] **Decision A3 specifically:** are the nine `HAIOS-COLLAB-*` point-in-time reports live documents or historical records? If records, `retired` is the truthful disposition.
- [ ] **Decision B — owners.** 0 of 46 assigned. A cadence with no assignee produces a queue nobody is late on.
- [ ] `review_policy: {draft: 30, review: 90, approved: 180}` — accept or set real intervals.
- [ ] Overdue stays **advisory** while derivation-mismatch becomes **blocking** — confirm that split is the intended one.
- [ ] `governance-triage.yml` cadence (Mondays 07:00 UTC) and the issue-per-queue shape.
- [ ] **Item 8:** `review_due` and "overdue" are deadline words for what is staleness. Renaming them touches 41 entries and a pre-existing tool — routed, not taken.
- [ ] The 5 documents with **no** `review_due` — leave them, or declare them off-cadence. Under a resource-based reading a missing date is not a defect: it simply means no staleness reference exists yet, which `--record` supplies on first review. They are outside `review_baseline:` for the same reason: there is no seeded date to freeze.
- [ ] `review_baseline:` is accepted as the frozen record of the seeded dates, and changing an entry is understood to be a ratified re-dating rather than an edit.

## Records (97)

No decision requested. Listed so the coverage rule cannot be satisfied by silence.

| file | what it is |
|---|---|
| `z1-inbox/2026-09-06/HANDOFF.md` | Handoff — 2026-09-06 drop |
| `z1-inbox/2026-09-06/MANIFEST.md` | Manifest — 2026-09-06 drop (sets the inbox append-only convention) |
| `z1-inbox/2026-09-08/CYCLE_1_EXTERNAL_REVIEW.md` | Cycle 1 external review |
| `z1-inbox/2026-09-08/CYCLE_2_ADVERSARIAL_REPORT.md` | Cycle 2 adversarial report |
| `z1-inbox/2026-09-08/CYCLE_3_METADATA.md` | Cycle 3 metadata |
| `z1-inbox/2026-09-08/MERGE_RECEIPT_AND_CYCLE1.md` | Merge receipt 2026-09-08 (#217, #218 verified from origin/main) |
| `z1-inbox/2026-09-08/P_J4_BRIER_EXPLAINED.md` | P_J4 Brier score explainer |
| `z1-inbox/2026-09-08/REGISTRY_ENTRY_TEMPLATE.md` | Template — registry entry for H-CAND blocks |
| `z1-inbox/2026-09-08/Z2_RULINGS_2026-09-08.md` | Z2 rulings 2026-09-08 (three decisions, hashed) |
| `z1-inbox/2026-09-09/HANDOFF.md` | Handoff — 2026-09-09 |
| `z1-inbox/2026-09-09/IC-030-REPIN-01.md` | Q-IC030-REPIN-01 work order (Z1 self-assigned; no Z2 decision requested) |
| `z1-inbox/2026-09-10/HANDOFF.md` | Handoff — 2026-09-10 |
| `z1-inbox/2026-09-10/Q-IC030-REPIN-01-RESULT.md` | Q-IC030-REPIN-01 result — repin + manifest reconciliation (COMPLETE, 3/3) |
| `z1-inbox/2026-09-13/HANDOFF.md` | Handoff — 2026-09-13 (registry audit Phase 0) |
| `z1-inbox/2026-09-13/MANIFEST.md` | Manifest — 2026-09-13 drop (registry audit) |
| `z1-inbox/2026-09-13/Z2_RULING_RESOURCE_UNITS_HEADER.md` | Z2 ruling — RESOURCE_UNITS.yaml header ratified; hash remains unsigned by Z2 |
| `z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md` | Z2 ruling — .z1-control/ratify.py Zone 2 ratified (Night, 2026-09-13) |
| `z1-inbox/2026-09-14/HANDOFF.md` | Handoff — 2026-09-14 (Intent-OS board re-read, checker, relay fixes) |
| `z1-inbox/2026-09-14/Z2_RULINGS_2026-09-14.md` | Z2 rulings 2026-09-14 — signatures issued by .z1-control/ratify.py (Q-INTENTOS-LAUNCH-01 ACCEPT) |
| `z1-inbox/2026-09-14/Z2_RULING_AMBIGUITY_BSM_D.md` | Z2 ruling — AMBIGUITY-BSM-D: Z2-GOVARCH-02 supersedes SESSION_RITUALS §A.1; amend to WGS-primary / halt-only-if-both-fail (Night, 2026-09-14) |
| `z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md` | Z2 ruling — d17 local only · d18 z1-inbox + INDEX.yaml · d19 freeze path · temporary tokens revoked (Night, 2026-09-14) |
| `z1-inbox/2026-09-14/Z3-DEPLOYMENT-Q-FRAMEWORK-AUDIT-DEPLOY-01.md` | Z3 deployment log — Q-FRAMEWORK-AUDIT-DEPLOY-01 (12 repos, per-repo framework audit) |
| `z1-inbox/2026-09-16/HANDOFF.md` | Handoff — 2026-09-16 (two sessions: Intent-OS test surface · Z2 queue at close of S-091626-01) |
| `z1-inbox/2026-09-16/HOLOGRAPHIC_HYPOTHESIS_PROTOCOL.md` | Holographic self-representation hypothesis testing protocol (Phase 2 integration mocks, Phase 3 live services, Phase 4 verdict analysis) |
| `z1-inbox/2026-09-16/PHASE2_HANDOFF.md` | Phase 2 Handoff — Holographic integration tests complete, CI green, ready for Z2 review and Phase 3 authorization |
| `z1-inbox/2026-09-16/PHASE3_EXECUTION_CHECKLIST.md` | Phase 3 execution checklist (infrastructure complete; awaiting credential deployment) |
| `z1-inbox/2026-09-16/PHASE3_LAUNCH.md` | Phase 3 launch — holographic live service testing (Z2 authorization received; awaiting credential configuration) |
| `z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md` | Z2 rulings — 2026-09-16 (six): PR #343 ACCEPT, Q-MOLT-LEDGER-SCAN-01 ACCEPT, SESSION_RITUALS v6.4.2 bump ACCEPT (applied), Section F.1 ACCEPT reading (a), ledger → resource-based DIRECTION_GIVEN, ratify.py 1.2.0 awaiting Z2 (Night, 2026-09-16) |
| `z1-inbox/2026-09-17/HANDOFF.md` | Handoff — 2026-09-17 (Intent-OS refresh: the mechanism for automated updates) |
| `z1-inbox/2026-09-17/REQ-20260917-01.md` | Agent request REQ-20260917-01 — Wire the decision relay live so the board can rule and request from a browser |
| `z1-inbox/2026-09-18/Z2_RULINGS_2026-09-18.md` | Z2 rulings 2026-09-18 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md` | Z2 ruling — the merge is the ratification: the hash echo is retired, a ruling's PR changes one file, the merger and the merge date sign it, a job on main records it (Night, 2026-09-18) |
| `z1-inbox/2026-09-19/BROKER-TRACK-STATUS-2026-09-19.md` | Broker Track status report (2026-09-19) |
| `z1-inbox/2026-09-19/PHASE-1-IMPLEMENTATION-STATUS.md` | Phase 1 implementation status report (2026-09-19) |
| `z1-inbox/2026-09-19/PHASE-1B-GRANT-MATCHING-SPEC.md` | Phase 1B Grant Matching Engine specification |
| `z1-inbox/2026-09-19/PHASE-1B-IMPLEMENTATION-STATUS.md` | Phase 1B implementation status report |
| `z1-inbox/2026-09-19/PHASE-2B-SPECIFICATION.md` | Phase 2B specification |
| `z1-inbox/2026-09-19/Z2_RULINGS_2026-09-19.md` | Z2 rulings 2026-09-19 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-21/Z2_RATIFY_SMAG_BLOCKERS.md` | Z2 Ratification: SMAG Calibration & Sequencing Blockers |
| `z1-inbox/2026-09-21/Z2_RULINGS_2026-09-21.md` | Z2 rulings 2026-09-21 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-22/HANDOFF.md` | Session Close Handoff — OI-BRIDGE-01 v0.2 Specification & IC-063 Mitigation |
| `z1-inbox/2026-09-22/MEASUREMENT-SCOPE-AUDIT.md` | Measurement Scope Audit — Blockchain Trading Pilot (Z-012) |
| `z1-inbox/2026-09-22/Z2_RULINGS_2026-09-22.md` | Z2 rulings 2026-09-22 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-23/BUZZ_INTEGRATION_SPEC.md` | Buzz Integration Specification — Technical mapping of HumanAIOS Z1/Z2/Z3 governance to Buzz affordances |
| `z1-inbox/2026-09-23/Z2_RULINGS_2026-09-23.md` | Z2 rulings 2026-09-23 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-24/Z2_RULINGS_2026-09-24.md` | Z2 rulings 2026-09-24 — recovered Q-MAIL merge-is-ratification receipt |
| `z1-inbox/2026-09-25/DEPLOYMENT-FREQUENCY-VERIFICATION.md` | Deployment Frequency Improvement Verification Report |
| `z1-inbox/2026-09-25/HANDOFF-PHASE-1-CI-CONSOLIDATION.md` | Z1 Handoff: Phase 1 CI/CD Consolidation (PR #538) |
| `z1-inbox/2026-09-25/HANDOFF-PHASE-2B-TELEMETRY.md` | Session Handoff — Phase 2B Telemetry Implementation Complete |
| `z1-inbox/2026-09-25/PHASE-1-CI-CONSOLIDATION-HANDOFF.md` | Z1 Handoff: Phase 1 CI/CD Consolidation (isolated branch) |
| `z1-inbox/2026-09-25/PHASE-2-EXECUTIVE-START.md` | Phase 2: Executive Start — Options A & B Immediate Launch |
| `z1-inbox/2026-09-25/PHASE-2A-MONITORING-IMPLEMENTATION.md` | Phase 2A: Monitoring & Validation — Implementation Plan |
| `z1-inbox/2026-09-25/PHASE-2B-PROCESS-IMPROVEMENT-IMPLEMENTATION.md` | Phase 2B: Process Improvement & Behavioral Data Capture — Implementation Plan |
| `z1-inbox/2026-09-25/SESSION-CLOSURE-HANDOFF.md` | Z1 Session Closure Handoff — Phase 1 CI Consolidation & Corrective Fix |
| `z1-inbox/2026-09-25/Z2_RULINGS_2026-09-25.md` | Z2 rulings 2026-09-25 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-27/MOLT-MEASUREMENT-MANUAL-EXTRACTION.md` | MOLT Measurement Manual Extraction Procedure — Blockchain Trading Pilot (Z-012) |
| `z1-inbox/2026-09-27/Z2_RULINGS_2026-09-27.md` | Z2 rulings 2026-09-27 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-28/IC-065-EVIDENCE-LEDGER-GAP-PR465.md` | IC-065 — Evidence Ledger Gap (PR #465) |
| `z1-inbox/2026-09-28/Z2_RULINGS_2026-09-28.md` | Z2 rulings 2026-09-28 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-09-30/PHASE3-CREDENTIAL-DEPLOYMENT-GUIDE.md` | Phase 3 credential deployment guide |
| `z1-inbox/2026-10-01/HANDOFF.md` | Z1 Session Handoff — Phase 2B Salvage Complete |
| `z1-inbox/2026-10-01/PR-630-REMEDIATION-PATCHES.md` | PR #630 Remediation Patches — 6 Actionable Fixes |
| `z1-inbox/2026-10-01/PR-630-WARRANT.md` | WARRANT: PR #630 Admissions Approval & Credential Deployment |
| `z1-inbox/2026-10-01/RED-TEAM-AUDIT-PR-630.md` | Red-Team Audit Report — PR #630 Credential Deployment Findings |
| `z1-inbox/2026-10-01/Z2_RULINGS_2026-10-01.md` | Z2 rulings 2026-10-01 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-10-01/Z3-EXECUTION-CYCLE-1-HANDOFF.md` | Z3 Execution Cycle 1 Handoff — Results & Verification Gaps |
| `z1-inbox/2026-10-02/SESSION_FINDINGS.md` | Z1 Session Handoff — Five Friction Points & TENSION_FINDINGS Feedback Loop |
| `z1-inbox/2026-10-09/Z2_RULINGS_2026-10-09.md` | Z2 rulings 2026-10-09 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-10-10/HANDOFF.md` | Session Handoff — Manifest Integrity Fix (GNER E0/E1/E2) |
| `z1-inbox/2026-10-14/HANDOFF.md` | Session Handoff — Multi-agent queue plan (Q-MULTI-AGENT-QUEUE-PLAN-01) |
| `z1-inbox/2026-10-14/QUEUE_MAP_2026-10-14.md` | QUEUE_MAP — open PRs and issues of operations, 2026-10-14 |
| `z1-inbox/2026-10-14/Z2_RULINGS_2026-10-14.md` | Z2 rulings — 2026-10-14 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-10-15/Q-REPO-GRAPH-LOOKUP-01-RATIFICATION.md` | Night ratification record for Q-REPO-GRAPH-LOOKUP-01 |
| `z1-inbox/2026-10-15/Z2_RULINGS_2026-10-15.md` | Z2 rulings — 2026-10-15 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-10-21/CAPACITY_CONTROL_PLANE_REVIEW_RECORD.md` | Record of the Z2-directed capacity change (4 to 9) and what is still unsigned |
| `z1-inbox/2026-10-21/Z2_RULINGS_2026-10-21.md` | Z2 rulings — 2026-10-21 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-10-22/Q-REPO-GRAPH-LOOKUP-01-RE-RATIFICATION.md` | Night re-ratification record for Q-REPO-GRAPH-LOOKUP-01 (supersedes the 2026-10-15 record) |
| `z1-inbox/2026-10-22/Z2_RULINGS_2026-10-22.md` | Z2 rulings 2026-10-22 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-10-24/Z2_RULINGS_2026-10-24.md` | Z2 rulings 2026-10-24 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-10-27/H-GOVERNANCE-OVERDUE-Z2-DECISION-01.md` | H-GOVERNANCE-OVERDUE-Z2-DECISION-01 — Escalation: Overdue Z2 Governance Decision on Q-PR956-GOVERNANCE-ADMISSION-01 |
| `z1-inbox/2026-10-31/Z2_RULINGS_2026-10-31.md` | Z2 rulings — 2026-10-31 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-11-02/Z2_RULINGS_2026-11-02.md` | Z2 rulings 2026-11-02 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-04/Z2_RULINGS_2026-11-04.md` | Z2 rulings 2026-11-04 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-11/Z2_RULINGS_2026-11-11.md` | Z2 rulings — 2026-11-11 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-11-12/Z2_RULINGS_2026-11-12.md` | Z2 rulings 2026-11-12 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-13/Z2_RULINGS_2026-11-13.md` | Z2 rulings 2026-11-13 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-14/Z2_RULINGS_2026-11-14.md` | Z2 rulings 2026-11-14 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-15/Z2_RULINGS_2026-11-15.md` | Z2 rulings 2026-11-15 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-16/Z2_RULINGS_2026-11-16.md` | Z2 rulings — 2026-11-16 (signed via .z1-control/ratify.py) |
| `z1-inbox/2026-11-19/Z2_RULINGS_2026-11-19.md` | Z2 rulings 2026-11-19 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-20/Q-INTENT-OS-WITNESS-LEDGER-01-INDEX-RECONCILE.md` | INDEX reconcile record for Q-INTENT-OS-WITNESS-LEDGER-01 (Z1 pending Night; z2_hash PENDING_NIGHT_REPIN) |
| `z1-inbox/2026-11-20/Z2_RULINGS_2026-11-20.md` | Z2 rulings 2026-11-20 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-25/Z2_RULINGS_2026-11-25.md` | Z2 rulings 2026-11-25 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-25/Z2_RULING_MERGE_RATIFIES_ALL_CANDIDATES.md` | Z2 ruling — the merge ratifies every candidate, not only board rulings (Night, 2026-11-25) |
| `z1-inbox/2026-11-26/Z2_RULINGS_2026-11-26.md` | Z2 rulings 2026-11-26 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/2026-11-28/Z2_RULINGS_2026-11-28.md` | Z2 rulings 2026-11-28 — signatures issued by .z1-control/ratify.py and tools/intent_os_reconcile_v1_0.py |
| `z1-inbox/PHASE-2-IMPLEMENTATION-PLAN.md` | Phase 2 Account Hub API Integrations & Cockpit Enhancement — implementation plan |

## Excluded from the conversion record (12)

Neither a candidate nor a record. Listed because an exclusion the index accepts must still be visible — silence is what the coverage rule exists to prevent.

- `z1-inbox/2026-11-07/swarm_trusted_host_v2_1/README.md`
- `z1-inbox/2026-11-07/swarm_trusted_host_v2_1/docs/SECURITY_GAPS.md`
- `z1-inbox/2026-11-07/swarm_trusted_host_v2_1/evidence/ROUND4_INDEPENDENT_HANDOFF.md`
- `z1-inbox/2026-11-12/Z2_BATCH_PACKET_B1-B3.md`
- `z1-inbox/2026-11-12/project-desk-bridge/README.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/AUDIT_HANDOFF.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/AUDIT_LOG.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/IMPLEMENTATION_NOTES.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/LIMITATION_REGISTER.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/RECONCILIATION_REPORT.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/TEST_A_REPORT.md`
- `z1-inbox/2026-11-12/project-desk-bridge/docs/TEST_MANIFEST.md`

---

**Converting an inbox item to a Z2 decision:** add it to `z1-inbox/INDEX.yaml` under `candidates:` with `status: awaiting_z2` and a falsifier in the block itself, run `python3 .z1-control/render.py`, and commit both. An undecided candidate carries no signature fields at all.

Z2 records the decision by setting `status`, `ratified_by`, `ratified_at`, a `z2_ruling` that resolves to a file **indexed under `records:`**, and a `z2_hash` that **appears in that ruling**. All five are required: the validator refuses a signature from anyone outside `ratifiers:`, and refuses a hash the cited ruling does not carry.
