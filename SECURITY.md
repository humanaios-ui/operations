# Security Policy

HumanAIOS is an integrity-measurement project. Holding ourselves to the security
standard we ask others to meet is part of the **Witness principle**: the scrutiny
we apply to AI substrates applies equally to the systems and operators running the
assessments.

## Reporting a vulnerability

**Please report privately — do not open a public issue for a security matter.**

1. **Preferred:** use GitHub's private vulnerability reporting on this repo —
   **Security → Advisories → “Report a vulnerability.”** This opens a private
   channel with the maintainers.
2. If that is unavailable, contact the maintainer through their GitHub profile
   (`@humanaios-ui`) and request a private channel before sharing details.

Please include: what you found, where (repo + path/URL), how to reproduce, and the
impact you see. We aim to acknowledge within **72 hours** and to agree a
remediation and coordinated-disclosure timeline with you from there.

## Scope

This is a **pre-launch R&D** ecosystem; the most sensitive surfaces are:

- **The ACAT pipeline** (`acat/`) and any assessment write path — corpus integrity
  is a research-validity concern as well as a security one. Report anything that
  lets unauthenticated writes reach `acat_assessments_v1` or the derived stats.
- **The site generator** (`site/`, `tools/registry_site_generator*`) — the public
  site must never publish content marked internal-only. A rendering path that leaks
  private registry entries or PII is in scope.
- **The document-control system** (`.doc-control/`, `document-registry.yaml`) — a
  bypass that lets a controlled document be altered without tripping the gate.
- Any **workflow / CI** misconfiguration (see `.github/workflows/`).

Out of scope: findings that require operator-level (Zone 3) credentials you were
given legitimately; volumetric/DoS testing against live services; social
engineering.

## Secrets — our standing rule

**No secret is ever committed to a repository.** Credentials live in a secrets
manager or hardware key — never in files, a browser, or an AI context, and we use
short-lived cut credentials rather than minting long-lived ones. Handling of
credential-bearing actions is **Zone 3** (operator-only) under
[GOVERNANCE.md](GOVERNANCE.md).

If you find a committed secret (even a placeholder that invites a real one),
report it privately as above. We run toward adopting automated secret scanning
(GitHub secret scanning + `gitleaks`) as part of the health growth path in
[SYSTEM_HEALTH.md](SYSTEM_HEALTH.md).

## Supported versions

`main` is the living line and the only supported branch. Fixes land on `main`;
there are no maintained release branches at this stage.

---

<sub>◐ The Witness · security scrutiny applies in both directions. See [SYSTEM_HEALTH.md](SYSTEM_HEALTH.md) for the wider health posture.</sub>
