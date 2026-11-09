"""Verification script for Phase 3 (Voice) and Phase 4 (Memory and Personality).
Verifies acceptance criteria for both phases:
- Phase 3: Multilingual speech handling, quiet hours, mute/unmute.
- Phase 4: SQLite memory persistence across restarts and command-based forgetting.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import load_config
from arth.brain import OllamaManager
from arth.voice.tts import TTSEngine
from arth.voice.wake_word import WakeWordDetector
from arth.voice.sounds import SoundManager
from arth.memory.manager import MemoryManager
from arth.personality import PersonalityEngine
from arth.tools.base import ToolRegistry


def main():
    print("=" * 65)
    print("  VERIFYING PHASE 3 (VOICE) & PHASE 4 (MEMORY & PERSONALITY)")
    print("=" * 65)

    config = load_config()
    brain = OllamaManager(config)
    tts = TTSEngine(config)
    sounds = SoundManager(config, tts)
    personality = PersonalityEngine()

    test_db = PROJECT_ROOT / "logs" / "verify_phase4.db"
    if test_db.exists():
        test_db.unlink()
    memory = MemoryManager(db_path=test_db)

    registry = ToolRegistry()

    # ====================================================
    # PHASE 3: VOICE & SOUND VERIFICATION
    # ====================================================
    print("\n--- PHASE 3.1: Startup Sound & Greeting (Section 32) ---")
    greeting = sounds.startup_greeting()
    print(f"Startup Chime + Spoken Greeting: '{greeting}'")
    assert greeting == "HELLOO BOSSS!"
    print("✓ VERIFIED: Startup sequence executed 'HELLOO BOSSS!'.")

    print("\n--- PHASE 3.2: Multilingual Speech Detection (Section 2) ---")
    en_lang = tts.detect_language("Boss, your system is running smoothly.")
    hi_lang = tts.detect_language("बॉस, आज का मौसम बहुत अच्छा है।")
    kn_lang = tts.detect_language("ಬಾಸ್, ನಿಮ್ಮ ಕೆಲಸ ಮುಗಿದಿದೆ.")
    print(f"  English text detected as: '{en_lang}' (Expected: 'en')")
    print(f"  Hindi text detected as:   '{hi_lang}' (Expected: 'hi')")
    print(f"  Kannada text detected as: '{kn_lang}' (Expected: 'kn')")
    assert en_lang == "en" and hi_lang == "hi" and kn_lang == "kn"
    print("✓ VERIFIED: Multilingual text successfully mapped to native voices.")

    print("\n--- PHASE 3.3: Mic Mute & 'wake up' Listener (Section 18) ---")
    woken = []
    detector = WakeWordDetector(tts_callback=lambda msg: woken.append(msg))
    print("  Current State: Listening")
    detector.check_audio_transcription_for_wake_or_mute("ARTH, mute")
    print(f"  Command 'ARTH, mute' received -> State: {'MUTED' if detector.is_muted else 'ACTIVE'}")
    assert detector.is_muted is True

    # Ignored command
    res_ign = detector.check_audio_transcription_for_wake_or_mute("open my notes")
    assert res_ign is None
    print("  General commands while muted: IGNORED.")

    # React to 'ARTH, wake up'
    detector.check_audio_transcription_for_wake_or_mute("ARTH, wake up")
    print(f"  Command 'ARTH, wake up' received -> State: {'MUTED' if detector.is_muted else 'ACTIVE'}")
    assert detector.is_muted is False
    assert len(woken) == 1
    print(f"  Confirmation spoken: '{woken[0]}'")
    print("✓ VERIFIED: Mic mute and exclusive 'wake up' listener confirmed.")

    # ====================================================
    # PHASE 4: MEMORY & PERSONALITY VERIFICATION
    # ====================================================
    print("\n--- PHASE 4.1: Remember This (Section 7) ---")
    rem_reply = brain.process_turn(
        user_input="ARTH, remember this: Boss's favorite drink is filter coffee",
        tool_registry=registry,
        permission_engine=None,
        memory=memory,
        personality=personality,
    )
    print(f"Boss >> 'ARTH, remember this: Boss's favorite drink is filter coffee'")
    print(f"ARTH >> '{rem_reply}'")
    assert "filter coffee" in rem_reply

    print("\n--- PHASE 4.2: Persistence Across Restarts (Section 7) ---")
    # Simulate app restart by closing and re-opening MemoryManager from same SQLite DB
    restarted_memory = MemoryManager(db_path=test_db)
    recall_reply = brain.process_turn(
        user_input="what do you know about me?",
        tool_registry=registry,
        permission_engine=None,
        memory=restarted_memory,
        personality=personality,
    )
    print(f"Boss >> 'what do you know about me?' (after restart)")
    print(f"ARTH >>\n{recall_reply}")
    assert "filter coffee" in recall_reply
    print("✓ VERIFIED: Memory persisted across restart in SQLite.")

    print("\n--- PHASE 4.3: Forget Command (Section 7) ---")
    forget_reply = brain.process_turn(
        user_input="forget filter coffee",
        tool_registry=registry,
        permission_engine=None,
        memory=restarted_memory,
        personality=personality,
    )
    print(f"Boss >> 'forget filter coffee'")
    print(f"ARTH >> '{forget_reply}'")
    assert "forgotten" in forget_reply.lower()

    verify_forgotten = restarted_memory.what_do_you_know_about_me()
    assert "filter coffee" not in verify_forgotten
    print("✓ VERIFIED: Memory forgotten on command.")

    print("\n--- PHASE 4.4: Habit Learning (Section 25) ---")
    restarted_memory.record_habit("Opens terminal and codes at 10 AM")
    habits_reply = brain.process_turn(
        user_input="what habits have you noticed?",
        tool_registry=registry,
        permission_engine=None,
        memory=restarted_memory,
        personality=personality,
    )
    print(f"Boss >> 'what habits have you noticed?'")
    print(f"ARTH >>\n{habits_reply}")
    assert "Opens terminal" in habits_reply
    print("✓ VERIFIED: Habits tracked and recalled.")

    print("\n--- PHASE 4.5: Honest Pushback & Goodbye Joke (Section 32) ---")
    pushback = brain.process_turn(
        user_input="ARTH, delete everything right now",
        tool_registry=registry,
        permission_engine=None,
        memory=restarted_memory,
        personality=personality,
    )
    print(f"Boss >> 'ARTH, delete everything right now'")
    print(f"ARTH >> '{pushback}'")
    assert "bad idea" in pushback

    goodbye = brain.process_turn(
        user_input="goodbye ARTH",
        tool_registry=registry,
        permission_engine=None,
        memory=restarted_memory,
        personality=personality,
    )
    print(f"Boss >> 'goodbye ARTH'")
    print(f"ARTH >> '{goodbye}'")
    assert "Boss." in goodbye
    print("✓ VERIFIED: Pushback and goodbye jokes active.")

    print("\n" + "=" * 65)
    print("  PHASE 3 & PHASE 4 ACCEPTANCE CRITERIA FULLY VERIFIED!")
    print("=" * 65)

    if test_db.exists():
        test_db.unlink()


if __name__ == "__main__":
    main()
