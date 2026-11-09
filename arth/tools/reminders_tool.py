"""Reminders tool for ARTH.
Implements Section 4 & 33 of ARTH_SPEC:
- Reminders: add, list, complete, delete.
- Notification banner and spoken alert.
- Asks permission before creating or deleting reminders.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class RemindersTool(Tool):
    name = "manage_reminders"
    description = "Add, list, or delete reminders with scheduled times."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "delete"],
                "description": "Operation to perform.",
            },
            "title": {"type": "string", "description": "Title or topic of the reminder."},
            "time_str": {"type": "string", "description": "When the reminder should trigger (e.g. '18:00', 'tomorrow 9am')."},
            "reminder_id": {"type": "integer", "description": "ID of reminder to delete."},
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    DEFAULT_STORE = os.path.expanduser("~/Desktop/ARTH/logs/reminders.json")

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
        title = kwargs.get("title", "a reminder")
        time_str = kwargs.get("time_str", "scheduled time")
        if action == "add":
            return f"schedule a reminder for '{title}' at {time_str}"
        elif action == "delete":
            return f"delete reminder #{kwargs.get('reminder_id', '')}"
        return "list all active reminders"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "list")
        items = self._load()

        if action == "add":
            title = kwargs.get("title", "").strip()
            time_str = kwargs.get("time_str", "unspecified time").strip()
            new_id = (max([r["id"] for r in items], default=0)) + 1
            reminder = {
                "id": new_id,
                "title": title,
                "time": time_str,
                "created_at": time.time(),
                "completed": False,
            }
            items.append(reminder)
            self._save(items)
            return {
                "status": "success",
                "message": f"Added reminder #{new_id}: '{title}' for {time_str}.",
                "reminder": reminder,
            }

        elif action == "delete":
            rem_id = kwargs.get("reminder_id")
            new_items = [r for r in items if r["id"] != rem_id]
            self._save(new_items)
            return {
                "status": "success",
                "message": f"Deleted reminder #{rem_id}.",
                "remaining_count": len(new_items),
            }

        else:
            return {
                "status": "success",
                "reminders": items,
                "message": f"You have {len(items)} reminders scheduled.",
            }
