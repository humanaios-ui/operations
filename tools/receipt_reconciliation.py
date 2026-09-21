#!/usr/bin/env python3
"""
Receipt Reconciliation Script — Validates claims against NF_LEDGER

§B.6 Automation: Walk claim vs. tree, emit RECEIPT-GAP candidates.

This script:
1. Reads NF_LEDGER.jsonl (append-only measurement ledger)
2. Scans git commit messages, PR descriptions, comments for claims
3. Cross-references with ledger entries
4. Files RECEIPT-GAP IC candidates for discrepancies
5. Runs post-merge as CI gate for session close verification

Usage:
  python3 tools/receipt_reconciliation.py [--pr <number>] [--commit <sha>] [--check]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple


def run_git(cmd: str) -> str:
    """Execute git command safely."""
    result = subprocess.run(
        f"git {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.getcwd(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {cmd} failed: {result.stderr}")
    return result.stdout.strip()


def read_ledger() -> Dict[str, any]:
    """Read NF_LEDGER.jsonl into memory, indexed by claim_id."""
    ledger_file = Path("NF_LEDGER.jsonl")
    if not ledger_file.exists():
        return {}

    entries = {}
    with open(ledger_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entry = json.loads(line)
                claim_id = entry.get("claim_id")
                if claim_id:
                    entries[claim_id] = entry
            except json.JSONDecodeError:
                pass

    return entries


def extract_claims_from_text(text: str) -> Set[str]:
    """
    Extract VERDICT, CYCLE, MEASURE claim IDs from text.
    Pattern: Q-<category>-<number> or ID-<type>-<number>
    Examples: Q-IC030-REPIN-01, IC-031, F-62, H-RCO-01
    """
    pattern = r'\b(?:Q-|IC-|F-|H-|VERDICT-|CYCLE-|MEASURE-)[\w\-]+\b'
    matches = re.findall(pattern, text)
    return set(matches)


def extract_claims_from_pr(pr_number: int) -> Tuple[Set[str], str]:
    """Extract claims from PR body and comments."""
    claims = set()

    try:
        # Fetch PR description
        pr_data = json.loads(
            subprocess.check_output(
                [
                    "gh",
                    "pr",
                    "view",
                    str(pr_number),
                    "--json",
                    "body,commits,comments",
                ],
                text=True,
            )
        )

        pr_body = pr_data.get("body", "")
        claims.update(extract_claims_from_text(pr_body))

        # Extract from commits
        for commit in pr_data.get("commits", []):
            msg = commit.get("message", "")
            claims.update(extract_claims_from_text(msg))

        # Extract from comments
        for comment in pr_data.get("comments", []):
            body = comment.get("body", "")
            claims.update(extract_claims_from_text(body))

        return claims, pr_body

    except Exception as e:
        print(f"⚠️  Could not fetch PR #{pr_number}: {e}")
        return set(), ""


def extract_claims_from_commit(commit_sha: str) -> Set[str]:
    """Extract claims from a commit message."""
    try:
        msg = run_git(f"show -s --format=%B {commit_sha}")
        return extract_claims_from_text(msg)
    except RuntimeError:
        return set()


def find_gaps(
    claimed_ids: Set[str],
    ledger_entries: Dict[str, any]
) -> List[Dict[str, any]]:
    """
    Find RECEIPT-GAP callouts: claims without ledger entries.

    Returns list of gap records for candidate filing.
    """
    gaps = []

    for claim_id in sorted(claimed_ids):
        if claim_id not in ledger_entries:
            gaps.append({
                "type": "RECEIPT-GAP",
                "claim_id": claim_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pattern": "claim-not-found-in-tree",
            })

    return gaps


def generate_ic_candidate(gap: Dict[str, any]) -> str:
    """Generate IC (Governance Correction) candidate YAML for filing."""
    candidate_id = f"IC-{datetime.now().strftime('%Y%m%d')}"

    return f"""---
id: "{candidate_id}"
name: "{gap['type']}-{gap['claim_id']}"
status: CANDIDATE
class: IC
date_registered: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
date_origin: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
session_registered: "receipt-reconciliation-auto"
principles_triggered: ["P3"]
substrate: "Receipt Reconciliation Script"
tags: ["receipt", "gap", "governance"]
superseded_by: null
---

