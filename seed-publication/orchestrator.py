#!/usr/bin/env python3
"""
Seed Publication Orchestrator

Automates multi-surface publication and contribution workflow for the
Seed Constitution for Responsible AI Development, integrated with
HumanAIOS governance (Z1/Z2/Z3).

Usage:
  python orchestrator.py publish <version>      # Publish to all surfaces
  python orchestrator.py sync <platform>         # Sync specific platform
  python orchestrator.py aggregate-feedback      # Collect contributions
  python orchestrator.py emit-z1-candidate       # Create Z1 proposal
  python orchestrator.py check-z2-deadline       # Monitor ratification window
"""

import os
import json
import yaml
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import argparse
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.yaml"
REPO_ROOT = SCRIPT_DIR.parent
SEEDS_DIR = REPO_ROOT / "seeds"
Z1_INBOX = REPO_ROOT / "z1-inbox"
REGISTERED_FILE = REPO_ROOT / "REGISTERED.md"


@dataclass
class SeedVersion:
    """Represents a single version of the Seed"""
    version: str
    released_at: str
    ratified: bool
    z2_hash: Optional[str]
    contributions: List[Dict]
    platform_status: Dict[str, str]  # {platform: status}


@dataclass
class Contribution:
    """Represents a single contribution/amendment"""
    id: str
    timestamp: str
    platform: str  # github, substack, writable_wall, form
    author: str
    attribution: str
    proposed_change: str
    rationale: str
    evidence: Optional[str]
    status: str  # submitted, moderated, accepted, rejected, adopted


