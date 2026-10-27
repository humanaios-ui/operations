# ECC for Codex CLI

> **Repository visit reflex (pilot):** Follow the bounded ENTER/EXIT handoff in [AGENTS.md](../AGENTS.md). This is not an instruction to bypass admission or publish without permission.

This provides a repo-local ECC baseline for Codex CLI.

## Repo Skill

- Repo-generated Codex skill: `.agents/skills/operations/SKILL.md`
- Claude-facing companion skill: `.claude/skills/operations/SKILL.md`
- Keep user-specific credentials and private MCPs in `~/.codex/config.toml`, not in this repo.

## MCP Baseline

Treat `.codex/config.toml` as the default ECC-safe baseline for work in this repository.
The generated baseline enables GitHub, Context7, Exa, Memory, Playwright, and Sequential Thinking.

## Multi-Agent Support

- Explorer: read-only evidence gathering
- Reviewer: correctness, security, and regression review
- Docs researcher: API and release-note verification

## Workflow Files

No dedicated workflow command files were generated for this repo. If workflow command files are added later, use them as reusable task scaffolds for recurring repository workflows.