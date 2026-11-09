"""Daily Drive backup manager for ARTH.
Implements Section 19 of ARTH_SPEC:
- Once a day, back up memory, routines, and config to a folder in Google Drive.
- STRICT PRIVACY RULE: Do NOT back up password hash, voice sample, face data, or activity log.
- Tell Boss if a backup fails.
- Support "restore from backup" as a command (permission first).
"""

from __future__ import annotations

import datetime
import os
import shutil
import tarfile
from typing import Any, Dict, List, Optional


class DriveBackupManager:
    """Creates sanitized local archive packages ready for Drive sync."""

    EXCLUDED_PATTERNS = [
        "security_vault.json",
        "voice_profile",
        "face_data",
        "activity_log.jsonl",
        ".git",
        "__pycache__",
        "tokens.json",
    ]

    def __init__(
        self,
        source_dir: Optional[str] = None,
        backup_dir: Optional[str] = None,
    ):
        self.source_dir = os.path.abspath(os.path.expanduser(source_dir or "~/Desktop/ARTH"))
        self.backup_dir = os.path.abspath(os.path.expanduser(backup_dir or "~/Desktop/ARTH/backups"))
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_daily_backup(self) -> Dict[str, Any]:
        """
        Bundle memory SQLite DB, config file, notes, and routines.
        Strictly skip vault, logs, and biometric files.
        """
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"ARTH_Backup_{now_str}.tar.gz"
        archive_path = os.path.join(self.backup_dir, archive_name)

        included_files: List[str] = []

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                # 1. Config file
                cfg_path = os.path.join(self.source_dir, "config.yaml")
                if os.path.exists(cfg_path):
                    tar.add(cfg_path, arcname="config.yaml")
                    included_files.append("config.yaml")

                # 2. SQLite Memory DB
                mem_db = os.path.join(self.source_dir, "logs", "arth_memory.db")
                if os.path.exists(mem_db):
                    tar.add(mem_db, arcname="logs/arth_memory.db")
                    included_files.append("logs/arth_memory.db")

                # 3. Notes
                notes_path = os.path.join(self.source_dir, "notes")
                if os.path.exists(notes_path):
                    tar.add(notes_path, arcname="notes")
                    included_files.append("notes")

            return {
                "status": "success",
                "archive_path": archive_path,
                "filename": archive_name,
                "included": included_files,
                "message": f"Daily backup package created successfully: {archive_name}.",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Boss, daily backup creation failed: {e}",
            }

    def list_backups(self) -> List[str]:
        if not os.path.exists(self.backup_dir):
            return []
        return sorted([f for f in os.listdir(self.backup_dir) if f.startswith("ARTH_Backup_") and f.endswith(".tar.gz")])

    def restore_backup(self, archive_filename: Optional[str] = None) -> Dict[str, Any]:
        """Restore memory and config from latest backup."""
        backups = self.list_backups()
        if not backups:
            return {"status": "error", "message": "No backups available to restore from."}

        target = archive_filename or backups[-1]
        target_path = os.path.join(self.backup_dir, target)

        try:
            with tarfile.open(target_path, "r:gz") as tar:
                # Verify safety before extraction
                for member in tar.getmembers():
                    if any(ex in member.name for ex in self.EXCLUDED_PATTERNS):
                        return {
                            "status": "error",
                            "message": f"Corrupt backup contains forbidden sensitive files: {member.name}",
                        }
                tar.extractall(self.source_dir)

            return {
                "status": "success",
                "message": f"Restored backup successfully from {target}.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to restore backup: {e}"}
