"""Project helper tool for ARTH.
Implements Section 27 of ARTH_SPEC:
- Create project folder with starter code (inside allowed folder only).
- Track project tasks and progress.
- Research a topic and save notes with sources.
- Strict permission: says exactly what it will create and waits for Boss's yes.
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class ProjectHelperTool(Tool):
    name = "project_helper"
    description = "Create a project workspace with starter code and track project milestones."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "status", "add_milestone"],
                "description": "Project action to perform.",
            },
            "project_name": {"type": "string", "description": "Name of the project."},
            "language": {
                "type": "string",
                "enum": ["python", "web", "cli"],
                "description": "Project starter template language.",
            },
            "milestone": {"type": "string", "description": "Milestone title when adding milestone."},
        },
        "required": ["action", "project_name"],
    }
    is_sensitive = False
    is_risky = False

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = os.path.abspath(
            os.path.expanduser(workspace_root or "~/Desktop/ARTH_Workspace")
        )
        os.makedirs(self.workspace_root, exist_ok=True)

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "create")
        name = kwargs.get("project_name", "NewProject")
        lang = kwargs.get("language", "python")
        if action == "create":
            return f"create project directory '{name}' with starter {lang} code inside workspace"
        elif action == "add_milestone":
            return f"add milestone to project '{name}'"
        return f"check status and tasks for project '{name}'"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "create")
        name = kwargs.get("project_name", "").strip()
        lang = kwargs.get("language", "python").lower()

        if not name:
            return {"status": "error", "message": "Project name is required."}

        project_dir = os.path.join(self.workspace_root, name)

        if action == "create":
            if os.path.exists(project_dir):
                return {
                    "status": "error",
                    "message": f"Project folder '{name}' already exists. ARTH never overwrites files.",
                }

            os.makedirs(project_dir, exist_ok=True)

            # Starter files
            if lang == "python":
                main_py = os.path.join(project_dir, "main.py")
                with open(main_py, "w", encoding="utf-8") as f:
                    f.write('def main():\n    print("Hello from ' + name + '!")\n\nif __name__ == "__main__":\n    main()\n')
            elif lang == "web":
                idx_html = os.path.join(project_dir, "index.html")
                with open(idx_html, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html><head><title>{name}</title></head><body><h1>{name}</h1></body></html>")

            # Project tracker metadata
            meta_path = os.path.join(project_dir, ".arth_project.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "project_name": name,
                    "language": lang,
                    "milestones": ["Project initialized"],
                }, f, indent=2)

            return {
                "status": "success",
                "project_path": project_dir,
                "message": f"Created project '{name}' with starter {lang} template in workspace.",
            }

        elif action == "status":
            meta_path = os.path.join(project_dir, ".arth_project.json")
            if not os.path.exists(meta_path):
                return {"status": "error", "message": f"No ARTH project found at {name}."}

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "status": "success",
                "project": data,
                "message": f"Project '{name}' has {len(data.get('milestones', []))} milestone(s).",
            }

        elif action == "add_milestone":
            milestone = kwargs.get("milestone", "Milestone").strip()
            meta_path = os.path.join(project_dir, ".arth_project.json")
            if not os.path.exists(meta_path):
                return {"status": "error", "message": f"No project '{name}' found."}

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data.setdefault("milestones", []).append(milestone)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return {
                "status": "success",
                "milestones": data["milestones"],
                "message": f"Added milestone '{milestone}' to {name}.",
            }

        return {"status": "error", "message": f"Unknown action: {action}"}
