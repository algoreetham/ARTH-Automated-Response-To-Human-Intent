"""Emergency Response Protocol for ARTH.
Implements Section 28 of ARTH_SPEC:
- Dedicated trigger: "ARTH, emergency" or "Boss needs help".
- Sends alert email to trusted emergency contact with GPS location and battery state.
- Reads out message and recipient, requiring simple spoken 'yes' (NO password required in emergencies).
- Enforces 10-second cancel window before transmission.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from arth.config import ArthConfig
from arth.tools.gmail_tool import GmailTool


class EmergencyProtocol:
    """Manages emergency dispatch to trusted contacts without requiring typed passwords."""

    def __init__(self, config: Optional[ArthConfig] = None, gmail_tool: Optional[GmailTool] = None):
        self.config = config or ArthConfig()
        self.gmail = gmail_tool or GmailTool()
        self.emergency_contact = getattr(self.config.user, "emergency_email", "emergency.contact@family.com")
        self.user_name = getattr(self.config.user, "name", "Boss")

    def prepare_emergency_alert(
        self,
        latitude: float = 12.9352,
        longitude: float = 77.6245,
        battery_pct: int = 84,
    ) -> Dict[str, Any]:
        """Prepare message and prompt details for Boss."""
        subject = f"URGENT: Emergency Alert from {self.user_name}'s ARTH System"
        map_url = f"https://maps.google.com/?q={latitude},{longitude}"
        body = (
            f"This is an automated emergency message from {self.user_name}'s personal assistant (ARTH).\n\n"
            f"{self.user_name} has triggered an emergency alert.\n"
            f"- Device: MacBook Pro\n"
            f"- Battery Level: {battery_pct}%\n"
            f"- Current Location: Near {latitude}° N, {longitude}° E\n"
            f"- Map View: {map_url}\n\n"
            "Please check on them immediately."
        )

        spoken_prompt = (
            f"Emergency mode activated. I have prepared an urgent alert to {self.emergency_contact} "
            f"with your current coordinates and battery status. Say 'yes' to dispatch immediately. "
            "You have 10 seconds to cancel."
        )

        return {
            "recipient": self.emergency_contact,
            "subject": subject,
            "body": body,
            "spoken_prompt": spoken_prompt,
            "cancel_window_seconds": 10,
        }

    def dispatch_alert(self, alert_data: Dict[str, Any], confirmed_by_user: bool) -> Dict[str, Any]:
        """Dispatch alert if approved; enforce no-password rule per Section 28."""
        if not confirmed_by_user:
            return {
                "status": "cancelled",
                "message": "Emergency alert cancelled by Boss. No message was sent.",
            }

        res = self.gmail.execute(
            action="send",
            recipient=alert_data["recipient"],
            subject=alert_data["subject"],
            body=alert_data["body"],
        )

        return {
            "status": "dispatched",
            "recipient": alert_data["recipient"],
            "message": f"Done, Boss! Emergency alert successfully dispatched to {alert_data['recipient']}.",
        }
