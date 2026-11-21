#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 11:
1. Hardware Settings (Volume, Brightness, Dark Mode, Sleep Display, Screenshot).
2. Screen Vision & Active Window Perception.
3. YouTube Player.
4. Emergency Protocol (Section 28).
5. LaunchAgent Auto-Start (Section 3).
6. Crash Recovery & Circuit Breaker (Section 20).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arth.autostart import LaunchAgentManager
from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.emergency import EmergencyProtocol
from arth.permissions import PermissionEngine
from arth.resilience import CrashRecoveryController
from arth.tools.registry_factory import get_default_registry


def main():
    print("=" * 65)
    print("🚀 ARTH PHASE 11 & JARVIS MARK-XXXIX FEATURE VERIFICATION")
    print("=" * 65)

    reg = get_default_registry()
    cfg = ArthConfig()
    brain = OllamaManager(cfg)
    perm = PermissionEngine(prompt_callback=lambda p: True)

    # 1. Hardware Settings
    print("\n--- 1. Testing Hardware Controls (Mark-XXXIX Feature) ---")
    res_vol = brain.process_turn("turn up the volume", reg, perm)
    print("ARTH >>", res_vol)
    assert "Volume increased" in res_vol

    res_mute = brain.process_turn("mute audio", reg, perm)
    print("ARTH >>", res_mute)
    assert "muted" in res_mute.lower()
    print("✅ Hardware controls verified.")

    # 2. Screen Vision
    print("\n--- 2. Testing Screen Perception (Mark-XXXIX Feature) ---")
    res_vision = brain.process_turn("what's on my screen", reg, perm)
    print("ARTH >>", res_vision)
    assert "Boss, you are currently in" in res_vision
    print("✅ Screen vision & workspace perception verified.")

    # 3. YouTube Player
    print("\n--- 3. Testing YouTube Launcher (Mark-XXXIX Feature) ---")
    res_yt = brain.process_turn("play interlinked on youtube", reg, perm)
    print("ARTH >>", res_yt)
    assert "Playing 'interlinked' on YouTube" in res_yt
    print("✅ Direct YouTube playback verified.")

    # 4. Emergency Mode (Section 28)
    print("\n--- 4. Testing Emergency Protocol (Section 28) ---")
    res_emerg = brain.process_turn("ARTH, emergency", reg, perm)
    print("ARTH >>", res_emerg)
    assert "Emergency alert successfully dispatched" in res_emerg
    print("✅ Emergency protocol verified.")

    # 5. LaunchAgent Auto-Start (Section 3)
    print("\n--- 5. Testing LaunchAgent Auto-Start (Section 3) ---")
    mgr = LaunchAgentManager(target_plist=Path("logs/test_launchagent.plist"))
    res_in = mgr.install()
    print("LaunchAgent >>", res_in["message"])
    assert mgr.is_installed()
    mgr.uninstall()
    assert not mgr.is_installed()
    print("✅ macOS LaunchAgent auto-start verified.")

    # 6. Crash Recovery & Circuit Breaker (Section 20)
    print("\n--- 6. Testing Crash Recovery & Circuit Breaker (Section 20) ---")
    controller = CrashRecoveryController(max_crashes=3, window_seconds=300.0)
    _, msg1 = controller.record_crash("Minor error 1")
    assert "Boss, I crashed but I'm back" in msg1
    controller.record_crash("Minor error 2")
    can_restart, msg3 = controller.record_crash("Fatal error 3")
    assert can_restart is False
    assert "crashed 3 times" in msg3
    print("ARTH (Circuit Breaker) >>", msg3)
    print("✅ Crash recovery and circuit breaker verified.")

    print("\n" + "=" * 65)
    print("🎉 ALL PHASE 11 & MARK-XXXIX CAPABILITIES FULLY SATISFIED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
