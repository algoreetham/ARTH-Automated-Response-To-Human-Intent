"""Activity Logger Engine for ARTH.
Enforces Section 14 of ARTH_SPEC:
- Record everything ARTH does: time, what was asked, which tool, device, result, short reason.
- Show it in a Log tab with search and filter.
- Never log passwords, OTPs, full email or notification contents, clipboard contents, moods, or face/voice data.
- Supports 'what did you do today?' and 'why did you do that?'.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default log storage path
DEFAULT_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOGS_DIR / "activity_log.jsonl"


@dataclass
class LogEntry:
    id: str
    timestamp: str  # ISO 8601 string
    query: str      # What Boss asked
    tool: str       # Which tool was selected
    device: str     # Target device (e.g., 'MacBook Pro')
    status: str     # 'approved', 'denied', 'executed', 'failed'
    reason: str     # Short plain-language description

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActivityLogger:
    """Manages secure, privacy-compliant audit logging of all ARTH actions."""

    # Patterns to redact per Section 14
    REDACT_PATTERNS = [
        (r"\b(password|pwd|passcode)\s*[:=]\s*\S+", r"\1: [REDACTED]"),
        (r"\b\d{4,8}\b", "[CODE/OTP REDACTED]"),  # Potential OTPs or PINs
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL REDACTED]"),
    ]

    def __init__(self, log_file: Optional[Path | str] = None, device_name: str = "MacBook Pro"):
        self.log_file = Path(log_file) if log_file else DEFAULT_LOG_FILE
        self.device_name = device_name
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.touch(exist_ok=True)
        except Exception:
            pass

    def sanitize(self, text: str) -> str:
        """Strip sensitive credentials, passwords, and OTPs before logging."""
        sanitized = text
        for pattern, replacement in self.REDACT_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        # Cap length to prevent full content logging
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."
        return sanitized

    def log(
        self,
        query: str,
        tool: str,
        status: str,
        reason: str,
        device: Optional[str] = None,
    ) -> LogEntry:
        """Record an action in the activity log."""
        entry = LogEntry(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=self.sanitize(query),
            tool=self.sanitize(tool),
            device=device or self.device_name,
            status=status.lower(),
            reason=self.sanitize(reason),
        )

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            print(f"Warning: Could not write activity log: {e}")

        return entry

    def get_logs(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve logs with optional search query and status filter."""
        if not self.log_file.exists():
            return []

        entries = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entries.append(data)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return []

        # Most recent first
        entries.reverse()

        filtered = []
        q = query.lower() if query else None
        s = status.lower() if status and status.lower() != "all" else None

        for item in entries:
            if s and item.get("status") != s:
                continue
            if q:
                searchable = (
                    f"{item.get('query', '')} {item.get('tool', '')} {item.get('reason', '')}"
                ).lower()
                if q not in searchable:
                    continue
            filtered.append(item)
            if len(filtered) >= limit:
                break

        return filtered

    def get_last_action_reason(self) -> str:
        """Answers: 'ARTH, why did you do that?' (Section 14)."""
        logs = self.get_logs(limit=1)
        if not logs:
            return "Boss, I haven't performed any actions yet."
        last = logs[0]
        return f"I {last['status']} '{last['tool']}' because {last['reason']} (Request: '{last['query']}')."

    def get_today_summary(self) -> str:
        """Answers: 'what did you do today?' (Section 14)."""
        logs = self.get_logs(limit=50)
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_logs = [l for l in logs if l.get("timestamp", "").startswith(today_date)]

        if not today_logs:
            return "Boss, I haven't executed any actions today."

        approved_count = sum(1 for l in today_logs if l.get("status") in ["approved", "executed"])
        denied_count = sum(1 for l in today_logs if l.get("status") == "denied")

        summary = f"Boss, today I processed {len(today_logs)} actions ({approved_count} approved/executed, {denied_count} denied)."
        return summary
