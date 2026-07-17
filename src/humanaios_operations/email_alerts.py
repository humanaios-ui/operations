"""Email Alerts Module

Sends notifications for new opportunities, deadline alerts, and funding decisions.
"""

import json
import smtplib
import os
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional


class EmailAlerts:
    """Send email notifications via SMTP"""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        """
        Initialize email client.

        Environment variables used if parameters not provided:
        - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_pass = smtp_pass or os.getenv("SMTP_PASS")
        self.from_email = from_email or os.getenv("FROM_EMAIL", self.smtp_user)

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass)

    def send(self, to_email: str, subject: str, body_html: str) -> bool:
        """Send HTML email"""
        if not self.is_configured():
            print(f"⚠️  Email not configured. Would send to {to_email}:")
            print(f"   Subject: {subject}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)

            print(f"✓ Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            return False

    def send_opportunity_digest(self, to_email: str, opportunities: List[Dict]) -> bool:
        """Send digest of top opportunities"""
        subject = f"🎯 Your Top Funding Opportunities ({datetime.now().strftime('%Y-%m-%d')})"

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px;">
                <h2>Your Top Funding Opportunities</h2>
                <p>Based on your research profile, here are the best-fitting opportunities for you:</p>

                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f0f0f0;">
                        <th style="padding: 10px; text-align: left;">Opportunity</th>
                        <th style="padding: 10px;">Score</th>
                        <th style="padding: 10px;">Deadline</th>
                    </tr>
        """

        for opp in opportunities[:10]:
            score = opp.get("fit_score", 0.0)
            deadline = opp.get("deadline", "Rolling")
            name = opp.get("name", "Unknown")
            url = opp.get("url", "#")

            html += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px;"><a href="{url}">{name}</a></td>
                        <td style="padding: 10px; text-align: center;">{score:.2f}</td>
                        <td style="padding: 10px;">{deadline}</td>
                    </tr>
            """

        html += """
                </table>

                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    View the full dashboard: <a href="https://github.com/humanaios-ui/operations/tree/main/reports">reports/dashboard.html</a>
                </p>

                <p style="font-size: 12px; color: #999;">
                    This is an automated email from HumanAIOS Operations Hub.
                </p>
            </body>
        </html>
        """

        return self.send(to_email, subject, html)

    def send_deadline_alert(
        self,
        to_email: str,
        opportunity: Dict,
        days_until: int,
    ) -> bool:
        """Send urgent deadline alert"""
        name = opportunity.get("name", "Unknown opportunity")
        deadline = opportunity.get("deadline", "N/A")
        url = opportunity.get("url", "#")

        subject = f"⏰ Urgent: {name} deadline in {days_until} days"

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px;">
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h2 style="color: #856404; margin: 0;">⏰ Deadline Alert</h2>
                </div>

                <h3>{name}</h3>
                <p><strong>Deadline:</strong> {deadline}</p>
                <p><strong>Time remaining:</strong> {days_until} days</p>

                <p>
                    <a href="{url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Opportunity
                    </a>
                </p>

                <p style="font-size: 12px; color: #999;">
                    This is an automated alert from HumanAIOS Operations Hub.
                </p>
            </body>
        </html>
        """

        return self.send(to_email, subject, html)

    def send_funding_decision(
        self,
        to_email: str,
        application: Dict,
        decision: str,
        amount: Optional[float] = None,
    ) -> bool:
        """Send funding decision notification"""
        title = application.get("title", "Unknown proposal")
        icon = "🎉" if decision == "funded" else "📋"

        subject = f"{icon} Funding Decision: {title[:50]}..."

        status_html = (
            f"<h3 style='color: #28a745;'>✓ Funded: ${amount:,.0f}</h3>"
            if decision == "funded"
            else "<h3 style='color: #dc3545;'>✗ Not funded</h3>"
        )

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px;">
                <h2>{title}</h2>
                {status_html}

                <p><strong>Decision date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>

                <p style="margin-top: 20px; font-size: 14px;">
                    Next steps: Review the decision and update your application tracker.
                </p>

                <p style="font-size: 12px; color: #999;">
                    This is an automated notification from HumanAIOS Operations Hub.
                </p>
            </body>
        </html>
        """

        return self.send(to_email, subject, html)


def send_opportunity_digest(data_dir: str = "data", email_addr: Optional[str] = None):
    """CLI: Send opportunity digest email"""
    alerter = EmailAlerts()
    to_email = email_addr or os.getenv("ALERT_EMAIL")

    if not to_email:
        print("✗ ALERT_EMAIL not configured")
        return 1

    # Load ranked opportunities
    opps_file = Path(data_dir) / "ranked_opportunities.json"
    if not opps_file.exists():
        print(f"✗ Ranked opportunities not found: {opps_file}")
        return 1

    with open(opps_file) as f:
        opportunities = json.load(f)

    if not alerter.send_opportunity_digest(to_email, opportunities):
        return 1

    return 0


def check_deadlines(data_dir: str = "data", days_threshold: int = 7, dry_run: bool = False):
    """CLI: Check for upcoming deadlines and send alerts"""
    alerter = EmailAlerts()
    to_email = os.getenv("ALERT_EMAIL")

    if not to_email:
        print("✗ ALERT_EMAIL not configured")
        return 1

    # Load ranked opportunities
    opps_file = Path(data_dir) / "ranked_opportunities.json"
    if not opps_file.exists():
        print(f"✗ Ranked opportunities not found: {opps_file}")
        return 1

    with open(opps_file) as f:
        opportunities = json.load(f)

    # Check for upcoming deadlines
    today = datetime.now().date()
    urgent = []

    for opp in opportunities:
        deadline_str = opp.get("deadline")
        if not deadline_str:
            continue

        try:
            deadline = datetime.fromisoformat(deadline_str).date()
            days_until = (deadline - today).days

            if 0 < days_until <= days_threshold:
                urgent.append((opp, days_until))
        except ValueError:
            continue

    if not urgent:
        print(f"✓ No deadlines in next {days_threshold} days")
        return 0

    print(f"⏰ Found {len(urgent)} upcoming deadline(s):")
    for opp, days in urgent:
        print(f"  - {opp['name']}: {days} days")

        if not dry_run:
            alerter.send_deadline_alert(to_email, opp, days)

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send email alerts")
    subparsers = parser.add_subparsers(dest="command")

    digest = subparsers.add_parser("digest", help="Send opportunity digest")
    digest.add_argument("--email", help="Recipient email (or ALERT_EMAIL env var)")

    deadlines = subparsers.add_parser("deadlines", help="Check for deadline alerts")
    deadlines.add_argument("--days", type=int, default=7, help="Days threshold")
    deadlines.add_argument("--dry-run", action="store_true", help="Don't send emails")

    args = parser.parse_args()

    if args.command == "digest":
        exit(send_opportunity_digest(email_addr=args.email))
    elif args.command == "deadlines":
        exit(check_deadlines(days_threshold=args.days, dry_run=args.dry_run))
    else:
        parser.print_help()
