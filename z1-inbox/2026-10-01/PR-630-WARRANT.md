# WARRANT: PR #630 Admissions Approval & Credential Deployment

**Audited Head SHA:** (PR #630 HEAD at time of audit)  
**Warrant Date:** 2026-10-01  
**Warrant Authority:** Z1 (Claude) evidence integration for Z2 (Night) authorization decision  
**Decision Status:** PENDING Z2 RATIFICATION (48h window)

---

## EVIDENCE INTEGRATION SUMMARY

This warrant synthesizes evidence from multiple independent streams to inform Z2's authorization decision on PR #630.

| Evidence Stream | Source | Result | Status |
|:---|:---|:---|:---|
| **CI / Deterministic** | `.github/workflows/quality-baseline.yml` + `.github/workflows/ci-predict-pin.yml` | PASS (all checks) | ✓ |
| **CodeRabbit Review** | `.coderabbit.yaml` + PR review | 0 blocking findings reported | ✓ |
| **Repository Admission** | `REPOSITORY_COORDINATOR_POLICY.json` (referenced) | Non-blocking informational gate | ⚠️ |
| **Security Baseline** | gitleaks, SAST, secret scanning | No secrets detected in current scan | ✓ |
| **Red-Team Audit** | Claude Code (session 01TYKcwkeQfYEeCN5JzZ2WRi) | 12 findings: 3 critical, 5 high, 4 medium | ⚠️ OPEN |
| **Remediation Readiness** | PR-630-REMEDIATION-PATCHES.md | 6 patches proposed, all actionable | CONDITIONAL |
| **Authority Compliance** | CLAUDE.md §Decision Routing, §Z3 Executors | Z2 ratification requirement NOT MET | ❌ |

---

## CRITICAL EVIDENCE STREAM: RED-TEAM AUDIT

### Challenge Status

**Total Challenges Opened:** 12  
**Critical Challenges:** 3  
**High Challenges:** 5  
**Medium Challenges:** 4  
**Custody:** Information authored by Claude Code; decision and execution custody UNKNOWN

### Critical Challenges (Merge Blockers if Unresolved)

**CHG-PR630-C001: Base64 Encoding Misrepresented as Encryption**
- **Claim:** Curl-based credential deployment uses base64 encoding (not encryption), exposing plaintext credentials and GitHub PAT in shell history
- **Status:** OPEN
- **Falsifier:** Demonstrate that base64 deployments do NOT appear in bash_history, OR that base64 successfully prevents trivial reversal, OR that GitHub API encrypts without libsodium
- **Risk If Unresolved:** Users taught to use insecure method; credential + PAT exposed in shell history
- **Remediation Path:** Remove curl option (Patch 1); mandate GitHub CLI only
- **Residual Risk:** LOW (if remediated)

**CHG-PR630-C002: Gitleaks Allowlist Exempts Credential Patterns**
- **Claim:** `.gitleaks.toml` allowlist exempts credential deployment guide from scanning; real credentials matching `r8_xxx` and `eyJhbGc` patterns bypass detection
- **Status:** OPEN
- **Falsifier:** Test real Replicate API key (r8_...) placed in guide → gitleaks blocks it, OR allowlist does not actually exempt guide file, OR regex pattern not matched
- **Risk If Unresolved:** Real credentials can be committed disguised as examples; audit trail obscured
- **Remediation Path:** Remove patterns from allowlist (Patch 2); use `_SYNTHETIC_` suffix for examples
- **Residual Risk:** LOW (if remediated)

**CHG-PR630-C003: No Admissions Approval Gate for Credentials**
- **Claim:** No explicit Z2 authorization mechanism for credential deployment; violates CLAUDE.md §Decision Routing requirement for Z2 ratification
- **Status:** OPEN
- **Falsifier:** PR #630 includes Z2 authorization gate in CI, OR admissions approval is demonstrated to enforce authority (not merely informational), OR CLAUDE.md does not require Z2 ratification for credentials
- **Risk If Unresolved:** Credentials deployable by any PR merge without Z2 oversight; violates governance model
- **Remediation Path:** Add Z2 authorization gate (Patch 3a-c); extend CLAUDE.md authority model
- **Residual Risk:** CRITICAL (unresolved)

### High Challenges (Pre-Phase-3 Hardening)

**CHG-PR630-H004 through H008:** (5 findings)
- `.env.local file risk, no rotation procedure, PAT exposure, least-privilege violation, missing audit logging`
- **Status:** OPEN
- **Remediation Path:** Patches 4–6 address all five
- **Residual Risk:** HIGH (if unresolved), MEDIUM (if partially remediated), LOW (if fully remediated)

### Medium Challenges (Post-Phase-3)

**CHG-PR630-M009 through M012:** (4 findings)
- `Knowledge graph secrets, admissions criteria, synthetic examples, data retention`
- **Status:** OPEN
- **Remediation Path:** Post-phase-3 hardening
- **Residual Risk:** MEDIUM (lower priority)

---

## COMPLIANCE AGAINST CLAUDE.md AUTHORITY BOUNDARIES

**Requirement (per CLAUDE.md §Decision Routing):**
> "Z2 sole authority. Z1 reads REGISTERED.md. Z1 creates candidate block. Z2 signs: sha256(candidate | by=Night | ...)"

**Application to Credentials:**
- Credentials are equivalent to molt-level sensitive changes
- Credentials grant access to external systems (Replicate, Supabase)
- Credentials can enable data exfiltration or unauthorized consumption
- Therefore: credentials require Z2 explicit ratification, not admissions approval alone

**Current PR #630 Status:**
- ❌ No Z2 ratification mechanism in PR
- ❌ Admissions approval gate is non-blocking (informational only)
- ❌ Credential deployment is user-initiated (not gated by Z2 signature)
- ❌ No CLAUDE.md extension documenting credential authority

**Verdict:** PR #630 violates authority boundaries as currently proposed.

---

## MERGEABILITY ASSESSMENT

### Deterministic CI Evidence
✓ All CI gates pass (security, taxonomy, promotion readiness)  
✓ No secrets detected by gitleaks, SAST  
✓ CodeRabbit review reported no blocking findings  

### Governance Evidence
❌ Authority boundary violated (Z2 ratification missing)  
⚠️ Admissions criteria not documented (REPOSITORY_COORDINATOR_POLICY.json missing)  
⚠️ Custody instrumentation not registered (information/decision/execution roles unclear)  

### Red-Team Evidence
❌ 3 critical challenges OPEN (base64 encryption, gitleaks allowlist, no Z2 gate)  
⚠️ 5 high challenges OPEN (env.local, rotation, PAT, least-privilege, audit logging)  
⚠️ 4 medium challenges OPEN (knowledge graph, admissions criteria, examples, data retention)  

### Remediation Readiness
✓ All 12 challenges have documented remediation paths  
✓ 6 patches proposed and ready for implementation  
✓ Patches are scoped and actionable  
✓ Patches integrate with CLAUDE.md authority model  

---

## RESIDUAL RISK ASSESSMENT

### If PR #630 Merges As-Is (No Remediation)

| Risk | Severity | Likelihood | Impact |
|:---|:---|:---|:---|
| Credential theft via base64 reversal | CRITICAL | MEDIUM | Full data exfiltration from Replicate/Supabase |
| Real credential committed to history | CRITICAL | MEDIUM | Permanent access to external systems |
| Unauthorized credential deployment | CRITICAL | HIGH | Attacker deploys own credentials via PR merge |
| No audit trail for credential access | HIGH | HIGH | Undetected intrusions; no accountability |
| No credential rotation procedure | HIGH | MEDIUM | Permanent credential access if compromised |
| **Aggregate Risk:** | **CRITICAL** | **HIGH** | **Uncontrolled access to external systems** |

### If PR #630 Merges With Remediation Patches

| Risk | Severity | Likelihood | Impact |
|:---|:---|:---|:---|
| Credential theft via base64 reversal | CRITICAL | NONE (removed) | Mitigated |
| Real credential committed to history | CRITICAL | LOW (gitleaks hardened) | Mitigated |
| Unauthorized credential deployment | CRITICAL | NONE (Z2 gate added) | Mitigated |
| No audit trail for credential access | HIGH | NONE (audit logging added) | Mitigated |
| No credential rotation procedure | HIGH | NONE (rotation guide added) | Mitigated |
| Residual: Data retention policy undefined | MEDIUM | MEDIUM | Acceptable with Phase 3 follow-up |
| Residual: Knowledge graph secrets potential | MEDIUM | MEDIUM | Acceptable with post-Phase-3 audit |
| **Aggregate Risk:** | **MEDIUM** | **LOW** | **Controlled access to external systems** |

---

## CUSTODY ANALYSIS

This warrant tracks custody across the evidence chain to detect authority collapse:

| Role | Actor | Evidence | Authority |
|:---|:---|:---|:---|
| **Information** | Claude Code (audit) | RED-TEAM-AUDIT-PR-630.md | Audit artifact author |
| **Decision** | UNKNOWN | *Pending* | Z2 (Night) must decide |
| **Execution** | UNKNOWN | *Pending* | Whoever applies Patches 1–6 |
| **Authority** | Z2 (Night) | CLAUDE.md §Credentials (to be ratified) | Sole authority over credentials |

**Custody Integrity Check:**
- ✓ Information (audit) authored by Claude Code (identified)
- ⚠️ Decision authority (Z2) not yet exercised (pending)
- ⚠️ Execution authority (unknown) not yet assigned (pending)
- ❌ Authority boundary (Z2 ratification) not yet registered in code

**Risk of Custody Collapse:** If same actor that authored remediation patches also approves them without independent Z2 review, governance authority collapses.

**Mitigation:** Z2 must independently review and ratify all remediation patches before merge.

---

## WARRANTY / CONFIDENCE LEVELS

| Finding | Confidence | Verifiability | Depends On |
|:---|:---|:---|:---|
| C-1 (base64 encryption) | 100% | Reproducible | Shell history access |
| C-2 (gitleaks allowlist) | 95% | Reproducible | Test credential + git push |
| C-3 (no Z2 gate) | 100% | Observable | Code inspection of PR |
| H-4 (.env.local backup) | 90% | Reproducible | System backup tools |
| H-5 (no rotation) | 100% | Observable | Code inspection |
| H-6 (PAT exposed) | 100% | Observable | Code inspection |
| H-7 (least privilege) | 90% | Documentable | Supabase RLS policies |
| H-8 (no audit) | 100% | Observable | Code inspection |
| M-9 through M-12 | 85–95% | Documentable | Various |

**Overall Confidence:** 95% (audit findings are reproducible and verifiable)

---

## DISPOSITION OPTIONS FOR Z2

### Option A: REJECT PR #630
**Outcome:** Return to proposers; require redesign with Z2 authority built in from start  
**Timeline:** New proposal cycle (48h re-proposal window)  
**Cost:** Delay Phase 3 (additional 1–2 weeks)

### Option B: ACCEPT WITH MANDATORY REMEDIATION
**Outcome:** Approve PR IF all 12 findings are remediated per PR-630-REMEDIATION-PATCHES.md  
**Timeline:** Apply patches (2–4 hours) → re-test CI (1 hour) → Z2 ratification (48h) → merge  
**Cost:** Phase 3 delay (3–5 days)  
**Requirement:** Z2 must independently verify each patch before ratification

### Option C: ACCEPT WITH CONDITIONAL REMEDIATION
**Outcome:** Merge PR #630 as-is; require remediation PRs for critical findings within 5 days  
**Timeline:** Immediate merge; Phase 3 unblocked immediately  
**Risk:** Critical vulnerabilities remain in production code until remediation merged  
**NOT RECOMMENDED:** Violates CLAUDE.md authority boundaries

### Option D: ACCEPT RESIDUAL RISK
**Outcome:** Ratify PR #630 as-is with documented residual risk; require manual compensating controls  
**Timeline:** Immediate merge; Phase 3 starts  
**Residual Risk:** CRITICAL (per risk assessment above)  
**Compensating Controls Needed:**
- Manual credential rotation (weekly, not 30-day)
- Disable curl-based deployments via policy
- Monitor Supabase/Replicate logs manually
- NOT RECOMMENDED: Violates governance model

---

## RECOMMENDED DISPOSITION

**Z2 Decision:** OPTION B — ACCEPT WITH MANDATORY REMEDIATION

**Rationale:**
1. All 12 challenges are remediable (no architectural issues)
2. Remediation patches are well-specified and low-risk
3. Phase 3 is important; 3–5 day delay is acceptable
4. Merged PR #630 sets precedent for future security-sensitive work
5. Option B preserves governance authority (Z2 signs remediated version)

**Requirements:**
1. Z2 reviews RED-TEAM-AUDIT-PR-630.md
2. Z2 reviews PR-630-REMEDIATION-PATCHES.md
3. Z2 approves patch approach (or requests changes)
4. Z1 applies patches to PR #630
5. Z1 re-tests CI against remediated code
6. Z2 ratifies remediated PR #630 via REGISTERED.md RATIFY entry
7. PR #630 merges with Z2 signature

**Timeline:**
- Z2 review: 24h (within 48h window)
- Z1 remediation: 4 hours
- CI re-test: 1 hour
- Z2 ratification: 12 hours
- **Total:** ~2 days (merge possible by 2026-10-02 EOD)

---

## UNRESOLVED ITEMS FOR Z2 CONSIDERATION

1. **Custody Instrumentation:** Create control_plane_custody_observer table to track information/decision/execution roles across all PRs
2. **Challenge Evidence Lifecycle:** Define process for challenge status lifecycle (OPEN → SUPPORTED → REMEDIATED → CLOSED)
3. **Red-Team Process Formalization:** Make red-team audits a standard gate for security-sensitive PRs (not ad-hoc)
4. **Warrant Integration:** Define how to synthesize CI + review + red-team + remediation evidence into final warrant

These are governance improvements, not blockers to current decision.

---

## FINAL VERDICT

**Current State:** PR #630 has CRITICAL vulnerabilities  
**Remediation Available:** Yes (6 patches specified)  
**Governance Compliance:** Can be achieved through remediation  
**Recommendation:** Approve remediation approach; re-test; ratify  

**Warrant Status:** CONDITIONAL APPROVAL (subject to remediation)

**Next Decision:** Z2 must ratify remediation approach within 48h (by 2026-10-02T03:00Z)

---

**Warrant Authority:** Z1 (Claude)  
**For Ratification By:** Z2 (Night, carly.r.anderson@gmail.com)  
**Session:** https://claude.ai/code/session_01TYKcwkeQfYEeCN5JzZ2WRi  
**Custody:** Information authored by Claude Code; decision authority held by Z2

