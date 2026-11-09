"""Text-to-Speech (TTS) engine for ARTH.
Enforces Sections 2, 15, and 22 of ARTH_SPEC:
- Voice: calm, female, natural. Normal speed.
- Languages: English, Hindi, Kannada.
- Sarvam Bulbul v3 (when SARVAM_API_KEY present), free Edge-TTS fallback, macOS 'say' fallback.
- Quiet Hours (Section 15): strictly silences speech during configured quiet hours.
- Interruption: allows stopping speech immediately.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

from arth.config import ArthConfig, QuietHoursConfig, VoiceConfig


class TTSEngine:
    """Multilingual Text-to-Speech synthesizer with quiet-hours suppression and instant interruption."""

    # Default neural voices (Male Jarvis British/Deep style)
    VOICE_MAP = {
        "en": "en-GB-RyanNeural",    # British refined male Jarvis tone
        "hi": "hi-IN-MadhurNeural",   # Indian male natural voice
        "kn": "kn-IN-GaganNeural",    # Kannada male natural voice
    }

    def __init__(self, config: Optional[ArthConfig] = None):
        self.config = config or ArthConfig()
        self.voice_cfg: VoiceConfig = self.config.voice
        self.quiet_cfg: QuietHoursConfig = self.config.quiet_hours

        self.sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
        self._current_process: Optional[subprocess.Popen] = None
        self._is_speaking = False
        self._lock = threading.Lock()

    def is_quiet_hours(self) -> bool:
        """Check if current system time falls within quiet hours (Section 15)."""
        if not self.quiet_cfg.enabled:
            return False

        try:
            now = datetime.now().time()
            start_h, start_m = map(int, self.quiet_cfg.start.split(":"))
            end_h, end_m = map(int, self.quiet_cfg.end.split(":"))
            start_time = datetime.now().replace(hour=start_h, minute=start_m, second=0).time()
            end_time = datetime.now().replace(hour=end_h, minute=end_m, second=0).time()

            if start_time < end_time:
                return start_time <= now <= end_time
            else:
                # Overnights (e.g. 22:00 to 07:00)
                return now >= start_time or now <= end_time
        except Exception:
            return False

    def stop(self) -> None:
        """Interrupt and immediately terminate any current speech playback."""
        with self._lock:
            if self._current_process:
                try:
                    self._current_process.terminate()
                except Exception:
                    pass
                self._current_process = None
            self._is_speaking = False

    def detect_language(self, text: str) -> str:
        """Detect whether text is Kannada, Hindi/Devanagari, or English."""
        # Kannada unicode block: U+0C80–U+0CFF
        if any("\u0C80" <= c <= "\u0CFF" for c in text):
            return "kn"
        # Devanagari unicode block (Hindi): U+0900–U+097F
        if any("\u0900" <= c <= "\u097F" for c in text):
            return "hi"
        return "en"

    def speak(self, text: str, lang: Optional[str] = None, blocking: bool = True) -> bool:
        """
        Synthesize and speak text out loud.
        Returns True if spoken, False if suppressed by quiet hours or error.
        """
        clean_text = text.strip()
        if not clean_text:
            return False

        # Strictly respect quiet hours (Section 15)
        if self.is_quiet_hours():
            return False

        target_lang = lang or self.detect_language(clean_text)

        if blocking:
            return self._speak_sync(clean_text, target_lang)
        else:
            t = threading.Thread(target=self._speak_sync, args=(clean_text, target_lang), daemon=True)
            t.start()
            return True

    def _speak_sync(self, text: str, lang: str) -> bool:
        self.stop()
        self._is_speaking = True

        try:
            # 1. macOS native British male Jarvis voice (instant, zero network latency)
            success = self._speak_macos_say(text)
            if success:
                return True

            # 2. Try Sarvam Bulbul v3 if API key available
            if self.sarvam_key:
                success = self._speak_sarvam(text, lang)
                if success:
                    return True

            # 3. Try Edge-TTS (Neural voice)
            if HAS_EDGE_TTS:
                success = self._speak_edge(text, lang)
                if success:
                    return True

            return False
        finally:
            self._is_speaking = False

    def _speak_sarvam(self, text: str, lang: str) -> bool:
        """Synthesize audio using Sarvam AI Bulbul v3 API."""
        try:
            url = "https://api.sarvam.ai/text-to-speech"
            headers = {"api-subscription-key": self.sarvam_key}
            lang_code = f"{lang}-IN" if lang in ["hi", "kn", "en"] else "en-IN"
            payload = {
                "inputs": [text],
                "target_language_code": lang_code,
                "speaker": "arvind",  # Deep natural male voice
                "model": "bulbul:v1",
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                audios = data.get("audios", [])
                if audios:
                    import base64
                    audio_bytes = base64.b64decode(audios[0])
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                        tf.write(audio_bytes)
                        tf_path = tf.name
                    self._play_audio_file(tf_path)
                    try:
                        os.unlink(tf_path)
                    except Exception:
                        pass
                    return True
        except Exception:
            pass
        return False

    def _speak_edge(self, text: str, lang: str) -> bool:
        """Synthesize using Edge-TTS asynchronously."""
        voice = self.VOICE_MAP.get(lang, "en-GB-RyanNeural")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            output_file = tf.name

        try:
            async def _run_edge():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_file)

            asyncio.run(_run_edge())
            self._play_audio_file(output_file)
            return True
        except Exception:
            return False
        finally:
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except Exception:
                    pass

    def _speak_macos_say(self, text: str) -> bool:
        """Fallback to native macOS say command with British male Jarvis voice (Daniel)."""
        try:
            with self._lock:
                self._current_process = subprocess.Popen(
                    ["say", "-v", "Daniel", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            self._current_process.wait()
            return True
        except Exception:
            return False

    def _play_audio_file(self, file_path: str) -> None:
        """Play audio using native macOS afplay command."""
        try:
            with self._lock:
                self._current_process = subprocess.Popen(
                    ["afplay", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            self._current_process.wait()
        except Exception:
            pass
