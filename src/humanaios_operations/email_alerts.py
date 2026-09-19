"""
Email Alerts — Send SMTP notifications for funding opportunities and deadlines.

Supports:
- SMTP (Gmail, custom servers)
- Sendmail (local)
- HTML templates for different alert types
- Graceful degradation when email not configured
"""

import json
import os
import smtplib
import subprocess
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


def _email_html_wrapper(title: str, content: str) -> str:
    """Wrap content in consistent HTML email template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; }}
            .opportunity {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 4px; }}
            .opportunity .name {{ font-weight: bold; font-size: 16px; }}
            .opportunity .meta {{ color: #666; font-size: 14px; margin-top: 5px; }}
            .score {{ display: inline-block; background: #667eea; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
            .urgent {{ border-left-color: #e74c3c; }}
            .urgent .score {{ background: #e74c3c; }}
            .cta {{ text-align: center; margin-top: 20px; }}
            .cta a {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{title}</h1>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>HumanAIOS Operations Hub • {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_email(subject: str, body_html: str, to_email: str | None = None, use_sendmail: bool = False) -> bool:
    """Send email via SMTP or Sendmail."""
    config = get_smtp_config()
    to_email = to_email or config["to_email"]

    if not to_email:
        print("⚠️  No recipient email configured (ALERT_EMAIL)")
        return False

    if use_sendmail or not config["host"]:
        return _send_via_sendmail(subject, body_html, to_email)
    else:
        return _send_via_smtp(subject, body_html, to_email, config)


def _send_via_smtp(subject: str, body_html: str, to_email: str, config: dict) -> bool:
    """Send email via SMTP (Gmail, custom servers)."""
    if not all([config["host"], config["user"], config["password"]]):
        print("⚠️  SMTP not configured. Required: SMTP_HOST, SMTP_USER, SMTP_PASS")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = to_email

        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)

        print(f"✓ Email sent via SMTP: {subject}")
        return True

    except smtplib.SMTPException as e:
        print(f"✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False


def _send_via_sendmail(subject: str, body_html: str, to_email: str) -> bool:
    """Send email via local sendmail binary."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"noreply@humanaios.local"
        msg["To"] = to_email

        msg.attach(MIMEText(body_html, "html"))

        proc = subprocess.Popen(["/usr/sbin/sendmail", "-t"], stdin=subprocess.PIPE)
        proc.communicate(msg.as_bytes())

        if proc.returncode == 0:
            print(f"✓ Email sent via sendmail: {subject}")
            return True
        else:
            print(f"✗ Sendmail failed (exit code {proc.returncode})")
            return False

    except FileNotFoundError:
        print("⚠️  Sendmail not found. Install postfix or configure SMTP.")
        return False
    except Exception as e:
        print(f"✗ Error sending via sendmail: {e}")
        return False


def digest_report(opportunities_file: str = "data/ranked_opportunities.json") -> bool:
    """Send weekly digest of top opportunities."""
    if not Path(opportunities_file).exists():
        print(f"⚠️  No opportunities file: {opportunities_file}")
        return False

    with open(opportunities_file) as f:
        data = json.load(f)

    opps = data if isinstance(data, list) else []
    top_opps = opps[:5]

    if not top_opps:
        print("ℹ️  No opportunities to send in digest")
        return True

    content = "<p>Your top 5 funding opportunities this week, ranked by research fit:</p>"

    for i, opp in enumerate(top_opps, 1):
        name = opp.get("name", "Unknown")
        fit_score = opp.get("fit_score", 0)
        deadline = opp.get("deadline", "Rolling")
        sponsor = opp.get("sponsor", "")
        award = opp.get("award_size", "N/A")
        fit_pct = int(fit_score * 100)

        content += f"""
        <div class="opportunity">
            <div class="name">#{i} {name}</div>
            <div class="meta">
                <strong>Fit Score:</strong> <span class="score">{fit_pct}%</span><br/>
                <strong>Sponsor:</strong> {sponsor}<br/>
                <strong>Award:</strong> {award}<br/>
                <strong>Deadline:</strong> {deadline}
            </div>
        </div>
        """

    html = _email_html_wrapper("📊 Weekly Funding Digest", content)
    return send_email(
        subject="📊 HumanAIOS Weekly Digest",
        body_html=html
    )


def deadline_alert(opportunities_file: str = "data/ranked_opportunities.json", days_ahead: int = 7) -> bool:
    """Send alert for deadlines coming up within N days."""
    if not Path(opportunities_file).exists():
        print(f"⚠️  No opportunities file: {opportunities_file}")
        return False

    with open(opportunities_file) as f:
        data = json.load(f)

    opps = data if isinstance(data, list) else []
    urgent = [o for o in opps if o.get("days_to_deadline", 999) <= days_ahead]

    if not urgent:
        print(f"ℹ️  No deadlines within {days_ahead} days")
        return True

    content = f"<p><strong>⚠️ {len(urgent)} opportunities with deadlines in the next {days_ahead} days:</strong></p>"

    for opp in sorted(urgent, key=lambda x: x.get("days_to_deadline", 999)):
        name = opp.get("name", "Unknown")
        deadline = opp.get("deadline", "Unknown")
        days = opp.get("days_to_deadline", "?")
        sponsor = opp.get("sponsor", "")

        content += f"""
        <div class="opportunity urgent">
            <div class="name">{name}</div>
            <div class="meta">
                <strong>Deadline:</strong> {deadline}<br/>
                <strong>Days Left:</strong> <span class="score">{days}d</span><br/>
                <strong>Sponsor:</strong> {sponsor}
            </div>
        </div>
        """

    html = _email_html_wrapper("⏰ Urgent Funding Deadlines", content)
    return send_email(
        subject=f"⏰ URGENT: {len(urgent)} funding deadlines within {days_ahead} days",
        body_html=html
    )


def test_smtp_connection() -> bool:
    """Test SMTP connection with configured credentials."""
    config = get_smtp_config()

    if not all([config["host"], config["user"], config["password"]]):
        print("❌ SMTP configuration incomplete")
        print(f"  SMTP_HOST: {'✓' if config['host'] else '✗ missing'}")
        print(f"  SMTP_USER: {'✓' if config['user'] else '✗ missing'}")
        print(f"  SMTP_PASS: {'✓' if config['password'] else '✗ missing'}")
        print(f"  ALERT_EMAIL: {'✓' if config['to_email'] else '✗ missing'}")
        return False

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            print(f"✅ SMTP connection successful: {config['host']}:{config['port']}")
            return True
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
