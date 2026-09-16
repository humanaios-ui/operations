# Practice → Resolution Target Map

**Location:** `ledgers/PRACTICE_RESOLUTION_MAP.md`
**Status:** Z1 map — **not ratified**. The UNAMBIGUOUS rows are actionable; the AMBIGUOUS and
UNRESOLVABLE rows are **not**, and are listed here as Z2 decisions.
**Serves:** `ledgers/NF_LEDGER.jsonl` resolution, per the resolver rule pinned in
`ledgers/mesh_pins_090826.json`
**Derived:** 2026-09-16, S-091526-01
**Pins:** `operations` @ `846aaf6` · `empirica-practice-mesh` @ `f2d37a87ec8da924de4c15319528e8e236b02aa2`
(HEAD at derivation; 12 commits, full history read)

---

## Why this file exists

The pin spec fixes the resolution rule:

> `"resolver": "tree read of the named repo at date+3 (UTC); missing file = NO; final read 2026-10-04"`

**"The named repo" resolves for 3 of 15 practices.** The other 12 name no repository that exists. The
first resolution pass (2026-09-16) spent nearly all of its effort discovering that, and almost none on
the reads themselves — the reads took seconds. That asymmetry is the whole reason this file exists: a
per-session resolution step is cheap *only once this mapping is written down*. Proposing a §B.7 ritual
without it would ship an obligation whose real cost nobody had measured.

Nothing in `empirica-practice-mesh` documents the mapping (`README.md`, `CLAUDE.md`,
`PIPELINE_ARCHITECTURE.md` were all checked). It is derived here from the tree, not from prose.

---

## The map

| practice | tokens | resolved | class | resolution target |
|:--|--:|--:|:--|:--|
| `acat-x` | 3 | 0 | AMBIGUOUS | repo `acat-x` OR mesh dir |
| `collaborator-ops` | 3 | 0 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `empirica-autonomy` | 4 | 0 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `empirica-epistemology` | 3 | 0 | **UNRESOLVABLE** | — none — |
| `empirica-foundation-evaluator` | 5 | 1 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `empirica-mesh-support` | 4 | 0 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `empirica-outreach` | 5 | 2 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `empirica-quality-assurance` | 3 | 0 | **UNRESOLVABLE** | — none — |
| `empirica-resource-miner` | 4 | 0 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `grok-crossref` | 6 | 3 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `humanaios` | 4 | 0 | AMBIGUOUS | repo `humanaios` OR mesh dir |
| `humanaios-internal` | 3 | 0 | AMBIGUOUS | repo `humanaios-internal` OR mesh dir |
| `local-machine-optimizer` | 3 | 0 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `opportunity-aggregator` | 4 | 1 | UNAMBIGUOUS | mesh dir (scaffold only) |
| `website` | 4 | 0 | AMBIGUOUS | mesh dir (vendors `operations-repo`) |

"mesh dir" = `humanaios-ui/empirica-practice-mesh` → `practices/<practice>/`.

| class | practices | tokens | may Z1 resolve? |
|:--|--:|--:|:--|
| UNAMBIGUOUS | 10 | 38 | **yes** — one candidate target |
| AMBIGUOUS | 3 | 16 | **no** — two candidate targets, different verdicts |
| UNRESOLVABLE | 2 | 6 | **no** — no target exists anywhere |
| | **15** | **58** | |

All 7 resolutions written on 2026-09-16 fall in UNAMBIGUOUS rows. None touched an AMBIGUOUS or
UNRESOLVABLE practice.

---

## The two Z2 decisions this surfaces

**D1 — Where does an AMBIGUOUS practice resolve?** 16 tokens. Three practices share a name with a
real repository (`acat-x`, `humanaios`, `humanaios-internal`), and a fourth (`website`) has a mesh
directory that vendors a copy of another repo under `operations-repo/`. The two candidate targets give
**different verdicts**: the mesh directories are scaffold-only, so reading the mesh dir returns NO for
essentially everything, while the real repositories are active and may well hold the artifact. This is
not a tie to be broken by convention — picking the mesh dir would score 16 tokens NO on a technicality.

**D2 — What happens to an UNRESOLVABLE practice?** 6 tokens. `empirica-epistemology` and
`empirica-quality-assurance` carry pinned forecasts but have no mesh directory and no repository of
their own. As specified they can never be read, at the 2026-10-04 final read or ever. The options are a
ruling that names a target, a `STRIKE` on the tokens, or letting the pins expire VOID — each is a
different statement about what the forecast meant, and it is Z2's to make.

Until D1 and D2 are ruled, resolving those 22 tokens would be picking a target to get a verdict, which
is the manufactured-calibration failure the resolution discipline exists to prevent. They stay
unresolved.

---

## Inverse gap

Three practice directories exist in the mesh with **no tokens in the pin spec** — work with no
forecast against it, the mirror of a forecast with no work:

- `empirica-temporal-oracle` (has real content: `src/`, `README.md`, `INITIALIZATION_COMPLETE.md`)
- `flta-app-empirica`
- `schema.sql` (a directory, not a file — likely a scaffolding accident)

Not an error in the ledger; noted so the next census does not read 15 practices as the whole mesh.

---

## Resolution procedure (UNAMBIGUOUS rows only)

```bash
# 1. what is ripe? a token is readable at due-date + 3 days
python3 tools/nf_ledger_v0_1.py status ledgers/NF_LEDGER.jsonl
#    NB: the "scoreable-now" column means well-formed and Z2-dated.
#    It does NOT mean the window has closed. Compute date+3 yourself.

# 2. read the target tree at a pinned sha (clone is read-only, public)
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 \
  https://github.com/humanaios-ui/empirica-practice-mesh /tmp/mesh
git -C /tmp/mesh log --diff-filter=AD --name-only -- practices/<practice>

# 3. resolve, with the sha in the source — the tool refuses a verdict without one
python3 tools/nf_ledger_v0_1.py resolve ledgers/NF_LEDGER.jsonl <TOKEN_ID> NO \
  --by Z1 --source "empirica-practice-mesh@<sha> practices/<practice>/ — <what was read>"

# 4. confirm
python3 tools/nf_ledger_v0_1.py verify ledgers/NF_LEDGER.jsonl
python3 tools/nf_ledger_v0_1.py score  ledgers/NF_LEDGER.jsonl
```

Cannot determine the verdict from a tree read → **leave it unresolved and raise a RECEIPT-GAP**. An
unresolved pin is honest; a guessed one corrupts the calibration series permanently, because the ledger
is append-only and a wrong resolution is correctable only by a DISPUTE event.

A `token_id` in a new RESOLVE row will trip `gitleaks`' `generic-api-key` rule; `.gitleaks.toml`
allowlists that exact shape and nothing else.

---

## Maintenance

This map is derived, not authored — it goes stale the moment a practice gains content, a repository is
created, or the pin spec adds a practice. Re-derive it against a fresh mesh clone before any resolution
pass, and re-pin the shas in the header. A stale map that reads as current would turn a NO into a
false negative, which is the direction that matters.
