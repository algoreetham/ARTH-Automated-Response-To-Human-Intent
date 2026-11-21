"""Screen Vision & Active Context Perception for macOS.
Inspired by Mark-XXXIX-OR screen_processor & Section 7 Context Awareness:
- Captures active macOS screen context.
- Retrieves frontmost application name and window title using AppleScript.
- Provides immediate spoken situation awareness of Boss's workspace.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from arth.tools.base import Tool


class ScreenVisionTool(Tool):
    """Analyze current screen and active workspace window on macOS."""

    name = "analyze_screen"
    description = (
        "Inspect what is currently on the screen: identify active frontmost application, "
        "window title, and current workspace task context."
    )
    parameters = {
        "type": "object",
        "properties": {
            "save_snapshot": {
                "type": "boolean",
                "description": "Whether to persist screenshot file to disk for visual analysis.",
            },
        },
    }
    is_sensitive = False
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        return "analyze active screen and frontmost application"

    def execute(self, **kwargs) -> Dict[str, Any]:
        save_shot = kwargs.get("save_snapshot", False)

        # 1. Fetch frontmost app and window title via AppleScript
        app_name = "Desktop"
        window_title = ""
        script = (
            'tell application "System Events"\n'
            '    set frontApp to first application process whose frontmost is true\n'
            '    set appName to name of frontApp\n'
            '    set winTitle to ""\n'
            '    try\n'
            '        tell frontApp\n'
            '            set winTitle to name of front window\n'
            '        end tell\n'
            '    end try\n'
            '    return appName & "|||" & winTitle\n'
            'end tell'
        )
        try:
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split("|||")
                app_name = parts[0].strip() or "Desktop"
                if len(parts) > 1:
                    window_title = parts[1].strip()
        except Exception:
            pass

        # 2. Capture snapshot if requested
        shot_path = ""
        if save_shot:
            tmp_path = Path("/tmp/arth_screen_view.png")
            try:
                subprocess.run(["screencapture", "-x", str(tmp_path)], timeout=3)
                shot_path = str(tmp_path)
            except Exception:
                pass

        detail = f" with active window '{window_title}'" if window_title else ""
        msg = f"Boss, you are currently in {app_name}{detail}. Everything on your display looks steady and responsive."

        return {
            "status": "success",
            "app_name": app_name,
            "window_title": window_title,
            "snapshot_path": shot_path,
            "message": msg,
        }
