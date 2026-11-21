"""macOS LaunchAgent Auto-Start Manager for ARTH.
Implements Section 3 of ARTH_SPEC:
- Generates and installs LaunchAgent plist in ~/Library/LaunchAgents/com.arth.assistant.plist.
- Configures RunAtLoad and KeepAlive for seamless boot on user login.
- Supports install, uninstall, and status check.
"""

from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Dict


PLIST_LABEL = "com.arth.assistant"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_PATH = LAUNCH_AGENTS_DIR / f"{PLIST_LABEL}.plist"


class LaunchAgentManager:
    """Manages installation and status of ARTH auto-boot LaunchAgent on macOS."""

    def __init__(self, target_plist: Optional[Path] = None):
        self.plist_path = target_plist or PLIST_PATH
        self.workspace_dir = Path(__file__).resolve().parent.parent

    def generate_plist_content(self, python_exec: Optional[str] = None) -> Dict[str, Any]:
        """Generate property list configuration for macOS launchd."""
        py_bin = python_exec or sys.executable
        main_script = str(self.workspace_dir / "main.py")

        return {
            "Label": PLIST_LABEL,
            "ProgramArguments": [py_bin, main_script, "--web"],
            "RunAtLoad": True,
            "KeepAlive": {
                "SuccessfulExit": False,
            },
            "WorkingDirectory": str(self.workspace_dir),
            "StandardOutPath": str(self.workspace_dir / "logs" / "arth_stdout.log"),
            "StandardErrorPath": str(self.workspace_dir / "logs" / "arth_stderr.log"),
        }

    def install(self, python_exec: Optional[str] = None) -> Dict[str, Any]:
        """Write plist file and register with macOS launchctl."""
        self.plist_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate_plist_content(python_exec)

        with open(self.plist_path, "wb") as f:
            plistlib.dump(content, f)

        # Attempt launchctl load
        try:
            subprocess.run(["launchctl", "load", str(self.plist_path)], capture_output=True, timeout=3)
        except Exception:
            pass

        return {
            "status": "installed",
            "path": str(self.plist_path),
            "label": PLIST_LABEL,
            "message": f"Done, Boss! ARTH will now auto-start when you log in to macOS.",
        }

    def uninstall(self) -> Dict[str, Any]:
        """Unload and remove plist file."""
        if self.plist_path.exists():
            try:
                subprocess.run(["launchctl", "unload", str(self.plist_path)], capture_output=True, timeout=3)
            except Exception:
                pass
            try:
                self.plist_path.unlink()
            except Exception:
                pass
            return {"status": "uninstalled", "message": "Done, Boss! Auto-start LaunchAgent removed."}
        return {"status": "not_installed", "message": "LaunchAgent was not installed."}

    def is_installed(self) -> bool:
        """Check if plist file currently exists."""
        return self.plist_path.exists()
