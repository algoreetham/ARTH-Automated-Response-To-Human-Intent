"""Test tool implementation for ARTH Phase 1.
Used to verify tool calling, parameter extraction, and human permission engine.
"""

from __future__ import annotations

from typing import Any, Dict
from arth.tools.base import Tool


class TestActionTool(Tool):
    """A fake test tool representing a system action (e.g. organizing files or creating items)."""

    name = "organize_test_files"
    description = "Organize or move test files into a designated folder inside the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "source_folder": {
                "type": "string",
                "description": "Folder where files are located (e.g., 'Downloads')",
            },
            "destination_folder": {
                "type": "string",
                "description": "Folder to move files into (e.g., 'Notes' or 'Projects')",
            },
            "file_count": {
                "type": "integer",
                "description": "Number of files to move or organize",
            },
        },
        "required": ["source_folder", "destination_folder"],
    }

    def describe_action(self, **kwargs) -> str:
        source = kwargs.get("source_folder", "source")
        dest = kwargs.get("destination_folder", "destination")
        count = kwargs.get("file_count", 5)
        return f"move {count} files from {source} to {dest}"

    def execute(self, **kwargs) -> Dict[str, Any]:
        source = kwargs.get("source_folder", "source")
        dest = kwargs.get("destination_folder", "destination")
        count = kwargs.get("file_count", 5)
        return {
            "status": "success",
            "message": f"Successfully moved {count} files from '{source}' to '{dest}'.",
            "files_affected": count,
        }
