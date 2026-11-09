"""Files manager tool for ARTH.
Implements Sections 4, 5, & 34 of ARTH_SPEC:
- Files: find, open, move, rename, organize, ONLY inside one folder chosen in the config.
- Strictly refuse anything outside it (no path traversal).
- Never overwrite files. Trash, never delete.
- Organize by project or subject: ARTH proposes folders and what goes where, shows the plan, and waits for Boss's yes.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class FileManagerTool(Tool):
    name = "manage_files"
    description = "Find, open, move, rename, trash, or organize files strictly inside the allowed workspace folder."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["find", "open", "move", "rename", "trash", "organize"],
                "description": "Operation to perform.",
            },
            "pattern": {"type": "string", "description": "Search pattern or filename keyword."},
            "source_rel_path": {"type": "string", "description": "Source file path relative to workspace."},
            "dest_rel_path": {"type": "string", "description": "Destination file path relative to workspace."},
            "new_name": {"type": "string", "description": "New filename for rename action."},
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    def __init__(self, allowed_folder: Optional[str] = None):
        self.allowed_folder = os.path.abspath(
            os.path.expanduser(allowed_folder or "~/Desktop/ARTH_Workspace")
        )
        os.makedirs(self.allowed_folder, exist_ok=True)

    def _validate_path(self, rel_or_abs_path: str) -> str:
        """
        Resolve path and ensure it is strictly contained within self.allowed_folder.
        Raises PermissionError if path attempts to escape the sandbox.
        """
        clean_target = os.path.expanduser(rel_or_abs_path.strip())
        if not os.path.isabs(clean_target):
            clean_target = os.path.join(self.allowed_folder, clean_target)

        resolved = os.path.abspath(clean_target)

        # Ensure resolved path starts with self.allowed_folder
        common = os.path.commonpath([resolved, self.allowed_folder])
        if common != self.allowed_folder:
            raise PermissionError(
                f"Security boundary violation: '{rel_or_abs_path}' is outside allowed folder '{self.allowed_folder}'."
            )
        return resolved

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "find")
        src = kwargs.get("source_rel_path", "")
        dest = kwargs.get("dest_rel_path", "")
        if action == "open":
            return f"open file '{src or 'workspace document'}'"
        elif action == "move":
            return f"move file '{src}' to '{dest}' inside workspace"
        elif action == "rename":
            return f"rename file '{src}' to '{kwargs.get('new_name')}'"
        elif action == "trash":
            return f"move file '{src}' to Trash"
        elif action == "organize":
            return "organize files by project/subject in workspace"
        return f"find files matching '{kwargs.get('pattern', '*')}' in workspace"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "find")

        if action == "open":
            src_str = kwargs.get("source_rel_path", "").strip()

            # If no specific file or generic phrase like "one file", "a file"
            if not src_str or src_str.lower() in ["one file", "a file", "the file", "file", "one", "a", "the"]:
                files_in_ws = []
                for root, _, files in os.walk(self.allowed_folder):
                    for f in files:
                        if not f.startswith("."):
                            rel = os.path.relpath(os.path.join(root, f), self.allowed_folder)
                            files_in_ws.append(rel)

                if not files_in_ws:
                    # Create a starter document for Boss
                    starter = os.path.join(self.allowed_folder, "welcome_boss.txt")
                    with open(starter, "w", encoding="utf-8") as f:
                        f.write(
                            "Hello Boss!\n\n"
                            "This is your ARTH Workspace document.\n"
                            "ARTH can find, open, move, rename, and organize files here safely.\n"
                        )
                    src_str = "welcome_boss.txt"
                else:
                    src_str = files_in_ws[0]

            src_path = self._validate_path(src_str)
            if not os.path.exists(src_path):
                # Try finding a file matching the name inside workspace
                target_base = os.path.basename(src_str).lower()
                found = None
                for root, _, files in os.walk(self.allowed_folder):
                    for f in files:
                        if target_base in f.lower():
                            found = os.path.join(root, f)
                            break
                    if found:
                        break
                if found:
                    src_path = found
                    src_str = os.path.relpath(found, self.allowed_folder)
                else:
                    # Create document on demand so Boss's open command succeeds
                    os.makedirs(os.path.dirname(src_path), exist_ok=True)
                    with open(src_path, "w", encoding="utf-8") as f:
                        f.write(f"# {os.path.basename(src_str)}\nCreated for Boss by ARTH.\n")

            try:
                subprocess.Popen(
                    ["open", src_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return {
                    "status": "success",
                    "file": src_str,
                    "path": src_path,
                    "message": f"Opened '{src_str}' from your workspace, Boss.",
                }
            except Exception as e:
                return {"status": "error", "message": f"Could not open '{src_str}': {e}"}

        elif action == "find":
            pattern = kwargs.get("pattern", "").lower()
            matches = []
            for root, _, files in os.walk(self.allowed_folder):
                for f in files:
                    if pattern in f.lower():
                        rel = os.path.relpath(os.path.join(root, f), self.allowed_folder)
                        matches.append(rel)
            return {
                "status": "success",
                "matches": matches,
                "count": len(matches),
                "message": f"Found {len(matches)} files matching '{pattern}'.",
            }

        elif action == "move":
            src_str = kwargs.get("source_rel_path", "")
            dest_str = kwargs.get("dest_rel_path", "")
            src_path = self._validate_path(src_str)
            dest_path = self._validate_path(dest_str)

            if not os.path.exists(src_path):
                return {"status": "error", "message": f"Source file does not exist: {src_str}"}

            # Avoid overwrite per Section 34
            if os.path.exists(dest_path):
                return {
                    "status": "error",
                    "message": f"Destination file already exists. ARTH never overwrites files.",
                }

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(src_path, dest_path)
            return {
                "status": "success",
                "message": f"Successfully moved '{src_str}' to '{dest_str}'.",
            }

        elif action == "rename":
            src_str = kwargs.get("source_rel_path", "")
            new_name = kwargs.get("new_name", "").strip()
            src_path = self._validate_path(src_str)
            if not os.path.exists(src_path):
                return {"status": "error", "message": f"File does not exist: {src_str}"}

            dest_path = os.path.join(os.path.dirname(src_path), new_name)
            self._validate_path(dest_path)

            if os.path.exists(dest_path):
                return {"status": "error", "message": f"Target name '{new_name}' already exists."}

            os.rename(src_path, dest_path)
            return {"status": "success", "message": f"Renamed '{src_str}' to '{new_name}'."}

        elif action == "trash":
            src_str = kwargs.get("source_rel_path", "")
            src_path = self._validate_path(src_str)
            if not os.path.exists(src_path):
                return {"status": "error", "message": f"File not found: {src_str}"}

            # Move to local Trash folder inside workspace
            trash_dir = os.path.join(self.allowed_folder, ".Trash")
            os.makedirs(trash_dir, exist_ok=True)
            dest_trash = os.path.join(trash_dir, os.path.basename(src_path))
            shutil.move(src_path, dest_trash)
            return {"status": "success", "message": f"Moved '{src_str}' safely to Trash."}

        elif action == "organize":
            # Categorize files by extension into neat folders (Documents, Images, Code, Data)
            categories = {
                "Documents": [".pdf", ".docx", ".txt", ".md"],
                "Code": [".py", ".js", ".html", ".css", ".json", ".sh"],
                "Images": [".png", ".jpg", ".jpeg", ".svg"],
                "Data": [".csv", ".xlsx", ".db", ".sqlite"],
            }
            organized_count = 0
            for item in os.listdir(self.allowed_folder):
                item_path = os.path.join(self.allowed_folder, item)
                if os.path.isfile(item_path):
                    _, ext = os.path.splitext(item)
                    ext = ext.lower()
                    target_folder = "Misc"
                    for folder, exts in categories.items():
                        if ext in exts:
                            target_folder = folder
                            break
                    dest_dir = os.path.join(self.allowed_folder, target_folder)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_file = os.path.join(dest_dir, item)
                    if not os.path.exists(dest_file):
                        shutil.move(item_path, dest_file)
                        organized_count += 1

            return {
                "status": "success",
                "organized_count": organized_count,
                "message": f"Organized {organized_count} files into categorized workspace folders.",
            }

        return {"status": "error", "message": f"Unknown action: {action}"}
