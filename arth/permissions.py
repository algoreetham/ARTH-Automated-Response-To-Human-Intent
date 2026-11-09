"""Permission and safety verification engine for ARTH.
Enforces Section 5, 12, and 30 of ARTH_SPEC:
- Always ask before ANY action.
- For multi-step tasks, ask before EVERY step with exact action details.
- Do nothing until Boss says yes. If no, cancel immediately.
- Sensitive items (passwords, secret documents, banking) are strictly flagged.
- Risky actions (erase phone, send email, shut down/sleep other devices, move/rename many files)
  require spoken 'yes' PLUS Face Check AND Typed Password (Section 12, 30).
"""

from __future__ import annotations

import re
import sys
from typing import Any, Callable, Dict, Optional, Tuple

from arth.security.auth import SecurityManager


class PermissionEngine:
    """Evaluates and requests permission from Boss before actions are taken."""

    SENSITIVE_KEYWORDS = [
        "secret",
        "confidential",
        "password",
        "private",
        "banking",
        "bank",
        "otp",
        "token",
        "credential",
        "ssn",
        "card",
        "salary",
        "tax",
    ]

    RISKY_KEYWORDS = [
        "erase",
        "wipe",
        "send email",
        "shut down",
        "sleep other device",
        "rename many",
        "move many",
        "delete all",
    ]

    def __init__(
        self,
        prompt_callback: Optional[Callable[[str], bool]] = None,
        security_manager: Optional[SecurityManager] = None,
        risky_auth_callback: Optional[Callable[[], Tuple[str, str, str]]] = None,
        interactive_auth_fallback: bool = False,
        strict_mode: bool = True,
    ):
        self.prompt_callback = prompt_callback or self._default_terminal_prompt
        self.security_manager = security_manager or SecurityManager()
        self.risky_auth_callback = risky_auth_callback
        self.interactive_auth_fallback = interactive_auth_fallback
        self.strict_mode = strict_mode
        self.last_reason: str = ""

    @staticmethod
    def _default_terminal_prompt(prompt_message: str) -> bool:
        """Prompt Boss directly in the terminal."""
        try:
            resp = input(f"\n[PERMISSIONS] {prompt_message} (yes/no): ").strip().lower()
            return resp in ["yes", "y", "sure", "ok", "okay", "go ahead", "approved"]
        except (EOFError, KeyboardInterrupt):
            return False

    def is_sensitive_action(
        self,
        action_description: str,
        params: Optional[Dict[str, Any]] = None,
        context_text: Optional[str] = None,
    ) -> bool:
        """Check if the action involves sensitive or secret information."""
        text_to_check = action_description.lower()
        if params:
            text_to_check += " " + str(params).lower()
        if context_text:
            text_to_check += " " + context_text.lower()

        for kw in self.SENSITIVE_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_to_check):
                return True
        return False

    def is_risky_action(
        self,
        action_description: str,
        params: Optional[Dict[str, Any]] = None,
        context_text: Optional[str] = None,
        tool: Optional[Any] = None,
    ) -> bool:
        """Check if the action is classified as risky per Section 12."""
        if tool and getattr(tool, "is_risky", False):
            return True

        text_to_check = action_description.lower()
        if params:
            text_to_check += " " + str(params).lower()
        if context_text:
            text_to_check += " " + context_text.lower()

        for kw in self.RISKY_KEYWORDS:
            if kw in text_to_check:
                return True

        return False

    def check_permission(
        self,
        action_description: str,
        params: Optional[Dict[str, Any]] = None,
        context_text: Optional[str] = None,
        cost: Optional[str] = None,
        tool: Optional[Any] = None,
        auth_credentials: Optional[Tuple[str, str, str]] = None,
    ) -> bool:
        """
        Request approval before taking an action.
        Returns True if approved, False otherwise.
        Sets self.last_reason with the outcome detail.
        For standard actions: requires Boss approval (spoken/modal 'yes').
        For risky actions: requires approval PLUS Face Check AND Typed Password.
        """
        is_sensitive = self.is_sensitive_action(action_description, params, context_text)
        is_risky = self.is_risky_action(action_description, params, context_text, tool)

        cost_notice = f" (Estimated cost: {cost})" if cost else ""
        sensitivity_notice = " [SENSITIVE/SECRET DOCUMENT]" if is_sensitive else ""
        risky_notice = " [HIGH RISK: Face Check + Password Required]" if is_risky else ""

        message = (
            f"Boss, I'm about to {action_description}.{sensitivity_notice}{risky_notice}{cost_notice} Go ahead?"
        )

        approved = self.prompt_callback(message)

        if not approved:
            print("Action cancelled by Boss. Doing nothing.")
            self.last_reason = "Boss cancelled the action."
            return False

        # If it's a risky action, enforce Face Check + Typed Password (Section 12, 30)
        if is_risky:
            password = None
            face_vector = "boss_local_face_vector_v1"
            anti_spoof = "blink"

            if auth_credentials:
                password, face_vector, anti_spoof = auth_credentials
            elif self.risky_auth_callback:
                password, face_vector, anti_spoof = self.risky_auth_callback()
            elif self.interactive_auth_fallback and sys.stdin.isatty():
                try:
                    import getpass
                    password = getpass.getpass("[SECURITY] Enter Boss typed password: ")
                    anti_spoof = input(f"[SECURITY] Face check anti-spoof: {self.security_manager.request_anti_spoof_challenge()} (blink/head_turn): ").strip()
                except Exception:
                    password = None
            else:
                password = None

            if not password:
                self.last_reason = "Risky action blocked: Typed password required."
                return False

            sec_ok, sec_msg = self.security_manager.verify_risky_credentials(
                candidate_password=password,
                face_input=face_vector,
                anti_spoof_response=anti_spoof,
            )

            if not sec_ok:
                self.last_reason = f"Risky action blocked by security: {sec_msg}"
                return False

        self.last_reason = "Approved."
        return True
