#!/usr/bin/env python3
"""GitHub integration for PR Manager. Standing: STUB until MCP fetchers wired (Phase 1)."""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class GitHubPRData:
    number: int
    title: str
    body: str
    author: str
    created_at: str
    updated_at: str
    branch: str
    target: str
    url: str
    state: str
    draft: bool
    merge_conflict: bool
    reviews: List[Dict[str, Any]]
    check_runs: List[Dict[str, Any]]
    labels: List[str]


class GitHubIntegration:
    """Fetches and parses PR data. STUB until MCP wired."""

    CONSTANTS_PATHS = [
        "behavior_spec.json", "RESOURCE_UNITS.yaml", "constants.json",
        "weights/", "caps/", "rubrics/",
    ]
    GATE_PATHS = [
        ".github/workflows/", ".z1-control/", "system_graph.json",
        ".github/CODEOWNERS", "ci_gates.py",
    ]

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    def parse_governance_metadata(self, body: str) -> Dict[str, Any]:
        metadata = {
            "zone": None,
            "smag_prediction": None,
            "molt_tier_claimed": None,
            "receipt_reconciliation": None,
        }
        if body is None:
            body = ""
        smag_match = re.search(r"smag_p:\s*(0\.\d{2})", body, re.IGNORECASE)
        if smag_match:
            try:
                metadata["smag_prediction"] = float(smag_match.group(1))
            except ValueError:
                pass
        molt_match = re.search(r"molt_tier_claimed:\s*`?(\d)`?", body, re.IGNORECASE)
        if molt_match:
            try:
                metadata["molt_tier_claimed"] = int(molt_match.group(1))
            except ValueError:
                pass
        if re.search(r"\[x\]\s*\*\*Z1\*\*", body, re.IGNORECASE):
            metadata["zone"] = "Z1"
        elif re.search(r"\[x\]\s*\*\*Z2\*\*", body, re.IGNORECASE):
            metadata["zone"] = "Z2"
        elif re.search(r"\[x\]\s*\*\*Z3\*\*", body, re.IGNORECASE):
            metadata["zone"] = "Z3"
        if re.search(r"\[x\]\s*\*\*Immune memory\*\*", body, re.IGNORECASE):
            metadata["receipt_reconciliation"] = True
        return metadata

    def analyze_check_runs(self, check_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis = {"status": "PASS", "failed_jobs": [], "flaky_jobs": [], "running_jobs": []}
        for run in check_runs:
            conclusion = run.get("conclusion", "pending")
            status = run.get("status", "pending")
            name = run.get("name", "Unknown")
            if status == "in_progress":
                analysis["running_jobs"].append(name)
                if analysis["status"] == "PASS":
                    analysis["status"] = "RUNNING"
            elif conclusion == "failure":
                analysis["failed_jobs"].append(name)
                analysis["status"] = "FAIL"
        return analysis

    def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        analysis = {
            "requested_reviewers": [], "approved_by": [],
            "changes_requested_by": [], "review_comments_count": 0,
        }
        reviewer_state = {}
        for review in reviews:
            reviewer = review.get("user", {}).get("login", "Unknown")
            state = review.get("state", "COMMENTED")
            reviewer_state[reviewer] = state
        for reviewer, state in reviewer_state.items():
            if state == "APPROVED":
                analysis["approved_by"].append(reviewer)
            elif state == "CHANGES_REQUESTED":
                analysis["changes_requested_by"].append(reviewer)
        return analysis

    def observe_molt_tier(self, files_changed: List[str]) -> int:
        """Observe molt tier from paths only (never from claim)."""
        has_constants = any(
            any(c in f for c in self.CONSTANTS_PATHS) for f in files_changed
        )
        has_gates = any(
            any(g in f for g in self.GATE_PATHS) for f in files_changed
        )
        if has_gates:
            return 2
        if has_constants:
            return 1
        return 0

    def estimate_molt_tier(self, files_changed: List[str], body: str) -> Dict[str, Any]:
        """effective = max(claimed, observed). Undershoot → blocker/escalate."""
        if body is None:
            body = ""
        metadata = self.parse_governance_metadata(body)
        claimed = metadata.get("molt_tier_claimed")
        observed = self.observe_molt_tier(files_changed)
        if claimed is None:
            return {"claimed": None, "observed": observed, "effective": observed, "undershoot": False}
        effective = max(claimed, observed)
        undershoot = claimed < observed
        return {
            "claimed": claimed,
            "observed": observed,
            "effective": effective,
            "undershoot": undershoot,
        }

    def estimate_merge_probability(
        self, ci_status: str, has_merge_conflict: bool,
        reviews: Dict[str, Any], smag_prediction: Optional[float],
    ) -> float:
        base_prob = smag_prediction if smag_prediction is not None else 0.75
        if ci_status == "FAIL":
            base_prob *= 0.3
        elif ci_status == "RUNNING":
            base_prob *= 0.6
        if has_merge_conflict:
            base_prob *= 0.5
        if reviews.get("changes_requested_by"):
            base_prob *= 0.6
        elif reviews.get("approved_by"):
            base_prob *= 1.1
        return max(0.0, min(1.0, base_prob))

    def estimate_time_to_merge(
        self, ci_status: str, has_merge_conflict: bool,
        reviews_pending: List[str], molt_tier: int,
    ) -> int:
        estimate = 0.0
        if ci_status == "RUNNING":
            estimate += 0.5
        elif ci_status == "FAIL":
            estimate += 1.0
        if has_merge_conflict:
            estimate += 0.5
        if reviews_pending:
            estimate += 24
        if molt_tier == 2:
            estimate += 12
        elif molt_tier == 1:
            estimate += 6
        return max(1, int(estimate + 0.5))


class PRDataValidator:
    @staticmethod
    def check_smag_prediction(pr_data: GitHubPRData, smag_prediction: Optional[float]):
        if smag_prediction is None:
            return False, "SMAG prediction missing"
        if not (0.0 <= smag_prediction <= 1.0):
            return False, f"SMAG {smag_prediction} out of range"
        return True, "SMAG valid"

    @staticmethod
    def check_molt_tier(pr_data: GitHubPRData, molt_result: Dict[str, Any]):
        effective = molt_result.get("effective", -1)
        if effective not in [0, 1, 2]:
            return False, f"Molt tier {effective} invalid"
        if molt_result.get("undershoot"):
            return False, (
                f"Molt undershoot: claimed={molt_result.get('claimed')} "
                f"< observed={molt_result.get('observed')} — escalate"
            )
        return True, f"Molt effective={effective}"

    @staticmethod
    def check_zone(pr_data: GitHubPRData, zone: Optional[str]):
        if zone is None:
            return False, "Zone not selected"
        if zone not in ["Z1", "Z2", "Z3"]:
            return False, f"Zone {zone} invalid"
        return True, f"Zone {zone}"

    @staticmethod
    def check_immunity_memory(pr_data: GitHubPRData):
        body = pr_data.body or ""
        if "IC-" in body or "F-" in body or "H-" in body:
            return True, "Immunity memory referenced"
        return None, "Receipt validation not yet wired (Phase 1)"


if __name__ == "__main__":
    integration = GitHubIntegration("humanaios-ui", "operations")
    sample = "smag_p: 0.92\nmolt_tier_claimed: `0`\n- [x] **Z1**"
    print(integration.parse_governance_metadata(sample))
    print(integration.estimate_molt_tier([".github/workflows/x.yml"], sample))
