"""Human-like thinking fillers for ARTH.
Enforces Section 21 of ARTH_SPEC:
- While thinking or running a slow tool, say a short filler in ARTH's witty style.
- Reply in the language spoken (English, Hindi, Kannada).
- Vary the phrases.
- Never during quiet hours.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from arth.voice.tts import TTSEngine


class FillerManager:
    """Provides varied thinking fillers across English, Hindi, and Kannada."""

    FILLERS: Dict[str, List[str]] = {
        "en": [
            "Hmm, let me check that for you, Boss.",
            "One sec Boss, pulling that up right now.",
            "On it Boss, let me see.",
            "Hold tight Boss, checking on that.",
        ],
        "hi": [
            "Ek minute Boss, abhi dekhta hoon.",
            "Rukye Boss, check kar raha hoon.",
            "Zara ek sec Boss, abhi nikaalta hoon.",
        ],
        "kn": [
            "Ondhu nimisha Boss, check maadtini.",
            "Swalpa iriri Boss, nodtini.",
            "Haa Boss, nodta idini.",
        ],
    }

    def __init__(self, tts: Optional[TTSEngine] = None):
        self.tts = tts
        self._last_spoken: Dict[str, str] = {}

    def get_filler(self, lang: str = "en") -> str:
        """Get a fresh, varied filler phrase in the target language."""
        options = self.FILLERS.get(lang, self.FILLERS["en"])
        last = self._last_spoken.get(lang)
        choices = [opt for opt in options if opt != last] or options
        chosen = random.choice(choices)
        self._last_spoken[lang] = chosen
        return chosen

    def say_filler(self, lang: str = "en") -> Optional[str]:
        """Speak a filler phrase if not in quiet hours."""
        phrase = self.get_filler(lang)
        if self.tts and not self.tts.is_quiet_hours():
            self.tts.speak(phrase, lang=lang, blocking=False)
        return phrase
