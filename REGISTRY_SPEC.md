# REGISTRY SPECIFICATION — HumanAIOS Findings Registry (PATH A: Codified Practice)

**Status:** RATIFIED (Z2 approval 2026-08-04, Carly)  
**Effective Date:** 2026-08-04  
**Version:** 0.1  
**Canonical Registry URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`

---

## PURPOSE

This specification codifies the existing practice and architecture of the HumanAIOS findings registry. The registry serves as the single source of truth for:
- **F-class findings** (empirical observations, ratified by Z2)
- **IC-class integrity corrections** (errors discovered and remediated, traced in registry)
- **H-class hypotheses** (testable predictions with drop conditions)
- **D-class drift patterns** (named divergence classes discovered from system output)

The registry is the index that binds independent verification streams: public repos, preprints, datasets, and governance records.

---

## CANONICAL STORE

**Medium:** REGISTERED.md — a Markdown file under Git version control  
**Location:** `humanaios-ui/operations/blob/main/REGISTERED.md` (GitHub)  
**Canonical URL (raw):** `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`

**Single Source of Truth Rule:**
The file at the main branch HEAD is the registry. Every mirror, cache, summary, or database view is DERIVED and non-authoritative. Where a mirror and the canonical file disagree, the file wins and the mirror is repaired.

**Rationale:**
Markdown-in-Git chosen deliberately over a database:
- Human-readable without tooling (maximally durable, portable)
- Machine-parseable (YAML front-matter, structured text)
- Commit history IS the audit trail — provenance for free, Art. 12 analog satisfied by the medium itself
- Never-delete append-only enforced by Git history (immutable record)

---

## ENTRY CLASSES

| Class | Purpose | Authority | Lifecycle |
|-------|---------|-----------|-----------|
| **F** | Findings: Ratified observations; "what is true that was not known before" | Z2 ratification required | CANDIDATE → RATIFIED → ACTIVE / SUPERSEDED |
| **IC** | Integrity Corrections: Errors discovered; cost-classified by impact | Z2 ratification; recorded with evidence trail | DISCOVERED → REGISTERED → REMEDIATION_TRACKED |
| **H** | Hypotheses: Testable predictions; drop conditions explicit | Z2 ratification; drop conditions must be clear | CANDIDATE → REGISTERED → TESTED / DISCONFIRMED |
| **D** | Drift Classes: Named divergence patterns; naming authority is Z2 only | Z2 exclusive naming right | D-CANDIDATE → (Z2 reviews) → D-CLASS NAMED or REJECTED |
| **R** | Rulings: Formal Z2 decisions; governance actions | Z2 formal authority | (Receipt form: R-YYYY-MM-DD-NN) |
| **GD** | Governance Directives: Operational rules; Z2-signed | Z2 formal authority | DRAFT → RATIFIED → ACTIVE |

---

## ENTRY SCHEMA

Every entry carries (required for all entries after 2026-05-08):

```yaml
---
id: "F-XX" | "H-XX" | "IC-XXX" | "D-CLASS-NAME" | "R-YYYY-MM-DD-NN" | "GD-NN"
name: "Short slug"
status: CANDIDATE | PROVISIONAL | RATIFIED | ACTIVE | SUPERSEDED | REJECTED | CONFIRMED | DISCONFIRMED | PENDING_ZONE2
class: F | H | IC | D | R | GD
date_registered: "YYYY-MM-DD"
date_origin: "YYYY-MM-DD" (when first discovered, not registered)
session_registered: "S-MMDDYY-NN-slug"
principles_triggered: ["P-N"] (if applicable)
substrate: "Provider name / model version" (for findings)
tags: ["drift", "dataset", "governance", "intent"] (comma-separated keywords)
superseded_by: null | "F-XX" (if superseded)
evidence_trail: "source session(s), originating event(s), recurrence count for D-classes"
ratification_receipt: "date + form (in-session | PR | ruling id) + scope note"
---
```

---

## WRITE RULES

**Who can write:**
- Z1 (Claude, agent) submits via pull request; PR approval by Z2 is itself a valid ratification form
- Z2 (Carly) commits directly to main (branch protection enforced; no direct pushes from CI/automation)

**Branch Protection (REQUIRED):**
- `main` branch protection enabled
- No direct pushes; Z2 review mandatory
- CI may not bypass review (no `--force`, no `--no-verify`)
- NOTE: Branch protection verification is a known open item from prior security audit; it is a ratification blocker for this spec

**Never Delete:**
Entries are never deleted or rewritten. Corrections happen by addition:
- A new entry supersedes the old
- Old entry marked SUPERSEDED with forward pointer
- All versions remain readable (Git history immutable)
- This extends the Supabase migrate-by-addition pattern to governance memory itself

---

## READ RULES

**IC-030 Hard Halt (Mandatory Pre-Operation Check):**
Any registry-touching operation (registration, findings scan, supersession, status change) MUST begin with a live fetch of REGISTERED.md at HEAD. Operating on a stale or absent copy is the IC-030 condition and hard-halts the operation.

- Drafting FOR Z2 without live fetch is permitted but must be labeled "reconciliation-pending" — never presented as registry-final
- LLM agents fetching this file for reasoning context should treat synopsis as the citable fact
- Agent access: read access is unrestricted; the registry is the shared ground truth all substrates load

---

## DOCUMENT FLOW CONVENTIONS

1. **F-class findings** ordered strictly by F-number (F-18 through F-55+)
2. **Honest gaps preserved:** F-32 and F-33 are intentional gaps reflecting historical ID transition; preserved because external references depend on stable IDs
3. **Slug-to-number mapping:** Legacy slug-named entries (F-RLHF → F-20) retain slugs in `name:` field but carry sequential F-number; external citations using original slugs remain valid
4. **Entry ordering:** F-class, then IC-class, then H-class, then other classes
5. **No renumbering:** Once assigned, IDs never change (enables external citations)

---

## DERIVED VIEWS (NOT AUTHORITATIVE)

**Local Mirror:** Optional empirica workspace mirror (ARTIFACT_REGISTRY_INDEX.yaml) for query and dashboarding. Derived, rebuildable, never authoritative. Sync failures repair FROM the canonical file.

**Supabase Mirror:** Optional parsed mirror in existing Supabase project for API access. Derived, rebuildable. Sync failures repair FROM the file.

**WGS Record:** Cross-session reconciliation sweeps read the registry; they never write it. Read-only access.

---

## LIFECYCLE

- **Candidate:** Enters via Z1 draft, findings scan, discovery pipeline, or panel review — always with evidence trail
- **Review:** Z2 applies relevance criterion (does naming improve governance outcomes?) and replication requirement for D-CANDIDATE
- **Decision:** RATIFIED (receipt) | REJECTED (retained with reason) | DEFERRED as CANDIDATE
- **Provisional Track:** Clusters may hold provisional names with automatic expiration if unvalidated
- **Supersession:** By addition only (never deletion)
- **Dormancy:** Ratified executable entries default to RATIFIED-DORMANT; RATIFIED-ACTIVE is separate explicit Z2 act

---

## INTEGRITY

**Provenance:** Git commit history + signed commits where available  
**Receipts:** DCM-scored — unratified writes are structurally impossible under branch protection  
**Reconciliation:** findings-scan and receipt-reconciliation skills audit session claims against registry state  
**Survivability:** The registry, public repos, dataset, and preprint together form the independently verifiable record

---

## COMPLIANCE CHECKLIST (Z2 Verification)

Before activating this spec as RATIFIED:

- [ ] Branch protection on `humanaios-ui/operations` main branch is verified enabled
- [ ] claim_class_gate.py points to canonical URL: `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`
- [ ] CI workflows reference this spec and enforce IC-030 hard-halt rule
- [ ] Local empirica mirror (ARTIFACT_REGISTRY_INDEX.yaml) template created and tested
- [ ] Mirror-sync CI check added (alerts if divergence >3 days; non-blocking)
- [ ] External preprints/citations reviewed for URL dependency (redirect plan if any)

---

## ACTIVATION

**Effective Date:** Upon Z2 ratification (Carly approval)  
**Status:** RATIFIED  
**Z2 Receipt:**  
- **Form:** In-session approval + formal declaration  
- **Authority:** Z2 (Carly Anderson)  
- **Date:** 2026-08-04

---

Wado. 🦅

---

**Companion documents:**
- `.empirica/governance/ARTIFACT_REGISTRY_FINDINGS.md` — Assessment + decision framework
- `.empirica/governance/ARTIFACT_REGISTRY_INDEX.yaml` — Metadata template (local mirror)
- `.github/workflows/registry-mirror-sync.yml` — CI check (mirror divergence alert)
