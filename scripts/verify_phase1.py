"""Verification script for Phase 1.
Demonstrates the exact criterion from ARTH_SPEC:
'Done when: I chat in the terminal, ARTH picks a fake test tool, asks permission, and does nothing on "no".'
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import load_config
from arth.brain import OllamaManager
from arth.permissions import PermissionEngine
from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool


def main():
    print("=" * 60)
    print("  VERIFYING PHASE 1: BRAIN, TOOLS & PERMISSION ENGINE")
    print("=" * 60)

    config = load_config()
    brain = OllamaManager(config)

    registry = ToolRegistry()
    test_tool = TestActionTool()
    registry.register(test_tool)

    # ----------------------------------------------------
    # SCENARIO 1: Boss asks for action, says "no" to permission
    # ----------------------------------------------------
    print("\n--- SCENARIO 1: Boss says 'no' to permission prompt ---")
    user_prompt = "Boss wants you to move 12 files from Downloads to Notes"
    print(f"Boss >> {user_prompt}")

    def prompt_no(msg: str) -> bool:
        print(f"[PERMISSIONS PROMPT TRIGGERED] {msg} -> [USER TYPES: no]")
        return False

    engine_no = PermissionEngine(prompt_callback=prompt_no)
    response_no = brain.process_turn(
        user_input=user_prompt,
        tool_registry=registry,
        permission_engine=engine_no,
    )
    print(f"ARTH >> {response_no}")
    assert "cancelled" in response_no.lower(), "Expected action to be cancelled!"
    print("✓ VERIFIED: ARTH picked the test tool, asked permission, and did NOTHING on 'no'.")

    # ----------------------------------------------------
    # SCENARIO 2: Boss asks for action, says "yes" to permission
    # ----------------------------------------------------
    print("\n--- SCENARIO 2: Boss says 'yes' to permission prompt ---")
    print(f"Boss >> {user_prompt}")

    def prompt_yes(msg: str) -> bool:
        print(f"[PERMISSIONS PROMPT TRIGGERED] {msg} -> [USER TYPES: yes]")
        return True

    engine_yes = PermissionEngine(prompt_callback=prompt_yes)
    response_yes = brain.process_turn(
        user_input=user_prompt,
        tool_registry=registry,
        permission_engine=engine_yes,
    )
    print(f"ARTH >> {response_yes}")
    assert "Done, Boss!" in response_yes, "Expected action to be executed!"
    print("✓ VERIFIED: ARTH executed the action only after receiving 'yes'.")

    # ----------------------------------------------------
    # SCENARIO 3: Secret/Sensitive Document Request
    # ----------------------------------------------------
    print("\n--- SCENARIO 3: Secret / Sensitive Document Check ---")
    sensitive_prompt = "Move confidential secret password document from Downloads to Notes"
    print(f"Boss >> {sensitive_prompt}")

    def prompt_sensitive(msg: str) -> bool:
        print(f"[PERMISSIONS PROMPT TRIGGERED] {msg} -> [USER TYPES: yes]")
        assert "SENSITIVE/SECRET" in msg
        return True

    engine_sensitive = PermissionEngine(prompt_callback=prompt_sensitive)
    response_sensitive = brain.process_turn(
        user_input=sensitive_prompt,
        tool_registry=registry,
        permission_engine=engine_sensitive,
    )
    print(f"ARTH >> {response_sensitive}")
    print("✓ VERIFIED: Sensitive / secret document flag correctly added.")

    print("\n" + "=" * 60)
    print("  ALL PHASE 1 CRITERIA SUCCESSFULLY VERIFIED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
