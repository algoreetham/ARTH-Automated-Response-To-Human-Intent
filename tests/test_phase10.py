"""Tests for Phase 10 — Smart Proactive Behavior, Routines, and Ambient Controls.
Enforces Sections 13, 23, 24, 29, & 33 of ARTH_SPEC.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from arth.brain import OllamaManager
from arth.logger import ActivityLogger
from arth.permissions import PermissionEngine
from arth.routines import RoutineManager, RoutineTool
from arth.tools.registry_factory import get_default_registry
from arth.watcher import ProactiveWatcher, MusicControlTool


class TestRoutineEngine:
    """Test Section 13 Routines & Single Upfront Confirmation."""

    def test_default_starter_routines_exist(self, tmp_path):
        store = tmp_path / "routines.json"
        mgr = RoutineManager(store_path=str(store))
        routines = mgr.list_routines()
        ids = [r["id"] for r in routines]
        assert "study_mode" in ids
        assert "coding_mode" in ids
        assert "chill_mode" in ids
        assert "sleep_mode" in ids

    def test_sleep_mode_preserves_alarms(self, tmp_path):
        store = tmp_path / "routines.json"
        mgr = RoutineManager(store_path=str(store))
        sleep_r = mgr.get_routine("sleep_mode")
        assert sleep_r["keep_alarms"] is True
        assert any("alarm" in s.lower() for s in sleep_r["steps"])

    def test_describe_routine_reads_out_all_steps(self, tmp_path):
        store = tmp_path / "routines.json"
        mgr = RoutineManager(store_path=str(store))
        desc = mgr.describe_routine_execution("study_mode")
        assert "Study Mode" in desc
        assert "1." in desc
        assert "2." in desc

    def test_add_and_delete_custom_routine(self, tmp_path):
        store = tmp_path / "routines.json"
        mgr = RoutineManager(store_path=str(store))
        custom = mgr.add_routine("Workout Mode", ["Play gym playlist", "Set 30-min timer"])
        assert custom["name"] == "Workout Mode"
        assert len(custom["steps"]) == 2

        deleted = mgr.delete_routine("Workout Mode")
        assert deleted is True
        assert mgr.get_routine("Workout Mode") is None


class TestProactiveWatcher:
    """Test Sections 23, 24, & 29 Proactive Watcher, Not Now, and Care."""

    def test_battery_low_nudge(self, tmp_path):
        log_file = tmp_path / "test_proactive.jsonl"
        logger = ActivityLogger(log_file=str(log_file))
        watcher = ProactiveWatcher(logger=logger)

        day_time = datetime(2026, 11, 21, 14, 0, 0)
        nudge = watcher.check_system_and_nudge(battery_pct=12, current_time=day_time)
        assert nudge is not None
        assert "12%" in nudge
        assert "plugging in your charger" in nudge

    def test_storage_low_nudge(self, tmp_path):
        log_file = tmp_path / "test_proactive.jsonl"
        logger = ActivityLogger(log_file=str(log_file))
        watcher = ProactiveWatcher(logger=logger)

        day_time = datetime(2026, 11, 21, 14, 0, 0)
        nudge = watcher.check_system_and_nudge(storage_gb=6.5, current_time=day_time)
        assert nudge is not None
        assert "6.5 GB" in nudge

    def test_posture_break_nudge_after_2_hours(self, tmp_path):
        log_file = tmp_path / "test_proactive.jsonl"
        logger = ActivityLogger(log_file=str(log_file))
        watcher = ProactiveWatcher(logger=logger)

        day_time = datetime(2026, 11, 21, 14, 0, 0)
        nudge = watcher.check_system_and_nudge(work_duration_minutes=130, current_time=day_time)
        assert nudge is not None
        assert "two hours" in nudge
        assert "stretch" in nudge

    def test_not_now_silences_nudges_for_one_hour(self, tmp_path):
        log_file = tmp_path / "test_proactive.jsonl"
        logger = ActivityLogger(log_file=str(log_file))
        watcher = ProactiveWatcher(logger=logger)

        day_time = datetime(2026, 11, 21, 14, 0, 0)
        res = watcher.trigger_not_now(current_time=day_time)
        assert "stay quiet" in res
        assert "next hour" in res

        # 30 mins later -> still silenced
        half_hour_later = datetime(2026, 11, 21, 14, 30, 0)
        nudge = watcher.check_system_and_nudge(battery_pct=8, current_time=half_hour_later)
        assert nudge is None

    def test_quiet_hours_silence_nudges(self, tmp_path):
        log_file = tmp_path / "test_proactive.jsonl"
        logger = ActivityLogger(log_file=str(log_file))
        watcher = ProactiveWatcher(logger=logger)

        # 23:30 is in quiet hours (22:00 - 07:00)
        night_time = datetime(2026, 11, 21, 23, 30, 0)
        nudge = watcher.check_system_and_nudge(battery_pct=10, current_time=night_time)
        assert nudge is None


class TestMusicControls:
    """Test Section 33 Ambient Music Controls."""

    def test_music_actions(self):
        tool = MusicControlTool()
        res_play = tool.execute(action="play", genre_or_mood="synthwave")
        assert res_play["status"] == "success"
        assert "synthwave" in res_play["message"]

        res_pause = tool.execute(action="pause")
        assert res_pause["status"] == "success"
        assert "paused" in res_pause["message"]

        res_next = tool.execute(action="next")
        assert res_next["status"] == "success"
        assert "next track" in res_next["message"]


class TestPhase10BrainIntegration:
    """Test end-to-end integration with ARTH Brain."""

    def test_brain_routine_denied_on_no(self):
        brain = OllamaManager()
        registry = get_default_registry()
        # Boss says "No" to the routine upfront
        perm = PermissionEngine(prompt_callback=lambda p: False)

        resp = brain.process_turn("start study mode", registry, perm)
        assert "Action cancelled" in resp or "denied" in resp.lower()

    def test_brain_routine_executed_on_yes(self):
        brain = OllamaManager()
        registry = get_default_registry()
        # Boss approves upfront with "Yes"
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("start study mode", registry, perm)
        assert "Study Mode" in resp
        assert "Successfully executed all" in resp

    def test_brain_not_now_command(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("ARTH, not now", registry, perm)
        assert "stay quiet" in resp or "next hour" in resp

    def test_brain_music_command(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("play some lofi music", registry, perm)
        assert "Playing lofi music" in resp
