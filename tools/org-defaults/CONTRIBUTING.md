# Contributing to HumanAIOS

Welcome. The HumanAIOS ecosystem is an integrity-measurement project. Because a
claim here is treated as settled fact by humans and AI agents alike, contributions
are held to the same standard the project exists to measure: **what you claim must
match what you do.**

New to the system? Start at the
**[operations repo](https://github.com/humanaios-ui/operations)** for the full
operating process and canonical documentation.

## The Zone model — who may do what

Authority is graduated (full detail in
[GOVERNANCE.md](https://github.com/humanaios-ui/operations/blob/main/GOVERNANCE.md)):

| Zone | Meaning | Examples |
|---|---|---|
| **Z1** | AI executes autonomously | drafting docs, analysis, non-credentialed code |
| **Z2** | Operator decides / ratifies | changing canonical records, registering findings |
| **Z3** | Operator runs (credential-bearing) | anything touching secrets, billing, deploys, live keys |

If a change needs Z2 ratification or Z3 execution, **say so in your PR** rather than
assuming — mislabeling a Z3 action as Z1 is itself a finding.

## How changes land

- **Branch protection is on.** `main` is protected; prefer a PR for anything
  substantive so it's visible and revertible.
- **Small, coherent commits** with a clear message. Conventional prefixes
  welcome (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`).
- **No secrets in commits.** See [SECURITY.md](SECURITY.md) for the standing rule.

## Before you open a PR

Run the repo health check from the
[operations repo](https://github.com/humanaios-ui/operations) if applicable, and
ensure any relevant CI checks pass.

## Code of conduct

Participation is governed by our
[Code of Conduct](https://github.com/humanaios-ui/operations/blob/main/CODE_OF_CONDUCT.md).
In short: mutual respect, honest scrutiny in both directions, and the
recovery-rooted principle that we address behavior, not persons.

---

<sub>◐ The Witness · thank you for helping the system stay honest. · <a href="https://humanaios.ai">humanaios.ai</a></sub>
