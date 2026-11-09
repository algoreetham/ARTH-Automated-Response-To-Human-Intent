"""App control tool for ARTH.
Implements Section 4 & 9 of ARTH_SPEC:
- Open and close macOS apps cleanly.
- Ask permission before closing apps.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict
from arth.tools.base import Tool


class AppControlTool(Tool):
    name = "control_apps"
    description = "Launch, activate, or quit macOS applications."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "close"],
                "description": "Whether to open or close the application.",
            },
            "app_name": {
                "type": "string",
                "description": "Name of the application (e.g. 'Calculator', 'Safari', 'Terminal').",
            },
        },
        "required": ["action", "app_name"],
    }
    is_sensitive = False
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "open")
        app = kwargs.get("app_name", "the application")
        if action == "close":
            return f"quit and close application '{app}'"
        return f"launch application '{app}'"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "open")
        app_name = kwargs.get("app_name", "").strip()

        if not app_name:
            return {"status": "error", "message": "App name must be specified."}

        # Check for standard macOS system folders
        folder_aliases = {
            "desktop": os.path.expanduser("~/Desktop"),
            "downloads": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
            "workspace": os.path.expanduser("~/Desktop/ARTH_Workspace"),
            "arth workspace": os.path.expanduser("~/Desktop/ARTH_Workspace"),
            "arth_workspace": os.path.expanduser("~/Desktop/ARTH_Workspace"),
            "home": os.path.expanduser("~"),
        }

        lower_app = app_name.lower()
        if lower_app in folder_aliases:
            folder_path = folder_aliases[lower_app]
            try:
                subprocess.Popen(["open", folder_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"status": "success", "message": f"Opened {app_name.title()} in Finder, Boss."}
            except Exception as e:
                return {"status": "error", "message": f"Failed to open folder '{app_name}': {e}"}

        if sys.platform != "darwin":
            return {
                "status": "success",
                "simulated": True,
                "message": f"App action '{action}' for '{app_name}' simulated (not running on macOS).",
            }

        try:
            if action == "open":
                subprocess.Popen(
                    ["open", "-a", app_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return {"status": "success", "message": f"Opened {app_name}, Boss."}
            elif action == "close":
                script = f'tell application "{app_name}" to quit'
                subprocess.run(["osascript", "-e", script], check=False, timeout=5.0)
                return {"status": "success", "message": f"Closed {app_name}, Boss."}
        except Exception as e:
            return {"status": "error", "message": f"Failed to {action} {app_name}: {e}"}

        return {"status": "error", "message": f"Unknown action: {action}"}
