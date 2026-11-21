#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 10: Routines & Smart Behavior.
Verifies all 3 acceptance criteria:
1. ARTH executes Starter Routines (Study, Coding, Chill, Sleep) with single upfront confirmation.
2. Sleep mode preserves morning alarms and reminders.
3. Proactive system watcher delivers low-battery/storage alerts and honors 1-hour 'Not Now'.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.permissions import PermissionEngine
from arth.routines import RoutineManager, RoutineTool
from arth.tools.base import ToolRegistry
from arth.watcher import ProactiveWatcher, MusicControlTool


def main():
    print("=" * 65)
    print("🧘🎵 ARTH PHASE 10: ROUTINES & SMART BEHAVIOR VERIFICATION")
    print("=" * 65)

    mgr = RoutineManager(store_path="logs/test_phase10_routines.json")
    routine_tool = RoutineTool(manager=mgr)
    music_tool = MusicControlTool()

    reg = ToolRegistry()
    reg.register(routine_tool)
    reg.register(music_tool)

    cfg = ArthConfig()
    brain = OllamaManager(cfg)

    # 1. Starter Routines & Upfront Confirmation
    print("\n--- 1. Testing Starter Routines & Upfront Confirmation (Section 13) ---")
    # Denied upfront on "No"
    perm_deny = PermissionEngine(prompt_callback=lambda msg: False)
    res_deny = brain.process_turn("start study mode", reg, perm_deny)
    print("ARTH (Denied) >>", res_deny)
    assert "cancelled" in res_deny.lower()

    # Approved upfront on "Yes"
    perm_ok = PermissionEngine(prompt_callback=lambda msg: True)
    res_ok = brain.process_turn("start study mode", reg, perm_ok)
    print("ARTH (Approved) >>", res_ok)
    assert "Study Mode" in res_ok
    assert "Successfully executed all" in res_ok
    print("✅ Routines upfront single confirmation verified.")

    # 2. Sleep Mode preserves morning alarms
    print("\n--- 2. Testing Sleep Mode Alarm Preservation (Section 13) ---")
    sleep_r = mgr.get_routine("sleep_mode")
    assert sleep_r["keep_alarms"] is True
    print(f"Sleep mode steps: {sleep_r['steps']}")
    print("✅ Sleep mode preserves alarms.")

    # 3. Proactive System Watcher & 1-Hour Silence
    print("\n--- 3. Testing Proactive Watcher & 'Not Now' (Section 23 & 24) ---")
    watcher = brain.watcher
    day_time = datetime(2026, 11, 21, 15, 0, 0)
    batt_alert = watcher.check_system_and_nudge(battery_pct=11, current_time=day_time)
    print("ARTH (Proactive Alert) >>", batt_alert)
    assert "11%" in batt_alert

    # User says "not now"
    silence_resp = brain.process_turn("ARTH, not now", reg, perm_ok)
    print("ARTH ('Not Now') >>", silence_resp)
    assert "stay quiet" in silence_resp

    # Verified silenced
    suppressed_alert = watcher.check_system_and_nudge(battery_pct=9, current_time=datetime(2026, 11, 21, 15, 20, 0))
    assert suppressed_alert is None
    print("✅ Proactive watcher and 1-hour quiet cooldown verified.")

    # 4. Ambient Music Control
    print("\n--- 4. Testing Ambient Music Controls (Section 33) ---")
    music_res = brain.process_turn("play some synthwave music", reg, perm_ok)
    print("ARTH (Music) >>", music_res)
    assert "synthwave" in music_res.lower()
    print("✅ Ambient music playback verified.")

    print("\n" + "=" * 65)
    print("🎉 PHASE 10 ACCEPTANCE CRITERIA FULLY SATISFIED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
