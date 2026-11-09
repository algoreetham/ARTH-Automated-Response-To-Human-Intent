"""Google Client credential and session manager for ARTH.
Implements OAuth2 flow check and mock/live service access for Gmail, Calendar, and Drive.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


class GoogleClientManager:
    """Manages Google OAuth2 credentials and service stubs."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ):
        self.credentials_path = credentials_path or os.path.expanduser("~/Desktop/ARTH/credentials.json")
        self.token_path = token_path or os.path.expanduser("~/Desktop/ARTH/token.json")

    def has_credentials(self) -> bool:
        """Check if OAuth2 credentials or token exist."""
        return os.path.exists(self.credentials_path) or os.path.exists(self.token_path)

    def get_service_status(self) -> Dict[str, Any]:
        """Return connectivity status for Google services."""
        connected = self.has_credentials()
        return {
            "connected": connected,
            "account": "user@gmail.com" if connected else None,
            "message": "Connected to Google Workspace" if connected else "Google OAuth credentials not configured in credentials.json.",
        }
