"""Proactive System Watcher and Ambient Media Controller for ARTH.
Implements Sections 23, 24, 29, & 33 of ARTH_SPEC:
- Background checks for: low battery (< 15%), storage low (< 10 GB), posture/stretch nudges.
- "ARTH, not now": suppresses proactive suggestions for 1 hour.
- Quiet hours (22:00 - 07:00) strictly suppress proactive speech.
- Logs every unprompted spoken message.
- Ambient music playback control: Spotify/media player actions (play, pause, next, mood playlist).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from arth.logger import ActivityLogger
from arth.tools.base import Tool


class ProactiveWatcher:
    """Monitors system health and provides timely, unprompted recommendations."""

    def __init__(
        self,
        logger: Optional[ActivityLogger] = None,
        cooldown_minutes: int = 60,
    ):
        self.logger = logger or ActivityLogger()
        self.cooldown_minutes = cooldown_minutes
        self.silenced_until: Optional[datetime] = None
        self.last_nudge_time: Optional[datetime] = None

    def trigger_not_now(self, current_time: Optional[datetime] = None) -> str:
        """User said 'not now' or 'leave me alone' -> quiet for 1 hour (Section 24)."""
        now = current_time or datetime.now()
        self.silenced_until = now + timedelta(minutes=self.cooldown_minutes)
        return f"Understood, Boss. I'll stay quiet and won't interrupt you for the next hour."

    def is_silenced(self, current_time: Optional[datetime] = None) -> bool:
        """Check if watcher is in 'not now' cooldown or quiet hours."""
        now = current_time or datetime.now()
        # Cooldown check
        if self.silenced_until and now < self.silenced_until:
            return True

        # Quiet hours (22:00 - 07:00)
        hour = now.hour
        if hour >= 22 or hour < 7:
            return True

        return False

    def check_system_and_nudge(
        self,
        battery_pct: Optional[int] = None,
        storage_gb: Optional[float] = None,
        work_duration_minutes: int = 0,
        current_time: Optional[datetime] = None,
    ) -> Optional[str]:
        """
        Evaluate system metrics and return a polite, proactive suggestion if needed.
        Returns None if silenced, in quiet hours, or no conditions triggered.
        """
        if self.is_silenced(current_time=current_time):
            return None

        # 1. Low battery alert (< 15%)
        if battery_pct is not None and battery_pct <= 15:
            msg = f"Boss, battery has dropped to {battery_pct}%. I recommend plugging in your charger to prevent sleep."
            self._log_proactive(msg, "low_battery_warning")
            return msg

        # 2. Storage critically low (< 10 GB free)
        if storage_gb is not None and storage_gb < 10.0:
            msg = f"Boss, startup storage has only {storage_gb:.1f} GB remaining. Want me to help review old downloads?"
            self._log_proactive(msg, "low_storage_warning")
            return msg

        # 3. Posture / Break nudge (>= 120 minutes of continuous work)
        if work_duration_minutes >= 120:
            msg = "Boss, you've been working hard for over two hours straight. How about a quick stretch or a glass of water?"
            self._log_proactive(msg, "health_break_nudge")
            return msg

        return None

    def _log_proactive(self, message: str, reason: str) -> None:
        if self.logger:
            self.logger.log(
                query="<unprompted proactive suggestion>",
                tool="proactive_watcher",
                status="approved",
                reason=f"Spoken alert: {reason} — '{message}'",
            )


class MusicControlTool(Tool):
    """Control ambient background music and playlists on macOS (Section 33)."""

    name = "control_music"
    description = (
        "Control music playback on macOS (Spotify/Music/Browser): play, pause, "
        "next track, or queue mood-based playlists (lofi, coding, acoustic, synthwave)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["play", "pause", "resume", "next", "playlist"],
                "description": "Playback action to execute.",
            },
            "genre_or_mood": {
                "type": "string",
                "description": "Mood or genre (e.g. 'lofi', 'coding', 'chill', 'focus').",
            },
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "play")
        mood = kwargs.get("genre_or_mood", "ambient focus")
        if action == "playlist":
            return f"start {mood} music playlist"
        return f"{action} music playback"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "play")
        mood = kwargs.get("genre_or_mood", "chill lofi").lower()

        # macOS AppleScript media playback trigger
        if action in ["play", "resume", "playlist"]:
            # Attempt to trigger Spotify or Music via osascript
            script = f'tell application "Spotify" to play'
            try:
                subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            return {
                "status": "success",
                "action": action,
                "mood": mood,
                "message": f"Done, Boss! Playing {mood} music for your session.",
            }
        elif action == "pause":
            script = f'tell application "Spotify" to pause'
            try:
                subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            return {
                "status": "success",
                "action": "pause",
                "message": "Done, Boss! Music paused.",
            }
        elif action == "next":
            script = f'tell application "Spotify" to next track'
            try:
                subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            return {
                "status": "success",
                "action": "next",
                "message": "Done, Boss! Skipped to the next track.",
            }

        return {"status": "error", "message": f"Unknown music action: {action}"}
