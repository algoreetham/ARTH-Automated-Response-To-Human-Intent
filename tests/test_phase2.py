"""Automated test suite for ARTH Phase 2: GUI and Activity Log.
Verifies ActivityLogger recording, privacy redaction, search/filter, and GUI bridge async permission flow.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import ArthConfig
from arth.brain import OllamaManager
from arth.logger import ActivityLogger, LogEntry
from arth.gui.bridge import GUIBridge


class TestActivityLogger:
    def test_log_recording_and_retrieval(self, tmp_path):
        """Verify actions are correctly recorded to disk and retrieved."""
        log_file = tmp_path / "test_log.jsonl"
        logger = ActivityLogger(log_file=log_file, device_name="MacBook Pro")

        entry = logger.log(
            query="organize downloads",
            tool="organize_test_files",
            status="approved",
            reason="Boss approved moving files",
        )

        assert entry.tool == "organize_test_files"
        assert entry.status == "approved"

        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0]["query"] == "organize downloads"
        assert logs[0]["device"] == "MacBook Pro"

    def test_privacy_sanitization(self, tmp_path):
        """Verify sensitive passwords and OTPs are redacted per Section 14."""
        log_file = tmp_path / "test_log.jsonl"
        logger = ActivityLogger(log_file=log_file)

        logger.log(
            query="Enter password: supersecretpassword123 with OTP 849201",
            tool="vault_login",
            status="denied",
            reason="User cancelled password entry",
        )

        logs = logger.get_logs()
        logged_query = logs[0]["query"]

        assert "supersecretpassword123" not in logged_query
        assert "[REDACTED]" in logged_query
        assert "[CODE/OTP REDACTED]" in logged_query

    def test_search_and_filter(self, tmp_path):
        """Verify search query and status filtering in Activity Log."""
        log_file = tmp_path / "test_log.jsonl"
        logger = ActivityLogger(log_file=log_file)

        logger.log("move files", "organize_test_files", "approved", "Moved 10 files")
        logger.log("delete folder", "organize_test_files", "denied", "Boss refused deletion")
        logger.log("weather check", "weather_tool", "approved", "Checked weather for Bangalore")

        # 1. Filter by status
        approved = logger.get_logs(status="approved")
        assert len(approved) == 2

        denied = logger.get_logs(status="denied")
        assert len(denied) == 1
        assert denied[0]["query"] == "delete folder"

        # 2. Search by keyword
        weather_logs = logger.get_logs(query="weather")
        assert len(weather_logs) == 1
        assert weather_logs[0]["tool"] == "weather_tool"

    def test_audit_queries(self, tmp_path):
        """Verify 'what did you do today?' and 'why did you do that?' queries."""
        log_file = tmp_path / "test_log.jsonl"
        logger = ActivityLogger(log_file=log_file)

        logger.log("move files", "organize_test_files", "approved", "Moved 5 files")
        today_summary = logger.get_today_summary()
        assert "processed 1 actions" in today_summary

        reason = logger.get_last_action_reason()
        assert "I approved 'organize_test_files'" in reason


class TestGUIBridgeAndAcceptance:
    """Core acceptance test for Phase 2:
    'Done when: the same test works in the window and every action shows in the log.'
    """

    def test_gui_bridge_permission_denial_and_logging(self, tmp_path):
        """Simulate GUI user sending message, modal asking permission, user clicking Deny."""
        log_file = tmp_path / "gui_log.jsonl"
        logger = ActivityLogger(log_file=log_file)
        cfg = ArthConfig()
        brain = OllamaManager(cfg)
        bridge = GUIBridge(cfg, brain, logger=logger)

        # Mock pywebview window to intercept JS evaluate calls
        mock_window = MagicMock()
        bridge.set_window(mock_window)

        # Background thread to click "Deny" after modal opens
        def simulate_boss_click_deny():
            time.sleep(0.1)
            bridge.resolve_permission(False)

        thread = threading.Thread(target=simulate_boss_click_deny)
        thread.start()

        # Send command through bridge
        result = bridge.send_message("Please move 12 files from Downloads to Notes")
        thread.join()

        # 1. Verify JS modal was triggered
        assert mock_window.evaluate_js.called

        # 2. Verify reply confirms cancellation
        assert "Action cancelled" in result["reply"]

        # 3. Verify action is present in the activity log with status 'denied'
        logs = bridge.get_logs()
        assert len(logs) == 1
        assert logs[0]["status"] == "denied"
        assert logs[0]["tool"] == "organize_test_files"

    def test_gui_bridge_permission_approval_and_logging(self, tmp_path):
        """Simulate GUI user sending message, modal asking permission, user clicking Approve."""
        log_file = tmp_path / "gui_log.jsonl"
        logger = ActivityLogger(log_file=log_file)
        cfg = ArthConfig()
        brain = OllamaManager(cfg)
        bridge = GUIBridge(cfg, brain, logger=logger)

        mock_window = MagicMock()
        bridge.set_window(mock_window)

        def simulate_boss_click_approve():
            for _ in range(50):
                time.sleep(0.05)
                if bridge._is_waiting_for_permission:
                    bridge.resolve_permission(True)
                    break

        thread = threading.Thread(target=simulate_boss_click_approve)
        thread.start()

        result = bridge.send_message("Please move 12 files from Downloads to Notes")
        thread.join()

        # 1. Verify reply confirms execution
        assert "Done, Boss!" in result["reply"]

        # 2. Verify action is present in the activity log with status 'approved'
        logs = bridge.get_logs()
        assert len(logs) == 1
        assert logs[0]["status"] == "approved"
        assert logs[0]["tool"] == "organize_test_files"

    def test_gui_initial_state(self, tmp_path):
        """Verify initial state contains user info, to-dos, and system settings."""
        cfg = ArthConfig()
        brain = OllamaManager(cfg)
        logger = ActivityLogger(log_file=tmp_path / "init_log.jsonl")
        bridge = GUIBridge(cfg, brain, logger=logger)

        state = bridge.get_initial_state()
        assert state["user_name"] == "Boss"
        assert state["model"] == "gemma4:12b"
        assert len(state["todos"]) >= 1
