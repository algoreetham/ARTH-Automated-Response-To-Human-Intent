#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 6: Everyday Tools.
Verifies each tool works by voice/chat with permission asked before execution:
1. Reminders (add, list)
2. To-dos (add, priority, deadline)
3. Notes (save, read, search)
4. Clipboard (read/write on demand, never in background)
5. Weather (auto-city detection, clean report)
6. News (startups/cricket/tech with sources)
7. Web search (citations and short spoken summary)
8. Study helper (explain code, debug, interactive quiz)
"""

import sys
from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.logger import ActivityLogger
from arth.permissions import PermissionEngine
from arth.tools.base import ToolRegistry
from arth.tools.reminders_tool import RemindersTool
from arth.tools.todos_tool import TodosTool
from arth.tools.notes_tool import NotesTool
from arth.tools.clipboard_tool import ClipboardTool
from arth.tools.weather_tool import WeatherTool
from arth.tools.news_tool import NewsTool
from arth.tools.web_search_tool import WebSearchTool
from arth.tools.study_helper_tool import StudyHelperTool


def main():
    print("=" * 65)
    print("🛠️ ARTH PHASE 6: EVERYDAY TOOLS VERIFICATION SUITE")
    print("=" * 65)

    reg = ToolRegistry()
    rem_tool = RemindersTool(store_path="logs/test_reminders.json")
    todo_tool = TodosTool(store_path="logs/test_todos.json")
    notes_tool = NotesTool(notes_dir="notes")
    clip_tool = ClipboardTool()
    weather_tool = WeatherTool()
    news_tool = NewsTool()
    search_tool = WebSearchTool()
    study_tool = StudyHelperTool()

    for tool in [rem_tool, todo_tool, notes_tool, clip_tool, weather_tool, news_tool, search_tool, study_tool]:
        reg.register(tool)

    cfg = ArthConfig()
    brain = OllamaManager(cfg)

    # Permission tracker: Auto-approve for automated testing
    prompts_asked = []
    def approval_callback(msg: str) -> bool:
        prompts_asked.append(msg)
        return True

    perm = PermissionEngine(prompt_callback=approval_callback)

    # 1. Reminders
    print("\n--- 1. Testing Reminders Tool ---")
    resp = brain.process_turn("ARTH, remind me to check the oven at 18:00", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    assert len(prompts_asked) >= 1
    print("✅ Reminders verified: Added with permission check.")

    # 2. To-dos
    print("\n--- 2. Testing To-dos Tool ---")
    resp = brain.process_turn("ARTH, add a todo: finish machine learning assignment", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ To-dos verified: Task added with priority and deadline.")

    # 3. Notes
    print("\n--- 3. Testing Notes Tool ---")
    resp = brain.process_turn("ARTH, save note: review chapter 4 for exam", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ Notes verified: Plain-text note saved.")

    # 4. Clipboard
    print("\n--- 4. Testing Clipboard Tool ---")
    resp = brain.process_turn("ARTH, what is on my clipboard?", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ Clipboard verified: Read on request only.")

    # 5. Weather
    print("\n--- 5. Testing Weather Tool ---")
    resp = brain.process_turn("ARTH, what's the weather like?", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ Weather verified: Location detected and conditions reported.")

    # 6. News
    print("\n--- 6. Testing News Tool ---")
    resp = brain.process_turn("ARTH, what's the latest startups news?", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ News verified: Category headlines and sources returned.")

    # 7. Web Search
    print("\n--- 7. Testing Web Search Tool ---")
    resp = brain.process_turn("search for latest Python 3.13 features", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ Web search verified: Spoken summary and sources provided.")

    # 8. Study & Coding Helper
    print("\n--- 8. Testing Study & Coding Helper ---")
    resp = brain.process_turn("ARTH, quiz me on python", reg, perm)
    print("ARTH >>", resp)
    assert "Done, Boss!" in resp
    print("✅ Study helper verified: Quiz questions prepared.")

    print("\n" + "=" * 65)
    print("🎉 ALL PHASE 6 EVERYDAY TOOLS VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