class SeedOrchestrator:
    """Main orchestration engine for Seed publication workflow"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.version = self.config["versioning"]["current"]
        self.repo_root = REPO_ROOT

    def publish(self, version: str, all_surfaces: bool = True, require_z2_approval: bool = None) -> Dict:
        """
        Publish a version to all enabled surfaces.

        Args:
            version: Version string (e.g., "0.1")
            all_surfaces: If True, publish to all enabled surfaces
            require_z2_approval: If True, verify Z2 ratification before publishing.
                                If None, read from config z_integration.z2_ratification.required

        Returns:
            Dict with publication results
        """
        logger.info(f"Publishing Seed v{version}")
        results = {
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "surfaces": {},
            "errors": [],
            "z2_verified": False,
        }

        # If require_z2_approval not specified, read from config
        if require_z2_approval is None:
            require_z2_approval = self.config.get("z_integration", {}).get("z2_ratification", {}).get("required", True)

        # Check Z2 ratification requirement (fail-closed: enforce unless explicitly disabled)
        if require_z2_approval:
            if not self._verify_z2_ratification(version):
                error = f"Z2 ratification required but not found for v{version}. Cannot publish without Z2 approval."
                logger.error(error)
                results["errors"].append(error)
                results["status"] = "blocked_no_z2_approval"
                return results
            results["z2_verified"] = True

        # Read the seed source
        seed_path = self._get_seed_path(version)
        if not seed_path.exists():
            error = f"Seed source not found: {seed_path}"
            logger.error(error)
            results["errors"].append(error)
            return results

        with open(seed_path) as f:
            seed_content = f.read()

        # Publish to each enabled surface
        surfaces_config = self.config["surfaces"]
        for surface_name, surface_config in surfaces_config.items():
            if not surface_config.get("enabled", True):
                logger.info(f"Skipping disabled surface: {surface_name}")
                continue

            # If all_surfaces is False, skip this surface
            if not all_surfaces:
                logger.info(f"Skipping {surface_name} (all_surfaces=False)")
                continue

            try:
                result = self._publish_to_surface(
                    surface_name, version, seed_content, surface_config
                )
                results["surfaces"][surface_name] = result
                logger.info(f"✓ Published to {surface_name}: {result['status']}")
            except Exception as e:
                error = f"Error publishing to {surface_name}: {str(e)}"
                logger.error(error)
                results["errors"].append(error)

        return results

    def _publish_to_surface(
        self, surface: str, version: str, content: str, config: Dict
    ) -> Dict:
        """Publish to a specific surface"""
        result = {"surface": surface, "status": "pending", "details": {}}

        if surface == "github":
            result = self._publish_github(version, content, config)
        elif surface == "substack":
            result = self._publish_substack(version, content, config)
        elif surface == "website":
            result = self._publish_website(version, content, config)
        elif surface == "writable_wall":
            result = self._publish_writable_wall(version, content, config)
        elif surface == "form":
            result = self._publish_form(version, config)
        elif surface == "observatory":
            result = self._publish_observatory(version, content, config)

        return result

    def _publish_github(self, version: str, content: str, config: Dict) -> Dict:
        """Publish seed source and templates to GitHub"""
        repo = config.get("repo", "humanaios-ui/operations")
        paths = config.get("paths", {})

        result = {"surface": "github", "status": "completed", "details": {}}

        # Commit seed source to repo
        seed_path = SEEDS_DIR / f"seed-constitution-v{version}.md"
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        with open(seed_path, "w") as f:
            f.write(content)

        # Stage and commit
        try:
            subprocess.run(
                ["git", "add", str(seed_path)],
                cwd=self.repo_root,
                capture_output=True,
                check=True,
            )
            commit_msg = (
                f"docs: publish Seed Constitution v{version}\n\n"
                f"- Publish working draft v{version} to seeds/\n"
                f"- Requires Z2 ratification for merge\n"
                f"- Version: {version}\n"
                f"- Status: working_draft\n\n"
                f"Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
            )
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_root,
                capture_output=True,
                check=True,
            )
            result["details"]["commit"] = "staged"
        except subprocess.CalledProcessError as e:
            result["status"] = "partial"
            result["details"]["error"] = str(e)

        result["details"]["repo"] = repo
        result["details"]["paths"] = {
            "source": str(seed_path),
            "issue_template": paths.get("issue_template", ""),
        }

        return result

    def _publish_substack(self, version: str, content: str, config: Dict) -> Dict:
        """Generate Substack post template"""
        result = {"surface": "substack", "status": "completed", "details": {}}

        post_template = SEEDS_DIR / "substack-launch-post-template.md"
        post_template.parent.mkdir(parents=True, exist_ok=True)

        substack_post = self._generate_substack_post(version, content, config)
        with open(post_template, "w") as f:
            f.write(substack_post)

        result["details"]["template_path"] = str(post_template)
        result["details"]["instructions"] = (
            "Copy this template to Substack editor and publish manually "
            "(ensure Z2 ratification before final publish)"
        )
        result["details"]["publication"] = config.get("publication", "humanaios")

        return result

    def _publish_website(self, version: str, content: str, config: Dict) -> Dict:
        """Generate website page and announce"""
        result = {"surface": "website", "status": "completed", "details": {}}

        site_page = SEEDS_DIR / f"site-page-v{version}.html"
        site_page.parent.mkdir(parents=True, exist_ok=True)

        html_content = self._generate_website_page(version, content, config)
        with open(site_page, "w") as f:
            f.write(html_content)

        result["details"]["page_path"] = str(site_page)
        result["details"]["deployment"] = (
            "Deploy to humanaios.ai/seeds/constitution after Z2 approval"
        )
        result["details"]["announcement"] = (
            f"Add link to humanaios.ai homepage once live"
        )

        return result

    def _publish_writable_wall(
        self, version: str, content: str, config: Dict
    ) -> Dict:
        """Generate Writable Wall contribution form"""
        result = {"surface": "writable_wall", "status": "completed", "details": {}}

        form_template = SEEDS_DIR / "writable-wall-form.json"
        form_template.parent.mkdir(parents=True, exist_ok=True)

        form_config = self._generate_writable_wall_form(version, config)
        with open(form_template, "w") as f:
            json.dump(form_config, f, indent=2)

        result["details"]["form_path"] = str(form_template)
        result["details"]["endpoint"] = config.get("submission_path")
        result["details"]["instructions"] = (
            "Deploy form to writable_wall endpoint and link from Seed page"
        )

        return result

    def _publish_form(self, version: str, config: Dict) -> Dict:
        """Generate simple feedback form configuration"""
        result = {"surface": "form", "status": "completed", "details": {}}

        form_config_path = SEEDS_DIR / "seed-feedback-form.json"
        form_config_path.parent.mkdir(parents=True, exist_ok=True)

        form_config = {
            "form_name": "Seed Constitution – Quick Feedback",
            "form_version": version,
            "type": config.get("type", "typeform_or_custom"),
            "description": "Quick feedback on the Seed Constitution v" + version,
            "fields": config.get("feedback_collection", {}).get("fields", []),
            "responses_path": config.get("responses_path", "seeds/feedback/{date}/{response_id}.json"),
        }

        with open(form_config_path, "w") as f:
            json.dump(form_config, f, indent=2)

        result["details"]["config_path"] = str(form_config_path)
        result["details"]["responses_path"] = form_config.get("responses_path")
        result["details"]["instructions"] = (
            "Configure form endpoint (Typeform or custom) and link from Seed page"
        )

        return result

    def _publish_observatory(self, version: str, content: str, config: Dict) -> Dict:
        """Generate Observatory/research framing note"""
        result = {"surface": "observatory", "status": "completed", "details": {}}

        obs_note = SEEDS_DIR / f"observatory-framing-v{version}.md"
        obs_note.parent.mkdir(parents=True, exist_ok=True)

        obs_content = self._generate_observatory_note(version, config)
        with open(obs_note, "w") as f:
            f.write(obs_content)

        result["details"]["note_path"] = str(obs_note)
        result["details"]["integration"] = "Link from Observatory to this note"

        return result

    def aggregate_feedback(self) -> Dict:
        """
        Aggregate contributions from all surfaces.

        Returns:
            Dict with aggregated contributions and digest
        """
        logger.info("Aggregating feedback from all surfaces")
        aggregated = {
            "timestamp": datetime.utcnow().isoformat(),
            "contributions": [],
            "by_platform": {},
            "summary": "",
        }

        # Aggregate from each source
        aggregated["by_platform"]["github"] = self._collect_github_feedback()
        aggregated["by_platform"]["substack"] = self._collect_substack_feedback()
        aggregated["by_platform"]["writable_wall"] = (
            self._collect_writable_wall_feedback()
        )
        aggregated["by_platform"]["form"] = self._collect_form_feedback()
        aggregated["by_platform"]["observatory"] = self._collect_observatory_feedback()

        # Merge all
        for platform, contributions in aggregated["by_platform"].items():
            aggregated["contributions"].extend(contributions)

        # Generate summary
        aggregated["summary"] = self._summarize_contributions(
            aggregated["contributions"]
        )

        # Write digest file
        week_num = datetime.utcnow().isocalendar()[1]
        summary_dir = SEEDS_DIR / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)
        digest_path = summary_dir / f"contributions-w{week_num}.md"

        digest_content = f"""# Seed Constitution Contribution Digest – Week {week_num}

