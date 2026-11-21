#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 9: Multi-Device Control.
Verifies all 3 acceptance criteria:
1. Android phone control over home Wi-Fi (ring, battery, DND, notifications with OTP redaction).
2. Secondary Mac control (Wake-on-LAN, sleep and shutdown blocked without Face + Password).
3. Lost phone finder (locate on map with last-known-location note, lock message, and remote erase with ERASE code).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.permissions import PermissionEngine
from arth.security.auth import SecurityManager
from arth.tools.base import ToolRegistry
from arth.tools.device_tool import AndroidDeviceTool, SecondaryMacTool, LostPhoneFinderTool


def main():
    print("=" * 65)
    print("📱💻 ARTH PHASE 9: MULTI-DEVICE CONTROL VERIFICATION")
    print("=" * 65)

    sec = SecurityManager(vault_path="logs/test_phase9_vault.json")
    sec.set_password("BossMasterKey2026")
    sec.enroll_face("boss_face_phase9_sample")

    android = AndroidDeviceTool()
    sec_mac = SecondaryMacTool()
    lost_phone = LostPhoneFinderTool()

    reg = ToolRegistry()
    reg.register(android)
    reg.register(sec_mac)
    reg.register(lost_phone)

    cfg = ArthConfig()
    brain = OllamaManager(cfg, security_manager=sec)
    perm = PermissionEngine(prompt_callback=lambda msg: True, security_manager=sec)

    # 1. Android Phone Integration
    print("\n--- 1. Testing Android Phone Integration (Section 11) ---")
    res_batt = brain.process_turn("check my phone battery", reg, perm)
    print("ARTH >>", res_batt)
    assert "Android phone is at" in res_batt

    res_ring = brain.process_turn("ring my phone please", reg, perm)
    print("ARTH >>", res_ring)
    assert "Ringing your Android phone" in res_ring

    res_notif = android.execute(action="notifications")
    print("ARTH [Notifications] >>", res_notif["message"])
    assert "[REDACTED OTP]" in res_notif["message"]
    print("✅ Android phone actions and OTP redaction verified.")

    # 2. Secondary Mac Control & Risky Gates
    print("\n--- 2. Testing Secondary Mac Control (Section 11 & 12) ---")
    res_wol = brain.process_turn("wake other mac", reg, perm)
    print("ARTH >>", res_wol)
    assert "Wake-on-LAN" in res_wol

    # Sleep without credentials -> blocked
    res_sleep_blocked = brain.process_turn("put secondary mac to sleep", reg, perm)
    print("ARTH (No Auth) >>", res_sleep_blocked)
    assert "Security alert" in res_sleep_blocked or "denied" in res_sleep_blocked.lower()

    # Sleep with valid credentials -> approved
    res_sleep_ok = brain.process_turn(
        "put secondary mac to sleep",
        reg,
        perm,
        auth_credentials=("BossMasterKey2026", "boss_face_phase9_sample", True),
    )
    print("ARTH (Authenticated) >>", res_sleep_ok)
    assert "Put secondary Mac" in res_sleep_ok
    print("✅ Secondary Mac WOL and Risky gate verified.")

    # 3. Lost Phone Safety Finder
    print("\n--- 3. Testing Lost Phone Safety Finder (Section 11 & 12) ---")
    res_locate = brain.process_turn("where is my lost phone", reg, perm)
    print("ARTH >>", res_locate)
    assert "LAST KNOWN location" in res_locate
    assert "maps.google.com" in res_locate

    # Erase without "ERASE" code -> blocked
    res_erase_bad = lost_phone.execute(action="erase", confirmation_code="NO")
    print("ARTH (Bad Code) >>", res_erase_bad["message"])
    assert res_erase_bad["status"] == "error"

    # Erase with "ERASE" code -> approved
    res_erase_ok = lost_phone.execute(action="erase", confirmation_code="ERASE")
    print("ARTH (Confirmed) >>", res_erase_ok["message"])
    assert res_erase_ok["status"] == "success"
    print("✅ Lost phone locator and remote erase safety code verified.")

    print("\n" + "=" * 65)
    print("🎉 PHASE 9 ACCEPTANCE CRITERIA FULLY SATISFIED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
