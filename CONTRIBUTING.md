# Contributing to HumanAIOS · operations

Welcome. This repository is the **exoskeleton** — the canonical operating process
and single source of truth for the ecosystem. Because a claim here is treated as
settled fact by humans and AI agents alike, contributions are held to the same
standard the project exists to measure: **what you claim must match what you do.**

New to the system? Start at **[START_HERE.md](START_HERE.md)** for the live map.

## The Zone model — who may do what

Authority is graduated (full detail in [GOVERNANCE.md](GOVERNANCE.md)):

| Zone | Meaning | Examples |
|---|---|---|
| **Z1** | AI executes autonomously | drafting docs, analysis, non-credentialed code |
| **Z2** | Operator decides / ratifies | changing canonical records, registering findings |
| **Z3** | Operator runs (credential-bearing) | anything touching secrets, billing, deploys, live keys |

If a change needs Z2 ratification or Z3 execution, **say so in your PR** rather than
assuming — mislabeling a Z3 action as Z1 is itself a finding.

## How changes land

- **Read the map first.** [START_HERE.md](START_HERE.md) → [SEED.md](SEED.md)
  (why) → [SESSION_RITUALS.md](SESSION_RITUALS.md) (how a session runs).
- **Branch protection is on.** `main` here is light-touch (force-push and deletion
  blocked); the sibling repos require a review. Prefer a PR for anything
  substantive so it's visible and revertible.
- **Small, coherent commits** with a clear message. Conventional prefixes
  welcome (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`).

## Document control

Controlled documents are tracked in **`document-registry.yaml`** and indexed in
**[CONTROLLED_DOCUMENTS.md](CONTROLLED_DOCUMENTS.md)**. The CI gate
(`.github/workflows/document-control.yml`) runs `.doc-control/validate.py` on every
`.md` / registry change:

- **Adding a controlled document?** Register it in `document-registry.yaml` and add
  the frontmatter (`doc_id`, `title`, `revision`, `status`, `owner`, `canonical`).
  An unregistered `doc_id` (or a registered doc missing its file) fails the gate.
- **Content-accuracy holds** block a doc from `status: approved` while a known issue
  is unresolved — don't route around them.
- Prose lint and link checks run **advisory** (warn, don't block).

## The immune memory

When you discover something the system should remember — a bug, a failure mode, a
correction — register it in **[REGISTERED.md](REGISTERED.md)** as an `F` (finding),
`H` (hypothesis), or `IC` (integrity correction), using the YAML entry schema at the
top of that file. This is how a lesson becomes an antibody: named once, it can be
taught to the validator/CI so it doesn't recur.

## Before you open a PR — run a checkup

```bash
python3 tools/repo_health.py        # 0–100 repo vitality
python3 tools/repo_health.py --strict   # non-zero exit below threshold
```

Green-ish vitals + a passing doc-control gate + a clear Zone label = a mergeable PR.

## Code of conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). In short:
mutual respect, honest scrutiny in both directions, and the recovery-rooted
principle that we address behavior, not persons.

---

<sub>◐ The Witness · thank you for helping the system stay honest. · <a href="https://humanaios.ai">humanaios.ai</a></sub>