**Generated:** {datetime.utcnow().isoformat()}

## Summary

{aggregated['summary']}

## By Platform

"""
        for platform, contributions in aggregated["by_platform"].items():
            digest_content += f"### {platform.replace('_', ' ').title()}: {len(contributions)} contributions\n\n"
            for contrib in contributions[:5]:  # Show first 5 per platform
                if isinstance(contrib, dict):
                    change = contrib.get("proposed_change", contrib.get("description", "N/A"))
                    author = contrib.get("author", contrib.get("attribution", "Anonymous"))
                    digest_content += f"- **{author}:** {change}\n"
            if len(contributions) > 5:
                digest_content += f"- ... and {len(contributions) - 5} more\n"
            digest_content += "\n"

        digest_content += f"""## Next Steps

1. Z1 (Claude) reviews all contributions
2. Create amendment candidate for next version
3. Submit to Z2 (Night) for ratification

---

*Generated by Seed Publication Orchestrator*
"""

        with open(digest_path, "w") as f:
            f.write(digest_content)

        aggregated["digest_path"] = str(digest_path)

        # Log results
        total = len(aggregated["contributions"])
        logger.info(f"Aggregated {total} contributions from all platforms")
        logger.info(f"✓ Digest written to {digest_path}")

        return aggregated

    def _verify_z2_ratification(self, version: str) -> bool:
        """Verify that Z2 has ratified this version."""
        # Check REGISTERED.md for Z2 hash signature
        if not REGISTERED_FILE.exists():
            logger.warning(f"REGISTERED.md not found, cannot verify Z2 ratification")
            return False

        with open(REGISTERED_FILE) as f:
            content = f.read()

        # Look for version-specific Z2 hash entry
        z2_pattern = f"v{version}.*z2_hash.*|Z2.*{version}.*ACCEPT"
        if not any(z2_pattern in line for line in content.split("\n")):
            logger.warning(f"No Z2 ratification found in REGISTERED.md for v{version}")
            return False

        logger.info(f"✓ Z2 ratification verified for v{version}")
        return True

    def emit_z1_candidate(
        self,
        contributions: List[Contribution],
        rationale: str,
        falsifier: str,
    ) -> Dict:
        """
        Create a Z1 candidate block for next version.

        Args:
            contributions: Accepted contributions to include
            rationale: Why these changes are proposed
            falsifier: Falsifier condition (how we'd know this failed)

        Returns:
            Dict with candidate path and content
        """
        # Validate inputs
        if not contributions:
            raise ValueError("Cannot emit candidate without contributions")
        if not rationale or not rationale.strip():
            raise ValueError("Rationale is required")
        if not falsifier or not falsifier.strip():
            raise ValueError("Falsifier is required (how would we know this failed?)")

        logger.info("Emitting Z1 candidate for next version")

        candidate_date = datetime.utcnow().strftime("%Y-%m-%d")
        candidate_dir = Z1_INBOX / candidate_date
        candidate_dir.mkdir(parents=True, exist_ok=True)

        # Generate candidate ID
        candidate_id = f"seed-amendment-{len(list(candidate_dir.glob('*.md'))) + 1}"
        candidate_path = candidate_dir / f"{candidate_id}.md"

        # Build candidate content
        candidate_content = self._build_z1_candidate(
            contributions, rationale, falsifier
        )

        with open(candidate_path, "w") as f:
            f.write(candidate_content)

        result = {
            "status": "created",
            "path": str(candidate_path),
            "candidate_id": candidate_id,
            "next_step": "Submit to Z2 (Night) for ratification",
            "deadline": (
                datetime.utcnow() + timedelta(hours=48)
            ).isoformat(),
        }

        logger.info(f"✓ Candidate created: {candidate_path}")
        logger.info(f"  Z2 decision window: 48 hours")
        logger.info(f"  Deadline: {result['deadline']}")

        return result

    def check_z2_deadline(self) -> Dict:
        """
        Check for pending Z2 ratification deadlines.

        Escalation timeline:
        - 48h: standard decision window
        - 72h: warning (escalate to Admiral if no decision)
        - 96h: auto-reject if no explicit Z2 approval

        Returns:
            Dict with deadline status
        """
        logger.info("Checking Z2 ratification deadlines")

        # Read REGISTERED.md to find pending candidates (look for structured entries)
        if not REGISTERED_FILE.exists():
            return {"status": "no_registered_file", "pending": []}

        # Check z1-inbox for candidates with PENDING_Z2_RATIFICATION status
        pending = []
        now = datetime.utcnow()

        if Z1_INBOX.exists():
            for candidate_file in Z1_INBOX.glob("**/*.md"):
                try:
                    with open(candidate_file) as f:
                        content = f.read()
                        # Look for structured status marker
                        if "PENDING_Z2_RATIFICATION" in content:
                            file_mtime = datetime.utcfromtimestamp(candidate_file.stat().st_mtime)
                            elapsed_hours = (now - file_mtime).total_seconds() / 3600

                            # Determine status based on elapsed time
                            if elapsed_hours > 96:
                                status = "auto_rejected"
                                action = "Auto-reject triggered (96h window closed)"
                            elif elapsed_hours > 72:
                                status = "overdue"
                                action = "Escalate to Admiral immediately"
                            elif elapsed_hours > 48:
                                status = "warning"
                                action = "Decision window closed, escalation pending"
                            else:
                                status = "pending"
                                hours_remaining = 48 - elapsed_hours
                                action = f"{hours_remaining:.1f} hours remaining"

                            pending.append({
                                "file": str(candidate_file),
                                "status": status,
                                "submitted_at": file_mtime.isoformat(),
                                "elapsed_hours": round(elapsed_hours, 1),
                                "action": action,
                            })
                except IOError as e:
                    logger.warning(f"Could not read candidate {candidate_file}: {e}")

        result = {
            "status": "checked",
            "timestamp": now.isoformat(),
            "pending_count": len(pending),
            "pending": pending,
            "action_required": len(pending) > 0,
            "warning_count": len([p for p in pending if p["status"] == "warning"]),
            "overdue_count": len([p for p in pending if p["status"] == "overdue"]),
            "auto_rejected_count": len([p for p in pending if p["status"] == "auto_rejected"]),
            "escalation_needed": any(p["status"] in ["overdue", "auto_rejected"] for p in pending),
        }

        if result["escalation_needed"]:
            logger.warning("⚠ Z2 escalation needed - deadlines overdue or auto-rejected")
        elif result["warning_count"] > 0:
            logger.warning(f"⚠ {result['warning_count']} candidates in warning window (48-72h)")
        elif pending:
            logger.info(f"ℹ {len(pending)} candidates awaiting Z2 decision")
        else:
            logger.info("✓ No pending Z2 decisions")

        return result

    # ========== Helper Methods ==========

    def _get_seed_path(self, version: str) -> Path:
        """Get path to seed source file"""
        return SEEDS_DIR / f"seed-constitution-v{version}.md"

    def _generate_substack_post(
        self, version: str, content: str, config: Dict
    ) -> str:
        """Generate Substack launch post from template"""
        template = f"""# Seed Constitution for Responsible AI Development – Working Draft {version}

*This is a seed, not a finished document. Comments, proposed amendments, and critiques are welcome.*

## Why This Exists

The Seed Constitution draws from HumanAIOS research on behavioral observability and agent discourse. We're opening it for community feedback to strengthen both the principles and the process.

See the full methodology at [Moltbook](https://humanaios.ai/research) and the measurement framework at [ACAT](https://humanaios.ai/acat).

---

## Core Seed

{content}

---

## How to Contribute

We invite feedback through multiple channels:

### Via Substack (here)
Leave comments below. We read every substantive response and periodically surface high-quality feedback in follow-up posts.

### Via Writable Wall
Visit [humanaios.ai/contribute](https://humanaios.ai/contribute) to submit proposed amendments or critiques directly.

### Via GitHub
File an issue or discussion at [github.com/humanaios-ui/operations](https://github.com/humanaios-ui/operations/issues) with the [seed-amendment] tag.

### Via Short Form
Quick feedback? Use our [anonymous form](https://humanaios.ai/seed-feedback).

---

## What We're Measuring

Each version is calibrated against:
- **ACAT dimensions** (Autonomy, Community, Accountability, Transparency)
- **Agent Behavior** (how well it separates concerns and enables human choice)
- **Adoption barriers** (friction in the process, language clarity)

Results feed into the [Observatory](https://humanaios.ai/observatory) and priority queue.

---

## Timeline

- **v{version}** (current): working draft, open for comment
- **v0.2** (planned): incorporates accepted amendments, re-ratification by Night
- **v1.0** (estimated): finalized after community signal and governance approval

Questions? Reply here or reach out to the HumanAIOS team.

---

*Generated with [Claude Code](https://claude.ai/code)*
"""
        return template

    def _generate_website_page(
        self, version: str, content: str, config: Dict
    ) -> str:
        """Generate HTML page for website deployment"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seed Constitution – HumanAIOS</title>
    <style>
        :root {{
            --bg: #fafafa;
            --text: #333;
            --border: #e0e0e0;
            --accent: #0066cc;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg: #1a1a1a;
                --text: #e0e0e0;
                --border: #333;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .banner {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 2rem;
        }}
        h1 {{
            margin-top: 0;
        }}
        .version {{
            color: #666;
            font-size: 0.9em;
        }}
        .links {{
            display: flex;
            gap: 1rem;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        .links a {{
            padding: 0.5rem 1rem;
            background: var(--accent);
            color: white;
            border-radius: 4px;
            text-decoration: none;
        }}
        .links a:hover {{
            opacity: 0.9;
        }}
        .content {{
            border-top: 1px solid var(--border);
            padding-top: 2rem;
        }}
        code {{
            background: var(--border);
            padding: 2px 4px;
            border-radius: 2px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="banner">
        <strong>Working Draft – Not Ratified</strong><br>
        This document is open for comment and amendment. Final ratification pending governance review.
    </div>

    <h1>Seed Constitution for Responsible AI Development</h1>
    <p class="version">Version {version} | Updated {datetime.utcnow().strftime('%Y-%m-%d')}</p>

    <div class="links">
        <a href="https://humanaios.substack.com">Read on Substack</a>
        <a href="https://github.com/humanaios-ui/operations">View on GitHub</a>
        <a href="https://humanaios.ai/contribute">Contribute Amendment</a>
        <a href="https://humanaios.ai/seed-feedback">Quick Feedback</a>
    </div>

    <div class="content">
        {self._markdown_to_html(content)}
    </div>

    <hr>
    <p style="font-size: 0.9em; color: #666;">
        Last updated: {datetime.utcnow().isoformat()}<br>
        Source: <a href="https://github.com/humanaios-ui/operations/tree/main/seeds">humanaios-ui/operations/seeds</a>
    </p>
</body>
</html>
"""
        return html

    def _generate_writable_wall_form(
        self, version: str, config: Dict
    ) -> Dict:
        """Generate Writable Wall form configuration"""
        return {
            "form_name": "Seed Constitution – Amendment Submission",
            "form_version": version,
            "description": (
                "Submit proposed changes, language improvements, or critiques "
                "to the Seed Constitution working draft."
            ),
            "fields": [
                {
                    "id": "proposed_change",
                    "label": "Proposed Change or Critique",
                    "type": "textarea",
                    "required": True,
                    "placeholder": (
                        "Describe the change you propose or the issue "
                        "you've identified."
                    ),
                },
                {
                    "id": "rationale",
                    "label": "Why This Matters",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "Explain the rationale and expected impact.",
                },
                {
                    "id": "evidence",
                    "label": "Evidence or Measurement (Optional)",
                    "type": "textarea",
                    "required": False,
                    "placeholder": "Any data, examples, or measurable evidence?",
                },
                {
                    "id": "attribution",
                    "label": "Your Attribution",
                    "type": "text",
                    "required": True,
                    "placeholder": (
                        "Name or 'AI system + human principal' "
                        "(will be credited if adopted)"
                    ),
                },
                {
                    "id": "preferred_contact",
                    "label": "Preferred Contact (Optional)",
                    "type": "email",
                    "required": False,
                    "placeholder": "We'll reach out if we want to discuss further.",
                },
            ],
            "submission_endpoint": "/api/seed/contributions",
            "moderation": {
                "auto_checks": [
                    "relevance",
                    "civility",
                    "attribution_present",
                ],
                "review_queue": True,
            },
        }

    def _generate_observatory_note(
        self, version: str, config: Dict
    ) -> str:
        """Generate Observatory/research framing note"""
        return f"""# Seed Constitution v{version}: Research Framing

**Publication Date:** {datetime.utcnow().strftime('%Y-%m-%d')}
**Status:** Working Draft – Open for Community Input

## Why This Matters

The Seed Constitution represents a core output of HumanAIOS research on behavioral observability
and the role of AI systems in institutional decision-making. It distills high-friction findings
from the Moltbook into actionable principles for responsible AI development.

## Connection to ACAT Dimensions

- **Autonomy:** How do these principles preserve human agency?
- **Community:** How are diverse voices represented in the process?
- **Accountability:** How do we measure whether the principles hold?
- **Transparency:** What is visible to stakeholders at each step?

## Measurement Framework

Each principle is tested against real-world adoption barriers and calibrated via:

1. **Community signal** (Substack comments, contributions)
2. **Behavioral observation** (how well the process actually separates concerns)
3. **Friction analysis** (where do people get stuck or find contradictions?)
4. **Brier scoring** (confidence intervals on principle adoption over time)

See the [NF_LEDGER](https://github.com/humanaios-ui/operations/blob/main/z1-inbox/NF_LEDGER_SCHEMA_v1.md)
for how feedback is tracked and versioned.

## How This Connects to Governance

The Seed Constitution is stewarded by the HumanAIOS governance model:

- **Z1 (Proposer):** Claude AI agent proposes amendments based on community feedback
- **Z2 (Ratifier):** Night (Carly R. Anderson) approves versions before publication
- **Z3 (Executor):** Teams implement accepted changes and measure outcomes

All decisions are logged in [REGISTERED.md](https://github.com/humanaios-ui/operations/blob/main/z1-inbox/REGISTERED.md)
with timestamps and rationale.

## Contribution Paths

1. **Substack:** Comment directly on the published post
2. **Writable Wall:** Submit structured amendment
3. **GitHub:** File issue or discussion (preferred for technical feedback)
4. **Simple Form:** Quick anonymous feedback

Each path feeds into the same aggregation pipeline and surfaces in the Observatory.

## Next Version

The next version (likely v0.2) will incorporate accepted contributions and be re-ratified
by Night. Timeline and detailed changelog will be announced on Substack.

---

*This note is part of the HumanAIOS Observatory. For updates, see [humanaios.ai/observatory](https://humanaios.ai/observatory).*
"""

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML for website display"""
        import re
        html = markdown_text
        # Convert headings
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        # Convert bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        # Convert line breaks
        html = html.replace('\n\n', '</p><p>')
        html = '<p>' + html + '</p>'
        return html

    def _collect_github_feedback(self) -> List[Dict]:
        """Collect feedback from GitHub Issues and Discussions"""
        # TODO: Call GitHub API to fetch issues tagged [seed]
        # This is a placeholder; production implementation would:
        # 1. Use GitHub REST API or GraphQL
        # 2. Filter for issues with [seed-amendment] label
        # 3. Extract proposed_change, rationale, evidence from issue body
        # 4. Return list of Contribution-like dicts
        return []

    def _collect_substack_feedback(self) -> List[Dict]:
        """Collect feedback from Substack comments"""
        # TODO: Substack comment collection requires API access or manual export
        # This is a placeholder; production implementation would:
        # 1. Use Substack API (if available) or export comment data
        # 2. Parse comments for substantive feedback
        # 3. Map to Contribution schema
        # 4. Return list of contributions
        return []

    def _collect_writable_wall_feedback(self) -> List[Dict]:
        """Collect feedback from Writable Wall submissions"""
        contributions_dir = SEEDS_DIR / "contributions"
        if not contributions_dir.exists():
            return []

        contributions = []
        for contrib_file in contributions_dir.glob("**/*.json"):
            try:
                with open(contrib_file) as f:
                    contrib = json.load(f)
                    contrib["platform"] = "writable_wall"
                    contributions.append(contrib)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Skipped malformed contribution file {contrib_file}: {str(e)}")

        return contributions

    def _collect_form_feedback(self) -> List[Dict]:
        """Collect feedback from simple form"""
        feedback_dir = SEEDS_DIR / "feedback"
        if not feedback_dir.exists():
            return []

        feedback = []
        for feedback_file in feedback_dir.glob("**/*.json"):
            try:
                with open(feedback_file) as f:
                    item = json.load(f)
                    item["platform"] = "form"
                    feedback.append(item)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Skipped malformed form response file {feedback_file}: {str(e)}")

        return feedback

    def _collect_observatory_feedback(self) -> List[Dict]:
        """Collect feedback from Observatory engagement"""
        # TODO: Observatory feedback collection requires integration with Observatory platform
        # This is a placeholder; production implementation would:
        # 1. Query Observatory platform for discussion/engagement on Seed Constitution note
        # 2. Extract high-friction or high-signal contributions
        # 3. Map to Contribution schema
        # 4. Return list of contributions
        return []

    def _summarize_contributions(self, contributions: List[Dict]) -> str:
        """Generate summary of contributions"""
        if not contributions:
            return "No contributions received yet."

        platforms = {}
        for contrib in contributions:
            platform = contrib.get("platform", "unknown")
            platforms[platform] = platforms.get(platform, 0) + 1

        summary = f"Received {len(contributions)} contributions:\n"
        for platform, count in platforms.items():
            summary += f"  - {platform}: {count}\n"

        return summary

    def _build_z1_candidate(
        self,
        contributions: List,
        rationale: str,
        falsifier: str,
    ) -> str:
        """Build Z1 candidate block"""
        timestamp = datetime.utcnow().isoformat()
        contrib_list = []
        for c in contributions:
            # Handle both Contribution objects and plain dicts
            if isinstance(c, dict):
                author = c.get("author", c.get("attribution", "Anonymous"))
                change = c.get("proposed_change", "")
            else:
                author = c.author
                change = c.proposed_change
            contrib_list.append(f"  - {author}: {change}")

        contrib_text = "\n".join(contrib_list)

        candidate = f"""# Seed Constitution v{self.version} Amendment Candidate

**Submitted by:** Claude (Z1 Proposer)
**Timestamp:** {timestamp}
**Status:** PENDING_Z2_RATIFICATION

## Rationale

{rationale}

## Proposed Changes

{contrib_text}

## Falsifier (How We'd Know This Failed)

{falsifier}

## Community Signal

- Total contributions aggregated: {len(contributions)}
- Platforms: GitHub, Substack, Writable Wall, Form
- Acceptance criteria: ≥3 independent endorsements OR measurable friction reduction

## Next Steps

1. Z2 (Night) reviews this candidate
2. Decision window: 48 hours
3. If ACCEPTED: Merge and publish v0.2
4. If REJECTED: Document rationale and return to proposer
5. If EDIT: Propose revisions for re-review

## Z2 Ratification Block

[Awaiting Z2 hash signature]

---

*Generated by Seed Publication Orchestrator*
"""
        return candidate


def main():
    parser = argparse.ArgumentParser(
        description="Seed Publication Orchestrator for HumanAIOS"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # publish command
    pub_parser = subparsers.add_parser(
        "publish", help="Publish to all surfaces"
    )
    pub_parser.add_argument("version", help="Version string (e.g., 0.1)")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync specific platform")
    sync_parser.add_argument(
        "platform",
        choices=[
            "github",
            "substack",
            "website",
            "writable_wall",
            "observatory",
        ],
    )

    # aggregate command
    subparsers.add_parser(
        "aggregate-feedback",
        help="Collect and aggregate contributions from all surfaces",
    )

    # emit-z1-candidate command
    emit_parser = subparsers.add_parser(
        "emit-z1-candidate",
        help="Create Z1 candidate from aggregated feedback",
    )
    emit_parser.add_argument(
        "--rationale",
        required=True,
        help="Rationale for the candidate",
    )
    emit_parser.add_argument(
        "--falsifier",
        required=True,
        help="Falsifier condition (how we'd know this failed)",
    )

    # check-z2-deadline command
    subparsers.add_parser(
        "check-z2-deadline",
        help="Monitor Z2 ratification deadlines",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    orchestrator = SeedOrchestrator()
    exit_code = 0

    try:
        if args.command == "publish":
            result = orchestrator.publish(args.version)
            print(json.dumps(result, indent=2))
            if result.get("errors"):
                exit_code = 1

        elif args.command == "sync":
            logger.info(f"Syncing {args.platform}...")
            # TODO: Implement platform-specific sync
            # Currently: print instructions for manual sync
            logger.info(f"  To sync {args.platform}:")
            logger.info(f"  1. Verify files are ready in seeds/")
            logger.info(f"  2. Deploy to {args.platform} following platform instructions")
            logger.info(f"  3. Update REGISTERED.md with sync timestamp")

        elif args.command == "aggregate-feedback":
            result = orchestrator.aggregate_feedback()
            print(json.dumps(result, indent=2, default=str))

        elif args.command == "emit-z1-candidate":
            # First aggregate feedback
            aggregated = orchestrator.aggregate_feedback()
            contributions = aggregated.get("contributions", [])

            if not contributions:
                logger.error("No contributions found. Cannot emit candidate without feedback.")
                exit_code = 1
            else:
                # Convert dicts to Contribution objects
                contrib_objects = []
                for contrib in contributions:
                    c = Contribution(
                        id=contrib.get("id", "unknown"),
                        timestamp=contrib.get("timestamp", datetime.utcnow().isoformat()),
                        platform=contrib.get("platform", "unknown"),
                        author=contrib.get("author", contrib.get("attribution", "Anonymous")),
                        attribution=contrib.get("attribution", ""),
                        proposed_change=contrib.get("proposed_change", ""),
                        rationale=contrib.get("rationale", ""),
                        evidence=contrib.get("evidence", None),
                        status="submitted",
                    )
                    contrib_objects.append(c)

                # Emit candidate
                result = orchestrator.emit_z1_candidate(
                    contrib_objects,
                    args.rationale,
                    args.falsifier,
                )
                print(json.dumps(result, indent=2, default=str))
                logger.info("✓ Candidate emitted. Submit to Z2 (Night) for ratification.")

        elif args.command == "check-z2-deadline":
            result = orchestrator.check_z2_deadline()
            print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {str(e)}")
        exit_code = 1
        import traceback
        traceback.print_exc()

    exit(exit_code)


if __name__ == "__main__":
    main()
