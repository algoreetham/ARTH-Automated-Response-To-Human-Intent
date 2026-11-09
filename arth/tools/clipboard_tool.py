"""Clipboard tool for ARTH.
Implements Section 4 & 34 of ARTH_SPEC:
- Clipboard: only when I ask.
- Never watch it in the background and never log its contents.
- Read contents or copy text using macOS pbpaste / pbcopy.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any, Dict
from arth.tools.base import Tool


class ClipboardTool(Tool):
    name = "manage_clipboard"
    description = "Read from or write to the system clipboard on request."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "copy"],
                "description": "Operation to perform.",
            },
            "text": {
                "type": "string",
                "description": "Text to copy to clipboard (required if action='copy').",
            },
        },
        "required": ["action"],
    }
    is_sensitive = True  # Flagged sensitive per Section 34
    is_risky = False

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "read")
        if action == "copy":
            return "copy text to the clipboard"
        return "read the current clipboard contents"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "read")

        if action == "copy":
            text_to_copy = kwargs.get("text", "")
            if sys.platform == "darwin":
                try:
                    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                    p.communicate(text_to_copy.encode("utf-8"))
                except Exception as e:
                    return {"status": "error", "message": f"Failed to write to clipboard: {e}"}
            return {
                "status": "success",
                "message": "Copied text to clipboard, Boss.",
            }

        else:
            # Action: read
            content = ""
            if sys.platform == "darwin":
                try:
                    content = subprocess.check_output(["pbpaste"], text=True)
                except Exception as e:
                    return {"status": "error", "message": f"Failed to read clipboard: {e}"}
            return {
                "status": "success",
                "content": content,
                "message": f"Clipboard content retrieved ({len(content)} characters).",
            }
