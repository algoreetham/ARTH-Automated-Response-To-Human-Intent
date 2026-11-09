"""Automated test suite for ARTH Phase 4: Memory and Personality.
Verifies SQLite persistence across restarts, forgetting, habit tracking, honest pushback, and conversational cleanup.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.memory.manager import MemoryManager
from arth.personality import PersonalityEngine


class TestMemoryEngine:
    def test_memory_persistence_across_restarts(self, tmp_path):
        """Verify memory is saved in SQLite and persists across restarts (Section 7)."""
        db_file = tmp_path / "test_memory.db"

        # 1. First session: store fact
        mem1 = MemoryManager(db_path=db_file)
        res = mem1.remember(key="favourite_food", content="Boss loves Neer Dosa and Biryani")
        assert res["success"] is True

        # 2. Simulate restart: instantiate new manager instance from same SQLite DB
        mem2 = MemoryManager(db_path=db_file)
        known = mem2.what_do_you_know_about_me()
        assert "Neer Dosa" in known
        assert "Biryani" in known

    def test_memory_forget_command(self, tmp_path):
        """Verify memory can be forgotten on command (Section 7)."""
        db_file = tmp_path / "test_memory.db"
        mem = MemoryManager(db_path=db_file)

        mem.remember(key="coffee_pref", content="Boss drinks black coffee without sugar")
        assert "black coffee" in mem.what_do_you_know_about_me()

        forget_res = mem.forget("coffee")
        assert forget_res["success"] is True

        known_after = mem.what_do_you_know_about_me()
        assert "black coffee" not in known_after

    def test_refuse_emotional_and_password_storage(self, tmp_path):
        """Verify moods and emotional conversations are NEVER saved (Section 29)."""
        db_file = tmp_path / "test_memory.db"
        mem = MemoryManager(db_path=db_file)

        # Attempt to save emotional state
        res_mood = mem.remember("feeling", "I am feeling extremely sad and depressed today")
        assert res_mood["success"] is False
        assert "privacy rules" in res_mood["message"]

        # Attempt to save password
        res_pwd = mem.remember("password", "My bank password is Secret12345")
        assert res_pwd["success"] is False

    def test_habit_learning_and_forgetting(self, tmp_path):
        """Verify habit observation, recall, and forgetting (Section 25)."""
        db_file = tmp_path / "test_memory.db"
        mem = MemoryManager(db_path=db_file)

        # Observe habit twice
        mem.record_habit("Opens VS Code and studies at 8 PM")
        mem.record_habit("Opens VS Code and studies at 8 PM")

        habits = mem.get_habits()
        assert "Opens VS Code" in habits
        assert "observed 2 times" in habits

        # Forget habit
        mem.forget_habit("VS Code")
        assert "Opens VS Code" not in mem.get_habits()


class TestPersonalityEngine:
    def test_clean_spoken_response(self):
        """Verify markdown, bullets, emojis, and AI clichés are cleaned for speech (Section 8)."""
        persona = PersonalityEngine()

        raw_text = (
            "As an AI, great question! Here are your items: \n"
            "• Item 1 🚀\n"
            "• Item 2 💡\n"
            "• Item 3 🎯\n"
            "Hope this helps you out Boss!"
        )

        spoken = persona.clean_spoken_response(raw_text)
        assert "As an AI" not in spoken
        assert "great question" not in spoken
        assert "•" not in spoken
        assert "🚀" not in spoken

    def test_honest_pushback_on_dangerous_command(self):
        """Verify honest pushback against dangerous requests (Section 32)."""
        persona = PersonalityEngine()

        pushback = persona.check_honest_pushback("ARTH, delete everything right now")
        assert pushback is not None
        assert "sounds like a bad idea" in pushback

        safe_cmd = persona.check_honest_pushback("What is the weather in Bangalore?")
        assert safe_cmd is None

    def test_goodbye_humor(self):
        """Verify goodbye message includes joke and Boss sign-off (Section 32)."""
        persona = PersonalityEngine()
        goodbye = persona.get_goodbye()
        assert "Boss." in goodbye
        assert any(j in goodbye for j in ["binary", "bugs", "SQL", "Windows", "null"])
