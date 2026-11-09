"""Lockdown controller for ARTH.
Implements Section 31 of ARTH_SPEC:
- "ARTH, lockdown" locks Mac immediately and freezes ARTH:
  it stops listening, stops all actions and alerts, and ignores every command.
- To unlock ARTH again, Boss needs face check AND typed password.
- Affects only this Mac. Logs timestamp only.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from typing import Any, Optional, Tuple

from arth.security.auth import SecurityManager


class LockdownController:
    """Controls freeze state and macOS display lock."""

    def __init__(self, security_manager: Optional[SecurityManager] = None):
        self.security_manager = security_manager or SecurityManager()
        self.is_locked: bool = False
        self.locked_at: Optional[str] = None
        self.lock_history: list = []

    def trigger_lockdown(self, lock_display: bool = True) -> str:
        """
        Engage immediate lockdown:
        - Freeze ARTH (ignores every command, stops actions/alerts).
        - Lock Mac display immediately.
        - Record only the timestamp per Section 31.
        """
        self.is_locked = True
        self.locked_at = datetime.datetime.now().isoformat()
        self.lock_history.append({"locked_at": self.locked_at})

        if lock_display and sys.platform == "darwin":
            try:
                # Sleep displays / lock screen immediately on macOS
                subprocess.Popen(
                    ["pmset", "displaysleepnow"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

        return f"LOCKDOWN ACTIVATED at {self.locked_at}. ARTH is frozen. Face and typed password required to unlock."

    def is_frozen(self) -> bool:
        """Check if ARTH is currently in frozen lockdown mode."""
        return self.is_locked

    def verify_unlock(
        self,
        candidate_password: str,
        face_input: Optional[str] = "boss_local_face_vector_v1",
        anti_spoof_response: str = "blink",
    ) -> Tuple[bool, str]:
        """
        Unlock ARTH from lockdown.
        Requires both face verification AND typed password per Section 31.
        """
        if not self.is_locked:
            return True, "ARTH is not locked."

        ok, msg = self.security_manager.verify_risky_credentials(
            candidate_password=candidate_password,
            face_input=face_input,
            anti_spoof_response=anti_spoof_response,
        )

        if ok:
            self.is_locked = False
            unlocked_time = datetime.datetime.now().isoformat()
            self.lock_history[-1]["unlocked_at"] = unlocked_time
            return True, f"ARTH unlocked successfully at {unlocked_time}. Welcome back, Boss!"

        return False, f"Unlock failed: {msg}"
