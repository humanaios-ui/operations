# humanaios-ui / operations

Operating-process source of truth for HumanAIOS.

This repo is the canonical home for class-2 (operating process) and class-3 (findings registry) artifacts. Live state lives at `haioscc.pages.dev`. Public-facing surface lives at `humanaios.ai`. This repo is the middle layer: principles, findings, and protocols that update on a days-to-weeks cadence and need version control.

## Read this first

- **[CURRENT.md](./CURRENT.md)** — Operating process. Identity, lessons, hard-stop principles, dataset state. Fetched by every LLM at session open.
- **[REGISTERED.md](./REGISTERED.md)** — Findings registry (F-class), hypotheses (H-class), corrections (IC-class). Append-only.
- **[SESSION_RITUALS.md](./SESSION_RITUALS.md)** — Substrate-agnostic open/close protocols, parser tags, halt conditions.
- **[ACAT_SESSION_PROMPT.md](./ACAT_SESSION_PROMPT.md)** — Unified Phase 1 + Phase 3 session protocol. The complete prompt every substrate runs at session open and close.

## Raw URL pattern (for LLM fetch)

```
https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md
https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md
https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md
https://raw.githubusercontent.com/humanaios-ui/operations/main/ACAT_SESSION_PROMPT.md
```

## Update model

- **Zone 1 (Claude/Grok):** Drafts changes
- **Zone 2 (joint):** Reviews when change crosses a principle
- **Zone 3 (Night):** Commits and pushes

Every change bumps the "Last updated" line in the affected file and adds a one-line entry to that file's changelog.

## Why this repo exists

Registered as IC-020 in REGISTERED.md. The operating process previously had no canonical fetchable URL, living instead in Project files, CI version comments, Slack #wgs-sync, and human memory. This produced IC-019-class drift inevitably and repeatedly. This repo is the structural fix.

---

Wado.
