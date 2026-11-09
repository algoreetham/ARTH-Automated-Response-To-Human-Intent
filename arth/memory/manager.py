"""Memory and Habits Manager for ARTH.
Enforces Sections 7, 25, and 29 of ARTH_SPEC:
- Local SQLite database on laptop.
- Save something ONLY when Boss says 'remember this'.
- 'forget this' and 'what do you know about me?'.
- Notice and learn habits ('what habits have you noticed?', 'forget that habit').
- NEVER save moods or emotional conversations (Section 29) or passwords.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from arth.memory.db import MemoryDatabase


class MemoryManager:
    """Coordinates memory persistence and habit observation with strict privacy rules."""

    FORBIDDEN_KEYWORDS = [
        "mood",
        "sad",
        "crying",
        "depressed",
        "angry",
        "emotion",
        "password",
        "secret key",
        "otp",
        "pin",
    ]

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db = MemoryDatabase(db_path)

    def is_forbidden(self, text: str) -> bool:
        """Check if content contains emotional states, moods, or passwords."""
        lower = text.lower()
        for kw in self.FORBIDDEN_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                return True
        return False

    def remember(self, key: str, content: str, category: str = "general") -> Dict[str, Any]:
        """Save a fact to long-term memory. Triggered ONLY when Boss requests it."""
        if self.is_forbidden(content) or self.is_forbidden(key):
            return {
                "success": False,
                "message": "Boss, per privacy rules I never store emotional states, moods, or passwords to memory.",
            }

        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memories (key, content, category, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET content=excluded.content, created_at=excluded.created_at
                """, (key.strip(), content.strip(), category, now))
                conn.commit()
                return {
                    "success": True,
                    "message": f"Got it, Boss! I'll remember that: '{content.strip()}'.",
                }
        except Exception as e:
            return {"success": False, "message": f"Couldn't save memory: {e}"}

    def forget(self, key_or_content: str) -> Dict[str, Any]:
        """Delete a saved memory on command."""
        target = f"%{key_or_content.strip()}%"
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE key LIKE ? OR content LIKE ?", (target, target))
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    return {"success": True, "message": f"Consider it forgotten, Boss. Removed {deleted} record(s)."}
                return {"success": False, "message": f"Boss, I couldn't find anything matching '{key_or_content}' to forget."}
        except Exception as e:
            return {"success": False, "message": f"Error forgetting: {e}"}

    def what_do_you_know_about_me(self) -> str:
        """Answers: 'what do you know about me?' (Section 7)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, content FROM memories ORDER BY created_at DESC")
                rows = cursor.fetchall()
                if not rows:
                    return "Boss, you haven't asked me to remember anything about you yet."
                
                lines = ["Boss, here is everything you've asked me to remember:"]
                for k, v in rows:
                    lines.append(f"• {k}: {v}")
                return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving memories: {e}"

    def record_habit(self, habit_description: str) -> None:
        """Record an observed pattern/habit (Section 25)."""
        if self.is_forbidden(habit_description):
            return

        now = datetime.now(timezone.utc).isoformat()
        clean = habit_description.strip()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO habits (habit, frequency, last_observed)
                    VALUES (?, 1, ?)
                    ON CONFLICT(habit) DO UPDATE SET frequency = frequency + 1, last_observed = excluded.last_observed
                """, (clean, now))
                conn.commit()
        except Exception:
            pass

    def get_habits(self) -> str:
        """Answers: 'what habits have you noticed?' (Section 25)."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT habit, frequency FROM habits ORDER BY frequency DESC")
                rows = cursor.fetchall()
                if not rows:
                    return "Boss, I haven't noticed any recurring habits yet."

                lines = ["Boss, here are the habits I've noticed:"]
                for habit, freq in rows:
                    lines.append(f"• {habit} (observed {freq} times)")
                return "\n".join(lines)
        except Exception as e:
            return f"Error reading habits: {e}"

    def forget_habit(self, habit_query: str) -> str:
        """Forget an observed habit on command (Section 25)."""
        target = f"%{habit_query.strip()}%"
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM habits WHERE habit LIKE ?", (target,))
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    return f"Done, Boss. I've wiped that habit from my records."
                return f"Boss, I couldn't find any habit matching '{habit_query}'."
        except Exception as e:
            return f"Error forgetting habit: {e}"

    def get_context_for_prompt(self) -> str:
        """Return a compact memory summary to inject into the LLM system prompt."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, content FROM memories LIMIT 10")
                rows = cursor.fetchall()
                if not rows:
                    return ""
                return "Saved memories about Boss:\n" + "\n".join(f"- {k}: {v}" for k, v in rows)
        except Exception:
            return ""
