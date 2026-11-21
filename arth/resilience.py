"""Self-Healing, Crash Recovery & Circuit Breaker for ARTH.
Implements Section 20 of ARTH_SPEC:
- Automated crash recovery and restart loop.
- Plain-words spoken greeting after crash: "Boss, I crashed but I'm back".
- Technical stack trace logged in activity_log.jsonl.
- Circuit breaker: if it crashes 3 times in 5 minutes (300s), stops restarting and presents error.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from arth.logger import ActivityLogger


class CrashRecoveryController:
    """Manages crash limits, circuit breaking, and plain-words recovery messaging."""

    def __init__(
        self,
        max_crashes: int = 3,
        window_seconds: float = 300.0,
        logger: Optional[ActivityLogger] = None,
    ):
        self.max_crashes = max_crashes
        self.window_seconds = window_seconds
        self.logger = logger or ActivityLogger()
        self.crash_timestamps: List[float] = []

    def record_crash(self, error_message: str, stack_trace: str = "") -> Tuple[bool, str]:
        """
        Record a crash event.
        Returns:
            (can_restart: bool, message: str)
        """
        now = time.time()
        self.crash_timestamps.append(now)

        # Retain only crashes within window
        self.crash_timestamps = [t for t in self.crash_timestamps if (now - t) <= self.window_seconds]

        # Log technical error
        if self.logger:
            self.logger.log(
                query="<system crash event>",
                tool="crash_recovery",
                status="failed",
                reason=f"Crash #{len(self.crash_timestamps)}: {error_message}. Stack: {stack_trace[:120]}",
            )

        # Check circuit breaker limit
        if len(self.crash_timestamps) >= self.max_crashes:
            return (
                False,
                f"Boss, I've crashed {self.max_crashes} times in the last 5 minutes. "
                f"Halting automatic restarts to protect your system. Error: {error_message}",
            )

        return (
            True,
            "Boss, I crashed but I'm back. All systems restored and running.",
        )

    def get_status(self) -> Dict[str, Any]:
        """Return current crash count and circuit breaker health."""
        now = time.time()
        active_count = len([t for t in self.crash_timestamps if (now - t) <= self.window_seconds])
        return {
            "recent_crashes": active_count,
            "max_allowed": self.max_crashes,
            "healthy": active_count < self.max_crashes,
            "window_seconds": self.window_seconds,
        }
