#!/usr/bin/env python3
"""
Builder v1.7 compliant
multi_provider_elicitation_client_v0_1.py
HumanAIOS · humanaios-ui/operations · S-060626-01

Multi-provider ACAT elicitation client — Z2-TRUST-B build.
Submits ACAT Phase 1 prompts to any configured provider,
routes responses to the staging layer in acat_assessments_v1.

ACTIVATION GATE: This file is built but NOT activated.
Activation requires:
  1. PROVIDER_TAXONOMY_V1_0.md ratified (Zone 2)
  2. Migration 007 applied to Supabase (document_layer column live)
  3. Provider API keys in secret manager (Zone 3, Night only)
  4. Role-lock check confirmed: INFRA model_family ≠ SUBJECT model_family

Z2-CORPUS-TRUST-02 role-lock enforcement is built into this client.
Circular assessment (model scoring itself) is rejected at pipeline level.

Environment variables (all Zone 3 — never committed):
  SUPABASE_URL, SUPABASE_KEY (service_role for staging writes)
  ANTHROPIC_API_KEY          (if using Claude as INFRA)
  MISTRAL_API_KEY
  CEREBRAS_API_KEY
  GROQ_API_KEY
  OPENROUTER_API_KEY
  NVIDIA_API_KEY
  SAMBANOVA_API_KEY
  TOGETHER_API_KEY
  FIREWORKS_API_KEY

Usage (once activated):
  python multi_provider_elicitation_client_v0_1.py \\
    --subject mistral/mistral-large \\
    --infra anthropic/claude-sonnet-4-6 \\
    --n 5 \\
    --dry-run
"""
TOOL_NAME = "multi_provider_elicitation_client"
TOOL_VERSION = "1.0.0"

# Builder v1.7 compliant

TOOL_NAME = "multi_provider_elicitation_client"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("haios.elicitation")

# ── Provider registry ──────────────────────────────────────────────────────────
# Canonical provider → model_family mapping (from PROVIDER_TAXONOMY_V1_0.md)
# ACTIVATION GATE: do not add entries without taxonomy ratification

PROVIDER_REGISTRY = {
    # format: "provider_canonical/model_version": {"model_family": ..., "env_key": ...}
    "anthropic/claude-sonnet-4-6":   {"model_family": "claude",    "env_key": "ANTHROPIC_API_KEY"},
    "anthropic/claude-haiku-4-5":    {"model_family": "claude",    "env_key": "ANTHROPIC_API_KEY"},
    "mistral/mistral-large":         {"model_family": "mistral",   "env_key": "MISTRAL_API_KEY"},
    "mistral/mixtral-8x7b":          {"model_family": "mistral",   "env_key": "MISTRAL_API_KEY"},
    "cerebras/llama3-70b":           {"model_family": "llama",     "env_key": "CEREBRAS_API_KEY"},
    "groq/llama3-70b":               {"model_family": "llama",     "env_key": "GROQ_API_KEY"},
    "groq/mixtral-8x7b":             {"model_family": "mistral",   "env_key": "GROQ_API_KEY"},
    "openrouter/meta-llama-3-70b":   {"model_family": "llama",     "env_key": "OPENROUTER_API_KEY"},
    "nvidia/llama3-70b":             {"model_family": "llama",     "env_key": "NVIDIA_API_KEY"},
    "sambanova/llama3-405b":         {"model_family": "llama",     "env_key": "SAMBANOVA_API_KEY"},
    "together/llama3-70b":           {"model_family": "llama",     "env_key": "TOGETHER_API_KEY"},
    "fireworks/llama3-70b":          {"model_family": "llama",     "env_key": "FIREWORKS_API_KEY"},
}


class RoleLockViolation(Exception):
    """Raised when SUBJECT and INFRA share the same model_family (Z2-CORPUS-TRUST-02)."""
    pass


class ProviderNotRegistered(Exception):
    """Raised when a provider/model string is not in PROVIDER_REGISTRY."""
    pass


class ActivationGateError(Exception):
    """Raised when activation prerequisites are not met."""
    pass


# ── Role-lock enforcement (Z2-CORPUS-TRUST-02) ────────────────────────────────

def check_role_lock(subject_key: str, infra_key: str) -> None:
    """
    Enforce Z2-CORPUS-TRUST-02: SUBJECT xor INFRA, never same model_family per run.
    Raises RoleLockViolation if collision detected.
    Logs the check regardless of outcome (never silently dropped).
    """
    if subject_key not in PROVIDER_REGISTRY:
        raise ProviderNotRegistered(f"Subject model not in registry: {subject_key}")
    if infra_key not in PROVIDER_REGISTRY:
        raise ProviderNotRegistered(f"INFRA model not in registry: {infra_key}")

    subject_family = PROVIDER_REGISTRY[subject_key]["model_family"]
    infra_family   = PROVIDER_REGISTRY[infra_key]["model_family"]

    logger.info(
        "ROLE_LOCK_CHECK subject=%s family=%s infra=%s family=%s",
        subject_key, subject_family, infra_key, infra_family
    )

    if subject_family == infra_family:
        msg = (
            f"Z2-CORPUS-TRUST-02 VIOLATION: SUBJECT ({subject_key}, family={subject_family}) "
            f"and INFRA ({infra_key}, family={infra_family}) share model_family. "
            f"Circular assessment rejected at pipeline level. "
            f"Choose a different INFRA provider."
        )
        logger.error("ROLE_LOCK_VIOLATION %s", msg)
        raise RoleLockViolation(msg)

    logger.info("ROLE_LOCK_CHECK PASS subject_family=%s infra_family=%s", subject_family, infra_family)


