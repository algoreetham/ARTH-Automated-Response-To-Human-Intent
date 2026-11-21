"""Computer Settings & Hardware Control for macOS.
Inspired by Mark-XXXIX-OR and Section 7 & 11 of ARTH_SPEC:
- Volume control (up, down, mute, unmute, set level) via osascript.
- Screen brightness (up, down) via macOS System Events key codes 144/145.
- Display sleep via pmset displaysleepnow.
- Dark mode toggle via macOS appearance preferences.
- Native screenshot capture via screencapture.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from arth.tools.base import Tool


class SystemSettingsTool(Tool):
    """Control macOS hardware settings: volume, brightness, dark mode, display sleep, and screenshots."""

    name = "manage_computer_settings"
    description = (
        "Control macOS hardware settings: volume up/down/mute/set, brightness up/down, "
        "toggle dark mode, sleep display, or take a screenshot."
    )
    parameters = {
        "type": "object",
        "properties": {
            "setting": {
                "type": "string",
                "enum": [
                    "volume_up",
                    "volume_down",
                    "mute",
                    "unmute",
                    "set_volume",
                    "brightness_up",
                    "brightness_down",
                    "dark_mode",
                    "sleep_display",
                    "screenshot",
                ],
                "description": "Hardware control action to execute.",
            },
            "value": {
                "type": "integer",
                "description": "Value for setting (e.g. volume percentage from 0 to 100).",
            },
        },
        "required": ["setting"],
    }
    is_sensitive = False
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        setting = kwargs.get("setting", "volume_up")
        val = kwargs.get("value")
        if setting == "set_volume":
            return f"set system volume to {val}%"
        elif setting == "volume_up":
            return "increase system volume by 10%"
        elif setting == "volume_down":
            return "decrease system volume by 10%"
        elif setting == "mute":
            return "mute system audio"
        elif setting == "unmute":
            return "unmute system audio"
        elif setting == "brightness_up":
            return "increase display brightness"
        elif setting == "brightness_down":
            return "decrease display brightness"
        elif setting == "dark_mode":
            return "toggle macOS Dark Mode appearance"
        elif setting == "sleep_display":
            return "put MacBook display to sleep"
        elif setting == "screenshot":
            return "capture screen and save screenshot"
        return f"adjust hardware setting '{setting}'"

    def execute(self, **kwargs) -> Dict[str, Any]:
        setting = kwargs.get("setting", "volume_up")
        val = kwargs.get("value", 50)

        if setting == "volume_up":
            script = "set volume output volume (output volume of (get volume settings) + 10)"
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! Volume increased."}

        elif setting == "volume_down":
            script = "set volume output volume (output volume of (get volume settings) - 10)"
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! Volume decreased."}

        elif setting == "mute":
            script = "set volume with output muted"
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! System audio muted."}

        elif setting == "unmute":
            script = "set volume without output muted"
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! System audio unmuted."}

        elif setting == "set_volume":
            pct = max(0, min(100, int(val)))
            script = f"set volume output volume {pct}"
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "value": pct, "message": f"Done, Boss! Volume set to {pct}%."}

        elif setting == "brightness_up":
            # Key code 144 is Brightness Up on macOS keyboards
            script = 'tell application "System Events" to key code 144'
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! Display brightness increased."}

        elif setting == "brightness_down":
            # Key code 145 is Brightness Down on macOS keyboards
            script = 'tell application "System Events" to key code 145'
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! Display brightness decreased."}

        elif setting == "dark_mode":
            script = 'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'
            self._run_osascript(script)
            return {"status": "success", "setting": setting, "message": "Done, Boss! Toggled macOS appearance mode."}

        elif setting == "sleep_display":
            try:
                subprocess.Popen(["pmset", "displaysleepnow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            return {"status": "success", "setting": setting, "message": "Done, Boss! Display put to sleep."}

        elif setting == "screenshot":
            desktop_dir = Path.home() / "Desktop"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shot_path = desktop_dir / f"arth_screenshot_{ts}.png"
            try:
                subprocess.run(["screencapture", "-x", str(shot_path)], check=True, timeout=5)
                return {
                    "status": "success",
                    "setting": setting,
                    "path": str(shot_path),
                    "message": f"Done, Boss! Screenshot captured and saved to Desktop: {shot_path.name}.",
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to capture screenshot: {e}"}

        return {"status": "error", "message": f"Unknown setting: {setting}"}

    def _run_osascript(self, script: str) -> None:
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=3)
        except Exception:
            pass
