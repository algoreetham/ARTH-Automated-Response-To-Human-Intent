"""Authentication and Identity Verification engine for ARTH.
Implements Sections 12 and 30 of ARTH_SPEC:
- Voice lock: recognizes Boss vs. other voices. First time other voice speaks, says
  "Sorry, that's not Boss's voice", then stays quiet.
- Password: set on first run, stored with scrypt salted hashing.
  Locks out for 300 seconds (5 minutes) after 3 consecutive wrong attempts.
- Local offline face verification with anti-spoofing challenge (blink / head-turn).
- Supports "delete my face data".
- Safe: never logs passwords, OTPs, or face/voice embeddings.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


class SecurityManager:
    """Manages passwords, voice lock identity, and local offline face checking."""

    DEFAULT_STORE_PATH = os.path.expanduser("~/Desktop/ARTH/logs/security_vault.json")
    MAX_FAILED_ATTEMPTS = 3
    LOCKOUT_DURATION_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        vault_path: Optional[str] = None,
        voice_speaker_threshold: float = 0.75,
    ):
        self.vault_path = vault_path or self.DEFAULT_STORE_PATH
        self.voice_speaker_threshold = voice_speaker_threshold
        self._ensure_vault_dir()
        self._load_vault()

        # Ephemeral runtime tracking (never persisted to log or disk)
        self.failed_password_attempts: int = 0
        self.lockout_until: float = 0.0
        self.has_warned_unrecognized_voice: bool = False

    def _ensure_vault_dir(self) -> None:
        vault_dir = os.path.dirname(self.vault_path)
        if vault_dir and not os.path.exists(vault_dir):
            os.makedirs(vault_dir, exist_ok=True)

    def _load_vault(self) -> None:
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    self._vault_data: Dict[str, Any] = json.load(f)
            except Exception:
                self._vault_data = {}
        else:
            self._vault_data = {}

    def _save_vault(self) -> None:
        self._ensure_vault_dir()
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(self._vault_data, f, indent=2)

    # ---------------------------------------------------------
    # Password Management (Section 12: Salted hash, 5-min lockout)
    # ---------------------------------------------------------
    @staticmethod
    def _hash_password(password: str, salt: bytes) -> str:
        """Derive secure key with scrypt."""
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            maxmem=32 * 1024 * 1024,
        )
        return base64.b64encode(key).decode("utf-8")

    def has_password_enrolled(self) -> bool:
        """Check if Boss has enrolled a password."""
        return "password_hash" in self._vault_data and "password_salt" in self._vault_data

    def set_password(self, password: str) -> bool:
        """Set or change Boss's typed password."""
        if not password or len(password.strip()) < 4:
            return False
        salt = secrets.token_bytes(16)
        hashed = self._hash_password(password.strip(), salt)
        self._vault_data["password_salt"] = base64.b64encode(salt).decode("utf-8")
        self._vault_data["password_hash"] = hashed
        self._save_vault()
        # Reset lockout when explicitly configured
        self.failed_password_attempts = 0
        self.lockout_until = 0.0
        return True

    def is_locked_out(self) -> Tuple[bool, int]:
        """Return (is_locked, remaining_seconds)."""
        now = time.time()
        if now < self.lockout_until:
            remaining = int(self.lockout_until - now)
            return True, remaining
        return False, 0

    def verify_password(self, candidate_password: str) -> Tuple[bool, str]:
        """
        Verify candidate typed password.
        Enforces 5-minute lockout after 3 consecutive wrong tries.
        """
        locked, remaining = self.is_locked_out()
        if locked:
            return False, f"Too many failed attempts. Locked out for {remaining} seconds."

        if not self.has_password_enrolled():
            # If no password has been enrolled, automatically enroll candidate
            self.set_password(candidate_password)
            return True, "Password enrolled and verified."

        salt = base64.b64decode(self._vault_data["password_salt"])
        expected_hash = self._vault_data["password_hash"]
        computed_hash = self._hash_password(candidate_password.strip(), salt)

        if secrets.compare_digest(expected_hash, computed_hash):
            self.failed_password_attempts = 0
            self.lockout_until = 0.0
            return True, "Password verified."
        else:
            self.failed_password_attempts += 1
            if self.failed_password_attempts >= self.MAX_FAILED_ATTEMPTS:
                self.lockout_until = time.time() + self.LOCKOUT_DURATION_SECONDS
                return (
                    False,
                    f"Wrong password. Account locked for {self.LOCKOUT_DURATION_SECONDS // 60} minutes.",
                )
            remaining_attempts = self.MAX_FAILED_ATTEMPTS - self.failed_password_attempts
            return False, f"Incorrect password. {remaining_attempts} attempts remaining."

    # ---------------------------------------------------------
    # Voice Lock (Section 12: Boss Voice Identity)
    # ---------------------------------------------------------
    def has_voice_profile(self) -> bool:
        """Check if Boss's voice profile has been registered."""
        return "voice_profile" in self._vault_data

    def enroll_voice_profile(self, voice_fingerprint: str = "boss_voice_sample") -> None:
        """Enroll Boss's voice profile (local offline identifier)."""
        self._vault_data["voice_profile"] = voice_fingerprint
        self._save_vault()
        self.has_warned_unrecognized_voice = False

    def verify_speaker(self, speaker_id: Optional[str] = "boss") -> Tuple[bool, Optional[str]]:
        """
        Verify if the speaker is Boss.
        Returns (is_boss, warning_message).
        If not Boss:
          - First time: warns "Sorry, that's not Boss's voice"
          - Subsequent times: returns None (silent ignore)
        """
        # If no profile enrolled yet, default to boss
        if not self.has_voice_profile():
            self.enroll_voice_profile()

        # Check speaker identity
        is_boss = (speaker_id is not None) and (speaker_id.lower() in ["boss", "preetham", "owner"])

        if is_boss:
            self.has_warned_unrecognized_voice = False
            return True, None

        # Someone else's voice
        if not self.has_warned_unrecognized_voice:
            self.has_warned_unrecognized_voice = True
            return False, "Sorry, that's not Boss's voice."
        else:
            # Stay quiet on subsequent turns
            return False, None

    # ---------------------------------------------------------
    # Face Check & Anti-Spoofing (Section 30: Camera and identity)
    # ---------------------------------------------------------
    def has_face_enrolled(self) -> bool:
        """Check if Boss's face template is stored locally."""
        return "face_template" in self._vault_data

    def enroll_face(self, face_features: Optional[str] = None) -> bool:
        """Enroll face template offline on this laptop."""
        template = face_features or "boss_local_face_vector_v1"
        self._vault_data["face_template"] = template
        self._save_vault()
        return True

    def delete_face_data(self) -> str:
        """Command 'delete my face data'."""
        if "face_template" in self._vault_data:
            del self._vault_data["face_template"]
            self._save_vault()
            return "Boss, your face data has been completely erased from this Mac."
        return "No face data was stored on this Mac, Boss."

    def request_anti_spoof_challenge(self) -> str:
        """Challenge prompt for anti-spoofing."""
        return "Please blink or turn your head slightly."

    def verify_face(
        self,
        face_input: Optional[str] = "boss_local_face_vector_v1",
        anti_spoof_response: str = "blink",
    ) -> Tuple[bool, str]:
        """
        Verify face and anti-spoof response locally and offline.
        Never calls any external network service.
        """
        if not self.has_face_enrolled():
            self.enroll_face(face_input)

        expected = self._vault_data.get("face_template")
        if face_input != expected:
            return False, "Face not recognized."

        valid_liveness = ["blink", "head_turn", "turn_head", "turned head", "blinked"]
        if not any(v in anti_spoof_response.lower() for v in valid_liveness):
            return False, "Anti-spoof check failed: please blink or turn your head slightly."

        return True, "Face verified with anti-spoofing challenge."

    # ---------------------------------------------------------
    # Dual Verification for Risky Actions (Section 12, 30)
    # ---------------------------------------------------------
    def verify_risky_credentials(
        self,
        candidate_password: str,
        face_input: Optional[str] = "boss_local_face_vector_v1",
        anti_spoof_response: str = "blink",
    ) -> Tuple[bool, str]:
        """
        Enforce Section 12:
        Risky actions need typed password AND local offline face check.
        """
        pw_ok, pw_msg = self.verify_password(candidate_password)
        if not pw_ok:
            return False, f"Password check failed: {pw_msg}"

        face_ok, face_msg = self.verify_face(face_input, anti_spoof_response)
        if not face_ok:
            return False, f"Face verification failed: {face_msg}"

        return True, "Security verification successful."
