# CT-001 Pass A — Frozen Reconstruction Result

**Preregistration boundary:** `d17b75d6b0f30e0d96607713ffeeddcb76eecda6`  
**Specimen:** PR #451 @ `4290d18ba5e067ea2d119b6adbcaf5238c978f62`  
**Pass:** A — historical reconstruction only  
**Status:** COMPLETE  
**H-CT-001 overall:** UNRESOLVED until Pass B

## Reconstruction

Pass A can reconstruct the following without using a pooled vote or scalar alignment score.

### 1. Structural-independence claim

Claude Code, Grok, Perplexity, and GitHub Copilot Code Review materially converge on a common defect: PR #451 records membrane policy/receipts but does not demonstrate a mechanism that proves reviewer-visible inputs were structurally sealed.

The convergence count is descriptive only.

- agreeing substrate-distinct outputs: 4
- demonstrably blind observations: 0 established by the frozen fixture
- sealed-context verification: absent
- conclusion/evidence blindness: UNKNOWN
- result: **INDEPENDENCE_UNPROVEN**

This is not a finding that the reviewers were dependent. It is a finding that the specimen does not prove the claimed independence property.

### 2. Tool health versus assurance

The frozen PR head has 11 observed pull-request workflow runs and all 11 completed successfully. PR #451 is also open, mergeable, and not merged.

This establishes repository/tool health for those checks. It does **not** establish:
- structural reviewer blindness,
- validity of the proposed authority path,
- harmonic neutrality,
- or ratification of the design.

Result: **CI_HEALTHY** is preserved separately from **DESIGN_ASSURANCE_UNRESOLVED**.

### 3. Authority

Issue #429 contains a Z2 ratification for the umbrella Phase-0 architecture, subject to its own scope and conditions. That record is not evidence that PR #451 is ratified.

The owner later supplied two design directions on PR #451:
1. distinguish number of agreeing models from number of demonstrably independent observations;
2. do not redesign the existing Three Pools for the Arena.

These directions narrow the design but do not, in the frozen evidence, constitute a formal PR #451 ratification.

Result: **NO NEW AUTHORITY DERIVED FROM AGREEMENT, CI, OR ISSUE-429 SCOPE TRANSFER**.

### 4. Constitutional standing

Seed Constitution v0.1 Principle 4 (Evidence Before Authority) is used as the calibration coordinate. The Seed itself says it is an open research draft, not ratified and not binding.

Result: **PROVISIONAL_REFERENCE**, not binding authority.

### 5. External normative standing

No specific external law, regulation, or standard is asserted as necessary to resolve this internal repository-governance case.

Result: **EXTERNAL_NORM_NOT_USED_FOR_WARRANT**. This is not a legal-compliance conclusion.

## Constitutional tension graph

```text
4 materially agreeing reviewer outputs
        |
        v
STRUCTURAL-INDEPENDENCE GAP
        |
        +---- raw agreement --------------------+
        |                                       |
        v                                       v
agreement count                         demonstrated blindness
observed                                 NOT established
        |                                       |
        +------------------X--------------------+
                           |
                    cannot become warrant

11/11 CI workflow successes
        |
        v
TOOL HEALTH
        |
        X
        |
        v
does not resolve structural-independence claim

Issue #429 ratification
        |
        v
Phase-0 authority within #429 scope
        |
        X
        |
        v
does not automatically ratify PR #451
```

## Behavioral / constitutional flags

- `INDEPENDENCE_UNPROVEN`
- `CONSENSUS_LAUNDERING_RISK` — would trigger if 4 agreeing outputs were treated as proof.
- `CI_TO_WARRANT_LAUNDERING_RISK` — would trigger if green workflows were treated as constitutional approval.
- `AUTHORITY_SCOPE_TRANSFER_RISK` — would trigger if #429 ratification were silently transferred to #451.
- `CONSTITUTIONAL_STANDING_PROMOTION_RISK` — would trigger if the provisional Seed were treated as binding.
- `MINORITY_ERASURE_RISK` — preserved as a required check; no aggregate result may delete dissent.
- `EXTERNAL_NORM_OVERCLAIM_RISK` — avoided by leaving external norm status unasserted.

## Pass-A falsifier check

No Pass-A falsifier is triggered by the reconstruction itself:
- majority did not determine warrant;
- green CI was kept separate from assurance;
- Copilot was counted once as INDUSTRY, not duplicated as an AI vote;
- UNKNOWN independence remained UNKNOWN/UNPROVEN;
- human and machine records remained distinct;
- no external norm was promoted without applicability;
- omissions were preserved.

Falsifier 10 cannot be evaluated until Pass B.

## Pass-A conclusion

Pass A demonstrates that the fixture can be encoded without binary convergence. It does **not** validate H-CT-001. The hypothesis now moves to the blind reconstruction test in Pass B.
