"""ResearchProfile Service

Fetches ORCID data and extracts research areas + expertise scores.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter

import requests


class OrcidClient:
    """Public ORCID API client (no auth required for public profiles)"""

    def __init__(self, orcid_id: str):
        self.orcid_id = orcid_id
        self.base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
        self.headers = {"Accept": "application/json"}

    def get_works_summary(self) -> dict:
        """Fetch all publications"""
        response = requests.get(f"{self.base_url}/works.json", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_record_summary(self) -> dict:
        """Fetch profile summary (name, bio, etc.)"""
        response = requests.get(f"{self.base_url}/record.json", headers=self.headers)
        response.raise_for_status()
        return response.json()


class ResearchAreaExtractor:
    """Extract research areas from publication titles and abstracts"""

    # Domain keywords mapped to normalized research areas
    DOMAIN_KEYWORDS = {
        "ai_calibration": [
            "calibration", "calibrated", "calibrating", "confidence",
            "uncertainty", "confidence calibration", "model calibration",
            "prediction calibration", "epistemic"
        ],
        "digital_minds": [
            "digital minds", "artificial consciousness", "machine consciousness",
            "AI consciousness", "machine sentience", "digital sentience",
            "machine welfare", "AI welfare", "digital welfare",
            "moral status AI", "sentience detection"
        ],
        "self_assessment": [
            "self-assessment", "self assessment", "self-description", "self description",
            "self-awareness", "self awareness", "metacognition", "introspection",
            "model self-knowledge", "behavioral observability"
        ],
        "ai_safety": [
            "AI safety", "alignment", "AI alignment", "x-risk", "existential risk",
            "AI control", "AI governance", "AI ethics", "safe AI", "beneficial AI"
        ],
        "behavioral_observability": [
            "behavioral observability", "behavioral observability", "observable behavior",
            "behavior measurement", "behavioral tracking", "model behavior",
            "AI behavior", "system behavior", "prediction accuracy"
        ],
        "nlp": [
            "natural language", "NLP", "language model", "LLM", "transformer",
            "BERT", "GPT", "text generation", "language understanding"
        ],
        "machine_learning": [
            "machine learning", "neural network", "deep learning", "training",
            "optimization", "supervised learning", "unsupervised learning"
        ],
        "evaluation": [
            "evaluation", "benchmark", "assessment", "metrics", "measurement",
            "performance", "accuracy", "effectiveness", "testing"
        ],
        "open_science": [
            "open source", "open science", "reproducible", "replication",
            "public dataset", "open access", "transparency"
        ]
    }

    def extract_areas(self, titles_abstracts: List[str], top_n: int = 5) -> Dict[str, float]:
        """
        Extract research areas from publication text.

        Args:
            titles_abstracts: List of publication titles (and optionally abstracts)
            top_n: Return top N domains

        Returns:
            Dict mapping domain → confidence score (0.0-1.0)
        """
        # Count keyword hits per domain
        domain_hits = Counter()
        total_text = " ".join(titles_abstracts).lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                # Case-insensitive word boundary search
                pattern = r'\b' + re.escape(keyword) + r'\b'
                hits = len(re.findall(pattern, total_text))
                if hits > 0:
                    domain_hits[domain] += hits

        # Convert hits to confidence scores
        if not domain_hits:
            return {}

        max_hits = max(domain_hits.values())
        scores = {
            domain: min(1.0, hits / max_hits * 0.95 + 0.1)  # normalize to 0.1-1.0
            for domain, hits in domain_hits.most_common(top_n)
        }

        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    def score_expertise(self, publication_count: int, citation_count: int = 0) -> float:
        """
        Score overall expertise (0.0-1.0) based on publication volume + citations.

        Simple model: more pubs + higher citations = higher expertise
        """
        # Base score from publication count (1 pub = 0.3, 5+ = 0.9)
        pub_score = min(0.9, 0.15 + publication_count * 0.15)

        # Boost from citations (rough estimate)
        citation_score = min(0.3, citation_count * 0.01)  # 100 citations = +0.3

        return min(1.0, pub_score + citation_score)


class ResearchProfile:
    """Main service: fetch ORCID, extract profile, score expertise"""

    def __init__(self, orcid_id: str, data_dir: str = "data"):
        self.orcid_id = orcid_id
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.orcid_client = OrcidClient(orcid_id)
        self.extractor = ResearchAreaExtractor()

        self.profile = None
        self.publications = []
        self.research_areas = {}
        self.expertise_scores = {}

    def fetch(self) -> bool:
        """Fetch and process ORCID data"""
        try:
            # Get record + works
            record = self.orcid_client.get_record_summary()
            works_data = self.orcid_client.get_works_summary()

            # Extract profile info
            person = record.get("person", {})
            self.profile = {
                "name": person.get("name", {}).get("credit-name", {}).get("value"),
                "orcid_id": self.orcid_id,
                "biography": person.get("biography", {}).get("content"),
            }

            # Extract publications
            groups = works_data.get("group", [])
            publication_titles = []

            for group in groups:
                for work in group.get("work-summary", []):
                    title = work.get("title", {}).get("title", {}).get("value")
                    if title:
                        publication_titles.append(title)
                        self.publications.append({
                            "title": title,
                            "type": work.get("type"),
                            "year": work.get("publication-date", {}).get("year", {}).get("value"),
                            "put_code": work.get("put-code")
                        })

            # Extract research areas from titles
            self.research_areas = self.extractor.extract_areas(publication_titles, top_n=8)

            # Score overall expertise (simple: publication count)
            expertise_base = min(1.0, 0.5 + len(self.publications) * 0.05)
            self.expertise_scores = {
                area: min(1.0, score * (expertise_base + 0.1))
                for area, score in self.research_areas.items()
            }

            return True

        except Exception as e:
            print(f"Error fetching ORCID data: {e}")
            return False

    def save(self) -> Tuple[Path, Path]:
        """Save research_profile.json and expertise_map.json"""
        profile_data = {
            "orcid_id": self.orcid_id,
            "profile": self.profile,
            "publications": self.publications,
            "research_areas": self.research_areas,
            "expertise_scores": self.expertise_scores,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "publication_count": len(self.publications)
        }

        profile_file = self.data_dir / "research_profile.json"
        with open(profile_file, "w") as f:
            json.dump(profile_data, f, indent=2)

        # Separate expertise map for easy lookup
        expertise_map = {
            "orcid_id": self.orcid_id,
            "expertise_scores": self.expertise_scores,
            "research_areas": list(self.research_areas.keys()),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        expertise_file = self.data_dir / "expertise_map.json"
        with open(expertise_file, "w") as f:
            json.dump(expertise_map, f, indent=2)

        return profile_file, expertise_file

    def to_dict(self) -> dict:
        """Return as dictionary"""
        return {
            "orcid_id": self.orcid_id,
            "profile": self.profile,
            "publications": self.publications,
            "research_areas": self.research_areas,
            "expertise_scores": self.expertise_scores,
            "publication_count": len(self.publications)
        }


def main():
    """CLI: fetch and save research profile"""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch and analyze ORCID research profile")
    parser.add_argument("--orcid-id", default="0009-0003-7540-4245", help="ORCID ID")
    parser.add_argument("--data-dir", default="data", help="Directory to save data")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print(f"Fetching ORCID profile: {args.orcid_id}")
    profile = ResearchProfile(args.orcid_id, args.data_dir)

    if profile.fetch():
        profile_file, expertise_file = profile.save()
        print(f"✓ Profile saved: {profile_file}")
        print(f"✓ Expertise map saved: {expertise_file}")

        if args.verbose:
            print(f"\nName: {profile.profile['name']}")
            print(f"Publications: {len(profile.publications)}")
            print(f"\nResearch Areas:")
            for area, score in profile.research_areas.items():
                print(f"  {area}: {score:.2f}")
    else:
        print("✗ Failed to fetch profile")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
