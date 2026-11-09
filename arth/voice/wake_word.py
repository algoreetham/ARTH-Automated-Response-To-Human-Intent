"""Wake word detection, mic muting, and wake-up listener for ARTH.
Enforces Sections 2 and 18 of ARTH_SPEC:
- Wake word: 'ARTH'
- 'ARTH, mute' turns mic off, sets MUTED status.
- While muted, a tiny local listener listens ONLY for 'ARTH, wake up'.
- Confirms out loud when waking up.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from arth.config import ArthConfig


class WakeWordDetector:
    """Manages wake-word listening, mute state, and wake-up triggers."""

    def __init__(
        self,
        config: Optional[ArthConfig] = None,
        on_wake: Optional[Callable[[], None]] = None,
        tts_callback: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or ArthConfig()
        self.wake_word = self.config.voice.wake_word
        self.on_wake = on_wake
        self.tts_callback = tts_callback

        self._is_muted = False
        self._is_listening = False
        self._lock = threading.Lock()

    @property
    def is_muted(self) -> bool:
        return self._is_muted

    def mute(self) -> str:
        """Mute the microphone per Section 18."""
        with self._lock:
            self._is_muted = True
        return "MUTED"

    def unmute(self) -> str:
        """Unmute the microphone and confirm out loud."""
        with self._lock:
            self._is_muted = False
        msg = "I'm listening again, Boss."
        if self.tts_callback:
            self.tts_callback(msg)
        return msg

    def check_audio_transcription_for_wake_or_mute(self, text: str) -> Optional[str]:
        """
        Process a recognized text string:
        - If muted: only responds to 'ARTH, wake up' or 'wake up'
        - If active: detects 'ARTH, mute' or wake word 'ARTH'
        """
        clean = text.strip().lower()

        # While muted, listen ONLY for 'wake up'
        if self._is_muted:
            if "wake up" in clean or f"{self.wake_word.lower()} wake up" in clean:
                self.unmute()
                return "WAKE_UP"
            return None

        # When active, check for mute command
        if "mute" in clean or f"{self.wake_word.lower()} mute" in clean:
            self.mute()
            return "MUTED"

        # Check wake word
        if self.wake_word.lower() in clean:
            if self.on_wake:
                self.on_wake()
            return "WAKE"

        return None
