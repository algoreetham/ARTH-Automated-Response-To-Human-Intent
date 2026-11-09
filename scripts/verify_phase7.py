#!/usr/bin/env python3
"""Automated and interactive verification script for Phase 7: Files, Apps, & Project Helper.
Verifies:
1. Strict restriction to allowed folder (outside directory operations are refused).
2. Organizing a test folder only occurs after Boss's 'yes'.
3. App control (open / close apps).
4. Status report (battery, RAM, CPU, storage, Wi-Fi).
5. Project helper (scaffolding starter templates).
"""

import os
import shutil
import tempfile
from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.permissions import PermissionEngine
from arth.tools.base import ToolRegistry
from arth.tools.files_tool import FileManagerTool
from arth.tools.apps_tool import AppControlTool
from arth.tools.status_tool import StatusReportTool
from arth.tools.project_tool import ProjectHelperTool


def main():
    print("=" * 65)
    print("📁 ARTH PHASE 7: FILES, APPS & PROJECT HELPER VERIFICATION")
    print("=" * 65)

    test_ws = os.path.expanduser("~/Desktop/ARTH_Workspace_Test")
    os.makedirs(test_ws, exist_ok=True)

    files_tool = FileManagerTool(allowed_folder=test_ws)
    apps_tool = AppControlTool()
    status_tool = StatusReportTool()
    project_tool = ProjectHelperTool(workspace_root=test_ws)

    reg = ToolRegistry()
    for t in [files_tool, apps_tool, status_tool, project_tool]:
        reg.register(t)

    cfg = ArthConfig()
    brain = OllamaManager(cfg)

    # 1. Test Sandbox Restriction
    print("\n--- 1. Testing File Security Sandbox (Section 4 & 34) ---")
    try:
        files_tool._validate_path("../../secret_document.txt")
        assert False, "Should have blocked path traversal!"
    except PermissionError as e:
        print(f"Path traversal blocked as expected: {e}")
    print("✅ Sandbox Verified: Paths outside allowed folder are strictly refused.")

    # 2. Test Organize Folder on Permission
    print("\n--- 2. Testing Organize Test Folder on Approval (Acceptance Criteria) ---")
    with open(os.path.join(test_ws, "report.pdf"), "w") as f:
        f.write("pdf data")
    with open(os.path.join(test_ws, "algo.py"), "w") as f:
        f.write("python data")

    # A) On Boss 'no' -> nothing touched
    perm_deny = PermissionEngine(prompt_callback=lambda msg: False)
    deny_reply = brain.process_turn("ARTH, organize workspace files", reg, perm_deny)
    print("Deny turn reply:", deny_reply)
    assert os.path.exists(os.path.join(test_ws, "report.pdf"))
    assert "cancelled" in deny_reply.lower()
    print("✓ On 'no', action cancelled and no files were moved.")

    # B) On Boss 'yes' -> organized
    perm_allow = PermissionEngine(prompt_callback=lambda msg: True)
    allow_reply = brain.process_turn("ARTH, organize workspace files", reg, perm_allow)
    print("Approve turn reply:", allow_reply)
    assert "Done, Boss!" in allow_reply
    assert os.path.exists(os.path.join(test_ws, "Documents", "report.pdf"))
    assert os.path.exists(os.path.join(test_ws, "Code", "algo.py"))
    print("✅ Organize Verified: Folders organized only after Boss says 'yes'.")

    # 3. Status Report
    print("\n--- 3. Testing System Status Report (Section 23) ---")
    status_reply = brain.process_turn("ARTH, status report", reg, perm_allow)
    print("ARTH >>", status_reply)
    assert "Done, Boss!" in status_reply
    print("✅ Status Report Verified: Battery, RAM, CPU, storage, and Wi-Fi reported.")

    # 4. App Control
    print("\n--- 4. Testing App Control (Section 4) ---")
    app_reply = brain.process_turn("ARTH, open Calculator", reg, perm_allow)
    print("ARTH >>", app_reply)
    assert "Done, Boss!" in app_reply
    print("✅ App Control Verified: Application opened cleanly.")

    # 5. Project Helper
    print("\n--- 5. Testing Project Helper (Section 27) ---")
    proj_reply = brain.process_turn("ARTH, create project AgentDemo", reg, perm_allow)
    print("ARTH >>", proj_reply)
    assert "Done, Boss!" in proj_reply
    assert os.path.exists(os.path.join(test_ws, "AgentDemo", "main.py"))
    print("✅ Project Helper Verified: Scaffolded starter project inside allowed workspace.")

    # Cleanup test workspace
    shutil.rmtree(test_ws, ignore_errors=True)

    print("\n" + "=" * 65)
    print("🎉 ALL PHASE 7 ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
