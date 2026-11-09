"""SQLite database schema and access for ARTH Memory and Habits.
Enforces Section 7 and 25 of ARTH_SPEC:
- Local SQLite database on laptop.
- Save explicit facts ONLY when Boss says 'remember this'.
- Habit tracking (Section 25).
- Never save moods, emotional conversations, or passwords.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "logs" / "arth_memory.db"


class MemoryDatabase:
    """Manages SQLite tables for explicit memories and observed habits."""

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_db()

    def _ensure_db(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Explicit memories
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE,
                        content TEXT,
                        category TEXT DEFAULT 'general',
                        created_at TEXT
                    )
                """)
                # Observed habits (Section 25)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS habits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        habit TEXT UNIQUE,
                        frequency INTEGER DEFAULT 1,
                        last_observed TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Warning: Could not initialize SQLite memory DB: {e}")

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
