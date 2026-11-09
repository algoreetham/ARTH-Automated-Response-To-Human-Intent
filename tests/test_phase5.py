"""Tests for Phase 5: Security (Sections 12, 30, 31).
Verifies:
1. Voice lock: someone else's voice is ignored (speaks once 'Sorry, that's not Boss's voice', then stays quiet).
2. Typed password: scrypt salted hash with 5-minute lockout after 3 consecutive wrong attempts.
3. Face check & anti-spoofing challenge (local offline, delete face data command).
4. Risky action authorization: requires spoken 'yes' + Face Check + Typed Password.
5. Lockdown: "ARTH, lockdown" immediately freezes ARTH and locks display until unlocked with Face + Password.
"""

import os
import time
import pytest
from unittest.mock import MagicMock, patch

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.logger import ActivityLogger
from arth.permissions import PermissionEngine
from arth.security.auth import SecurityManager
from arth.security.lockdown import LockdownController
from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool
from arth.tools.risky_tool import RiskyTestActionTool


class TestVoiceLock:
    """Test voice lock obeying ONLY Boss."""

    def test_unrecognized_voice_warning_and_subsequent_silence(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.enroll_voice_profile("boss_sample_voice_v1")

        # Boss speaks -> allowed
        ok, warn = sec.verify_speaker("boss")
        assert ok is True
        assert warn is None

        # Unknown speaker 1st time -> rejected with exact message
        ok, warn = sec.verify_speaker("stranger")
        assert ok is False
        assert warn == "Sorry, that's not Boss's voice."

        # Unknown speaker 2nd time -> rejected and completely silent
        ok, warn = sec.verify_speaker("stranger")
        assert ok is False
        assert warn is None

        # Unknown speaker 3rd time -> still silent
        ok, warn = sec.verify_speaker("stranger")
        assert ok is False
        assert warn is None

        # Boss speaks again -> allowed and resets warning flag
        ok, warn = sec.verify_speaker("boss")
        assert ok is True
        assert warn is None


class TestPasswordAndLockout:
    """Test salted password and 5-minute lockout after 3 failed attempts."""

    def test_password_enrollment_and_verification(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))

        assert sec.set_password("MySuperSecret123") is True
        assert sec.has_password_enrolled() is True

        # Correct password
        ok, msg = sec.verify_password("MySuperSecret123")
        assert ok is True
        assert "verified" in msg.lower()

    def test_lockout_after_three_failed_attempts(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.set_password("CorrectPassword")

        # Attempt 1
        ok, msg = sec.verify_password("Wrong1")
        assert ok is False
        assert "2 attempts remaining" in msg

        # Attempt 2
        ok, msg = sec.verify_password("Wrong2")
        assert ok is False
        assert "1 attempts remaining" in msg

        # Attempt 3 -> Locked out
        ok, msg = sec.verify_password("Wrong3")
        assert ok is False
        assert "Account locked for 5 minutes" in msg

        # Subsequent attempts are instantly blocked by lockout
        is_locked, rem = sec.is_locked_out()
        assert is_locked is True
        assert rem > 0

        ok, msg = sec.verify_password("CorrectPassword")
        assert ok is False
        assert "Too many failed attempts" in msg


class TestFaceCheckAndAntiSpoofing:
    """Test local offline face recognition and anti-spoofing challenge."""

    def test_face_enrollment_and_verification_with_anti_spoof(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))

        assert sec.enroll_face("boss_face_embedding") is True
        assert sec.has_face_enrolled() is True

        # Challenge prompt
        challenge = sec.request_anti_spoof_challenge()
        assert "blink" in challenge.lower() or "turn your head" in challenge.lower()

        # Failed anti-spoof (no blink or head turn)
        ok, msg = sec.verify_face("boss_face_embedding", anti_spoof_response="static_photo")
        assert ok is False
        assert "anti-spoof check failed" in msg.lower()

        # Successful face + anti-spoof
        ok, msg = sec.verify_face("boss_face_embedding", anti_spoof_response="blink")
        assert ok is True

    def test_delete_my_face_data_command(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.enroll_face("boss_face_embedding")

        reply = sec.delete_face_data()
        assert "erased" in reply.lower()
        assert sec.has_face_enrolled() is False


class TestRiskyActionProtection:
    """Test that risky actions strictly require spoken yes + Face Check + Typed Password."""

    def test_risky_action_blocked_without_password_and_face(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.set_password("BossPass123")
        sec.enroll_face("boss_face")

        perm = PermissionEngine(
            prompt_callback=lambda msg: True,  # Spoken 'yes'
            security_manager=sec,
        )

        risky_tool = RiskyTestActionTool()

        # Permission granted by voice, but no password provided -> BLOCKED
        approved = perm.check_permission(

            action_description="permanently erase all contents from phone",
            tool=risky_tool,
            auth_credentials=None,
        )
        assert approved is False
        assert "password required" in perm.last_reason.lower()

    def test_risky_action_blocked_with_wrong_password(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.set_password("BossPass123")
        sec.enroll_face("boss_face")

        perm = PermissionEngine(
            prompt_callback=lambda msg: True,  # Spoken 'yes'
            security_manager=sec,
        )

        risky_tool = RiskyTestActionTool()

        # Wrong password supplied
        approved = perm.check_permission(

            action_description="permanently erase all contents from phone",
            tool=risky_tool,
            auth_credentials=("WrongPassword", "boss_face", "blink"),
        )
        assert approved is False
        assert "blocked by security" in perm.last_reason.lower()

    def test_risky_action_approved_with_valid_face_and_password(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.set_password("BossPass123")
        sec.enroll_face("boss_face")

        perm = PermissionEngine(
            prompt_callback=lambda msg: True,  # Spoken 'yes'
            security_manager=sec,
        )

        risky_tool = RiskyTestActionTool()

        approved = perm.check_permission(

            action_description="permanently erase all contents from phone",
            tool=risky_tool,
            auth_credentials=("BossPass123", "boss_face", "blink"),
        )
        assert approved is True
        assert perm.last_reason == "Approved."


class TestLockdownController:
    """Test 'ARTH, lockdown' freezes ARTH until Face + Password unlock."""

    def test_lockdown_freezes_and_blocks_all_commands(self, tmp_path):
        vault_path = tmp_path / "sec_vault.json"
        sec = SecurityManager(vault_path=str(vault_path))
        sec.set_password("LockdownPassword")
        sec.enroll_face("boss_face")

        lockdown = LockdownController(security_manager=sec)
        cfg = ArthConfig()
        brain = OllamaManager(cfg, security_manager=sec, lockdown_controller=lockdown)
        registry = ToolRegistry()
        perm = PermissionEngine(security_manager=sec)

        # Trigger lockdown
        msg = brain.process_turn("ARTH, lockdown", registry, perm)
        assert "LOCKDOWN ACTIVATED" in msg
        assert lockdown.is_frozen() is True

        # Any command during lockdown is rejected
        blocked_resp = brain.process_turn("What time is it?", registry, perm)
        assert "ARTH IS FROZEN IN LOCKDOWN" in blocked_resp

        # Wrong credentials fail to unlock
        fail_unlock = brain.process_turn(
            "unlock",
            registry,
            perm,
            auth_credentials=("WrongPass", "boss_face", "blink"),
        )
        assert "rejected" in fail_unlock.lower()
        assert lockdown.is_frozen() is True

        # Valid credentials successfully unlock ARTH
        success_unlock = brain.process_turn(
            "unlock",
            registry,
            perm,
            auth_credentials=("LockdownPassword", "boss_face", "blink"),
        )
        assert "unlocked successfully" in success_unlock.lower()
        assert lockdown.is_frozen() is False

        # Regular commands work again
        normal_resp = brain.process_turn("Hello ARTH", registry, perm)
        assert "Boss" in normal_resp
