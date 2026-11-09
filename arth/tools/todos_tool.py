"""To-dos tool for ARTH.
Implements Section 4 & 33 of ARTH_SPEC:
- To-dos: when I add one, ask me for priority and deadline. If I say "skip", save it without them.
- Show tasks sorted by priority and deadline.
- Mark complete, list, delete tasks.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class TodosTool(Tool):
    name = "manage_todos"
    description = "Add, view, complete, or delete to-do tasks with priorities and deadlines."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "complete", "delete"],
                "description": "Operation to perform.",
            },
            "task": {"type": "string", "description": "The task content."},
            "priority": {"type": "string", "enum": ["High", "Medium", "Low", "None"], "description": "Task priority."},
            "deadline": {"type": "string", "description": "Task due date/time, or 'skip'."},
            "task_id": {"type": "integer", "description": "ID of task to complete or delete."},
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    DEFAULT_STORE = os.path.expanduser("~/Desktop/ARTH/logs/todos.json")

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = store_path or self.DEFAULT_STORE
        self._ensure_store()

    def _ensure_store(self) -> None:
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        if not os.path.exists(self.store_path):
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, items: List[Dict[str, Any]]) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def describe_action(self, **kwargs) -> str:
        action = kwargs.get("action", "list")
        task = kwargs.get("task", "a task")
        if action == "add":
            return f"add to-do task: '{task}'"
        elif action == "complete":
            return f"mark task #{kwargs.get('task_id')} as completed"
        elif action == "delete":
            return f"delete to-do task #{kwargs.get('task_id')}"
        return "list all to-dos"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "list")
        items = self._load()

        if action == "add":
            task_str = kwargs.get("task", "").strip()
            priority = kwargs.get("priority", "Medium")
            if priority and priority.lower() == "skip":
                priority = "None"
            deadline = kwargs.get("deadline", "")
            if deadline and deadline.lower() == "skip":
                deadline = ""

            new_id = (max([t["id"] for t in items], default=0)) + 1
            todo = {
                "id": new_id,
                "task": task_str,
                "priority": priority,
                "deadline": deadline,
                "completed": False,
                "created_at": time.time(),
            }
            items.append(todo)
            self._save(items)
            return {
                "status": "success",
                "message": f"Added task #{new_id}: '{task_str}' [Priority: {priority}, Deadline: {deadline or 'None'}].",
                "todo": todo,
            }

        elif action == "complete":
            tid = kwargs.get("task_id")
            for t in items:
                if t["id"] == tid:
                    t["completed"] = True
            self._save(items)
            return {"status": "success", "message": f"Task #{tid} marked complete."}

        elif action == "delete":
            tid = kwargs.get("task_id")
            items = [t for t in items if t["id"] != tid]
            self._save(items)
            return {"status": "success", "message": f"Task #{tid} deleted."}

        else:
            # Sort by priority order (High, Medium, Low, None) then created_at
            priority_rank = {"High": 1, "Medium": 2, "Low": 3, "None": 4}
            sorted_items = sorted(
                items,
                key=lambda x: (
                    1 if x.get("completed") else 0,
                    priority_rank.get(x.get("priority", "None"), 4),
                ),
            )
            return {
                "status": "success",
                "todos": sorted_items,
                "message": f"You have {len(sorted_items)} tasks.",
            }
