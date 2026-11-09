#!/usr/bin/env python3
"""Interactive/automated verification for Phase 5: Security.
Verifies all 3 acceptance criteria:
1. Someone else's voice is ignored (speaks once, then stays silent).
2. Risky test action needs Face check and Typed Password.
3. Lockdown freezes ARTH until unlocked.
"""

import sys
from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.logger import ActivityLogger
from arth.permissions import PermissionEngine
from arth.security.auth import SecurityManager
from arth.security.lockdown import LockdownController
from arth.tools.base import ToolRegistry
from arth.tools.risky_tool import RiskyTestActionTool


def main():
    print("=" * 65)
    print("🔒 ARTH PHASE 5: SECURITY VERIFICATION SUITE")
    print("=" * 65)

    sec = SecurityManager(vault_path="logs/test_security_vault.json")
    sec.enroll_voice_profile("boss_voice_sample")
    sec.set_password("BossSecurePass2026")
    sec.enroll_face("boss_local_face_vector_v1")

    lockdown = LockdownController(security_manager=sec)
    cfg = ArthConfig()
    logger = ActivityLogger(log_file="logs/test_security_log.jsonl")
    brain = OllamaManager(cfg, security_manager=sec, lockdown_controller=lockdown)

    registry = ToolRegistry()
    risky_tool = RiskyTestActionTool()
    registry.register(risky_tool)

    # 1. Voice Lock Acceptance
    print("\n--- 1. Testing Voice Lock (Section 12) ---")
    resp1 = brain.process_turn("Hello ARTH", registry, PermissionEngine(security_manager=sec), speaker_id="stranger")
    print(f"Unknown voice turn 1: '{resp1}'")
    assert resp1 == "Sorry, that's not Boss's voice."

    resp2 = brain.process_turn("ARTH can you hear me?", registry, PermissionEngine(security_manager=sec), speaker_id="stranger")
    print(f"Unknown voice turn 2: '{resp2}' (Expected: silent/empty)")
    assert resp2 == ""

    resp3 = brain.process_turn("Hello ARTH", registry, PermissionEngine(security_manager=sec), speaker_id="boss")
    print(f"Boss voice turn 3: '{resp3}'")
    assert "Boss" in resp3
    print("✅ Voice Lock Verified: Unrecognized speaker warned once, then ignored.")

    # 2. Risky Action Protection Acceptance
    print("\n--- 2. Testing Risky Action Multi-Factor (Section 12, 30) ---")
    perm = PermissionEngine(
        prompt_callback=lambda msg: True,  # Boss says 'yes'
        security_manager=sec,
    )

    # Attempt without password
    res_no_pw = brain.process_turn(
        "Please erase test-phone",
        registry,
        perm,
        speaker_id="boss",
        auth_credentials=None,
    )
    print(f"Risky action without password: '{res_no_pw}'")
    assert "password required" in res_no_pw.lower()

    # Attempt with wrong password
    res_wrong_pw = brain.process_turn(
        "Please erase test-phone",
        registry,
        perm,
        speaker_id="boss",
        auth_credentials=("WrongPassword123", "boss_local_face_vector_v1", "blink"),
    )
    print(f"Risky action with wrong password: '{res_wrong_pw}'")
    assert "blocked by security" in res_wrong_pw.lower()

    # Attempt with correct face + password
    res_success = brain.process_turn(
        "Please erase test-phone",
        registry,
        perm,
        speaker_id="boss",
        auth_credentials=("BossSecurePass2026", "boss_local_face_vector_v1", "blink"),
    )
    print(f"Risky action with Face + Password: '{res_success}'")
    assert "Done, Boss!" in res_success
    print("✅ Risky Action Verified: Spoken yes + Face Check + Typed Password enforced.")

    # 3. Lockdown Acceptance
    print("\n--- 3. Testing Lockdown Mode (Section 31) ---")
    lock_resp = brain.process_turn("ARTH, lockdown", registry, perm, speaker_id="boss")
    print(f"Trigger lockdown: '{lock_resp}'")
    assert "LOCKDOWN ACTIVATED" in lock_resp
    assert lockdown.is_frozen() is True

    # Try executing any command while frozen
    frozen_resp = brain.process_turn("Tell me a joke", registry, perm, speaker_id="boss")
    print(f"Command during lockdown: '{frozen_resp}'")
    assert "ARTH IS FROZEN IN LOCKDOWN" in frozen_resp

    # Unlock with valid Face + Password
    unlock_resp = brain.process_turn(
        "unlock",
        registry,
        perm,
        speaker_id="boss",
        auth_credentials=("BossSecurePass2026", "boss_local_face_vector_v1", "blink"),
    )
    print(f"Unlock command: '{unlock_resp}'")
    assert "unlocked successfully" in unlock_resp.lower()
    assert lockdown.is_frozen() is False
    print("✅ Lockdown Verified: Freezes all commands until Face + Password unlock.")

    print("\n" + "=" * 65)
    print("🎉 ALL PHASE 5 SECURITY ACCEPTANCE CRITERIA VERIFIED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
