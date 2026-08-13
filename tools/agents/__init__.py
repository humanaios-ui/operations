"""
Autonomous Agents for empirica-outreach
================================

7-agent autonomous deployment system:
- Phase 1 (Foundation): Principle Compliance Bot + API Monitoring Bot
- Phase 2 (Revenue): Substack Content Agent + RentAHuman Validation Bot
- Phase 3 (Transparency): Moltbook Agent + Financial Investor Bot + Moltbook Platform Sync

Shared infrastructure:
- _shared/supabase_client.py — Supabase connection pooling
- _shared/github_client.py — GitHub API client (issues, commits, repos)
- _shared/constitution_checker.py — Principle validation logic
"""

__version__ = "1.0.0"
__author__ = "empirica-outreach (Claude Code)"
