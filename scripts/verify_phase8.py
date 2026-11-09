#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 8: Google Services.
Verifies all 3 acceptance criteria:
1. ARTH drafts an email in the right tone (friend vs professor).
2. Sends it ONLY after face and password.
3. Adds a calendar event.
"""

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.google.backup import DriveBackupManager
from arth.permissions import PermissionEngine
from arth.security.auth import SecurityManager
from arth.tools.base import ToolRegistry
from arth.tools.calendar_tool import CalendarTool
from arth.tools.gmail_tool import GmailTool


def main():
    print("=" * 65)
    print("📧 ARTH PHASE 8: GOOGLE SERVICES ACCEPTANCE VERIFICATION")
    print("=" * 65)

    sec = SecurityManager(vault_path="logs/test_phase8_vault.json")
    sec.set_password("BossSecret2026")
    sec.enroll_face("boss_face_sample_1")

    gmail_tool = GmailTool()
    cal_tool = CalendarTool(store_path="logs/test_phase8_calendar.json")

    reg = ToolRegistry()
    reg.register(gmail_tool)
    reg.register(cal_tool)

    cfg = ArthConfig()
    brain = OllamaManager(cfg, security_manager=sec)

    # 1. Email Draft in Right Tone
    print("\n--- 1. Testing Email Draft in Right Tone (Section 33) ---")
    draft_res = brain.process_turn(
        "ARTH, draft email to professor asking for deadline extension",
        reg,
        PermissionEngine(prompt_callback=lambda msg: True, security_manager=sec),
        speaker_id="boss",
    )
    print("ARTH >>", draft_res)
    assert len(gmail_tool.drafts) >= 1
    draft = gmail_tool.drafts[-1]
    assert draft["tone"] == "professor"
    assert "Dear Professor" in draft["body"]
    print("✅ Email Draft Verified: Drafted in polite, academic tone.")

    # 2. Sending Email Requires Face + Password (Section 12 Acceptance)
    print("\n--- 2. Testing Send Email Multi-Factor Gate (Section 12) ---")
    perm_voice_only = PermissionEngine(prompt_callback=lambda msg: True, security_manager=sec)

    # Attempt without Face + Password
    send_fail = brain.process_turn(
        "ARTH, send email to professor",
        reg,
        perm_voice_only,
        speaker_id="boss",
        auth_credentials=None,
    )
    print("Attempt send without Face + Password >>", send_fail)
    assert "security alert" in send_fail.lower()
    assert len(gmail_tool.outbox) == 0
    print("✓ Send blocked without credentials.")

    # Attempt with Face + Password
    send_success = brain.process_turn(
        "ARTH, send email to professor",
        reg,
        perm_voice_only,
        speaker_id="boss",
        auth_credentials=("BossSecret2026", "boss_face_sample_1", "blink"),
    )
    print("Attempt send with Face + Password >>", send_success)
    assert "Done, Boss!" in send_success
    assert len(gmail_tool.outbox) == 1
    print("✅ Send Email Verified: Sent only after Face + Password validation.")

    # 3. Add Calendar Event
    print("\n--- 3. Testing Google Calendar Event Addition (Section 4 & 33) ---")
    cal_reply = brain.process_turn(
        "ARTH, schedule event: Machine Learning Project Review",
        reg,
        PermissionEngine(prompt_callback=lambda msg: True, security_manager=sec),
        speaker_id="boss",
    )
    print("ARTH >>", cal_reply)
    assert "Done, Boss!" in cal_reply
    events = cal_tool.execute(action="list")["events"]
    assert any("Machine Learning" in e["title"] for e in events)
    print("✅ Calendar Event Verified: Event added with automatic reminders.")

    # 4. Drive Daily Backup
    print("\n--- 4. Testing Google Drive Backup (Section 19) ---")
    backup_mgr = DriveBackupManager(source_dir=".", backup_dir="backups")
    backup_res = backup_mgr.create_daily_backup()
    print("Backup creation >>", backup_res["message"])
    assert backup_res["status"] == "success"
    print("✅ Drive Backup Verified: Sanitized archive package generated.")

    print("\n" + "=" * 65)
    print("🎉 ALL PHASE 8 ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