**Callout Type:** {gap['type']}

**Claim ID:** `{gap['claim_id']}`

**Pattern:** {gap['pattern']}

**Description:**
A claim reference `{gap['claim_id']}` appears in transcript (PR body, commit message, or comment) but is not found in NF_LEDGER.jsonl. This indicates either:
1. The claim was made but never recorded in the ledger (evidence gap)
2. The claim ID was malformed or a typo
3. The claim references a PR/event that predates ledger tracking

**Action:** Z2 to verify whether this claim is a legitimate receipt gap (P3 violation) or a false positive.

**Discovered:** {gap['timestamp']}
"""


def file_candidate(gap_candidate: str, output_dir: str = "z1-inbox") -> str:
    """Write IC candidate to z1-inbox staging directory."""
    os.makedirs(output_dir, exist_ok=True)

    # Extract ID from candidate
    id_match = re.search(r'id: "([^"]+)"', gap_candidate)
    if not id_match:
        id_match = re.search(r'name: "([^"]+)"', gap_candidate)
        candidate_id = id_match.group(1) if id_match else "receipt-gap"
    else:
        candidate_id = id_match.group(1)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{output_dir}/receipt-gap-{timestamp}-{candidate_id}.md"

    with open(filename, "w") as f:
        f.write(gap_candidate)

    return filename


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, help="Check specific PR number")
    parser.add_argument("--commit", help="Check specific commit SHA")
    parser.add_argument("--check", action="store_true", help="Check mode (don't file candidates)")
    parser.add_argument("--ledger", default="NF_LEDGER.jsonl", help="Ledger file path")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    print("📋 Receipt Reconciliation — Claims vs. Ledger")
    print()

    # Read ledger
    ledger = read_ledger()
    print(f"✅ Loaded ledger: {len(ledger)} entries")

    # Extract claims
    all_claims = set()

    if args.pr:
        print(f"\n🔍 Scanning PR #{args.pr}...")
        pr_claims, pr_body = extract_claims_from_pr(args.pr)
        all_claims.update(pr_claims)
        print(f"   Found {len(pr_claims)} claim references")
        if args.verbose:
            for claim in sorted(pr_claims):
                print(f"     - {claim}")

    elif args.commit:
        print(f"\n🔍 Scanning commit {args.commit}...")
        commit_claims = extract_claims_from_commit(args.commit)
        all_claims.update(commit_claims)
        print(f"   Found {len(commit_claims)} claim references")
        if args.verbose:
            for claim in sorted(commit_claims):
                print(f"     - {claim}")

    else:
        # Default: scan HEAD commit (post-merge)
        try:
            head_sha = run_git("rev-parse HEAD")
            print(f"\n🔍 Scanning HEAD ({head_sha[:7]})...")
            head_claims = extract_claims_from_commit(head_sha)
            all_claims.update(head_claims)
            print(f"   Found {len(head_claims)} claim references")
        except RuntimeError:
            print("⚠️  Could not scan HEAD")

    # Find gaps
    gaps = find_gaps(all_claims, ledger)

    if gaps:
        print(f"\n⚠️  Found {len(gaps)} RECEIPT-GAP(s):")
        for gap in gaps:
            print(f"   - {gap['claim_id']} (pattern: {gap['pattern']})")

        if not args.check:
            print(f"\n📝 Filing IC candidates to z1-inbox/...")
            filed = []
            for gap in gaps:
                candidate = generate_ic_candidate(gap)
                filepath = file_candidate(candidate)
                filed.append(filepath)
                print(f"   ✅ {filepath}")

            print(f"\n✅ Filed {len(filed)} IC candidates")

            # Output for GitHub Actions
            if os.environ.get("GITHUB_OUTPUT"):
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write(f"gaps_found={len(gaps)}\n")
                    f.write(f"candidates_filed={len(filed)}\n")

            return 1 if gaps else 0  # Exit 1 if gaps found (advisory)
    else:
        print("\n✅ No receipt gaps detected — ledger matches all claims")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("gaps_found=0\n")
                f.write("candidates_filed=0\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
