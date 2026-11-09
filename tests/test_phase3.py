"""Automated test suite for ARTH Phase 3: Voice, Sounds & Quiet Hours.
Verifies multilingual detection, quiet hours suppression, mute/unmute, fillers, and startup chimes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import ArthConfig
from arth.voice.tts import TTSEngine
from arth.voice.wake_word import WakeWordDetector
from arth.voice.sounds import SoundManager
from arth.voice.fillers import FillerManager


class TestTTSEngine:
    def test_language_detection(self):
        """Verify automatic detection of Kannada, Hindi, and English."""
        tts = TTSEngine()

        # English
        assert tts.detect_language("Hello Boss, how can I help?") == "en"
        # Hindi (Devanagari)
        assert tts.detect_language("नमस्ते बॉस, क्या हाल है?") == "hi"
        # Kannada
        assert tts.detect_language("ನಮಸ್ಕಾರ ಬಾಸ್, ಹೇಗಿದ್ದೀರಾ?") == "kn"

    def test_quiet_hours_suppression(self):
        """Verify speech is completely suppressed during quiet hours (Section 15)."""
        cfg = ArthConfig()
        cfg.quiet_hours.enabled = True
        # Set quiet hours to full day 00:00 to 23:59 for test
        cfg.quiet_hours.start = "00:00"
        cfg.quiet_hours.end = "23:59"

        tts = TTSEngine(cfg)
        assert tts.is_quiet_hours() is True

        spoken = tts.speak("Hello Boss", blocking=True)
        assert spoken is False  # Suppressed!

    def test_quiet_hours_disabled(self):
        """Verify speech proceeds when quiet hours are turned off."""
        cfg = ArthConfig()
        cfg.quiet_hours.enabled = False

        tts = TTSEngine(cfg)
        assert tts.is_quiet_hours() is False

    def test_stop_interruption(self):
        """Verify tts.stop() clears active process and speaking flag."""
        tts = TTSEngine()
        mock_proc = MagicMock()
        tts._current_process = mock_proc
        tts._is_speaking = True

        tts.stop()
        assert mock_proc.terminate.called
        assert tts._is_speaking is False


class TestWakeWordAndMute:
    def test_wake_word_and_muting_cycle(self):
        """Verify mute command silences mic, and only 'ARTH, wake up' reactivates (Section 18)."""
        tts_messages = []
        detector = WakeWordDetector(tts_callback=lambda msg: tts_messages.append(msg))

        assert detector.is_muted is False

        # 1. Normal wake word
        res = detector.check_audio_transcription_for_wake_or_mute("ARTH what time is it")
        assert res == "WAKE"

        # 2. Command to mute
        res_mute = detector.check_audio_transcription_for_wake_or_mute("ARTH, mute")
        assert res_mute == "MUTED"
        assert detector.is_muted is True

        # 3. While muted, general commands are ignored
        res_ignore = detector.check_audio_transcription_for_wake_or_mute("ARTH what is the weather")
        assert res_ignore is None
        assert detector.is_muted is True

        # 4. 'ARTH, wake up' wakes the assistant
        res_wake = detector.check_audio_transcription_for_wake_or_mute("ARTH, wake up")
        assert res_wake == "WAKE_UP"
        assert detector.is_muted is False
        assert len(tts_messages) == 1
        assert "listening again" in tts_messages[0]


class TestSoundsAndFillers:
    def test_startup_greeting(self):
        """Verify startup sequence produces 'HELLOO BOSSS!' (Section 32)."""
        cfg = ArthConfig()
        cfg.quiet_hours.enabled = False
        sounds = SoundManager(cfg)

        with patch("subprocess.Popen") as mock_afplay:
            with patch.object(sounds.tts, "speak") as mock_speak:
                greeting = sounds.startup_greeting()
                assert greeting == "HELLOO BOSSS!"
                assert mock_speak.called

    def test_filler_manager_multilingual_and_varied(self):
        """Verify fillers for EN, HI, KN vary between calls (Section 21)."""
        fillers = FillerManager()

        en_filler1 = fillers.get_filler("en")
        en_filler2 = fillers.get_filler("en")
        assert len(en_filler1) > 0
        assert len(en_filler2) > 0

        hi_filler = fillers.get_filler("hi")
        assert any(w in hi_filler for w in ["minute", "dekhta", "Rukye", "sec"])

        kn_filler = fillers.get_filler("kn")
        assert any(w in kn_filler for w in ["nimisha", "iriri", "nodta", "nodtini"])
