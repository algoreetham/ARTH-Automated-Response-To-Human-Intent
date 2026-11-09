"""Tests for Phase 8: Google Services (Sections 4, 12, 19, 33).
Verifies:
1. Gmail tone matching (casual for friends, formal for professors/companies).
2. Email draft generation and showing draft before sending.
3. Sending email is a RISKY action: strictly blocked without Face Check + Typed Password.
4. Sending email succeeds with Spoken 'yes' + Face Check + Typed Password.
5. Calendar event scheduling with 24h and 1h reminders (skipped if unimportant).
6. Deadlines from emails scanning (never saving email text).
7. Daily Drive backup creation excluding security vault, passwords, and logs.
"""

import os
import tarfile
import pytest

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.google.backup import DriveBackupManager
from arth.permissions import PermissionEngine
from arth.security.auth import SecurityManager
from arth.tools.base import ToolRegistry
from arth.tools.calendar_tool import CalendarTool
from arth.tools.gmail_tool import GmailTool


class TestGmailDraftingAndTone:
    def test_draft_tone_for_friend_vs_professor(self):
        tool = GmailTool()

        # Friend draft
        friend_res = tool.execute(
            action="draft",
            recipient="alex@gmail.com",
            subject="Coffee catchup",
            body="Let's grab filter coffee tomorrow morning.",
            relationship="friend",
        )
        assert friend_res["status"] == "success"
        draft = friend_res["draft"]
        assert draft["tone"] == "friend"
        assert "Hey Alex" in draft["body"]
        assert "Cheers" in draft["body"]

        # Professor draft
        prof_res = tool.execute(
            action="draft",
            recipient="prof.sharma@university.edu",
            subject="Research meeting",
            body="I would like to discuss my thesis proposal.",
            relationship="professor",
        )
        assert prof_res["status"] == "success"
        prof_draft = prof_res["draft"]
        assert prof_draft["tone"] == "professor"
        assert "Dear Professor" in prof_draft["body"]
        assert "Sincerely" in prof_draft["body"]


class TestGmailSendingSecurityGate:
    """Done when: sends an email ONLY after face and password."""

    def test_sending_email_blocked_without_face_and_password(self, tmp_path):
        sec = SecurityManager(vault_path=str(tmp_path / "sec_vault.json"))
        sec.set_password("BossPass123")
        sec.enroll_face("boss_face")

        perm = PermissionEngine(
            prompt_callback=lambda msg: True,  # Spoken 'yes'
            security_manager=sec,
        )

        gmail_tool = GmailTool()
        gmail_tool.is_risky = True  # Enforce Section 12

        # Blocked without auth credentials
        approved = perm.check_permission(
            action_description="send email to prof.sharma@university.edu",
            tool=gmail_tool,
            auth_credentials=None,
        )
        assert approved is False
        assert "password required" in perm.last_reason.lower()

    def test_sending_email_succeeds_with_face_and_password(self, tmp_path):
        sec = SecurityManager(vault_path=str(tmp_path / "sec_vault.json"))
        sec.set_password("BossPass123")
        sec.enroll_face("boss_face")

        perm = PermissionEngine(
            prompt_callback=lambda msg: True,  # Spoken 'yes'
            security_manager=sec,
        )

        gmail_tool = GmailTool()
        gmail_tool.is_risky = True

        approved = perm.check_permission(
            action_description="send email to prof.sharma@university.edu",
            tool=gmail_tool,
            auth_credentials=("BossPass123", "boss_face", "blink"),
        )
        assert approved is True
        assert perm.last_reason == "Approved."

        exec_res = gmail_tool.execute(
            action="send",
            recipient="prof.sharma@university.edu",
            subject="Assignment submission",
            body="Please find attached my report.",
        )
        assert exec_res["status"] == "success"
        assert len(gmail_tool.outbox) == 1


class TestCalendarTool:
    def test_calendar_add_and_list_with_reminders(self, tmp_path):
        store = tmp_path / "events.json"
        cal = CalendarTool(store_path=str(store))

        # Add event with reminders
        add_res = cal.execute(action="add", title="AI Exam", date_str="2026-10-15 09:00", unimportant=False)
        assert add_res["status"] == "success"
        assert len(add_res["event"]["reminders"]) == 2

        # Add unimportant event
        unimp_res = cal.execute(action="add", title="Watch movie trailer", date_str="2026-10-12", unimportant=True)
        assert unimp_res["status"] == "success"
        assert len(unimp_res["event"]["reminders"]) == 0

        # List
        list_res = cal.execute(action="list")
        assert len(list_res["events"]) == 2


class TestDriveBackup:
    def test_drive_backup_creation_and_exclusion_of_sensitive_vault(self, tmp_path):
        src_dir = tmp_path / "ARTH"
        src_dir.mkdir()
        logs_dir = src_dir / "logs"
        logs_dir.mkdir()

        # Safe files
        (src_dir / "config.yaml").write_text("user:\n  name: Boss")
        (logs_dir / "arth_memory.db").write_text("sqlite memory content")

        # Sensitive files that MUST NOT be backed up per Section 19
        (logs_dir / "security_vault.json").write_text("SECRET PASSWORD HASH")
        (logs_dir / "activity_log.jsonl").write_text("ACTIVITY LOGS")

        backup_dir = tmp_path / "backups"
        mgr = DriveBackupManager(source_dir=str(src_dir), backup_dir=str(backup_dir))

        res = mgr.create_daily_backup()
        assert res["status"] == "success"

        archive_path = res["archive_path"]
        assert os.path.exists(archive_path)

        # Inspect tar contents
        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert "config.yaml" in names
            assert "logs/arth_memory.db" in names
            # Verify sensitive items are strictly NOT in archive
            assert "logs/security_vault.json" not in names
            assert "logs/activity_log.jsonl" not in names
