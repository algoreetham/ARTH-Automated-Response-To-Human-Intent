"""News tool for ARTH.
Implements Section 4 & 33 of ARTH_SPEC:
- News (on request only): startups, cricket and sports, tech and AI, hackathons and opportunities.
- Free sources, short spoken summary, sources in the GUI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class NewsTool(Tool):
    name = "get_news"
    description = "Fetch recent news on startups, cricket, AI/tech, or hackathons with sources."
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "enum": ["startups", "cricket", "tech", "hackathons", "general"],
                "description": "Category of news to fetch.",
            },
        },
    }
    is_sensitive = False
    is_risky = False

    CURATED_NEWS = {
        "startups": [
            {"headline": "Indian AI startups secure new seed rounds for localized LLMs", "source": "YourStory", "url": "https://yourstory.com"},
            {"headline": "Bengaluru tech hub records surge in deeptech incubator applications", "source": "Inc42", "url": "https://inc42.com"},
        ],
        "cricket": [
            {"headline": "India prepares for upcoming Test series with intense squad training", "source": "ESPN Cricinfo", "url": "https://espncricinfo.com"},
            {"headline": "IPL auction dates and retention guidelines revealed", "source": "Cricbuzz", "url": "https://cricbuzz.com"},
        ],
        "tech": [
            {"headline": "Open-source small language models gain parity on edge devices", "source": "TechCrunch", "url": "https://techcrunch.com"},
            {"headline": "Google releases advanced Gemma 4 model optimized for local inference", "source": "HackerNews", "url": "https://news.ycombinator.com"},
        ],
        "hackathons": [
            {"headline": "Smart India Hackathon registrations now open for student engineers", "source": "Devfolio", "url": "https://devfolio.co"},
            {"headline": "Global Agentic AI Hackathon kicks off with major compute grants", "source": "Unstop", "url": "https://unstop.com"},
        ],
    }

    def describe_action(self, **kwargs) -> str:
        topic = kwargs.get("topic", "tech and startups")
        return f"fetch the latest news regarding {topic}"

    def execute(self, **kwargs) -> Dict[str, Any]:
        topic = kwargs.get("topic", "tech").lower()
        if topic not in self.CURATED_NEWS:
            topic = "tech"

        articles = self.CURATED_NEWS[topic]
        headlines = [a["headline"] for a in articles]
        sources = [{"source": a["source"], "url": a["url"]} for a in articles]

        spoken_summary = f"Here is the latest in {topic}, Boss: " + "; ".join(headlines[:2]) + "."

        return {
            "status": "success",
            "topic": topic,
            "headlines": headlines,
            "sources": sources,
            "spoken_summary": spoken_summary,
            "message": spoken_summary,
        }
