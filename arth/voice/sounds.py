"""Sound effects and startup greeting for ARTH.
Enforces Section 32 of ARTH_SPEC:
- Startup: play futuristic startup sound, greet excitedly: 'HELLOO BOSSS!'
- Futuristic sound effects for startup, when starting to listen, and when completing a task.
- Suppressed during quiet hours.
"""

from __future__ import annotations

import os
import subprocess
import threading
from typing import Optional

from arth.config import ArthConfig
from arth.voice.tts import TTSEngine


class SoundManager:
    """Manages audio cues, chimes, and startup greetings."""

    def __init__(self, config: Optional[ArthConfig] = None, tts: Optional[TTSEngine] = None):
        self.config = config or ArthConfig()
        self.tts = tts or TTSEngine(self.config)

    def is_quiet(self) -> bool:
        return self.tts.is_quiet_hours()

    def play_chime(self, sound_type: str = "startup") -> None:
        """Play a short macOS system chime if not during quiet hours."""
        if self.is_quiet():
            return

        sound_name_map = {
            "startup": "Hero",
            "listen": "Tink",
            "task_done": "Glass",
            "alert": "Ping",
        }
        sound_name = sound_name_map.get(sound_type, "Tink")
        sound_path = f"/System/Library/Sounds/{sound_name}.aiff"

        if os.path.exists(sound_path):
            try:
                subprocess.Popen(
                    ["afplay", sound_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def startup_greeting(self) -> str:
        """Execute the exact startup sequence: chime + excited 'HELLOO BOSSS!'."""
        self.play_chime("startup")
        greeting = "HELLOO BOSSS!"
        if not self.is_quiet():
            # Speak greeting out loud
            self.tts.speak(greeting, blocking=False)
        return greeting
