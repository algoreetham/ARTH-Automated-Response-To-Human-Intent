"""Automated test suite for ARTH Phase 1: Brain and Permissions.
Verifies tool calling, human-in-the-loop permission enforcement, and multi-request sequencing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import ArthConfig
from arth.brain import OllamaManager
from arth.permissions import PermissionEngine
from arth.multi_request import MultiRequestHandler
from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool


class TestToolSystem:
    def test_tool_registration_and_ollama_schema(self):
        """Verify tool schema generation adheres to Ollama function calling format."""
        registry = ToolRegistry()
        tool = TestActionTool()
        registry.register(tool)

        assert registry.get("organize_test_files") == tool
        schemas = registry.get_ollama_tools_schema()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "organize_test_files"
        assert "source_folder" in schemas[0]["function"]["parameters"]["properties"]


class TestPermissionEngine:
    def test_permission_granted_on_yes(self):
        """Verify action proceeds when Boss approves."""
        engine = PermissionEngine(prompt_callback=lambda prompt: True)
        approved = engine.check_permission("move 5 files from Downloads to Notes")
        assert approved is True

    def test_permission_refused_on_no(self):
        """Verify action is blocked immediately when Boss says no."""
        engine = PermissionEngine(prompt_callback=lambda prompt: False)
        approved = engine.check_permission("move 5 files from Downloads to Notes")
        assert approved is False

    def test_sensitive_document_detection(self):
        """Verify sensitive keywords are detected and flagged."""
        prompt_received = []

        def mock_prompt(msg: str) -> bool:
            prompt_received.append(msg)
            return True

        engine = PermissionEngine(prompt_callback=mock_prompt)
        engine.check_permission("read confidential salary and secret password sheet")

        assert len(prompt_received) == 1
        assert "[SENSITIVE/SECRET DOCUMENT]" in prompt_received[0]


class TestMultiRequest:
    def test_split_compound_utterance(self):
        """Verify compound requests are separated into distinct actions."""
        handler = MultiRequestHandler()
        requests = handler.split_requests("organize test files and then check the weather")
        assert len(requests) == 2
        assert "organize test files" in requests[0]
        assert "check the weather" in requests[1]

    def test_order_requests_by_choice(self):
        """Verify Boss's chosen order determines execution sequence."""
        # User selects option 2 first
        handler = MultiRequestHandler(prompt_callback=lambda msg: "2")
        requests = ["organize test files", "check the weather"]
        ordered = handler.order_requests(requests)

        assert ordered[0] == "check the weather"
        assert ordered[1] == "organize test files"


class TestPhase1Acceptance:
    """Core acceptance test for Phase 1:
    'Done when: I chat in the terminal, ARTH picks a fake test tool, asks permission, and does nothing on "no".'
    """

    def test_arth_picks_test_tool_and_does_nothing_on_no(self):
        """Simulate terminal chat where ARTH picks tool, asks permission, and cancels on 'no'."""
        cfg = ArthConfig()
        brain = OllamaManager(cfg)

        registry = ToolRegistry()
        test_tool = TestActionTool()
        test_tool.execute = MagicMock(return_value={"status": "success"})
        registry.register(test_tool)

        prompt_messages = []

        def mock_permission_prompt(msg: str) -> bool:
            prompt_messages.append(msg)
            return False  # Boss says "no"

        engine = PermissionEngine(prompt_callback=mock_permission_prompt)

        response = brain.process_turn(
            user_input="Boss wants you to move 12 files from Downloads to Notes",
            tool_registry=registry,
            permission_engine=engine,
        )

        # 1. Verify ARTH asked permission with exact details
        assert len(prompt_messages) == 1
        assert "Boss, I'm about to move 12 files from Downloads to Notes" in prompt_messages[0]

        # 2. Verify tool execute was NEVER called
        test_tool.execute.assert_not_called()

        # 3. Verify response confirms cancellation
        assert "Action cancelled" in response

    def test_arth_picks_test_tool_and_executes_on_yes(self):
        """Simulate terminal chat where Boss approves and action executes."""
        cfg = ArthConfig()
        brain = OllamaManager(cfg)

        registry = ToolRegistry()
        test_tool = TestActionTool()
        registry.register(test_tool)

        prompt_messages = []

        def mock_permission_prompt(msg: str) -> bool:
            prompt_messages.append(msg)
            return True  # Boss says "yes"

        engine = PermissionEngine(prompt_callback=mock_permission_prompt)

        response = brain.process_turn(
            user_input="Please move 12 files from Downloads to Notes",
            tool_registry=registry,
            permission_engine=engine,
        )

        assert len(prompt_messages) == 1
        assert "move 12 files from Downloads to Notes" in prompt_messages[0]
        assert "Done, Boss!" in response
        assert "Successfully moved 12 files" in response
