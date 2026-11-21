"""Tests for Phase 11 & Mark-XXXIX Capabilities:
1. Computer Settings & Hardware Control (Volume, Brightness, Dark Mode, Display Sleep, Screenshot).
2. Screen Vision & Active Context Perception.
3. YouTube Player & Video Launcher.
4. Emergency Protocol (Section 28: No password, 10s cancel window, spoken yes).
5. macOS LaunchAgent Auto-Start (Section 3).
6. Crash Recovery & Circuit Breaker (Section 20: 3 crashes in 5 minutes).
"""

from __future__ import annotations

import plistlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from arth.autostart import LaunchAgentManager
from arth.brain import OllamaManager
from arth.emergency import EmergencyProtocol
from arth.permissions import PermissionEngine
from arth.resilience import CrashRecoveryController
from arth.tools.registry_factory import get_default_registry
from arth.tools.system_settings_tool import SystemSettingsTool
from arth.tools.vision_tool import ScreenVisionTool
from arth.tools.youtube_tool import YouTubeTool


class TestComputerSettingsHardware:
    """Test macOS hardware settings controls inspired by Mark-XXXIX-OR."""

    def test_volume_controls(self):
        tool = SystemSettingsTool()
        res_up = tool.execute(setting="volume_up")
        assert res_up["status"] == "success"
        assert "Volume increased" in res_up["message"]

        res_down = tool.execute(setting="volume_down")
        assert res_down["status"] == "success"
        assert "Volume decreased" in res_down["message"]

        res_mute = tool.execute(setting="mute")
        assert res_mute["status"] == "success"
        assert "muted" in res_mute["message"]

        res_set = tool.execute(setting="set_volume", value=65)
        assert res_set["status"] == "success"
        assert "65%" in res_set["message"]

    def test_brightness_and_dark_mode(self):
        tool = SystemSettingsTool()
        res_bright = tool.execute(setting="brightness_up")
        assert res_bright["status"] == "success"
        assert "brightness increased" in res_bright["message"].lower()

        res_dark = tool.execute(setting="dark_mode")
        assert res_dark["status"] == "success"
        assert "appearance mode" in res_dark["message"].lower()

    def test_screenshot_action(self):
        tool = SystemSettingsTool()
        desc = tool.describe_action(setting="screenshot")
        assert "screenshot" in desc


class TestScreenVisionTool:
    """Test screen perception and frontmost window detection."""

    def test_analyze_screen(self):
        tool = ScreenVisionTool()
        res = tool.execute(save_snapshot=False)
        assert res["status"] == "success"
        assert "app_name" in res
        assert "Boss" in res["message"]


class TestYouTubeTool:
    """Test YouTube video launcher."""

    def test_play_youtube(self):
        tool = YouTubeTool()
        res = tool.execute(query="lofi hip hop radio")
        assert res["status"] == "success"
        assert "youtube.com/results" in res["url"]
        assert "lofi" in res["url"]
        assert "Playing 'lofi hip hop radio' on YouTube" in res["message"]


class TestEmergencyProtocol:
    """Test Section 28 Emergency Protocol."""

    def test_prepare_emergency_alert(self):
        ep = EmergencyProtocol()
        alert = ep.prepare_emergency_alert(latitude=12.9352, longitude=77.6245, battery_pct=42)
        assert "URGENT" in alert["subject"]
        assert "12.9352" in alert["body"]
        assert "42%" in alert["body"]
        assert alert["cancel_window_seconds"] == 10
        assert "Say 'yes' to dispatch" in alert["spoken_prompt"]

    def test_emergency_alert_dispatched_on_yes(self):
        ep = EmergencyProtocol()
        alert = ep.prepare_emergency_alert()
        res = ep.dispatch_alert(alert, confirmed_by_user=True)
        assert res["status"] == "dispatched"
        assert "Emergency alert successfully dispatched" in res["message"]

    def test_emergency_alert_cancelled_on_no(self):
        ep = EmergencyProtocol()
        alert = ep.prepare_emergency_alert()
        res = ep.dispatch_alert(alert, confirmed_by_user=False)
        assert res["status"] == "cancelled"
        assert "Emergency alert cancelled by Boss" in res["message"]


class TestLaunchAgentAutoStart:
    """Test Section 3 macOS LaunchAgent."""

    def test_generate_plist_content(self, tmp_path):
        plist_file = tmp_path / "com.arth.test.plist"
        mgr = LaunchAgentManager(target_plist=plist_file)
        data = mgr.generate_plist_content("/usr/bin/python3")
        assert data["Label"] == "com.arth.assistant"
        assert data["RunAtLoad"] is True
        assert "/usr/bin/python3" in data["ProgramArguments"]

    def test_install_and_uninstall_plist(self, tmp_path):
        plist_file = tmp_path / "com.arth.test.plist"
        mgr = LaunchAgentManager(target_plist=plist_file)
        assert not mgr.is_installed()

        res_in = mgr.install("/usr/bin/python3")
        assert res_in["status"] == "installed"
        assert mgr.is_installed()

        res_un = mgr.uninstall()
        assert res_un["status"] == "uninstalled"
        assert not mgr.is_installed()


class TestCrashRecoveryAndCircuitBreaker:
    """Test Section 20 Crash Recovery & Circuit Breaker."""

    def test_crash_recovery_plain_words(self, tmp_path):
        controller = CrashRecoveryController(max_crashes=3, window_seconds=300.0)
        can_restart, msg = controller.record_crash("IndexError: list index out of range")
        assert can_restart is True
        assert "Boss, I crashed but I'm back" in msg

    def test_circuit_breaker_halts_after_three_crashes(self, tmp_path):
        controller = CrashRecoveryController(max_crashes=3, window_seconds=300.0)
        controller.record_crash("Crash 1")
        controller.record_crash("Crash 2")
        can_restart, msg = controller.record_crash("Crash 3")

        assert can_restart is False
        assert "Halting automatic restarts" in msg
        assert "crashed 3 times" in msg


class TestPhase11BrainIntegration:
    """Test ARTH Brain execution of Mark-XXXIX capabilities and Section 28 emergency."""

    def test_brain_volume_command(self):
        brain = OllamaManager()
        reg = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("turn up the volume", reg, perm)
        assert "Volume increased" in resp

    def test_brain_mute_command(self):
        brain = OllamaManager()
        reg = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("mute audio", reg, perm)
        assert "audio muted" in resp.lower()

    def test_brain_screen_vision_command(self):
        brain = OllamaManager()
        reg = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("what's on my screen", reg, perm)
        assert "Boss, you are currently in" in resp

    def test_brain_youtube_command(self):
        brain = OllamaManager()
        reg = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("play interlinked on youtube", reg, perm)
        assert "Playing 'interlinked' on YouTube" in resp

    def test_brain_emergency_mode_approved(self):
        brain = OllamaManager()
        reg = get_default_registry()
        # Boss confirms emergency dispatch
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("ARTH, emergency", reg, perm)
        assert "Emergency alert successfully dispatched" in resp
