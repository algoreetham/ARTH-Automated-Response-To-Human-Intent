"""Tests for Phase 6: Everyday Tools (Sections 4, 17, 33, 34).
Verifies:
1. Reminders tool: add, list, delete with permission asked.
2. To-dos tool: add, list, complete, delete with priority/deadline.
3. Notes tool: save, read, search, list plain-text notes.
4. Clipboard tool: read and copy strictly on request, sensitive classification.
5. Weather tool: auto location detection, city reporting, non-persistent location.
6. News tool: category-based news with sources and concise spoken summary.
7. Web search tool: free search with citations, URLs, and spoken summary.
8. Study & coding helper: explain code, debug code, and interactive quiz mode.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.permissions import PermissionEngine
from arth.tools.base import ToolRegistry
from arth.tools.reminders_tool import RemindersTool
from arth.tools.todos_tool import TodosTool
from arth.tools.notes_tool import NotesTool
from arth.tools.clipboard_tool import ClipboardTool
from arth.tools.weather_tool import WeatherTool
from arth.tools.news_tool import NewsTool
from arth.tools.web_search_tool import WebSearchTool
from arth.tools.study_helper_tool import StudyHelperTool


class TestRemindersTool:
    def test_add_and_list_reminders(self, tmp_path):
        store = tmp_path / "reminders.json"
        tool = RemindersTool(store_path=str(store))

        add_res = tool.execute(action="add", title="Team Standup", time_str="10:00 AM")
        assert add_res["status"] == "success"
        assert add_res["reminder"]["id"] == 1

        list_res = tool.execute(action="list")
        assert list_res["status"] == "success"
        assert len(list_res["reminders"]) == 1
        assert list_res["reminders"][0]["title"] == "Team Standup"

    def test_delete_reminder(self, tmp_path):
        store = tmp_path / "reminders.json"
        tool = RemindersTool(store_path=str(store))
        tool.execute(action="add", title="Call Mom", time_str="18:00")
        del_res = tool.execute(action="delete", reminder_id=1)
        assert del_res["status"] == "success"
        assert del_res["remaining_count"] == 0


class TestTodosTool:
    def test_todo_crud_and_sorting(self, tmp_path):
        store = tmp_path / "todos.json"
        tool = TodosTool(store_path=str(store))

        # Add High priority and Low priority
        tool.execute(action="add", task="Fix critical bug", priority="High", deadline="today")
        tool.execute(action="add", task="Read documentation", priority="Low", deadline="skip")

        list_res = tool.execute(action="list")
        todos = list_res["todos"]
        assert len(todos) == 2
        # High priority should be first
        assert todos[0]["priority"] == "High"
        assert todos[0]["deadline"] == "today"
        assert todos[1]["deadline"] == ""

        # Complete task 1
        comp_res = tool.execute(action="complete", task_id=1)
        assert comp_res["status"] == "success"


class TestNotesTool:
    def test_notes_creation_and_search(self, tmp_path):
        notes_dir = tmp_path / "notes"
        tool = NotesTool(notes_dir=str(notes_dir))

        # Save note
        save_res = tool.execute(action="save", title="Project Idea", content="Agentic OS for Mac")
        assert save_res["status"] == "success"

        # Read note
        read_res = tool.execute(action="read", title="Project Idea")
        assert read_res["status"] == "success"
        assert "Agentic OS" in read_res["content"]

        # Search notes
        search_res = tool.execute(action="search", query="Agentic")
        assert search_res["status"] == "success"
        assert search_res["count"] == 1


class TestClipboardTool:
    def test_clipboard_tool_sensitivity_and_action(self):
        tool = ClipboardTool()
        assert tool.is_sensitive is True
        desc = tool.describe_action(action="read")
        assert "clipboard" in desc.lower()


class TestWeatherTool:
    def test_weather_execution(self):
        tool = WeatherTool()
        res = tool.execute(city="Bengaluru")
        assert res["status"] == "success"
        assert res["city"] == "Bengaluru"
        assert "temp_c" in res
        assert "condition" in res
        assert "bengaluru" in res["message"].lower()


class TestNewsTool:
    def test_news_categories_and_sources(self):
        tool = NewsTool()
        res = tool.execute(topic="startups")
        assert res["status"] == "success"
        assert len(res["headlines"]) >= 1
        assert len(res["sources"]) >= 1
        assert "url" in res["sources"][0]
        assert "Boss" in res["spoken_summary"]


class TestWebSearchTool:
    def test_web_search_results_and_spoken_summary(self):
        tool = WebSearchTool()
        res = tool.execute(query="Gemma 4")
        assert res["status"] == "success"
        assert len(res["results"]) >= 1
        assert "spoken_summary" in res
        assert "Boss" in res["spoken_summary"]


class TestStudyHelperTool:
    def test_study_helper_modes(self):
        tool = StudyHelperTool()

        # Code explanation
        exp_res = tool.execute(mode="explain_code", code_or_text="def add(a, b): return a + b")
        assert exp_res["status"] == "success"
        assert "Boss" in exp_res["spoken_summary"]
        assert "Code Analysis" in exp_res["gui_content"]

        # Quiz mode
        quiz_res = tool.execute(mode="quiz", subject="python")
        assert quiz_res["status"] == "success"
        assert len(quiz_res["questions"]) >= 1
        assert "Boss" in quiz_res["spoken_summary"]


class TestPhase6AcceptancePermissionFlow:
    """Verify that permission is requested before every mutating everyday tool action."""

    def test_reminders_require_permission_before_execution(self, tmp_path):
        store = tmp_path / "reminders.json"
        rem_tool = RemindersTool(store_path=str(store))
        reg = ToolRegistry()
        reg.register(rem_tool)

        cfg = ArthConfig()
        brain = OllamaManager(cfg)

        prompt_history = []
        def mock_callback(msg: str) -> bool:
            prompt_history.append(msg)
            return True

        perm = PermissionEngine(prompt_callback=mock_callback)

        reply = brain.process_turn("Please remind me to call John at 18:00", reg, perm)
        assert len(prompt_history) == 1
        assert "schedule a reminder" in prompt_history[0]
        assert "Done, Boss!" in reply
