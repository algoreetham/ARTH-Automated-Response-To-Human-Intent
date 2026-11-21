"""Tests for Phase 9 — Multi-Device Control (Android, Secondary Mac, Lost Phone).
Enforces Sections 11, 12, & 14 of ARTH_SPEC.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from arth.brain import OllamaManager
from arth.permissions import PermissionEngine
from arth.tools.device_tool import AndroidDeviceTool, SecondaryMacTool, LostPhoneFinderTool
from arth.tools.registry_factory import get_default_registry


class TestAndroidPhoneControl:
    """Test Section 11 Android Wi-Fi integration."""

    def test_ring_phone(self):
        tool = AndroidDeviceTool()
        res = tool.execute(action="ring")
        assert res["status"] == "success"
        assert "Ringing your Android phone" in res["message"]

    def test_battery_level(self):
        tool = AndroidDeviceTool()
        res = tool.execute(action="battery")
        assert res["status"] == "success"
        assert "level" in res
        assert "discharging" in res["charging"] or "charging" in res["charging"]
        assert "Boss" in res["message"]

    def test_dnd_toggle(self):
        tool = AndroidDeviceTool()
        res1 = tool.execute(action="dnd", dnd_state="on")
        assert res1["dnd_active"] is True
        assert "turned ON" in res1["message"]

        res2 = tool.execute(action="dnd", dnd_state="off")
        assert res2["dnd_active"] is False
        assert "turned OFF" in res2["message"]

    def test_open_app_on_phone(self):
        tool = AndroidDeviceTool()
        res = tool.execute(action="open_app", app_name="Spotify")
        assert res["status"] == "success"
        assert res["app"] == "Spotify"
        assert "Opened Spotify" in res["message"]

    def test_notifications_redact_otps(self):
        tool = AndroidDeviceTool()
        res = tool.execute(action="notifications")
        assert res["status"] == "success"
        assert tool.is_sensitive is True
        # OTP 849201 must be redacted
        assert "849201" not in res["message"]
        assert "[REDACTED OTP]" in res["message"]
        assert "WhatsApp" in res["message"]


class TestSecondaryMacControl:
    """Test Section 11 Secondary Mac controls and Section 12 Risky gates."""

    def test_wake_mac_magic_packet(self):
        tool = SecondaryMacTool(target_ip="192.168.1.160", target_mac_address="00:11:22:33:44:55")
        res = tool.execute(action="wake")
        assert res["status"] == "success"
        assert "Wake-on-LAN" in res["message"]
        assert "completely powered off cannot be woken" in res["message"]

    def test_lock_secondary_mac(self):
        tool = SecondaryMacTool()
        res = tool.execute(action="lock")
        assert res["status"] == "success"
        assert "Locked screen" in res["message"]

    def test_sleep_and_shutdown_are_risky_actions(self):
        tool = SecondaryMacTool()
        # Describe action must flag as risky
        desc_sleep = tool.describe_action(action="sleep")
        assert tool.is_risky is True
        assert "sleep" in desc_sleep

        tool.is_risky = False
        desc_shut = tool.describe_action(action="shutdown")
        assert tool.is_risky is True
        assert "shut down" in desc_shut


class TestLostPhoneFinder:
    """Test Section 11 Lost Phone Finder and Section 12 Remote Wipe."""

    def test_locate_lost_phone(self):
        tool = LostPhoneFinderTool()
        res = tool.execute(action="locate")
        assert res["status"] == "success"
        assert "latitude" in res
        assert "longitude" in res
        assert "maps.google.com" in res["map_url"]
        assert "LAST KNOWN location" in res["message"]

    def test_lock_message_lost_phone(self):
        tool = LostPhoneFinderTool(contact_number="+91 99999 88888")
        res = tool.execute(action="lock_message", message="Reward if returned to Boss!")
        assert res["status"] == "success"
        assert "Reward if returned to Boss!" in res["message"]

    def test_erase_denied_without_confirmation_code(self):
        tool = LostPhoneFinderTool()
        res = tool.execute(action="erase", confirmation_code="wrong")
        assert res["status"] == "error"
        assert "ERASE" in res["message"]
        assert res.get("requires_confirmation") is True

    def test_erase_approved_with_confirmation_code(self):
        tool = LostPhoneFinderTool()
        res = tool.execute(action="erase", confirmation_code="ERASE")
        assert res["status"] == "success"
        assert tool.is_risky is True
        assert "Remote wipe instruction verified" in res["message"]


class TestPhase9BrainIntegration:
    """Test end-to-end intent resolution and permission gating in ARTH Brain."""

    def test_brain_phone_battery_intent(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("check my phone battery", registry, perm)
        assert "Android phone is at" in resp

    def test_brain_ring_phone_intent(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("ring my phone please", registry, perm)
        assert "Ringing your Android phone" in resp

    def test_brain_wake_secondary_mac(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("wake other mac", registry, perm)
        assert "Wake-on-LAN" in resp

    def test_brain_sleep_secondary_mac_denied_without_face_auth(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        # Risky action without face & password credentials
        resp = brain.process_turn("put secondary mac to sleep", registry, perm)
        assert "Security alert" in resp or "denied" in resp.lower() or "password" in resp.lower()

    def test_brain_locate_lost_phone(self):
        brain = OllamaManager()
        registry = get_default_registry()
        perm = PermissionEngine(prompt_callback=lambda p: True)

        resp = brain.process_turn("where is my lost phone", registry, perm)
        assert "last known location" in resp
