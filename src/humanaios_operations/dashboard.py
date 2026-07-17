"""Dashboard HTML Generator

Generates a responsive, dark-mode aware HTML dashboard.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class DashboardGenerator:
    """Generate HTML dashboard from data files"""

    def __init__(self, data_dir: str = "data", output_dir: str = "reports"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def load_profile(self) -> Dict:
        """Load research profile"""
        profile_file = self.data_dir / "research_profile.json"
        if not profile_file.exists():
            return {}
        with open(profile_file) as f:
            return json.load(f)

    def load_opportunities(self) -> List[Dict]:
        """Load ranked opportunities"""
        opps_file = self.data_dir / "ranked_opportunities.json"
        if not opps_file.exists():
            return []
        with open(opps_file) as f:
            return json.load(f)

    def load_applications(self) -> Dict:
        """Load application pipeline status"""
        # This would typically read from SQLite, but for now return mock data
        return {
            "total": 1,
            "draft": 1,
            "submitted": 0,
            "pending": 0,
            "funded": 0,
            "rejected": 0,
            "applications": []
        }

    def generate_html(self) -> str:
        """Generate complete HTML dashboard"""
        profile = self.load_profile()
        opportunities = self.load_opportunities()
        applications = self.load_applications()

        # Extract key data
        name = profile.get("profile", {}).get("name", "HumanAIOS")
        pub_count = profile.get("publication_count", 0)
        research_areas = profile.get("research_areas", {})
        expertise = profile.get("expertise_scores", {})

        top_opps = opportunities[:5]
        total_apps = applications["total"]
        funded_count = applications["funded"]

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HumanAIOS Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --accent-color: #0066cc;
            --success-color: #28a745;
            --warning-color: #ffc107;
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-primary: #1a1a1a;
                --bg-secondary: #2a2a2a;
                --text-primary: #ffffff;
                --text-secondary: #cccccc;
                --border-color: #444444;
                --accent-color: #4da6ff;
            }}
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            transition: background-color 0.3s, color 0.3s;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 40px;
        }}

        h1 {{
            font-size: 32px;
            margin-bottom: 5px;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .card h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            color: var(--accent-color);
        }}

        .stat {{
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .stat-label {{
            color: var(--text-secondary);
        }}

        .stat-value {{
            font-weight: bold;
            font-size: 18px;
        }}

        .tag {{
            display: inline-block;
            background-color: var(--accent-color);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }}

        .opportunities-list {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 40px;
        }}

        .opportunity {{
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .opportunity:last-child {{
            border-bottom: none;
        }}

        .opportunity-name {{
            flex: 1;
            font-weight: 500;
        }}

        .opportunity-score {{
            background-color: var(--accent-color);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin-left: 15px;
        }}

        .footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 12px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }}

        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}

            h1 {{
                font-size: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 HumanAIOS Operations Dashboard</h1>
            <div class="subtitle">Integrated funding discovery, research profiling, and proposal tracking</div>
        </header>

        <div class="grid">
            <!-- Research Profile Card -->
            <div class="card">
                <h2>📊 Research Profile</h2>
                <div class="stat">
                    <span class="stat-label">Researcher</span>
                    <span class="stat-value">{name}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Publications</span>
                    <span class="stat-value">{pub_count}</span>
                </div>
                <div style="margin-top: 15px;">
                    <div class="stat-label">Research Areas:</div>
                    <div style="margin-top: 8px;">
"""

        # Add research areas
        for area in list(research_areas.keys())[:3]:
            html += f'                        <span class="tag">{area.replace("_", " ").title()}</span>\n'

        html += f"""
                    </div>
                </div>
            </div>

            <!-- Application Pipeline Card -->
            <div class="card">
                <h2>📋 Application Pipeline</h2>
                <div class="stat">
                    <span class="stat-label">Total</span>
                    <span class="stat-value">{total_apps}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">In Progress</span>
                    <span class="stat-value">{applications['draft'] + applications['submitted']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Funded</span>
                    <span class="stat-value" style="color: var(--success-color);">{funded_count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Success Rate</span>
                    <span class="stat-value">
                        {f'{(funded_count/max(1, total_apps - (applications["draft"] + applications["submitted"])))*100:.0f}%' if (total_apps - (applications['draft'] + applications['submitted'])) > 0 else 'N/A'}
                    </span>
                </div>
            </div>

            <!-- Quick Stats Card -->
            <div class="card">
                <h2>📈 Quick Stats</h2>
                <div class="stat">
                    <span class="stat-label">Top Expertise</span>
                    <span class="stat-value">
                        {max(expertise.values()) if expertise else 0:.2f}
                    </span>
                </div>
                <div class="stat">
                    <span class="stat-label">Expertise Domains</span>
                    <span class="stat-value">{len(expertise)}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Avg Opportunity Fit</span>
                    <span class="stat-value">
                        {sum(o.get('fit_score', 0) for o in top_opps) / max(1, len(top_opps)):.2f}
                    </span>
                </div>
            </div>
        </div>

        <!-- Top Opportunities -->
        <div class="opportunities-list">
            <h2>🎯 Top Opportunities for You</h2>
"""

        for i, opp in enumerate(top_opps, 1):
            name_short = opp.get("name", "Unknown")[:60]
            score = opp.get("fit_score", 0.0)
            html += f"""
            <div class="opportunity">
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">{i}. {name_short}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">{opp.get("category", "unknown").replace("_", " ").title()}</div>
                </div>
                <div class="opportunity-score">{score:.2f}</div>
            </div>
"""

        html += """
        </div>

        <footer class="footer">
            <p>🤖 HumanAIOS Operations Hub • Auto-generated on {}</p>
            <p><a href="./ranked_opportunities.md" style="color: var(--accent-color);">View full opportunities report →</a></p>
        </footer>
    </div>
</body>
</html>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M UTC"))

        return html

    def write_dashboard(self) -> Path:
        """Generate and save dashboard HTML"""
        html = self.generate_html()
        output_file = self.output_dir / "dashboard.html"
        with open(output_file, "w") as f:
            f.write(html)
        return output_file


def main():
    """CLI: Generate dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate HumanAIOS dashboard")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--output-dir", default="reports", help="Output directory")

    args = parser.parse_args()

    generator = DashboardGenerator(args.data_dir, args.output_dir)
    output_file = generator.write_dashboard()
    print(f"✓ Dashboard generated: {output_file}")

    return 0


if __name__ == "__main__":
    exit(main())
