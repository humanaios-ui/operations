"""Private master profile -> bounded Resource Miner projection.

This module never fetches credentials, writes back to source, or publishes personal
data. Authenticated git checkouts are read at HEAD, exact paths only. The human
operator chooses when to run it and must opt in to local matching.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .portfolio_maintainer import (
    BUSINESS_SCHEMA, BUSINESS_SOURCE, PROFILE_SCHEMA, observe_portfolio,
)

MASTER_PATH = "src/data/master_profile.yaml"
SEED_PATH = "SEED.md"
CONSUMER_PATH = "lib/matching/humanaios-profile.ts"
MASTER_REPO = "humanaios-ui/humanaios-internal"
SEED_REPO = "humanaios-ui/operations"
CONSUMER_REPO = "humanaios-ui/opportunity-aggregator"
REV = re.compile(r"^[a-f0-9]{40}$")


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True, capture_output=True, text=True, timeout=15,
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("authenticated local git read failed") from exc
    return result.stdout.strip()


def _approved_repo(root: str | Path, expected: str) -> Path:
    try:
        path = Path(root).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        raise ValueError("repository checkout not found") from None
    if not path.is_dir():
        raise ValueError("repository checkout must be a directory")
    remote = _git(path, "remote", "get-url", "origin").rstrip("/")
    accepted = (
        f"https://github.com/{expected}",
        f"https://github.com/{expected}.git",
        f"git@github.com:{expected}.git",
        f"git@github.com:{expected}",
        f"ssh://git@github.com/{expected}.git",
    )
    if remote not in accepted:
        raise ValueError("repository origin does not match pinned source")
    return path


def _git_file(root: str | Path, repo: str, file_path: str) -> tuple[str, str]:
    checkout = _approved_repo(root, repo)
    revision = _git(checkout, "rev-parse", f"HEAD:{file_path}")
    if not REV.fullmatch(revision):
        raise ValueError("invalid source blob SHA")
    # Read by the resolved blob SHA so the reported revision is the content read.
    size = _git(checkout, "cat-file", "-s", revision)
    if not size.isdigit() or int(size) > 200_000:
        raise ValueError("source exceeds bounded read limit")
    data = _git(checkout, "cat-file", "blob", revision)
    return revision, data


def load_private_master(private_checkout: str | Path) -> tuple[dict[str, Any], str]:
    """Read only the committed, exact master profile; never PROFILE.yaml."""
    revision, source = _git_file(private_checkout, MASTER_REPO, MASTER_PATH)
    try:
        import yaml  # optional local package dependency; never CI secret injection
    except ImportError as exc:
        raise RuntimeError("install PyYAML locally before running this command") from exc
    try:
        profile = yaml.safe_load(source)
    except yaml.YAMLError:
        # Do not chain: the parser error embeds a snippet of private source.
        raise ValueError("invalid master profile YAML") from None
    if not isinstance(profile, dict):
        raise ValueError("invalid master profile YAML")
    required = {"version", "profile_id", "contact", "summary",
                "competencies", "achievements", "experience", "education", "metadata"}
    if not required.issubset(profile):
        raise ValueError("master profile lacks required sections")
    if not isinstance(profile["competencies"], dict):
        raise ValueError("missing competency map")
    if not isinstance(profile["experience"], list):
        raise ValueError("missing experience records")
    return profile, revision


def narrow_capabilities(master: dict[str, Any]) -> list[str]:
    """Classify broad work domains. Never forward free text or identity."""
    competencies = master["competencies"]
    out = []
    if competencies.get("ai_research"):
        out.append("ai_evaluation")
    if competencies.get("data_quality"):
        out.append("data_quality")
    if competencies.get("operations"):
        out.append("research_operations")
    technical = competencies.get("technical_skills") or {}
    if isinstance(technical, dict):
        if technical.get("quality_compliance"):
            out.append("quality_compliance")
        if technical.get("data_analytics"):
            out.append("statistical_analysis")
        if technical.get("infrastructure"):
            out.append("workflow_automation")
    return out


def project_personal(master: dict[str, Any], revision: str,
                     *, owner_approved: bool) -> dict[str, Any]:
    if not owner_approved:
        raise PermissionError("explicit local owner approval required")
    return {
        "schema": PROFILE_SCHEMA,
        "capability_codes": narrow_capabilities(master),
        "approved_for_local_matching": True,
        "revision": revision,
    }


def project_seed(ops_checkout: str | Path) -> dict[str, Any]:
    revision, text = _git_file(ops_checkout, SEED_REPO, SEED_PATH)
    normalized = text.casefold()
    if ("humanaios llc" not in normalized
            or "behavioral observability" not in normalized
            or "trl 2" not in normalized):
        raise ValueError("SEED content does not support expected research-stage anchor")
    return {
        "schema": BUSINESS_SCHEMA,
        "source_url": BUSINESS_SOURCE,
        "revision": revision,
        "stage": "research",
        "legal_form": "llc",
        "focus": "behavioral_observability",
    }


def project_consumer(consumer_checkout: str | Path) -> tuple[dict[str, Any], str]:
    revision, source = _git_file(consumer_checkout, CONSUMER_REPO, CONSUMER_PATH)
    # Bounded extraction from known TS source. No JavaScript evaluation.
    scope = source.split("export const humanaiosProfile", 1)
    if len(scope) != 2:
        raise ValueError("consumer export missing")
    text = scope[1].split("/**\n * Calculate grant relevance", 1)[0]
    # Reject backslash escapes and require a property boundary: a truncated
    # description would hide an unsupported claim behind NO_DRIFT_OBSERVED.
    desc = re.search(r"description:\s*'([^'\\]{1,2000})'\s*[,}]", text)
    stage = re.search(r"fundingStage:\s*'([a-z-]+)'", text)
    budget = re.search(r"budgetRange:\s*(null|\{)", text)
    team = re.search(r"teamProfile:\s*\{\s*size:\s*'([a-z]+)'", text)
    if not (desc and stage and budget and team):
        raise ValueError("consumer model could not be read safely")
    return ({
        "description": desc.group(1),
        "fundingStage": stage.group(1),
        "budgetRange": None if budget.group(1) == "null" else "UNAPPROVED_RANGE",
        "teamSize": team.group(1),
    }, revision)


def read_local_portfolio(
    private_checkout: str | Path,
    operations_checkout: str | Path,
    consumer_checkout: str | Path,
    *,
    owner_approved: bool = False,
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One explicit, bounded local read of all three authoritative source roles.

    Reads local committed HEAD only; HEAD is not verified as reachable from origin/main.
    """
    if not owner_approved:
        raise PermissionError("explicit local owner approval required")
    master, master_rev = load_private_master(private_checkout)
    personal = project_personal(master, master_rev, owner_approved=owner_approved)
    seed = project_seed(operations_checkout)
    consumer, consumer_rev = project_consumer(consumer_checkout)
    report = observe_portfolio(personal, seed, consumer, prior=prior)
    report["source_consumer_revision"] = consumer_rev
    report["read_mode"] = "LOCAL_GIT_HEAD_ONLY"
    report["template_status"] = "MASTER_REMAINS_PRIVATE_APPLICATION_SOURCE"
    return report
