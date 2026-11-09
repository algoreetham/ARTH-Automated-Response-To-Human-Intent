"""Speech-to-Text (STT) engine for ARTH.
Enforces Section 2 and 22 of ARTH_SPEC:
- Languages: English, Hindi, Kannada (mixed speech supported).
- Primary: Sarvam Saaras API (if SARVAM_API_KEY present).
- Free speech recognition (Google Speech API via speech_recognition).
- Hardware mic capture via sounddevice.
"""

from __future__ import annotations

import io
import os
import wave
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

try:
    import sounddevice as sd
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

from arth.config import ArthConfig


class STTEngine:
    """Multilingual Speech-to-Text recognizer with Sarvam Saaras, Google STT, and native mic recording."""

    def __init__(self, config: Optional[ArthConfig] = None):
        self.config = config or ArthConfig()
        self.sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
        self.recognizer = sr.Recognizer() if HAS_SPEECH_RECOGNITION else None

    def transcribe_audio_file(self, file_path: str, lang: str = "en") -> Dict[str, Any]:
        """Transcribe an audio file into text."""
        if not os.path.exists(file_path):
            return {"text": "", "language": lang, "confidence": 0.0}

        # 1. Try Sarvam Saaras API if key available
        if self.sarvam_key:
            sarvam_res = self._transcribe_sarvam(file_path, lang)
            if sarvam_res.get("text"):
                return sarvam_res

        # 2. Try SpeechRecognition (Google STT)
        if HAS_SPEECH_RECOGNITION and self.recognizer:
            try:
                with sr.AudioFile(file_path) as source:
                    audio_data = self.recognizer.record(source)
                lang_code = "en-IN" if lang == "en" else ("hi-IN" if lang == "hi" else ("kn-IN" if lang == "kn" else "en-IN"))
                text = self.recognizer.recognize_google(audio_data, language=lang_code)
                if text:
                    return {
                        "text": text,
                        "language": lang,
                        "confidence": 0.9,
                    }
            except Exception as e:
                pass

        return {
            "text": "",
            "language": "en",
            "confidence": 0.0,
            "error": "No STT backend available.",
        }

    def record_and_transcribe(self, duration: float = 4.0, lang: str = "en") -> Dict[str, Any]:
        """Record live audio from the native MacBook microphone and transcribe it."""
        if not HAS_SOUNDDEVICE or not HAS_SPEECH_RECOGNITION or not self.recognizer:
            return {"text": "", "error": "Hardware recording requires sounddevice and speech_recognition."}

        samplerate = 16000
        try:
            frames = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
            sd.wait()

            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(frames.tobytes())
            bio.seek(0)

            with sr.AudioFile(bio) as source:
                audio_data = self.recognizer.record(source)

            # Try Indian English first, then Hindi/Kannada fallback if requested
            lang_code = "en-IN" if lang == "en" else ("hi-IN" if lang == "hi" else ("kn-IN" if lang == "kn" else "en-IN"))
            text = self.recognizer.recognize_google(audio_data, language=lang_code)
            return {
                "text": text.strip(),
                "language": lang,
                "confidence": 0.9,
            }
        except sr.UnknownValueError:
            return {"text": "", "error": "No speech detected or could not understand audio."}
        except sr.RequestError as e:
            return {"text": "", "error": f"Speech service request failed: {e}"}
        except Exception as e:
            return {"text": "", "error": str(e)}

    def _transcribe_sarvam(self, file_path: str, lang: str) -> Dict[str, Any]:
        """Call Sarvam Saaras API for audio transcription."""
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {"api-subscription-key": self.sarvam_key}
        lang_code = f"{lang}-IN" if lang in ["hi", "kn", "en"] else "unknown"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                data = {"model": "saaras:v1", "language_code": lang_code}
                resp = httpx.post(url, headers=headers, files=files, data=data, timeout=15.0)
                if resp.status_code == 200:
                    res = resp.json()
                    return {
                        "text": res.get("transcript", ""),
                        "language": res.get("language_code", lang),
                        "confidence": 0.95,
                    }
        except Exception as e:
            return {"text": "", "error": str(e)}

        return {"text": "", "confidence": 0.0}

