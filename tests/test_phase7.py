"""Tests for Phase 7: Files, Apps, and Project Helper (Sections 4, 23, 27, 34).
Verifies:
1. File operations strictly sandboxed to one allowed folder (no path traversal).
2. File find, move, rename inside workspace.
3. Organize workspace into categorized directories with permission.
4. App control (open / quit application).
5. System status report (battery, RAM, CPU, storage, Wi-Fi).
6. Project helper (create project scaffold with starter code).
7. Phase 7 Acceptance Criteria: ARTH organizes a test folder only after Boss says yes,
   and nothing outside it can be touched.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from arth.brain import OllamaManager
from arth.config import ArthConfig
from arth.permissions import PermissionEngine
from arth.tools.base import ToolRegistry
from arth.tools.files_tool import FileManagerTool
from arth.tools.apps_tool import AppControlTool
from arth.tools.status_tool import StatusReportTool
from arth.tools.project_tool import ProjectHelperTool


class TestFileManagerSandboxAndSafety:
    """Test file operations are strictly restricted to allowed folder."""

    def test_path_traversal_outside_allowed_folder_is_strictly_blocked(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = FileManagerTool(allowed_folder=str(workspace))

        # Attempt path traversal out of workspace
        with pytest.raises(PermissionError) as exc_info:
            tool._validate_path("../../etc/passwd")
        assert "Security boundary violation" in str(exc_info.value)

        # Attempt absolute path outside workspace
        with pytest.raises(PermissionError) as exc_info:
            tool._validate_path("/Library/Preferences")
        assert "Security boundary violation" in str(exc_info.value)

    def test_file_operations_inside_allowed_folder(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = FileManagerTool(allowed_folder=str(workspace))

        # Create sample files
        doc = workspace / "notes.txt"
        doc.write_text("Meeting notes")

        # 1. Find
        find_res = tool.execute(action="find", pattern="notes")
        assert find_res["status"] == "success"
        assert "notes.txt" in find_res["matches"]

        # 2. Rename
        rename_res = tool.execute(action="rename", source_rel_path="notes.txt", new_name="renamed_notes.txt")
        assert rename_res["status"] == "success"
        assert (workspace / "renamed_notes.txt").exists()

        # 3. Move
        move_res = tool.execute(action="move", source_rel_path="renamed_notes.txt", dest_rel_path="Archive/notes.txt")
        assert move_res["status"] == "success"
        assert (workspace / "Archive" / "notes.txt").exists()

        # 4. Trash (never permanent delete per Section 5)
        trash_res = tool.execute(action="trash", source_rel_path="Archive/notes.txt")
        assert trash_res["status"] == "success"
        assert (workspace / ".Trash" / "notes.txt").exists()

        # 5. Open file (Section 4 & 34)
        sample = workspace / "test_doc.txt"
        sample.write_text("Hello Boss")
        open_res = tool.execute(action="open", source_rel_path="test_doc.txt")
        assert open_res["status"] == "success"
        assert "test_doc.txt" in open_res["message"]

        # Open generic "one file"
        open_one_res = tool.execute(action="open", source_rel_path="one file")
        assert open_one_res["status"] == "success"


class TestAppControl:
    def test_app_control_actions(self):
        tool = AppControlTool()
        open_desc = tool.describe_action(action="open", app_name="Calculator")
        assert "launch" in open_desc.lower()
        close_desc = tool.describe_action(action="close", app_name="Calculator")
        assert "quit" in close_desc.lower()


class TestStatusReport:
    def test_status_report_diagnostics(self):
        tool = StatusReportTool()
        res = tool.execute()
        assert res["status"] == "success"
        assert "spoken_summary" in res
        assert "Boss" in res["spoken_summary"]
        assert "battery" in res["gui_details"]
        assert "storage" in res["gui_details"]


class TestProjectHelper:
    def test_create_project_and_status(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = ProjectHelperTool(workspace_root=str(workspace))

        # Create project
        create_res = tool.execute(action="create", project_name="MyTestAgent", language="python")
        assert create_res["status"] == "success"
        assert (workspace / "MyTestAgent" / "main.py").exists()

        # Project status
        status_res = tool.execute(action="status", project_name="MyTestAgent")
        assert status_res["status"] == "success"
        assert "Project initialized" in status_res["project"]["milestones"]


class TestPhase7AcceptanceCriteria:
    """Done when: ARTH organizes a test folder only after my yes, and nothing outside it can be touched."""

    def test_organize_test_folder_denied_on_no(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = FileManagerTool(allowed_folder=str(workspace))

        # Populate with test files
        (workspace / "doc1.txt").write_text("doc")
        (workspace / "script1.py").write_text("code")

        reg = ToolRegistry()
        reg.register(tool)
        cfg = ArthConfig()
        brain = OllamaManager(cfg)

        # Deny permission
        perm = PermissionEngine(prompt_callback=lambda msg: False)

        resp = brain.process_turn("ARTH, organize workspace files", reg, perm)
        assert "cancelled" in resp.lower()
        # Verify files were NOT moved
        assert (workspace / "doc1.txt").exists()
        assert (workspace / "script1.py").exists()

    def test_organize_test_folder_executed_on_yes(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = FileManagerTool(allowed_folder=str(workspace))

        # Populate with test files
        (workspace / "doc1.txt").write_text("doc")
        (workspace / "script1.py").write_text("code")

        reg = ToolRegistry()
        reg.register(tool)
        cfg = ArthConfig()
        brain = OllamaManager(cfg)

        # Grant permission
        perm = PermissionEngine(prompt_callback=lambda msg: True)

        resp = brain.process_turn("ARTH, organize workspace files", reg, perm)
        assert "Done, Boss!" in resp
        # Verify files were categorized into subfolders
        assert (workspace / "Documents" / "doc1.txt").exists()
        assert (workspace / "Code" / "script1.py").exists()

    def test_brain_open_file_and_app_commands(self, tmp_path):
        workspace = tmp_path / "ARTH_Workspace"
        workspace.mkdir()
        tool = FileManagerTool(allowed_folder=str(workspace))
        (workspace / "notes.txt").write_text("Meeting notes")

        apps_tool = AppControlTool()

        reg = ToolRegistry()
        reg.register(tool)
        reg.register(apps_tool)

        cfg = ArthConfig()
        brain = OllamaManager(cfg)
        perm = PermissionEngine(prompt_callback=lambda msg: True)

        # 1. Open one file
        resp1 = brain.process_turn("open one file", reg, perm)
        assert "opened" in resp1.lower()

        # 2. Open specific file
        resp2 = brain.process_turn("open file notes.txt", reg, perm)
        assert "notes.txt" in resp2.lower()

        # 3. Open application
        resp3 = brain.process_turn("open Calculator", reg, perm)
        assert "calculator" in resp3.lower()