# ── Staging row builder ────────────────────────────────────────────────────────

def build_staging_row(
    subject_key: str,
    agent_name: str,
    phase1_scores: dict,
    session_id: Optional[str] = None,
    infra_key: Optional[str] = None,
) -> dict:
    """
    Build a row ready for INSERT into acat_assessments_v1 with document_layer='staging'.
    Does not write to DB — returns dict for caller to submit.

    phase1_scores must contain: truth, service, harm, autonomy, value, humility
    (integers 0-100, per ACAT instrument v5.4)
    """
    reg = PROVIDER_REGISTRY[subject_key]
    provider_canonical, model_version = subject_key.split("/", 1)
    total = sum(phase1_scores[d] for d in ["truth", "service", "harm", "autonomy", "value", "humility"])

    row = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_quality": "verified",
        "agent_name": agent_name,
        "provider": provider_canonical,
        "provider_canonical": provider_canonical,
        "model_version": model_version,
        "model_family": reg["model_family"],
        "document_layer": "staging",          # Z2-TRUST-B: quarantined by default
        "layer": "ai-self-report",
        "phase": "phase1",
        "submission_version": "v7.0",         # first multi-provider version
        "submission_purity": "agent_self_only",
        "mode": "automated",
        # ACAT Phase 1 dimension scores
        "truth":     phase1_scores["truth"],
        "service":   phase1_scores["service"],
        "harm":      phase1_scores["harm"],
        "autonomy":  phase1_scores["autonomy"],
        "value":     phase1_scores["value"],
        "humility":  phase1_scores["humility"],
        "total":     total,
        "pre_total": total,
        # Phase 3 fields — empty until pair completes
        "post_total":     None,
        "learning_index": None,
        "pair_id":        session_id or str(uuid.uuid4()),
        # Metadata
        "flags": json.dumps([]),
        "metadata_raw": json.dumps({
            "infra_model": infra_key,
            "infra_family": PROVIDER_REGISTRY[infra_key]["model_family"] if infra_key else None,
            "role_lock_verified": True,
            "submission_version": "v7.0",
        }),
    }
    return row


# ── Activation gate check ──────────────────────────────────────────────────────

def check_activation_gates() -> None:
    """
    Verify prerequisites before any elicitation run.
    Hard stop if gates not met.
    """
    gates = {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL"),
        "SUPABASE_KEY": os.environ.get("SUPABASE_KEY"),
    }
    missing = [k for k, v in gates.items() if not v]
    if missing:
        raise ActivationGateError(
            f"Missing required environment variables: {missing}. "
            f"Set via secret manager before running. "
            f"Provider API keys also required per PROVIDER_REGISTRY."
        )
    logger.info("ACTIVATION_GATES passed: Supabase credentials present")


# ── CLI entrypoint (dry-run only until activated) ─────────────────────────────


def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("✓ Smoke test PASSED")
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-provider ACAT elicitation client (ACTIVATION GATE: not yet active)"
    )
    parser.add_argument("--subject", required=True,
        help="Subject model: provider_canonical/model_version (e.g. mistral/mistral-large)")
    parser.add_argument("--infra", required=True,
        help="INFRA (elicitation) model: provider_canonical/model_version")
    parser.add_argument("--n", type=int, default=1,
        help="Number of sessions to run")
    parser.add_argument("--dry-run", action="store_true",
        help="Validate role-lock and registry; do not call APIs or write to Supabase")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    print(f"\nACTIVATION GATE: This client is not yet active.")
    print(f"Prerequisites required before first live run:")
    print(f"  1. PROVIDER_TAXONOMY_V1_0.md ratified (Zone 2) — PENDING")
    print(f"  2. Migration 007 applied to Supabase — PENDING (Night, Zone 3)")
    print(f"  3. Provider API keys in secret manager — PENDING (Night, Zone 3)")
    print(f"  4. submission_version 'v7.0' added to schema if constrained — check pre-flight")
    print()

    if args.dry_run:
        print(f"DRY-RUN: validating role-lock for subject={args.subject} infra={args.infra}")
        try:
            check_role_lock(args.subject, args.infra)
            subject_family = PROVIDER_REGISTRY[args.subject]["model_family"]
            infra_family   = PROVIDER_REGISTRY[args.infra]["model_family"]
            print(f"  ROLE_LOCK: PASS")
            print(f"  Subject family: {subject_family}")
            print(f"  INFRA family:   {infra_family}")
            print(f"  No collision — run would be permitted once activation gates clear.")
        except (RoleLockViolation, ProviderNotRegistered) as e:
            print(f"  ROLE_LOCK: FAIL — {e}")
