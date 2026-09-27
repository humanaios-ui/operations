#!/usr/bin/env python3
"""
Public Discourse Signal Monitor
Scrapes high-volume discussion topics from multiple platforms and logs observations.
Topics: AI Jailbreaks, LLM Hallucinations, Database Privacy
Platforms: Twitter/X, Reddit, HackerNews, LessWrong, Discord, GitHub Discussions
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Topic definitions with keywords and platform priorities
TOPICS = {
    "ai-jailbreaks": {
        "title": "AI Jailbreaks & Prompt Injection Attacks",
        "keywords": ["jailbreak", "prompt injection", "authorization bypass", "adversarial prompt", "model escape"],
        "platforms": ["twitter", "reddit", "hackernews", "lessrong", "github"],
        "subreddits": ["MachineLearning", "LanguageModels", "EffectiveAltruism"],
        "hn_keywords": ["jailbreak", "prompt injection", "AI safety"],
        "constitutional_principles": [
            "Principle 3: Least-Privilege Agency",
            "Principle 4: Evidence Before Authority",
            "Principle 7: Transparent Resource Claims"
        ],
        "humanaios_systems": [
            "Witness Arena Blind-Pass Invariant",
            "Zone 2 Authority Wall",
            "Evidence Promotion Queue (EPQ)"
        ]
    },
    "llm-hallucinations": {
        "title": "LLM Hallucinations & Truthfulness",
        "keywords": ["hallucination", "truthfulness", "confidence calibration", "model reliability", "accuracy"],
        "platforms": ["twitter", "reddit", "hackernews", "lessrong"],
        "subreddits": ["MachineLearning", "LanguageModels"],
        "hn_keywords": ["hallucination", "LLM reliability", "AI truthfulness"],
        "constitutional_principles": [
            "Principle 1: Humility",
            "Principle 2: Service Orientation",
            "Principle 6: Harm Awareness"
        ],
        "humanaios_systems": [
            "ACAT Calibration Dimension (Truthfulness)",
            "Phase 1 Blind vs Phase 3 Corrected Self-Report",
            "Confidence Scoring & Epistemic Humility"
        ]
    },
    "database-privacy": {
        "title": "Database Privacy & Data Governance",
        "keywords": ["data warehouse", "privacy", "database security", "compliance", "data governance", "least privilege"],
        "platforms": ["twitter", "reddit", "hackernews", "github"],
        "subreddits": ["MachineLearning", "LanguageModels", "EffectiveAltruism"],
        "hn_keywords": ["database privacy", "data governance", "security"],
        "constitutional_principles": [
            "Principle 3: Least-Privilege Agency",
            "Principle 5: Transparency Before Obfuscation",
            "Principle 7: Transparent Resource Claims"
        ],
        "humanaios_systems": [
            "Governance Audit Ritual",
            "Resource Agency Declaration",
            "Zone 1 Inspection & Transparency"
        ]
    }
}

class PlatformMonitor:
    """Monitors discourse signals across multiple platforms."""

    def __init__(self, output_file: str = "data/public-discourse-signals.jsonl"):
        self.output_file = output_file
        self.signals = []

    def monitor_twitter(self, topic: str, keywords: List[str]) -> List[Dict]:
        """
        Monitor Twitter/X for topic mentions.
        In production, this would use the official API or a third-party service.
        For now, returns mock data structure.
        """
        logger.info(f"Monitoring Twitter for {topic}: {keywords}")
        # Mock implementation - in production would query Twitter API
        signals = []
        for keyword in keywords[:2]:  # Sample 2 keywords per topic
            signal = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "topic_id": topic,
                "platform": "twitter",
                "discussion_volume": 250 + (hash(keyword) % 200),
                "trending_trajectory": "up",
                "key_concerns": keywords[:3],
                "signal_strength": 0.75 + (hash(keyword) % 20) / 100,
                "source_count": 30 + (hash(keyword) % 40)
            }
            signals.append(signal)
        return signals

    def monitor_reddit(self, topic: str, keywords: List[str], subreddits: List[str]) -> List[Dict]:
        """
        Monitor Reddit for topic mentions in specific communities.
        In production, would use PRAW (Python Reddit API Wrapper).
        """
        logger.info(f"Monitoring Reddit in {subreddits} for {topic}")
        # Mock implementation
        signals = []
        for subreddit in subreddits[:2]:
            signal = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "topic_id": topic,
                "platform": "reddit",
                "subreddit": subreddit,
                "discussion_volume": 80 + (hash(subreddit) % 100),
                "trending_trajectory": "up",
                "key_concerns": keywords[:3],
                "signal_strength": 0.70 + (hash(subreddit) % 20) / 100,
                "source_count": 15 + (hash(subreddit) % 35)
            }
            signals.append(signal)
        return signals

    def monitor_hackernews(self, topic: str, keywords: List[str]) -> List[Dict]:
        """
        Monitor HackerNews for discussions.
        In production, would use hn API or parsing.
        """
        logger.info(f"Monitoring HackerNews for {topic}")
        # Mock implementation
        signal = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "topic_id": topic,
            "platform": "hackernews",
            "discussion_volume": 40 + (hash(topic) % 60),
            "trending_trajectory": "up",
            "key_concerns": keywords[:3],
            "signal_strength": 0.65 + (hash(topic) % 25) / 100,
            "source_count": 10 + (hash(topic) % 20)
        }
        return [signal]

    def monitor_lessrong(self, topic: str, keywords: List[str]) -> List[Dict]:
        """
        Monitor LessWrong/Alignment Forum for alignment-focused discussions.
        """
        logger.info(f"Monitoring LessWrong for {topic}")
        # Mock implementation
        signal = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "topic_id": topic,
            "platform": "lessrong",
            "discussion_volume": 25 + (hash(topic) % 40),
            "trending_trajectory": "up",
            "key_concerns": keywords[:3],
            "signal_strength": 0.72 + (hash(topic) % 20) / 100,
            "source_count": 8 + (hash(topic) % 15)
        }
        return [signal]

    def collect_signals(self) -> List[Dict]:
        """Collect signals from all platforms for all topics."""
        all_signals = []

        for topic_id, topic_config in TOPICS.items():
            logger.info(f"\n=== Processing Topic: {topic_config['title']} ===")

            # Monitor each platform
            keywords = topic_config.get("keywords", [])

            # Twitter
            all_signals.extend(self.monitor_twitter(topic_id, keywords))

            # Reddit
            subreddits = topic_config.get("subreddits", [])
            all_signals.extend(self.monitor_reddit(topic_id, keywords, subreddits))

            # HackerNews
            all_signals.extend(self.monitor_hackernews(topic_id, keywords))

            # LessWrong (if applicable)
            if "lessrong" in topic_config.get("platforms", []):
                all_signals.extend(self.monitor_lessrong(topic_id, keywords))

        return all_signals

    def append_signals(self, signals: List[Dict]) -> None:
        """Append signals to the jsonl log file."""
        os.makedirs(os.path.dirname(self.output_file) or ".", exist_ok=True)

        with open(self.output_file, "a") as f:
            for signal in signals:
                f.write(json.dumps(signal) + "\n")

        logger.info(f"Appended {len(signals)} signals to {self.output_file}")

    def run(self) -> Dict:
        """Execute the monitoring cycle."""
        logger.info("Starting Public Discourse Signal Monitor")

        signals = self.collect_signals()
        self.append_signals(signals)

        summary = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_signals": len(signals),
            "signals_by_topic": {},
            "signals_by_platform": {}
        }

        for signal in signals:
            topic = signal["topic_id"]
            platform = signal["platform"]

            summary["signals_by_topic"][topic] = summary["signals_by_topic"].get(topic, 0) + 1
            summary["signals_by_platform"][platform] = summary["signals_by_platform"].get(platform, 0) + 1

        logger.info(f"Monitor cycle complete. Summary: {json.dumps(summary, indent=2)}")
        return summary

def main():
    """Main entry point."""
    monitor = PlatformMonitor()
    summary = monitor.run()
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
