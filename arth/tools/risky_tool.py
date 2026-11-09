"""Risky test tool to verify multi-factor authorization per Section 12 & 30 of ARTH_SPEC.
Risky actions: erase phone, send email, shut down or sleep other devices, move or rename many files.
Requires spoken 'yes' + Face Check + Typed Password.
"""

from __future__ import annotations

from typing import Any, Dict
from arth.tools.base import Tool


class RiskyTestActionTool(Tool):
    """A simulated risky system tool (e.g. erase device, massive system wipe)."""

    name = "risky_wipe_device"
    description = "Perform a high-risk security operation such as erasing a test device."
    parameters = {
        "type": "object",
        "properties": {
            "device_id": {
                "type": "string",
                "description": "Identifier of the target device to wipe.",
            },
            "confirmation_code": {
                "type": "string",
                "description": "The mandatory confirmation code (e.g. ERASE).",
            },
        },
        "required": ["device_id"],
    }
    is_sensitive = True
    is_risky = True  # Flag denoting Section 12 requirement for Face + Password

    def describe_action(self, **kwargs) -> str:
        device_id = kwargs.get("device_id", "target device")
        return f"permanently erase all contents from {device_id}"

    def execute(self, **kwargs) -> Dict[str, Any]:
        device_id = kwargs.get("device_id", "target device")
        return {
            "status": "success",
            "message": f"High-risk action completed: {device_id} was safely wiped.",
            "device_id": device_id,
        }
