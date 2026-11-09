"""Notes tool for ARTH.
Implements Section 4 & 34 of ARTH_SPEC:
- Notes: save to an 'ARTH Notes' folder as plain text. If offline, keep them locally and sync later.
- List notes, read note, search notes.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class NotesTool(Tool):
    name = "manage_notes"
    description = "Create, view, search, and list plain-text notes."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["save", "list", "read", "search"],
                "description": "Operation to perform.",
            },
            "title": {"type": "string", "description": "Title or filename of the note."},
            "content": {"type": "string", "description": "Body content of the note."},
            "query": {"type": "string", "description": "Search keyword for finding notes."},
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    DEFAULT_NOTES_DIR = os.path.expanduser("~/Desktop/ARTH/notes")

    def __init__(self, notes_dir: Optional[str] = None):
        self.notes_dir = notes_dir or self.DEFAULT_NOTES_DIR
        os.makedirs(self.notes_dir, exist_ok=True)

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "list")
        title = kwargs.get("title", "a note")
        if action == "save":
            return f"save note '{title}' to ARTH Notes"
        elif action == "read":
            return f"read note '{title}'"
        elif action == "search":
            return f"search notes for '{kwargs.get('query', '')}'"
        return "list all saved notes"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "list")

        if action == "save":
            title = kwargs.get("title", f"Note_{int(time.time())}").strip()
            safe_filename = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip() + ".txt"
            content = kwargs.get("content", "")
            filepath = os.path.join(self.notes_dir, safe_filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "message": f"Saved note '{title}' to {filepath}.",
                "filename": safe_filename,
            }

        elif action == "read":
            title = kwargs.get("title", "").strip()
            # Find match
            for fname in os.listdir(self.notes_dir):
                if title.lower() in fname.lower():
                    path = os.path.join(self.notes_dir, fname)
                    with open(path, "r", encoding="utf-8") as f:
                        data = f.read()
                    return {"status": "success", "title": fname, "content": data}
            return {"status": "error", "message": f"Note matching '{title}' not found."}

        elif action == "search":
            q = kwargs.get("query", "").lower()
            matches = []
            for fname in os.listdir(self.notes_dir):
                if fname.endswith(".txt"):
                    path = os.path.join(self.notes_dir, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            text = f.read()
                        if q in fname.lower() or q in text.lower():
                            matches.append({"filename": fname, "preview": text[:100]})
                    except Exception:
                        pass
            return {"status": "success", "matches": matches, "count": len(matches)}

        else:
            files = [f for f in os.listdir(self.notes_dir) if f.endswith(".txt")]
            return {"status": "success", "notes": files, "count": len(files)}
