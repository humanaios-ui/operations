"""ApplicationTracker Service

Track funding applications from draft through decision.
"""

import sqlite3
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional


class ApplicationTracker:
    """SQLite-based tracking of grant applications"""

    def __init__(self, db_path: str = "data/applications.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT,
                created_at DATETIME,
                submitted_at DATETIME,
                decision_at DATETIME,
                decision TEXT,
                amount_requested REAL,
                amount_awarded REAL,
                proposal_file TEXT,
                budget_file TEXT,
                notes TEXT
            )
        """)

        # Decisions/outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                decision TEXT,
                amount REAL,
                feedback TEXT,
                learned_lessons TEXT,
                decision_date DATETIME,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_application(
        self,
        opportunity_id: str,
        title: str,
        amount_requested: Optional[float] = None,
        proposal_file: Optional[str] = None,
        status: str = "draft"
    ) -> str:
        """
        Create a new application.

        Returns: application_id
        """
        app_id = f"app_{datetime.now().strftime('%Y%m%d')}_{str(uuid4())[:8]}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO applications
            (id, opportunity_id, title, status, created_at, amount_requested, proposal_file)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (app_id, opportunity_id, title, status, datetime.now(), amount_requested, proposal_file))

        conn.commit()
        conn.close()

        return app_id

    def get_application(self, app_id: str) -> Optional[Dict]:
        """Retrieve an application by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        cols = ["id", "opportunity_id", "title", "status", "created_at", "submitted_at",
                "decision_at", "decision", "amount_requested", "amount_awarded", "proposal_file", "budget_file", "notes"]
        return dict(zip(cols, row))

    def update_status(self, app_id: str, status: str) -> bool:
        """Update application status"""
        valid_statuses = ["draft", "submitted", "pending", "funded", "rejected"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        conn.commit()
        conn.close()

        return cursor.rowcount > 0

    def submit_application(self, app_id: str) -> bool:
        """Mark application as submitted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE applications SET status = ?, submitted_at = ? WHERE id = ?",
            ("submitted", datetime.now(), app_id)
        )
        conn.commit()
        conn.close()

        return cursor.rowcount > 0

    def record_decision(self, app_id: str, decision: str, amount: Optional[float] = None, feedback: str = "") -> bool:
        """
        Record a decision (funded/rejected) on an application.

        Args:
            app_id: Application ID
            decision: "funded" or "rejected"
            amount: Amount awarded (if funded)
            feedback: Feedback from funder
        """
        if decision not in ["funded", "rejected"]:
            raise ValueError("Decision must be 'funded' or 'rejected'")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE applications
            SET status = ?, decision = ?, decision_at = ?, amount_awarded = ?
            WHERE id = ?
        """, ("decided", decision, datetime.now(), amount, app_id))

        # Also record in decisions table for history
        decision_id = f"dec_{uuid4()}"
        cursor.execute("""
            INSERT INTO decisions
            (id, application_id, decision, amount, feedback, decision_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (decision_id, app_id, decision, amount, feedback, datetime.now()))

        conn.commit()
        conn.close()

        return cursor.rowcount > 0

    def list_applications(self, status: Optional[str] = None) -> List[Dict]:
        """List applications, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")

        rows = cursor.fetchall()
        conn.close()

        cols = ["id", "opportunity_id", "title", "status", "created_at", "submitted_at",
                "decision_at", "decision", "amount_requested", "amount_awarded", "proposal_file", "budget_file", "notes"]

        return [dict(zip(cols, row)) for row in rows]

    def get_pipeline_status(self) -> Dict:
        """Get overview of application pipeline"""
        all_apps = self.list_applications()

        status_counts = {
            "draft": len([a for a in all_apps if a["status"] == "draft"]),
            "submitted": len([a for a in all_apps if a["status"] == "submitted"]),
            "pending": len([a for a in all_apps if a["status"] == "pending"]),
            "funded": len([a for a in all_apps if a["status"] == "funded"]),
            "rejected": len([a for a in all_apps if a["status"] == "rejected"]),
        }

        funded = [a for a in all_apps if a["decision"] == "funded"]
        total_awarded = sum(a["amount_awarded"] or 0 for a in funded)

        return {
            "total_applications": len(all_apps),
            "status_counts": status_counts,
            "funded_count": len(funded),
            "total_awarded": total_awarded,
            "success_rate": len(funded) / max(1, len([a for a in all_apps if a["status"] == "decided"])),
            "applications": all_apps
        }

    def export_json(self, output_file: str = "data/applications_export.json"):
        """Export all applications to JSON"""
        pipeline = self.get_pipeline_status()
        with open(output_file, "w") as f:
            json.dump(pipeline, f, indent=2, default=str)
        return output_file


def main():
    """CLI: manage applications"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage funding applications")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create command
    create = subparsers.add_parser("create", help="Create new application")
    create.add_argument("--opportunity-id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--amount", type=float, help="Amount requested")
    create.add_argument("--proposal-file", help="Path to proposal file")

    # list command
    list_cmd = subparsers.add_parser("list", help="List applications")
    list_cmd.add_argument("--status", help="Filter by status")

    # submit command
    submit = subparsers.add_parser("submit", help="Mark as submitted")
    submit.add_argument("app_id")

    # decide command
    decide = subparsers.add_parser("decide", help="Record decision")
    decide.add_argument("app_id")
    decide.add_argument("--decision", required=True, choices=["funded", "rejected"])
    decide.add_argument("--amount", type=float, help="Amount awarded")
    decide.add_argument("--feedback", default="")

    # status command
    subparsers.add_parser("status", help="Show pipeline status")

    args = parser.parse_args()

    tracker = ApplicationTracker()

    if args.command == "create":
        app_id = tracker.create_application(
            args.opportunity_id,
            args.title,
            args.amount,
            args.proposal_file
        )
        print(f"✓ Created application: {app_id}")

    elif args.command == "list":
        apps = tracker.list_applications(args.status)
        print(f"Applications ({len(apps)}):")
        for app in apps:
            print(f"  {app['id']}: {app['title']} ({app['status']})")

    elif args.command == "submit":
        if tracker.submit_application(args.app_id):
            print(f"✓ Marked as submitted: {args.app_id}")
        else:
            print(f"✗ Application not found: {args.app_id}")

    elif args.command == "decide":
        if tracker.record_decision(args.app_id, args.decision, args.amount, args.feedback):
            print(f"✓ Recorded decision: {args.app_id} ({args.decision})")
        else:
            print(f"✗ Application not found: {args.app_id}")

    elif args.command == "status":
        status = tracker.get_pipeline_status()
        print("Application Pipeline Status:")
        print(f"  Total: {status['total_applications']}")
        for s, count in status['status_counts'].items():
            print(f"  {s}: {count}")
        print(f"  Funded: {status['funded_count']} (${status['total_awarded']:.0f})")
        if status['total_applications'] > 0:
            print(f"  Success rate: {status['success_rate']:.1%}")

    return 0


if __name__ == "__main__":
    exit(main())
