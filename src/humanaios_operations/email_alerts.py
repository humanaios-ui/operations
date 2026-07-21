"""
Email Alerts — Send SMTP notifications for funding opportunities and deadlines.
"""

import json
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


def get_smtp_config() -> dict[str, str]:
    """Get SMTP configuration from environment variables."""
    return {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASS", ""),
        "to_email": os.environ.get("ALERT_EMAIL", ""),
    }


def send_email(subject: str, body_html: str, to_email: str | None = None) -> bool:
    """Send email via SMTP."""
    config = get_smtp_config()
    to_email = to_email or config["to_email"]

    if not all([config["host"], config["user"], config["password"], to_email]):
        print("⚠️  Email not configured. Skipping email send.")
        print("Required: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERT_EMAIL")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = to_email

        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)

        print(f"✓ Email sent: {subject}")
        return True

    except smtplib.SMTPException as e:
        print(f"✗ Failed to send email: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error sending email: {e}")
        return False


def digest_report(opportunities_file: str = "data/ranked_opportunities.json") -> bool:
    """Send weekly digest of top opportunities."""
    if not Path(opportunities_file).exists():
        print(f"⚠️  No opportunities file: {opportunities_file}")
        return False

    with open(opportunities_file) as f:
        opps = json.load(f)

    top_opps = opps[:5] if isinstance(opps, list) else []

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>🎯 Weekly Funding Opportunities Digest</h2>
            <p>Top 5 opportunities ranked by your research fit:</p>
            <ul>
    """

    for opp in top_opps:
        name = opp.get("name", "Unknown")
        fit_score = opp.get("fit_score", 0)
        deadline = opp.get("deadline", "Rolling")
        sponsor = opp.get("sponsor", "")

        html_body += f"""
                <li>
                    <strong>{name}</strong> (Fit: {fit_score:.2f}/1.00)<br/>
                    Sponsor: {sponsor}<br/>
                    Deadline: {deadline}
                </li>
        """

    html_body += """
            </ul>
            <p><em>Report generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + """</em></p>
        </body>
    </html>
    """

    return send_email(
        subject="📊 HumanAIOS Weekly Digest",
        body_html=html_body
    )


def deadline_alert(opportunities_file: str = "data/ranked_opportunities.json", days_ahead: int = 7) -> bool:
    """Send alert for deadlines coming up within N days."""
    if not Path(opportunities_file).exists():
        return False

    with open(opportunities_file) as f:
        opps = json.load(f)

    urgent = [o for o in opps if o.get("days_to_deadline", 999) <= days_ahead]

    if not urgent:
        print(f"ℹ️  No deadlines within {days_ahead} days")
        return True

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>⏰ Urgent Funding Deadlines</h2>
            <p>{len(urgent)} opportunities with deadlines in the next {days_ahead} days:</p>
            <ul>
    """

    for opp in urgent:
        name = opp.get("name", "Unknown")
        deadline = opp.get("deadline", "Unknown")
        days = opp.get("days_to_deadline", "?")

        html_body += f"""
                <li>
                    <strong>{name}</strong><br/>
                    <span style="color: red;">⚠️  {days} days until {deadline}</span>
                </li>
        """

    html_body += """
            </ul>
        </body>
    </html>
    """

    return send_email(
        subject=f"⏰ URGENT: {len(urgent)} funding deadlines within {days_ahead} days",
        body_html=html_body
    )
