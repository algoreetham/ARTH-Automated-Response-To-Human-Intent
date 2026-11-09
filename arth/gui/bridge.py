"""GUI Bridge linking pywebview Javascript UI to ARTH Python core.
Handles message passing, permission modal synchronization, activity logs, and status updates.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.logger import ActivityLogger
from arth.memory import MemoryManager
from arth.multi_request import MultiRequestHandler
from arth.permissions import PermissionEngine
from arth.personality import PersonalityEngine
from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool
from arth.voice.tts import TTSEngine
from arth.voice.stt import STTEngine


class GUIBridge:
    """Exposed to Javascript in pywebview via window.pywebview.api."""

    def __init__(
        self,
        config: Optional[ArthConfig] = None,
        brain: Optional[OllamaManager] = None,
        logger: Optional[ActivityLogger] = None,
        memory: Optional[MemoryManager] = None,
        personality: Optional[PersonalityEngine] = None,
        tts: Optional[TTSEngine] = None,
        stt: Optional[STTEngine] = None,
    ):
        self.config = config or ArthConfig()
        self.brain = brain or OllamaManager(self.config)
        self.logger = logger or ActivityLogger()
        self.memory = memory or MemoryManager()
        self.personality = personality or PersonalityEngine()
        self.tts = tts or TTSEngine(self.config)
        self.stt = stt or STTEngine(self.config)

        # Tools
        from arth.tools.registry_factory import get_default_registry
        self.registry = get_default_registry()

        # Permission synchronization
        self._permission_event = threading.Event()
        self._permission_response: bool = False
        self._pending_permission_prompt: Optional[str] = None
        self._is_waiting_for_permission: bool = False

        # Permission engine wired to GUI callback
        self.permission_engine = PermissionEngine(
            prompt_callback=self._gui_permission_prompt,
            strict_mode=True,
        )
        self.multi_handler = MultiRequestHandler()

        # Chat history
        self.history: List[Dict[str, str]] = []
        self._window: Any = None

    def set_window(self, window: Any) -> None:
        """Store reference to pywebview window for sending JS events."""
        self._window = window

    def _gui_permission_prompt(self, prompt_message: str) -> bool:
        """Called by PermissionEngine. Opens popup modal in GUI and waits for response."""
        self._permission_event.clear()
        self._permission_response = False
        self._pending_permission_prompt = prompt_message
        self._is_waiting_for_permission = True

        # Notify JS frontend to show permission popup
        if self._window:
            try:
                self._window.evaluate_js(
                    f"window.arthApp && window.arthApp.showPermissionModal({repr(prompt_message)});"
                )
            except Exception:
                pass

        # Wait for Boss to click Approve or Deny (timeout 60 seconds)
        got_response = self._permission_event.wait(timeout=60.0)
        self._pending_permission_prompt = None
        self._is_waiting_for_permission = False

        if not got_response:
            return False  # Timed out -> auto-cancel for safety

        return self._permission_response

    # --- Methods called directly from JS ---

    def send_message(self, user_input: str, speak: bool = True) -> Dict[str, Any]:
        """Receive message from GUI text box, process through brain and return result."""
        text = user_input.strip()
        if not text:
            return {"status": "empty"}

        # Check for multiple requests
        split_reqs = self.multi_handler.split_requests(text)
        responses = []

        for req in split_reqs:
            resp = self.brain.process_turn(
                user_input=req,
                tool_registry=self.registry,
                permission_engine=self.permission_engine,
                history=self.history,
                logger=self.logger,
                memory=self.memory,
                personality=self.personality,
            )
            responses.append(resp)
            self.history.append({"role": "user", "content": req})
            self.history.append({"role": "assistant", "content": resp})

        combined_reply = "\n\n".join(responses)
        if combined_reply and self.tts and speak:
            clean_speech = self.personality.clean_spoken_response(combined_reply)
            self.tts.speak(clean_speech, blocking=False)

        return {
            "status": "success",
            "reply": combined_reply,
            "logs": self.logger.get_logs(limit=20),
        }

    def listen_voice(self, duration: float = 4.0, lang: str = "en") -> Dict[str, Any]:
        """Record voice natively from hardware microphone and process turn."""
        res = self.stt.record_and_transcribe(duration=duration, lang=lang)
        transcript = res.get("text", "").strip()
        if not transcript:
            err_msg = res.get("error", "No speech detected")
            return {
                "status": "no_speech",
                "error": err_msg,
                "reply": "Boss, I couldn't hear your voice clearly. Please try speaking closer to the microphone.",
            }

        turn_res = self.send_message(transcript, speak=True)
        return {
            "status": "success",
            "transcript": transcript,
            "reply": turn_res.get("reply", ""),
            "logs": turn_res.get("logs", []),
        }

    def resolve_permission(self, approved: bool) -> bool:
        """Called from JS modal when Boss clicks 'Approve' (True) or 'Deny' (False)."""
        self._permission_response = bool(approved)
        self._permission_event.set()
        return True

    def get_pending_permission(self) -> Dict[str, Any]:
        """Return currently pending permission prompt for web UI polling."""
        return {
            "waiting": self._is_waiting_for_permission,
            "prompt": self._pending_permission_prompt,
        }

    def get_logs(self, query: str = "", status: str = "all") -> List[Dict[str, Any]]:
        """Fetch activity logs for the Log tab."""
        return self.logger.get_logs(query=query, status=status, limit=100)

    def get_initial_state(self) -> Dict[str, Any]:
        """Return initial state on GUI load."""
        return {
            "user_name": self.config.user.name,
            "model": self.config.brain.model,
            "context_window": self.config.brain.context_window,
            "status": "Idle",
            "logs": self.logger.get_logs(limit=50),
            "todos": [
                {"id": 1, "task": "Review ARTH architecture", "done": False, "priority": "High"},
                {"id": 2, "task": "Setup Google OAuth in .env", "done": False, "priority": "Medium"},
                {"id": 3, "task": "Verify Ollama Gemma 4 model", "done": True, "priority": "Low"},
            ],
            "reminders": [
                {"id": 1, "title": "Quiet hours active at 22:00", "time": "22:00"},
            ],
        }
