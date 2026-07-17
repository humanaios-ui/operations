"""FundingFitScorer Service

Scores funding opportunities by fit to your research profile.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class FundingFitScorer:
    """Score how well a funding opportunity fits your expertise + constraints"""

    # Map research areas to opportunity keywords
    RESEARCH_AREA_KEYWORDS = {
        "ai_calibration": ["calibration", "uncertainty", "confidence", "epistemic"],
        "digital_minds": ["sentience", "consciousness", "welfare", "moral status", "digital minds"],
        "self_assessment": ["self-assessment", "self-description", "introspection", "metacognition"],
        "ai_safety": ["safety", "alignment", "x-risk", "governance", "control"],
        "behavioral_observability": ["observability", "behavior", "measurement", "tracking"],
        "nlp": ["NLP", "language", "transformer", "text", "LLM"],
        "machine_learning": ["machine learning", "neural", "deep learning", "optimization"],
        "evaluation": ["evaluation", "benchmark", "assessment", "metrics"],
        "open_science": ["open source", "reproducible", "public", "transparency"],
    }

    def __init__(self, research_profile: Dict):
        """
        Initialize scorer with a research profile.

        Args:
            research_profile: Dict with 'expertise_scores' and 'research_areas' keys
        """
        self.expertise_scores = research_profile.get("expertise_scores", {})
        self.research_areas = set(research_profile.get("research_areas", {}).keys())

    def score_expertise_fit(self, opportunity: Dict) -> float:
        """
        Score how well this opportunity matches your expertise (0.0-1.0).

        Extracts keywords from opportunity name/notes and compares to your research areas.
        """
        opp_text = (
            opportunity.get("name", "") + " " +
            opportunity.get("notes", "") + " " +
            opportunity.get("category", "")
        ).lower()

        # Count keyword matches for each domain
        domain_matches = {}
        for domain, keywords in self.RESEARCH_AREA_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw.lower() in opp_text)
            if matches > 0:
                domain_matches[domain] = matches

        if not domain_matches:
            return 0.3  # baseline score if no keywords match

        # Score based on overlap with your research areas
        your_areas = self.research_areas
        matched_yours = sum(1 for d in domain_matches.keys() if d in your_areas)
        total_matched = len(domain_matches)

        # Weight by your expertise in matched areas
        expertise_boost = sum(
            self.expertise_scores.get(d, 0.5)
            for d in domain_matches.keys()
            if d in your_areas
        ) / max(1, matched_yours)

        overlap_ratio = matched_yours / total_matched if total_matched > 0 else 0.0
        return min(1.0, (overlap_ratio * 0.6 + expertise_boost * 0.4))

    def score_eligibility_fit(self, opportunity: Dict, is_native_eligible: bool = True) -> float:
        """
        Score eligibility (0.0 or 1.0).

        Binary: either you can apply or you can't.
        """
        # Check if opportunity requires native eligibility
        if opportunity.get("native_eligible") and not is_native_eligible:
            return 0.0

        # Check for entity-type requirements (org vs individual)
        category = opportunity.get("category", "")
        if category == "grants" and not is_native_eligible:
            # Grants often require org; other types more flexible
            return 0.5

        return 1.0

    def score_timeline_fit(self, opportunity: Dict, hours_available_per_week: float = 10.0) -> float:
        """
        Score timeline feasibility (0.0-1.0).

        Estimates proposal effort vs. time to deadline.
        """
        deadline = opportunity.get("deadline")
        if not deadline:
            # Rolling deadline = ample time
            return 1.0

        # Parse deadline (ISO format or estimate)
        try:
            from datetime import datetime
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline.split("T")[0])
            else:
                deadline_date = deadline
            days_to_deadline = (deadline_date - datetime.now()).days
        except:
            return 0.8  # default if parsing fails

        # Estimate proposal effort by category
        effort_estimate = {
            "grants": 12,  # 12 hours to write a solid grant proposal
            "fellowship": 8,  # 8 hours for fellowship
            "career_transition": 6,  # 6 hours for career transition
            "compute_credit": 1,  # 1 hour for compute credits
            "contest": 4,  # 4 hours for contest entry
            "research-grant": 10,  # 10 hours for research grant
            "default": 8
        }

        category = opportunity.get("category", "default")
        hours_needed = effort_estimate.get(category, 8)

        # Assume 10 hours/week available (can override)
        hours_available = days_to_deadline * (hours_available_per_week / 7)

        if hours_available < hours_needed:
            # Very tight timeline
            feasibility = hours_available / hours_needed
            return feasibility * 0.7  # penalize tight deadlines
        else:
            # Ample time
            return min(1.0, 1.0 - (max(0, (hours_available - hours_needed) / 100) * 0.2))

    def score_opportunity(self, opportunity: Dict, is_native_eligible: bool = True) -> Dict:
        """
        Score a funding opportunity across all dimensions.

        Returns:
            {
                "fit_score": 0.0-1.0,
                "expertise_fit": 0.0-1.0,
                "eligibility_fit": 0.0-1.0,
                "timeline_fit": 0.0-1.0,
                "recommendation": "high" | "medium" | "low"
            }
        """
        expertise = self.score_expertise_fit(opportunity)
        eligibility = self.score_eligibility_fit(opportunity, is_native_eligible)
        timeline = self.score_timeline_fit(opportunity)

        # Composite score: 50% expertise, 30% eligibility, 20% timeline
        fit_score = (expertise * 0.5 + eligibility * 0.3 + timeline * 0.2)

        # Determine recommendation
        if fit_score >= 0.80:
            recommendation = "high"
        elif fit_score >= 0.60:
            recommendation = "medium"
        else:
            recommendation = "low"

        return {
            "fit_score": round(fit_score, 2),
            "expertise_fit": round(expertise, 2),
            "eligibility_fit": round(eligibility, 2),
            "timeline_fit": round(timeline, 2),
            "recommendation": recommendation
        }


def score_all_opportunities(research_profile: Dict, opportunities: List[Dict]) -> List[Dict]:
    """
    Score all opportunities and return sorted by fit.

    Args:
        research_profile: Your research profile (from ResearchProfile service)
        opportunities: List of funding opportunities (from funding-pipeline)

    Returns:
        List of opportunities with added 'fit_score', 'fit_breakdown' fields, sorted desc
    """
    scorer = FundingFitScorer(research_profile)

    scored = []
    for opp in opportunities:
        scores = scorer.score_opportunity(opp)
        opp_with_scores = opp.copy()
        opp_with_scores["fit_score"] = scores["fit_score"]
        opp_with_scores["fit_breakdown"] = {
            "expertise_match": scores["expertise_fit"],
            "eligibility_match": scores["eligibility_fit"],
            "timeline_fit": scores["timeline_fit"]
        }
        opp_with_scores["recommendation"] = scores["recommendation"]
        scored.append(opp_with_scores)

    # Sort by fit_score descending
    return sorted(scored, key=lambda x: x["fit_score"], reverse=True)


def generate_ranked_report(scored_opps: List[Dict], top_n: int = 10) -> str:
    """
    Generate a markdown report of top opportunities.

    Args:
        scored_opps: Opportunities with fit scores
        top_n: Show top N opportunities

    Returns:
        Markdown formatted report
    """
    md = "# Funding Opportunities Ranked by Your Fit\n\n"
    md += "| Opportunity | Score | Expertise | Eligibility | Timeline | Recommendation |\n"
    md += "|---|---|---|---|---|---|\n"

    for opp in scored_opps[:top_n]:
        name = opp.get("name", "Unknown")
        fit = opp.get("fit_score", 0.0)
        expertise = opp.get("fit_breakdown", {}).get("expertise_match", 0.0)
        eligibility = opp.get("fit_breakdown", {}).get("eligibility_match", 0.0)
        timeline = opp.get("fit_breakdown", {}).get("timeline_fit", 0.0)
        rec = opp.get("recommendation", "unknown").upper()

        md += f"| {name} | {fit:.2f} | {expertise:.2f} | {eligibility:.2f} | {timeline:.2f} | {rec} |\n"

    return md


def main():
    """CLI: score opportunities and generate report"""
    import argparse

    parser = argparse.ArgumentParser(description="Score funding opportunities by research fit")
    parser.add_argument("--profile", default="data/research_profile.json", help="Research profile file")
    parser.add_argument("--opportunities", default="data/sources.json", help="Opportunities file")
    parser.add_argument("--output", default="data/ranked_opportunities.json", help="Output file")
    parser.add_argument("--markdown", help="Also generate markdown report to this file")

    args = parser.parse_args()

    # Load files
    try:
        with open(args.profile) as f:
            profile = json.load(f)
        with open(args.opportunities) as f:
            opps = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    print(f"Scoring {len(opps)} opportunities against your profile...")

    # Score all
    scored = score_all_opportunities(profile, opps)

    # Save JSON
    with open(args.output, "w") as f:
        json.dump(scored, f, indent=2)
    print(f"✓ Scored opportunities saved: {args.output}")

    # Generate markdown if requested
    if args.markdown:
        report = generate_ranked_report(scored, top_n=15)
        with open(args.markdown, "w") as f:
            f.write(report)
        print(f"✓ Markdown report generated: {args.markdown}")

    # Print top 5
    print("\nTop 5 Opportunities for You:")
    for i, opp in enumerate(scored[:5], 1):
        print(f"{i}. {opp['name']} — {opp['fit_score']:.2f} ({opp['recommendation']})")

    return 0


if __name__ == "__main__":
    exit(main())
