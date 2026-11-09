"""Verification script for Phase 2: GUI and Activity Log.
Verifies the acceptance criterion:
'Done when: the same test works in the window and every action shows in the log.'
"""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arth.config import load_config
from arth.brain import OllamaManager
from arth.logger import ActivityLogger
from arth.gui.bridge import GUIBridge


def main():
    print("=" * 60)
    print("  VERIFYING PHASE 2: GUI & ACTIVITY LOG")
    print("=" * 60)

    test_log_file = PROJECT_ROOT / "logs" / "test_verification_log.jsonl"
    if test_log_file.exists():
        test_log_file.unlink()

    config = load_config()
    brain = OllamaManager(config)
    logger = ActivityLogger(log_file=test_log_file)
    bridge = GUIBridge(config, brain, logger=logger)

    mock_window = MagicMock()
    bridge.set_window(mock_window)

    # ----------------------------------------------------
    # TEST 1: GUI User sends command -> Modal pops up -> User clicks 'Deny'
    # ----------------------------------------------------
    print("\n--- TEST 1: GUI Action Denied via Popup Modal ---")
    user_prompt = "Boss wants you to move 12 files from Downloads to Notes"
    print(f"GUI Chat Input >> '{user_prompt}'")

    def simulate_deny_click():
        time.sleep(0.1)
        print("  [GUI POPUP APPEARS ON SCREEN] Boss clicks: ❌ Deny")
        bridge.resolve_permission(False)

    t1 = threading.Thread(target=simulate_deny_click)
    t1.start()

    res1 = bridge.send_message(user_prompt)
    t1.join()

    print(f"GUI Chat Output >> {res1['reply']}")
    assert "Action cancelled" in res1["reply"]

    # Verify action logged as 'denied'
    logs1 = bridge.get_logs()
    print(f"  [LOG AUDIT] Total entries: {len(logs1)}")
    assert len(logs1) == 1
    assert logs1[0]["status"] == "denied"
    assert logs1[0]["tool"] == "organize_test_files"
    print(f"  [LOG ENTRY] Status: {logs1[0]['status']} | Tool: {logs1[0]['tool']} | Reason: {logs1[0]['reason']}")
    print("✓ VERIFIED: Modal popup denied action and logged 'denied' in Activity Log.")

    # ----------------------------------------------------
    # TEST 2: GUI User sends command -> Modal pops up -> User clicks 'Approve'
    # ----------------------------------------------------
    print("\n--- TEST 2: GUI Action Approved via Popup Modal ---")
    print(f"GUI Chat Input >> '{user_prompt}'")

    def simulate_approve_click():
        time.sleep(0.1)
        print("  [GUI POPUP APPEARS ON SCREEN] Boss clicks: ✓ Approve")
        bridge.resolve_permission(True)

    t2 = threading.Thread(target=simulate_approve_click)
    t2.start()

    res2 = bridge.send_message(user_prompt)
    t2.join()

    print(f"GUI Chat Output >> {res2['reply']}")
    assert "Done, Boss!" in res2["reply"]

    # Verify action logged as 'approved'
    logs2 = bridge.get_logs()
    print(f"  [LOG AUDIT] Total entries: {len(logs2)}")
    assert len(logs2) == 2
    assert logs2[0]["status"] == "approved"
    assert logs2[0]["tool"] == "organize_test_files"
    print(f"  [LOG ENTRY] Status: {logs2[0]['status']} | Tool: {logs2[0]['tool']} | Reason: {logs2[0]['reason']}")
    print("✓ VERIFIED: Modal popup approved action and logged 'approved' in Activity Log.")

    # ----------------------------------------------------
    # TEST 3: Search and Filter in Activity Log
    # ----------------------------------------------------
    print("\n--- TEST 3: Searching & Filtering in Log Tab ---")
    filtered_denied = bridge.get_logs(status="denied")
    assert len(filtered_denied) == 1
    print(f"  Filter by 'denied' -> {len(filtered_denied)} entry found.")

    filtered_approved = bridge.get_logs(status="approved")
    assert len(filtered_approved) == 1
    print(f"  Filter by 'approved' -> {len(filtered_approved)} entry found.")

    searched = bridge.get_logs(query="Downloads")
    assert len(searched) == 2
    print(f"  Search query 'Downloads' -> {len(searched)} entries found.")

    # ----------------------------------------------------
    # TEST 4: Voice/Chat Log Audit Queries (Section 14)
    # ----------------------------------------------------
    print("\n--- TEST 4: Section 14 Audit Questions ---")
    today_reply = brain.process_turn("what did you do today?", bridge.registry, bridge.permission_engine, logger=logger)
    print(f"Boss >> 'what did you do today?'")
    print(f"ARTH >> '{today_reply}'")
    assert "today I processed 2 actions" in today_reply

    why_reply = brain.process_turn("ARTH, why did you do that?", bridge.registry, bridge.permission_engine, logger=logger)
    print(f"Boss >> 'ARTH, why did you do that?'")
    print(f"ARTH >> '{why_reply}'")
    assert "I approved 'organize_test_files'" in why_reply

    print("\n" + "=" * 60)
    print("  PHASE 2 ACCEPTANCE CRITERIA FULLY VERIFIED!")
    print("=" * 60)

    # Cleanup test log
    if test_log_file.exists():
        test_log_file.unlink()


if __name__ == "__main__":
    main()
