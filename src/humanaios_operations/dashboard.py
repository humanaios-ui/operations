"""
Dashboard Generator — Create visual HTML dashboard of opportunities and progress.
"""

import json
from datetime import datetime
from pathlib import Path


def load_data(opportunities_file: str = "data/ranked_opportunities.json", profile_file: str = "data/research_profile.json") -> tuple:
    """Load opportunities and profile data."""
    opportunities = []
    profile = {}

    if Path(opportunities_file).exists():
        with open(opportunities_file) as f:
            opportunities = json.load(f)

    if Path(profile_file).exists():
        with open(profile_file) as f:
            profile = json.load(f)

    return opportunities, profile


def generate_dashboard_html(opportunities: list, profile: dict) -> str:
    """Generate HTML dashboard."""
    research_areas = profile.get("research_areas", [])
    publications = profile.get("publications", [])

    opp_rows = ""
    for opp in opportunities[:10]:  # Top 10
        fit = opp.get("fit_score", 0)
        name = opp.get("name", "")
        sponsor = opp.get("sponsor", "")
        deadline = opp.get("deadline", "Rolling")
        fit_pct = int(fit * 100)

        color = "red" if fit_pct >= 80 else "orange" if fit_pct >= 60 else "gray"
        opp_rows += f"""
        <tr>
            <td><strong>{name}</strong></td>
            <td>{sponsor}</td>
            <td>{deadline}</td>
            <td><span style="color: {color}; font-weight: bold;">{fit_pct}%</span></td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HumanAIOS Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
            .subtitle {{ color: #94a3b8; margin-bottom: 30px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .card {{
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 20px;
            }}
            .card h3 {{ font-size: 14px; color: #94a3b8; margin-bottom: 10px; text-transform: uppercase; }}
            .card .value {{ font-size: 32px; font-weight: bold; }}
            .card .unit {{ color: #64748b; font-size: 14px; margin-top: 5px; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                overflow: hidden;
            }}
            thead tr {{ background: #0f172a; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ font-weight: 600; color: #94a3b8; }}
            tr:last-child td {{ border-bottom: none; }}
            .footer {{ margin-top: 40px; text-align: center; color: #64748b; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 HumanAIOS Operations Dashboard</h1>
            <p class="subtitle">Research profile • Funding opportunities • Application tracking</p>

            <div class="grid">
                <div class="card">
                    <h3>Research Areas</h3>
                    <div class="value">{len(research_areas)}</div>
                    <div class="unit">active domains</div>
                </div>
                <div class="card">
                    <h3>Publications</h3>
                    <div class="value">{len(publications)}</div>
                    <div class="unit">from ORCID</div>
                </div>
                <div class="card">
                    <h3>Opportunities</h3>
                    <div class="value">{len(opportunities)}</div>
                    <div class="unit">tracked & ranked</div>
                </div>
                <div class="card">
                    <h3>Last Sync</h3>
                    <div class="value" style="font-size: 14px;">{datetime.now().strftime('%Y-%m-%d')}</div>
                    <div class="unit">{datetime.now().strftime('%H:%M UTC')}</div>
                </div>
            </div>

            <h2 style="margin-bottom: 20px;">Top 10 Opportunities (by Research Fit)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Opportunity</th>
                        <th>Sponsor</th>
                        <th>Deadline</th>
                        <th>Fit Score</th>
                    </tr>
                </thead>
                <tbody>
                    {opp_rows}
                </tbody>
            </table>

            <div class="footer">
                Generated by HumanAIOS Operations Hub • {datetime.now().isoformat()}
            </div>
        </div>
    </body>
    </html>
    """

    return html


def generate_dashboard(opportunities_file: str = "data/ranked_opportunities.json", profile_file: str = "data/research_profile.json", output_file: str = "reports/dashboard.html") -> bool:
    """Generate and save dashboard HTML."""
    opportunities, profile = load_data(opportunities_file, profile_file)

    html = generate_dashboard_html(opportunities, profile)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(html)

    print(f"✓ Dashboard saved to {output_file}")
    return True
