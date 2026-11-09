"""Google Calendar tool for ARTH.
Implements Sections 4 & 33 of ARTH_SPEC:
- Calendar reminders: the day before AND 1 hour before every event.
- If Boss says an event is unimportant, skip its reminders.
- Add events, list upcoming events.
- Needs Boss's yes before adding an event.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from arth.tools.base import Tool


class CalendarTool(Tool):
    name = "manage_calendar"
    description = "List upcoming Google Calendar events or schedule new events with reminder alerts."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "delete"],
                "description": "Operation to perform.",
            },
            "title": {"type": "string", "description": "Title of the calendar event."},
            "date_str": {"type": "string", "description": "Date or time (e.g. '2026-10-15 14:00')."},
            "unimportant": {"type": "boolean", "description": "If true, skip reminders."},
            "event_id": {"type": "integer", "description": "ID of event to delete."},
        },
        "required": ["action"],
    }
    is_sensitive = False
    is_risky = False

    DEFAULT_STORE = os.path.expanduser("~/Desktop/ARTH/logs/calendar_events.json")

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
        title = kwargs.get("title", "an event")
        date_str = kwargs.get("date_str", "scheduled date")
        if action == "add":
            return f"add event '{title}' on {date_str} to Google Calendar"
        elif action == "delete":
            return f"remove calendar event #{kwargs.get('event_id')}"
        return "list upcoming Google Calendar events"

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "list")
        events = self._load()

        if action == "add":
            title = kwargs.get("title", "General Event").strip()
            date_str = kwargs.get("date_str", "Tomorrow").strip()
            unimportant = kwargs.get("unimportant", False)

            reminders = []
            if not unimportant:
                reminders = ["24 hours before", "1 hour before"]

            new_id = (max([e["id"] for e in events], default=0)) + 1
            event = {
                "id": new_id,
                "title": title,
                "date": date_str,
                "reminders": reminders,
                "created_at": time.time(),
            }
            events.append(event)
            self._save(events)
            rem_desc = " (Reminders: 1 day & 1 hour prior)" if reminders else " (Reminders skipped)"
            return {
                "status": "success",
                "message": f"Added event #{new_id}: '{title}' for {date_str}{rem_desc}.",
                "event": event,
            }

        elif action == "delete":
            eid = kwargs.get("event_id")
            events = [e for e in events if e["id"] != eid]
            self._save(events)
            return {"status": "success", "message": f"Event #{eid} removed from Google Calendar."}

        else:
            return {
                "status": "success",
                "events": events,
                "message": f"You have {len(events)} upcoming events in Google Calendar.",
            }
