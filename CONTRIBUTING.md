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

## How a pull request is admitted

Opening a pull request does not put it in the operator queue. Admission is a separate, explicit step. It is routing only: it is **not** code approval and **not** merge authority. This is how it works today, as seen on this repository's pull requests:

- **A draft carries no weight.** The admission check passes a draft in the `WORKBENCH` lane, which is isolated from the operator queue. Mark the pull request ready when its head is final.
- **Admission is bound to one exact commit.** An authorized identity posts `/coordinator admit <full head SHA>` on the ready pull request. The coordinator replies with a receipt; `STATE_EVENT_COMMITTED` means the admission is recorded. A comment alone is never approval. Only the recorded state counts.
- **Any push voids it.** A new commit, or a merge of `main` into your branch, moves the head. The old admission is revoked (the ledger records a `REVOKE`) and the new head needs its own `/coordinator admit`. Batch your fixes first, and give the new full SHA when you ask.
- **A red check right after an admit can be a race.** The admission check can read "no explicit admission record" when it ran just before the admit was recorded. Wait for the coordinator's `ADMIT` receipt, then re-run the failed check once.
- **Issues are not admitted work.** Opening or assigning an issue does not admit a pull request.
- **Say your molt tier.** The pull request body needs `molt_tier_claimed: 0`, `1` or `2`. The template has the line.
- **Where to look.** Each pull request carries the coordinator's index comment and receipts. The full record is `ADMISSION_LEDGER.jsonl` on the `repository-coordinator-state` branch; the copy on `main` is old. A generated page joining admissions to Z2 rulings is a ratified direction (`Q-ADMISSION-RULING-GRAPH-01`) and is not built yet.

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

Start with the pre-submission check. It catches the common blockers before you push
and drafts the PR body:

```bash
python3 tools/pre_submit.py                          # branch, no-op, readiness, workflows, secrets, molt tier
python3 tools/pre_submit.py --body-out draft.md      # also write a PR body from the template
python3 tools/pre_submit.py --input filled.md        # lint your filled-in body before you submit it
```

It blocks on these local conditions: on the default branch, no commits, an empty
diff, a failing readiness check, an unparseable workflow, or a recognized private
key, GitHub token, or AWS access-key format in an added line. It does not run
pytest, ruff, or mypy, and it does not replace the remaining CI gates. CI remains
the authority. It never fills in `smag_p` or `molt_tier_claimed` for you.
Those are your prediction, and CI measures the gap. The draft shows the measured tier
beside the empty field.

Then the vitality check:

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
