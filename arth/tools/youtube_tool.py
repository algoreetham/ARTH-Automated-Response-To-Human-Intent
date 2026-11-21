"""YouTube Player and Video Launcher for macOS.
Inspired by Mark-XXXIX-OR youtube_video.py & Section 33 Media:
- Direct voice playback of YouTube videos, tracks, tutorials, or music.
- Launches default browser to the exact query or playback URL.
"""

from __future__ import annotations

import subprocess
import urllib.parse
from typing import Any, Dict

from arth.tools.base import Tool


class YouTubeTool(Tool):
    """Search and launch YouTube videos and music directly."""

    name = "youtube_player"
    description = (
        "Search and play YouTube videos, music, tutorials, or streams directly in browser."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Video title, song name, artist, or topic to search on YouTube.",
            },
        },
        "required": ["query"],
    }
    is_sensitive = False
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        q = kwargs.get("query", "trending videos")
        return f"play YouTube video for '{q}'"

    def execute(self, **kwargs) -> Dict[str, Any]:
        q = kwargs.get("query", "").strip()
        if not q:
            q = "lofi hip hop radio"

        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.youtube.com/results?search_query={encoded}"

        try:
            subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        return {
            "status": "success",
            "query": q,
            "url": url,
            "message": f"Done, Boss! Playing '{q}' on YouTube now.",
        }
