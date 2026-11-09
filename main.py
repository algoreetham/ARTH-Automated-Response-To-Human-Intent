"""ARTH: Automated Response to Human Intent.
Phases 0 - 4: Foundation, Brain, Tools, GUI, Voice, Memory & Personality.
"""

from __future__ import annotations

import argparse
import sys

from arth.config import load_config
from arth.brain import OllamaManager
from arth.permissions import PermissionEngine
from arth.multi_request import MultiRequestHandler
from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool
from arth.logger import ActivityLogger
from arth.memory.manager import MemoryManager
from arth.personality import PersonalityEngine
from arth.voice.tts import TTSEngine
from arth.voice.stt import STTEngine
from arth.voice.sounds import SoundManager


def run_terminal_chat(config, brain: OllamaManager, tts: TTSEngine, memory: MemoryManager, personality: PersonalityEngine, logger: ActivityLogger) -> None:
    """Run interactive terminal chat loop with voice, memory, tools, and human permission gate."""
    # 1. Setup tool registry
    from arth.tools.registry_factory import get_default_registry
    registry = get_default_registry()

    # 2. Setup safety & multi-request engines
    permission_engine = PermissionEngine(strict_mode=True)
    multi_handler = MultiRequestHandler()

    print("\n" + "=" * 54)
    print("  🤖 ARTH — Personal AI Assistant (Terminal Chat)")
    print(f"  Addressing: {config.user.name}")
    print("  Type 'exit' or 'quit' to close.")
    print("=" * 54 + "\n")

    history = []

    while True:
        try:
            user_input = input(f"{config.user.name} >> ").strip()
        except (EOFError, KeyboardInterrupt):
            goodbye_msg = personality.get_goodbye()
            print(f"\n{goodbye_msg}\n")
            tts.speak(personality.clean_spoken_response(goodbye_msg), blocking=True)
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            goodbye_msg = personality.get_goodbye()
            print(f"\n{goodbye_msg}\n")
            tts.speak(personality.clean_spoken_response(goodbye_msg), blocking=True)
            break

        # Check for multiple requests (Section 16)
        split_reqs = multi_handler.split_requests(user_input)
        ordered_reqs = multi_handler.order_requests(split_reqs)

        # Process each request in chosen order
        for req in ordered_reqs:
            if len(ordered_reqs) > 1:
                print(f"\n[Executing step: '{req}']")

            response = brain.process_turn(
                user_input=req,
                tool_registry=registry,
                permission_engine=permission_engine,
                history=history,
                logger=logger,
                memory=memory,
                personality=personality,
            )
            print(f"\nARTH >> {response}\n")

            # Speak response (Section 8: short spoken response, simple words)
            tts.speak(personality.clean_spoken_response(response), blocking=False)

            history.append({"role": "user", "content": req})
            history.append({"role": "assistant", "content": response})


def main() -> int:
    parser = argparse.ArgumentParser(description="ARTH - Automated Response to Human Intent")
    parser.add_argument("--config", type=str, default=None, help="Path to custom config.yaml")
    parser.add_argument("--check-only", action="store_true", help="Only verify Ollama readiness and exit")
    parser.add_argument("--terminal", "--chat", action="store_true", help="Launch interactive terminal mode")
    parser.add_argument("--gui", action="store_true", help="Launch interactive native macOS GUI window")
    parser.add_argument("--web", action="store_true", help="Launch web browser interface on http://127.0.0.1:8501")
    parser.add_argument("--port", type=int, default=8501, help="Port for web server (default: 8501)")
    args = parser.parse_args()

    # 1. Load configuration and core services
    config = load_config(config_path=args.config)
    brain = OllamaManager(config)
    tts = TTSEngine(config)
    sounds = SoundManager(config, tts)
    memory = MemoryManager()
    personality = PersonalityEngine()
    logger = ActivityLogger()
    stt = STTEngine(config)

    # 2. Verify status
    status = brain.verify_readiness()
    if not status.get("ready"):
        print(f"\n{status.get('message')}\n")
        if not args.web:
            return 1
        print("⚡ Operating web preview in hybrid mode with rule-based heuristics & system tools.")
    else:
        print("Ollama is ready")
        if status.get("detail"):
            print(f"Status: {status['detail']}")

    print(f"Loaded configuration for {config.user.name}.")
    print(f"Configured brain: {config.brain.model} (fallback: {config.brain.fallback_model}, context window: {config.brain.context_window})")

    # Startup greeting (Section 32)
    if not args.check_only:
        greeting = sounds.startup_greeting()
        print(f"\n>>> {greeting} <<<\n")

    if args.check_only:
        return 0

    # 3. GUI, Web, or Terminal launch
    if args.web:
        from arth.gui.app import run_web_server
        run_web_server(
            port=args.port,
            config=config,
            brain=brain,
            logger=logger,
            tts=tts,
            stt=stt,
            memory=memory,
            personality=personality,
        )
        return 0

    if args.gui:
        from arth.gui.app import launch_gui
        launch_gui(
            config=config,
            brain=brain,
            logger=logger,
            tts=tts,
            stt=stt,
            memory=memory,
            personality=personality,
        )
        return 0

    if args.terminal:
        run_terminal_chat(config, brain, tts, memory, personality, logger)
        return 0

    if sys.stdin.isatty():
        run_terminal_chat(config, brain, tts, memory, personality, logger)

    return 0


if __name__ == "__main__":
    sys.exit(main())
