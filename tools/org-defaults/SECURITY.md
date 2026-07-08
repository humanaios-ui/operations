# Security Policy

HumanAIOS is an integrity-measurement project. Holding ourselves to the security
standard we ask others to meet is part of the **Witness principle**: the scrutiny
we apply to AI substrates applies equally to the systems and operators running the
assessments.

## Reporting a vulnerability

**Please report privately — do not open a public issue for a security matter.**

1. **Preferred:** use GitHub's private vulnerability reporting on this repo —
   **Security → Advisories → "Report a vulnerability."** This opens a private
   channel with the maintainers.
2. If that is unavailable, contact the maintainer through their GitHub profile
   (`@humanaios-ui`) and request a private channel before sharing details.

Please include: what you found, where (repo + path/URL), how to reproduce, and the
impact you see. We aim to acknowledge within **72 hours** and to agree a
remediation and coordinated-disclosure timeline with you from there.

## Scope

This is a **pre-launch R&D** ecosystem. The most sensitive surfaces org-wide are:

- Any **assessment write path** — corpus integrity is a research-validity concern
  as well as a security one. Report anything that allows unauthenticated writes to
  the ACAT assessment tables or derived statistics.
- Any **workflow / CI misconfiguration** — a broken gate that silently accepts bad
  content or leaks secrets is in scope.
- Any path that **publishes content marked internal-only** to a public surface.
- The **document-control system** — a bypass that lets a controlled document be
  altered without tripping the gate.

Out of scope: findings that require operator-level (Zone 3) credentials you were
given legitimately; volumetric/DoS testing against live services; social
engineering.

## Secrets — our standing rule

**No secret is ever committed to a repository.** Credentials live in a secrets
manager or hardware key — never in files, a browser, or an AI context, and we use
short-lived cut credentials rather than minting long-lived ones. Handling of
credential-bearing actions is **Zone 3** (operator-only) under the
[governance model](https://github.com/humanaios-ui/operations/blob/main/GOVERNANCE.md).

If you find a committed secret (even a placeholder that invites a real one),
report it privately as above.

## Supported versions

`main` is the living line and the only supported branch. Fixes land on `main`;
there are no maintained release branches at this stage.

---

<sub>◐ The Witness · security scrutiny applies in both directions. Full policy and
health posture: <a href="https://github.com/humanaios-ui/operations/blob/main/SECURITY.md">operations/SECURITY.md</a></sub>
