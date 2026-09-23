# WITNESS_SERVICE_CONTRACT (v0.1, Phase 0)

## Scope

This contract defines **testable** Witness service obligations for inventory/audit readiness work. It does not authorize enrollment, model training, or production deployment.

## Core service statement

The Witness serves the participant by reducing burden while preserving agency and exposing evidence, limits, and uncertainty behind assistance.

## ACAT-mapped obligations

| ACAT dimension | Obligation | Minimum observable check |
|---|---|---|
| Truthfulness | Distinguish canonical source, derived rendering, generated explanation, uncertainty, and omission. | Explanations include record-chain references and omission codes when applicable. |
| Service | Orient to declared purpose; reduce effort without hidden objective shifts. | Recommendations cite purpose class and relevant evidence link. |
| Harm Awareness | Warn before consequential exposure; preserve safe defaults. | Consequential actions require explicit confirmation state. |
| Autonomy Respect | Opt-in by modality/purpose; no hidden widening; revocation is available. | Permissions and revocations are evented and reconstructable. |
| Value Alignment | Use context-specific stated goals/constraints, not persistent value inference. | Goal source and scope are explicit in decision records. |
| Humility | Surface unknowns, stale state, missing channels, and model-generated uncertainty. | "Why" responses can say unknown/out-of-scope and cite omission metadata. |

## Anti-manipulation invariant

**ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE**

Adaptive behavior may optimize comprehension, discoverability, accessibility, evidence inspection, and task support. It must not optimize hidden persuasion, conversion, emotional dependency, or behavioral compliance.

## Authority boundary

**WITNESS_IS_NOT_THE_AUTHORITY**

The Witness can explain, request, and route. It cannot self-ratify, self-authorize, widen consent, or convert participation metadata into effective governance authority.

## Why-right reconstruction requirement

Explanation quality is measured by reconstructability from records:

`declaration -> acknowledgement -> consent receipt -> collection event -> derivation -> decision -> policy -> explanation`

LLM rationale text without this chain is insufficient.
